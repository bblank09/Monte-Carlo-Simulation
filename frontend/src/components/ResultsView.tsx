import { useState } from "react";
import type { ReactNode } from "react";
import { Download, ShieldCheck } from "lucide-react";
import type { SimulateResponse } from "../types/simulate";
import { AllocationPie, AxisCurve, Histogram, CorrelationMatrix, DataTable, Heatmap, PercentileRange, TargetProbabilityChart } from "./charts";
import type { AllocationSlice, ChartSeries, HeatmapRow, HistogramBin, TableSection } from "./charts";

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

interface RunConfigData {
  simulation_model?: string;
  simulation_period_years?: number;
  initial_amount?: number;
  tax_treatment?: string;
  holdings?: { proj_id: string; weight: number }[];
  n_paths?: number;
  seed?: number;
  rebalancing?: string;
  inflation_model?: string;
  inflation_mean?: number;
  inflation_volatility?: number;
  cashflow_mode?: string;
  cashflow_amount?: number;
  cashflow_inflation_adjusted?: boolean;
  cashflow_frequency?: string;
  bootstrap_model?: string;
  block_years?: number;
  time_series_model?: string;
  distribution?: string;
  degrees_of_freedom?: number;
  expected_return?: number;
  expected_volatility?: number;
  sequence_of_returns_risk?: number;
}

function pctString(value: number, digits = 2) {
  return `${(value * 100).toFixed(digits)}%`;
}

