import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Request

from backend.app.core.errors import AppHTTPException
from backend.app.core.limiter import limiter
from backend.app.data.returns import NavGapError, build_price_panel, log_returns
from backend.app.data.sec_client import get_daily_nav
from backend.app.domain.enums import ErrorCode
from backend.app.domain.schemas import SimulateRequest, SimulateResponse
from backend.app.engine.orchestrator import run_simulation

router = APIRouter()
RUNS_DIR = Path("data/runs")
logger = logging.getLogger("app.simulate")


def load_nav_returns(proj_ids: list[str], simulation_period_years: int):
    """Fetch NAV history for the requested funds and return daily log returns. Raises a
    hard error (never interpolates) if any requested fund has no usable NAV history."""
    import pandas as pd
    frames = []
    for proj_id in proj_ids:
        nav_df = get_daily_nav(proj_id, "2000-01-01", pd.Timestamp.today().strftime("%Y-%m-%d"))
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
    return log_returns(panel)


@router.post("/simulate", response_model=SimulateResponse)
@limiter.limit("10/minute")
def simulate(request: Request, simulation_request: SimulateRequest) -> SimulateResponse:
    proj_ids = [h.proj_id for h in simulation_request.holdings]
    started = time.monotonic()
    try:
        returns_df = load_nav_returns(proj_ids, simulation_request.simulation_period_years)
        response = run_simulation(simulation_request, returns_df)
    except AppHTTPException:
        raise
    except (KeyError, ValueError) as exc:
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
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "request.json").write_text(
        json.dumps(request.model_dump(mode="json"), indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    (run_dir / "result.json").write_text(
        json.dumps(to_jsonable(result), indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )


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
