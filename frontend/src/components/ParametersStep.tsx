import { useState } from "react";
import type { SimulateRequest, NamedGoal, FundSummary, Holding } from "../types/simulate";

interface Props {
  active: boolean;
  value: SimulateRequest;
  onChange: (value: SimulateRequest) => void;
  onBack: () => void;
  onContinue: () => void;
  funds: FundSummary[];
}

export function ParametersStep({ active, value, onChange, onBack, onContinue, funds }: Props) {
  const [multiGoal, setMultiGoal] = useState(value.multi_goal_enabled);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  function patch(fields: Partial<SimulateRequest>) {
    onChange({ ...value, ...fields });
  }

  function toggleMultiGoal(enabled: boolean) {
    setMultiGoal(enabled);
    patch({
      multi_goal_enabled: enabled,
      goals: enabled ? (value.goals ?? []) : undefined,
      years_to_retirement: enabled ? (value.years_to_retirement ?? 20) : undefined,
      glide_path_years: enabled ? (value.glide_path_years ?? 10) : undefined,
    });
  }

  const goalsSummary = multiGoal && value.goals && value.goals.length > 0
    ? `${value.goals.length} goal${value.goals.length !== 1 ? "s" : ""}`
    : "single cashflow mode";

  return (
    <div className={active ? "page active" : "page"}>
      <div className="page-head">
        <h1>Set your simulation parameters</h1>
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
            />
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
            />
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
          <div className="form-field">
            <label htmlFor="simulation_model">Simulation Model</label>
            <select
              className="field"
              id="simulation_model"
              value={value.simulation_model}
              onChange={(e) => patch({ simulation_model: e.target.value as SimulateRequest["simulation_model"] })}
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
            <div className="section-title" style={{ marginTop: 20 }}>Historical Model Settings</div>
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
              <div className="form-field">
                <label htmlFor="bootstrap_model">Bootstrap Model</label>
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
                <label htmlFor="sequence_of_returns_risk">Sequence of Returns Risk</label>
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
              </div>
            </div>
          </>
        )}

        {/* ===== Time Series Model ===== */}
        {(value.simulation_model === "forecasted" || value.simulation_model === "statistical") && (
          <>
            <div className="section-title" style={{ marginTop: 20 }}>Time Series Model</div>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="time_series_model">Model Type</label>
                <select
                  className="field"
                  id="time_series_model"
                  value={value.time_series_model ?? "normal"}
                  onChange={(e) => patch({ time_series_model: e.target.value as SimulateRequest["time_series_model"] })}
                >
                  <option value="normal">Normal</option>
                  <option value="garch">GARCH</option>
                </select>
              </div>
            </div>
          </>
        )}

        {/* ===== Parameterized Distribution ===== */}
        {value.simulation_model === "parameterized" && (
          <>
            <div className="section-title" style={{ marginTop: 20 }}>Parameterized Distribution</div>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="distribution">Distribution</label>
                <select
                  className="field"
                  id="distribution"
                  value={value.distribution ?? "normal"}
                  onChange={(e) => patch({ distribution: e.target.value as SimulateRequest["distribution"] })}
                >
                  <option value="normal">Normal</option>
                  <option value="fat_tailed">Fat-tailed (Student-t)</option>
                </select>
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
                  />
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
                />
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
                />
              </div>
            </div>
          </>
        )}

        {/* ===== Cashflow & Goals ===== */}
        <div className="section-title" style={{ marginTop: 20 }}>Cashflow &amp; Goals</div>
        <div className="form-grid">
          <div className="form-field">
            <label htmlFor="multi_goal">Advanced: multiple goals</label>
            <select
              className="field"
              id="multi_goal"
              value={multiGoal ? "yes" : "no"}
              onChange={(e) => toggleMultiGoal(e.target.value === "yes")}
            >
              <option value="no">Single cashflow</option>
              <option value="yes">Multiple goals</option>
            </select>
          </div>
        </div>

        {!multiGoal ? (
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="cashflow_mode">Cashflow</label>
              <select
                className="field"
                id="cashflow_mode"
                value={value.cashflow_mode}
                onChange={(e) => patch({ cashflow_mode: e.target.value as SimulateRequest["cashflow_mode"] })}
              >
                <option value="none">No contributions or withdrawals</option>
                <option value="contribute">Contribute fixed amount periodically</option>
                <option value="withdraw_fixed">Withdraw fixed amount periodically</option>
                <option value="withdraw_percent">Withdraw fixed percentage periodically</option>
                <option value="rolling_average_spending">Rolling average spending rule</option>
                <option value="geometric_spending">Geometric spending rule</option>
                <option value="withdraw_life_expectancy">Withdraw based on life expectancy</option>
              </select>
            </div>
            {value.cashflow_mode !== "none" && (
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
                  />
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
            )}
          </div>
        ) : (
          <GoalsTable goals={value.goals ?? []} onChange={(goals) => patch({ goals })} />
        )}

        {/* ===== Multistage Planning (when multi-goal enabled) ===== */}
        {multiGoal && (
          <>
            <div className="section-title" style={{ marginTop: 20 }}>Multistage Planning</div>
            <div className="form-grid">
              <div className="form-field">
                <label htmlFor="years_to_retirement">Years to Retirement</label>
                <input
                  className="field num"
                  id="years_to_retirement"
                  min={1}
                  type="number"
                  value={value.years_to_retirement ?? 20}
                  onChange={(e) => patch({ years_to_retirement: Number(e.target.value) })}
                />
              </div>
              <div className="form-field">
                <label htmlFor="glide_path_years">Glide Path Years</label>
                <input
                  className="field num"
                  id="glide_path_years"
                  min={1}
                  type="number"
                  value={value.glide_path_years ?? 10}
                  onChange={(e) => patch({ glide_path_years: Number(e.target.value) })}
                />
              </div>
            </div>
            <div className="section-title" style={{ marginTop: 20 }}>Retirement Portfolio Allocation</div>
            <RetirementAllocationTable
              funds={funds}
              retirementHoldings={value.retirement_holdings ?? []}
              onChange={(retirement_holdings) => patch({ retirement_holdings })}
            />
          </>
        )}

        {/* ===== Inflation & Rebalancing ===== */}
        <div className="section-title" style={{ marginTop: 20 }}>Inflation &amp; Rebalancing</div>
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
                />
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
                />
              </div>
            </>
          )}
          <div className="form-field">
            <label htmlFor="rebalancing">Rebalancing</label>
            <select
              className="field"
              id="rebalancing"
              value={value.rebalancing}
              onChange={(e) => patch({ rebalancing: e.target.value as SimulateRequest["rebalancing"] })}
            >
              <option value="none">No rebalancing</option>
              <option value="annual">Rebalance annually</option>
              <option value="semiannual">Rebalance semi-annually</option>
              <option value="quarterly">Rebalance quarterly</option>
              <option value="monthly">Rebalance monthly</option>
            </select>
          </div>
        </div>

        {/* ===== Advanced Settings (optional) ===== */}
        <div className={advancedOpen ? "advanced-toggle open" : "advanced-toggle"} onClick={() => setAdvancedOpen((open) => !open)}>
          <span className="chev">&#9654;</span> Advanced settings
        </div>
        <div className={advancedOpen ? "advanced-body open" : "advanced-body"}>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="n_paths">Number of Simulation Paths</label>
              <input
                className="field num"
                id="n_paths"
                min={1}
                type="number"
                value={value.n_paths}
                onChange={(e) => patch({ n_paths: Number(e.target.value) })}
              />
            </div>
            {value.simulation_model === "historical" && value.bootstrap_model === "block_of_years" && (
              <div className="form-field">
                <label htmlFor="block_years">Block Size (years)</label>
                <input
                  className="field num"
                  id="block_years"
                  min={1}
                  type="number"
                  value={value.block_years ?? 1}
                  onChange={(e) => patch({ block_years: Number(e.target.value) })}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ===== Review Box ===== */}
      <div className="review-box">
        Run <b>{value.simulation_model}</b> simulation for <b>{value.simulation_period_years} years</b> with initial amount <b>{value.initial_amount.toLocaleString()}</b> using <b>{value.n_paths.toLocaleString()} paths</b>
        {value.cashflow_mode !== "none" && !multiGoal ? <>, with <b>{value.cashflow_mode}</b> mode cashflows</> : null}
        {multiGoal ? <>, with {goalsSummary}</> : null}
        {value.rebalancing !== "none" ? <>, rebalanced <b>{value.rebalancing}</b></> : null}.
      </div>

      {/* ===== Actions ===== */}
      <div className="actions">
        <button className="btn btn-ghost" onClick={onBack} type="button">&larr; Back</button>
        <button className="btn btn-primary" onClick={onContinue} type="button">Continue to Results &rarr;</button>
      </div>
    </div>
  );
}

