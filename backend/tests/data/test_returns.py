import pandas as pd
import pytest

from backend.app.data.returns import (
    NavGapError,
    build_price_panel,
    estimate_mu_sigma,
    log_returns,
)


def test_build_price_panel_pivots_a_single_fund():
    nav_df = pd.DataFrame({
        "nav_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"] * 1),
        "proj_id": ["A", "A", "A"],
        "last_val": [10.0, 10.5, 11.0],
    })
    panel = build_price_panel(nav_df)
    assert list(panel.columns) == ["A"]
    assert panel.loc["2024-01-02", "A"] == 10.5


def test_build_price_panel_trims_leading_and_trailing_nan_without_erroring():
    # Fund B starts listing later than fund A -- this is a normal join
    # boundary, not a gap, and should just be trimmed via dropna(), not
    # raise NavGapError.
    nav_df = pd.DataFrame({
        "nav_date": pd.to_datetime(
            ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-02", "2024-01-03"]
        ),
        "proj_id": ["A", "A", "A", "B", "B"],
        "last_val": [10.0, 10.5, 11.0, 5.0, 5.2],
    })
    panel = build_price_panel(nav_df)
    assert list(panel.index.strftime("%Y-%m-%d")) == ["2024-01-02", "2024-01-03"]


def test_build_price_panel_tolerates_isolated_single_day_gap():
    # Fund A is missing 2024-01-02 -- a single isolated day sandwiched
    # between two of its own valid observations (fund B's 2024-01-02 row is
    # what puts that date into the joined panel's index at all). Real SEC
    # data has this constantly (each fund has its own occasional one-off
    # reporting slip) -- it's ordinary calendar noise, not a NAV gap, and
    # gets forward-filled rather than rejected.
    nav_df = pd.DataFrame({
        "nav_date": pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-02"]),
        "proj_id": ["A", "A", "B"],
        "last_val": [10.0, 11.0, 5.0],
    })
    panel = build_price_panel(nav_df)
    assert panel.loc["2024-01-02", "A"] == 10.0  # forward-filled from 2024-01-01


def test_build_price_panel_raises_navgaperror_on_extended_interior_gap():
    # Fund A is missing 8 consecutive days -- a genuine reporting outage,
    # well past MAX_TOLERATED_GAP_RUN -- which must be a hard error, never
    # forward-filled.
    nav_df = pd.DataFrame({
        "nav_date": pd.concat([
            pd.Series(["2024-01-01", "2024-01-10"]),  # fund A: only brackets the gap
            pd.Series([f"2024-01-{d:02d}" for d in range(2, 10)]),  # fund B: fills every day in between
        ]).pipe(pd.to_datetime),
        "proj_id": ["A", "A"] + ["B"] * 8,
        "last_val": [10.0, 11.0] + [5.0] * 8,
    })
    with pytest.raises(NavGapError, match="NAV_GAP"):
        build_price_panel(nav_df)


def test_log_returns_and_estimate_mu_sigma():
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    panel = pd.DataFrame({"A": [10, 10.1, 10.2, 10.15, 10.3]}, index=idx)
    returns = log_returns(panel)
    assert len(returns) == 4
    mu, sigma = estimate_mu_sigma(returns, periods_per_year=252)
    assert mu.shape == (1,)
    assert sigma.shape == (1, 1)
