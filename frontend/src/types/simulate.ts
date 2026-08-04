export interface Holding {
  proj_id: string;
  weight: number;
}

export interface SimulateRequest {
  holdings: Holding[];
  initial_amount: number;
  simulation_period_years: number;
  tax_treatment: "pre_tax" | "after_tax";
  simulation_model: "historical" | "forecasted" | "statistical" | "parameterized";
  n_paths: number;
  seed?: number;
  rebalancing: "none" | "annual" | "semiannual" | "quarterly" | "monthly";
  use_full_history?: boolean;
  bootstrap_model?: "single_month" | "single_year" | "block_of_years";
  block_years?: number;
  sequence_of_returns_risk?: number;
  time_series_model?: "normal" | "garch";
  distribution?: "normal" | "fat_tailed";
  degrees_of_freedom?: number;
  expected_return?: number;
  expected_volatility?: number;
  cashflow_mode: "none" | "contribute" | "withdraw_fixed" | "withdraw_percent" | "rolling_average_spending" | "geometric_spending" | "withdraw_life_expectancy";
  cashflow_amount?: number;
  cashflow_inflation_adjusted?: boolean;
  cashflow_frequency?: "monthly" | "quarterly" | "annually";
  multi_goal_enabled: boolean;
  goals?: NamedGoal[];
  years_to_retirement?: number;
  glide_path_years?: number;
  retirement_holdings?: Holding[];
  inflation_model: "historical" | "parameterized";
  inflation_mean?: number;
  inflation_volatility?: number;
}

export interface NamedGoal {
  purpose: string;
  is_withdrawal: boolean;
  amount: number;
  inflation_adjusted: boolean;
  frequency: "monthly" | "quarterly" | "annually";
  starts_year: number;
  ends_year: number;
}

export interface SimulateResponse {
  overview: Record<string, unknown>;
  growth: Record<string, unknown>;
  distribution: Record<string, unknown>;
  metrics: Record<string, unknown>;
  risk: Record<string, unknown>;
  goals: Record<string, unknown> | null;
  run_config: Record<string, unknown>;
}

// --- Deviations from the task-16 brief (documented in task-16-report.md) ---
//
// FundSummary: not specified in the brief, but frontend/src/api/client.ts
// (Task 14/14b) already defines it inline as the getFunds() return shape.
// Hoisted here so client.ts/mockData.ts/PortfolioStep.tsx share one
// definition instead of three ad hoc copies.
export interface FundSummary {
  proj_id: string;
  proj_name_thai?: string;
  amc_name_thai?: string;
}
