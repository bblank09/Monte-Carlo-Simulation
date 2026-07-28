import numpy as np
import pandas as pd


def test_historical_bootstrap_shape():
    from historical_sim import simulate_historical
    rng = np.random.default_rng(1)
    dates = pd.date_range("2015-01-01", periods=1500, freq="B")
    rets = pd.DataFrame(rng.normal(0.0003, 0.01, (1500, 2)), index=dates, columns=["A", "B"])
    config = {"simulation_period_years": 5, "n_paths": 500, "seed": 1, "bootstrap_model": "single_year"}
    weights = np.array([0.6, 0.4])
    paths = simulate_historical(rets, weights, config)
    assert paths.shape == (500, 6)  # 5 years + initial value
    assert np.all(paths[:, 0] == 1.0)  # normalized to start at 1.0
