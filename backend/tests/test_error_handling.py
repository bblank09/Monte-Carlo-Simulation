from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from backend.app.domain.schemas import SimulateResponse
from backend.app.main import app

client = TestClient(app)


def _valid_payload() -> dict:
    return {
        "holdings": [{"proj_id": "FUND_A", "weight": 100.0}],
        "initial_amount": 1000000,
        "simulation_period_years": 10,
        "tax_treatment": "pre_tax",
        "simulation_model": "parameterized",
        "n_paths": 1000,
        "seed": 1,
        "rebalancing": "annual",
        "distribution": "normal",
        "expected_return": 0.07,
        "expected_volatility": 0.14,
        "inflation_model": "parameterized",
        "inflation_mean": 0.03,
        "inflation_volatility": 0.01,
    }


def _fake_response() -> SimulateResponse:
    return SimulateResponse(
        overview={"n_paths": 1000, "survived_count": 1000, "survival_rate": 1.0},
        growth={"fan_chart": {}, "survival_over_time": []},
        distribution={"ending_balance_histogram": []},
        metrics={"percentile_table": {}, "sharpe": {}, "sortino": {}},
        risk={"correlation_and_returns": {}},
        run_config={},
    )


def test_validation_error_is_structured_json():
    response = client.post("/api/simulate", json={"holdings": []})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert isinstance(response.json()["detail"], list)


def test_unhandled_simulation_error_is_generic_json():
    with (
        patch("backend.app.api.simulate.load_nav_returns", return_value=pd.DataFrame()),
        patch("backend.app.api.simulate.run_simulation", side_effect=RuntimeError("secret stack detail")),
    ):
        response = TestClient(app, raise_server_exceptions=False).post("/api/simulate", json=_valid_payload())

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error", "code": "INTERNAL_ERROR"}
    assert "secret stack detail" not in response.text


def test_missing_run_returns_stable_error_code():
    response = client.get("/api/simulate/run_does_not_exist")
    assert response.status_code == 404
    assert response.json()["code"] == "RUN_NOT_FOUND"
