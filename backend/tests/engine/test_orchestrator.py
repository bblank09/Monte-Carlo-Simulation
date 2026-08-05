import numpy as np
import pandas as pd
import pytest

from backend.app.domain.schemas import Holding, SimulateRequest
from backend.app.engine.orchestrator import run_simulation


def _returns_df():
    idx = pd.date_range("2015-01-01", periods=252 * 8, freq="B")
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "M0027_2535": rng.normal(0.0003, 0.011, len(idx)),
        "M0209_2548": rng.normal(0.0002, 0.009, len(idx)),
    }, index=idx)


def test_historical_request_produces_all_response_sections():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
        initial_amount=1_000_000, simulation_period_years=10, tax_treatment="pre_tax",
        simulation_model="historical", n_paths=2000, seed=1, rebalancing="annual",
        bootstrap_model="single_year", use_full_history=True, sequence_of_returns_risk=0,
        inflation_model="parameterized", inflation_mean=0.03, inflation_volatility=0.01,
    )
    response = run_simulation(req, _returns_df())
    assert response.overview["survived_count"] >= 0
    assert set(response.metrics["percentile_table"]["ending_balance"].keys()) == {10, 25, 50, 75, 90}
    assert "fan_chart" in response.growth
    assert len(response.distribution["ending_balance_histogram"]) == req.n_paths
    assert len(response.distribution["max_drawdown_histogram"]) == req.n_paths
    assert response.goals is None


def test_parameterized_request_skips_data_estimation():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=100.0)],
        initial_amount=500_000, simulation_period_years=15, tax_treatment="pre_tax",
        simulation_model="parameterized", n_paths=2000, seed=2, rebalancing="annual",
        distribution="normal", expected_return=0.07, expected_volatility=0.14,
        inflation_model="parameterized", inflation_mean=0.03, inflation_volatility=0.01,
    )
    response = run_simulation(req, _returns_df())
    assert response.metrics["percentile_table"]["ending_balance"][50] > 0


def test_percentile_table_has_all_eight_metrics_end_to_end():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
        initial_amount=1_000_000, simulation_period_years=10, tax_treatment="pre_tax",
        simulation_model="historical", n_paths=1000, seed=1, rebalancing="annual",
        bootstrap_model="single_year", use_full_history=True, sequence_of_returns_risk=0,
        inflation_model="historical",
    )
    response = run_simulation(req, _returns_df())
    expected_keys = {
        "ending_balance", "ending_balance_real", "cagr", "twrr_nominal", "twrr_real",
        "annual_mean_return", "annualized_volatility", "max_drawdown", "max_drawdown_excl_cashflows",
    }
    assert set(response.metrics["percentile_table"].keys()) == expected_keys
    assert "expected_return_by_horizon" in response.risk
    assert "annual_return_probability" in response.risk
    assert "loss_probability" in response.risk


def test_multistage_glide_path_request_produces_goals_section_with_glide_path():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
        initial_amount=1_000_000, simulation_period_years=10, tax_treatment="pre_tax",
        simulation_model="historical", n_paths=1000, seed=1, rebalancing="annual",
        bootstrap_model="single_year", use_full_history=True, sequence_of_returns_risk=0,
        inflation_model="parameterized", inflation_mean=0.03, inflation_volatility=0.01,
        multi_goal_enabled=True,
        goals=[{"purpose": "Retirement", "is_withdrawal": True, "amount": 5000.0,
                "inflation_adjusted": False, "frequency": "monthly", "starts_year": 5, "ends_year": 10}],
        years_to_retirement=5, glide_path_years=3,
        retirement_holdings=[Holding(proj_id="M0027_2535", weight=20.0), Holding(proj_id="M0209_2548", weight=80.0)],
    )
    response = run_simulation(req, _returns_df())
    assert response.goals is not None
    assert "glide_path" in response.goals
    assert response.goals["glide_path"]["years"] == list(range(11))
    allocations = response.goals["glide_path"]["allocations"]
    # Semantics match frontend/src/api/mockData.ts: hold the start allocation (0.60)
    # steady until years_to_retirement - glide_path_years = 5 - 3 = 2, then transition
    # linearly so the retirement allocation (0.20) is fully reached exactly AT
    # years_to_retirement=5, and held there afterward.
    assert allocations["M0027_2535"][0] == 0.6
    assert allocations["M0027_2535"][2] == 0.6  # transition hasn't started yet
    assert allocations["M0027_2535"][5] == 0.2  # fully transitioned exactly at retirement
    assert allocations["M0027_2535"][10] == 0.2  # holds steady after retirement
    assert "cashflows_nominal" in response.goals

    # Regression: the displayed chart and the actual simulation must use the exact same
    # weight-at-year formula (engine.goals.glide_path_weights), so they can never
    # disagree -- cross-check the displayed values directly against that shared function
    # rather than against a second, independently-maintained formula.
    from backend.app.engine.goals import glide_path_weights
    start_weights = np.array([0.6, 0.4])
    retirement_weights = np.array([0.2, 0.8])
    for y in [0, 2, 3, 4, 5, 10]:
        expected = glide_path_weights(start_weights, retirement_weights, years_to_retirement=5, glide_path_years=3, year=y)
        assert allocations["M0027_2535"][y] == pytest.approx(expected[0])
        assert allocations["M0209_2548"][y] == pytest.approx(expected[1])
