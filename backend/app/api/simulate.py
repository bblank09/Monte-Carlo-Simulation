import json
import logging
import math
import os
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Request

from backend.app.core.config import resolve_project_path, settings
from backend.app.core.errors import AppHTTPException
from backend.app.core.limiter import limiter
from backend.app.data.returns import NavGapError, build_price_panel, log_returns
from backend.app.data.sec_client import MIN_USABLE_NAV_OBSERVATIONS, get_daily_nav
from backend.app.domain.enums import ErrorCode
from backend.app.domain.schemas import SimulateRequest, SimulateResponse
from backend.app.engine.orchestrator import run_simulation

router = APIRouter()
RUNS_DIR = resolve_project_path(settings.runs_dir)
MAX_PERSISTED_RUNS = settings.max_persisted_runs
logger = logging.getLogger("app.simulate")


def nav_date_window(
    as_of: pd.Timestamp,
    simulation_period_years: int,
    use_full_history: bool | None,
) -> tuple[str, str]:
    """Return the NAV query window implied by the historical-data setting."""
    end = as_of.normalize()
    start = (
        pd.Timestamp("2000-01-01")
        if use_full_history is not False
        else end - pd.DateOffset(years=simulation_period_years)
    )
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def load_nav_returns(
    proj_ids: list[str],
    simulation_period_years: int,
    use_full_history: bool | None = True,
):
    """Fetch NAV history for the requested funds and return daily log returns. Raises a
    hard error (never interpolates) if any requested fund has no usable NAV history."""
    start_date, end_date = nav_date_window(
        pd.Timestamp.today(), simulation_period_years, use_full_history
    )
    frames = []
    for proj_id in proj_ids:
        nav_df = get_daily_nav(proj_id, start_date, end_date)
        if nav_df.empty:
            raise AppHTTPException(
                status_code=503,
                detail=f"No cached NAV history for {proj_id}.",
                code=ErrorCode.NAV_CACHE_MISSING,
            )
        frames.append(nav_df)
    nav_df = pd.concat(frames, ignore_index=True)
    try:
        panel = build_price_panel(nav_df)
    except NavGapError as exc:
        raise AppHTTPException(
            status_code=422,
            detail=str(exc),
            code=ErrorCode.INSUFFICIENT_NAV_HISTORY,
        ) from exc
    returns = log_returns(panel)
    minimum_returns = max(2, MIN_USABLE_NAV_OBSERVATIONS - 1)
    insufficient = {
        proj_id: int(returns[proj_id].notna().sum()) if proj_id in returns.columns else 0
        for proj_id in proj_ids
        if proj_id not in returns.columns or int(returns[proj_id].notna().sum()) < minimum_returns
    }
    if insufficient:
        details = ", ".join(f"{proj_id}: {count}" for proj_id, count in insufficient.items())
        raise AppHTTPException(
            status_code=422,
            detail=(
                f"Insufficient cached NAV history ({details} daily returns); "
                f"at least {minimum_returns} daily returns ({MIN_USABLE_NAV_OBSERVATIONS} NAV observations) are required."
            ),
            code=ErrorCode.INSUFFICIENT_NAV_HISTORY,
        )
    return returns


@router.post("/simulate", response_model=SimulateResponse)
@limiter.limit("10/minute")
def simulate(request: Request, simulation_request: SimulateRequest) -> SimulateResponse:
    proj_ids = [h.proj_id for h in simulation_request.holdings]
    started = time.monotonic()
    try:
        if simulation_request.simulation_model == "parameterized":
            # Parameterized paths are driven entirely by user assumptions. Historical
            # NAV is intentionally optional; risk diagnostics will be marked unavailable
            # instead of blocking a valid assumption-only run.
            returns_df = pd.DataFrame(columns=proj_ids)
        else:
            returns_df = load_nav_returns(
                proj_ids,
                simulation_request.simulation_period_years,
                simulation_request.use_full_history,
            )
        response = run_simulation(simulation_request, returns_df)
    except AppHTTPException:
        raise
    except (KeyError, ValueError, ArithmeticError, FloatingPointError) as exc:
        raise AppHTTPException(
            status_code=422,
            detail=str(exc),
            code=ErrorCode.SIMULATION_FAILED,
        ) from exc
    result = response.model_dump(mode="json")
    run_id = make_run_id()
    result.update({
        "run_id": run_id,
        "created_at": utc_now().isoformat(timespec="seconds").replace("+00:00", "Z"),
        "data_source": "sec_open_data",
    })
    persist_run(run_id, simulation_request, result)
    logger.info("simulation request succeeded: run_id=%s duration=%.3fs", run_id, time.monotonic() - started)
    return SimulateResponse.model_validate(result)


@router.get("/simulate/{run_id}", response_model=SimulateResponse)
def get_simulation(run_id: str) -> dict[str, Any]:
    # The run id is used as a filesystem path. Reject path traversal rather
    # than trusting a value supplied through a public URL query parameter.
    if run_id != Path(run_id).name or run_id in ("", ".", ".."):
        raise AppHTTPException(
            status_code=404,
            detail=f"Simulation run not found: {run_id}",
            code=ErrorCode.RUN_NOT_FOUND,
        )

    result_path = RUNS_DIR / run_id / "result.json"
    if not result_path.is_file():
        raise AppHTTPException(
            status_code=404,
            detail=f"Simulation run not found: {run_id}",
            code=ErrorCode.RUN_NOT_FOUND,
        )
    return json.loads(result_path.read_text(encoding="utf-8"))


def make_run_id() -> str:
    return f"run_{utc_now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"


def utc_now() -> datetime:
    return datetime.now(UTC)


def persist_run(run_id: str, request: SimulateRequest, result: dict[str, Any]) -> None:
    run_dir = RUNS_DIR / run_id
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    temporary_dir = Path(tempfile.mkdtemp(prefix=f".{run_id}.tmp-", dir=RUNS_DIR))
    try:
        (temporary_dir / "request.json").write_text(
            json.dumps(request.model_dump(mode="json"), indent=2, ensure_ascii=False, allow_nan=False),
            encoding="utf-8",
        )
        (temporary_dir / "result.json").write_text(
            json.dumps(to_jsonable(result), indent=2, ensure_ascii=False, allow_nan=False),
            encoding="utf-8",
        )
        os.replace(temporary_dir, run_dir)
    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise
    _prune_persisted_runs()


def _prune_persisted_runs() -> None:
    """Keep generated run artifacts bounded without touching non-run data."""
    if not RUNS_DIR.is_dir():
        return
    run_dirs = [path for path in RUNS_DIR.iterdir() if path.is_dir() and path.name.startswith("run_")]
    run_dirs.sort(key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)
    for stale_dir in run_dirs[MAX_PERSISTED_RUNS:]:
        shutil.rmtree(stale_dir)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if hasattr(value, "item"):
        return to_jsonable(value.item())
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    return value
