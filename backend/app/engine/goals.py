import numpy as np


def apply_cashflow(paths: np.ndarray, initial_amount: float, cashflow: dict) -> np.ndarray:
    """Apply one fixed annual contribution/withdrawal to normalized growth-factor paths,
    year by year, compounding on the resulting dollar balance each year."""
    n_paths, n_years_plus_one = paths.shape
    n_years = n_years_plus_one - 1
    growth_factors = paths[:, 1:] / paths[:, :-1]
    sign = -1.0 if cashflow["is_withdrawal"] else 1.0
    amount = cashflow["amount"]
    values = np.empty((n_paths, n_years_plus_one))
    values[:, 0] = initial_amount
    for year in range(n_years):
        grown = values[:, year] * growth_factors[:, year]
        values[:, year + 1] = np.maximum(grown + sign * amount, 0.0)
    return values


_FREQUENCY_MULTIPLIER = {"monthly": 12, "quarterly": 4, "annually": 1}


def _annualized_goal_amount(goal: dict) -> float:
    """A goal's `amount` is a per-occurrence figure; scale it to an annual net cashflow
    by its frequency. A goal marked "monthly" withdraws 12x its entered amount per year,
    not 1x -- the frontend's per-goal Frequency selector must actually change simulated
    behavior, not just be a display label."""
    return goal["amount"] * _FREQUENCY_MULTIPLIER[goal["frequency"]]


def apply_named_goals(paths: np.ndarray, initial_amount: float, goals: list[dict]) -> tuple[np.ndarray, list[dict]]:
    """Apply multiple named goals in chronological order (by starts_year), tracking a
    per-goal success rate: the fraction of paths whose balance stayed >= 0 throughout the
    goal's active window."""
    n_paths, n_years_plus_one = paths.shape
    n_years = n_years_plus_one - 1
    growth_factors = paths[:, 1:] / paths[:, :-1]
    values = np.empty((n_paths, n_years_plus_one))
    values[:, 0] = initial_amount
    solvent = np.ones(n_paths, dtype=bool)
    goal_solvent_tracking = {id(g): np.ones(n_paths, dtype=bool) for g in goals}

    for year in range(n_years):
        grown = values[:, year] * growth_factors[:, year]
        net_cashflow = np.zeros(n_paths)
        for goal in goals:
            if goal["starts_year"] <= year < goal["ends_year"]:
                sign = -1.0 if goal["is_withdrawal"] else 1.0
                net_cashflow += sign * _annualized_goal_amount(goal)
        new_balance = grown + net_cashflow
        solvent &= new_balance >= 0
        values[:, year + 1] = np.maximum(new_balance, 0.0)
        for goal in goals:
            if goal["starts_year"] <= year < goal["ends_year"]:
                goal_solvent_tracking[id(goal)] &= solvent

    summary = []
    for goal in goals:
        summary.append({
            "purpose": goal["purpose"],
            "success_rate": float(goal_solvent_tracking[id(goal)].mean()),
        })
    return values, summary


def glide_path_weights(start_weights: np.ndarray, end_weights: np.ndarray, glide_path_years: int, year: int) -> np.ndarray:
    if year >= glide_path_years:
        return end_weights
    t = year / glide_path_years
    return start_weights * (1 - t) + end_weights * t


def build_cashflow_series(paths: np.ndarray, initial_amount: float, goals: list[dict], inflation_draws: np.ndarray | None = None) -> dict:
    """Per-year median net cashflow across all simulated paths, for the Goals &
    Cashflows tab's chart. `inflation_draws` (shape (n_paths, n_years), from
    engine/inflation.py) discounts nominal cashflows to present-dollar terms via the
    per-path cumulative inflation factor; without it, present-dollar == nominal."""
    n_years = paths.shape[1] - 1
    nominal = np.zeros(n_years)
    for year in range(n_years):
        net = 0.0
        for goal in goals:
            if goal["starts_year"] <= year < goal["ends_year"]:
                sign = -1.0 if goal["is_withdrawal"] else 1.0
                net += sign * _annualized_goal_amount(goal)
        nominal[year] = net

    if inflation_draws is None:
        present_dollar = nominal.copy()
    else:
        median_inflation = np.median(inflation_draws, axis=0)  # shape (n_years,)
        cumulative_factor = np.cumprod(1 + median_inflation)
        present_dollar = nominal / cumulative_factor

    return {
        "cashflows_nominal": nominal.tolist(),
        "cashflows_present_dollar": present_dollar.tolist(),
    }