function GoalsTable({ goals, onChange }: { goals: NamedGoal[]; onChange: (goals: NamedGoal[]) => void }) {
  function addGoal() {
    onChange([...goals, {
      purpose: "", is_withdrawal: true, amount: 0, inflation_adjusted: true,
      frequency: "annually", starts_year: 0, ends_year: 1,
    }]);
  }
  function updateGoal(index: number, fields: Partial<NamedGoal>) {
    onChange(goals.map((g, i) => (i === index ? { ...g, ...fields } : g)));
  }
  function removeGoal(index: number) {
    onChange(goals.filter((_, i) => i !== index));
  }
  return (
    <div className="goals-table">
      {goals.map((goal, index) => (
        <div className="goal-row" key={index}>
          <input className="field" placeholder="Purpose" value={goal.purpose} onChange={(e) => updateGoal(index, { purpose: e.target.value })} />
          <select className="field" value={goal.is_withdrawal ? "withdraw" : "contribute"}
            onChange={(e) => updateGoal(index, { is_withdrawal: e.target.value === "withdraw" })}>
            <option value="contribute">Contribute</option>
            <option value="withdraw">Withdraw</option>
          </select>
          <input className="field" type="number" placeholder="Amount" value={goal.amount} onChange={(e) => updateGoal(index, { amount: Number(e.target.value) })} />
          <input className="field" type="number" placeholder="Starts (year)" value={goal.starts_year} onChange={(e) => updateGoal(index, { starts_year: Number(e.target.value) })} />
          <input className="field" type="number" placeholder="Ends (year)" value={goal.ends_year} onChange={(e) => updateGoal(index, { ends_year: Number(e.target.value) })} />
          <button className="btn btn-ghost" type="button" onClick={() => removeGoal(index)}>Remove</button>
        </div>
      ))}
      <button type="button" className="link-btn" onClick={addGoal}>+ Add goal</button>
    </div>
  );
}

