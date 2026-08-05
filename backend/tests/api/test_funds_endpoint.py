from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@patch("backend.app.api.funds.find_equity_funds")
def test_funds_endpoint_returns_list(mock_find):
    mock_find.return_value = [{"proj_id": "M0027_2535", "proj_name_thai": "K หุ้นทุน"}]
    resp = client.get("/api/funds")
    assert resp.status_code == 200
    assert resp.json()[0]["proj_id"] == "M0027_2535"


@patch("backend.app.api.funds.find_equity_funds")
def test_funds_endpoint_includes_policy_desc(mock_find):
    mock_find.return_value = [{"proj_id": "M0027_2535", "proj_name_th": "K หุ้นทุน", "comp_name_th": "AMC", "policy_desc": "ตราสารทุน"}]
    resp = client.get("/api/funds")
    assert resp.status_code == 200
    assert resp.json()[0]["policy_desc"] == "ตราสารทุน"
