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
        years_to_retirement=4, glide_path_years=4, n_years=4, n_paths=5, seed=1,
    )
    assert paths.shape == (5, 5)
    assert np.allclose(paths[:, 0], 1.0)
    # years_to_retirement == glide_path_years == 4, so the transition window is [0, 4]:
    # weight on asset 0 declines each year (0.8 -> 0.6 -> 0.4 -> 0.2), so each year's
    # growth factor shrinks -- the cumulative path must be strictly concave (decelerating).
    year_over_year_growth = paths[0, 1:] / paths[0, :-1]
    assert np.all(np.diff(year_over_year_growth) < 0)


def test_glide_path_matches_static_weights_when_start_equals_end():
    same_weights = np.array([0.5, 0.5])

    def fake_simulate_year(weights, year_seed):
        return np.full(3, 1.05)

    paths = simulate_with_glide_path(
        fake_simulate_year, same_weights, same_weights,
        years_to_retirement=5, glide_path_years=5, n_years=3, n_paths=3, seed=1,
    )
    expected = np.array([1.0, 1.05, 1.05 ** 2, 1.05 ** 3])
    assert np.allclose(paths[0], expected)


def test_glide_path_uses_hold_then_transition_to_retirement_schedule():
    # Regression: simulate_with_glide_path must drive its per-year weights through the
    # SAME hold-then-transition-to-years_to_retirement schedule as the displayed chart
    # (orchestrator.py's goals.glide_path), not the old year-0-start schedule -- so the
    # response's chart data and the actual simulated allocations can never disagree.
    start_weights = np.array([1.0, 0.0])
    end_weights = np.array([0.0, 1.0])
    seen_weights = []

    def recording_simulate_year(weights, year_seed):
        seen_weights.append(weights.copy())
        return np.ones(1)

    # years_to_retirement=6, glide_path_years=2 -> hold start through year 4, transition
    # over [4, 6], fully at end_weights from year 6 on.
    simulate_with_glide_path(
        recording_simulate_year, start_weights, end_weights,
        years_to_retirement=6, glide_path_years=2, n_years=8, n_paths=1, seed=1,
    )
    assert np.allclose(seen_weights[0], start_weights)   # year 0: still holding
    assert np.allclose(seen_weights[4], start_weights)   # year 4: transition window starts
    assert np.allclose(seen_weights[5], [0.5, 0.5])       # year 5: midpoint of transition
    assert np.allclose(seen_weights[6], end_weights)      # year 6: fully transitioned
    assert np.allclose(seen_weights[7], end_weights)      # year 7: holds after retirement
