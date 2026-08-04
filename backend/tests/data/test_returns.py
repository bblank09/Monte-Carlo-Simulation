import numpy as np
import pandas as pd
from backend.app.data.returns import build_price_panel, log_returns, estimate_mu_sigma


def test_build_price_panel_pivots_and_ffills():
    nav_df = pd.DataFrame({
        "nav_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"] * 1),
        "proj_id": ["A", "A", "A"],
        "last_val": [10.0, 10.5, 11.0],
    })
    panel = build_price_panel(nav_df)
    assert list(panel.columns) == ["A"]
    assert panel.loc["2024-01-02", "A"] == 10.5


def test_log_returns_and_estimate_mu_sigma():
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    panel = pd.DataFrame({"A": [10, 10.1, 10.2, 10.15, 10.3]}, index=idx)
    returns = log_returns(panel)
    assert len(returns) == 4
    mu, sigma = estimate_mu_sigma(returns, periods_per_year=252)
    assert mu.shape == (1,)
    assert sigma.shape == (1, 1)
