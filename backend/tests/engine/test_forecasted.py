import numpy as np

from backend.app.engine.forecasted import simulate_forecasted


def test_normal_model_shape_and_start():
    mu = np.array([0.08, 0.04])
    sigma = np.array([[0.04, 0.01], [0.01, 0.02]])
    weights = np.array([0.6, 0.4])
    config = {"seed": 3, "n_paths": 40, "simulation_period_years": 8, "time_series_model": "normal"}
    paths = simulate_forecasted(mu, sigma, weights, config)
    assert paths.shape == (40, 9)
    assert np.allclose(paths[:, 0], 1.0)
