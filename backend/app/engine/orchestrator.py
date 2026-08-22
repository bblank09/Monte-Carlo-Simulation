import numpy as np
import pandas as pd

from backend.app.data.returns import estimate_mu_sigma
from backend.app.domain.schemas import SimulateRequest, SimulateResponse
from backend.app.engine.forecasted import simulate_forecasted
from backend.app.engine.glide_path_orchestration import simulate_with_glide_path
from backend.app.engine.goals import (
    apply_cashflow,
    apply_named_goals,
    build_cashflow_series,
    glide_path_weights,
)
from backend.app.engine.historical import simulate_historical
from backend.app.engine.inflation import (
    THAILAND_CPI_ANNUAL_RETURNS,
    THAILAND_CPI_SOURCE,
    THAILAND_CPI_VINTAGE,
    simulate_inflation,
)
from backend.app.engine.parameterized import simulate_parameterized
from backend.app.engine.results import (
    annual_return_probability,
    compute_var_es,
    correlation_and_returns_table,
    expected_return_by_horizon,
    loss_probability,
    percentile_table,
    sharpe_sortino_by_percentile,
    survival_series,
    withdrawal_rates_by_percentile,
)
from backend.app.engine.statistical import simulate_statistical


def run_simulation(request: SimulateRequest, returns_df: pd.DataFrame) -> SimulateResponse:
    proj_ids = [h.proj_id for h in request.holdings]
    weights = np.array([h.weight for h in request.holdings]) / 100.0
    has_return_history = bool(not returns_df.empty and all(proj_id in returns_df.columns for proj_id in proj_ids))
    subset = returns_df[proj_ids] if all(proj_id in returns_df.columns for proj_id in proj_ids) else pd.DataFrame(columns=proj_ids)
    if request.simulation_model == "parameterized":
        # User-specified return and volatility are the complete model input. Asset
        # history is optional and only powers the diagnostics table when supplied.
        mu, sigma = None, None
    else:
        if not has_return_history:
            raise ValueError("simulation requires usable return history for the selected model")
        mu, sigma = estimate_mu_sigma(subset)

    config = _build_engine_config(request)
    years_to_retirement = request.years_to_retirement
    glide_path_years = request.glide_path_years
    retirement_holdings = request.retirement_holdings
    is_multistage = bool(
        request.multi_goal_enabled
        and years_to_retirement is not None
        and glide_path_years is not None
        and retirement_holdings
    )

    if is_multistage:
        assert years_to_retirement is not None
        assert glide_path_years is not None
        assert retirement_holdings is not None
        retirement_weights = np.array([h.weight for h in retirement_holdings]) / 100.0
        year_simulator = _make_year_simulator(request, config, mu, sigma, subset)
        growth_paths = simulate_with_glide_path(
            year_simulator, weights, retirement_weights,
            years_to_retirement=years_to_retirement,
            glide_path_years=glide_path_years,
            n_years=request.simulation_period_years, n_paths=request.n_paths, seed=request.seed,
        )
    elif request.simulation_model == "historical":
        growth_paths = simulate_historical(subset, weights, config)
    elif request.simulation_model == "forecasted":
        growth_paths = simulate_forecasted(mu, sigma, weights, config, returns_df=subset)
    elif request.simulation_model == "statistical":
        growth_paths = simulate_statistical(mu, sigma, weights, config, returns_df=subset)
    elif request.simulation_model == "parameterized":
        growth_paths = simulate_parameterized(config)
    else:
        raise ValueError(f"unknown simulation_model: {request.simulation_model}")

    growth_paths = _apply_tax_treatment(growth_paths, request.tax_treatment, request.tax_rate)
    inflation_draws = _simulate_inflation_draws(request)
    goals_summary = None
    goal_dicts: list[dict] = []
    if request.multi_goal_enabled and request.goals:
        goal_dicts = [g.model_dump() for g in request.goals]
        dollar_paths, goals_summary = apply_named_goals(
            growth_paths, request.initial_amount, goal_dicts, inflation_draws=inflation_draws,
        )
    elif request.cashflow_mode != "none":
        cashflow = {
            "amount": request.cashflow_amount,
            "is_withdrawal": request.cashflow_mode != "contribute",
            "is_percent": request.cashflow_mode == "withdraw_percent",
            "inflation_adjusted": bool(request.cashflow_inflation_adjusted),
            "frequency": request.cashflow_frequency,
        }
        dollar_paths = apply_cashflow(
            growth_paths, request.initial_amount, cashflow, inflation_draws=inflation_draws,
        )
    else:
        dollar_paths = growth_paths * request.initial_amount

    normalized_paths = dollar_paths / request.initial_amount
    pct_table = percentile_table(
        normalized_paths, request.initial_amount,
        inflation_draws=inflation_draws, growth_only_paths=growth_paths,
    )
    sharpe_sortino = sharpe_sortino_by_percentile(normalized_paths)
    withdrawal_rates = withdrawal_rates_by_percentile(normalized_paths, request.simulation_period_years)
    survival = survival_series(dollar_paths)
    corr_table = correlation_and_returns_table(subset, proj_ids) if has_return_history else {
        "available": False,
        "reason": "Historical NAV diagnostics are not required for the Parameterized model.",
        "correlation": {},
        "stats": {},
    }
    ending_values = dollar_paths[:, -1] - request.initial_amount
    var, es = compute_var_es(ending_values)

    survived_mask = np.all(dollar_paths > 0, axis=1)
    survived_count = int(survived_mask.sum())
    terminal_positive_rate = float((dollar_paths[:, -1] > 0).mean())

    overview = {
        "n_paths": request.n_paths,
        "survived_count": survived_count,
        "survival_rate": survived_count / dollar_paths.shape[0],
        "terminal_positive_rate": terminal_positive_rate,
        "median_ending_balance": pct_table["ending_balance"][50],
        "median_cagr": pct_table["cagr"][50],
        "holdings": [{"proj_id": h.proj_id, "weight": h.weight} for h in request.holdings],
        "historical_data_range": _data_range(subset) if has_return_history else None,
    }
    growth = {
        "fan_chart": {p: (np.percentile(dollar_paths, p, axis=0)).tolist() for p in [10, 25, 50, 75, 90]},
        "survival_over_time": survival.tolist(),
    }
    running_peak = np.maximum.accumulate(dollar_paths, axis=1)
    max_drawdown = (dollar_paths / running_peak - 1.0).min(axis=1)
    distribution = {
        "ending_balance_histogram": dollar_paths[:, -1].tolist(),
        "max_drawdown_histogram": max_drawdown.tolist(),
    }
    metrics = {
        "percentile_table": pct_table,
        "sharpe": sharpe_sortino["sharpe"],
        "sortino": sharpe_sortino["sortino"],
        "safe_withdrawal_rate": withdrawal_rates["safe_withdrawal_rate"],
        "perpetual_withdrawal_rate": withdrawal_rates["perpetual_withdrawal_rate"],
    }
    risk = {
        "correlation_and_returns": corr_table,
        "value_at_risk": var,
        "expected_shortfall": es,
        "expected_return_by_horizon": expected_return_by_horizon(normalized_paths),
        "annual_return_probability": annual_return_probability(normalized_paths),
        "loss_probability": loss_probability(normalized_paths, growth_only_paths=growth_paths),
    }
    goals_section = None
    if goals_summary is not None:
        goals_section = {
            "summary": goals_summary,
            **build_cashflow_series(growth_paths, request.initial_amount, goal_dicts, inflation_draws=inflation_draws),
        }
        if is_multistage:
            assert years_to_retirement is not None
            assert glide_path_years is not None
            years_axis = list(range(request.simulation_period_years + 1))
            # Uses the exact same `glide_path_weights` function that
            # `simulate_with_glide_path` used to drive the actual per-year simulation
            # above -- one source of truth, so the displayed chart can never disagree
            # with the allocation the simulation actually used.
            allocations = {
                proj_id: [
                    float(glide_path_weights(
                        weights, retirement_weights, years_to_retirement,
                        glide_path_years, y,
                    )[i])
                    for y in years_axis
                ]
                for i, proj_id in enumerate(proj_ids)
            }
            goals_section["glide_path"] = {"years": years_axis, "allocations": allocations}

    run_config = request.model_dump()
    run_config["data_provenance"] = {
        "asset_returns": "SEC Open Data NAV cache" if has_return_history else "Not used (Parameterized assumptions)",
        "asset_data_range": _data_range(subset) if has_return_history else None,
        "historical_inflation": {
            "source": THAILAND_CPI_SOURCE,
            "vintage": THAILAND_CPI_VINTAGE,
            "observations": int(THAILAND_CPI_ANNUAL_RETURNS.size),
            "used": request.inflation_model == "historical",
        },
    }

    return SimulateResponse(
        overview=overview, growth=growth, distribution=distribution,
        metrics=metrics, risk=risk, goals=goals_section,
        run_config=run_config,
    )


