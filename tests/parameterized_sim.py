import numpy as np
from scipy.stats import t as student_t


def simulate_parameterized(config: dict) -> np.ndarray:
    rng = np.random.default_rng(config["seed"])
    n_paths = config["n_paths"]
    n_years = config["simulation_period_years"]
    mu = config["expected_return"]
    sigma = config["expected_volatility"]
    if config["distribution"] == "normal":
        annual_returns = rng.normal(mu, sigma, size=(n_paths, n_years))
    elif config["distribution"] == "fat_tailed":
        dof = config["degrees_of_freedom"]
        raw = student_t.rvs(df=dof, size=(n_paths, n_years), random_state=rng)
        scale = sigma / np.sqrt(dof / (dof - 2))
        annual_returns = mu + scale * raw
    else:
        raise ValueError("unknown distribution: " + str(config["distribution"]))
    # Fat-tailed draws with low degrees_of_freedom can produce returns < -100%, which is not
    # economically meaningful without leverage (a portfolio cannot lose more than all of its value)
    annual_returns = np.maximum(annual_returns, -0.999)
    growth = np.cumprod(1 + annual_returns, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])
