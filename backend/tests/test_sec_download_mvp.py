from datetime import date
from typing import Any

import pandas as pd
import pytest

from scripts.sec_download_mvp import RefreshError, refresh_cache


class FakeSecClient:
    def __init__(self, payloads=None, error: Exception | None = None):
        self.payloads = list(payloads or [])
        self.error = error
        self.calls: list[tuple[Any, Any]] = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        if self.error:
            raise self.error
        return self.payloads.pop(0)


def _universe(path):
    pd.DataFrame(
        [
            {
                "proj_id": "FUND_A",
                "fund_class_name": "main",
                "display_name": "Fund A",
                "nav_start": "2024-01-01",
                "nav_end": "2024-01-02",
            }
        ]
    ).to_csv(path, index=False)


def test_refresh_writes_mc_cache_schema_and_manifest(tmp_path):
    universe = tmp_path / "fund_universe.csv"
    nav_panel = tmp_path / "nav_panel.parquet"
    manifest = tmp_path / "sec_data_manifest.json"
    _universe(universe)
    client = FakeSecClient(
        [
            {
                "items": [
                    {"proj_id": "FUND_A", "fund_class_name": "main", "nav_date": "2024-01-01", "last_val": "10.0"},
                    {"proj_id": "FUND_A", "fund_class_name": "main", "nav_date": "2024-01-02", "last_val": "10.5"},
                ]
            }
        ]
    )

    result = refresh_cache(
        universe_path=universe,
        nav_panel_path=nav_panel,
        manifest_path=manifest,
        client=client,
        end_date=date(2024, 1, 2),
    )

    frame = pd.read_parquet(nav_panel)
    assert list(frame["proj_id"]) == ["FUND_A", "FUND_A"]
    assert frame["nav_per_unit"].tolist() == [10.0, 10.5]
    assert result["fund_count"] == 1
    assert result["valid_for_monte_carlo"] is True
    assert manifest.is_file()
    assert client.calls[0][1]["page_size"] == 100


def test_refresh_does_not_replace_existing_cache_after_download_failure(tmp_path):
    universe = tmp_path / "fund_universe.csv"
    nav_panel = tmp_path / "nav_panel.parquet"
    manifest = tmp_path / "sec_data_manifest.json"
    _universe(universe)
    original = pd.DataFrame(
        [{"proj_id": "FUND_A", "nav_date": "2023-01-01", "nav_per_unit": 9.0}]
    )
    original.to_parquet(nav_panel, index=False)
    nav_before = nav_panel.read_bytes()
    client = FakeSecClient(error=RuntimeError("SEC unavailable"))

    with pytest.raises(RefreshError, match="SEC NAV request failed"):
        refresh_cache(
            universe_path=universe,
            nav_panel_path=nav_panel,
            manifest_path=manifest,
            client=client,
            end_date=date(2024, 1, 2),
        )

    assert nav_panel.read_bytes() == nav_before
    assert not manifest.exists()
