import numpy as np


def apply_cashflow(
    paths: np.ndarray,
    initial_amount: float,
    cashflow: dict,
    inflation_draws: np.ndarray | None = None,
) -> np.ndarray:
    """Apply one annual contribution/withdrawal to normalized growth-factor paths, year
    by year, compounding on the resulting dollar balance each year.

    `cashflow["is_percent"]` selects between two amount interpretations:
    - False (default): `cashflow["amount"]` is a per-occurrence DOLLAR figure, scaled to
      an annual net cashflow by `cashflow["frequency"]` via `_annualized_goal_amount` --
      a "monthly" cashflow actually withdraws/contributes 12x its entered amount per
      year, not 1x.
    - True: `cashflow["amount"]` is a per-occurrence PERCENT-OF-CURRENT-BALANCE figure
      (e.g. 1 means 1%). It is still scaled by `cashflow["frequency"]` the same way, then
      applied against that year's grown balance -- so a path with a larger balance
      withdraws more dollars than a path with a smaller one, unlike the fixed-dollar
      case. This mirrors "withdraw_percent" in the Cashflow selector
      (backend/app/domain/schemas.py's `cashflow_mode`), which used to silently fall
      through to fixed-dollar treatment (a bug: a user picking e.g. "4%" got a $4/year
      withdrawal instead of 4% of their balance) until this was implemented.
    """
    n_paths, n_years_plus_one = paths.shape
    n_years = n_years_plus_one - 1
    growth_factors = paths[:, 1:] / paths[:, :-1]
    sign = -1.0 if cashflow["is_withdrawal"] else 1.0
    is_percent = cashflow.get("is_percent", False)
    annual_rate_or_amount = _annualized_goal_amount(cashflow)
    inflation_factors = _inflation_factors(inflation_draws, n_paths, n_years)
    values = np.empty((n_paths, n_years_plus_one))
    values[:, 0] = initial_amount
    for year in range(n_years):
        grown = values[:, year] * growth_factors[:, year]
        if is_percent:
            amount = grown * (annual_rate_or_amount / 100.0)
        else:
            amount = annual_rate_or_amount * (
                inflation_factors[:, year] if cashflow.get("inflation_adjusted", False) else 1.0
            )
        values[:, year + 1] = np.maximum(grown + sign * amount, 0.0)
    return values


_FREQUENCY_MULTIPLIER = {"monthly": 12, "quarterly": 4, "annually": 1}


def _annualized_goal_amount(goal: dict) -> float:
    """A goal's `amount` is a per-occurrence figure; scale it to an annual net cashflow
    by its frequency. A goal marked "monthly" withdraws 12x its entered amount per year,
    not 1x -- the frontend's per-goal Frequency selector must actually change simulated
    behavior, not just be a display label."""
    return goal["amount"] * _FREQUENCY_MULTIPLIER[goal["frequency"]]


def _inflation_factors(
    inflation_draws: np.ndarray | None,
    n_paths: int,
    n_years: int,
) -> np.ndarray:
    """Return a cumulative inflation multiplier for every path and year."""
    if inflation_draws is None:
        return np.ones((n_paths, n_years))
    expected_shape = (n_paths, n_years)
    if inflation_draws.shape != expected_shape:
        raise ValueError(f"inflation_draws must have shape {expected_shape}, got {inflation_draws.shape}")
    return np.cumprod(1.0 + inflation_draws, axis=1)