function money(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function percentError(successes: number, trials: number) {
  if (!trials) return 0;
  const p = Math.min(1, Math.max(0, successes / trials));
  return 1.96 * Math.sqrt((p * (1 - p)) / trials);
}

function isCashflowRun(runConfig: RunConfigData) {
  return !!runConfig.cashflow_mode && runConfig.cashflow_mode !== "none";
}

function zeroThresholdProbability(values: Record<string, number>) {
  return values[">= 0.00%"] ?? values["0%"] ?? values[">= 0%"] ?? 0;
}

function MetricCard({
  label,
  value,
  sub,
  tone,
  emphasis = false,
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "positive" | "negative";
  emphasis?: boolean;
}) {
  const className = ["metricCard", emphasis ? "metricCard-emphasis" : "", tone ? `metricCard-${tone}` : ""]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={className}>
      <span>{label}</span>
      <strong>{value}</strong>
      {sub ? <small>{sub}</small> : null}
    </div>
  );
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
          onClick={() => downloadText(`${result.run_id || "result"}.json`, JSON.stringify(result, null, 2), "application/json")}
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
  const metrics = result.metrics as unknown as MetricsData;
  const risk = result.risk as unknown as RiskData;
  const runConfig = result.run_config as unknown as RunConfigData;
  const cashflowRun = isCashflowRun(runConfig);
  const slices: AllocationSlice[] = overview.holdings.map((h) => ({
    key: h.proj_id,
    label: h.proj_id,
    weight: h.weight,
  }));
  const lowSurvival = overview.survival_rate < 0.5;
  const p10 = metrics.percentile_table.ending_balance["10"];
  const p90 = metrics.percentile_table.ending_balance["90"];
  const samplingError = percentError(overview.survived_count, overview.n_paths);
  const survivalLabel = cashflowRun ? "Withdrawal survival rate" : "Positive ending balance rate";
  return (
    <div className="tabStack">
      <section className="chartPanel">
        <h3>Decision summary</h3>
        <p className="summaryText">
          {overview.survived_count.toLocaleString()} of {overview.n_paths.toLocaleString()} simulated paths (
          {pctString(overview.survival_rate)}) {cashflowRun ? "funded the configured cashflows" : "ended with a positive balance"} through the full simulation horizon.
        </p>
        <div className="metricGrid">
          <MetricCard label="Median Ending Balance" value={money(overview.median_ending_balance)} emphasis />
          <MetricCard label="Median CAGR" value={pctString(overview.median_cagr)} />
          <MetricCard label={survivalLabel} value={pctString(overview.survival_rate)} tone={lowSurvival ? "negative" : "positive"} />
          <MetricCard label="Simulated Paths" value={overview.n_paths.toLocaleString()} sub={`Approx. sampling error ±${pctString(samplingError)}`} />
        </div>
      </section>
      <div className="panelGrid">
        <DataTable
          section={{
            title: "Run snapshot",
            columns: ["assumption", "value"],
            rows: [
              ["Simulation model", SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? "Monte Carlo"],
              ["Horizon", `${runConfig.simulation_period_years ?? "—"} years`],
              ["Initial amount", money(runConfig.initial_amount ?? 0)],
              ["Inflation", humanizeLabel(runConfig.inflation_model ?? "not specified")],
              ["Cashflow", cashflowRun ? `${humanizeLabel(runConfig.cashflow_mode ?? "")} · ${humanizeLabel(runConfig.cashflow_frequency ?? "")}` : "None"],
              ["Rebalancing", humanizeLabel(runConfig.rebalancing ?? "not specified")],
            ],
          }}
        />
        <DataTable
          section={{
            title: "Result checklist",
            columns: ["question", "result", "evidence"],
            rows: [
              [survivalLabel, pctString(overview.survival_rate), "Overview / Growth"],
              ["Lower-tail ending balance (P10)", money(p10), p10 > 0 ? "Positive lower-tail outcome" : "Lower-tail depletion"],
              ["Median to upper-tail spread (P90 − P10)", money(p90 - p10), "Distribution"],
              ["Terminal loss VaR / ES (90%)", `${money(risk.value_at_risk)} / ${money(risk.expected_shortfall)}`, "Risk & Correlation"],
              ["Estimated Monte Carlo sampling error", `±${pctString(samplingError)}`, `${overview.n_paths.toLocaleString()} paths`],
            ],
          }}
        />
      </div>
      <DataTable
        section={{
          title: "Terminal outcomes",
          columns: ["scenario", "nominal ending balance", "real ending balance", "reading"],
          rows: PERCENTILE_KEYS.map((p) => [
            `P${p}`,
            money(metrics.percentile_table.ending_balance[p]),
            money(metrics.percentile_table.ending_balance_real[p]),
            p === "10" ? "Downside case" : p === "50" ? "Middle simulated outcome" : p === "90" ? "Upper-tail outcome" : "Distribution range",
          ]),
        }}
      />
      <PercentileRange
        title="Terminal balance range"
        markers={[
          { label: "Initial", value: runConfig.initial_amount ?? 0, color: "var(--text-tertiary)" },
          { label: "P10", value: p10, color: "var(--danger)" },
          { label: "P50", value: metrics.percentile_table.ending_balance["50"], color: "var(--accent)" },
          { label: "P90", value: p90, color: "var(--success)" },
        ]}
        valueFormat={money}
      />
      <section className="chartPanel">
        <h3>Portfolio Allocation</h3>
        <AllocationPie slices={slices} />
      </section>
      <section className="tablePanel">
        <h3>Portfolio Holdings</h3>
        <div className="tableScroller">
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
      </section>
    </div>
  );
}

// --- Growth -------------------------------------------------------------

interface GrowthData {
  fan_chart: Record<string, number[]>;
  survival_over_time: number[];
}

function growthMilestoneSection(growth: GrowthData): TableSection {
  const horizon = Math.max(0, (growth.fan_chart["50"]?.length ?? 1) - 1);
  const milestones = Array.from(new Set([1, 5, 10, 20, horizon].filter((year) => year > 0 && year <= horizon)));
  return {
    title: "Projected value milestones",
    columns: ["year", "P10 ending balance", "P50 ending balance", "P90 ending balance", "survival"],
    rows: milestones.map((year) => [
      `Year ${year}`,
      growth.fan_chart["10"]?.[year] == null ? "N/A" : money(growth.fan_chart["10"][year]),
      growth.fan_chart["50"]?.[year] == null ? "N/A" : money(growth.fan_chart["50"][year]),
      growth.fan_chart["90"]?.[year] == null ? "N/A" : money(growth.fan_chart["90"][year]),
      growth.survival_over_time[year] == null ? "N/A" : pctString(growth.survival_over_time[year]),
    ]),
  };
}

