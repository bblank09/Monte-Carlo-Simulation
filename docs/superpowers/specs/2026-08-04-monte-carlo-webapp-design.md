# Monte Carlo Simulation Webapp — Design Spec

Date: 2026-08-04
Status: draft, pending user review
Supersedes: `docs/superpowers/specs/2026-07-29-monte-carlo-webapp-design.md` (deleted — its yfinance/US-ticker scope is obsolete)

## 1. Goal

Build a web app around the existing Monte Carlo simulation engine (currently living as
notebook-support code in `tests/*.py`). The app is the forward-looking sibling of
**Backtest Portfolio Webull:SEC OPENAI** (same author, same course, same data source).
Backtest answers "what did happen"; this app answers "what could happen."

The UX/UI shell (3-step wizard, visual design tokens, chart primitives, layout patterns)
is copied directly from Backtest Portfolio. The internals — simulation engine, API
schema, results content — are entirely different and specific to Monte Carlo simulation.

## 2. Scope

**Data source: SEC Thailand Open Data only.** No yfinance, no US tickers. This narrows
the original v1 draft further — `webull_client.py` (actually a yfinance wrapper) and the
two-calendar merge in `returns_lib.build_price_panel` are dropped, not promoted.

**Feature depth: full parity with Portfolio Visualizer's Monte Carlo + Financial Goals
tools**, built in one pass (not phased). This includes multi-stage/glide-path allocation
and named multi-goal cashflows — the Financial Goals-level feature set — not just the
single-stage basic Monte Carlo tool.

Reference (loaded live via browser, 2026-08-04):
- https://www.portfoliovisualizer.com/monte-carlo-simulation — single-stage tool, full
  field list and results structure captured verbatim (see §4, §5).
- https://www.portfoliovisualizer.com/financial-goals — multi-stage/glide-path/named-goals
  tool, captured verbatim (see §4, §5).

## 3. Simulation models (confirmed, not new work)

`tests/*.py` already implements all 4 models Portfolio Visualizer offers, under matching
names — this was a deliberate design choice when the notebook was built, not a
coincidence:

| PV model name | Existing file | Method |
|---|---|---|
| Historical Returns | `historical_sim.py` | bootstrap resample of real annual returns, with replacement |
| Forecasted Returns | `forecasted_sim.py` | draws from `N(w'μ, w'Σw)` (Normal) or GARCH(1,1) (`arch_model`) |
| Statistical Returns | `statistical_sim.py` | daily GBM (Euler) from portfolio μ/Σ, annual-indexed sampling |
| Parameterized Returns | `parameterized_sim.py` | user-specified distribution: Normal or Student-t fat-tailed |

These are promoted into `backend/app/engine/` largely as-is (see §7). New engine work is
scoped precisely in §6.

## 4. Parameters tab (step 2) — field inventory

Grouped with progressive disclosure (fields appear/disappear based on earlier selections),
matching how portfoliovisualizer.com itself conditionally shows fields:

**Core** (always visible)
- Initial Amount
- Simulation Period in Years (5–75)
- Tax Treatment: Pre-tax / After-tax
- Simulation Model: Historical / Forecasted / Statistical / Parameterized

**Model-specific** (shown per Simulation Model)
- Historical → Use Full History (Yes/No), Bootstrap Model (Single Month / Single Year /
  Block of Years), Sequence of Returns Risk (No Adjustment / Worst 1–10 Years First)
- Forecasted, Statistical → Time Series Model: Normal / GARCH
- Parameterized → Distribution: Normal / Fat-tailed (Student-t + Degrees of Freedom),
  Expected Return, Expected Volatility (user-entered, no data estimation)

**Cashflow & Goals**
- Default: single cashflow — mode (none / contribute fixed / withdraw fixed amount /
  withdraw fixed % / rolling-average spending / geometric spending / withdraw by life
  expectancy), amount, inflation-adjusted toggle, frequency (monthly/quarterly/annual)
- Advanced toggle: **multi-goal mode** — table of named goals (Purpose, Type
  contribute/withdraw, Amount, Inflation-adjusted, Starts In, Ends In, Frequency), matching
  PV's Financial Goals table. Enabling multi-goal mode also enables **multistage
  planning**: Years to Retirement + Glide Path Years, and a second (retirement-stage)
  asset allocation alongside the starting allocation.

**Inflation & Rebalancing**
- Inflation Model: Historical / Parameterized (mean + volatility)
- Rebalancing: No rebalancing / Annual / Semi-annual / Quarterly / Monthly — confirmed
  present in PV's own form (not an invented field)

## 5. Results tab (step 3) — 7 sub-tabs

Sub-tabs are organized by chart/content type (matching what PV itself groups together on
the results page), not forced into Backtest Portfolio's existing 8-tab names — Monte
Carlo output is structurally different (percentile bands, survival curves, distribution
histograms) from a backtest's single realized path.