def apply_named_goals(
    paths: np.ndarray,
    initial_amount: float,
    goals: list[dict],
    inflation_draws: np.ndarray | None = None,
) -> tuple[np.ndarray, list[dict]]:
    """Apply multiple named goals in chronological order (by starts_year), tracking a
    per-goal success rate: the fraction of paths whose balance stayed >= 0 throughout the
    goal's active window."""
    n_paths, n_years_plus_one = paths.shape
    n_years = n_years_plus_one - 1
    growth_factors = paths[:, 1:] / paths[:, :-1]
    inflation_factors = _inflation_factors(inflation_draws, n_paths, n_years)
    values = np.empty((n_paths, n_years_plus_one))
    values[:, 0] = initial_amount
    solvent = np.ones(n_paths, dtype=bool)
    goal_solvent_tracking = {id(g): np.ones(n_paths, dtype=bool) for g in goals}

    for year in range(n_years):
        grown = values[:, year] * growth_factors[:, year]
        net_cashflow = np.zeros(n_paths)
        for goal in goals:
            # `year` indexes the transition that LANDS at balance year (year + 1), so a
            # goal active for calendar years [starts_year, ends_year] inclusive fires on
            # every transition whose landing year falls in that inclusive range --
            # equivalently `starts_year - 1 <= year < ends_year`. Comparing `year` itself
            # against `starts_year` (i.e. `starts_year <= year < ends_year`) silently
            # drops the very first withdrawal/contribution year whenever starts_year >= 1
            # (starts_year == 0 is unaffected since year is never negative -- note
            # this means starts_year=0 and starts_year=1 both resolve to the same
            # `-1 <= year` / `0 <= year` lower bound and therefore collide on the
            # same first transition (year=0, landing at balance-year 1). This is
            # accepted as intentional: year 0 is the initial balance before any
            # growth has occurred, so a goal cannot meaningfully start "in" year 0
            # vs. year 1 -- both mean "active from the very first transition".)
            if goal["starts_year"] - 1 <= year < goal["ends_year"]:
                sign = -1.0 if goal["is_withdrawal"] else 1.0
                if goal.get("inflation_adjusted", False):
                    net_cashflow += sign * _annualized_goal_amount(goal) * inflation_factors[:, year]
                else:
                    net_cashflow += sign * _annualized_goal_amount(goal)
        new_balance = grown + net_cashflow
        solvent &= new_balance >= 0
        values[:, year + 1] = np.maximum(new_balance, 0.0)
        for goal in goals:
            # `year` indexes the transition that LANDS at balance year (year + 1), so a
            # goal active for calendar years [starts_year, ends_year] inclusive fires on
            # every transition whose landing year falls in that inclusive range --
            # equivalently `starts_year - 1 <= year < ends_year`. Comparing `year` itself
            # against `starts_year` (i.e. `starts_year <= year < ends_year`) silently
            # drops the very first withdrawal/contribution year whenever starts_year >= 1
            # (starts_year == 0 is unaffected since year is never negative -- note
            # this means starts_year=0 and starts_year=1 both resolve to the same
            # `-1 <= year` / `0 <= year` lower bound and therefore collide on the
            # same first transition (year=0, landing at balance-year 1). This is
            # accepted as intentional: year 0 is the initial balance before any
            # growth has occurred, so a goal cannot meaningfully start "in" year 0
            # vs. year 1 -- both mean "active from the very first transition".)
            if goal["starts_year"] - 1 <= year < goal["ends_year"]:
                goal_solvent_tracking[id(goal)] &= solvent

    summary = []
    for goal in goals:
        summary.append({
            "purpose": goal["purpose"],
            "success_rate": float(goal_solvent_tracking[id(goal)].mean()),
        })
    return values, summary


def glide_path_weights(
    start_weights: np.ndarray, end_weights: np.ndarray,
    years_to_retirement: int, glide_path_years: int, year: int,
) -> np.ndarray:
    """Single source of truth for the glide-path allocation at a given year, used both by
    `glide_path_orchestration.simulate_with_glide_path` (drives the actual per-year
    simulation) and by `orchestrator.py`'s displayed `goals.glide_path` chart data --
    having both call this one function is what guarantees the chart the user sees can
    never drift from the allocation the simulation actually used.

    Matches the schedule already shipped in `frontend/src/api/mockData.ts`: hold the
    starting allocation steady until `years_to_retirement - glide_path_years`, then
    transition linearly so the retirement allocation is fully reached exactly AT
    `years_to_retirement`, holding there afterward. `glide_path_years <= 0` is a
    degenerate input (no transition window) and is treated as already fully
    transitioned."""
    if glide_path_years <= 0:
        return end_weights
    if year <= years_to_retirement:
        progress = min(1.0, (years_to_retirement - year) / glide_path_years)
        return start_weights * progress + end_weights * (1 - progress)
    return end_weights


def build_cashflow_series(paths: np.ndarray, initial_amount: float, goals: list[dict], inflation_draws: np.ndarray | None = None) -> dict:
    """Build cashflow values with an explicit Year 0..N axis.

    Year 0 is the initial balance before the first growth transition. Cashflows are
    therefore written to the balance year in which they occur, keeping the API, chart,
    and mock convention identical.
    """
    n_years = paths.shape[1] - 1
    years = list(range(n_years + 1))
    nominal = np.zeros(n_years + 1)
    inflation_factors = _inflation_factors(inflation_draws, paths.shape[0], n_years)
    median_inflation_factors = np.median(inflation_factors, axis=0)
    for transition_year in range(n_years):
        calendar_year = transition_year + 1
        net = 0.0
        for goal in goals:
            # A goal starting at Year 0 is active from the first simulated transition;
            # there is no pre-growth cashflow at the initial balance point.
            start_year = max(1, goal["starts_year"])
            if start_year <= calendar_year <= goal["ends_year"]:
                sign = -1.0 if goal["is_withdrawal"] else 1.0
                amount = _annualized_goal_amount(goal)
                if goal.get("inflation_adjusted", False):
                    amount *= median_inflation_factors[transition_year]
                net += sign * amount
        nominal[calendar_year] = net

    if inflation_draws is None:
        present_dollar = nominal.copy()
    else:
        present_dollar = np.zeros_like(nominal)
        present_dollar[1:] = nominal[1:] / median_inflation_factors

    return {
        "years": years,
        "cashflows_nominal": nominal.tolist(),
        "cashflows_present_dollar": present_dollar.tolist(),
    }
