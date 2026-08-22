"""Regression tests for the three bug candidates flagged by Phase 4 manual
verification (docs/manual-verification-formula-audit.md, Task 2/4/5):

1. TWRR/CAGR conflation in results.py::percentile_table
2. Sharpe/Sortino numerator/denominator basis mismatch in
   results.py::sharpe_sortino_by_percentile
3. Goal cashflow off-by-one in goals.py::apply_named_goals /
   build_cashflow_series
"""
import numpy as np
import pytest

from backend.app.engine.goals import apply_named_goals, build_cashflow_series
from backend.app.engine.results import (
    percentile_table,
    sharpe_sortino_by_percentile,
    withdrawal_rates_by_percentile,
)


def test_twrr_nominal_strips_cashflow_effect_instead_of_matching_cagr():
    # Pure asset growth: +10%/yr for 2 years -> growth-only CAGR = 10%.
    growth_only_paths = np.array([[1.0, 1.1, 1.21]])
    # The post-cashflow normalized balance path diverges from growth_only_paths
    # because a withdrawal was taken out along the way -- CAGR on THIS array
    # conflates asset performance with the dollar effect of withdrawal timing/size.
    post_cashflow_paths = np.array([[1.0, 0.9, 0.95]])

    table = percentile_table(post_cashflow_paths, initial_amount=1.0, growth_only_paths=growth_only_paths)

    cagr = table["cagr"][50]
    twrr = table["twrr_nominal"][50]

    # CAGR computed on the cashflow-affected balance path.
    assert cagr == pytest_approx(0.95 ** 0.5 - 1)
    # A correct nominal TWRR strips the cashflow's dollar effect -- it should equal
    # the growth-only path's CAGR (10%), not the post-cashflow CAGR, and therefore
    # must differ from `cagr` here.
    assert twrr == pytest_approx(1.21 ** 0.5 - 1)
    assert twrr != cagr


def pytest_approx(value, abs=1e-9):
    return pytest.approx(value, abs=abs)


def test_twrr_real_matches_twrr_nominal_when_inflation_is_zero():
    # Same setup as the twrr_nominal test above: growth_only_paths carries the
    # pure asset-growth path (10%/yr for 2 years), post_cashflow_paths carries
    # the post-withdrawal dollar balance. With exactly zero inflation, real and
    # nominal TWRR must coincide -- both describe the same cashflow-free asset
    # growth, just with a no-op deflator applied to the real one.
    growth_only_paths = np.array([[1.0, 1.1, 1.21]])
    post_cashflow_paths = np.array([[1.0, 0.9, 0.95]])
    zero_inflation = np.zeros((1, 2))

    table = percentile_table(
        post_cashflow_paths,
        initial_amount=1.0,
        inflation_draws=zero_inflation,
        growth_only_paths=growth_only_paths,
    )

    twrr_nominal = table["twrr_nominal"][50]
    twrr_real = table["twrr_real"][50]

    # Correct value: growth-only CAGR (10%), not the post-cashflow-contaminated
    # figure that deflating `ending` (the post-cashflow balance) would produce.
    assert twrr_real == pytest_approx(1.21 ** 0.5 - 1)
    assert twrr_real == pytest_approx(twrr_nominal)


def test_perpetual_withdrawal_rate_uses_arithmetic_mean_not_geometric_cagr():
    # Single path, 2 annual periods: +50% then -50%. Growth factors 1.5, 0.5.
    # Arithmetic mean of per-period returns [0.5, -0.5] is exactly 0.
    # Per-period variance (population) = ((0.5-0)^2 + (-0.5-0)^2) / 2 = 0.25.
    # Correct PWR = arithmetic_mean - 0.5*variance = 0 - 0.5*0.25 = -0.125.
    #
    # The buggy formula instead uses the per-path GEOMETRIC CAGR
    # (0.75 ** 0.5 - 1 ~= -13.4%) as the "mu" term, double-applying the
    # geometric/arithmetic variance-drag correction and producing a materially
    # different (and wrong) PWR.
    paths = np.array([[1.0, 1.5, 0.75]])

    result = withdrawal_rates_by_percentile(paths, n_years=2)

    pwr = result["perpetual_withdrawal_rate"][50]
    assert pwr == pytest_approx(-0.125)


def test_sharpe_uses_same_basis_numerator_and_denominator():
    # Single path, 2 annual periods: +50% then -50%. Growth factors 1.5, 0.5.
    paths = np.array([[1.0, 1.5, 0.75]])

    result = sharpe_sortino_by_percentile(paths, risk_free_rate=0.0)

    # Arithmetic mean of the per-period returns [0.5, -0.5] is exactly 0, so a
    # same-basis Sharpe numerator is 0 and the ratio must be exactly 0 -- even
    # though the geometric CAGR on this path is negative (~-13.4%), which is what
    # the old code used as the numerator and would have produced a nonzero,
    # negative Sharpe.
    assert result["sharpe"][50] == pytest_approx(0.0)
    assert result["sortino"][50] == pytest_approx(0.0)


def test_apply_named_goals_produces_five_withdrawals_for_starts_1_ends_5():
    # 5-year simulation (6 balance points), flat 0% growth so the math is trivial
    # to hand-verify. A goal configured starts_year=1, ends_year=5 is meant to
    # withdraw in every one of the 5 simulated years (1 through 5 inclusive).
    n_years = 5
    paths = np.ones((1, n_years + 1))
    goals = [
        {"purpose": "Retirement", "amount": 100.0, "is_withdrawal": True,
         "inflation_adjusted": False, "frequency": "annually",
         "starts_year": 1, "ends_year": 5},
    ]

    values, _ = apply_named_goals(paths, initial_amount=1000.0, goals=goals)

    # 5 withdrawals of 100 each -> ending balance should be 1000 - 5*100 = 500.
    assert values[0, -1] == pytest_approx(500.0)

    series = build_cashflow_series(paths, initial_amount=1000.0, goals=goals)
    nonzero_years = [v for v in series["cashflows_nominal"] if v != 0.0]
    assert len(nonzero_years) == 5
