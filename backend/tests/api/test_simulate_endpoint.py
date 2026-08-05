from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.domain.schemas import SimulateResponse

client = TestClient(app)


def _fake_response():
    return SimulateResponse(
        overview={"n_paths": 100, "survived_count": 95, "survival_rate": 0.95,
                   "median_ending_balance": 2_000_000.0, "median_cagr": 0.07, "holdings": []},
        growth={"fan_chart": {}, "survival_over_time": []},
        distribution={"ending_balance_histogram": []},
        metrics={"percentile_table": {"ending_balance": {}, "cagr": {}}, "sharpe": {}, "sortino": {},
                 "safe_withdrawal_rate": {}, "perpetual_withdrawal_rate": {}},
        risk={"correlation_and_returns": {}, "value_at_risk": 0.0, "expected_shortfall": 0.0},
        goals=None, run_config={},
    )


@patch("backend.app.api.simulate.load_nav_returns")
@patch("backend.app.api.simulate.run_simulation")
@patch("backend.app.api.simulate.persist_run")
def test_simulate_endpoint_returns_200(mock_persist, mock_run, mock_load):
    import pandas as pd
    mock_load.return_value = pd.DataFrame()
    mock_run.return_value = _fake_response()
    payload = {
        "holdings": [{"proj_id": "M0027_2535", "weight": 100.0}],
        "initial_amount": 1000000, "simulation_period_years": 10, "tax_treatment": "pre_tax",
        "simulation_model": "parameterized", "n_paths": 1000, "seed": 1, "rebalancing": "annual",
        "distribution": "normal", "expected_return": 0.07, "expected_volatility": 0.14,
        "inflation_model": "parameterized", "inflation_mean": 0.03, "inflation_volatility": 0.01,
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    assert resp.json()["overview"]["survival_rate"] == 0.95
    assert resp.json()["run_id"].startswith("run_")
    assert resp.json()["data_source"] == "sec_open_data"
    mock_persist.assert_called_once()


def test_get_simulation_returns_persisted_run(tmp_path, monkeypatch):
    from backend.app.api import simulate as simulate_api
    from backend.app.domain.schemas import SimulateRequest

    monkeypatch.setattr(simulate_api, "RUNS_DIR", tmp_path)
    request = SimulateRequest.model_validate({
        "holdings": [{"proj_id": "M0027_2535", "weight": 100.0}],
        "initial_amount": 1000000, "simulation_period_years": 10, "tax_treatment": "pre_tax",
        "simulation_model": "parameterized", "n_paths": 1000, "seed": 1, "rebalancing": "annual",
        "distribution": "normal", "expected_return": 0.07, "expected_volatility": 0.14,
        "inflation_model": "parameterized", "inflation_mean": 0.03, "inflation_volatility": 0.01,
    })
    run_id = "run_20260805_120000_abcdef12"
    result = _fake_response().model_dump(mode="json")
    result.update({"run_id": run_id, "created_at": "2026-08-05T12:00:00Z", "data_source": "sec_open_data"})
    simulate_api.persist_run(run_id, request, result)

    resp = client.get(f"/api/simulate/{run_id}")
    assert resp.status_code == 200
    assert resp.json()["run_id"] == run_id

    traversal = client.get("/api/simulate/../result.json")
    assert traversal.status_code == 404


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
