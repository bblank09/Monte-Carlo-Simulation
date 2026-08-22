import numpy as np

from backend.app.engine.statistical import simulate_statistical


def test_normal_model_no_rebalancing_matches_buy_and_hold():
    mu = np.array([0.08, 0.04])
    sigma = np.array([[0.04, 0.005], [0.005, 0.02]])
    weights = np.array([0.7, 0.3])
    config = {"seed": 5, "n_paths": 20, "simulation_period_years": 3,
              "time_series_model": "normal", "rebalancing": "none"}
    paths = simulate_statistical(mu, sigma, weights, config)
    assert paths.shape == (20, 4)
    assert np.allclose(paths[:, 0], 1.0)


def test_normal_model_annual_rebalancing_resets_weights_each_year():
    mu = np.array([0.08, 0.04])
    sigma = np.array([[0.04, 0.005], [0.005, 0.02]])
    weights = np.array([0.7, 0.3])
    config = {"seed": 5, "n_paths": 20, "simulation_period_years": 3,
              "time_series_model": "normal", "rebalancing": "annual"}
    paths = simulate_statistical(mu, sigma, weights, config)
    assert paths.shape == (20, 4)
    assert np.all(paths[:, 1:] > 0)


def test_no_rebalancing_and_annual_rebalancing_diverge():
    mu = np.array([0.15, -0.02])
    sigma = np.array([[0.09, 0.0], [0.0, 0.01]])
    weights = np.array([0.5, 0.5])
    config_none = {"seed": 9, "n_paths": 500, "simulation_period_years": 10,
                   "time_series_model": "normal", "rebalancing": "none"}
    config_annual = dict(config_none, rebalancing="annual")
    paths_none = simulate_statistical(mu, sigma, weights, config_none)
    paths_annual = simulate_statistical(mu, sigma, weights, config_annual)
    assert not np.allclose(np.median(paths_none[:, -1]), np.median(paths_annual[:, -1]), rtol=0.01)
