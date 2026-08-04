import { useState } from "react";
import type { ReactNode } from "react";
import { Download, ShieldCheck } from "lucide-react";
import type { SimulateResponse } from "../types/simulate";
import { AllocationPie, AxisCurve, Histogram, CorrelationMatrix, DataTable } from "./charts";
import type { AllocationSlice, ChartSeries, HistogramBin, TableSection } from "./charts";

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

const PERCENTILE_KEYS = ["10", "25", "50", "75", "90"];
const HORIZON_YEARS = ["1", "3", "5", "10", "15", "20", "25", "30"];

function pctString(value: number, digits = 2) {
  return `${(value * 100).toFixed(digits)}%`;
}

function money(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
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
        <button
          className="secondaryButton"
          onClick={() => downloadText("simulation_result.json", JSON.stringify(result, null, 2), "application/json")}
          type="button"
        >
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
  const slices: AllocationSlice[] = overview.holdings.map((h) => ({
    key: h.proj_id,
    label: h.proj_id,
    weight: h.weight,
  }));
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
      <h3>Portfolio Allocation</h3>
      <AllocationPie slices={slices} />
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
  max_drawdown_histogram: number[];
}

function DistributionTab({ result }: { result: SimulateResponse }) {
  const distribution = result.distribution as unknown as DistributionData;
  const bins = buildHistogramBins(distribution.ending_balance_histogram, 30, money);
  const drawdownBins = distribution.max_drawdown_histogram
    ? buildHistogramBins(distribution.max_drawdown_histogram, 30, (v) => pctString(v, 1))
    : [];
  return (
    <div className="card">
      <h2>Distribution</h2>
      <p>Distribution of the simulated portfolio's ending balance across all paths.</p>
      <Histogram rows={bins} />
      {drawdownBins.length ? (
        <>
          <h3>Max Drawdown Distribution</h3>
          <p>Distribution of each simulated path's worst peak-to-trough drawdown.</p>
          <Histogram rows={drawdownBins} />
        </>
      ) : null}
    </div>
  );
}

