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
def test_simulate_endpoint_returns_200(mock_run, mock_load, ):
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


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
