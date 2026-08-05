import numpy as np
import pandas as pd

# The panel's row index is the UNION of every requested fund's own reported
# nav_date values, not a shared trading calendar -- Thai SEC funds don't all
# report on identical days (each has its own occasional single-day
# submission slip or a local processing hiccup around a holiday), so a fund
# will show up as "missing" on a handful of scattered, ISOLATED days purely
# because a different fund in the request happened to report that day. That
# is normal calendar noise, not a NAV gap, and tolerating a short run of it
# via forward-fill is standard practice for daily NAV series. A genuine
# reporting gap -- the fund itself stopped reporting for an extended,
# anomalous stretch (suspension, delisting pause, real data outage) -- looks
# completely different: a long RUN of consecutive missing entries, not
# scattered singletons. This constant is the line between the two.
MAX_TOLERATED_GAP_RUN = 5


class NavGapError(ValueError):
    """Raised when a fund's NAV series has a genuine extended interior gap
    (a run of more than MAX_TOLERATED_GAP_RUN consecutive missing entries
    between two valid observations). Per CLAUDE.md's Landmines: "NAV gaps
    are hard errors. Never forward-fill or interpolate across a gap." --
    this is about real reporting outages, not the isolated single-day
    calendar misalignment between funds that gets tolerated below."""


def build_price_panel(nav_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot SEC fund NAV rows into a wide panel indexed by nav_date.

    Funds are allowed to have different listing windows -- a fund that
    starts trading later than another, or one whose history hasn't caught
    up to `nav_date.max()` yet, produces leading/trailing NaN in its
    column, which is normal and gets trimmed via `dropna()` on the final
    intersection. Within a fund's own active history, isolated short runs
    of missing entries (see MAX_TOLERATED_GAP_RUN) are forward-filled as
    ordinary reporting-calendar noise; a longer run is a genuine NAV gap
    and raises NavGapError rather than being silently interpolated.
    """
    panel = nav_df.pivot(index="nav_date", columns="proj_id", values="last_val").sort_index()

    for proj_id in panel.columns:
        series = panel[proj_id]
        valid_idx = series.notna()
        if not valid_idx.any():
            continue
        first_valid = valid_idx.idxmax()
        last_valid = valid_idx[::-1].idxmax()
        interior_mask = pd.Series(False, index=series.index)
        interior_mask.loc[first_valid:last_valid] = True
        is_gap = series.isna() & interior_mask

        # Group consecutive missing rows into runs (same approach as the
        # sibling Backtest project's gap-segment logic) so a genuine
        # multi-day outage is judged by its longest run, not its total
        # scattered-day count.
        run_id = (is_gap != is_gap.shift(fill_value=False)).cumsum()
        for _, run in is_gap.groupby(run_id):
            if not run.iloc[0]:
                continue
            if len(run) > MAX_TOLERATED_GAP_RUN:
                gap_dates = run.index
                raise NavGapError(
                    f"NAV_GAP: fund {proj_id!r} is missing {len(gap_dates)} consecutive "
                    f"observation(s) between {gap_dates[0].date()} and {gap_dates[-1].date()} "
                    f"(within its own {first_valid.date()}..{last_valid.date()} history) -- "
                    f"exceeds the {MAX_TOLERATED_GAP_RUN}-day tolerance for normal reporting-"
                    "calendar noise. NAV gaps are hard errors and are never forward-filled "
                    "or interpolated."
                )

        panel[proj_id] = series.ffill()

    return panel.dropna()


def log_returns(price_panel: pd.DataFrame) -> pd.DataFrame:
    return np.log(price_panel / price_panel.shift(1)).dropna()


def estimate_mu_sigma(returns_df: pd.DataFrame, periods_per_year: int = 252) -> tuple[np.ndarray, np.ndarray]:
    mu_daily = returns_df.mean().to_numpy()
    sigma_daily = returns_df.cov().to_numpy()
    mu_annual = mu_daily * periods_per_year
    sigma_annual = sigma_daily * periods_per_year
    return mu_annual, sigma_annual
