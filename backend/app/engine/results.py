import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq

_PCTS = [10, 25, 50, 75, 90]


def _percentile_band(values: np.ndarray) -> dict:
    return {p: float(np.percentile(values, p)) for p in _PCTS}


def percentile_table(paths: np.ndarray, initial_amount: float, inflation_draws: np.ndarray | None = None, growth_only_paths: np.ndarray | None = None) -> dict:
    ending = paths[:, -1] * initial_amount
    n_years = paths.shape[1] - 1
    cagr = paths[:, -1] ** (1 / n_years) - 1
    per_period_returns = paths[:, 1:] / paths[:, :-1] - 1
    annual_mean_return = per_period_returns.mean(axis=1)
    annualized_volatility = per_period_returns.std(axis=1)
    # TWRR strips cashflow timing by construction (it's a ratio of period-end to
    # period-start values) -- on this array, nominal TWRR and CAGR coincide.
    twrr_nominal = cagr

    running_max = np.maximum.accumulate(paths, axis=1)
    max_drawdown = (paths / running_max - 1).min(axis=1)

    if growth_only_paths is not None:
        running_max_g = np.maximum.accumulate(growth_only_paths, axis=1)
        max_drawdown_excl_cashflows = (growth_only_paths / running_max_g - 1).min(axis=1)
    else:
        max_drawdown_excl_cashflows = max_drawdown

    if inflation_draws is not None:
        cumulative_inflation = np.prod(1 + inflation_draws, axis=1)
        ending_real = ending / cumulative_inflation
        twrr_real = (ending_real / initial_amount) ** (1 / n_years) - 1
    else:
        ending_real = ending
        twrr_real = cagr

    return {
        "ending_balance": _percentile_band(ending),
        "ending_balance_real": _percentile_band(ending_real),
        "cagr": _percentile_band(cagr),
        "twrr_nominal": _percentile_band(twrr_nominal),
        "twrr_real": _percentile_band(twrr_real),
        "annual_mean_return": _percentile_band(annual_mean_return),
        "annualized_volatility": _percentile_band(annualized_volatility),
        "max_drawdown": _percentile_band(max_drawdown),
        "max_drawdown_excl_cashflows": _percentile_band(max_drawdown_excl_cashflows),
    }


def expected_return_by_horizon(paths: np.ndarray, horizons: list[int] = [1, 3, 5, 10, 15, 20, 25, 30]) -> dict:
    n_years = paths.shape[1] - 1
    result = {}
    for h in horizons:
        if h > n_years:
            continue
        annualized = paths[:, h] ** (1 / h) - 1
        result[str(h)] = _percentile_band(annualized)
    return result


def annual_return_probability(paths: np.ndarray, horizons: list[int] = [1, 3, 5, 10, 15, 20, 25, 30], thresholds: list[float] = [0.0, 0.025, 0.05, 0.075, 0.10, 0.125]) -> dict:
    n_years = paths.shape[1] - 1
    result = {}
    for t in thresholds:
        label = f">= {t * 100:.2f}%"
        row = {}
        for h in horizons:
            if h > n_years:
                continue
            annualized = paths[:, h] ** (1 / h) - 1
            row[str(h)] = float((annualized >= t).mean())
        result[label] = row
    return result


def loss_probability(paths: np.ndarray, growth_only_paths: np.ndarray | None = None, thresholds: list[float] = [0.0, 0.025, 0.05, 0.075, 0.10, 0.125]) -> dict:
    def _for_pathset(pset: np.ndarray) -> dict:
        running_max = np.maximum.accumulate(pset, axis=1)
        drawdown = 1 - pset / running_max
        end_loss = 1 - pset[:, -1] / pset[:, 0]
        within, end = {}, {}
        for t in thresholds:
            label = f">= {t * 100:.2f}%"
            within[label] = float((drawdown.max(axis=1) >= t).mean())
            end[label] = float((end_loss >= t).mean())
        return {"within_period": within, "end_of_period": end}

    excl = _for_pathset(growth_only_paths if growth_only_paths is not None else paths)
    incl = _for_pathset(paths)
    return {"excluding_cashflows": excl, "including_cashflows": incl}


