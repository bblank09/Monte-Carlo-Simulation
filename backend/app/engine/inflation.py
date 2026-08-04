import numpy as np


def simulate_inflation(config: dict, n_paths: int, n_years: int, asset_return_correlation: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Simulate annual inflation draws. `asset_return_correlation` is accepted for future
    correlated-sampling work (PV correlates inflation samples with simulated asset returns
    based on historical correlations) but is not yet applied — draws are independent for now."""
    rng = rng or np.random.default_rng(config.get("seed"))
    model = config["inflation_model"]
    if model == "parameterized":
        mean = config["inflation_mean"]
        vol = config["inflation_volatility"]
        return rng.normal(mean, vol, size=(n_paths, n_years))
    elif model == "historical":
        cpi_returns = np.asarray(config["cpi_returns"])
        return rng.choice(cpi_returns, size=(n_paths, n_years), replace=True)
    else:
        raise ValueError(f"unknown inflation_model: {model}")
