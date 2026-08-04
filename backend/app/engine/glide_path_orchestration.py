import numpy as np
from backend.app.engine.goals import glide_path_weights


def simulate_with_glide_path(simulate_year_fn, start_weights: np.ndarray, end_weights: np.ndarray, glide_path_years: int, n_years: int, n_paths: int, seed: int | None = None) -> np.ndarray:
    """Chain one-year simulations together, re-deriving that year's target weights from
    the glide path before each call. `simulate_year_fn(weights, year_seed)` must return
    an array of shape (n_paths,) of that year's per-path growth factor."""
    values = np.empty((n_paths, n_years + 1))
    values[:, 0] = 1.0
    for year in range(n_years):
        weights = glide_path_weights(start_weights, end_weights, glide_path_years, year)
        year_seed = None if seed is None else seed + year
        growth_factor = simulate_year_fn(weights, year_seed)
        values[:, year + 1] = values[:, year] * growth_factor
    return values