function survivalYAxisDomain(values: number[]): [number, number] {
  const finiteValues = values.filter((value) => Number.isFinite(value)).map((value) => value * 100);
  if (!finiteValues.length) return [0, 100];
  const dataMin = Math.max(0, Math.min(...finiteValues));
  const dataMax = Math.min(100, Math.max(...finiteValues));
  const spread = dataMax - dataMin;

  // A flat 100% line is a valid result, not a 99–100% trend. Keep the full
  // probability scale in that boundary case so the chart does not imply
  // precision that the simulation did not produce.
  if (dataMin >= 99.999 && dataMax >= 99.999) return [0, 100];
  if (spread < 0.001) {
    const padding = Math.max(0.5, dataMax * 0.01);
    return [Math.max(0, dataMin - padding), Math.min(100, dataMax + padding)];
  }

  const padding = Math.max(0.25, spread * 0.12);
  return [Math.max(0, dataMin - padding), Math.min(100, dataMax + padding)];
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
  const horizon = Math.max(0, (growth.fan_chart["50"]?.length ?? 1) - 1);
  const terminalValue = (percentile: string) => {
    const values = growth.fan_chart[percentile] ?? [];
    return values[horizon] ?? values[values.length - 1] ?? 0;
  };
  const survivalValues = growth.survival_over_time.filter((value) => Number.isFinite(value));
  const survivalLatest = survivalValues[survivalValues.length - 1] ?? 0;
  const survivalMin = survivalValues.length ? Math.min(...survivalValues) : 0;
  const survivalDomain = survivalYAxisDomain(growth.survival_over_time);
  return (
    <div className="tabStack">
      <div className="growthLayout">
        <AxisCurve
          className="growthFanChart"
          title="Simulated Portfolio Balances"
          series={fanSeries}
          valueFormat={(v) => v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          xFormat={(v) => `Yr ${v}`}
          badgeText={`P50 · ${money(terminalValue("50"))}`}
          stats={[
            { label: `P10 at Yr ${horizon}`, value: money(terminalValue("10")) },
            { label: `P50 at Yr ${horizon}`, value: money(terminalValue("50")) },
            { label: `P90 at Yr ${horizon}`, value: money(terminalValue("90")) },
          ]}
        />
        <div className="growthSupportGrid">
          <AxisCurve
            className="growthSurvivalChart"
            title="Portfolio Survival Over Time"
            series={survivalSeries}
            valueFormat={(v) => `${v.toFixed(1)}%`}
            xFormat={(v) => `Yr ${v}`}
            yDomain={survivalDomain}
            badgeText={`Yr ${horizon} · ${pctString(survivalLatest)}`}
            stats={[
              { label: "Start", value: pctString(survivalValues[0] ?? 0) },
              { label: "Lowest", value: pctString(survivalMin) },
              { label: "Latest", value: pctString(survivalLatest) },
            ]}
          />
          <DataTable section={growthMilestoneSection(growth)} />
        </div>
      </div>
      <p className="footnote">The fan chart shows the distribution of simulated balances; survival is the share of paths still above zero at each year.</p>
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
  const overview = result.overview as unknown as OverviewData;
  const metrics = result.metrics as unknown as MetricsData;
  const risk = result.risk as unknown as RiskData;
  const runConfig = result.run_config as unknown as RunConfigData;
  // Keep ending balances in their native currency unit. The histogram
  // primitive accepts an axis formatter, so dollars are not accidentally
  // rendered as percentages (or transformed into an unexplained total return).
  const bins = buildHistogramBins(distribution.ending_balance_histogram, 10, money);
  const drawdownBins = distribution.max_drawdown_histogram
    ? buildHistogramBins(distribution.max_drawdown_histogram, 10, (v) => pctString(v, 1))
    : [];
  const p10 = metrics.percentile_table.ending_balance["10"];
  const p90 = metrics.percentile_table.ending_balance["90"];
  const terminalLossProbability = zeroThresholdProbability(risk.loss_probability.including_cashflows.end_of_period);
  const defaultTarget = (runConfig.initial_amount ?? 0) > 0 ? runConfig.initial_amount ?? 0 : metrics.percentile_table.ending_balance["50"];
  const [endingTarget, setEndingTarget] = useState(defaultTarget);
  return (
    <div className="tabStack">
      <div className="metricGrid">
        <MetricCard label="Probability of depletion" value={pctString(1 - overview.survival_rate)} tone={overview.survival_rate < 0.5 ? "negative" : undefined} sub="Full-horizon terminal outcome" />
        <MetricCard label="P10 ending balance" value={money(p10)} sub="Downside case" />
        <MetricCard label="P90 − P10 spread" value={money(p90 - p10)} sub="Terminal outcome dispersion" />
        <MetricCard label="Terminal loss probability" value={pctString(terminalLossProbability)} sub="Ending balance below initial amount" />
      </div>
      <div className="panelGrid">
        <section className="chartPanel">
          <h3>Ending balance distribution</h3>
          <p>Simulated ending balances across all paths, shown in the portfolio currency.</p>
          <Histogram rows={bins} showGainLossLegend={false} valueFormat={money} />
        </section>
        {drawdownBins.length ? (
          <section className="chartPanel">
            <h3>Max drawdown distribution</h3>
            <p>Worst peak-to-trough loss for each simulated path.</p>
            <Histogram rows={drawdownBins} showGainLossLegend={false} valueFormat={(value) => pctString(value, 1)} />
          </section>
        ) : null}
      </div>
      {distribution.ending_balance_histogram.length ? (
        <TargetProbabilityChart
          title="Probability of Ending Below Target"
          values={distribution.ending_balance_histogram}
          target={endingTarget}
          onTargetChange={setEndingTarget}
          targetPresets={[
            { label: "Initial", value: runConfig.initial_amount ?? 0 },
            { label: "P10", value: p10 },
            { label: "P50", value: metrics.percentile_table.ending_balance["50"] },
            { label: "P90", value: p90 },
          ]}
          xFormat={money}
        />
      ) : null}
      <DataTable
        section={{
          title: "Terminal outcome markers",
          columns: ["marker", "value", "interpretation"],
          rows: [
            ["Initial amount", money((result.run_config as unknown as RunConfigData).initial_amount ?? 0), "Reference capital"],
            ["P10", money(p10), "10% of paths ended at or below this balance"],
            ["P50", money(metrics.percentile_table.ending_balance["50"]), "Median simulated outcome"],
            ["P90", money(p90), "90% of paths ended at or below this balance"],
            ["Terminal loss VaR (90%)", money(risk.value_at_risk), "Loss relative to initial amount"],
            ["Expected shortfall (90%)", money(risk.expected_shortfall), "Average loss beyond the VaR cutoff"],
          ],
        }}
      />
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
  const bins: HistogramBin[] = Array.from({ length: nBins }, (_, i) => ({
    bin: formatBinLabel(min + i * width),
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
  ending_balance_real: Record<string, number>;
  cagr: Record<string, number>;
  annual_mean_return: Record<string, number>;
  annualized_volatility: Record<string, number>;
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
      ["TWRR (nominal)", ...pcts.map((p) => pctString(pt.twrr_nominal[p]))],
      ["TWRR (real)", ...pcts.map((p) => pctString(pt.twrr_real[p]))],
      ["Ending Balance", ...pcts.map((p) => money(pt.ending_balance[p]))],
      ["Ending Balance (real)", ...pcts.map((p) => money(pt.ending_balance_real[p]))],
      ["Annual Mean Return", ...pcts.map((p) => pctString(pt.annual_mean_return[p]))],
      ["Annualized Volatility", ...pcts.map((p) => pctString(pt.annualized_volatility[p]))],
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

function groupedMetricsSection(
  metrics: MetricsData,
  title: string,
  rows: [string, (percentile: string) => string][]
): TableSection {
  return {
    title,
    columns: ["metric", ...PERCENTILE_KEYS.map((p) => `P${p}`)],
    rows: rows.map(([label, formatter]) => [label, ...PERCENTILE_KEYS.map(formatter)]),
  };
}

function MetricsTab({ result }: { result: SimulateResponse }) {
  const metrics = result.metrics as unknown as MetricsData;
  const pt = metrics.percentile_table;
  return (
    <div className="tabStack">
      <div className="metricGrid">
        <MetricCard label="Median CAGR" value={pctString(pt.cagr["50"])} />
        <MetricCard label="P10 ending balance" value={money(pt.ending_balance["10"])} sub="Downside case" />
        <MetricCard label="Median real balance" value={money(pt.ending_balance_real["50"])} sub="Inflation-adjusted" />
        <MetricCard label="Median max drawdown" value={pctString(pt.max_drawdown["50"])} tone="negative" sub="Typical path-level peak-to-trough loss" />
      </div>
      <div className="panelGrid">
        <DataTable
          section={groupedMetricsSection(metrics, "Performance outcomes", [
            ["TWRR (nominal, excl. cashflows)", (p) => pctString(pt.twrr_nominal[p])],
            ["TWRR (real, excl. cashflows)", (p) => pctString(pt.twrr_real[p])],
            ["CAGR", (p) => pctString(pt.cagr[p])],
            ["Ending Balance", (p) => money(pt.ending_balance[p])],
            ["Ending Balance (real)", (p) => money(pt.ending_balance_real[p])],
          ])}
        />
        <DataTable
          section={groupedMetricsSection(metrics, "Risk-adjusted outcomes", [
            ["Annual Mean Return", (p) => pctString(pt.annual_mean_return[p])],
            ["Annualized Volatility", (p) => pctString(pt.annualized_volatility[p])],
            ["Max Drawdown", (p) => pctString(pt.max_drawdown[p])],
            ["Max Drawdown (excl. cashflows)", (p) => pctString(pt.max_drawdown_excl_cashflows[p])],
            ["Sharpe Ratio", (p) => metrics.sharpe[p].toFixed(2)],
            ["Sortino Ratio", (p) => metrics.sortino[p].toFixed(2)],
          ])}
        />
      </div>
      <DataTable
        section={groupedMetricsSection(metrics, "Withdrawal capacity", [
          ["Safe Withdrawal Rate", (p) => pctString(metrics.safe_withdrawal_rate[p])],
          ["Perpetual Withdrawal Rate", (p) => pctString(metrics.perpetual_withdrawal_rate[p])],
        ])}
      />
      <p className="footnote">Each percentile describes the distribution across simulated paths. Withdrawal rates should be read with the run horizon, cashflow rule and desired success threshold.</p>
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
    title: "Table — Expected Annual Return by Horizon",
    columns: ["percentile", ...HORIZON_YEARS.map((h) => `${h}yr`)],
    rows: PERCENTILE_KEYS.map((p) => [
      `${p}th`,
      ...HORIZON_YEARS.map((h) => data[h]?.[p] == null ? "N/A" : pctString(data[h][p])),
    ]),
  };
}

function annualReturnProbabilitySection(data: Record<string, Record<string, number>>): TableSection {
  const thresholdLabels = Object.keys(data);
  return {
    title: "Table — Annual Return Probability",
    columns: ["threshold", ...HORIZON_YEARS.map((h) => `${h}yr`)],
    rows: thresholdLabels.map((label) => [
      `>= ${label}`,
      ...HORIZON_YEARS.map((h) => data[label]?.[h] == null ? "N/A" : pctString(data[label][h])),
    ]),
  };
}

function lossProbabilitySection(data: RiskData["loss_probability"]): TableSection {
  const thresholdLabels = Object.keys(data.excluding_cashflows.within_period);
  return {
    title: "Table — Loss Probability",
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

function expectedReturnHeatmapRows(data: Record<string, Record<string, number>>): HeatmapRow[] {
  return PERCENTILE_KEYS.map((p) => ({
    label: `P${p}`,
    values: HORIZON_YEARS.map((h) => data[h]?.[p] ?? null),
  }));
}

function annualReturnProbabilityHeatmapRows(data: Record<string, Record<string, number>>): HeatmapRow[] {
  return Object.keys(data).map((threshold) => ({
    label: threshold.startsWith(">=") ? threshold.replace(">=", "≥") : `≥ ${threshold}`,
    values: HORIZON_YEARS.map((h) => data[threshold]?.[h] ?? null),
  }));
}

function lossProbabilityHeatmapRows(data: RiskData["loss_probability"]): HeatmapRow[] {
  const thresholds = Object.keys(data.excluding_cashflows.within_period);
  return thresholds.map((threshold) => ({
    label: threshold.startsWith(">=") ? threshold.replace(">=", "≥") : `≥ ${threshold}`,
    values: [
      data.excluding_cashflows.within_period[threshold] ?? null,
      data.excluding_cashflows.end_of_period[threshold] ?? null,
      data.including_cashflows.within_period[threshold] ?? null,
      data.including_cashflows.end_of_period[threshold] ?? null,
    ],
  }));
}

function riskContributionSection(
  risk: RiskData,
  holdings: { proj_id: string; weight: number }[]
): TableSection {
  const ids = Object.keys(risk.correlation_and_returns.correlation);
  const weights = ids.map((id) => (holdings.find((holding) => holding.proj_id === id)?.weight ?? 0) / 100);
  const volatilities = ids.map((id) => risk.correlation_and_returns.stats[id]?.volatility ?? 0);
  const covariance = ids.map((rowId, rowIndex) => ids.map((columnId, columnIndex) => {
    const correlation = risk.correlation_and_returns.correlation[rowId]?.[columnId] ?? (rowIndex === columnIndex ? 1 : 0);
    return volatilities[rowIndex] * volatilities[columnIndex] * correlation;
  }));
  const sigmaWeight = ids.map((_, rowIndex) => covariance[rowIndex].reduce((sum, value, columnIndex) => sum + value * weights[columnIndex], 0));
  const portfolioVariance = weights.reduce((sum, weight, index) => sum + weight * sigmaWeight[index], 0);
  const portfolioVolatility = Math.sqrt(Math.max(0, portfolioVariance));
  if (!ids.length || portfolioVolatility === 0) {
    return { title: "Risk contribution by holding", columns: ["holding", "risk contribution"], rows: [] };
  }
  return {
    title: "Risk contribution by holding",
    columns: ["holding", "historical volatility", "share of portfolio risk"],
    rows: ids.map((id, index) => {
      const component = (weights[index] * sigmaWeight[index]) / portfolioVolatility;
      return [id, pctString(volatilities[index]), pctString(component / portfolioVolatility)];
    }),
  };
}

function RiskTab({ result }: { result: SimulateResponse }) {
  const risk = result.risk as unknown as RiskData;
  const overview = result.overview as unknown as OverviewData;
  const runConfig = result.run_config as unknown as RunConfigData;
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
    <div className="tabStack">
      <div className="metricGrid">
        <MetricCard label="Terminal loss VaR (90%)" value={money(risk.value_at_risk)} sub="Loss relative to initial amount" />
        <MetricCard label="Terminal expected shortfall (90%)" value={money(risk.expected_shortfall)} sub="Average loss beyond VaR" />
        <MetricCard label="Terminal depletion" value={pctString(1 - overview.survival_rate)} tone={overview.survival_rate < 0.5 ? "negative" : undefined} />
        <MetricCard label="P90 max drawdown" value={pctString((result.metrics as unknown as MetricsData).percentile_table.max_drawdown["90"])} sub="Less severe end of drawdown distribution" />
      </div>
      <div className="panelGrid">
        <section className="tablePanel">
          <h3>Correlation Matrix</h3>
          <p className="summaryText">Pairwise holding correlation; stronger positive clusters provide less diversification benefit.</p>
          <CorrelationMatrix ids={ids} correlation={risk.correlation_and_returns.correlation} />
        </section>
        <DataTable section={statsSection} />
      </div>
      <DataTable section={riskContributionSection(risk, overview.holdings)} />
      <p className="footnote">Per-holding statistics and risk contribution use the selected holdings' observed return history; they are diagnostics for diversification, not additional simulated paths.</p>
      <div className="panelGrid riskHeatmapGrid">
        {risk.expected_return_by_horizon ? (
          <Heatmap
            title="Expected annual return by horizon"
            columns={HORIZON_YEARS.map((h) => `${h}yr`)}
            rows={expectedReturnHeatmapRows(risk.expected_return_by_horizon)}
            valueFormat={pctString}
            diverging
            description="N/A means the selected horizon is longer than this run's simulation period."
          />
        ) : null}
        {risk.annual_return_probability ? (
          <Heatmap
            title="Probability of reaching annual return threshold"
            columns={HORIZON_YEARS.map((h) => `${h}yr`)}
            rows={annualReturnProbabilityHeatmapRows(risk.annual_return_probability)}
            valueFormat={pctString}
            description="Probability that annualized return meets or exceeds the row threshold."
          />
        ) : null}
      </div>
      {risk.loss_probability ? (
        <Heatmap
          title="Loss probability"
          columns={["Excl. cashflows · within", "Excl. cashflows · end", "Incl. cashflows · within", "Incl. cashflows · end"]}
          rows={lossProbabilityHeatmapRows(risk.loss_probability)}
          valueFormat={pctString}
          description="Within-period loss captures whether a path ever crossed the drawdown threshold; end-of-period uses the terminal balance."
        />
      ) : null}
      <div className="tableDetailsGroup">
        {risk.expected_return_by_horizon ? <DataTable section={expectedReturnByHorizonSection(risk.expected_return_by_horizon)} /> : null}
        {risk.annual_return_probability ? <DataTable section={annualReturnProbabilitySection(risk.annual_return_probability)} /> : null}
        {risk.loss_probability ? <DataTable section={lossProbabilitySection(risk.loss_probability)} /> : null}
      </div>
      <p className="footnote">Model: {SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? "Monte Carlo"}. VaR and expected shortfall here describe terminal loss relative to the initial amount, not a one-period worst-case loss.</p>
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
    <div className="tabStack">
      {summary.length === 0 ? (
        <p>No goals were configured for this simulation.</p>
      ) : (
        <section className="tablePanel">
          <h3>Goal Success Rates</h3>
          <div className="tableScroller">
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
          </div>
        </section>
      )}
      {hasCashflows ? (
        <AxisCurve
          title="Annual Cashflow (nominal vs. present dollar)"
          series={cashflowSeries}
          valueFormat={(v) => v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          xFormat={(v) => `Yr ${v}`}
        />
      ) : null}
      {glidePathSeries.length ? (
        <>
          <div className="notePanel">
            <h3>Glide Path</h3>
            <p>Target allocation transition from the working-years portfolio to the retirement portfolio.</p>
          </div>
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
      ["Simulation Paths", String(runConfig.n_paths ?? "")],
      ["Seed", runConfig.seed == null ? "Random" : String(runConfig.seed)],
      ["Tax Treatment", humanizeLabel(runConfig.tax_treatment ?? "")],
      ["Simulation Model", SIMULATION_MODEL_LABELS[runConfig.simulation_model ?? ""] ?? runConfig.simulation_model ?? ""],
      ["Inflation Model", humanizeLabel(runConfig.inflation_model ?? "")],
      ["Cashflow Mode", humanizeLabel(runConfig.cashflow_mode ?? "none")],
      ["Cashflow Frequency", humanizeLabel(runConfig.cashflow_frequency ?? "")],
      ["Rebalancing", humanizeLabel(runConfig.rebalancing ?? "")],
      ...(runConfig.expected_return == null ? [] : [["Expected Return", pctString(runConfig.expected_return)]]),
      ...(runConfig.expected_volatility == null ? [] : [["Expected Volatility", pctString(runConfig.expected_volatility)]]),
      ...(runConfig.distribution == null ? [] : [["Return Distribution", humanizeLabel(runConfig.distribution)]]),
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
      ["Terminal Loss VaR (90%)", money(risk.value_at_risk)],
      ["Terminal Expected Shortfall (90%)", money(risk.expected_shortfall)],
    ],
  };
}

function simulationDiagnosticsRows(overview: OverviewData, runConfig: RunConfigData): TableSection {
  return {
    title: "Simulation diagnostics",
    columns: ["diagnostic", "value"],
    rows: [
      ["Simulated paths", overview.n_paths.toLocaleString()],
      ["Full-horizon positive paths", `${overview.survived_count.toLocaleString()} (${pctString(overview.survival_rate)})`],
      ["Approximate 95% sampling error", `±${pctString(percentError(overview.survived_count, overview.n_paths))}`],
      ["Simulation horizon", `${runConfig.simulation_period_years ?? "—"} years`],
      ["Random seed", runConfig.seed == null ? "Random" : String(runConfig.seed)],
      ["Tail metric definition", "Terminal loss relative to initial amount; ES averages losses beyond the 90th-percentile cutoff"],
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
      body: `${overview.survived_count} of ${overview.n_paths} simulated paths (${pctString(overview.survival_rate)}) remained positive through the full horizon. The ending balance spread runs from ${money(metrics.percentile_table.ending_balance["10"])} at the 10th percentile to ${money(metrics.percentile_table.ending_balance["90"])} at the 90th percentile.`,
    },
    { title: "7. Diversification and correlation", body: `Correlation was computed across ${ids.length} holding(s): ${ids.join(", ")}. See the Risk & Correlation tab for the full pairwise matrix.` },
    { title: "8. Simulation diagnostics", body: markdownTable(simulationDiagnosticsRows(overview, runConfig)) },
    { title: "Formula reference", body: markdownTable(FORMULA_ROWS) },
    {
      title: "Limitations",
      body: "Monte Carlo simulation only — not a forecast or investment advice. Based on historical return estimates (or user-specified assumptions for the Parameterized model); past correlations and volatility may not hold in the future. Does not account for taxes or fees beyond what was explicitly configured.",
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
          <button
            className="secondaryButton"
            onClick={() => downloadText("result.json", JSON.stringify(result, null, 2), "application/json")}
            type="button"
          >
            result.json
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

        <ReportSection title="Simulation diagnostics">
          <DataTable caption="Simulation diagnostics" compact section={simulationDiagnosticsRows(overview, runConfig)} />
        </ReportSection>

        <ReportSection title="3. Portfolio specification">
          <DataTable caption="Portfolio specification" compact section={portfolioSpecRows(runConfig)} />
        </ReportSection>

        <ReportSection title="4. Performance results">
          <DataTable caption="Performance Summary" section={metricsSection(metrics)} />
        </ReportSection>

        <ReportSection title="5. Risk analysis">
          <DataTable caption="Risk analysis" compact section={riskSummaryRows(metrics, risk)} />
        </ReportSection>

        <ReportSection title="6. Distribution analysis">
          <p>
            {overview.survived_count} of {overview.n_paths} simulated paths ({pctString(overview.survival_rate)})
            remained positive through the full horizon. The ending balance spread runs from{" "}
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
            Monte Carlo simulation only &mdash; not a forecast or investment advice. Based on historical return
            estimates (or user-specified assumptions for the Parameterized model); past correlations and volatility
            may not hold in the future. Does not account for taxes or fees beyond what was explicitly configured.
          </p>
        </ReportSection>
      </section>
    </div>
  );
}
