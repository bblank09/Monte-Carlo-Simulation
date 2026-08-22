from typing import Literal

from pydantic import BaseModel, Field, FiniteFloat, field_validator, model_validator


class Holding(BaseModel):
    proj_id: str = Field(min_length=1)
    weight: FiniteFloat = Field(ge=0, le=100)


class NamedGoal(BaseModel):
    purpose: str = Field(min_length=1)
    is_withdrawal: bool
    amount: FiniteFloat = Field(gt=0)
    inflation_adjusted: bool
    frequency: Literal["monthly", "quarterly", "annually"]
    starts_year: int = Field(ge=0)
    ends_year: int = Field(ge=0)

    @field_validator("purpose")
    @classmethod
    def purpose_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("named goal purpose must contain text")
        return value

    @model_validator(mode="after")
    def year_range_is_ordered(self):
        if self.starts_year >= self.ends_year:
            raise ValueError("named goal starts_year must be less than ends_year")
        return self


class SimulateRequest(BaseModel):
    holdings: list[Holding]
    initial_amount: FiniteFloat = Field(gt=0)
    simulation_period_years: int = Field(ge=5, le=75)
    tax_treatment: Literal["pre_tax", "after_tax"]
    tax_rate: FiniteFloat | None = Field(default=None, ge=0, le=1)
    simulation_model: Literal["historical", "forecasted", "statistical", "parameterized"]
    n_paths: int = Field(ge=1000, le=20000, default=10000)
    seed: int | None = None
    rebalancing: Literal["none", "annual", "semiannual", "quarterly", "monthly"]

    # Historical-specific
    use_full_history: bool | None = None
    bootstrap_model: Literal["single_month", "single_year", "block_of_years"] | None = None
    block_years: int | None = Field(default=None, ge=1)
    sequence_of_returns_risk: int | None = Field(default=0, ge=0, le=10)

    # Forecasted / Statistical-specific
    time_series_model: Literal["normal", "garch"] | None = None

    # Parameterized-specific
    distribution: Literal["normal", "fat_tailed"] | None = None
    degrees_of_freedom: FiniteFloat | None = None
    expected_return: FiniteFloat | None = None
    expected_volatility: FiniteFloat | None = Field(default=None, gt=0)

    # Only modes with distinct engine semantics are accepted. Unsupported
    # spending rules must not silently fall through to fixed withdrawals.
    cashflow_mode: Literal["none", "contribute", "withdraw_fixed", "withdraw_percent"] = "none"
    cashflow_amount: FiniteFloat | None = Field(default=None, gt=0)
    cashflow_inflation_adjusted: bool | None = None
    cashflow_frequency: Literal["monthly", "quarterly", "annually"] | None = None

    # Multi-goal / multistage (advanced)
    multi_goal_enabled: bool = False
    goals: list[NamedGoal] | None = None
    years_to_retirement: int | None = Field(default=None, ge=1)
    glide_path_years: int | None = Field(default=None, ge=1)
    retirement_holdings: list[Holding] | None = None

    # Inflation
    inflation_model: Literal["historical", "parameterized"]
    inflation_mean: FiniteFloat | None = None
    inflation_volatility: FiniteFloat | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def weights_sum_to_100(self):
        if self.simulation_model != "historical":
            # The UI only exposes this switch for Historical Returns. Do not let a
            # stale browser session silently change the NAV window for another model.
            self.use_full_history = None
        proj_ids = [holding.proj_id for holding in self.holdings]
        if len(proj_ids) != len(set(proj_ids)):
            raise ValueError("holdings must not contain duplicate proj_id values")
        total = sum(h.weight for h in self.holdings)
        if abs(total - 100.0) > 0.05:
            raise ValueError(f"holding weights must sum to 100, got {total}")
        if self.tax_treatment == "after_tax" and self.tax_rate is None:
            raise ValueError("after_tax requires an explicit tax_rate between 0 and 1")
        if self.simulation_model in {"forecasted", "statistical"} and self.time_series_model is None:
            raise ValueError("forecasted and statistical models require time_series_model")
        if self.simulation_model != "statistical" and self.rebalancing != "none":
            raise ValueError("rebalancing is only supported by the Statistical model")
        if self.simulation_model == "statistical" and self.time_series_model == "garch" and self.rebalancing != "none":
            raise ValueError("rebalancing is not supported by the portfolio-level GARCH model")
        if self.cashflow_mode != "none":
            if self.cashflow_amount is None or self.cashflow_frequency is None:
                raise ValueError("cashflow modes require cashflow_amount and cashflow_frequency")
            if self.cashflow_mode == "withdraw_percent" and self.cashflow_amount > 100:
                raise ValueError("withdraw_percent cashflow_amount must be at most 100")
        if self.multi_goal_enabled:
            if not self.goals:
                raise ValueError("multi_goal_enabled requires at least one named goal")
            for goal in self.goals:
                if goal.ends_year > self.simulation_period_years:
                    raise ValueError("named goal ends_year cannot exceed simulation horizon")
            multistage_values = (
                self.years_to_retirement,
                self.glide_path_years,
                self.retirement_holdings,
            )
            if any(value is not None for value in multistage_values):
                if not all(value is not None for value in multistage_values):
                    raise ValueError(
                        "glide-path composition requires years_to_retirement, glide_path_years, "
                        "and retirement_holdings together"
                    )
                if self.years_to_retirement > self.simulation_period_years:
                    raise ValueError("years_to_retirement cannot exceed simulation horizon")
                if self.glide_path_years > self.years_to_retirement:
                    raise ValueError("glide_path_years cannot exceed years_to_retirement")
                retirement_ids = [holding.proj_id for holding in self.retirement_holdings]
                if set(retirement_ids) != set(proj_ids):
                    raise ValueError(
                        "retirement_holdings must use the same fund IDs as holdings; "
                        "the glide path changes weights, not the selected universe"
                    )
        if self.retirement_holdings is not None:
            retirement_ids = [holding.proj_id for holding in self.retirement_holdings]
            if len(retirement_ids) != len(set(retirement_ids)):
                raise ValueError("retirement_holdings must not contain duplicate proj_id values")
            retirement_total = sum(holding.weight for holding in self.retirement_holdings)
            if abs(retirement_total - 100.0) > 0.05:
                raise ValueError(f"retirement_holdings weights must sum to 100, got {retirement_total}")
            retirement_by_id = {holding.proj_id: holding for holding in self.retirement_holdings}
            # The engine stores weights in the primary holdings' order. Canonicalize
            # here so a user-editable retirement table can never swap allocations merely
            # because its rows were entered in a different order.
            self.retirement_holdings = [retirement_by_id[proj_id] for proj_id in proj_ids]
        return self

    @model_validator(mode="after")
    def parameterized_requires_return_and_volatility(self):
        if self.simulation_model == "parameterized":
            if self.expected_return is None or self.expected_volatility is None or self.distribution is None:
                raise ValueError("parameterized model requires expected_return, expected_volatility, distribution")
            if self.distribution == "fat_tailed" and (self.degrees_of_freedom is None or self.degrees_of_freedom <= 2):
                raise ValueError("fat_tailed distribution requires degrees_of_freedom greater than 2")
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
    goals: dict | None = None
    run_config: dict