def parametric_var_es(weights: np.ndarray, mu: np.ndarray, sigma: np.ndarray, alpha: float = 0.90) -> tuple[float, float]:
    port_mu = weights @ mu
    port_sd = np.sqrt(weights @ sigma @ weights)
    z = norm.ppf(alpha)
    var = -port_mu + z * port_sd
    es = -port_mu + (norm.pdf(z) / (1 - alpha)) * port_sd
    return var, es


def compute_var_es(ending_values: np.ndarray, alpha: float = 0.90) -> tuple[float, float]:
    # Losses are expressed as positive magnitudes (a bigger number = a worse
    # outcome), matching parametric_var_es's convention, so that ES >= VaR.
    losses = -ending_values
    var_threshold = float(np.percentile(losses, alpha * 100))
    es = float(losses[losses >= var_threshold].mean())
    return var_threshold, es


def sharpe_sortino_by_percentile(paths: np.ndarray, risk_free_rate: float = 0.0) -> dict:
    n_years = paths.shape[1] - 1
    per_path_annual_returns = paths[:, -1] ** (1 / n_years) - 1
    per_period_returns = paths[:, 1:] / paths[:, :-1] - 1
    per_path_vol = per_period_returns.std(axis=1) * np.sqrt(1)
    downside = np.where(per_period_returns < 0, per_period_returns, 0.0)
    per_path_downside_vol = np.sqrt((downside ** 2).mean(axis=1))
    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = np.where(per_path_vol > 0, (per_path_annual_returns - risk_free_rate) / per_path_vol, 0.0)
        sortino = np.where(per_path_downside_vol > 0, (per_path_annual_returns - risk_free_rate) / per_path_downside_vol, 0.0)
    return {
        "sharpe": {p: float(np.percentile(sharpe, p)) for p in _PCTS},
        "sortino": {p: float(np.percentile(sortino, p)) for p in _PCTS},
    }


def withdrawal_rates_by_percentile(paths: np.ndarray, n_years: int) -> dict:
    n_paths = paths.shape[0]
    swr = np.empty(n_paths)
    for i in range(n_paths):
        growth_factors = paths[i, 1:] / paths[i, :-1]

        def final_balance(rate):
            balance = 1.0
            for g in growth_factors:
                balance = max(balance * g - rate, 0.0)
            return balance

        try:
            swr[i] = brentq(final_balance, 0.0, 1.0, xtol=1e-4)
        except ValueError:
            swr[i] = 0.0 if final_balance(1.0) > 0 else 1.0

    per_path_annual_returns = paths[:, -1] ** (1 / n_years) - 1
    per_period_returns = paths[:, 1:] / paths[:, :-1] - 1
    per_path_vol = per_period_returns.std(axis=1)
    pwr = per_path_annual_returns - 0.5 * per_path_vol ** 2

    return {
        "safe_withdrawal_rate": {p: float(np.percentile(swr, p)) for p in _PCTS},
        "perpetual_withdrawal_rate": {p: float(np.percentile(pwr, p)) for p in _PCTS},
    }


def survival_series(paths: np.ndarray) -> np.ndarray:
    return (paths > 0).mean(axis=0)


def correlation_and_returns_table(returns_df: pd.DataFrame, asset_names: list[str], periods_per_year: int = 252) -> dict:
    correlation = returns_df[asset_names].corr()
    cumulative = (1 + returns_df[asset_names]).prod()
    n_periods = len(returns_df)
    cagr = cumulative ** (periods_per_year / n_periods) - 1
    expected_return = returns_df[asset_names].mean() * periods_per_year
    volatility = returns_df[asset_names].std() * np.sqrt(periods_per_year)
    return {
        "correlation": {a: {b: float(correlation.loc[a, b]) for b in asset_names} for a in asset_names},
        "stats": {
            a: {"cagr": float(cagr[a]), "expected_return": float(expected_return[a]), "volatility": float(volatility[a])}
            for a in asset_names
        },
    }