1. **Overview** — summary paragraph (N portfolios simulated, historical data range used,
   portfolio mean/CAGR/stdev), portfolio allocation pie chart, survival headline
   ("X/10,000 survived"), key stat cards (median end balance, median CAGR)
2. **Growth** — Portfolio Balance fan chart (10th/25th/50th/75th/90th percentile bands
   over time, log-scale toggle, inflation-adjusted toggle) + Portfolio Survival-over-time
   chart (% of simulations still solvent, by year)
3. **Distribution** — Portfolio End Balance Histogram + Maximum Drawdown Histogram
   (excluding cashflows)
4. **Metrics** — Performance Summary table: percentile columns (10/25/50/75/90) ×
   {Time-Weighted Return nominal, Time-Weighted Return real, End Balance nominal, End
   Balance real, Annual Mean Return, Annualized Volatility, Sharpe Ratio, Sortino Ratio,
   Max Drawdown, Max Drawdown Excl. Cashflows, Safe Withdrawal Rate, Perpetual Withdrawal
   Rate}
5. **Risk & Correlation** — asset-by-asset correlation matrix (reuse `CorrelationMatrix`
   component, see §8) with per-asset CAGR/Expected Return/Volatility, Expected
   Annual Return by horizon table (percentile × 1/3/5/10/15/20/25/30yr), Annual Return
   Probability table (P(return ≥ X%) by horizon), Loss Probability table (P(loss ≥ X%),
   excl./incl. cashflows, within-period vs end-of-period)
6. **Goals & Cashflows** — visible only when multi-goal mode is enabled: named-goals
   table (Purpose/Type/Starts/Ends/Frequency/Times/Total/Success%), Simulated Cashflows
   chart (nominal + present-dollar), Glide Path chart (allocation transition over time,
   visible only when multistage is enabled)
7. **Report** — export report.md + run_config.json + metrics.json, same pattern as
   Backtest Portfolio's Report tab

## 6. New engine work required (not a promotion — must be written)

These are genuine gaps between the existing `tests/*.py` engine and full PV parity.
Flagged explicitly so the implementation plan doesn't treat them as simple file moves.

1. **`engine/inflation.py`** (new module) — Historical inflation model (from Thai CPI,
   sourced via SEC or a documented substitute if Thai CPI isn't available through SEC
   Open Data — needs a data-source check during planning) and Parameterized inflation
   (mean + volatility draw), correlated with simulated asset returns per PV's approach.
2. **Bootstrap sub-modes** in `historical_sim.py` — currently single-year resample only;
   needs Single Month and Block-of-Years modes.
3. **Sequence-of-Returns Risk** — reorder simulated annual returns so the worst N years
   occur first, applied post-simulation to Historical-model paths.
4. **`engine/results.py` additions** — Sharpe Ratio, Sortino Ratio, Safe Withdrawal Rate,
   and Perpetual Withdrawal Rate, each computed per percentile band (not just point
   estimates); Portfolio Survival-over-time series (currently only final survival % is
   implicit); Correlation-and-returns summary table.
5. **`engine/goals.py`** (new module) — multi-goal cashflow orchestration (named goals
   with independent start/end/frequency) and linear glide-path allocation interpolation
   between a starting and retirement-stage portfolio.
6. **Rebalancing consistency fix** — Historical/Forecasted/Parameterized models bootstrap
   already-portfolio-weighted annual returns, which implicitly rebalances every draw.
   `statistical_sim.py`'s GBM model instead combines per-asset price paths via
   `asset_paths @ weights`, which is a drifting-weight (buy-and-hold) computation with no
   rebalancing. For the Rebalancing Frequency parameter to mean the same thing across all
   4 simulation models, `statistical_sim.py` needs explicit periodic-rebalance logic
   added to its path simulation (apply target weights to path VALUES at each rebalance
   date, not just once at the end).
7. **Import fix on promotion** — `statistical_sim.py` currently imports
   `forecasted_sim._garch_annual_returns` across files; fix the import path when both
   land in `backend/app/engine/`.

## 7. Architecture — one-directional data flow (matches Backtest Portfolio's pattern)

```
SEC Open Data API (api.sec.or.th)
  -> backend/app/data/sec_client.py       (promoted from sec_opendata_client.py)
  -> data/processed/nav_panel.parquet      (cache)
  -> backend/app/engine/                   (pure computation, no I/O)
  -> backend/app/api/                      (FastAPI + Pydantic v2)
  -> frontend/src/                         (React + TypeScript, 3-step wizard)
```

**Engine promotion map:**

