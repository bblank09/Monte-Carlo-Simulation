import numpy as np
import pandas as pd
from backend.app.data.returns import estimate_mu_sigma
from backend.app.engine.gbm import simulate_gbm_paths  # noqa: F401 (used indirectly via statistical)
from backend.app.engine.historical import simulate_historical
from backend.app.engine.forecasted import simulate_forecasted
from backend.app.engine.statistical import simulate_statistical
from backend.app.engine.parameterized import simulate_parameterized
from backend.app.engine.inflation import simulate_inflation
from backend.app.engine.goals import apply_cashflow, apply_named_goals, glide_path_weights, build_cashflow_series
from backend.app.engine.glide_path_orchestration import simulate_with_glide_path
from backend.app.engine.results import (
    percentile_table, sharpe_sortino_by_percentile, withdrawal_rates_by_percentile,
    survival_series, correlation_and_returns_table, compute_var_es,
    expected_return_by_horizon, annual_return_probability, loss_probability,
)
from backend.app.domain.schemas import SimulateRequest, SimulateResponse

# Historical inflation has no real Thai CPI series wired in yet (spec's open item --
# see Task 11's "Known follow-up" note above). This placeholder approximates recent
# Thai CPI behavior until a real series is sourced; parameterized inflation (user
# input) does not use this constant at all.
_PLACEHOLDER_HISTORICAL_INFLATION_MEAN = 0.03
_PLACEHOLDER_HISTORICAL_INFLATION_VOL = 0.013


def run_simulation(request: SimulateRequest, returns_df: pd.DataFrame) -> SimulateResponse:
    proj_ids = [h.proj_id for h in request.holdings]
    weights = np.array([h.weight for h in request.holdings]) / 100.0
    subset = returns_df[proj_ids]
    mu, sigma = estimate_mu_sigma(subset)

    config = _build_engine_config(request)
    is_multistage = bool(
        request.multi_goal_enabled
        and request.years_to_retirement is not None
        and request.glide_path_years is not None
        and request.retirement_holdings
    )

    if is_multistage:
        retirement_weights = np.array([h.weight for h in request.retirement_holdings]) / 100.0
        year_simulator = _make_year_simulator(request, config, mu, sigma, subset)
        growth_paths = simulate_with_glide_path(
            year_simulator, weights, retirement_weights,
            years_to_retirement=request.years_to_retirement,
            glide_path_years=request.glide_path_years,
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

    goals_summary = None
    goal_dicts: list[dict] = []
    if request.multi_goal_enabled and request.goals:
        goal_dicts = [g.model_dump() for g in request.goals]
        dollar_paths, goals_summary = apply_named_goals(growth_paths, request.initial_amount, goal_dicts)
    elif request.cashflow_mode != "none":
        # rolling_average_spending / geometric_spending / withdraw_life_expectancy are
        # not yet distinctly implemented (see Task 11's "Known follow-up" note) -- they
        # fall through to the same fixed-amount treatment as withdraw_fixed for now.
        cashflow = {
            "amount": request.cashflow_amount or 0.0,
            "is_withdrawal": request.cashflow_mode != "contribute",
            "inflation_adjusted": bool(request.cashflow_inflation_adjusted),
            "frequency": request.cashflow_frequency or "annually",
        }
        dollar_paths = apply_cashflow(growth_paths, request.initial_amount, cashflow)
    else:
        dollar_paths = growth_paths * request.initial_amount

    normalized_paths = dollar_paths / request.initial_amount
    inflation_draws = _simulate_inflation_draws(request)

    pct_table = percentile_table(
        normalized_paths, request.initial_amount,
        inflation_draws=inflation_draws, growth_only_paths=growth_paths,
    )
    sharpe_sortino = sharpe_sortino_by_percentile(normalized_paths)
    withdrawal_rates = withdrawal_rates_by_percentile(normalized_paths, request.simulation_period_years)
    survival = survival_series(dollar_paths)
    corr_table = correlation_and_returns_table(subset, proj_ids)
    ending_values = dollar_paths[:, -1] - request.initial_amount
    var, es = compute_var_es(ending_values)

    survived_count = int((dollar_paths[:, -1] > 0).sum())

    overview = {
        "n_paths": request.n_paths,
        "survived_count": survived_count,
        "survival_rate": survived_count / dollar_paths.shape[0],
        "median_ending_balance": pct_table["ending_balance"][50],
        "median_cagr": pct_table["cagr"][50],
        "holdings": [{"proj_id": h.proj_id, "weight": h.weight} for h in request.holdings],
    }
    growth = {
        "fan_chart": {p: (np.percentile(dollar_paths, p, axis=0)).tolist() for p in [10, 25, 50, 75, 90]},
        "survival_over_time": survival.tolist(),
    }
    distribution = {
        "ending_balance_histogram": dollar_paths[:, -1].tolist(),
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
            years_axis = list(range(request.simulation_period_years + 1))
            # Uses the exact same `glide_path_weights` function that
            # `simulate_with_glide_path` used to drive the actual per-year simulation
            # above -- one source of truth, so the displayed chart can never disagree
            # with the allocation the simulation actually used.
            allocations = {
                proj_id: [
                    float(glide_path_weights(
                        weights, retirement_weights, request.years_to_retirement,
                        request.glide_path_years, y,
                    )[i])
                    for y in years_axis
                ]
                for i, proj_id in enumerate(proj_ids)
            }
            goals_section["glide_path"] = {"years": years_axis, "allocations": allocations}

    return SimulateResponse(
        overview=overview, growth=growth, distribution=distribution,
        metrics=metrics, risk=risk, goals=goals_section,
        run_config=request.model_dump(),
    )


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
        return rng.normal(
            _PLACEHOLDER_HISTORICAL_INFLATION_MEAN, _PLACEHOLDER_HISTORICAL_INFLATION_VOL,
            size=(request.n_paths, request.simulation_period_years),
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
