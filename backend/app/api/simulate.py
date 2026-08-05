import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from backend.app.domain.schemas import SimulateRequest, SimulateResponse
from backend.app.engine.orchestrator import run_simulation
from backend.app.data.sec_client import get_daily_nav
from backend.app.data.returns import NavGapError, build_price_panel, log_returns

router = APIRouter()
RUNS_DIR = Path("data/runs")


def load_nav_returns(proj_ids: list[str], simulation_period_years: int):
    """Fetch NAV history for the requested funds and return daily log returns. Raises a
    hard error (never interpolates) if any requested fund has no usable NAV history."""
    import pandas as pd
    frames = []
    for proj_id in proj_ids:
        nav_df = get_daily_nav(proj_id, "2000-01-01", pd.Timestamp.today().strftime("%Y-%m-%d"))
        if nav_df.empty:
            raise HTTPException(status_code=503, detail=f"NAV_CACHE_MISSING: no NAV history for {proj_id}")
        frames.append(nav_df)
    nav_df = pd.concat(frames, ignore_index=True)
    try:
        panel = build_price_panel(nav_df)
    except NavGapError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return log_returns(panel)


@router.post("/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest) -> SimulateResponse:
    proj_ids = [h.proj_id for h in request.holdings]
    returns_df = load_nav_returns(proj_ids, request.simulation_period_years)
    response = run_simulation(request, returns_df)
    result = response.model_dump(mode="json")
    result.update({
        "run_id": make_run_id(),
        "created_at": utc_now().isoformat(timespec="seconds").replace("+00:00", "Z"),
        "data_source": "sec_open_data",
    })
    persist_run(result["run_id"], request, result)
    return result


@router.get("/simulate/{run_id}", response_model=SimulateResponse)
def get_simulation(run_id: str) -> dict[str, Any]:
    # The run id is used as a filesystem path. Reject path traversal rather
    # than trusting a value supplied through a public URL query parameter.
    if run_id != Path(run_id).name or run_id in ("", ".", ".."):
        raise HTTPException(status_code=404, detail=f"Simulation run not found: {run_id}")

    result_path = RUNS_DIR / run_id / "result.json"
    if not result_path.is_file():
        raise HTTPException(status_code=404, detail=f"Simulation run not found: {run_id}")
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
