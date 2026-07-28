import numpy as np
import pandas as pd


def build_price_panel(nav_df: pd.DataFrame, webull_df: pd.DataFrame) -> pd.DataFrame:
    """Combine SEC fund NAV (Thai trading days) and Webull stock closes (US trading days)
    into one wide panel indexed by the union of both calendars, forward-filled."""
    nav_wide = nav_df.pivot(index="nav_date", columns="proj_id", values="last_val")
    webull_wide = webull_df.pivot(index="date", columns="ticker", values="close")
    panel = nav_wide.join(webull_wide, how="outer").sort_index()
    return panel.ffill().dropna()


def log_returns(price_panel: pd.DataFrame) -> pd.DataFrame:
    return np.log(price_panel / price_panel.shift(1)).dropna()


def estimate_mu_sigma(returns_df: pd.DataFrame, periods_per_year: int = 252) -> tuple[np.ndarray, np.ndarray]:
    mu_daily = returns_df.mean().to_numpy()
    sigma_daily = returns_df.cov().to_numpy()
    mu_annual = mu_daily * periods_per_year
    sigma_annual = sigma_daily * periods_per_year
    return mu_annual, sigma_annual
