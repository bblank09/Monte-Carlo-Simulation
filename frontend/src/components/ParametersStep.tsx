import { useState } from "react";
import { Info } from "lucide-react";
import type { Holding, NamedGoal, SimulateRequest } from "../types/simulate";

const SIMULATION_MODEL_HELP = "Controls how randomness is generated: Historical replays real past returns, Forecasted and Statistical simulate returns from a time-series model, and Parameterized draws from a distribution you define directly.";
const BOOTSTRAP_MODEL_HELP = "Determines how chunks of historical returns are resampled to build each simulated path (by single month, single year, or multi-year block).";
const SEQUENCE_OF_RETURNS_RISK_HELP = "Front-loads the worst historical years so you can see how a bad early sequence of returns affects the outcome.";
const TIME_SERIES_MODEL_HELP = "Normal assumes constant volatility over time; GARCH lets volatility cluster and change, closer to real market behavior.";

function defaultGoal(horizon: number): NamedGoal {
  return {
    purpose: "Retirement spending",
    is_withdrawal: true,
    amount: 5_000,
    inflation_adjusted: true,
    frequency: "monthly",
    starts_year: 1,
    ends_year: horizon,
  };
}

function InfoTip({ text }: { text: string }) {
  return (
    <span className="info-icon" title={text}>
      <Info aria-hidden="true" size={13} />
    </span>
  );
}
interface Props {
  active: boolean;
  value: SimulateRequest;
  onChange: (value: SimulateRequest) => void;
  onBack: () => void;
  onContinue: () => void;
  running?: boolean;
}

