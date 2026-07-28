import numpy as np
import pandas as pd


def simulate_historical(returns_df: pd.DataFrame, weights: np.ndarray, config: dict) -> np.ndarray:
    rng = np.random.default_rng(config["seed"])
    annual_returns = returns_df.groupby(returns_df.index.year).apply(lambda g: (1 + g).prod() - 1)
    portfolio_annual_returns = annual_returns.to_numpy() @ weights
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    sampled = rng.choice(portfolio_annual_returns, size=(n_paths, n_years), replace=True)
    growth = np.cumprod(1 + sampled, axis=1)
    paths = np.hstack([np.ones((n_paths, 1)), growth])
    return paths
