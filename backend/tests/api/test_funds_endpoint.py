from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


@patch("backend.app.api.funds.find_funds")
def test_funds_endpoint_matches_backtest_contract(mock_find):
    mock_find.return_value = [{"proj_id": "M0027_2535", "display_name": "K หุ้นทุน"}]
    resp = client.get("/api/funds")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["data_source"] == "sec_open_data"
    assert payload["funds"][0]["proj_id"] == "M0027_2535"


@patch("backend.app.api.funds.find_funds")
def test_funds_endpoint_includes_policy_desc(mock_find):
    mock_find.return_value = [{
        "proj_id": "M0027_2535",
        "proj_name_th": "K หุ้นทุน",
        "comp_name_th": "AMC",
        "display_name": "K หุ้นทุน",
        "fund_class_name": "main",
        "search_term": "ตราสารทุน",
        "amc_name_en": "AMC LTD",
        "policy_desc": "ตราสารทุน",
        "nav_start": "2015-01-01",
        "nav_end": "2026-07-31",
        "nav_months": 120,
        "nav_span_months": 138,
        "nav_completeness": 0.87,
        "nav_gap_count": 1,
        "nav_largest_gap_start": "2024-07",
        "nav_largest_gap_end": "2024-10",
    }]
    resp = client.get("/api/funds")
    assert resp.status_code == 200
    fund = resp.json()["funds"][0]
    assert fund["policy_desc"] == "ตราสารทุน"
    assert fund["display_name"] == "K หุ้นทุน"
    assert fund["fund_class_name"] == "main"
    assert fund["search_term"] == "ตราสารทุน"
    assert fund["amc_name_en"] == "AMC LTD"
    assert fund["nav_gap_count"] == 1
