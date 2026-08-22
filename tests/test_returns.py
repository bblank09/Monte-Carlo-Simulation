import numpy as np
import pandas as pd

from backend.app.data.returns import estimate_mu_sigma, log_returns


def test_log_returns_and_moments():
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    rng = np.random.default_rng(42)
    prices = pd.DataFrame({
        "A": 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 252))),
        "B": 50 * np.exp(np.cumsum(rng.normal(0.0002, 0.015, 252))),
    }, index=dates)
    rets = log_returns(prices)
    assert rets.shape == (251, 2)
    mu, sigma = estimate_mu_sigma(rets, periods_per_year=252)
    assert mu.shape == (2,)
    assert sigma.shape == (2, 2)
    assert np.allclose(sigma, sigma.T)  # covariance matrix must be symmetric
    assert np.all(np.linalg.eigvalsh(sigma) >= -1e-10)  # positive semi-definite
