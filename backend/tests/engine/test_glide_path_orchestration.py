import numpy as np
from backend.app.engine.glide_path_orchestration import simulate_with_glide_path


def test_glide_path_chains_yearly_growth_factors():
    start_weights = np.array([0.8, 0.2])
    end_weights = np.array([0.2, 0.8])

    def fake_simulate_year(weights, year_seed):
        # Deterministic stand-in: each year grows by (1 + weights[0] * 0.10), for a
        # fixed number of paths -- exercises the chaining logic without needing a real
        # simulation model.
        return np.full(5, 1.0 + weights[0] * 0.10)

    paths = simulate_with_glide_path(
        fake_simulate_year, start_weights, end_weights,
        glide_path_years=4, n_years=4, n_paths=5, seed=1,
    )
    assert paths.shape == (5, 5)
    assert np.allclose(paths[:, 0], 1.0)
    # Weight on asset 0 declines each year (0.8 -> 0.6 -> 0.4 -> 0.2), so each year's
    # growth factor shrinks -- the cumulative path must be strictly concave (decelerating).
    year_over_year_growth = paths[0, 1:] / paths[0, :-1]
    assert np.all(np.diff(year_over_year_growth) < 0)


def test_glide_path_matches_static_weights_when_start_equals_end():
    same_weights = np.array([0.5, 0.5])

    def fake_simulate_year(weights, year_seed):
        return np.full(3, 1.05)

    paths = simulate_with_glide_path(
        fake_simulate_year, same_weights, same_weights,
        glide_path_years=5, n_years=3, n_paths=3, seed=1,
    )
    expected = np.array([1.0, 1.05, 1.05 ** 2, 1.05 ** 3])
    assert np.allclose(paths[0], expected)
