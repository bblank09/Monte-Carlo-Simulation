import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from backend.app.core.config import resolve_project_path, settings

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
API_KEY = settings.sec_api_key or os.environ.get("SEC_OPENDATA_API_KEY")
BASE_URL = settings.sec_api_base_url

# Local cache, matching CLAUDE.md's documented data-flow ("SEC Open Data API ->
# backend/app/data/ -> data/processed/nav_panel.parquet (cache) -> backend/app/engine/").
# find_funds()/find_equity_funds() and get_daily_nav() below read this cache exclusively
# -- no live SEC API call happens on the request path (mirrors ../Backtest Portfolio
# Webull:SEC OPENAI's backend/app/sec/cache.py pattern). The live SEC Open Data API is
# slow and occasionally flaky, so a local cache keeps the app's hot path reproducible.
DATA_DIR = resolve_project_path(settings.processed_dir)
FUND_UNIVERSE_PATH = DATA_DIR / "fund_universe.csv"
NAV_PANEL_PATH = DATA_DIR / "nav_panel.parquet"
MIN_USABLE_NAV_OBSERVATIONS = 252

_NULLABLE_NUMERIC_FIELDS = {
    "nav_start",
    "nav_end",
    "nav_months",
    "nav_span_months",
    "nav_completeness",
    "nav_largest_gap_start",
    "nav_largest_gap_end",
}


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
    """Return the SEC fund universe with a typed, usable-history availability flag."""
    observation_counts = _nav_observation_counts()
    return [
        _with_nav_availability(_normalize_universe_record(record), observation_counts)
        for record in _load_fund_universe().to_dict(orient="records")
    ]


def _available_proj_ids() -> set[str]:
    """Return funds with enough distinct cached NAV observations for diagnostics."""
    return {
        proj_id
        for proj_id, count in _nav_observation_counts().items()
        if count >= MIN_USABLE_NAV_OBSERVATIONS
    }


def _nav_observation_counts() -> dict[str, int]:
    if not NAV_PANEL_PATH.exists():
        return {}
    try:
        nav = pd.read_parquet(NAV_PANEL_PATH, columns=["proj_id", "nav_date"])
    except (KeyError, OSError, ValueError):
        # Small fixtures and older caches may only contain the key column. Counting
        # rows is still safer than treating every key as fully available.
        nav = pd.read_parquet(NAV_PANEL_PATH, columns=["proj_id"])
    nav = nav.dropna(subset=["proj_id"])
    if "nav_date" in nav.columns:
        nav = nav.drop_duplicates(["proj_id", "nav_date"])
    counts = nav.groupby("proj_id").size()
    return {str(proj_id): int(count) for proj_id, count in counts.items()}


def _normalize_universe_record(record: dict) -> dict:
    normalized = {}
    for key, value in record.items():
        default = None if key in _NULLABLE_NUMERIC_FIELDS else (0 if key == "nav_gap_count" else "")
        normalized[key] = _clean_cache_value(value, default)
    return normalized


def _with_nav_availability(record: dict, observation_counts: dict[str, int]) -> dict:
    proj_id = str(record.get("proj_id", ""))
    observations = observation_counts.get(proj_id, 0)
    available = observations >= MIN_USABLE_NAV_OBSERVATIONS
    if available:
        reason = None
    elif observations == 0:
        reason = "No cached NAV history"
    else:
        reason = (
            f"Only {observations} cached NAV observations; "
            f"at least {MIN_USABLE_NAV_OBSERVATIONS} are required"
        )
    return {
        **record,
        "nav_available": available,
        "nav_observations": observations,
        "nav_min_observations": MIN_USABLE_NAV_OBSERVATIONS,
        "nav_availability_reason": reason,
    }


def find_equity_funds(policy_desc: str = "ตราสารทุน"):
    """Equity funds (policy_desc match, main share class) from the local fund-universe
    cache -- shaped like the raw SEC general-info/profiles API items (proj_name_th,
    comp_name_th, proj_id) so callers (backend/app/api/funds.py) don't need to change
    their field-mapping logic."""
    universe = _load_fund_universe()
    matched = universe[
        (universe["policy_desc"] == policy_desc) & (universe["fund_class_name"] == "main")
    ]
    observation_counts = _nav_observation_counts()
    return [
        _with_nav_availability({
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
        }, observation_counts)
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
    df = df.drop_duplicates(["proj_id", "nav_date"], keep="last")
    mask = (df["nav_date"] >= pd.Timestamp(start_date)) & (df["nav_date"] <= pd.Timestamp(end_date))
    return df.loc[mask].sort_values("nav_date").reset_index(drop=True)
