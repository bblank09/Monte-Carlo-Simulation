import numpy as np

from backend.app.engine.parameterized import simulate_parameterized


def test_normal_distribution_shape():
    config = {"seed": 1, "n_paths": 50, "simulation_period_years": 10,
              "expected_return": 0.07, "expected_volatility": 0.15, "distribution": "normal"}
    paths = simulate_parameterized(config)
    assert paths.shape == (50, 11)
    assert np.allclose(paths[:, 0], 1.0)


def test_fat_tailed_floor_at_negative_99_9_percent():
    config = {"seed": 1, "n_paths": 200, "simulation_period_years": 5,
              "expected_return": 0.0, "expected_volatility": 0.9,
              "distribution": "fat_tailed", "degrees_of_freedom": 3}
    paths = simulate_parameterized(config)
    per_period_return = paths[:, 1:] / paths[:, :-1] - 1
    assert per_period_return.min() >= -0.999 - 1e-9
