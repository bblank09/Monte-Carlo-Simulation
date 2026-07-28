import numpy as np


def simulate_gbm_paths(S0, mu, sigma, n_years, steps_per_year, n_paths, seed=None):
    rng = np.random.default_rng(seed)
    n_assets = len(S0)
    n_steps = n_years * steps_per_year
    dt = 1.0 / steps_per_year
    L = np.linalg.cholesky(sigma)
    drift = (mu - 0.5 * np.diag(sigma)) * dt
    paths = np.empty((n_paths, n_steps + 1, n_assets))
    paths[:, 0, :] = S0
    for t in range(1, n_steps + 1):
        z_indep = rng.standard_normal((n_paths, n_assets))
        z_corr = z_indep @ L.T
        shock = drift + np.sqrt(dt) * z_corr
        paths[:, t, :] = paths[:, t - 1, :] * np.exp(shock)
    return paths
