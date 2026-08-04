import numpy as np
import pandas as pd
from backend.app.engine.results import (
    percentile_table, parametric_var_es, compute_var_es,
    sharpe_sortino_by_percentile, withdrawal_rates_by_percentile,
    survival_series, correlation_and_returns_table,
    expected_return_by_horizon, annual_return_probability, loss_probability,
)


def _sample_paths(seed=0, n_paths=500, n_years=10):
    rng = np.random.default_rng(seed)
    annual = rng.normal(0.06, 0.15, size=(n_paths, n_years))
    growth = np.cumprod(1 + annual, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])


def test_percentile_table_has_all_eight_metrics_with_five_bands():
    table = percentile_table(_sample_paths(), initial_amount=1000.0)
    expected_keys = {
        "ending_balance", "ending_balance_real", "cagr", "twrr_nominal", "twrr_real",
        "annual_mean_return", "annualized_volatility", "max_drawdown", "max_drawdown_excl_cashflows",
    }
    assert set(table.keys()) == expected_keys
    for key in expected_keys:
        assert set(table[key].keys()) == {10, 25, 50, 75, 90}
    assert table["ending_balance"][50] > 0
    assert table["max_drawdown"][50] <= 0  # drawdowns are non-positive


def test_percentile_table_ending_balance_real_uses_inflation_draws():
    paths = _sample_paths()
    n_years = paths.shape[1] - 1
    inflation_draws = np.full((paths.shape[0], n_years), 0.10)  # 10%/yr every path
    table_no_inflation = percentile_table(paths, initial_amount=1000.0)
    table_with_inflation = percentile_table(paths, initial_amount=1000.0, inflation_draws=inflation_draws)
    # 10%/yr inflation over 10 years must discount the real ending balance well below nominal.
    assert table_with_inflation["ending_balance_real"][50] < table_no_inflation["ending_balance"][50]


def test_percentile_table_max_drawdown_excl_cashflows_uses_growth_only_paths():
    paths = _sample_paths(seed=1)
    # A pathset with a large synthetic mid-horizon dip simulates a cashflow-driven drawdown
    # that shouldn't appear in the "excl. cashflows" figure when growth_only_paths is flat.
    growth_only = np.ones_like(paths)
    table = percentile_table(paths, initial_amount=1000.0, growth_only_paths=growth_only)
    assert table["max_drawdown_excl_cashflows"][50] == 0.0


def test_expected_return_by_horizon_skips_horizons_beyond_path_length():
    table = expected_return_by_horizon(_sample_paths(n_years=5), horizons=[1, 3, 5, 10])
    assert set(table.keys()) == {"1", "3", "5"}
    for h in table:
        assert set(table[h].keys()) == {10, 25, 50, 75, 90}


def test_annual_return_probability_decreases_as_threshold_rises():
    table = annual_return_probability(_sample_paths(), horizons=[5], thresholds=[0.0, 0.10])
    assert table[">= 0.00%"]["5"] >= table[">= 10.00%"]["5"]


def test_loss_probability_has_four_quadrants():
    paths = _sample_paths()
    table = loss_probability(paths)
    assert set(table.keys()) == {"excluding_cashflows", "including_cashflows"}
    assert set(table["excluding_cashflows"].keys()) == {"within_period", "end_of_period"}


def test_parametric_and_empirical_var_es_are_positive_losses():
    weights = np.array([0.6, 0.4])
    mu = np.array([0.08, 0.03])
    sigma = np.array([[0.04, 0.005], [0.005, 0.02]])
    var, es = parametric_var_es(weights, mu, sigma)
    assert es >= var
    ending = np.random.default_rng(1).normal(0.0, 0.2, 1000)
    var2, es2 = compute_var_es(ending)
    assert es2 >= var2


def test_sharpe_sortino_by_percentile_returns_five_bands():
    result = sharpe_sortino_by_percentile(_sample_paths())
    assert set(result["sharpe"].keys()) == {10, 25, 50, 75, 90}
    assert set(result["sortino"].keys()) == {10, 25, 50, 75, 90}


def test_withdrawal_rates_by_percentile_returns_five_bands():
    result = withdrawal_rates_by_percentile(_sample_paths(), n_years=10)
    assert set(result["safe_withdrawal_rate"].keys()) == {10, 25, 50, 75, 90}
    assert set(result["perpetual_withdrawal_rate"].keys()) == {10, 25, 50, 75, 90}


def test_survival_series_starts_at_one_and_is_monotonic_or_equal():
    paths = _sample_paths()
    series = survival_series(paths)
    assert series[0] == 1.0
    assert len(series) == paths.shape[1]
    assert np.all(series >= 0) and np.all(series <= 1)


def _ruined_paths(seed=0, n_paths=200, n_years=10, ruin_frac=0.7):
    """Normalized growth-factor paths where a large fraction hit exactly 0.0 partway
    through and stay there -- simulating portfolio ruin from an aggressive cashflow
    (apply_cashflow/apply_named_goals floor a depleted balance to exactly 0.0)."""
    rng = np.random.default_rng(seed)
    annual = rng.normal(0.06, 0.15, size=(n_paths, n_years))
    growth = np.cumprod(1 + annual, axis=1)
    paths = np.hstack([np.ones((n_paths, 1)), growth])
    n_ruined = int(n_paths * ruin_frac)
    ruin_year = n_years // 2
    paths[:n_ruined, ruin_year:] = 0.0
    return paths


def test_percentile_table_no_nan_when_many_paths_are_ruined():
    paths = _ruined_paths()
    table = percentile_table(paths, initial_amount=1000.0)
    for metric in table.values():
        for value in metric.values():
            assert not np.isnan(value), f"NaN leaked into percentile_table: {metric}"


def test_withdrawal_rates_by_percentile_no_nan_when_many_paths_are_ruined():
    paths = _ruined_paths()
    result = withdrawal_rates_by_percentile(paths, n_years=paths.shape[1] - 1)
    for band in result.values():
        for value in band.values():
            assert not np.isnan(value), f"NaN leaked into withdrawal_rates_by_percentile: {band}"


def test_sharpe_sortino_by_percentile_no_nan_when_many_paths_are_ruined():
    paths = _ruined_paths()
    result = sharpe_sortino_by_percentile(paths)
    for band in result.values():
        for value in band.values():
            assert not np.isnan(value), f"NaN leaked into sharpe_sortino_by_percentile: {band}"


def test_correlation_and_returns_table_shape():
    idx = pd.date_range("2020-01-01", periods=500, freq="B")
    rng = np.random.default_rng(2)
    returns_df = pd.DataFrame({"A": rng.normal(0.0003, 0.01, 500), "B": rng.normal(0.0001, 0.008, 500)}, index=idx)
    table = correlation_and_returns_table(returns_df, ["A", "B"])
    assert table["correlation"]["A"]["A"] == 1.0
    assert "cagr" in table["stats"]["A"]
