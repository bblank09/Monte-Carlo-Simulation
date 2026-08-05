from fastapi import APIRouter, HTTPException
from backend.app.domain.schemas import SimulateRequest, SimulateResponse
from backend.app.engine.orchestrator import run_simulation
from backend.app.data.sec_client import get_daily_nav
from backend.app.data.returns import NavGapError, build_price_panel, log_returns

router = APIRouter()


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
    return run_simulation(request, returns_df)
