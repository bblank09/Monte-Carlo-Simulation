import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from backend.app.core.errors import AppHTTPException
from backend.app.domain.enums import ErrorCode

router = APIRouter(prefix="/data-status", tags=["data-status"])
PROCESSED_DIR = Path("data/processed")
FUND_UNIVERSE_PATH = PROCESSED_DIR / "fund_universe.csv"
NAV_PANEL_PATH = PROCESSED_DIR / "nav_panel.parquet"
MANIFEST_PATH = PROCESSED_DIR / "sec_data_manifest.json"


def _cache_error(detail: str) -> AppHTTPException:
    return AppHTTPException(status_code=503, detail=detail, code=ErrorCode.NAV_CACHE_MISSING)


@router.get("")
def get_data_status() -> dict:
    if not FUND_UNIVERSE_PATH.is_file() or not NAV_PANEL_PATH.is_file():
        raise _cache_error(
            "SEC cache is missing. Run scripts/sec_download_mvp.py to refresh data/processed."
        )

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.is_file() else {}
        universe = pd.read_csv(FUND_UNIVERSE_PATH, usecols=["proj_id", "nav_start", "nav_end"])
        if universe.empty or universe["proj_id"].nunique() == 0:
            raise _cache_error("SEC fund universe cache is empty.")

        nav_start = manifest.get("start")
        nav_end = manifest.get("end")
        if not nav_start or not nav_end:
            nav_start = _first_valid_date(universe["nav_start"])
            nav_end = _last_valid_date(universe["nav_end"])

        if not nav_start or not nav_end:
            raise _cache_error("SEC NAV cache has no usable date metadata.")

        return {
            "data_source": "sec_open_data",
            "nav_as_of": nav_end,
            "nav_start": nav_start,
            "fund_count": int(universe["proj_id"].nunique()),
        }
    except AppHTTPException:
        raise
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise _cache_error(f"SEC cache is invalid: {exc}") from exc


def _first_valid_date(values: pd.Series) -> str | None:
    parsed = pd.to_datetime(values, errors="coerce").dropna()
    return parsed.min().date().isoformat() if not parsed.empty else None


def _last_valid_date(values: pd.Series) -> str | None:
    parsed = pd.to_datetime(values, errors="coerce").dropna()
    return parsed.max().date().isoformat() if not parsed.empty else None
