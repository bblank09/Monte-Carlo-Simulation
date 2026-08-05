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


def test_glide_path_years_zero_is_rejected_at_validation_time():
    # glide_path_years=0 previously reached the engine and raised ZeroDivisionError
    # (HTTP 500) inside the glide-path weight formula. A 0-year glide path is a
    # degenerate/meaningless input, so it's rejected at the schema boundary (422)
    # instead of being silently handled deep in engine code.
    with pytest.raises(ValidationError):
        SimulateRequest(
            holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
            initial_amount=1_000_000,
            simulation_period_years=10,
            tax_treatment="pre_tax",
            simulation_model="historical",
            n_paths=1000,
            seed=42,
            bootstrap_model="single_year",
            use_full_history=True,
            sequence_of_returns_risk=0,
            rebalancing="annual",
            inflation_model="historical",
            multi_goal_enabled=True,
            goals=[{"purpose": "Retirement", "is_withdrawal": True, "amount": 1000.0,
                    "inflation_adjusted": False, "frequency": "monthly", "starts_year": 1, "ends_year": 5}],
            years_to_retirement=5,
            glide_path_years=0,
            retirement_holdings=[Holding(proj_id="M0027_2535", weight=20.0), Holding(proj_id="M0209_2548", weight=80.0)],
        )


def test_sequence_of_returns_risk_rejected_with_glide_path():
    # Under glide-path multistage composition, each year is simulated in isolation
    # (simulation_period_years=1 per call), so the sequence-of-returns-risk stress
    # test's "reorder the worst N years to the front" has no array longer than 1 to
    # reorder -- a silent no-op. Reject the combination at the schema boundary instead.
    with pytest.raises(ValidationError):
        SimulateRequest(
            holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
            initial_amount=1_000_000,
            simulation_period_years=10,
            tax_treatment="pre_tax",
            simulation_model="historical",
            n_paths=1000,
            seed=42,
            bootstrap_model="single_year",
            use_full_history=True,
            sequence_of_returns_risk=3,
            rebalancing="annual",
            inflation_model="historical",
            multi_goal_enabled=True,
            goals=[{"purpose": "Retirement", "is_withdrawal": True, "amount": 1000.0,
                    "inflation_adjusted": False, "frequency": "monthly", "starts_year": 1, "ends_year": 5}],
            years_to_retirement=5,
            glide_path_years=2,
            retirement_holdings=[Holding(proj_id="M0027_2535", weight=20.0), Holding(proj_id="M0209_2548", weight=80.0)],
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
