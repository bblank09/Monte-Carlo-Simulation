import numpy as np
from backend.app.engine.goals import glide_path_weights


def simulate_with_glide_path(simulate_year_fn, start_weights: np.ndarray, end_weights: np.ndarray, years_to_retirement: int, glide_path_years: int, n_years: int, n_paths: int, seed: int | None = None) -> np.ndarray:
    """Chain one-year simulations together, re-deriving that year's target weights from
    the glide path before each call. `simulate_year_fn(weights, year_seed)` must return
    an array of shape (n_paths,) of that year's per-path growth factor. `years_to_retirement`
    and `glide_path_years` are passed straight through to `goals.glide_path_weights` -- the
    single source of truth for the weight-at-year schedule, also used by orchestrator.py's
    displayed `goals.glide_path` chart data, so the simulation and the chart can never
    disagree."""
    values = np.empty((n_paths, n_years + 1))
    values[:, 0] = 1.0
    for year in range(n_years):
        weights = glide_path_weights(start_weights, end_weights, years_to_retirement, glide_path_years, year)
        year_seed = None if seed is None else seed + year
        growth_factor = simulate_year_fn(weights, year_seed)
        values[:, year + 1] = values[:, year] * growth_factor
    return values
