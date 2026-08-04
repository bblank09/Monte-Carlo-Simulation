import numpy as np
import pandas as pd


def build_price_panel(nav_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot SEC fund NAV rows into a wide panel indexed by nav_date, forward-filled
    within available data. SEC-only: no cross-calendar merge with a second data source."""
    panel = nav_df.pivot(index="nav_date", columns="proj_id", values="last_val").sort_index()
    return panel.ffill().dropna()


def log_returns(price_panel: pd.DataFrame) -> pd.DataFrame:
    return np.log(price_panel / price_panel.shift(1)).dropna()


def estimate_mu_sigma(returns_df: pd.DataFrame, periods_per_year: int = 252) -> tuple[np.ndarray, np.ndarray]:
    mu_daily = returns_df.mean().to_numpy()
    sigma_daily = returns_df.cov().to_numpy()
    mu_annual = mu_daily * periods_per_year
    sigma_annual = sigma_daily * periods_per_year
    return mu_annual, sigma_annual
