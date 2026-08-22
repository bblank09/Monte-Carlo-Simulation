export interface Holding {
  proj_id: string;
  weight: number;
}

export interface SimulateRequest {
  holdings: Holding[];
  initial_amount: number;
  simulation_period_years: number;
  tax_treatment: "pre_tax" | "after_tax";
  tax_rate?: number;
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
  /** Cashflow modes implemented by the backend engine. */
  cashflow_mode?: "none" | "contribute" | "withdraw_fixed" | "withdraw_percent";
  cashflow_amount?: number;
  cashflow_inflation_adjusted?: boolean;
  cashflow_frequency?: "monthly" | "quarterly" | "annually";
  multi_goal_enabled?: boolean;
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
  run_id: string;
  created_at: string;
  data_source: "sec_open_data";
  overview: Record<string, unknown>;
  growth: Record<string, unknown>;
  distribution: Record<string, unknown>;
  metrics: Record<string, unknown>;
  risk: Record<string, unknown>;
  goals: Record<string, unknown> | null;
  run_config: Record<string, unknown>;
}

// The fund contract intentionally matches Backtest Portfolio's SecFund exactly.
// Monte Carlo changes the simulation objective, not the SEC universe or picker.
export interface FundSummary {
  proj_id: string;
  unique_id: string;
  fund_class_name: string;
  class_abbr_name: string;
  display_name: string;
  search_term: string;
  amc_name_th: string;
  amc_name_en: string;
  policy_desc: string;
  nav_start: string | null;
  nav_end: string | null;
  nav_months: number | null;
  nav_span_months: number | null;
  nav_completeness: number | null;
  nav_gap_count: number | null;
  nav_largest_gap_start: string | null;
  nav_largest_gap_end: string | null;
  nav_available: boolean;
  nav_observations?: number | null;
  nav_min_observations?: number;
  nav_availability_reason?: string | null;
}