function RetirementAllocationTable({
  funds,
  retirementHoldings,
  onChange
}: {
  funds: FundSummary[];
  retirementHoldings: Holding[];
  onChange: (holdings: Holding[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const selectedIds = new Set(retirementHoldings.map((h) => h.proj_id));
  const filteredFunds = funds.filter((fund) => {
    if (selectedIds.has(fund.proj_id) && retirementHoldings.some((h) => h.proj_id === fund.proj_id && h.proj_id)) return true;
    const haystack = `${fund.proj_id} ${fund.proj_name_thai ?? ""}`.toLowerCase();
    return haystack.includes(query.toLowerCase());
  });

  function addFund(fund: FundSummary) {
    const existing = retirementHoldings.find((h) => h.proj_id === fund.proj_id);
    if (!existing) {
      onChange([...retirementHoldings, { proj_id: fund.proj_id, weight: 0 }]);
    }
    setQuery("");
    setOpen(false);
  }

  function removeFund(projId: string) {
    if (retirementHoldings.length <= 1) return;
    onChange(retirementHoldings.filter((h) => h.proj_id !== projId));
  }

  function updateWeight(projId: string, weight: number) {
    onChange(retirementHoldings.map((h) => (h.proj_id === projId ? { ...h, weight } : h)));
  }

  const total = retirementHoldings.reduce((sum, h) => sum + (h.weight || 0), 0);
  const complete = Math.abs(total - 100) < 0.01 && retirementHoldings.length > 0;

  function normalizeWeights() {
    if (total <= 0) {
      const share = 100 / retirementHoldings.length;
      onChange(retirementHoldings.map((h) => ({ ...h, weight: share })));
      return;
    }
    onChange(retirementHoldings.map((h) => ({ ...h, weight: (h.weight / total) * 100 })));
  }

  function clearWeights() {
    onChange(retirementHoldings.map((h) => ({ ...h, weight: 0 })));
  }

  return (
    <div className="form-grid" style={{ gridColumn: "1 / -1" }}>
      <div className="holdings-table" style={{ gridColumn: "1 / -1" }}>
        <div className="holdings-head">
          <div>Fund</div>
          <div>Weight %</div>
          <div></div>
        </div>
        {retirementHoldings.map((holding) => {
          const fund = funds.find((f) => f.proj_id === holding.proj_id);
          return (
            <div className="holdings-row" key={holding.proj_id}>
              <div className="fund-field">
                <input
                  className="field fund-input"
                  value={fund ? (fund.proj_name_thai || fund.proj_id) : ""}
                  disabled
                  placeholder="Fund"
                />
              </div>
              <input
                className="field num"
                type="number"
                min={0}
                max={100}
                step={0.1}
                value={holding.weight}
                onChange={(e) => updateWeight(holding.proj_id, Number(e.target.value))}
              />
              <button className="icon-btn" onClick={() => removeFund(holding.proj_id)} type="button">✕</button>
            </div>
          );
        })}
        <div style={{ position: "relative", gridColumn: "1 / -1" }}>
          <input
            className="field fund-input"
            placeholder="Add fund..."
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            autoComplete="off"
          />
          {open && filteredFunds.length > 0 && (
            <div className="fund-suggest open">
              {filteredFunds.map((fund) => (
                <button
                  key={fund.proj_id}
                  className="fund-suggest-item"
                  onClick={() => addFund(fund)}
                  type="button"
                  style={{ display: "block", width: "100%", textAlign: "left", padding: "9px 12px", border: 0, background: "none", cursor: "pointer", fontSize: "13px" }}
                >
                  {fund.proj_name_thai || fund.proj_id} <span style={{ display: "block", color: "var(--text-tertiary)", fontSize: "11.5px", marginTop: "2px" }}>{fund.proj_id}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="holdings-foot" style={{ gridColumn: "1 / -1" }}>
        <div className="holdings-foot-left">
          <div className="weight-actions">
            <button className="link-btn" onClick={normalizeWeights} type="button">Normalize to 100%</button>
            <span aria-hidden="true">&middot;</span>
            <button className="link-btn" onClick={clearWeights} type="button">Clear</button>
          </div>
        </div>
        <div className="weight-total">
          Total <span>{(Math.round(total * 10) / 10).toFixed(1)}%</span>
          <span className={complete ? "pill ok" : "pill warn"}>{complete ? "ready" : "incomplete"}</span>
        </div>
      </div>
    </div>
  );
}
