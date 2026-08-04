import numpy as np
import pandas as pd


def simulate_historical(returns_df: pd.DataFrame, weights: np.ndarray, config: dict) -> np.ndarray:
    rng = np.random.default_rng(config["seed"])
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    bootstrap_model = config.get("bootstrap_model", "single_year")

    if bootstrap_model == "single_year":
        annual_returns = _annual_portfolio_returns(returns_df, weights)
        sampled = rng.choice(annual_returns, size=(n_paths, n_years), replace=True)
    elif bootstrap_model == "single_month":
        monthly_returns = _monthly_portfolio_returns(returns_df, weights)
        sampled_months = rng.choice(monthly_returns, size=(n_paths, n_years * 12), replace=True)
        sampled = np.prod((1 + sampled_months).reshape(n_paths, n_years, 12), axis=2) - 1
    elif bootstrap_model == "block_of_years":
        block_years = config.get("block_years", 2)
        annual_returns = _annual_portfolio_returns(returns_df, weights)
        sampled = _block_bootstrap(annual_returns, n_paths, n_years, block_years, rng)
    else:
        raise ValueError(f"unknown bootstrap_model: {bootstrap_model}")

    risk_n = config.get("sequence_of_returns_risk", 0)
    if risk_n:
        sampled = _apply_sequence_of_returns_risk(sampled, risk_n)

    growth = np.cumprod(1 + sampled, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])


def _annual_portfolio_returns(returns_df: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    annual_returns = returns_df.groupby(returns_df.index.year).apply(lambda g: (1 + g).prod() - 1)
    return annual_returns.to_numpy() @ weights


def _monthly_portfolio_returns(returns_df: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    monthly_returns = returns_df.groupby([returns_df.index.year, returns_df.index.month]).apply(
        lambda g: (1 + g).prod() - 1
    )
    return monthly_returns.to_numpy() @ weights


def _block_bootstrap(annual_returns: np.ndarray, n_paths: int, n_years: int, block_years: int, rng: np.random.Generator) -> np.ndarray:
    """Sample contiguous blocks of `block_years` real annual returns (with replacement across
    starting points), concatenating blocks until n_years is reached, then truncating."""
    n_available = len(annual_returns)
    n_blocks_needed = -(-n_years // block_years)  # ceil division
    out = np.empty((n_paths, n_blocks_needed * block_years))
    for p in range(n_paths):
        chunks = []
        for _ in range(n_blocks_needed):
            start = rng.integers(0, max(1, n_available - block_years + 1))
            block = annual_returns[start:start + block_years]
            if len(block) < block_years:
                block = np.pad(block, (0, block_years - len(block)), mode="wrap")
            chunks.append(block)
        out[p] = np.concatenate(chunks)
    return out[:, :n_years]


def _apply_sequence_of_returns_risk(sampled: np.ndarray, worst_n: int) -> np.ndarray:
    """Reorder each path's sampled annual returns so the worst `worst_n` years occur first,
    stress-testing sequence-of-returns risk. The remaining years keep their sampled order."""
    n_years = sampled.shape[1]
    worst_n = min(worst_n, n_years)
    reordered = np.empty_like(sampled)
    for p in range(sampled.shape[0]):
        row = sampled[p]
        worst_idx = np.argsort(row)[:worst_n]
        rest_idx = np.array([i for i in range(n_years) if i not in set(worst_idx)], dtype=int)
        worst_sorted = row[worst_idx][np.argsort(row[worst_idx])]
        reordered[p] = np.concatenate([worst_sorted, row[rest_idx]])
    return reordered
