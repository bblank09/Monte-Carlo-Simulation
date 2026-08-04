import pytest
from pydantic import ValidationError
from backend.app.domain.schemas import SimulateRequest, Holding


def test_valid_historical_request_parses():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
        initial_amount=1_000_000,
        simulation_period_years=30,
        tax_treatment="pre_tax",
        simulation_model="historical",
        n_paths=10000,
        seed=42,
        bootstrap_model="single_year",
        use_full_history=True,
        sequence_of_returns_risk=0,
        rebalancing="annual",
        inflation_model="historical",
    )
    assert req.simulation_model == "historical"
    assert len(req.holdings) == 2


def test_weights_must_sum_to_100():
    with pytest.raises(ValidationError):
        SimulateRequest(
            holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=30.0)],
            initial_amount=1_000_000,
            simulation_period_years=30,
            tax_treatment="pre_tax",
            simulation_model="historical",
            n_paths=10000,
            seed=42,
            rebalancing="annual",
            inflation_model="historical",
        )


def test_parameterized_model_requires_expected_return_and_volatility():
    with pytest.raises(ValidationError):
        SimulateRequest(
            holdings=[Holding(proj_id="M0027_2535", weight=100.0)],
            initial_amount=1_000_000,
            simulation_period_years=10,
            tax_treatment="pre_tax",
            simulation_model="parameterized",
            n_paths=10000,
            seed=42,
            rebalancing="annual",
            inflation_model="parameterized",
            inflation_mean=0.03,
            inflation_volatility=0.01,
            distribution="normal",
        )
