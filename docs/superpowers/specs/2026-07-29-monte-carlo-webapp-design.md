# Monte Carlo Portfolio Web App — Design Spec (v1)

**Date:** 2026-07-29
**Course context:** ต่อยอดจาก CQF Module 1-2 Monte Carlo notebook project (`docs/superpowers/specs/2026-07-26-monte-carlo-portfolio-simulation-design.md`, notebook `01_monte_carlo_simulation.ipynb`)
**Sibling project:** [Portfolio-Backtester](https://github.com/bblank09/Portfolio-Backtester) — same author, same CQF course, historical backtesting instead of Monte Carlo. This design deliberately reuses its architecture, visual language, and objective-preset UX pattern.

**Goal:** Turn the existing, already-implemented Monte Carlo simulation engine (currently scattered as scratch modules under `tests/`) into a public-facing web app — a FastAPI + React/TypeScript dashboard where a general user builds their own portfolio and runs a real Monte Carlo simulation against one of four common real-world objectives.

---

## 1. เหตุผล/บริบท (Why)

The notebook project (`01_monte_carlo_simulation.ipynb`) already implements and verifies all four Portfolio-Visualizer-parity simulation models (Historical, Forecasted, Statistical, Parameterized/GBM+GARCH) as standalone Python modules under `tests/` (`gbm_engine.py`, `portfolio_lib.py`, `returns_lib.py`, `historical_sim.py`, `forecasted_sim.py`, `statistical_sim.py`, `parameterized_sim.py`, `results_lib.py`, `sec_opendata_client.py`, `webull_client.py`). These were written as scratch/proof-of-correctness scripts per the notebook implementation plan (section 10: "prove correct in `tests/`, then paste into the notebook") — they were never meant to be the permanent home for this code, which is why the folder now reads as messy: test files and library modules are mixed together.

The user's sibling project, Portfolio-Backtester, answered the analogous backward-looking question ("what would have happened") with a full web app, and *explicitly excluded* Monte Carlo from its scope by design. This project is the natural forward-looking counterpart: "what **could** happen."

Researched against real-world Monte Carlo usage (financial planning literature — Kitces, eMoney Advisor, T. Rowe Price, Maxifi, Portfolio Visualizer), the dominant use cases cluster into four questions, which become this app's **objective presets** — directly mirroring the sibling repo's four backtesting objectives (Past Performance / Monthly DCA / Monthly Withdrawal / Rebalancing Impact).

## 2. ขอบเขต (Scope, locked from conversation)

- **v1 covers only the Monte Carlo Simulation tool** (notebook 01's engine). Financial Goals and Asset-Liability Modeling (notebooks 02/03) are out of scope until their own engines exist.
- **Users are the general public** (portfolio/demo piece), not just the course instructor — UI must be approachable without assuming CQF or Portfolio Visualizer background, but every result must still be traceable to a stated formula (same standard as the sibling repo's Report tab).
- **Core user action**: pick their own portfolio (ticker + weight, not the fixed 5-asset set from the notebook spec) and run a real Monte Carlo simulation, choosing one of 4 objective presets.
- **4 objective presets for v1** (validated against real financial-planning practice, not just PV feature parity):

  | Objective | User question | Auto-filled defaults | Objective-specific summary |
  |---|---|---|---|
  | **Growth Projection** | "If I keep this portfolio, what could it be worth in N years?" | No cashflow, Statistical model (Normal), 30yr horizon | Percentile fan chart, ending-balance histogram |
  | **Retirement Withdrawal** | "If I withdraw $X/month, will it last?" | Fixed monthly withdrawal, 30yr horizon | Success rate %, depletion-year distribution |
  | **Goal Probability** | "What's the % chance I reach $X by year N?" | Target amount + target year prompt | P(reach goal), shortfall distribution |
  | **Risk / Tail-Risk Check** | "How bad could the bad case be?" | No cashflow, same portfolio | VaR/ES table, max-drawdown distribution, worst-decile paths |

  **Lump Sum vs DCA is deferred to v2** — it requires a dual-run comparison view (not a single-run auto-fill), and did not surface as a top real-world use case in research; the sibling repo backlogged its analogous feature too.

- Selecting an objective **auto-fills config but never hides the full input panel** — all 4 underlying simulation models (Historical / Forecasted / Statistical / Parameterized, including GARCH(1,1) time-series and Fat-Tailed distribution) remain selectable underneath every objective, per the original notebook spec's "replicate every PV field" requirement.
- **Portfolio input is free-form** (any ticker via yfinance, plus Thai SEC funds via `proj_id`) — not restricted to the notebook's fixed 5-asset demo set, since the audience is the general public building their own portfolio.

## 3. Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌────────────────────┐
│ yfinance / SEC    │ --> │ Cache/normalize layer │ --> │ data/processed/     │
│ Open Data (NAV)    │     │ (backend/app/data/)   │     │ price_panel.parquet │
└─────────────────┘     └──────────────────────┘     └──────────┬─────────┘
                                                                    │
                                                                    ▼
┌─────────────────┐     ┌──────────────────────┐     ┌────────────────────┐
│ React + TS         │ <-- │ FastAPI REST API      │ <-- │ MC Engine            │
│ frontend            │ --> │ (backend/app/api/)    │ --> │ (backend/app/engine/) │
└─────────────────┘     └──────────────────────┘     └────────────────────┘
```

This is a direct structural mirror of Portfolio-Backtester's architecture (same layering: data → cache → engine → API → frontend), swapping the historical backtest engine for a Monte Carlo engine.

**Tech stack** (matches sibling repo exactly, for consistency and shared design language):

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, hand-built SVG charting (no charting library dependency) |
| Backend | FastAPI, Pydantic v2, pandas, numpy, scipy, `arch` (GARCH) |
| Data | yfinance (US tickers), SEC Thailand Open Data (Thai funds), cached locally |
| Testing | pytest (engine + API), tsc (frontend type-check) |

**Promotion of existing code** (this is the concrete fix for "folder is messy"):

| Current location | New location | Notes |
|---|---|---|
| `tests/gbm_engine.py` | `backend/app/engine/gbm_engine.py` | Already correct — pure promotion |
| `tests/portfolio_lib.py` | `backend/app/engine/portfolio_lib.py` | Markowitz weights |
| `tests/returns_lib.py` | `backend/app/engine/returns_lib.py` | Price panel → log returns |
| `tests/historical_sim.py`, `forecasted_sim.py`, `statistical_sim.py`, `parameterized_sim.py` | `backend/app/engine/models/` | The 4 PV-parity simulation models |
| `tests/results_lib.py` | `backend/app/engine/results_lib.py` | Percentile/VaR/ES calculations |
| `tests/sec_opendata_client.py`, `webull_client.py` | `backend/app/data/` | Renamed `webull_client.py` → `price_client.py` (it uses yfinance, not Webull — see notebook spec section 2, Webull TH API proved unreliable) |
| `tests/test_*.py` | `backend/tests/` | Actual test suite, now testing the promoted package instead of sibling scratch files |

## 4. Screens (mirrors sibling repo's Main Workspace pattern)

1. **Portfolio Builder** — ticker/weight table, add/remove asset, allocation donut chart, live validation (weights sum to 100%, ticker resolves, price history exists), optional example portfolio for a zero-effort first run.
2. **Objective Picker** — 4 cards (Growth / Withdrawal / Goal / Risk), each with a plain-language question and a one-line preview of what the result will show.
3. **Assumptions Drawer** — simulation model (Historical/Forecasted/Statistical/Parameterized), time-series model (Normal/GARCH), distribution (Normal/Fat-Tailed), horizon, initial amount, rebalancing. Beginner defaults visible; advanced fields (GARCH params, degrees of freedom, bootstrap block size) collapsed by default — same rule as the sibling repo.
4. **Assumption Review** — plain-language summary before running (e.g. "Simulate $1,000,000 over 30 years using Statistical Returns (Normal). Portfolio: SPY 60%, QQQ 40%. Withdraw $2,000/month starting year 1."), plus data warnings.
5. **Run States** — validating inputs → fetching prices → estimating parameters (μ, Σ) → simulating paths → computing results.
6. **Results** — objective-specific summary tab first (per table in section 2), then shared tabs: Percentile Fan Chart, Ending Balance Distribution, Risk (VaR/ES/drawdown), Formula reference drawer (equation + CQF module citation + interpretation, same UX as the sibling repo's metric cards), Report export (`report.md`, `run_config.json`, `metrics.json`).

**Visual language**: reused directly from Portfolio-Backtester's `frontend/src/styles.css` — Inter font, purple accent `#5b21d6` (hover `#4c1bb3`), gray-25→900 neutral scale, `--success`/`--warn`/`--danger` semantic colors, 6/10/14px corner radii. "Serious financial workspace" feel, no marketing hero, opens directly into the builder.

## 5. Data flow & error handling

- Price/NAV fetch failures fall back to the last cached `data/processed/` snapshot with a visible warning banner — never silently substitute or forward-fill fabricated data (same rule the sibling repo states explicitly for its historical NAV cache).
- Short price history (fewer years than the requested estimation window) is surfaced as an explicit warning, not silently truncated.
- SEC Open Data requires a subscription key (per the original notebook spec's open item 9) — if missing, the app falls back to a bundled cached NAV snapshot for the two demo Thai funds and disables live SEC fund search, with a clear banner explaining why.

## 6. Testing

- Extend the existing pytest suite (already covers all 4 simulation models, GBM engine, portfolio weights, results calculations) — move it from `tests/test_*.py` (currently testing sibling scratch files by relative import) to `backend/tests/`, testing the promoted `backend/app/engine/` package instead.
- Add FastAPI endpoint smoke tests (`backend/tests/test_api.py`) once the API layer exists.
- `tsc -b` type-check on the frontend, matching the sibling repo's CI story.

## 7. Out of scope for v1

- Lump Sum vs DCA comparison (v2 — needs dual-run/comparison UI, not just an auto-fill preset)
- Financial Goals notebook (02) and Asset-Liability Modeling notebook (03) — no web engine exists for these yet
- Auth/accounts, saved portfolios, live broker execution
- Tax-accurate treatment (After-tax Returns remains a coarse toggle, as in the original notebook spec)
- Fixed 5-asset restriction from the original notebook spec — v1 web app accepts any ticker/fund the user enters

## 8. Open items before implementation

- Confirm which of the two data sources (yfinance vs SEC Open Data) needs a live API call at request time vs. can rely purely on the cached `data/processed/` panel already produced by the notebook.
- Confirm SEC Open Data subscription key status (notebook spec section 9 flagged this as unresolved) — determines whether Thai fund search is live or cached-only for v1.
- Decide whether the promoted `backend/app/engine/` package keeps the notebook's "no shared imports" constraint (irrelevant for a web app — that constraint existed only for the notebook's stand-alone-file teaching requirement) — **resolved: does not apply**, the whole point of the web app is a shared, importable engine package.
