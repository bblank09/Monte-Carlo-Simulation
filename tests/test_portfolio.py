import numpy as np


def test_tangency_and_min_variance_weights_sum_to_one():
    from portfolio_lib import min_variance_weights, tangency_weights
    mu = np.array([0.08, 0.05, 0.10])
    sigma = np.array([
        [0.04, 0.006, 0.01],
        [0.006, 0.0225, 0.004],
        [0.01, 0.004, 0.09],
    ])
    w_min = min_variance_weights(sigma)
    w_tan = tangency_weights(mu, sigma, rf=0.02)
    assert np.isclose(w_min.sum(), 1.0)
    assert np.isclose(w_tan.sum(), 1.0)
    # min-variance portfolio must have lower variance than any single asset
    var_min = w_min @ sigma @ w_min
    assert var_min <= min(np.diag(sigma))
