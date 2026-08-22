from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.core.limiter import limiter
from backend.app.domain.schemas import SimulateResponse
from backend.app.main import app


def _payload() -> dict:
    return {
        "holdings": [{"proj_id": "FUND_A", "weight": 100.0}],
        "initial_amount": 1000000,
        "simulation_period_years": 10,
        "tax_treatment": "pre_tax",
        "simulation_model": "parameterized",
        "n_paths": 1000,
        "seed": 1,
        "rebalancing": "none",
        "distribution": "normal",
        "expected_return": 0.07,
        "expected_volatility": 0.14,
        "inflation_model": "parameterized",
        "inflation_mean": 0.03,
        "inflation_volatility": 0.01,
    }


def _response() -> SimulateResponse:
    return SimulateResponse(
        overview={"n_paths": 1000, "survived_count": 1000, "survival_rate": 1.0},
        growth={"fan_chart": {}, "survival_over_time": []},
        distribution={"ending_balance_histogram": []},
        metrics={"percentile_table": {}, "sharpe": {}, "sortino": {}},
        risk={"correlation_and_returns": {}},
        run_config={},
    )


@pytest.fixture(autouse=True)
def reset_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_eleventh_simulation_request_within_a_minute_is_rate_limited():
    client = TestClient(app)
    with (
        patch("backend.app.api.simulate.load_nav_returns", return_value=pd.DataFrame()),
        patch("backend.app.api.simulate.run_simulation", return_value=_response()),
        patch("backend.app.api.simulate.persist_run"),
    ):
        responses = [client.post("/api/simulate", json=_payload()) for _ in range(11)]

    assert [response.status_code for response in responses[:10]] == [200] * 10
    assert responses[10].status_code == 429
    assert responses[10].json()["code"] == "RATE_LIMIT_EXCEEDED"
