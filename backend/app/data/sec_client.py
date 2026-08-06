import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from backend.app.core.config import settings

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
API_KEY = settings.sec_api_key or os.environ.get("SEC_OPENDATA_API_KEY")
BASE_URL = settings.sec_api_base_url

# Local cache, matching CLAUDE.md's documented data-flow ("SEC Open Data API ->
# backend/app/data/ -> data/processed/nav_panel.parquet (cache) -> backend/app/engine/").
# find_funds()/find_equity_funds() and get_daily_nav() below read this cache exclusively
# -- no live SEC API call happens on the request path (mirrors ../Backtest Portfolio
# Webull:SEC OPENAI's backend/app/sec/cache.py pattern). The live SEC Open Data API is
# slow and occasionally flaky, so a local cache keeps the app's hot path reproducible.
DATA_DIR = Path(__file__).resolve().parents[3] / settings.processed_dir
FUND_UNIVERSE_PATH = DATA_DIR / "fund_universe.csv"
NAV_PANEL_PATH = DATA_DIR / "nav_panel.parquet"


def _clean_cache_value(value, default=None):
    """Convert pandas missing/scalar values to JSON-safe Python values."""
    if value is None or pd.isna(value):
        return default
    return value.item() if hasattr(value, "item") else value


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


def find_funds() -> list[dict]:
    """Return the complete SEC fund universe using Backtest's exact API shape."""
    return _load_fund_universe().fillna("").to_dict(orient="records")


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
            "proj_id": _clean_cache_value(row["proj_id"], ""),
            # The cache stores a short display_name (e.g. "K-SET50"), not SEC's full
            # official Thai fund name -- close enough for search/selection, and this
            # project never had the full proj_name_th field cached either way.
            "proj_name_th": _clean_cache_value(row["display_name"], ""),
            "comp_name_th": _clean_cache_value(row["amc_name_th"], ""),
            # Keep the full display/search contract that the sibling Backtest
            # Portfolio picker uses. The Monte Carlo engine still consumes
            # only proj_id; these fields are presentation metadata.
            "display_name": _clean_cache_value(row["display_name"], ""),
            "fund_class_name": _clean_cache_value(row["fund_class_name"], ""),
            "search_term": _clean_cache_value(row.get("search_term", row["policy_desc"]), ""),
            "amc_name_th": _clean_cache_value(row["amc_name_th"], ""),
            "amc_name_en": _clean_cache_value(row.get("amc_name_en", ""), ""),
            "policy_desc": _clean_cache_value(row["policy_desc"], ""),
            "nav_start": _clean_cache_value(row.get("nav_start")),
            "nav_end": _clean_cache_value(row.get("nav_end")),
            "nav_months": _clean_cache_value(row.get("nav_months")),
            "nav_span_months": _clean_cache_value(row.get("nav_span_months")),
            "nav_completeness": _clean_cache_value(row.get("nav_completeness")),
            "nav_gap_count": _clean_cache_value(row.get("nav_gap_count"), 0),
            "nav_largest_gap_start": _clean_cache_value(row.get("nav_largest_gap_start")),
            "nav_largest_gap_end": _clean_cache_value(row.get("nav_largest_gap_end")),
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
