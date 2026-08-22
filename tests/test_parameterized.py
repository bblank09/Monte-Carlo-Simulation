import numpy as np
from scipy.stats import kurtosis

from backend.app.engine.parameterized import simulate_parameterized


def test_parameterized_fat_tailed_has_higher_kurtosis_than_normal():
    base_config = {"simulation_period_years": 1, "n_paths": 20000, "seed": 11,
                   "expected_return": 0.07, "expected_volatility": 0.15, "degrees_of_freedom": 5}
    normal_paths = simulate_parameterized({**base_config, "distribution": "normal"})
    fat_paths = simulate_parameterized({**base_config, "distribution": "fat_tailed"})
    normal_ret = np.log(normal_paths[:, -1])
    fat_ret = np.log(fat_paths[:, -1])
    assert kurtosis(fat_ret) > kurtosis(normal_ret) + 0.5
