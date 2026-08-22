from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_is_available_under_both_api_prefixes():
    for path in ("/api/health", "/api/v1/health"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["data_source"] == "sec_open_data"


@patch("backend.app.api.funds.find_funds", return_value=[{"proj_id": "FUND_A"}])
def test_funds_is_available_under_both_api_prefixes(mock_find_funds):
    for path in ("/api/funds", "/api/v1/funds"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["data_source"] == "sec_open_data"
    assert mock_find_funds.call_count == 2


def test_data_status_is_available_under_both_api_prefixes(tmp_path, monkeypatch):
    from backend.app.api import data_status

    universe_path = tmp_path / "fund_universe.csv"
    nav_path = tmp_path / "nav_panel.parquet"
    manifest_path = tmp_path / "sec_data_manifest.json"
    pd.DataFrame(
        [{"proj_id": "FUND_A", "nav_start": "2020-01-01", "nav_end": "2024-01-02"}]
    ).to_csv(universe_path, index=False)
    nav_path.write_bytes(b"cache exists")
    monkeypatch.setattr(data_status, "FUND_UNIVERSE_PATH", universe_path)
    monkeypatch.setattr(data_status, "NAV_PANEL_PATH", nav_path)
    monkeypatch.setattr(data_status, "MANIFEST_PATH", manifest_path)

    for path in ("/api/data-status", "/api/v1/data-status"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {
            "data_source": "sec_open_data",
            "nav_as_of": "2024-01-02",
            "nav_start": "2020-01-01",
            "fund_count": 1,
            "min_usable_nav_observations": 252,
        }
