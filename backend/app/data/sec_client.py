import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
API_KEY = os.environ.get("SEC_OPENDATA_API_KEY")
BASE_URL = "https://api.sec.or.th"

# Local cache, matching CLAUDE.md's documented data-flow ("SEC Open Data API ->
# backend/app/data/ -> data/processed/nav_panel.parquet (cache) -> backend/app/engine/").
# find_equity_funds() and get_daily_nav() below read this cache exclusively -- no live
# SEC API call happens on the request path (mirrors ../Backtest Portfolio Webull:SEC
# OPENAI's backend/app/sec/cache.py pattern, which this project's own doc comment
# already specified but never implemented until now). The live SEC Open Data API is
# slow and occasionally flaky (see the project's e2e test comments) and every request
# hitting it directly meant "Load an example portfolio" and /api/simulate could each
# take 30-90s or outright 500 on a transient timeout -- a local cache removes that
# entirely from the app's hot path.
DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"
FUND_UNIVERSE_PATH = DATA_DIR / "fund_universe.csv"
NAV_PANEL_PATH = DATA_DIR / "nav_panel.parquet"


def _headers():
    return {"Ocp-Apim-Subscription-Key": API_KEY}


def get_amcs():
    """Not used by the app's request path (no cached equivalent needed yet) -- kept as
    a live call for ad hoc/administrative use only."""
    resp = requests.get(f"{BASE_URL}/v2/fund/general-info/amcs", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()["items"]


@lru_cache(maxsize=1)
def _load_fund_universe() -> pd.DataFrame:
    if not FUND_UNIVERSE_PATH.exists():
        raise FileNotFoundError(
            f"FUND_UNIVERSE_CACHE_MISSING: no cached fund universe at {FUND_UNIVERSE_PATH}. "
            "Populate data/processed/fund_universe.csv (see CLAUDE.md's Data flow section)."
        )
    return pd.read_csv(FUND_UNIVERSE_PATH)


def find_equity_funds(policy_desc: str = "ตราสารทุน"):
    """Equity funds (policy_desc match, main share class) from the local fund-universe
    cache -- shaped like the raw SEC general-info/profiles API items (proj_name_th,
    comp_name_th, proj_id) so callers (backend/app/api/funds.py) don't need to change
    their field-mapping logic."""
    universe = _load_fund_universe()
    matched = universe[
        (universe["policy_desc"] == policy_desc) & (universe["fund_class_name"] == "main")
    ]
    return [
        {
            "proj_id": row["proj_id"],
            # The cache stores a short display_name (e.g. "K-SET50"), not SEC's full
            # official Thai fund name -- close enough for search/selection, and this
            # project never had the full proj_name_th field cached either way.
            "proj_name_th": row["display_name"],
            "comp_name_th": row["amc_name_th"],
        }
        for _, row in matched.iterrows()
    ]


def get_daily_nav(proj_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Daily NAV history for one fund from the local NAV cache, filtered to the
    requested date range. Returns the same (nav_date, proj_id, last_val) shape the
    live-API version used to, so callers (backend/app/api/simulate.py) are unaffected."""
    if not NAV_PANEL_PATH.exists():
        return pd.DataFrame(columns=["nav_date", "proj_id", "last_val"])
    df = pd.read_parquet(NAV_PANEL_PATH, filters=[("proj_id", "=", proj_id)])
    if df.empty:
        return pd.DataFrame(columns=["nav_date", "proj_id", "last_val"])
    df = df[["nav_date", "proj_id", "nav_per_unit"]].rename(columns={"nav_per_unit": "last_val"})
    df["nav_date"] = pd.to_datetime(df["nav_date"])
    mask = (df["nav_date"] >= pd.Timestamp(start_date)) & (df["nav_date"] <= pd.Timestamp(end_date))
    return df.loc[mask].sort_values("nav_date").reset_index(drop=True)
