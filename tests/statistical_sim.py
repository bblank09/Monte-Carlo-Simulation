import numpy as np
from gbm_engine import simulate_gbm_paths
from forecasted_sim import _garch_annual_returns


def simulate_statistical(mu, sigma, weights, config, returns_df=None):
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    if config["time_series_model"] == "normal":
        asset_paths = simulate_gbm_paths(
            S0=np.ones(len(weights)), mu=mu, sigma=sigma,
            n_years=n_years, steps_per_year=252, n_paths=n_paths, seed=config["seed"],
        )
        portfolio_paths = asset_paths @ weights
        annual_idx = np.arange(0, n_years * 252 + 1, 252)
        return portfolio_paths[:, annual_idx]
    elif config["time_series_model"] == "garch":
        rng = np.random.default_rng(config["seed"])
        port_mu = weights @ mu
        annual_returns = _garch_annual_returns(returns_df, weights, port_mu, n_years, n_paths, rng)
        growth = np.cumprod(1 + annual_returns, axis=1)
        return np.hstack([np.ones((n_paths, 1)), growth])
    else:
        raise ValueError("unknown time_series_model: " + str(config["time_series_model"]))
