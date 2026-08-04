import { useState } from "react";
import { Download, ShieldCheck } from "lucide-react";
import type { SimulateResponse } from "../types/simulate";
import { AxisCurve, Histogram, CorrelationMatrix, DataTable } from "./charts";
import type { ChartSeries, HistogramBin, TableSection } from "./charts";

type ResultsTab = "overview" | "growth" | "distribution" | "metrics" | "risk" | "goals" | "report";

interface Props {
  result: SimulateResponse;
}

const SIMULATION_MODEL_LABELS: Record<string, string> = {
  historical: "Historical",
  forecasted: "Forecasted",
  statistical: "Statistical",
  parameterized: "Parameterized",
};

function downloadResultJson(result: SimulateResponse) {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "simulation_result.json";
  a.click();
  URL.revokeObjectURL(url);
}

export function ResultsView({ result }: Props) {
  const tabs: { id: ResultsTab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "growth", label: "Growth" },
    { id: "distribution", label: "Distribution" },
    { id: "metrics", label: "Metrics" },
    { id: "risk", label: "Risk & Correlation" },
    ...(result.goals ? [{ id: "goals" as ResultsTab, label: "Goals & Cashflows" }] : []),
    { id: "report", label: "Report" },
  ];
  const [activeTab, setActiveTab] = useState<ResultsTab>("overview");

  const runConfig = result.run_config as unknown as {
    simulation_model?: string;
    simulation_period_years?: number;
  };
  const modelLabel = SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? "Monte Carlo";
  const years = runConfig.simulation_period_years;

  return (
    <section className="resultShell" id="report-output">
      <div className="resultHeader">
        <div>
          <span className="sourceLine">
            <ShieldCheck size={16} /> Simulation result
          </span>
          <h2>
            {modelLabel} model{years ? ` · ${years}-year horizon` : ""}
          </h2>
        </div>
        <button className="secondaryButton" onClick={() => downloadResultJson(result)} type="button">
          <Download size={16} /> Result JSON
        </button>
      </div>

      <nav className="resultTabs" aria-label="Simulation output tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={tab.id === activeTab ? "resultTab active" : "resultTab"}
            onClick={() => setActiveTab(tab.id)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === "overview" && <OverviewTab result={result} />}
      {activeTab === "growth" && <GrowthTab result={result} />}
      {activeTab === "distribution" && <DistributionTab result={result} />}
      {activeTab === "metrics" && <MetricsTab result={result} />}
      {activeTab === "risk" && <RiskTab result={result} />}
      {activeTab === "goals" && result.goals && <GoalsTab goals={result.goals} />}
      {activeTab === "report" && <ReportTab result={result} />}
    </section>
  );
}

// --- Overview ---------------------------------------------------------

interface OverviewData {
  survived_count: number;
  n_paths: number;
  survival_rate: number;
  median_ending_balance: number;
  median_cagr: number;
  holdings: { proj_id: string; weight: number }[];
}

