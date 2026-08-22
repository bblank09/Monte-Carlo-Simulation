import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError
from typing import Any

from backend.app.data.returns import build_price_panel
from backend.app.core.errors import AppHTTPException
from backend.app.domain.schemas import Holding, SimulateRequest
from backend.app.engine.forecasted import simulate_forecasted
from backend.app.engine.historical import simulate_historical
from backend.app.engine.orchestrator import _simulate_inflation_draws, run_simulation
from backend.app.engine.results import correlation_and_returns_table, survival_series


def _request(**overrides) -> SimulateRequest:
    values: dict[str, Any] = {
        "holdings": [Holding(proj_id="A", weight=100.0)],
        "initial_amount": 100_000.0,
        "simulation_period_years": 5,
        "tax_treatment": "pre_tax",
        "simulation_model": "parameterized",
        "n_paths": 1000,
        "seed": 123,
        "rebalancing": "none",
        "distribution": "normal",
        "expected_return": 0.05,
        "expected_volatility": 0.10,
        "inflation_model": "parameterized",
        "inflation_mean": 0.03,
        "inflation_volatility": 0.01,
    }
    values.update(overrides)
    return SimulateRequest(**values)


def _returns() -> pd.DataFrame:
    return pd.DataFrame(
        {"A": np.full(30, 0.001)},
        index=pd.date_range("2018-01-01", periods=30, freq="D"),
    )


def test_historical_compounds_log_returns_as_simple_returns():
    returns = pd.DataFrame(
        {"A": [np.log(1.10)]},
        index=pd.to_datetime(["2020-01-02"]),
    )

    paths = simulate_historical(
        returns,
        np.array([1.0]),
        {"seed": 7, "simulation_period_years": 1, "n_paths": 1, "bootstrap_model": "single_year"},
    )

    assert paths[0, -1] == pytest.approx(1.10)


def test_forecasted_normal_compounds_log_mu_as_simple_return():
    paths = simulate_forecasted(
        np.array([np.log(1.10)]),
        np.array([[0.0]]),
        np.array([1.0]),
        {"seed": 7, "simulation_period_years": 1, "n_paths": 1, "time_series_model": "normal"},
    )

    assert paths[0, -1] == pytest.approx(1.10)


def test_correlation_table_compounds_log_returns_as_simple_returns():
    returns = pd.DataFrame({"A": [np.log(1.10)]})

    stats = correlation_and_returns_table(returns, ["A"], periods_per_year=1)["stats"]["A"]

    assert stats["cagr"] == pytest.approx(0.10)


def test_after_tax_requires_rate_and_reduces_positive_returns():
    with pytest.raises(ValidationError):
        _request(tax_treatment="after_tax")

    before_tax = run_simulation(_request(), _returns())
    after_tax = run_simulation(_request(tax_treatment="after_tax", tax_rate=0.20), _returns())

    assert after_tax.overview["median_ending_balance"] < before_tax.overview["median_ending_balance"]


def test_unsupported_cashflow_modes_are_rejected_instead_of_falling_back():
    for mode in ("rolling_average_spending", "geometric_spending", "withdraw_life_expectancy"):
        with pytest.raises(ValidationError):
            _request(cashflow_mode=mode, cashflow_amount=1000.0)


def test_rebalancing_is_rejected_for_portfolio_level_models():
    with pytest.raises(ValidationError):
        _request(rebalancing="annual")


def test_student_t_requires_more_than_two_degrees_of_freedom():
    with pytest.raises(ValidationError):
        _request(distribution="fat_tailed", degrees_of_freedom=2.0)


def test_named_goals_validate_amount_and_year_order():
    with pytest.raises(ValidationError):
        _request(
            multi_goal_enabled=True,
            goals=[
                {
                    "purpose": "",
                    "is_withdrawal": True,
                    "amount": -1.0,
                    "inflation_adjusted": False,
                    "frequency": "annually",
                    "starts_year": 5,
                    "ends_year": 4,
                }
            ],
        )


def test_glide_path_parameters_stay_within_the_simulation_horizon():
    with pytest.raises(ValidationError):
        _request(
            simulation_period_years=10,
            multi_goal_enabled=True,
            goals=[
                {
                    "purpose": "Retirement",
                    "is_withdrawal": True,
                    "amount": 1_000.0,
                    "inflation_adjusted": False,
                    "frequency": "annually",
                    "starts_year": 1,
                    "ends_year": 10,
                }
            ],
            years_to_retirement=11,
            glide_path_years=5,
            retirement_holdings=[Holding(proj_id="A", weight=100.0)],
        )


def test_glide_path_retirement_allocation_uses_the_same_funds():
    with pytest.raises(ValidationError):
        _request(
            multi_goal_enabled=True,
            goals=[
                {
                    "purpose": "Retirement",
                    "is_withdrawal": True,
                    "amount": 1_000.0,
                    "inflation_adjusted": False,
                    "frequency": "annually",
                    "starts_year": 1,
                    "ends_year": 5,
                }
            ],
            years_to_retirement=3,
            glide_path_years=2,
            retirement_holdings=[Holding(proj_id="B", weight=100.0)],
        )


