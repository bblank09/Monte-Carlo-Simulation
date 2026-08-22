import numpy as np

from backend.app.engine.gbm import simulate_gbm_paths


def test_shape_and_start_value():
    S0 = np.array([1.0, 1.0])
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.01], [0.01, 0.02]])
    paths = simulate_gbm_paths(S0, mu, sigma, n_years=2, steps_per_year=252, n_paths=100, seed=42)
    assert paths.shape == (100, 505, 2)
    assert np.allclose(paths[:, 0, :], S0)


def test_reproducible_with_seed():
    S0 = np.array([1.0])
    mu = np.array([0.07])
    sigma = np.array([[0.03]])
    a = simulate_gbm_paths(S0, mu, sigma, n_years=1, steps_per_year=12, n_paths=10, seed=7)
    b = simulate_gbm_paths(S0, mu, sigma, n_years=1, steps_per_year=12, n_paths=10, seed=7)
    assert np.array_equal(a, b)
