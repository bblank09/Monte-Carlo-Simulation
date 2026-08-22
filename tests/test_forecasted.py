import numpy as np
import pandas as pd
import pytest

from backend.app.engine.forecasted import simulate_forecasted


def test_forecasted_garch_shape():
    pytest.importorskip("arch")
    rng = np.random.default_rng(9)
    dates = pd.date_range("2015-01-01", periods=1500, freq="B")
    rets = pd.DataFrame(rng.normal(0.0003, 0.01, (1500, 2)), index=dates, columns=["A", "B"])
    weights = np.array([0.5, 0.5])
    config = {"simulation_period_years": 5, "n_paths": 2000, "seed": 3, "time_series_model": "garch"}
    paths = simulate_forecasted(None, None, weights, config, returns_df=rets)
    assert paths.shape == (2000, 6)


def test_forecasted_normal_shape_and_mean():
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.006], [0.006, 0.0225]])
    weights = np.array([0.5, 0.5])
    config = {"simulation_period_years": 10, "n_paths": 20000, "seed": 3, "time_series_model": "normal"}
    paths = simulate_forecasted(mu, sigma, weights, config)
    assert paths.shape == (20000, 11)
    ending = paths[:, -1]
    assert 1.0 < np.median(ending) < 5.0
