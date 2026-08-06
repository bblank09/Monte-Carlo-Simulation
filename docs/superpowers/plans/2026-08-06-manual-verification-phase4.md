# Phase 4 — Reference Citations + Manual Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cite the academic/industry source for every formula in `backend/app/engine/`, verify each formula against that source line-by-line, run one real simulation on 2 real SEC funds over a short window, independently recompute every metric on every ResultsView tab in Excel (not by copying the Python), and file the discrepancy report — fixing `backend/app/engine/` with a TDD test first for any real bug found.

**Architecture:** This is a verification project, not a feature build. Scope is the **Monte Carlo Simulation** repo (this repo) — NOT the sibling Backtest Portfolio repo. The checklist's tab names (Growth, Drawdown, Returns, Cashflows, Rebalancing) map onto **this app's actual tabs**: Overview, Growth, Distribution, Metrics, Risk & Correlation, Goals & Cashflows (only when a goal is configured). "Rebalancing" here means the rebalancing-frequency parameter inside the Statistical(GBM) model, not a standalone tab.

**Tech Stack:** Python (backend engine), pytest (TDD), Excel (`.xlsx` via anthropic-skills:xlsx skill) for independent recomputation, `curl`/httpx for hitting the running FastAPI simulate endpoint.

## Global Constraints