function buildHistogramBins(
  values: number[],
  nBins: number,
  formatBinLabel: (value: number) => string = money
): HistogramBin[] {
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = (max - min) / nBins || 1;
  // Bin labels double as React keys in Histogram (key={row.bin}), so they
  // must stay unique even when the raw values are close together (e.g. a
  // fractional drawdown range like -0.65..-0.02 would collapse to a
  // handful of duplicate "0"/"-1" strings under whole-number formatting) —
  // the bin index is appended to guarantee uniqueness regardless of the
  // caller's formatter/value scale.
  const bins: HistogramBin[] = Array.from({ length: nBins }, (_, i) => ({
    bin: `${formatBinLabel(min + i * width)}#${i}`,
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

interface PercentileTable {
  ending_balance: Record<string, number>;
  cagr: Record<string, number>;
  twrr_nominal: Record<string, number>;
  twrr_real: Record<string, number>;
  max_drawdown: Record<string, number>;
  max_drawdown_excl_cashflows: Record<string, number>;
}

interface MetricsData {
  percentile_table: PercentileTable;
  sharpe: Record<string, number>;
  sortino: Record<string, number>;
  safe_withdrawal_rate: Record<string, number>;
  perpetual_withdrawal_rate: Record<string, number>;
}

function metricsSection(metrics: MetricsData): TableSection {
  const pcts = PERCENTILE_KEYS;
  const columns = ["metric", ...pcts.map((p) => `${p}th Percentile`)];
  const pt = metrics.percentile_table;
  return {
    title: "Performance Summary",
    columns,
    rows: [
      ["Ending Balance", ...pcts.map((p) => money(pt.ending_balance[p]))],
      ["TWRR (nominal)", ...pcts.map((p) => pctString(pt.twrr_nominal[p]))],
      ["TWRR (real)", ...pcts.map((p) => pctString(pt.twrr_real[p]))],
      ["CAGR", ...pcts.map((p) => pctString(pt.cagr[p]))],
      ["Max Drawdown", ...pcts.map((p) => pctString(pt.max_drawdown[p]))],
      ["Max Drawdown (excl. cashflows)", ...pcts.map((p) => pctString(pt.max_drawdown_excl_cashflows[p]))],
      ["Sharpe Ratio", ...pcts.map((p) => metrics.sharpe[p].toFixed(2))],
      ["Sortino Ratio", ...pcts.map((p) => metrics.sortino[p].toFixed(2))],
      ["Safe Withdrawal Rate", ...pcts.map((p) => pctString(metrics.safe_withdrawal_rate[p]))],
      ["Perpetual Withdrawal Rate", ...pcts.map((p) => pctString(metrics.perpetual_withdrawal_rate[p]))],
    ],
  };
}

function MetricsTab({ result }: { result: SimulateResponse }) {
  const metrics = result.metrics as unknown as MetricsData;
  return (
    <div className="card">
      <h2>Metrics</h2>
      <DataTable section={metricsSection(metrics)} />
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
  expected_return_by_horizon: Record<string, Record<string, number>>;
  annual_return_probability: Record<string, Record<string, number>>;
  loss_probability: {
    excluding_cashflows: { within_period: Record<string, number>; end_of_period: Record<string, number> };
    including_cashflows: { within_period: Record<string, number>; end_of_period: Record<string, number> };
  };
}

function expectedReturnByHorizonSection(data: Record<string, Record<string, number>>): TableSection {
  return {
    title: "Expected Annual Return by Horizon",
    columns: ["percentile", ...HORIZON_YEARS.map((h) => `${h}yr`)],
    rows: PERCENTILE_KEYS.map((p) => [`${p}th`, ...HORIZON_YEARS.map((h) => pctString(data[h]?.[p] ?? 0))]),
  };
}

function annualReturnProbabilitySection(data: Record<string, Record<string, number>>): TableSection {
  const thresholdLabels = Object.keys(data);
  return {
    title: "Annual Return Probability",
    columns: ["threshold", ...HORIZON_YEARS.map((h) => `${h}yr`)],
    rows: thresholdLabels.map((label) => [
      `>= ${label}`,
      ...HORIZON_YEARS.map((h) => pctString(data[label]?.[h] ?? 0)),
    ]),
  };
}

function lossProbabilitySection(data: RiskData["loss_probability"]): TableSection {
  const thresholdLabels = Object.keys(data.excluding_cashflows.within_period);
  return {
    title: "Loss Probability",
    columns: [
      "threshold",
      "Excl. Cashflows — Within",
      "Excl. Cashflows — End",
      "Incl. Cashflows — Within",
      "Incl. Cashflows — End",
    ],
    rows: thresholdLabels.map((label) => [
      `>= ${label}`,
      pctString(data.excluding_cashflows.within_period[label] ?? 0),
      pctString(data.excluding_cashflows.end_of_period[label] ?? 0),
      pctString(data.including_cashflows.within_period[label] ?? 0),
      pctString(data.including_cashflows.end_of_period[label] ?? 0),
    ]),
  };
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
      {risk.expected_return_by_horizon ? (
        <>
          <h3>Expected Annual Return by Horizon</h3>
          <DataTable section={expectedReturnByHorizonSection(risk.expected_return_by_horizon)} />
        </>
      ) : null}
      {risk.annual_return_probability ? (
        <>
          <h3>Annual Return Probability</h3>
          <DataTable section={annualReturnProbabilitySection(risk.annual_return_probability)} />
        </>
      ) : null}
      {risk.loss_probability ? (
        <>
          <h3>Loss Probability</h3>
          <DataTable section={lossProbabilitySection(risk.loss_probability)} />
        </>
      ) : null}
    </div>
  );
}

// --- Goals & Cashflows ---------------------------------------------------------

interface GlidePath {
  years: number[];
  allocations: Record<string, number[]>;
}

interface GoalsData {
  summary: { purpose: string; success_rate: number }[];
  cashflows_nominal?: number[];
  cashflows_present_dollar?: number[];
  glide_path?: GlidePath;
}

const GLIDE_PALETTE = ["var(--accent)", "var(--success)", "var(--warn)", "var(--danger)", "#7c4ded"];

function GoalsTab({ goals }: { goals: Record<string, unknown> }) {
  const data = goals as unknown as GoalsData;
  const summary = data.summary ?? [];

  const hasCashflows = !!(data.cashflows_nominal && data.cashflows_nominal.length);
  const cashflowSeries: ChartSeries[] = hasCashflows
    ? [
        {
          label: "Nominal",
          color: "var(--accent)",
          points: (data.cashflows_nominal ?? []).map((y, x) => ({ x, y })),
        },
        {
          label: "Present dollar",
          color: "var(--success)",
          dashed: true,
          points: (data.cashflows_present_dollar ?? []).map((y, x) => ({ x, y })),
        },
      ]
    : [];

  const glidePathSeries: ChartSeries[] = data.glide_path
    ? Object.entries(data.glide_path.allocations).map(([projId, values], index) => ({
        label: projId,
        color: GLIDE_PALETTE[index % GLIDE_PALETTE.length],
        points: values.map((y, i) => ({ x: data.glide_path!.years[i] ?? i, y })),
      }))
    : [];

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
      {hasCashflows ? (
        <>
          <h3>Simulated Cashflows</h3>
          <AxisCurve
            title="Annual Cashflow (nominal vs. present dollar)"
            series={cashflowSeries}
            valueFormat={(v) => v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            xFormat={(v) => `Yr ${v}`}
          />
        </>
      ) : null}
      {glidePathSeries.length ? (
        <>
          <h3>Glide Path</h3>
          <p>Target allocation transition from the working-years portfolio to the retirement portfolio.</p>
          <AxisCurve
            title="Allocation by Holding Over Time"
            series={glidePathSeries}
            valueFormat={(v) => `${v.toFixed(1)}%`}
            xFormat={(v) => `Yr ${v}`}
          />
        </>
      ) : null}
    </div>
  );
}

// --- Report ---------------------------------------------------------

interface RunConfigData {
  simulation_model?: string;
  simulation_period_years?: number;
  initial_amount?: number;
  tax_treatment?: string;
  holdings?: { proj_id: string; weight: number }[];
}

function simulationMethodology(model: string | undefined) {
  switch (model) {
    case "historical":
      return "This run uses a historical bootstrap model: paths are built by resampling blocks of real historical fund returns, preserving the empirical shape of market behavior (fat tails, autocorrelation) without assuming a parametric distribution.";
    case "forecasted":
      return "This run uses a forecasted-returns model: expected return and volatility inputs are derived from forward-looking capital market assumptions rather than raw historical history, then simulated forward.";
    case "statistical":
      return "This run uses a statistical model: paths are generated from a fitted return-generating process (e.g. GARCH/normal) calibrated to the selected holdings' historical statistics.";
    case "parameterized":
      return "This run uses a parameterized model: the user directly specified expected return and volatility assumptions, which drive every simulated path.";
    default:
      return "This run uses a Monte Carlo simulation model to generate a distribution of possible future portfolio paths.";
  }
}

function reportNarrative(runConfig: RunConfigData) {
  const model = SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? "Monte Carlo";
  return `This report simulates a portfolio starting at ${money(runConfig.initial_amount ?? 0)} over a ${runConfig.simulation_period_years ?? "?"}-year horizon using the ${model} simulation model.`;
}

function portfolioSpecRows(runConfig: RunConfigData): TableSection {
  return {
    title: "",
    columns: ["field", "value"],
    rows: [
      ["Initial Amount", money(runConfig.initial_amount ?? 0)],
      ["Simulation Period (years)", String(runConfig.simulation_period_years ?? "")],
      ["Tax Treatment", humanizeLabel(runConfig.tax_treatment ?? "")],
      ["Simulation Model", SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? runConfig.simulation_model ?? ""],
      ...(runConfig.holdings ?? []).map((h) => [`Holding: ${h.proj_id}`, `${h.weight.toFixed(1)}%`]),
    ],
  };
}

function humanizeLabel(value: string) {
  return value.replace(/_/g, " ");
}

function riskSummaryRows(metrics: MetricsData, risk: RiskData): TableSection {
  const pt = metrics.percentile_table;
  return {
    title: "",
    columns: ["metric", "value (median)"],
    rows: [
      ["Sharpe Ratio", metrics.sharpe["50"].toFixed(2)],
      ["Sortino Ratio", metrics.sortino["50"].toFixed(2)],
      ["Max Drawdown", pctString(pt.max_drawdown["50"])],
      ["Value at Risk (90%)", money(risk.value_at_risk)],
      ["Expected Shortfall (90%)", money(risk.expected_shortfall)],
    ],
  };
}

const FORMULA_ROWS: TableSection = {
  title: "",
  columns: ["formula", "definition"],
  rows: [
    ["CAGR", "(Ending Balance / Initial Amount) ^ (1 / Years) - 1"],
    ["Sharpe Ratio", "(Portfolio Return - Risk-free Rate) / Portfolio Volatility"],
    ["Sortino Ratio", "(Portfolio Return - Risk-free Rate) / Downside Deviation"],
    ["Value at Risk (VaR)", "Loss at the chosen confidence percentile of the simulated ending-balance distribution"],
    ["Expected Shortfall (ES)", "Average loss in the tail beyond the VaR threshold"],
    ["Safe Withdrawal Rate", "Largest constant withdrawal rate that keeps the chosen percentile of paths solvent through the horizon"],
  ],
};

function markdownTable(section: TableSection) {
  if (!section.rows.length) return "_No rows._";
  const header = `| ${section.columns.map(humanizeLabel).join(" | ")} |`;
  const divider = `| ${section.columns.map(() => "---").join(" | ")} |`;
  const body = section.rows.map((row) => `| ${row.join(" | ")} |`).join("\n");
  return [header, divider, body].join("\n");
}

function reportMarkdown(result: SimulateResponse) {
  const runConfig = result.run_config as unknown as RunConfigData;
  const metrics = result.metrics as unknown as MetricsData;
  const risk = result.risk as unknown as RiskData;
  const overview = result.overview as unknown as OverviewData;
  const ids = Object.keys(risk.correlation_and_returns.correlation);

  const sections: { title: string; body: string }[] = [
    { title: "1. Research question", body: reportNarrative(runConfig) },
    { title: "2. Data and methodology", body: `${simulationMethodology(runConfig.simulation_model)} This is a forward-looking Monte Carlo simulation, not a historical backtest — it generates many possible future paths rather than replaying one realized history.` },
    { title: "3. Portfolio specification", body: markdownTable(portfolioSpecRows(runConfig)) },
    { title: "4. Performance results", body: markdownTable(metricsSection(metrics)) },
    { title: "5. Risk analysis", body: markdownTable(riskSummaryRows(metrics, risk)) },
    {
      title: "6. Distribution analysis",
      body: `${overview.survived_count} of ${overview.n_paths} simulated paths (${pctString(overview.survival_rate)}) survived through the full horizon. The ending balance spread runs from ${money(metrics.percentile_table.ending_balance["10"])} at the 10th percentile to ${money(metrics.percentile_table.ending_balance["90"])} at the 90th percentile.`,
    },
    { title: "7. Diversification and correlation", body: `Correlation was computed across ${ids.length} holding(s): ${ids.join(", ")}. See the Risk & Correlation tab for the full pairwise matrix.` },
    { title: "Formula reference", body: markdownTable(FORMULA_ROWS) },
    {
      title: "Limitations",
      body: "Monte Carlo simulation only — not a forecast or investment advice. Based on historical parameter estimates (or user-specified parameters for the Parameterized model); past correlations and volatility may not hold in the future. Does not account for taxes or fees beyond what was explicitly configured.",
    },
  ];

  const header = `# Research Report — ${SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? "Monte Carlo"} model, ${runConfig.simulation_period_years ?? "?"}-year horizon`;
  return [header, ...sections.map((s) => `## ${s.title}\n\n${s.body}`)].join("\n\n");
}

function ReportSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <strong>{title}</strong>
      {children}
    </section>
  );
}

function ReportTab({ result }: { result: SimulateResponse }) {
  const runConfig = result.run_config as unknown as RunConfigData;
  const metrics = result.metrics as unknown as MetricsData;
  const risk = result.risk as unknown as RiskData;
  const overview = result.overview as unknown as OverviewData;
  const modelLabel = SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? "Monte Carlo";

  return (
    <div className="tabStack">
      <section className="chartPanel">
        <h3>Export</h3>
        <div className="exportActions">
          <button
            className="secondaryButton"
            onClick={() => downloadText("report.md", reportMarkdown(result), "text/markdown")}
            type="button"
          >
            report.md
          </button>
          <button
            className="secondaryButton"
            onClick={() => downloadText("run_config.json", JSON.stringify(result.run_config, null, 2), "application/json")}
            type="button"
          >
            run_config.json
          </button>
          <button
            className="secondaryButton"
            onClick={() => downloadText("metrics.json", JSON.stringify(result.metrics, null, 2), "application/json")}
            type="button"
          >
            metrics.json
          </button>
          <button className="secondaryButton" onClick={() => window.print()} type="button">
            Print / Save PDF
          </button>
        </div>
      </section>

      <section className="reportPanel">
        <h3>
          Research Report &mdash; {modelLabel} model, {runConfig.simulation_period_years ?? "?"}-year horizon
        </h3>
        <p className="footnote">Monte Carlo simulation &middot; {overview.n_paths.toLocaleString()} simulated paths</p>

        <ReportSection title="1. Research question">
          <p>{reportNarrative(runConfig)}</p>
        </ReportSection>

        <ReportSection title="2. Data and methodology">
          <p>
            {simulationMethodology(runConfig.simulation_model)} This is a forward-looking Monte Carlo simulation, not
            a historical backtest — it generates many possible future paths rather than replaying one realized
            history.
          </p>
        </ReportSection>

        <ReportSection title="3. Portfolio specification">
          <DataTable caption="Portfolio specification" compact section={portfolioSpecRows(runConfig)} />
        </ReportSection>

        <ReportSection title="4. Performance results">
          <DataTable caption="Performance results" section={metricsSection(metrics)} />
        </ReportSection>

        <ReportSection title="5. Risk analysis">
          <DataTable caption="Risk analysis" compact section={riskSummaryRows(metrics, risk)} />
        </ReportSection>

        <ReportSection title="6. Distribution analysis">
          <p>
            {overview.survived_count} of {overview.n_paths} simulated paths ({pctString(overview.survival_rate)})
            survived through the full horizon. The ending balance spread runs from{" "}
            {money(metrics.percentile_table.ending_balance["10"])} at the 10th percentile to{" "}
            {money(metrics.percentile_table.ending_balance["90"])} at the 90th percentile.
          </p>
        </ReportSection>

        <ReportSection title="7. Diversification and correlation">
          <p>Pairwise correlation across all holdings, reused from the Risk &amp; Correlation tab:</p>
          <CorrelationMatrix
            ids={Object.keys(risk.correlation_and_returns.correlation)}
            correlation={risk.correlation_and_returns.correlation}
          />
        </ReportSection>

        <ReportSection title="Formula reference">
          <DataTable caption="Formula reference" compact section={FORMULA_ROWS} />
        </ReportSection>

        <ReportSection title="Limitations">
          <p>
            Monte Carlo simulation only &mdash; not a forecast or investment advice. Based on historical parameter
            estimates (or user-specified parameters for the Parameterized model); past correlations and volatility
            may not hold in the future. Does not account for taxes or fees beyond what was explicitly configured.
          </p>
        </ReportSection>
      </section>
    </div>
  );
}
