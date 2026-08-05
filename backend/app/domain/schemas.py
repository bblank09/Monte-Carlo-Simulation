from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class Holding(BaseModel):
    proj_id: str
    weight: float = Field(ge=0, le=100)


class NamedGoal(BaseModel):
    purpose: str
    is_withdrawal: bool
    amount: float
    inflation_adjusted: bool
    frequency: Literal["monthly", "quarterly", "annually"]
    starts_year: int = Field(ge=0)
    ends_year: int = Field(ge=0)


class SimulateRequest(BaseModel):
    holdings: list[Holding]
    initial_amount: float = Field(gt=0)
    simulation_period_years: int = Field(ge=5, le=75)
    tax_treatment: Literal["pre_tax", "after_tax"]
    simulation_model: Literal["historical", "forecasted", "statistical", "parameterized"]
    n_paths: int = Field(ge=1000, le=20000, default=10000)
    seed: Optional[int] = None
    rebalancing: Literal["none", "annual", "semiannual", "quarterly", "monthly"]

    # Historical-specific
    use_full_history: Optional[bool] = None
    bootstrap_model: Optional[Literal["single_month", "single_year", "block_of_years"]] = None
    block_years: Optional[int] = None
    sequence_of_returns_risk: Optional[int] = Field(default=0, ge=0, le=10)

    # Forecasted / Statistical-specific
    time_series_model: Optional[Literal["normal", "garch"]] = None

    # Parameterized-specific
    distribution: Optional[Literal["normal", "fat_tailed"]] = None
    degrees_of_freedom: Optional[float] = None
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None

    # Cashflow (single, default mode) -- 7 modes to match the frontend's Cashflow
    # dropdown (Task 17's ParametersStep). withdraw_fixed and withdraw_percent both have
    # dedicated engine support in engine/goals.py's apply_cashflow (fixed-dollar vs.
    # percent-of-current-balance). The remaining 3 (rolling_average_spending,
    # geometric_spending, withdraw_life_expectancy) do not yet have engine support --
    # the orchestrator's wiring treats them as withdraw_fixed for now and this is
    # flagged as a known follow-up, not silently dropped.
    cashflow_mode: Literal["none", "contribute", "withdraw_fixed", "withdraw_percent", "rolling_average_spending", "geometric_spending", "withdraw_life_expectancy"] = "none"
    cashflow_amount: Optional[float] = None
    cashflow_inflation_adjusted: Optional[bool] = None
    cashflow_frequency: Optional[Literal["monthly", "quarterly", "annually"]] = None

    # Multi-goal / multistage (advanced)
    multi_goal_enabled: bool = False
    goals: Optional[list[NamedGoal]] = None
    years_to_retirement: Optional[int] = None
    glide_path_years: Optional[int] = Field(default=None, ge=1)
    retirement_holdings: Optional[list[Holding]] = None

    # Inflation
    inflation_model: Literal["historical", "parameterized"]
    inflation_mean: Optional[float] = None
    inflation_volatility: Optional[float] = None

    @model_validator(mode="after")
    def weights_sum_to_100(self):
        total = sum(h.weight for h in self.holdings)
        if abs(total - 100.0) > 0.05:
            raise ValueError(f"holding weights must sum to 100, got {total}")
        return self

    @model_validator(mode="after")
    def parameterized_requires_return_and_volatility(self):
        if self.simulation_model == "parameterized":
            if self.expected_return is None or self.expected_volatility is None or self.distribution is None:
                raise ValueError("parameterized model requires expected_return, expected_volatility, distribution")
        return self

    @model_validator(mode="after")
    def sequence_of_returns_risk_incompatible_with_glide_path(self):
        # Multistage/glide-path composition (engine/glide_path_orchestration.py) runs
        # each model one simulated year at a time (simulation_period_years=1 per call).
        # historical.py's sequence-of-returns-risk stress test works by reordering the
        # worst N years to the front of a multi-year draw -- reordering within a
        # length-1 array is a no-op, so under glide-path composition the stress test
        # would silently do nothing instead of applying (previously an undisclosed gap;
        # rejecting the combination outright is safer than a simulation that looks like
        # it applied the stress test but didn't).
        is_multistage = bool(
            self.multi_goal_enabled and self.years_to_retirement is not None
            and self.glide_path_years is not None and self.retirement_holdings
        )
        if is_multistage and (self.sequence_of_returns_risk or 0) > 0:
            raise ValueError(
                "sequence_of_returns_risk is not supported together with glide-path "
                "multistage composition (years_to_retirement + glide_path_years + "
                "retirement_holdings) -- the stress test's year-reordering has no effect "
                "under the per-year composition, so this combination is rejected rather "
                "than silently ignored."
            )
        return self


class PercentileBand(BaseModel):
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float


class SimulateResponse(BaseModel):
    run_id: str = ""
    created_at: str = ""
    data_source: Literal["sec_open_data"] = "sec_open_data"
    overview: dict
    growth: dict
    distribution: dict
    metrics: dict
    risk: dict
    goals: Optional[dict] = None
    run_config: dict
