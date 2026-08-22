import numpy as np

# Thailand headline-CPI annual changes, expressed as decimal returns. The SEC
# Open Data feed does not publish CPI, so this is a versioned, offline fallback
# sourced from the World Bank/IMF Thailand series (2010-2024) rather than a
# hard-coded normal approximation. Refresh this series deliberately when the
# source publishes a new observation.
THAILAND_CPI_ANNUAL_RETURNS = np.array(
    [0.0328, 0.0381, 0.0302, 0.0218, 0.0190, -0.0090, 0.0019, 0.0067,
     0.0106, 0.0071, -0.0085, 0.0123, 0.0608, 0.0123, 0.0040],
    dtype=float,
)
THAILAND_CPI_SOURCE = "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG?locations=TH"
THAILAND_CPI_VINTAGE = "2010-2024"


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
        cpi_returns = np.asarray(config["cpi_returns"], dtype=float)
        if cpi_returns.ndim != 1 or cpi_returns.size == 0 or not np.isfinite(cpi_returns).all():
            raise ValueError("historical inflation requires a non-empty finite cpi_returns series")
        return rng.choice(cpi_returns, size=(n_paths, n_years), replace=True)
    else:
        raise ValueError(f"unknown inflation_model: {model}")