def _data_range(returns_df: pd.DataFrame) -> dict[str, str] | None:
    if returns_df.empty or len(returns_df.index) == 0:
        return None
    dates = pd.to_datetime(returns_df.index, errors="coerce").dropna()
    if len(dates) == 0:
        return None
    return {"start": dates.min().date().isoformat(), "end": dates.max().date().isoformat()}


def _make_year_simulator(request: SimulateRequest, config: dict, mu, sigma, subset):
    """Build a `simulate_year_fn(weights, year_seed) -> growth_factor[n_paths]` closure
    around whichever simulation model the request selected, for
    `glide_path_orchestration.simulate_with_glide_path` to call once per year. Every
    `simulate_*` model normalizes its output to start at 1.0, so running any of them
    with `simulation_period_years=1` and reading `paths[:, 1]` yields exactly that
    year's per-path growth factor, regardless of which model it is."""
    def simulate_year(weights: np.ndarray, year_seed: int | None) -> np.ndarray:
        year_config = dict(config, simulation_period_years=1, seed=year_seed)
        if request.simulation_model == "historical":
            paths = simulate_historical(subset, weights, year_config)
        elif request.simulation_model == "forecasted":
            paths = simulate_forecasted(mu, sigma, weights, year_config, returns_df=subset)
        elif request.simulation_model == "statistical":
            paths = simulate_statistical(mu, sigma, weights, year_config, returns_df=subset)
        elif request.simulation_model == "parameterized":
            paths = simulate_parameterized(year_config)
        else:
            raise ValueError(f"unknown simulation_model: {request.simulation_model}")
        return paths[:, 1]
    return simulate_year


