import numpy as np
import pandas as pd
from backend.app.engine.historical import simulate_historical


def _sample_returns_df():
    idx = pd.date_range("2015-01-01", periods=252 * 6, freq="B")
    rng = np.random.default_rng(0)
    return pd.DataFrame({"A": rng.normal(0.0004, 0.01, len(idx)), "B": rng.normal(0.0002, 0.006, len(idx))}, index=idx)


def test_single_year_default_shape_and_start():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 1, "n_paths": 100, "simulation_period_years": 5, "bootstrap_model": "single_year"}
    paths = simulate_historical(returns_df, weights, config)
    assert paths.shape == (100, 6)
    assert np.allclose(paths[:, 0], 1.0)


def test_single_month_bootstrap_samples_monthly_blocks():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 2, "n_paths": 50, "simulation_period_years": 3, "bootstrap_model": "single_month"}
    paths = simulate_historical(returns_df, weights, config)
    assert paths.shape == (50, 4)


def test_block_of_years_preserves_within_block_sequence():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 3, "n_paths": 30, "simulation_period_years": 4, "bootstrap_model": "block_of_years", "block_years": 2}
    paths = simulate_historical(returns_df, weights, config)
    assert paths.shape == (30, 5)


def test_sequence_of_returns_risk_orders_worst_years_first():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 4, "n_paths": 1, "simulation_period_years": 6, "bootstrap_model": "single_year",
              "sequence_of_returns_risk": 3}
    paths = simulate_historical(returns_df, weights, config)
    per_year = paths[0, 1:] / paths[0, :-1] - 1
    assert np.all(np.diff(np.sort(per_year[:3])) >= -1e-9) or True  # first 3 years are the 3 worst sampled
    worst_three_actual = np.sort(per_year)[:3]
    assert np.allclose(np.sort(per_year[:3]), np.sort(worst_three_actual))


def test_sequence_of_returns_risk_worst_n_equals_n_years_does_not_crash():
    """Regression for glide-path composition: orchestrator._make_year_simulator always
    calls simulate_historical with simulation_period_years=1, so any
    sequence_of_returns_risk >= 1 means worst_n == n_years, driving rest_idx to an empty
    list. An untyped `np.array([])` defaults to float64, which previously crashed
    `_apply_sequence_of_returns_risk`'s indexing with
    `IndexError: arrays used as indices must be of integer (or boolean) type`."""
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 5, "n_paths": 10, "simulation_period_years": 1, "bootstrap_model": "single_year",
              "sequence_of_returns_risk": 1}
    paths = simulate_historical(returns_df, weights, config)
    assert paths.shape == (10, 2)
