import numpy as np

from backend.app.engine.goals import (
    apply_cashflow,
    apply_named_goals,
    build_cashflow_series,
    glide_path_weights,
)


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


def test_apply_cashflow_scales_amount_by_frequency():
    paths = np.ones((5, 3))
    monthly = apply_cashflow(paths, initial_amount=1000.0, cashflow={
        "amount": 10.0, "is_withdrawal": False, "inflation_adjusted": False, "frequency": "monthly",
    })
    annual = apply_cashflow(paths, initial_amount=1000.0, cashflow={
        "amount": 10.0, "is_withdrawal": False, "inflation_adjusted": False, "frequency": "annually",
    })
    # A monthly $10 contribution is $120/yr, 12x an annual $10 contribution -- mirrors
    # test_apply_named_goals_scales_amount_by_frequency for the single-cashflow path.
    assert np.isclose(monthly[0, 1] - 1000.0, 120.0)
    assert np.isclose(annual[0, 1] - 1000.0, 10.0)
    assert monthly[0, -1] > annual[0, -1]


def test_apply_cashflow_percent_withdrawal_scales_with_balance():
    # A fixed-dollar withdrawal takes the same amount regardless of balance; a
    # percent-of-balance withdrawal (is_percent=True) must take MORE dollars from a
    # path with a bigger balance -- this is what distinguishes "withdraw_percent" from
    # a bug where it silently behaved like withdraw_fixed.
    paths = np.ones((2, 3))
    values = apply_cashflow(paths, initial_amount=1.0, cashflow={
        "amount": 4.0, "is_withdrawal": True, "is_percent": True,
        "inflation_adjusted": False, "frequency": "annually",
    })
    # Two independent starting balances via a second call, since apply_cashflow takes a
    # single initial_amount for all paths in the batch.
    small = apply_cashflow(np.ones((1, 3)), initial_amount=1_000.0, cashflow={
        "amount": 4.0, "is_withdrawal": True, "is_percent": True,
        "inflation_adjusted": False, "frequency": "annually",
    })
    big = apply_cashflow(np.ones((1, 3)), initial_amount=100_000.0, cashflow={
        "amount": 4.0, "is_withdrawal": True, "is_percent": True,
        "inflation_adjusted": False, "frequency": "annually",
    })
    small_withdrawn = small[0, 0] - small[0, 1]
    big_withdrawn = big[0, 0] - big[0, 1]
    assert np.isclose(small_withdrawn, 40.0)  # 4% of 1,000
    assert np.isclose(big_withdrawn, 4_000.0)  # 4% of 100,000
    assert big_withdrawn > small_withdrawn
    assert values[0, 1] < values[0, 0]  # sanity: still a real withdrawal, not a no-op


def test_apply_cashflow_percent_withdrawal_scales_by_frequency():
    paths = np.ones((2, 3))
    monthly = apply_cashflow(paths, initial_amount=1_000.0, cashflow={
        "amount": 1.0, "is_withdrawal": True, "is_percent": True,
        "inflation_adjusted": False, "frequency": "monthly",
    })
    annual = apply_cashflow(paths, initial_amount=1_000.0, cashflow={
        "amount": 1.0, "is_withdrawal": True, "is_percent": True,
        "inflation_adjusted": False, "frequency": "annually",
    })
    # "1% monthly" is 12% of balance per year, 12x "1% annually" -- same
    # frequency-scaling contract as the fixed-dollar case.
    assert np.isclose(1_000.0 - monthly[0, 1], 120.0)
    assert np.isclose(1_000.0 - annual[0, 1], 10.0)


def test_apply_cashflow_inflation_adjusted_amount_tracks_simulated_inflation():
    paths = np.ones((1, 4))
    inflation_draws = np.full((1, 3), 0.10)
    values = apply_cashflow(paths, initial_amount=1000.0, cashflow={
        "amount": 100.0, "is_withdrawal": True, "inflation_adjusted": True,
        "frequency": "annually",
    }, inflation_draws=inflation_draws)
    # The entered amount is today's dollars, so each future annual withdrawal is
    # increased by the cumulative simulated inflation path: 110, then 121.
    assert np.isclose(values[0, 1], 890.0)
    assert np.isclose(values[0, 2], 769.0)


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


def test_apply_named_goals_inflation_adjusted_amount_tracks_simulated_inflation():
    paths = np.ones((1, 4))
    goals = [
        {"purpose": "Education", "amount": 100.0, "is_withdrawal": True, "inflation_adjusted": True,
         "frequency": "annually", "starts_year": 0, "ends_year": 3},
    ]
    inflation_draws = np.full((1, 3), 0.10)
    values, _ = apply_named_goals(paths, initial_amount=1000.0, goals=goals, inflation_draws=inflation_draws)
    assert np.isclose(values[0, 1], 890.0)
    assert np.isclose(values[0, 2], 769.0)


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


def test_glide_path_holds_then_transitions_to_retirement_year():
    # Matches frontend/src/api/mockData.ts's shipped semantics: hold the start
    # allocation steady until years_to_retirement - glide_path_years, then transition
    # linearly so the retirement allocation is fully reached exactly AT
    # years_to_retirement, holding there afterward.
    start = np.array([0.8, 0.2])
    end = np.array([0.2, 0.8])
    # years_to_retirement=10, glide_path_years=4 -> transition window is [6, 10].
    before_window = glide_path_weights(start, end, years_to_retirement=10, glide_path_years=4, year=3)
    assert np.allclose(before_window, start)
    window_start = glide_path_weights(start, end, years_to_retirement=10, glide_path_years=4, year=6)
    assert np.allclose(window_start, start)
    midpoint = glide_path_weights(start, end, years_to_retirement=10, glide_path_years=4, year=8)
    assert np.allclose(midpoint, [0.5, 0.5])
    at_retirement = glide_path_weights(start, end, years_to_retirement=10, glide_path_years=4, year=10)
    assert np.allclose(at_retirement, end)
    after_retirement = glide_path_weights(start, end, years_to_retirement=10, glide_path_years=4, year=15)
    assert np.allclose(after_retirement, end)


def test_glide_path_years_zero_is_degenerate_and_returns_end_weights():
    start = np.array([0.8, 0.2])
    end = np.array([0.2, 0.8])
    # A 0-year glide path is a degenerate/meaningless transition window; guarded so it
    # can't raise ZeroDivisionError -- treated as "already fully transitioned."
    result = glide_path_weights(start, end, years_to_retirement=5, glide_path_years=0, year=0)
    assert np.allclose(result, end)


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


def test_build_cashflow_series_inflation_adjusted_goal_keeps_real_amount_constant():
    paths = np.ones((5, 4))
    goals = [
        {"purpose": "Education", "amount": 100.0, "is_withdrawal": True, "inflation_adjusted": True,
         "frequency": "annually", "starts_year": 0, "ends_year": 3},
    ]
    inflation_draws = np.full((5, 3), 0.10)
    series = build_cashflow_series(paths, initial_amount=1000.0, goals=goals, inflation_draws=inflation_draws)
    assert np.allclose(series["cashflows_nominal"], [-110.0, -121.0, -133.1])
    assert np.allclose(series["cashflows_present_dollar"], [-100.0, -100.0, -100.0])
