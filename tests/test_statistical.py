import numpy as np

from backend.app.engine.statistical import simulate_statistical


def test_statistical_uses_gbm_engine_and_matches_moments():
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.006], [0.006, 0.0225]])
    weights = np.array([0.5, 0.5])
    config = {"simulation_period_years": 1, "n_paths": 20000, "seed": 5, "time_series_model": "normal"}
    paths = simulate_statistical(mu, sigma, weights, config)
    assert paths.shape == (20000, 2)
    port_mu = weights @ mu
    port_var = weights @ sigma @ weights
    log_ret = np.log(paths[:, -1])
    assert np.isclose(log_ret.mean(), port_mu - 0.5 * port_var, atol=0.01)
