import numpy as np


def test_gbm_paths_shape_and_moments():
    from gbm_engine import simulate_gbm_paths
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.01], [0.01, 0.0225]])  # vol 20% and 15%, corr 0.333
    S0 = np.array([100.0, 100.0])
    paths = simulate_gbm_paths(S0, mu, sigma, n_years=1, steps_per_year=252, n_paths=20000, seed=7)
    assert paths.shape == (20000, 253, 2)
    log_returns_1y = np.log(paths[:, -1, :] / paths[:, 0, :])
    sample_mean = log_returns_1y.mean(axis=0)
    sample_cov = np.cov(log_returns_1y.T)
    expected_mean = mu - 0.5 * np.diag(sigma)
    assert np.allclose(sample_mean, expected_mean, atol=0.01)
    assert np.allclose(sample_cov, sigma, atol=0.005)