def _simulate_inflation_draws(request: SimulateRequest) -> np.ndarray:
    rng = np.random.default_rng(request.seed)
    if request.inflation_model == "historical":
        return simulate_inflation(
            {"inflation_model": "historical", "cpi_returns": THAILAND_CPI_ANNUAL_RETURNS},
            n_paths=request.n_paths,
            n_years=request.simulation_period_years,
            rng=rng,
        )
    return simulate_inflation(
        {
            "inflation_model": "parameterized",
            "inflation_mean": request.inflation_mean if request.inflation_mean is not None else 0.03,
            "inflation_volatility": request.inflation_volatility if request.inflation_volatility is not None else 0.01,
        },
        n_paths=request.n_paths, n_years=request.simulation_period_years, rng=rng,
    )


def _build_engine_config(request: SimulateRequest) -> dict:
    return {
        "seed": request.seed,
        "n_paths": request.n_paths,
        "simulation_period_years": request.simulation_period_years,
        "bootstrap_model": request.bootstrap_model,
        "block_years": request.block_years,
        "sequence_of_returns_risk": request.sequence_of_returns_risk or 0,
        "time_series_model": request.time_series_model,
        "rebalancing": request.rebalancing,
        "distribution": request.distribution,
        "degrees_of_freedom": request.degrees_of_freedom,
        "expected_return": request.expected_return,
        "expected_volatility": request.expected_volatility,
    }


def _apply_tax_treatment(
    growth_paths: np.ndarray,
    tax_treatment: str,
    tax_rate: float | None,
) -> np.ndarray:
    """Apply a transparent tax drag to positive per-period returns.

    This is intentionally a simple effective-rate model: gains are taxed in the
    period they occur, losses are not given an automatic tax benefit, and the
    result remains a normalized growth-factor path before cashflows are applied.
    The explicit rate is required by the request schema for after-tax runs.
    """
    if tax_treatment == "pre_tax" or tax_rate in (None, 0.0):
        return growth_paths
    with np.errstate(divide="ignore", invalid="ignore"):
        period_returns = growth_paths[:, 1:] / growth_paths[:, :-1] - 1.0
    taxed_returns = np.where(period_returns > 0.0, period_returns * (1.0 - tax_rate), period_returns)
    taxed_growth = np.cumprod(1.0 + taxed_returns, axis=1)
    return np.hstack([np.ones((growth_paths.shape[0], 1)), taxed_growth])
