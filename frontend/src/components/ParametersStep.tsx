import { useState } from "react";
import type { SimulateRequest, NamedGoal } from "../types/simulate";

interface Props {
  active: boolean;
  value: SimulateRequest;
  onChange: (value: SimulateRequest) => void;
  onContinue: () => void;
}

export function ParametersStep({ active, value, onChange, onContinue }: Props) {
  const [multiGoal, setMultiGoal] = useState(value.multi_goal_enabled);

  function patch(fields: Partial<SimulateRequest>) {
    onChange({ ...value, ...fields });
  }

  return (
    <div className={active ? "page active" : "page"}>
      <div className="page-head">
        <h1>Set your simulation parameters</h1>
        <p>Choose a simulation model and configure the assumptions behind it.</p>
      </div>

      <div className="card">
        <h2>Core</h2>
        <label>
          Initial Amount
          <input type="number" value={value.initial_amount}
            onChange={(e) => patch({ initial_amount: Number(e.target.value) })} />
        </label>
        <label>
          Simulation Period in Years
          <input type="number" min={5} max={75} step={5} value={value.simulation_period_years}
            onChange={(e) => patch({ simulation_period_years: Number(e.target.value) })} />
        </label>
        <label>
          Tax Treatment
          <select value={value.tax_treatment} onChange={(e) => patch({ tax_treatment: e.target.value as SimulateRequest["tax_treatment"] })}>
            <option value="pre_tax">Pre-tax Returns</option>
            <option value="after_tax">After-tax Returns</option>
          </select>
        </label>
        <label>
          Simulation Model
          <select value={value.simulation_model} onChange={(e) => patch({ simulation_model: e.target.value as SimulateRequest["simulation_model"] })}>
            <option value="historical">Historical Returns</option>
            <option value="forecasted">Forecasted Returns</option>
            <option value="statistical">Statistical Returns</option>
            <option value="parameterized">Parameterized Returns</option>
          </select>
        </label>
      </div>

      {value.simulation_model === "historical" && (
        <div className="card">
          <h2>Historical Model Settings</h2>
          <label>
            Use Full History
            <select value={value.use_full_history ? "yes" : "no"}
              onChange={(e) => patch({ use_full_history: e.target.value === "yes" })}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </label>
          <label>
            Bootstrap Model
            <select value={value.bootstrap_model ?? "single_year"}
              onChange={(e) => patch({ bootstrap_model: e.target.value as SimulateRequest["bootstrap_model"] })}>
              <option value="single_month">Single Month</option>
              <option value="single_year">Single Year</option>
              <option value="block_of_years">Block of Years</option>
            </select>
          </label>
          <label>
            Sequence of Returns Risk
            <select value={value.sequence_of_returns_risk ?? 0}
              onChange={(e) => patch({ sequence_of_returns_risk: Number(e.target.value) })}>
              <option value={0}>No Adjustments</option>
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>Worst {n} Year{n > 1 ? "s" : ""} First</option>
              ))}
            </select>
          </label>
        </div>
      )}

      {(value.simulation_model === "forecasted" || value.simulation_model === "statistical") && (
        <div className="card">
          <h2>Time Series Model</h2>
          <select value={value.time_series_model ?? "normal"}
            onChange={(e) => patch({ time_series_model: e.target.value as SimulateRequest["time_series_model"] })}>
            <option value="normal">Normal</option>
            <option value="garch">GARCH</option>
          </select>
        </div>
      )}

      {value.simulation_model === "parameterized" && (
        <div className="card">
          <h2>Parameterized Distribution</h2>
          <label>
            Distribution
            <select value={value.distribution ?? "normal"}
              onChange={(e) => patch({ distribution: e.target.value as SimulateRequest["distribution"] })}>
              <option value="normal">Normal</option>
              <option value="fat_tailed">Fat-tailed (Student-t)</option>
            </select>
          </label>
          {value.distribution === "fat_tailed" && (
            <label>
              Degrees of Freedom
              <input type="number" value={value.degrees_of_freedom ?? 5}
                onChange={(e) => patch({ degrees_of_freedom: Number(e.target.value) })} />
            </label>
          )}
          <label>
            Expected Return
            <input type="number" step="0.01" value={value.expected_return ?? 0}
              onChange={(e) => patch({ expected_return: Number(e.target.value) })} />
          </label>
          <label>
            Expected Volatility
            <input type="number" step="0.01" value={value.expected_volatility ?? 0}
              onChange={(e) => patch({ expected_volatility: Number(e.target.value) })} />
          </label>
        </div>
      )}

      <div className="card">
        <h2>Cashflow &amp; Goals</h2>
        <label>
          <input type="checkbox" checked={multiGoal}
            onChange={(e) => { setMultiGoal(e.target.checked); patch({ multi_goal_enabled: e.target.checked }); }} />
          Advanced: multiple goals
        </label>
        {!multiGoal ? (
          <>
            <label>
              Cashflow
              <select value={value.cashflow_mode}
                onChange={(e) => patch({ cashflow_mode: e.target.value as SimulateRequest["cashflow_mode"] })}>
                <option value="none">No contributions or withdrawals</option>
                <option value="contribute">Contribute fixed amount periodically</option>
                <option value="withdraw_fixed">Withdraw fixed amount periodically</option>
                <option value="withdraw_percent">Withdraw fixed percentage periodically</option>
              </select>
            </label>
            {value.cashflow_mode !== "none" && (
              <>
                <label>
                  Amount
                  <input type="number" value={value.cashflow_amount ?? 0}
                    onChange={(e) => patch({ cashflow_amount: Number(e.target.value) })} />
                </label>
                <label>
                  Inflation Adjusted
                  <select value={value.cashflow_inflation_adjusted ? "yes" : "no"}
                    onChange={(e) => patch({ cashflow_inflation_adjusted: e.target.value === "yes" })}>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </label>
                <label>
                  Frequency
                  <select value={value.cashflow_frequency ?? "annually"}
                    onChange={(e) => patch({ cashflow_frequency: e.target.value as SimulateRequest["cashflow_frequency"] })}>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="annually">Annually</option>
                  </select>
                </label>
              </>
            )}
          </>
        ) : (
          <GoalsTable goals={value.goals ?? []} onChange={(goals) => patch({ goals })} />
        )}
      </div>

      <div className="card">
        <h2>Inflation &amp; Rebalancing</h2>
        <label>
          Inflation Model
          <select value={value.inflation_model} onChange={(e) => patch({ inflation_model: e.target.value as SimulateRequest["inflation_model"] })}>
            <option value="historical">Historical Inflation</option>
            <option value="parameterized">Parameterized Inflation</option>
          </select>
        </label>
        {value.inflation_model === "parameterized" && (
          <>
            <label>
              Mean
              <input type="number" step="0.001" value={value.inflation_mean ?? 0.03}
                onChange={(e) => patch({ inflation_mean: Number(e.target.value) })} />
            </label>
            <label>
              Volatility
              <input type="number" step="0.001" value={value.inflation_volatility ?? 0.01}
                onChange={(e) => patch({ inflation_volatility: Number(e.target.value) })} />
            </label>
          </>
        )}
        <label>
          Rebalancing
          <select value={value.rebalancing} onChange={(e) => patch({ rebalancing: e.target.value as SimulateRequest["rebalancing"] })}>
            <option value="none">No rebalancing</option>
            <option value="annual">Rebalance annually</option>
            <option value="semiannual">Rebalance semi-annually</option>
            <option value="quarterly">Rebalance quarterly</option>
            <option value="monthly">Rebalance monthly</option>
          </select>
        </label>
      </div>

      <button className="primary" onClick={onContinue} type="button">Continue to Results</button>
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
          <input placeholder="Purpose" value={goal.purpose} onChange={(e) => updateGoal(index, { purpose: e.target.value })} />
          <select value={goal.is_withdrawal ? "withdraw" : "contribute"}
            onChange={(e) => updateGoal(index, { is_withdrawal: e.target.value === "withdraw" })}>
            <option value="contribute">Contribute</option>
            <option value="withdraw">Withdraw</option>
          </select>
          <input type="number" placeholder="Amount" value={goal.amount} onChange={(e) => updateGoal(index, { amount: Number(e.target.value) })} />
          <input type="number" placeholder="Starts (year)" value={goal.starts_year} onChange={(e) => updateGoal(index, { starts_year: Number(e.target.value) })} />
          <input type="number" placeholder="Ends (year)" value={goal.ends_year} onChange={(e) => updateGoal(index, { ends_year: Number(e.target.value) })} />
          <button type="button" onClick={() => removeGoal(index)}>Remove</button>
        </div>
      ))}
      <button type="button" className="link-btn" onClick={addGoal}>+ Add goal</button>
    </div>
  );
}