export function ParametersStep({ active, value, onChange, onBack, onContinue, running = false }: Props) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  function patch(fields: Partial<SimulateRequest>) {
    onChange({ ...value, ...fields });
  }

  function markTouched(field: string) {
    setTouched((current) => ({ ...current, [field]: true }));
  }

  const fieldErrors: Record<string, string> = {};
  if (!Number.isFinite(value.initial_amount) || value.initial_amount <= 0) {
    fieldErrors.initial_amount = "Initial amount must be greater than 0.";
  }
  if (!Number.isInteger(value.simulation_period_years) || value.simulation_period_years < 5 || value.simulation_period_years > 75) {
    fieldErrors.simulation_period_years = "Simulation period must be between 5 and 75 years.";
  }
  if (!Number.isInteger(value.n_paths) || value.n_paths > 20000) {
    fieldErrors.n_paths = "Number of paths cannot exceed 20,000.";
  } else if (value.n_paths < 1000) {
    fieldErrors.n_paths = "Fewer than 1,000 paths gives statistically unreliable percentile estimates.";
  }
  if (value.tax_treatment === "after_tax" && (!Number.isFinite(value.tax_rate) || (value.tax_rate ?? -1) < 0 || (value.tax_rate ?? 2) > 1)) {
    fieldErrors.tax_rate = "After-tax simulations require a tax rate between 0% and 100%.";
  }
  if ((value.simulation_model === "forecasted" || value.simulation_model === "statistical") && !value.time_series_model) {
    fieldErrors.time_series_model = "Choose a time-series model.";
  }
  if (value.simulation_model === "parameterized") {
    if (value.expected_return === undefined || value.expected_return === null || !Number.isFinite(value.expected_return)) {
      fieldErrors.expected_return = "Expected return is required.";
    }
    if (!Number.isFinite(value.expected_volatility) || !((value.expected_volatility ?? 0) > 0)) {
      fieldErrors.expected_volatility = "Expected volatility must be greater than 0.";
    }
    if (!value.distribution) {
      fieldErrors.distribution = "Choose a return distribution.";
    }
    if (value.distribution === "fat_tailed" && (
      !Number.isFinite(value.degrees_of_freedom) || !((value.degrees_of_freedom ?? 0) > 2)
    )) {
      fieldErrors.degrees_of_freedom = "Degrees of freedom must be greater than 2 for a fat-tailed distribution.";
    }
  }
  if (value.cashflow_mode && value.cashflow_mode !== "none" && (
    !Number.isFinite(value.cashflow_amount) || !((value.cashflow_amount ?? 0) > 0)
  )) {
    fieldErrors.cashflow_amount = "Cashflow amount must be greater than 0.";
  }
  if (value.inflation_model === "parameterized") {
    if (!Number.isFinite(value.inflation_mean)) fieldErrors.inflation_mean = "Inflation mean must be a number.";
    if (!Number.isFinite(value.inflation_volatility) || !((value.inflation_volatility ?? 0) > 0)) {
      fieldErrors.inflation_volatility = "Inflation volatility must be greater than 0.";
    }
  }
  if (value.simulation_model === "historical" && value.bootstrap_model === "block_of_years" && (!Number.isInteger(value.block_years) || (value.block_years ?? 0) < 1)) {
    fieldErrors.block_years = "Block size must be at least 1 year.";
  }
  const supportsRebalancing = value.simulation_model === "statistical" && (value.time_series_model ?? "normal") === "normal";
  if (!supportsRebalancing && value.rebalancing !== "none") {
    fieldErrors.rebalancing = "Rebalancing is available for Statistical Normal returns only.";
  }
  if (value.multi_goal_enabled) {
    const goals = value.goals ?? [];
    if (!goals.length) fieldErrors.goals = "Add at least one named goal.";
    for (const [index, goal] of goals.entries()) {
      if (!goal.purpose.trim() || goal.amount <= 0 || goal.starts_year >= goal.ends_year || goal.ends_year > value.simulation_period_years) {
        fieldErrors[`goal-${index}`] = "Each goal needs a purpose, positive amount, and valid years within the horizon.";
      }
    }
    if (!Number.isInteger(value.years_to_retirement) || (value.years_to_retirement ?? 0) < 1 || (value.years_to_retirement ?? 0) > value.simulation_period_years) {
      fieldErrors.years_to_retirement = "Years to retirement must be within the simulation horizon.";
    }
    if (!Number.isInteger(value.glide_path_years) || (value.glide_path_years ?? 0) < 1 || (value.glide_path_years ?? 0) > (value.years_to_retirement ?? 0)) {
      fieldErrors.glide_path_years = "Glide path years must be between 1 and years to retirement.";
    }
    const retirementTotal = (value.retirement_holdings ?? []).reduce((sum, holding) => sum + holding.weight, 0);
    const primaryIds = new Set(value.holdings.map((holding) => holding.proj_id));
    const retirementIds = new Set((value.retirement_holdings ?? []).map((holding) => holding.proj_id));
    if (!value.retirement_holdings?.length || Math.abs(retirementTotal - 100) > 0.05) {
      fieldErrors.retirement_holdings = "Retirement allocation weights must sum to 100%.";
    } else if (primaryIds.size !== retirementIds.size || [...primaryIds].some((projId) => !retirementIds.has(projId))) {
      fieldErrors.retirement_holdings = "Use the same fund IDs as the starting allocation; only weights change along the glide path.";
    }
  }
  function fieldError(field: string): string | null {
    return touched[field] ? (fieldErrors[field] ?? null) : null;
  }
  const canContinue = !running && Object.keys(fieldErrors).length === 0;

  function changeSimulationModel(simulation_model: SimulateRequest["simulation_model"]) {
    const timeSeriesModel = value.time_series_model ?? "normal";
    onChange({
      ...value,
      simulation_model,
      use_full_history: simulation_model === "historical" ? (value.use_full_history ?? true) : undefined,
      rebalancing: simulation_model === "statistical" && timeSeriesModel === "normal" ? value.rebalancing : "none",
    });
  }

  function changeTimeSeriesModel(time_series_model: SimulateRequest["time_series_model"]) {
    patch({
      time_series_model,
      rebalancing: time_series_model === "normal" ? value.rebalancing : "none",
    });
  }

  function toggleGoals(enabled: boolean) {
    const goals = value.goals?.length ? value.goals : [defaultGoal(value.simulation_period_years)];
    const retirementHoldings = value.retirement_holdings?.length ? value.retirement_holdings : value.holdings;
    patch({
      multi_goal_enabled: enabled,
      goals,
      years_to_retirement: value.years_to_retirement ?? Math.max(1, Math.floor(value.simulation_period_years / 2)),
      glide_path_years: value.glide_path_years ?? Math.min(5, Math.max(1, Math.floor(value.simulation_period_years / 2))),
      retirement_holdings: retirementHoldings,
    });
  }

  function updateGoal(index: number, fields: Partial<NamedGoal>) {
    const goals = [...(value.goals ?? [])];
    goals[index] = { ...goals[index], ...fields };
    patch({ goals });
  }

  function addGoal() {
    patch({ goals: [...(value.goals ?? []), defaultGoal(value.simulation_period_years)] });
  }

  function removeGoal(index: number) {
    patch({ goals: (value.goals ?? []).filter((_, goalIndex) => goalIndex !== index) });
  }

  function updateRetirementHolding(index: number, fields: Partial<Holding>) {
    const retirementHoldings = [...(value.retirement_holdings ?? [])];
    retirementHoldings[index] = { ...retirementHoldings[index], ...fields };
    patch({ retirement_holdings: retirementHoldings });
  }

  return (
    <div className={active ? "page active" : "page"}>
      <div className="page-head">
        <h1>Set your simulation assumptions</h1>
        <p>Choose a simulation model and configure the assumptions behind it.</p>
      </div>

      <div className="card">
        {/* ===== Core Parameters ===== */}
        <div className="section-title">Core</div>
        <div className="form-grid">
          <div className="form-field">
            <label htmlFor="initial_amount">Initial Amount</label>
            <input
              className="field num"
              id="initial_amount"
              min={0}
              type="number"
              value={value.initial_amount}
              onChange={(e) => patch({ initial_amount: Number(e.target.value) })}
              onBlur={() => markTouched("initial_amount")}
            />
            {fieldError("initial_amount") && <div className="field-error">{fieldError("initial_amount")}</div>}
          </div>
          <div className="form-field">
            <label htmlFor="simulation_period_years">Simulation Period in Years</label>
            <input
              className="field num"
              id="simulation_period_years"
              min={5}
              max={75}
              step={5}
              type="number"
              value={value.simulation_period_years}
              onChange={(e) => patch({ simulation_period_years: Number(e.target.value) })}
              onBlur={() => markTouched("simulation_period_years")}
            />
            {fieldError("simulation_period_years") && <div className="field-error">{fieldError("simulation_period_years")}</div>}
          </div>
          <div className="form-field">
            <label htmlFor="tax_treatment">Tax Treatment</label>
            <select
              className="field"
              id="tax_treatment"
              value={value.tax_treatment}
              onChange={(e) => patch({ tax_treatment: e.target.value as SimulateRequest["tax_treatment"] })}
            >
              <option value="pre_tax">Pre-tax Returns</option>
              <option value="after_tax">After-tax Returns</option>
            </select>
          </div>
          {value.tax_treatment === "after_tax" ? (
            <div className="form-field">
              <label htmlFor="tax_rate">Effective tax rate</label>
              <input
                className="field num"
                id="tax_rate"
                min={0}
                max={100}
                step={1}
                type="number"
                value={(value.tax_rate ?? 0.2) * 100}
                onChange={(e) => patch({ tax_rate: Number(e.target.value) / 100 })}
                onBlur={() => markTouched("tax_rate")}
              />
              {fieldError("tax_rate") && <div className="field-error">{fieldError("tax_rate")}</div>}
            </div>
          ) : null}
          <div className="form-field">
            <label htmlFor="simulation_model" className="label-with-info">Simulation Model <InfoTip text={SIMULATION_MODEL_HELP} /></label>
            <select
              className="field"
              id="simulation_model"
              value={value.simulation_model}
              onChange={(e) => changeSimulationModel(e.target.value as SimulateRequest["simulation_model"])}
            >
              <option value="historical">Historical Returns</option>
              <option value="forecasted">Forecasted Returns</option>
              <option value="statistical">Statistical Returns</option>
              <option value="parameterized">Parameterized Returns</option>
            </select>
          </div>
        </div>

        {/* ===== Historical Model Settings ===== */}
        {value.simulation_model === "historical" && (
          <>
            <div className="section-title section-title-spaced">Historical Model Settings</div>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="use_full_history">Use Full History</label>
                <select
                  className="field"
                  id="use_full_history"
                  value={value.use_full_history ? "yes" : "no"}
                  onChange={(e) => patch({ use_full_history: e.target.value === "yes" })}
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>
            </div>
          </>
        )}

        {/* ===== Time Series Model ===== */}
        {(value.simulation_model === "forecasted" || value.simulation_model === "statistical") && (
          <>
            <div className="section-title section-title-spaced">Time Series Model</div>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="time_series_model" className="label-with-info">Model Type <InfoTip text={TIME_SERIES_MODEL_HELP} /></label>
                <select
                  className="field"
                  id="time_series_model"
                  value={value.time_series_model ?? "normal"}
                  onChange={(e) => changeTimeSeriesModel(e.target.value as SimulateRequest["time_series_model"])}
                >
                  <option value="normal">Normal</option>
                  <option value="garch">GARCH</option>
                </select>
                {fieldError("time_series_model") && <div className="field-error">{fieldError("time_series_model")}</div>}
              </div>
            </div>
          </>
        )}

        {/* ===== Parameterized Distribution ===== */}
        {value.simulation_model === "parameterized" && (
          <>
            <div className="section-title section-title-spaced">Parameterized Distribution</div>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="distribution">Distribution</label>
                <select
                  className="field"
                  id="distribution"
                  value={value.distribution ?? "normal"}
                  onChange={(e) => patch({
                    distribution: e.target.value as SimulateRequest["distribution"],
                    degrees_of_freedom: e.target.value === "fat_tailed" ? (value.degrees_of_freedom ?? 5) : value.degrees_of_freedom,
                  })}
                >
                  <option value="normal">Normal</option>
                  <option value="fat_tailed">Fat-tailed (Student-t)</option>
                </select>
                {fieldError("distribution") && <div className="field-error">{fieldError("distribution")}</div>}
              </div>
              {value.distribution === "fat_tailed" && (
                <div className="form-field">
                  <label htmlFor="degrees_of_freedom">Degrees of Freedom</label>
                  <input
                    className="field num"
                    id="degrees_of_freedom"
                    min={1}
                    type="number"
                    value={value.degrees_of_freedom ?? 5}
                    onChange={(e) => patch({ degrees_of_freedom: Number(e.target.value) })}
                    onBlur={() => markTouched("degrees_of_freedom")}
                  />
                  {fieldError("degrees_of_freedom") && <div className="field-error">{fieldError("degrees_of_freedom")}</div>}
                </div>
              )}
              <div className="form-field">
                <label htmlFor="expected_return">Expected Return</label>
                <input
                  className="field num"
                  id="expected_return"
                  step="0.01"
                  type="number"
                  value={value.expected_return ?? 0}
                  onChange={(e) => patch({ expected_return: Number(e.target.value) })}
                  onBlur={() => markTouched("expected_return")}
                />
                {fieldError("expected_return") && <div className="field-error">{fieldError("expected_return")}</div>}
              </div>
              <div className="form-field">
                <label htmlFor="expected_volatility">Expected Volatility</label>
                <input
                  className="field num"
                  id="expected_volatility"
                  step="0.01"
                  type="number"
                  value={value.expected_volatility ?? 0}
                  onChange={(e) => patch({ expected_volatility: Number(e.target.value) })}
                  onBlur={() => markTouched("expected_volatility")}
                />
                {fieldError("expected_volatility") && <div className="field-error">{fieldError("expected_volatility")}</div>}
              </div>
            </div>
          </>
        )}

        {/* ===== Single Cashflow ===== */}
        <div className="section-title section-title-spaced">Cashflow</div>
        <div className="form-grid">
          <div className="form-field">
            <label htmlFor="cashflow_mode">Cashflow mode</label>
            <select
              className="field"
              id="cashflow_mode"
              value={value.cashflow_mode ?? "none"}
              onChange={(e) => patch({ cashflow_mode: e.target.value as SimulateRequest["cashflow_mode"] })}
            >
              <option value="none">No contributions or withdrawals</option>
              <option value="contribute">Contribute fixed amount periodically</option>
              <option value="withdraw_fixed">Withdraw fixed amount periodically</option>
              <option value="withdraw_percent">Withdraw fixed percentage periodically</option>
            </select>
          </div>
          {value.cashflow_mode && value.cashflow_mode !== "none" ? (
            <>
              <div className="form-field">
                <label htmlFor="cashflow_amount">Amount</label>
                <input
                  className="field num"
                  id="cashflow_amount"
                  min={0}
                  type="number"
                  value={value.cashflow_amount ?? 0}
                  onChange={(e) => patch({ cashflow_amount: Number(e.target.value) })}
                  onBlur={() => markTouched("cashflow_amount")}
                />
                {fieldError("cashflow_amount") && <div className="field-error">{fieldError("cashflow_amount")}</div>}
              </div>
              <div className="form-field">
                <label htmlFor="cashflow_inflation_adjusted">Inflation Adjusted</label>
                <select
                  className="field"
                  id="cashflow_inflation_adjusted"
                  value={value.cashflow_inflation_adjusted ? "yes" : "no"}
                  onChange={(e) => patch({ cashflow_inflation_adjusted: e.target.value === "yes" })}
                >
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>
              <div className="form-field">
                <label htmlFor="cashflow_frequency">Frequency</label>
                <select
                  className="field"
                  id="cashflow_frequency"
                  value={value.cashflow_frequency ?? "annually"}
                  onChange={(e) => patch({ cashflow_frequency: e.target.value as SimulateRequest["cashflow_frequency"] })}
                >
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="annually">Annually</option>
                </select>
              </div>
            </>
          ) : null}
        </div>

        {/* ===== Goals & Glide Path ===== */}
        <div className="section-title section-title-spaced">Goals &amp; glide path</div>
        <label className="check-row" htmlFor="multi_goal_enabled">
          <input
            checked={Boolean(value.multi_goal_enabled)}
            id="multi_goal_enabled"
            onChange={(event) => toggleGoals(event.target.checked)}
            type="checkbox"
          />
          <span>Enable named goals and glide path</span>
        </label>
        {value.multi_goal_enabled ? (
          <div className="goals-editor">
            <div className="goals-table">
              <div className="goals-head">
                <div>Purpose</div><div>Amount</div><div>Type</div><div>Inflation</div><div>Frequency</div><div>Starts</div><div>Ends</div><div />
              </div>
              {(value.goals ?? []).map((goal, index) => (
                <div className="goal-row" key={`goal-${index}`}>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`goal-purpose-${index}`}>Goal purpose {index + 1}</label>
                    <input className="field" id={`goal-purpose-${index}`} value={goal.purpose} onChange={(event) => updateGoal(index, { purpose: event.target.value })} />
                  </div>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`goal-amount-${index}`}>Goal amount {index + 1}</label>
                    <input className="field num" id={`goal-amount-${index}`} min={0} type="number" value={goal.amount} onChange={(event) => updateGoal(index, { amount: Number(event.target.value) })} />
                  </div>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`goal-type-${index}`}>Goal type {index + 1}</label>
                    <select className="field" id={`goal-type-${index}`} value={goal.is_withdrawal ? "withdrawal" : "contribution"} onChange={(event) => updateGoal(index, { is_withdrawal: event.target.value === "withdrawal" })}>
                      <option value="withdrawal">Withdrawal</option>
                      <option value="contribution">Contribution</option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`goal-inflation-${index}`}>Goal inflation {index + 1}</label>
                    <select className="field" id={`goal-inflation-${index}`} value={goal.inflation_adjusted ? "yes" : "no"} onChange={(event) => updateGoal(index, { inflation_adjusted: event.target.value === "yes" })}>
                      <option value="yes">Adjusted</option>
                      <option value="no">Fixed</option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`goal-frequency-${index}`}>Goal frequency {index + 1}</label>
                    <select className="field" id={`goal-frequency-${index}`} value={goal.frequency} onChange={(event) => updateGoal(index, { frequency: event.target.value as NamedGoal["frequency"] })}>
                      <option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="annually">Annually</option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`goal-start-${index}`}>Goal starts year {index + 1}</label>
                    <input className="field num" id={`goal-start-${index}`} min={0} type="number" value={goal.starts_year} onChange={(event) => updateGoal(index, { starts_year: Number(event.target.value) })} />
                  </div>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`goal-end-${index}`}>Goal ends year {index + 1}</label>
                    <input className="field num" id={`goal-end-${index}`} min={1} type="number" value={goal.ends_year} onChange={(event) => updateGoal(index, { ends_year: Number(event.target.value) })} />
                  </div>
                  <button aria-label={`Remove goal ${index + 1}`} className="icon-btn" disabled={(value.goals ?? []).length <= 1} onClick={() => removeGoal(index)} type="button">&times;</button>
                  {fieldError(`goal-${index}`) ? <div className="field-error">{fieldError(`goal-${index}`)}</div> : null}
                </div>
              ))}
            </div>
            {fieldError("goals") ? <div className="field-error">{fieldError("goals")}</div> : null}
            <button className="link-btn goals-add" onClick={addGoal} type="button">+ Add named goal</button>
            <div className="form-grid section-title-spaced">
              <div className="form-field">
                <label htmlFor="years_to_retirement">Years to retirement</label>
                <input className="field num" id="years_to_retirement" min={1} type="number" value={value.years_to_retirement ?? 1} onChange={(event) => patch({ years_to_retirement: Number(event.target.value) })} onBlur={() => markTouched("years_to_retirement")} />
                {fieldError("years_to_retirement") ? <div className="field-error">{fieldError("years_to_retirement")}</div> : null}
              </div>
              <div className="form-field">
                <label htmlFor="glide_path_years">Glide path years</label>
                <input className="field num" id="glide_path_years" min={1} type="number" value={value.glide_path_years ?? 1} onChange={(event) => patch({ glide_path_years: Number(event.target.value) })} onBlur={() => markTouched("glide_path_years")} />
                {fieldError("glide_path_years") ? <div className="field-error">{fieldError("glide_path_years")}</div> : null}
              </div>
            </div>
            <div className="section-title section-title-spaced">Retirement allocation</div>
            <p className="field-hint">The glide path changes weights across the same selected funds.</p>
            <div className="holdings-table">
              {(value.retirement_holdings ?? []).map((holding, index) => (
                <div className="holdings-row" key={`retirement-holding-${index}`}>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`retirement-proj-${index}`}>Retirement fund {index + 1}</label>
                    <input className="field" id={`retirement-proj-${index}`} value={holding.proj_id} onChange={(event) => updateRetirementHolding(index, { proj_id: event.target.value })} />
                  </div>
                  <div className="form-field">
                    <label className="sr-only" htmlFor={`retirement-weight-${index}`}>Retirement weight {index + 1}</label>
                    <input className="field num" id={`retirement-weight-${index}`} min={0} max={100} type="number" value={holding.weight} onChange={(event) => updateRetirementHolding(index, { weight: Number(event.target.value) })} />
                  </div>
                  <div />
                </div>
              ))}
            </div>
            {fieldError("retirement_holdings") ? <div className="field-error">{fieldError("retirement_holdings")}</div> : null}
          </div>
        ) : null}

        {/* ===== Inflation & Rebalancing ===== */}
        <div className="section-title section-title-spaced">Inflation &amp; Rebalancing</div>
        <div className="form-grid">
          <div className="form-field">
            <label htmlFor="inflation_model">Inflation Model</label>
            <select
              className="field"
              id="inflation_model"
              value={value.inflation_model}
              onChange={(e) => patch({ inflation_model: e.target.value as SimulateRequest["inflation_model"] })}
            >
              <option value="historical">Historical Inflation</option>
              <option value="parameterized">Parameterized Inflation</option>
            </select>
          </div>
          {value.inflation_model === "parameterized" && (
            <>
              <div className="form-field">
                <label htmlFor="inflation_mean">Mean</label>
                <input
                  className="field num"
                  id="inflation_mean"
                  step="0.001"
                  type="number"
                  value={value.inflation_mean ?? 0.03}
                  onChange={(e) => patch({ inflation_mean: Number(e.target.value) })}
                  onBlur={() => markTouched("inflation_mean")}
                />
                {fieldError("inflation_mean") && <div className="field-error">{fieldError("inflation_mean")}</div>}
              </div>
              <div className="form-field">
                <label htmlFor="inflation_volatility">Volatility</label>
                <input
                  className="field num"
                  id="inflation_volatility"
                  step="0.001"
                  type="number"
                  value={value.inflation_volatility ?? 0.01}
                  onChange={(e) => patch({ inflation_volatility: Number(e.target.value) })}
                  onBlur={() => markTouched("inflation_volatility")}
                />
                {fieldError("inflation_volatility") && <div className="field-error">{fieldError("inflation_volatility")}</div>}
              </div>
            </>
          )}
          {supportsRebalancing ? (
            <div className="form-field">
              <label htmlFor="rebalancing">Rebalancing</label>
              <select className="field" id="rebalancing" value={value.rebalancing} onChange={(e) => patch({ rebalancing: e.target.value as SimulateRequest["rebalancing"] })}>
                <option value="none">No rebalancing</option>
                <option value="annual">Rebalance annually</option>
                <option value="semiannual">Rebalance semi-annually</option>
                <option value="quarterly">Rebalance quarterly</option>
                <option value="monthly">Rebalance monthly</option>
              </select>
            </div>
          ) : (
            <p className="field-hint">Rebalancing is available for Statistical Normal returns only.</p>
          )}
          {fieldError("rebalancing") ? <div className="field-error">{fieldError("rebalancing")}</div> : null}
        </div>

        {/* ===== Advanced Settings (optional) ===== */}
        <button
          aria-controls="advanced-settings"
          aria-expanded={advancedOpen}
          className={advancedOpen ? "advanced-toggle open" : "advanced-toggle"}
          onClick={() => setAdvancedOpen((open) => !open)}
          type="button"
        >
          <span className="chev">&#9654;</span> Advanced settings
        </button>
        <div className={advancedOpen ? "advanced-body open" : "advanced-body"} id="advanced-settings">
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="n_paths">Number of Simulation Paths</label>
              <input
                className="field num"
                id="n_paths"
                min={1}
                max={20000}
                type="number"
                value={value.n_paths}
                onChange={(e) => patch({ n_paths: Number(e.target.value) })}
                onBlur={() => markTouched("n_paths")}
              />
              {fieldError("n_paths") && <div className="field-error">{fieldError("n_paths")}</div>}
            </div>
            {value.simulation_model === "historical" && (
              <>
                <div className="form-field">
                  <label htmlFor="bootstrap_model" className="label-with-info">Bootstrap Model <InfoTip text={BOOTSTRAP_MODEL_HELP} /></label>
                  <select
                    className="field"
                    id="bootstrap_model"
                    value={value.bootstrap_model ?? "single_year"}
                    onChange={(e) => patch({ bootstrap_model: e.target.value as SimulateRequest["bootstrap_model"] })}
                  >
                    <option value="single_month">Single Month</option>
                    <option value="single_year">Single Year</option>
                    <option value="block_of_years">Block of Years</option>
                  </select>
                </div>
                <div className="form-field">
                  <label htmlFor="sequence_of_returns_risk" className="label-with-info">Sequence of Returns Risk <InfoTip text={SEQUENCE_OF_RETURNS_RISK_HELP} /></label>
                  <select
                    className="field"
                    id="sequence_of_returns_risk"
                    value={value.sequence_of_returns_risk ?? 0}
                    onChange={(e) => patch({ sequence_of_returns_risk: Number(e.target.value) })}
                  >
                    <option value={0}>No Adjustments</option>
                    {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                      <option key={n} value={n}>Worst {n} Year{n > 1 ? "s" : ""} First</option>
                    ))}
                  </select>
                  {fieldError("sequence_of_returns_risk") && <div className="field-error">{fieldError("sequence_of_returns_risk")}</div>}
                </div>
                {value.bootstrap_model === "block_of_years" && (
                  <div className="form-field">
                    <label htmlFor="block_years">Block Size (years)</label>
                    <input
                      className="field num"
                      id="block_years"
                      min={1}
                      type="number"
                      value={value.block_years ?? 1}
                      onChange={(e) => patch({ block_years: Number(e.target.value) })}
                      onBlur={() => markTouched("block_years")}
                    />
                    {fieldError("block_years") && <div className="field-error">{fieldError("block_years")}</div>}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* ===== Review Box ===== */}
      <div className="review-box">
        Run <b>{value.simulation_model}</b> simulation for <b>{value.simulation_period_years} years</b> with initial amount <b>{value.initial_amount.toLocaleString()}</b> using <b>{value.n_paths.toLocaleString()} paths</b>
        {value.cashflow_mode && value.cashflow_mode !== "none" ? <>, with <b>{value.cashflow_mode}</b> cashflows</> : null}
        {value.rebalancing !== "none" ? <>, rebalanced <b>{value.rebalancing}</b></> : null}.
      </div>

      {/* ===== Actions ===== */}
      <div className="actions">
        <button className="btn btn-ghost" onClick={onBack} type="button">&larr; Back</button>
        <button className="btn btn-primary" disabled={!canContinue} onClick={onContinue} type="button">
          {running ? (
            <>
              <span className="spinner" /> Running&hellip;
            </>
          ) : (
            <>Continue to Results &rarr;</>
          )}
        </button>
      </div>
    </div>
  );
}
