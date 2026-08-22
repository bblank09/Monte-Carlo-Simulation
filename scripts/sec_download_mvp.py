"""Refresh the committed Monte Carlo SEC NAV cache.

The normal API path is deliberately offline. This command is the only place
that calls SEC Open Data: it reads the curated fund universe already committed
to ``data/processed/fund_universe.csv``, downloads all NAV pages for those
funds, validates the complete new panel, and only then atomically replaces
``data/processed/nav_panel.parquet``.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.config import resolve_project_path, settings
from backend.app.sec.client import SecOpenDataClient
from backend.app.sec.endpoints import FUND_DAILY_NAV
from backend.app.sec.normalizers import normalize_daily_nav_record, records

START_DATE = date(2015, 1, 1)
PAGE_SIZE = 100
PROCESSED_DIR = resolve_project_path(settings.processed_dir)
FUND_UNIVERSE_PATH = PROCESSED_DIR / "fund_universe.csv"
NAV_PANEL_PATH = PROCESSED_DIR / "nav_panel.parquet"
MANIFEST_PATH = PROCESSED_DIR / "sec_data_manifest.json"
NAV_COLUMNS = [
    "proj_id",
    "unique_id",
    "fund_class_name",
    "nav_date",
    "nav_per_unit",
    "net_asset",
    "sell_price",
    "buy_price",
    "last_upd_date",
]


class RefreshError(RuntimeError):
    """Raised when the new cache cannot be built and validated completely."""


def _optional_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def fetch_nav_for_fund(
    client: SecOpenDataClient,
    proj_id: str,
    expected_fund_class_name: str | None,
    end_date: date,
) -> tuple[list[dict], list[dict], int]:
    rows: list[dict] = []
    issues: list[dict] = []
    cursor: str | None = None
    page_count = 0

    while True:
        page_count += 1
        params = {
            "proj_id": proj_id,
            "start_nav_date": START_DATE.isoformat(),
            "end_nav_date": end_date.isoformat(),
            "page_size": PAGE_SIZE,
        }
        if cursor:
            params["next_cursor"] = cursor

        try:
            payload = client.get(FUND_DAILY_NAV, params=params)
        except Exception as exc:
            raise RefreshError(f"SEC NAV request failed for {proj_id}: {exc}") from exc

        page_records = records(payload)
        if not page_records:
            raise RefreshError(f"SEC NAV response was empty for {proj_id}, page {page_count}.")

        for record in page_records:
            record_class = _optional_text(record.get("fund_class_name") or record.get("FUND_CLASS_NAME"))
            if expected_fund_class_name and record_class and record_class != expected_fund_class_name:
                continue
            try:
                rows.append(normalize_daily_nav_record(record, proj_id=proj_id))
            except (KeyError, TypeError, ValueError) as exc:
                issues.append(
                    {
                        "proj_id": proj_id,
                        "nav_date": record.get("nav_date") or record.get("NAV_DATE") or "",
                        "error": str(exc),
                    }
                )

        next_cursor = payload.get("next_cursor") if isinstance(payload, dict) else None
        next_cursor = _optional_text(next_cursor)
        if not next_cursor:
            break
        if next_cursor == cursor:
            raise RefreshError(f"SEC NAV pagination cursor repeated for {proj_id}.")
        cursor = next_cursor

    if not rows:
        raise RefreshError(f"SEC NAV returned no valid rows for {proj_id}.")
    return rows, issues, page_count


def _validate_universe(universe: pd.DataFrame) -> None:
    required = {"proj_id", "fund_class_name"}
    missing = required - set(universe.columns)
    if missing:
        raise RefreshError(f"Fund universe is missing required columns: {sorted(missing)}")
    if universe.empty or universe["proj_id"].dropna().empty:
        raise RefreshError("Fund universe is empty.")


def _validate_nav_frame(nav_frame: pd.DataFrame, expected_proj_ids: set[str]) -> pd.DataFrame:
    missing = set(NAV_COLUMNS) - set(nav_frame.columns)
    if missing:
        raise RefreshError(f"Downloaded NAV panel is missing columns: {sorted(missing)}")

    frame = nav_frame[NAV_COLUMNS].copy()
    frame["proj_id"] = frame["proj_id"].astype(str)
    frame["nav_date"] = pd.to_datetime(frame["nav_date"], errors="raise")
    frame["nav_per_unit"] = pd.to_numeric(frame["nav_per_unit"], errors="raise")
    if frame["nav_per_unit"].isna().any() or (frame["nav_per_unit"] <= 0).any():
        raise RefreshError("Downloaded NAV panel contains a missing or non-positive NAV.")
    missing_funds = expected_proj_ids - set(frame["proj_id"])
    if missing_funds:
        sample = sorted(missing_funds)[:5]
        raise RefreshError(f"Downloaded NAV panel has no valid rows for {len(missing_funds)} funds: {sample}")

    frame = (
        frame.sort_values(["proj_id", "nav_date"])
        .drop_duplicates(["proj_id", "nav_date"], keep="last")
        .reset_index(drop=True)
    )
    return frame


def _atomic_write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        frame.to_parquet(temp_path, index=False)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _atomic_write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def refresh_cache(
    *,
    universe_path: Path = FUND_UNIVERSE_PATH,
    nav_panel_path: Path = NAV_PANEL_PATH,
    manifest_path: Path = MANIFEST_PATH,
    client: SecOpenDataClient | None = None,
    end_date: date | None = None,
) -> dict:
    universe = pd.read_csv(universe_path)
    _validate_universe(universe)
    funds = universe.drop_duplicates("proj_id").to_dict(orient="records")
    refresh_end = end_date or datetime.now(UTC).date()
    api_client = client or SecOpenDataClient()
    nav_rows: list[dict] = []
    skipped_invalid_rows = 0
    request_count = 0

    for fund in funds:
        proj_id = str(fund["proj_id"])
        expected_class = _optional_text(fund.get("fund_class_name"))
        rows, issues, pages = fetch_nav_for_fund(api_client, proj_id, expected_class, refresh_end)
        nav_rows.extend(rows)
        skipped_invalid_rows += len(issues)
        request_count += pages

    nav_frame = _validate_nav_frame(pd.DataFrame(nav_rows), {str(fund["proj_id"]) for fund in funds})
    manifest = {
        "source": "SEC Open Data",
        "endpoint": FUND_DAILY_NAV,
        "start": str(nav_frame["nav_date"].min().date()),
        "end": str(nav_frame["nav_date"].max().date()),
        "fund_count": len(funds),
        "nav_rows": len(nav_frame),
        "request_count": request_count,
        "skipped_invalid_nav_rows": skipped_invalid_rows,
        "valid_for_monte_carlo": True,
        "refreshed_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    # All network work and validation are complete before either committed file
    # is replaced, so an interrupted/partial SEC response leaves the last-known-
    # good cache available to the offline application.
    _atomic_write_parquet(nav_frame, nav_panel_path)
    _atomic_write_json(manifest, manifest_path)
    return manifest


def main() -> None:
    if not settings.sec_api_key:
        raise SystemExit("SEC_API_KEY (or SEC_OPENDATA_API_KEY) is required for a refresh.")
    manifest = refresh_cache()
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
