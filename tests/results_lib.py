import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def percentile_table(paths: np.ndarray, initial_amount: float) -> pd.DataFrame:
    pcts = [10, 25, 50, 75, 90]
    ending = paths[:, -1] * initial_amount
    n_years = paths.shape[1] - 1
    cagr = (paths[:, -1]) ** (1 / n_years) - 1
    return pd.DataFrame({p: [np.percentile(ending, p), np.percentile(cagr, p)] for p in pcts},
                         index=["ending_balance", "cagr"])


def parametric_var_es(weights: np.ndarray, mu: np.ndarray, sigma: np.ndarray, alpha: float = 0.90) -> tuple[float, float]:
    """Closed-form parametric VaR/ES from JA252.3 (assumes Normal returns)."""
    from scipy.stats import norm
    port_mu = weights @ mu
    port_sd = np.sqrt(weights @ sigma @ weights)
    z = norm.ppf(alpha)
    var = -port_mu + z * port_sd
    es = -port_mu + (norm.pdf(z) / (1 - alpha)) * port_sd
    return var, es


def compute_var_es(ending_values: np.ndarray, alpha: float = 0.90) -> tuple[float, float]:
    losses = -ending_values
    var_threshold = np.percentile(losses, alpha * 100)
    es = losses[losses >= var_threshold].mean()
    return -var_threshold, -es


def plot_fan_chart(paths: np.ndarray, initial_amount: float):
    pcts = [10, 25, 50, 75, 90]
    values = paths * initial_amount
    years = np.arange(paths.shape[1])
    fig, ax = plt.subplots(figsize=(9, 5))
    for p in pcts:
        ax.plot(years, np.percentile(values, p, axis=0), label=f"{p}th percentile")
    ax.set_xlabel("Year")
    ax.set_ylabel("Portfolio Balance")
    ax.legend()
    return fig


def plot_ending_histogram(paths: np.ndarray, initial_amount: float):
    ending = paths[:, -1] * initial_amount
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(ending, bins=60)
    ax.set_xlabel("End Balance")
    ax.set_ylabel("Frequency")
    return fig