| Existing file | New location | Notes |
|---|---|---|
| `gbm_engine.py` | `engine/gbm.py` | promote as-is |
| `historical_sim.py` | `engine/historical.py` | + bootstrap sub-modes, sequence-of-returns risk (§6.2, §6.3) |
| `forecasted_sim.py` | `engine/forecasted.py` | promote as-is |
| `statistical_sim.py` | `engine/statistical.py` | + rebalancing logic (§6.6); fix cross-import (§6.7) |
| `parameterized_sim.py` | `engine/parameterized.py` | promote as-is |
| `results_lib.py` | `engine/results.py` | + Sharpe/Sortino/SWR/PWR per percentile, survival series (§6.4) |
| `returns_lib.py` | `data/returns.py` | drop the yfinance/`webull_df` merge in `build_price_panel`; SEC-only |
| `sec_opendata_client.py` | `data/sec_client.py` | promote as-is |
| — | `engine/inflation.py` | new (§6.1) |
| — | `engine/goals.py` | new (§6.5) |
| `portfolio_lib.py` | **not promoted** | no optimizer in v1 — see §8 |
| `webull_client.py` | **not promoted** | yfinance-based, out of scope (SEC-only) |

**API** — `POST /api/simulate` (parallel to Backtest's `POST /api/backtests`), reusing
the fund-search/`testable-range` endpoints from Backtest Portfolio's pattern if the SEC
fund universe module can be shared code (same data source, same constraints). `GET
/api/health`. Mounted at both `/api/v1/*` and unversioned `/api/*`, matching Backtest's
convention.

**Schemas** — `SimulateRequest` (portfolio weights, Core params, a discriminated union of
model-specific params keyed by `simulation_model`, cashflow/goals config, inflation
config, rebalancing) → `SimulateResponse` split into sections matching the 7 results
sub-tabs.

**Error handling** — inherits Backtest Portfolio's hard rules: NAV gaps are hard errors,
never interpolated; "is this date range usable" is computed server-side only via a
`testable-range`-equivalent endpoint, never re-derived client-side.

**New project scaffolding needed** (currently absent): `pyproject.toml` (mirror
Backtest's `pandas>=3.0` floor — same corruption-bug rationale, same NAV pipeline),
`CLAUDE.md` (mirror Backtest's landmines section), and a `docker-compose.yml` using a
**named volume**, not a bind mount — this project's directory name also contains `:`
(`Monte Carlo Simulation Webull:SEC OPENAI`), which breaks Docker Desktop bind-mount path
parsing the same way it does for Backtest Portfolio.

## 8. Frontend — shell copied, internals replaced

- Copy `frontend/` scaffolding from Backtest Portfolio: Vite + React 19 + TypeScript,
  `Stepper.tsx`, `RunOverlay.tsx`, `api/client.ts` pattern (hand-mirrored types, no
  codegen), `styles.css` design tokens verbatim (verified via direct file read, 2026-08-04
  — `--accent: #5b21d6` / `#8b5cf6` dark, gray-25→900 scale, Inter font,
  `font-variant-numeric: tabular-nums` on all numeric cells, radii 6/10/14/pill, dark
  mode via `prefers-color-scheme` + `data-theme` override).
- **Reuse chart primitives**: `RunSummary.tsx` already contains generic, non-backtest-specific
  SVG chart components — `AxisCurve` (multi-series line chart, direct fit for the
  percentile fan chart), `Histogram`, `CorrelationMatrix`, `DataTable`. Extract/port these
  into `frontend/src/components/charts.tsx` in the new project rather than
  re-implementing hand-built SVG chart code from scratch. The two projects are separate
  git repos, so this is a copy-and-adapt, not a shared package.
- `PortfolioStep.tsx` — port near-verbatim (SEC fund search/select is identical between
  projects). Port the bulk-weight actions exactly as implemented: **Equal weight**,
  **Normalize to 100%**, **Clear** (confirmed via source read — Backtest Portfolio has no
  mean-variance optimizer; these three buttons are the full extent of its "auto weight"
  functionality, so `portfolio_lib.py`'s min-variance/tangency functions are not needed).
- `ParametersStep.tsx` — new, per §4.
- `ResultsView.tsx` — new, 7 sub-tabs per §5.

## 9. Testing

- pytest per engine module — reuse existing `test_*.py` for promoted-as-is modules
  (gbm, forecasted, parameterized); write new tests for inflation, goals, sequence-risk,
  bootstrap sub-modes, and the statistical-model rebalancing fix.
- Playwright e2e — one happy-path spec (portfolio → parameters → run → results), matching
  Backtest Portfolio's `e2e/happy-path.spec.ts` pattern.
- `tsc -b && vite build` doubles as frontend typecheck, per Backtest's convention.

## 10. Open items carried into planning (not blocking spec approval)

- Thai CPI data source for the Historical inflation model needs to be confirmed against
  what SEC Open Data actually exposes (or an alternative source identified) during
  implementation planning.
- Whether `GET /api/funds` / `testable-range` can literally be shared/ported from
  Backtest Portfolio's backend or need independent implementation should be resolved
  when the implementation plan lays out concrete tasks.
