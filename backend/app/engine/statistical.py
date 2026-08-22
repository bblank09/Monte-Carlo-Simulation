import numpy as np

from backend.app.engine.forecasted import _garch_annual_returns
from backend.app.engine.gbm import simulate_gbm_paths

_REBALANCE_STEPS_PER_YEAR = {"none": None, "annual": 1, "semiannual": 2, "quarterly": 4, "monthly": 12}


def simulate_statistical(mu, sigma, weights, config, returns_df=None):
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    if config["time_series_model"] == "normal":
        asset_paths = simulate_gbm_paths(
            S0=np.ones(len(weights)), mu=mu, sigma=sigma,
            n_years=n_years, steps_per_year=252, n_paths=n_paths, seed=config["seed"],
        )
        rebalancing = config.get("rebalancing", "annual")
        rebalances_per_year = _REBALANCE_STEPS_PER_YEAR.get(rebalancing)
        if rebalances_per_year is None:
            # No rebalancing: weights are applied once, at t=0, to price levels (buy-and-hold,
            # drifting weights thereafter).
            portfolio_paths = asset_paths @ weights
            annual_idx = np.arange(0, n_years * 252 + 1, 252)
            return portfolio_paths[:, annual_idx]
        return _rebalanced_portfolio_values(asset_paths, weights, rebalances_per_year, n_years)
    elif config["time_series_model"] == "garch":
        rng = np.random.default_rng(config["seed"])
        port_mu = weights @ mu
        annual_returns = _garch_annual_returns(returns_df, weights, port_mu, n_years, n_paths, rng)
        growth = np.cumprod(1 + annual_returns, axis=1)
        return np.hstack([np.ones((n_paths, 1)), growth])
    else:
        raise ValueError("unknown time_series_model: " + str(config["time_series_model"]))


def _rebalanced_portfolio_values(asset_paths: np.ndarray, weights: np.ndarray, rebalances_per_year: int, n_years: int) -> np.ndarray:
    """Rebuild portfolio value year-by-year, resetting each asset's weight to its target at
    every rebalance date. Each asset's within-period return between rebalance dates is applied
    to its target-weighted share of the portfolio value at the start of that period."""
    n_paths, n_steps_plus_one, _n_assets = asset_paths.shape
    steps_per_year = (n_steps_plus_one - 1) // n_years
    total_rebalances = rebalances_per_year * n_years
    steps_per_rebalance = steps_per_year // rebalances_per_year
    rebalance_step_indices = [i * steps_per_rebalance for i in range(total_rebalances + 1)]
    rebalance_step_indices[-1] = n_steps_plus_one - 1

    portfolio_value = np.ones(n_paths)
    values_at_period_start = np.tile(weights, (n_paths, 1))  # per-asset dollar allocation at period start
    annual_values = [np.ones(n_paths)]
    for period in range(total_rebalances):
        start_idx = rebalance_step_indices[period]
        end_idx = rebalance_step_indices[period + 1]
        asset_growth = asset_paths[:, end_idx, :] / asset_paths[:, start_idx, :]
        period_end_asset_values = values_at_period_start * asset_growth
        portfolio_value = period_end_asset_values.sum(axis=1)
        values_at_period_start = portfolio_value[:, None] * weights[None, :]
        if (period + 1) % rebalances_per_year == 0:
            annual_values.append(portfolio_value.copy())
    return np.array(annual_values).T