- Scope is `backend/app/engine/` and `backend/app/api/simulate.py` in **this repo only** — do not touch `../Backtest Portfolio Webull:SEC OPENAI`.
- `pandas>=3.0` is a hard floor (CLAUDE.md). Do not downgrade.
- NAV gaps are hard errors — never forward-fill or interpolate across a gap.
- Excel recomputation in 4.4 MUST use native Excel formulas (SUM, PRODUCT, PERCENTILE.INC, STDEV.S, etc.) referencing the raw NAV/return data — copying the Python formula as a pasted-in number is not verification and is explicitly disallowed by the checklist.
- Compare to 6 decimal places. Anything that differs beyond that needs a written reason (rounding, ddof convention, trading-day-count convention, etc.) — a bare "doesn't match" is not an acceptable end state for this task.
- Any real bug found must be fixed via TDD: write the failing test in `backend/tests/` first, watch it fail, then fix `backend/app/engine/`.
- Funds selected for 4.3: **K-SET50** (`proj_id=M0209_2548`, equity, `main` class) and **K-MONEY** (`proj_id=M0337_2550`, money-market, `main` class) — note both share `unique_id=C0000000021` (same AMC) but have distinct `proj_id`s, which is the actual fund-identifying field the API uses.
- **AMENDED (post-Task-3, by explicit user decision):** the plan originally called for a 4-month historical window (2025-01–2025-04). Task 3 discovered the live API's `SimulateRequest` schema has **no historical-window field at all** — only `simulation_period_years` (`ge=5, le=75`, a forward-projection horizon), and the engine always calibrates `mu`/`sigma` from the **full** committed NAV history (2015-01 through the cache's latest date), then projects forward. The user confirmed: use the actual run as executed — `simulation_period_years=5`, full-history calibration, `n_paths=2000`, `seed=42`, weights 50/50, `rebalancing=annual`, `time_series_model=normal`, a real goal configured (`multi_goal_enabled=true`, one withdrawal goal `starts_year=1..ends_year=5`) — as ground truth. **Every downstream task (4, 5) reconciles against this actual run, not the original 4-month concept.** The result JSON is `docs/manual-verification-run-result.json` (Task 3, complete) with `run_id=run_20260806_071020_b81fa66d`. Actual JSON response key layout (differs from the plan's original shorthand): top-level `{run_id, created_at, data_source, overview, growth, distribution, metrics, risk, goals, run_config}`; `metrics = {percentile_table, sharpe, sortino, safe_withdrawal_rate, perpetual_withdrawal_rate}`; `risk = {correlation_and_returns, value_at_risk, expected_shortfall, expected_return_by_horizon, annual_return_probability, loss_probability}`; `growth = {fan_chart, survival_over_time}`; `distribution = {ending_balance_histogram, max_drawdown_histogram}`; `goals` populated with `summary`, `cashflows_nominal`, `cashflows_present_dollar`.

---

## File Structure

| Path | Responsibility |
|---|---|
| `docs/manual-verification-refs.md` | Task 1 deliverable: one citation per formula, mapped to the exact function/line in `backend/app/engine/`. |
| `docs/manual-verification-formula-audit.md` | Task 2 deliverable: match/mismatch table, code vs. reference, per formula. |
| `docs/manual-verification-run-result.json` | Task 3 deliverable: raw simulate API response for the 2-fund, 4-month run. |
| `docs/manual-verification-2026-08-06.xlsx` | Task 4/4.5 deliverable: independent Excel recomputation of every tab's metrics + comparison to the JSON, tied out to 6 decimals. |
| `backend/tests/test_engine_manual_verification_fixes.py` | Only created if Task 4 surfaces a real bug (TDD regression test), one test per fixed formula. |

---

## Task 1: Formula Reference Citations (4.1)

**Files:**
- Create: `docs/manual-verification-refs.md`
- Read: `backend/app/engine/gbm.py`, `backend/app/engine/statistical.py`, `backend/app/engine/historical.py`, `backend/app/engine/forecasted.py`, `backend/app/engine/parameterized.py`, `backend/app/engine/results.py`, `backend/app/engine/goals.py`, `backend/app/engine/inflation.py`, `backend/app/engine/glide_path_orchestration.py`, `backend/app/engine/orchestrator.py`

**Interfaces:**
- Produces: a citation table keyed by `(engine_file, function_name)` that Task 2 consumes row-by-row.

- [ ] **Step 1: Enumerate every distinct formula in the engine**

Run and read each file fully (already read in this session: `results.py`, `statistical.py`; still need `gbm.py`, `historical.py`, `forecasted.py`, `parameterized.py`, `goals.py`, `inflation.py`, `glide_path_orchestration.py`, `orchestrator.py`). Build a checklist of formulas, e.g.:

- GBM path simulation (`gbm.py::simulate_gbm_paths`) — Geometric Brownian Motion discretization
- Portfolio rebalancing value roll-forward (`statistical.py::_rebalanced_portfolio_values`)
- CAGR / TWRR (`results.py::percentile_table`)
- Max drawdown (`results.py::percentile_table`)
- Parametric VaR/ES under normality (`results.py::parametric_var_es`)
- Historical (simulation) VaR/ES (`results.py::compute_var_es`)
- Sharpe ratio, Sortino ratio (`results.py::sharpe_sortino_by_percentile`)
- Safe withdrawal rate via root-finding, Perpetual withdrawal rate (`results.py::withdrawal_rates_by_percentile`)
- Bootstrap historical resampling (`historical.py`)
- GARCH(1,1) volatility simulation (`forecasted.py::_garch_annual_returns`)
- Inflation adjustment (`inflation.py`)
- Glide-path weight interpolation (`glide_path_orchestration.py`)
- Goal/cashflow application (`goals.py`)

- [ ] **Step 2: Find one authoritative citation per formula**

Use academic APIs per CLAUDE.md convention (Semantic Scholar / arXiv / OpenAlex) plus canonical textbook/practitioner sources. Suggested anchors — verify with `hyperresearch fetch` rather than trusting from memory:

- GBM discretization: Hull, *Options, Futures, and Other Derivatives* ch. 14, or Glasserman, *Monte Carlo Methods in Financial Engineering* (2003), ch. 3.
- CAGR / TWRR: CFA Institute GIPS Standards, "Time-Weighted Rate of Return" definition.
- Max drawdown: Magdon-Ismail & Atiya, "Maximum Drawdown" (2004), *Risk*.
- Parametric VaR/ES (Gaussian): Jorion, *Value at Risk* (3rd ed.), ch. 5–6; RiskMetrics Technical Document (J.P. Morgan, 1996).
- Historical/simulation VaR/ES: Jorion ch. 9.
- Sharpe ratio: Sharpe, W.F. (1994), "The Sharpe Ratio," *Journal of Portfolio Management*.
- Sortino ratio: Sortino & Price (1994), "Performance Measurement in a Downside Risk Framework," *Journal of Investing*.
- Safe withdrawal rate: Bengen, W. (1994), "Determining Withdrawal Rates Using Historical Data," *Journal of Financial Planning*.
- GARCH(1,1): Bollerslev, T. (1986), "Generalized Autoregressive Conditional Heteroskedasticity," *Journal of Econometrics*.
- Bootstrap resampling: Efron, B. & Tibshirani, R. (1993), *An Introduction to the Bootstrap*.

For each, run `hyperresearch fetch <url>` (per CLAUDE.md — never WebFetch) and record a full citation (author, year, title, publisher/journal, and either a DOI/arXiv id or the exact page/section referenced).

- [ ] **Step 3: Write `docs/manual-verification-refs.md`**

One row per formula:

```markdown
## <Formula name>
- **Code:** `backend/app/engine/<file>.py::<function>` (lines X–Y)
- **Citation:** <Author, Year, Title, Publisher/Journal, DOI/URL>
- **Canonical equation:** <LaTeX-ish or plain-text equation from the source>
```

- [ ] **Step 4: Commit**

```bash
git add docs/manual-verification-refs.md
git commit -m "docs: add formula reference citations for Phase 4 verification"
```

---

## Task 2: Code-vs-Reference Formula Audit (4.2)

**Files:**
- Create: `docs/manual-verification-formula-audit.md`
- Read: `docs/manual-verification-refs.md` (from Task 1), each engine source file

**Interfaces:**
- Consumes: citation table from Task 1.
- Produces: match/mismatch verdicts Task 4/4.5 uses to decide whether a discrepancy is expected (documented convention difference) or a real bug.

- [ ] **Step 1: For each formula in the Task 1 table, write out the canonical equation and the code's actual computation side by side**

Example row format:

```markdown
| Formula | Reference equation | Code (file:line) | Match? | Notes |
|---|---|---|---|---|
| CAGR | (V_end/V_start)^(1/n) - 1 | `results.py:27` `paths[:, -1] ** (1 / n_years) - 1` | ✅ Match | paths already normalized to V_start=1 |
| Sharpe | (R_p - R_f) / σ_p | `results.py:134` | ✅ Match | uses per-path realized annualized return, not population mean — documented deviation from textbook (population) Sharpe, see Notes |
| Max Drawdown | min_t (V_t / max_{s<=t} V_s - 1) | `results.py:36` | ✅ Match | |
```

- [ ] **Step 2: Flag every deviation explicitly, with reasoning**

For anything that doesn't match verbatim (e.g., ddof=0 vs ddof=1 in `std()`, population vs. sample volatility, per-path vs. cross-sectional Sharpe), write a short paragraph: is this an intentional/documented design choice (cite the CLAUDE.md landmine list or a code comment), or a candidate bug to carry into Task 4's live-number check?

- [ ] **Step 3: Commit**

```bash
git add docs/manual-verification-formula-audit.md
git commit -m "docs: audit engine formulas against cited references"
```

---

## Task 3: Real Simulation Run + Result JSON (4.3)

**Files:**
- Create: `docs/manual-verification-run-result.json`
- Modify (read-only reference): `backend/app/api/simulate.py`, `frontend/src/components/ParametersStep.tsx`, `frontend/src/components/PortfolioStep.tsx` (for request-payload shape)

**Interfaces:**
- Consumes: nothing new (uses the running API).
- Produces: `docs/manual-verification-run-result.json`, the single ground-truth artifact Task 4 recomputes against.

- [ ] **Step 1: Start the backend**

```bash
uvicorn backend.app.main:app --reload
```

- [ ] **Step 2: Confirm the two funds and inspect the simulate request schema**

```bash
curl -s localhost:8000/api/funds | python3 -c "import json,sys; d=json.load(sys.stdin); print([f for f in d if 'K-SET50' in f.get('display_name','') or 'K-MONEY' in f.get('display_name','')])"
```

Read `backend/app/api/simulate.py` for the exact request body field names (fund ids, weights, `simulation_period_years`, `n_paths`, `seed`, `simulation_model`, `rebalancing`) before building the payload — do not guess field names.

- [ ] **Step 3: POST a real simulation request**

Use the Statistical (GBM, normal) model — simplest to hand-recompute — with a small but non-trivial `n_paths` (e.g. 2000) and a fixed `seed` so the run is reproducible, weights 50/50 K-SET50 / K-MONEY, `simulation_period_years` set to match the 4-month window by using `data_start`/`data_end` fields if the API supports a custom historical window, otherwise the shortest supported period. Save the full response:

```bash
curl -s -X POST localhost:8000/api/simulate -H "Content-Type: application/json" -d @/tmp/manual-verify-request.json \
  | python3 -m json.tool > "docs/manual-verification-run-result.json"
```

- [ ] **Step 4: Sanity-check the JSON has all tabs' data**

```bash
python3 -c "import json; d=json.load(open('docs/manual-verification-run-result.json')); print(list(d.keys()))"
```

Confirm keys covering Overview/Growth/Distribution/Metrics/Risk/Goals exist (`percentile_table`, `expected_return_by_horizon`, `annual_return_probability`, `loss_probability`, `sharpe_sortino_by_percentile`, `withdrawal_rates_by_percentile`, `survival_series`, `correlation_and_returns_table`, and `goals`/cashflow data if a goal was configured in the request).

- [ ] **Step 5: Commit**

```bash
git add docs/manual-verification-run-result.json
git commit -m "docs: capture real 2-fund simulation result for manual verification"
```

---

## Task 4: Independent Excel Recomputation, All Tabs (4.4)

This is the core verification task. Load the **`anthropic-skills:xlsx`** skill when executing this task — the deliverable is a real `.xlsx` file.

**Files:**
- Create: `docs/manual-verification-2026-08-06.xlsx`
- Read: `docs/manual-verification-run-result.json` (Task 3), `data/processed/nav_panel.parquet` or `data/processed/price_panel.csv` (raw NAV inputs), `docs/manual-verification-formula-audit.md` (Task 2, for which conventions to replicate)

**Interfaces:**
- Consumes: Task 3's JSON (target values to reconcile against), Task 2's audit table (which convention to use per formula), raw NAV data.
- Produces: the Phase 4.5 deliverable file directly (same file, no rename needed).

**Workbook structure — one sheet per tab, plus a Raw Data and a Summary Tie-Out sheet:**

- [ ] **Step 1: `Raw Data` sheet**

Export the exact **full NAV history** the live engine actually used to derive `mu`/`sigma` for this run — per the Global Constraints amendment, the engine calibrates from full committed history, not a 4-month slice. Pull the full daily NAV series for `proj_id=M0209_2548` (K-SET50) and `proj_id=M0337_2550` (K-MONEY) from `data/processed/nav_panel.parquet` into columns (date, NAV_SET50, NAV_MONEY), plus a daily-return column for each via `=NAV_t/NAV_{t-1}-1`. This is the ground truth every other sheet's formulas reference — no values are pasted from Python except this raw NAV feed, which is itself the committed cache CLAUDE.md documents as authoritative. Read the parquet's actual column schema first (`df.columns.tolist()`) to confirm whether columns are keyed by `proj_id` or another id — do not assume the schema.

```bash
python3 -c "
import pandas as pd
df = pd.read_parquet('data/processed/nav_panel.parquet')
print(df.columns.tolist()[:10])
"
```
Read `backend/app/api/simulate.py`'s `load_nav_returns` to confirm the exact date range and column-selection logic the live engine used, then replicate it for the export.

- [ ] **Step 2: `Overview` sheet**

Recompute, with native formulas, ending balance percentiles and CAGR percentiles by simulating the same GBM math **conceptually explained, not by re-running 2000 paths in Excel** — instead, reconcile the **closed-form portfolio statistics** (annualized mean/vol of the historical window feeding the GBM `mu`/`sigma` inputs) against what the JSON's `metrics.percentile_table` implies (note: `percentile_table` is nested under the `metrics` key in the actual response, not top-level), e.g.:
  - `=AVERAGE(daily_returns)*252` vs. the `mu` the API would have derived
  - `=STDEV.S(daily_returns)*SQRT(252)` vs. `sigma`
  - Cross-check that `percentile_table.cagr["50"]` from the JSON is plausible given those two numbers (within 1 simulation-noise band, not exact — GBM percentiles are stochastic, so state explicitly in the sheet that percentile-band values are *plausibility-checked*, not bit-exact, while all deterministic aggregate formulas below are bit-exact to 6 decimals).

- [ ] **Step 3: `Growth` sheet**

Not applicable as literal per-path Excel columns (2000 stochastic paths). Instead independently recompute the **deterministic** ingredients feeding growth: `weights @ mu`, `weights @ sigma @ weights` (portfolio variance, via `=MMULT`), and confirm those match a hand Excel calc from the Raw Data sheet's mu/sigma vector, to 6 decimals.

- [ ] **Step 4: `Distribution` sheet**

Reconcile `risk.expected_return_by_horizon` and `risk.annual_return_probability` (both live under the `risk` key in the actual response): these are functions of the *same* `mu`/`sigma`/`n_paths`/`seed` — document in the sheet that exact percentile reproduction requires the identical PRNG stream (numpy `default_rng(seed)`), which Excel cannot replicate deterministically. State this as a **known, documented limitation** of Excel-only verification for stochastic percentile outputs, and instead verify: (a) monotonicity (P90 > P75 > P50...) holds in the JSON, (b) `annual_return_probability` thresholds are monotonically decreasing in threshold for a fixed horizon, both checkable via Excel formulas directly on the JSON-exported percentile numbers (no re-simulation needed).

- [ ] **Step 5: `Metrics` sheet**

Recompute Sharpe/Sortino/withdrawal-rate **formulas themselves** (JSON keys: `metrics.sharpe`, `metrics.sortino`, `metrics.safe_withdrawal_rate`, `metrics.perpetual_withdrawal_rate` — separate keys under `metrics`, not one combined object) against a single concrete illustrative path (construct one manual example path of 5 annual returns matching the run's `simulation_period_years=5`) fully by hand in Excel. Cross-reference Task 2's audit's two flagged bug candidates here — the Sharpe/Sortino numerator (geometric CAGR) vs. denominator (arithmetic per-period std) basis mismatch — and confirm numerically on this illustrative path whether it produces a materially different ratio than a textbook same-basis Sharpe would:
  - Sharpe: `=(AnnualizedReturn-RiskFreeRate)/Volatility`
  - Sortino: downside deviation via `=SQRT(SUMPRODUCT((returns<0)*returns^2)/COUNT(returns))`
  - Safe withdrawal rate: goal-seek (Excel's built-in Goal Seek, or `=IRR`-style manual bisection walkthrough documented in the sheet) confirming the same balance-depletion formula `balance = MAX(balance*g - rate, 0)` per period.
  Tie the illustrative-path numbers to 6 decimals against a hand trace; this validates the *formula*, since exact percentile-of-2000-paths values can't be replicated per Step 4's documented limitation.

- [ ] **Step 6: `Risk & Correlation` sheet**

Fully bit-exact reconcilable — these are deterministic functions of the historical return series, not of simulated paths (JSON key: `risk.correlation_and_returns`, not `correlation_and_returns_table`):
  - `=CORREL(returns_SET50, returns_MONEY)` vs. JSON `risk.correlation_and_returns.correlation`
  - `=STDEV.S(returns)*SQRT(252)` vs. JSON `volatility`
  - `=AVERAGE(returns)*252` vs. JSON `expected_return`
  - `=PRODUCT(1+returns)^(252/COUNT(returns))-1` vs. JSON `cagr`
  - Parametric VaR/ES via `=NORM.S.INV(0.90)` and the Jorion closed-form from Task 1's citation, vs. JSON `risk.value_at_risk` / `risk.expected_shortfall`.
  All of these must match the JSON to 6 decimals — flag any that don't as real discrepancies.

- [ ] **Step 7: `Goals & Cashflows` sheet** (Task 3's run included a real goal — this sheet is mandatory, not conditional)

Hand-trace the cashflow application formula from `goals.py` against a manual 5-period (`simulation_period_years=5`) balance roll-forward in Excel, cell by cell, reconciling against the JSON's `goals.summary` (`success_rate`), `goals.cashflows_nominal`, and `goals.cashflows_present_dollar` for the "Retirement withdrawal" goal (annual $20,000 inflation-adjusted withdrawal, years 1–5).

- [ ] **Step 8: `Summary Tie-Out` sheet**

One row per JSON metric that is bit-exact-checkable (Risk & Correlation sheet's items, the deterministic mu/sigma/variance from Growth sheet), columns: `Metric | JSON value | Excel value | Diff | Match (Y/N) | Notes`. Use `=ROUND(ABS(JSON-Excel),6)=0` for the Match column.

- [ ] **Step 9: Save the workbook**

Save directly as `docs/manual-verification-2026-08-06.xlsx` (this is also the 4.5 deliverable — no separate save step needed).

- [ ] **Step 10: Commit**

```bash
git add docs/manual-verification-2026-08-06.xlsx
git commit -m "docs: independent Excel recomputation for Phase 4 manual verification"
```

---

## Task 5: Discrepancy Triage + TDD Fixes (4.5)

**Files:**
- Modify: whichever `backend/app/engine/*.py` file(s) Task 4's Summary Tie-Out sheet flags as a real (not documented-convention) mismatch
- Create: `backend/tests/test_engine_manual_verification_fixes.py` (only if a fix is needed)

**Interfaces:**
- Consumes: Task 4's Summary Tie-Out `Match = N` rows.
- Produces: passing regression tests + corrected engine code.

- [ ] **Step 1: For each `Match = N` row, classify it**

Either (a) a documented convention difference already explained in Task 2's audit (population vs. sample stdev, etc.) — no code change, just note it in the sheet — or (b) a genuine bug.

- [ ] **Step 2: For each genuine bug, write the failing test first**

```python
def test_<metric>_matches_manual_calc():
    # Uses the exact NAV window / weights from docs/manual-verification-run-result.json
    ...
    assert result == pytest.approx(<hand_calculated_value>, abs=1e-6)
```

- [ ] **Step 3: Run it, confirm it fails**

```bash
pytest backend/tests/test_engine_manual_verification_fixes.py -v
```

- [ ] **Step 4: Fix the engine code minimally**

- [ ] **Step 5: Run it, confirm it passes; run full suite to check for regressions**

```bash
pytest backend/tests/test_engine_manual_verification_fixes.py -v
pytest
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/engine/ backend/tests/test_engine_manual_verification_fixes.py
git commit -m "fix: correct <metric> formula per Phase 4 manual verification"
```

- [ ] **Step 7: Final commit of all Phase 4 docs together (if not already committed piecemeal)**

```bash
git add docs/
git commit -m "docs: complete Phase 4 manual verification (refs, audit, Excel tie-out)"
```
