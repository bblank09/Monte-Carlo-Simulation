import numpy as np
from backend.app.engine.goals import apply_cashflow, apply_named_goals, glide_path_weights, build_cashflow_series


def test_apply_cashflow_withdrawal_reduces_balance():
    paths = np.ones((3, 4))  # flat growth, 3 years
    values = apply_cashflow(paths, initial_amount=1000.0, cashflow={
        "amount": 100.0, "is_withdrawal": True, "inflation_adjusted": False, "frequency": "annually",
    })
    assert values[0, 0] == 1000.0
    assert values[0, 1] < values[0, 0]


def test_apply_cashflow_contribution_increases_balance():
    paths = np.ones((3, 4))
    values = apply_cashflow(paths, initial_amount=1000.0, cashflow={
        "amount": 100.0, "is_withdrawal": False, "inflation_adjusted": False, "frequency": "annually",
    })
    assert values[0, 1] > values[0, 0]


def test_apply_named_goals_reports_success_rate():
    paths = np.ones((10, 4))
    goals = [
        {"purpose": "Savings", "amount": 50.0, "is_withdrawal": False, "inflation_adjusted": False,
         "frequency": "annually", "starts_year": 0, "ends_year": 3},
    ]
    values, summary = apply_named_goals(paths, initial_amount=1000.0, goals=goals)
    assert values.shape == (10, 4)
    assert summary[0]["purpose"] == "Savings"
    assert summary[0]["success_rate"] == 1.0  # contributions only, can't go negative


def test_apply_named_goals_scales_amount_by_frequency():
    paths = np.ones((5, 3))
    goals_monthly = [
        {"purpose": "Monthly contribution", "amount": 10.0, "is_withdrawal": False, "inflation_adjusted": False,
         "frequency": "monthly", "starts_year": 0, "ends_year": 2},
    ]
    goals_annual = [
        {"purpose": "Annual contribution", "amount": 10.0, "is_withdrawal": False, "inflation_adjusted": False,
         "frequency": "annually", "starts_year": 0, "ends_year": 2},
    ]
    values_monthly, _ = apply_named_goals(paths, initial_amount=1000.0, goals=goals_monthly)
    values_annual, _ = apply_named_goals(paths, initial_amount=1000.0, goals=goals_annual)
    # A monthly $10 contribution is $120/yr, 12x an annual $10 contribution -- the
    # monthly-goal path must end up materially higher than the annual-goal path.
    assert values_monthly[0, -1] > values_annual[0, -1]
    assert np.isclose(values_monthly[0, 1] - 1000.0, 120.0)
    assert np.isclose(values_annual[0, 1] - 1000.0, 10.0)


def test_glide_path_interpolates_linearly_then_clamps():
    start = np.array([0.8, 0.2])
    end = np.array([0.2, 0.8])
    mid = glide_path_weights(start, end, glide_path_years=10, year=5)
    assert np.allclose(mid, [0.5, 0.5])
    after = glide_path_weights(start, end, glide_path_years=10, year=15)
    assert np.allclose(after, end)


def test_build_cashflow_series_nominal_only_without_inflation():
    paths = np.ones((5, 4))
    goals = [
        {"purpose": "Withdrawal", "amount": 100.0, "is_withdrawal": True, "inflation_adjusted": False,
         "frequency": "annually", "starts_year": 0, "ends_year": 3},
    ]
    series = build_cashflow_series(paths, initial_amount=1000.0, goals=goals)
    assert len(series["cashflows_nominal"]) == 3
    assert series["cashflows_nominal"][0] == -100.0
    assert series["cashflows_present_dollar"] == series["cashflows_nominal"]


def test_build_cashflow_series_present_dollar_discounts_with_inflation():
    paths = np.ones((5, 4))
    goals = [
        {"purpose": "Withdrawal", "amount": 100.0, "is_withdrawal": True, "inflation_adjusted": False,
         "frequency": "annually", "starts_year": 0, "ends_year": 3},
    ]
    inflation_draws = np.full((5, 3), 0.10)  # 10%/yr every path, every year
    series = build_cashflow_series(paths, initial_amount=1000.0, goals=goals, inflation_draws=inflation_draws)
    # Year 2 (index 1) present-dollar value is discounted by (1.10)^2 vs. nominal --
    # for a negative (withdrawal) cashflow, "discounted" means smaller magnitude
    # (closer to zero), not a smaller signed value.
    assert abs(series["cashflows_present_dollar"][1]) < abs(series["cashflows_nominal"][1])
