import numpy as np


def test_percentile_table_and_var_es():
    from results_lib import percentile_table, compute_var_es
    rng = np.random.default_rng(1)
    paths = np.cumprod(1 + rng.normal(0.07, 0.15, (5000, 30)), axis=1)
    paths = np.hstack([np.ones((5000, 1)), paths])
    table = percentile_table(paths, initial_amount=1_000_000)
    assert list(table.columns) == [10, 25, 50, 75, 90]
    assert table.loc["ending_balance", 10] < table.loc["ending_balance", 90]
    ending_values = paths[:, -1] * 1_000_000
    var, es = compute_var_es(ending_values, alpha=0.90)
    assert es <= var  # Expected Shortfall must be at least as extreme as VaR (JA252.3)