function OverviewTab({ result }: { result: SimulateResponse }) {
  const overview = result.overview as unknown as OverviewData;
  return (
    <div className="card">
      <h2>Overview</h2>
      <p>
        {overview.survived_count} out of {overview.n_paths} simulated portfolios (
        {(overview.survival_rate * 100).toFixed(2)}%) survived all withdrawals through the full simulation
        horizon.
      </p>
      <div className="stat-row">
        <div className="metricCard">
          <span>Median Ending Balance</span>
          <strong>
            {overview.median_ending_balance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </strong>
        </div>
        <div className="metricCard">
          <span>Median CAGR</span>
          <strong>{(overview.median_cagr * 100).toFixed(2)}%</strong>
        </div>
        <div className="metricCard">
          <span>Survival Rate</span>
          <strong>{(overview.survival_rate * 100).toFixed(2)}%</strong>
        </div>
        <div className="metricCard">
          <span>Simulated Paths</span>
          <strong>{overview.n_paths.toLocaleString()}</strong>
        </div>
      </div>
      <h3>Portfolio Holdings</h3>
      <table>
        <thead>
          <tr>
            <th>Fund</th>
            <th>Weight</th>
          </tr>
        </thead>
        <tbody>
          {overview.holdings.map((h) => (
            <tr key={h.proj_id}>
              <td>{h.proj_id}</td>
              <td>{h.weight.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Growth -------------------------------------------------------------

interface GrowthData {
  fan_chart: Record<string, number[]>;
  survival_over_time: number[];
}

function GrowthTab({ result }: { result: SimulateResponse }) {
  const growth = result.growth as unknown as GrowthData;
  const percentileColors: Record<string, string> = {
    "10": "var(--danger)",
    "25": "var(--warn)",
    "50": "var(--accent)",
    "75": "var(--warn)",
    "90": "var(--danger)",
  };
  const fanSeries: ChartSeries[] = Object.entries(growth.fan_chart).map(([pct, values]) => ({
    label: `${pct}th percentile`,
    color: percentileColors[pct] ?? "var(--accent)",
    points: values.map((y, x) => ({ x, y })),
  }));
  const survivalSeries: ChartSeries[] = [
    {
      label: "Survival",
      color: "var(--success)",
      points: growth.survival_over_time.map((y, x) => ({ x, y: y * 100 })),
    },
  ];
  return (
    <div className="card">
      <h2>Growth</h2>
      <AxisCurve
        title="Simulated Portfolio Balances"
        series={fanSeries}
        valueFormat={(v) => v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        xFormat={(v) => `Yr ${v}`}
      />
      <AxisCurve
        title="Portfolio Survival Over Time"
        series={survivalSeries}
        valueFormat={(v) => `${v.toFixed(1)}%`}
        xFormat={(v) => `Yr ${v}`}
      />
    </div>
  );
}

// --- Distribution ---------------------------------------------------------

interface DistributionData {
  ending_balance_histogram: number[];
}

function DistributionTab({ result }: { result: SimulateResponse }) {
  const distribution = result.distribution as unknown as DistributionData;
  const bins = buildHistogramBins(distribution.ending_balance_histogram, 30);
  return (
    <div className="card">
      <h2>Distribution</h2>
      <p>Distribution of the simulated portfolio's ending balance across all paths.</p>
      <Histogram rows={bins} />
    </div>
  );
}

function buildHistogramBins(values: number[], nBins: number): HistogramBin[] {
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = (max - min) / nBins || 1;
  const bins: HistogramBin[] = Array.from({ length: nBins }, (_, i) => ({
    bin: (min + i * width).toLocaleString(undefined, { maximumFractionDigits: 0 }),
    count: 0,
    from: min + i * width,
    to: min + (i + 1) * width,
  }));
  for (const v of values) {
    const idx = Math.min(nBins - 1, Math.floor((v - min) / width));
    bins[idx].count += 1;
  }
  return bins;
}

// --- Metrics ---------------------------------------------------------

interface MetricsData {
  percentile_table: { ending_balance: Record<string, number>; cagr: Record<string, number> };
  sharpe: Record<string, number>;
  sortino: Record<string, number>;
  safe_withdrawal_rate: Record<string, number>;
  perpetual_withdrawal_rate: Record<string, number>;
}

function MetricsTab({ result }: { result: SimulateResponse }) {
  const metrics = result.metrics as unknown as MetricsData;
  const pcts = ["10", "25", "50", "75", "90"];
  const columns = ["metric", ...pcts.map((p) => `${p}th Percentile`)];
  const section: TableSection = {
    title: "Performance Summary",
    columns,
    rows: [
      ["Ending Balance", ...pcts.map((p) => metrics.percentile_table.ending_balance[p])],
      ["CAGR", ...pcts.map((p) => metrics.percentile_table.cagr[p])],
      ["Sharpe Ratio", ...pcts.map((p) => metrics.sharpe[p])],
      ["Sortino Ratio", ...pcts.map((p) => metrics.sortino[p])],
      ["Safe Withdrawal Rate", ...pcts.map((p) => metrics.safe_withdrawal_rate[p])],
      ["Perpetual Withdrawal Rate", ...pcts.map((p) => metrics.perpetual_withdrawal_rate[p])],
    ],
  };
  return (
    <div className="card">
      <h2>Metrics</h2>
      <DataTable section={section} />
    </div>
  );
}

// --- Risk & Correlation ---------------------------------------------------------

interface RiskData {
  correlation_and_returns: {
    correlation: Record<string, Record<string, number | null>>;
    stats: Record<string, { cagr: number; expected_return: number; volatility: number }>;
  };
  value_at_risk: number;
  expected_shortfall: number;
}

function RiskTab({ result }: { result: SimulateResponse }) {
  const risk = result.risk as unknown as RiskData;
  const ids = Object.keys(risk.correlation_and_returns.correlation);
  const statsSection: TableSection = {
    title: "Per-Holding Statistics",
    columns: ["holding", "cagr", "expected_return", "volatility"],
    rows: ids.map((id) => {
      const s = risk.correlation_and_returns.stats[id];
      return [id, s.cagr, s.expected_return, s.volatility];
    }),
  };
  return (
    <div className="card">
      <h2>Risk &amp; Correlation</h2>
      <div className="stat-row">
        <div className="metricCard">
          <span>Value at Risk (90%)</span>
          <strong>{risk.value_at_risk.toLocaleString(undefined, { maximumFractionDigits: 0 })}</strong>
        </div>
        <div className="metricCard">
          <span>Expected Shortfall (90%)</span>
          <strong>{risk.expected_shortfall.toLocaleString(undefined, { maximumFractionDigits: 0 })}</strong>
        </div>
      </div>
      <h3>Correlation Matrix</h3>
      <CorrelationMatrix ids={ids} correlation={risk.correlation_and_returns.correlation} />
      <h3>Per-Holding Statistics</h3>
      <DataTable section={statsSection} />
    </div>
  );
}

// --- Goals & Cashflows ---------------------------------------------------------

interface GoalsData {
  summary: { purpose: string; success_rate: number }[];
}

function GoalsTab({ goals }: { goals: Record<string, unknown> }) {
  const data = goals as unknown as GoalsData;
  const summary = data.summary ?? [];
  return (
    <div className="card">
      <h2>Goals &amp; Cashflows</h2>
      {summary.length === 0 ? (
        <p>No goals were configured for this simulation.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Purpose</th>
              <th>Success Rate</th>
            </tr>
          </thead>
          <tbody>
            {summary.map((row) => (
              <tr key={row.purpose}>
                <td>{row.purpose}</td>
                <td>{(row.success_rate * 100).toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// --- Report ---------------------------------------------------------

function ReportTab({ result }: { result: SimulateResponse }) {
  function downloadJson() {
    const blob = new Blob([JSON.stringify(result.run_config, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "run_config.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadFullResult() {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "simulation_result.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="card">
      <h2>Report</h2>
      <p>Export this simulation run for records or further analysis.</p>
      <div className="stat-row">
        <button type="button" className="btn btn-ghost" onClick={downloadJson}>
          Export run_config.json
        </button>
        <button type="button" className="btn btn-ghost" onClick={downloadFullResult}>
          Export full result (JSON)
        </button>
      </div>
    </div>
  );
}