def test_retirement_holdings_are_canonicalized_to_primary_holding_order():
    request = _request(
        holdings=[Holding(proj_id="A", weight=60.0), Holding(proj_id="B", weight=40.0)],
        multi_goal_enabled=True,
        goals=[
            {
                "purpose": "Retirement",
                "is_withdrawal": True,
                "amount": 1_000.0,
                "inflation_adjusted": False,
                "frequency": "annually",
                "starts_year": 1,
                "ends_year": 5,
            }
        ],
        years_to_retirement=3,
        glide_path_years=2,
        retirement_holdings=[Holding(proj_id="B", weight=80.0), Holding(proj_id="A", weight=20.0)],
    )

    assert [holding.proj_id for holding in request.retirement_holdings or []] == ["A", "B"]
    assert [holding.weight for holding in request.retirement_holdings or []] == [20.0, 80.0]


@pytest.mark.parametrize("model", ["forecasted", "statistical", "parameterized"])
def test_non_historical_models_ignore_historical_data_window_flag(model):
    overrides: dict[str, Any] = {"simulation_model": model, "use_full_history": False}
    if model in {"forecasted", "statistical"}:
        overrides["time_series_model"] = "normal"

    request = _request(**overrides)

    assert request.use_full_history is None


def test_historical_inflation_samples_empirical_cpi_observations():
    request = _request(inflation_model="historical")

    draws = _simulate_inflation_draws(request)
    expected_observations = np.array(
        [0.0328, 0.0381, 0.0302, 0.0218, 0.0190, -0.0090, 0.0019, 0.0067,
         0.0106, 0.0071, -0.0085, 0.0123, 0.0608, 0.0123, 0.0040]
    )

    assert np.isin(draws, expected_observations).all()


def test_price_panel_deduplicates_nav_observations_before_pivoting():
    nav = pd.DataFrame(
        {
            "proj_id": ["A", "A", "B"],
            "nav_date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-01"]),
            "last_val": [10.0, 10.5, 20.0],
        }
    )

    panel = build_price_panel(nav)

    assert panel.loc[pd.Timestamp("2024-01-01"), "A"] == 10.5


def test_limited_history_window_is_derived_from_simulation_horizon():
    from backend.app.api.simulate import nav_date_window

    assert nav_date_window(pd.Timestamp("2026-08-14"), 5, False) == (
        "2021-08-14",
        "2026-08-14",
    )
    assert nav_date_window(pd.Timestamp("2026-08-14"), 5, True) == (
        "2000-01-01",
        "2026-08-14",
    )


def test_load_nav_returns_rejects_history_shorter_than_the_usable_minimum(monkeypatch):
    from backend.app.api import simulate as simulate_api

    monkeypatch.setattr(
        simulate_api,
        "get_daily_nav",
        lambda *_args: pd.DataFrame(
            {
                "nav_date": [pd.Timestamp("2026-01-02")],
                "proj_id": ["A"],
                "last_val": [100.0],
            }
        ),
    )

    with pytest.raises(AppHTTPException) as exc_info:
        simulate_api.load_nav_returns(["A"], simulation_period_years=5, use_full_history=True)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "INSUFFICIENT_NAV_HISTORY"
    assert "at least" in str(exc_info.value.detail)


def test_parameterized_simulation_does_not_require_nav_returns():
    response = run_simulation(_request(), pd.DataFrame(columns=["A"]))

    assert response.metrics["percentile_table"]["ending_balance"][50] > 0
    assert response.risk["correlation_and_returns"]["available"] is False


def test_survival_series_is_cumulative_and_does_not_recover_after_zero():
    paths = np.array([[100.0, 0.0, 0.0, 100.0]], dtype=float)

    assert np.allclose(survival_series(paths), [1.0, 0.0, 0.0, 0.0])


def test_overview_full_horizon_survival_is_distinct_from_terminal_positivity(monkeypatch):
    import backend.app.engine.orchestrator as orchestrator

    paths = np.tile(np.array([1.0, 0.0, 0.0, 1.0, 1.0, 1.0]), (1000, 1))
    monkeypatch.setattr(orchestrator, "simulate_parameterized", lambda _config: paths)

    response = run_simulation(_request(), pd.DataFrame(columns=["A"]))

    assert response.overview["survival_rate"] == 0.0
    assert response.overview["terminal_positive_rate"] == 1.0
    assert response.overview["survived_count"] == 0


def test_run_config_contains_inflation_provenance():
    response = run_simulation(_request(inflation_model="historical"), _returns())

    provenance = response.run_config["data_provenance"]
    assert provenance["asset_returns"] == "SEC Open Data NAV cache"
    assert provenance["historical_inflation"]["source"].startswith("https://")
    assert provenance["historical_inflation"]["vintage"] == "2010-2024"


def test_persisted_runs_are_atomic_and_retained_with_a_bounded_history(tmp_path, monkeypatch):
    from backend.app.api import simulate as simulate_api

    monkeypatch.setattr(simulate_api, "RUNS_DIR", tmp_path)
    monkeypatch.setattr(simulate_api, "MAX_PERSISTED_RUNS", 2)
    request = _request()
    for index in range(3):
        simulate_api.persist_run(
            f"run_{index}",
            request,
            {"run_id": f"run_{index}", "value": index},
        )

    assert not (tmp_path / "run_0").exists()
    assert (tmp_path / "run_1" / "request.json").is_file()
    assert (tmp_path / "run_2" / "result.json").is_file()
    assert not list(tmp_path.glob(".*.tmp"))
