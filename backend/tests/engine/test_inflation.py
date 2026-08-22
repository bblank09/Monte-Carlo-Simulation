import numpy as np

from backend.app.engine.inflation import simulate_inflation


def test_parameterized_inflation_shape_and_mean():
    config = {"inflation_model": "parameterized", "inflation_mean": 0.03, "inflation_volatility": 0.01}
    rng = np.random.default_rng(11)
    draws = simulate_inflation(config, n_paths=5000, n_years=10, rng=rng)
    assert draws.shape == (5000, 10)
    assert abs(draws.mean() - 0.03) < 0.005


def test_historical_inflation_resamples_supplied_series():
    cpi_series = np.array([0.02, 0.025, 0.03, 0.04, 0.015])
    config = {"inflation_model": "historical", "cpi_returns": cpi_series}
    rng = np.random.default_rng(12)
    draws = simulate_inflation(config, n_paths=200, n_years=6, rng=rng)
    assert draws.shape == (200, 6)
    assert set(np.unique(draws)).issubset(set(cpi_series))


def test_unknown_model_raises():
    import pytest
    with pytest.raises(ValueError):
        simulate_inflation({"inflation_model": "bogus"}, n_paths=1, n_years=1)
