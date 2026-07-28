import numpy as np
from arch import arch_model


def simulate_forecasted(mu, sigma, weights, config, returns_df=None):
    rng = np.random.default_rng(config["seed"])
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    if config["time_series_model"] == "garch":
        port_mu = weights @ mu if mu is not None else float(np.nanmean(returns_df.to_numpy() @ weights)) * 252
        annual_returns = _garch_annual_returns(returns_df, weights, port_mu, n_years, n_paths, rng)
    elif config["time_series_model"] == "normal":
        port_mu = weights @ mu
        port_var = weights @ sigma @ weights
        annual_returns = rng.normal(port_mu, np.sqrt(port_var), size=(n_paths, n_years))
    else:
        raise ValueError(f"unknown time_series_model: {config['time_series_model']}")
    growth = np.cumprod(1 + annual_returns, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])


def _garch_annual_returns(returns_df, weights, port_mu, n_years, n_paths, rng):
    """GARCH(1,1) drives ONLY the time-varying volatility (JA252.5), simulated via the arch
    package with mean="Zero" - the drift (port_mu) is added back explicitly afterwards.

    Why: arch_model's mean="Constant" estimates mu via MLE, which weights observations
    inversely by their time-varying variance (like WLS). On this portfolio's data that
    produced mu=19.9%/year annualized vs. the simple historical mean of 12.2%/year - a huge
    gap that, compounded over a 30-year horizon, exploded into absurd ending balances
    (~$260M median vs. ~$10-20M for the other 3 simulation models). Fixing the mean
    externally keeps GARCH's role scoped to what JA252.5 actually introduces: volatility
    clustering, not a competing estimate of expected return.
    """
    port_returns_daily = returns_df.to_numpy() @ weights
    demeaned_pct = (port_returns_daily - port_returns_daily.mean()) * 100
    am = arch_model(demeaned_pct, vol="Garch", p=1, q=1, dist="normal", mean="Zero")
    res = am.fit(disp="off")
    forecasts = res.forecast(horizon=252 * n_years, method="simulation", simulations=n_paths, reindex=False)
    sim_daily_shock_pct = forecasts.simulations.values[-1] / 100
    daily_mu = port_mu / 252
    sim_daily = daily_mu + sim_daily_shock_pct
    sim_daily = sim_daily.reshape(n_paths, n_years, 252)
    return np.prod(1 + sim_daily, axis=2) - 1
