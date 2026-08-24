<div align="center">

# Monte Carlo Simulation

**Forward-looking portfolio simulation on SEC Thailand Open Data mutual fund NAV series**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](backend/app/main.py)
[![React + TypeScript](https://img.shields.io/badge/frontend-React%20%2B%20TS-61DAFB.svg)](frontend/package.json)

Built by [**Supachok Julaupay**](https://github.com/bblank09) &middot; [github.com/bblank09](https://github.com/bblank09)

</div>

## Table of Contents

1. [Abstract](#1-abstract)
2. [Motivation & Research Question](#2-motivation--research-question)
3. [System Architecture](#3-system-architecture)
4. [Methodology](#4-methodology)
5. [Features](#5-features)
6. [Installation & Setup](#6-installation--setup)
7. [Usage](#7-usage)
8. [Project Structure](#8-project-structure)
9. [Testing & Validation](#9-testing--validation)
10. [Example Output](#10-example-output)
11. [Limitations & Known Issues](#11-limitations--known-issues)
12. [Roadmap](#12-roadmap)
13. [License](#13-license)
14. [Acknowledgments & Data Attribution](#14-acknowledgments--data-attribution)

---

## 1. Abstract

This project is the forward-looking counterpart to the sibling
[Backtest Portfolio](../Backtest%20Portfolio%20Webull:SEC%20OPENAI) application. Backtest answers *"what did happen"* by
replaying one realized historical path; this application answers *"what could
happen"* by simulating thousands of possible future paths for a portfolio of
Thai mutual funds and reporting the resulting distribution — terminal-balance
percentiles, survival probability, drawdown and return distributions, risk
metrics, correlations, goal-hit probabilities, and an auditable methodology
report.

It is a full-stack application: a FastAPI simulation engine running four
distinct Monte Carlo models over a cached SEC Thailand Open Data NAV panel,
and a React/TypeScript dashboard for building a portfolio, choosing a model
and horizon, and inspecting the resulting distribution across seven analysis
tabs.

## 2. Motivation & Research Question

A historical backtest tells you what one realized sequence of Thai mutual
fund returns produced — but a single realized path is one draw from a much
wider space of things that could have happened, and says nothing directly
about what might happen next. Global forward-simulation tools such as
[Portfolio Visualizer](https://www.portfoliovisualizer.com/monte-carlo-simulation)
and [testfol.io](https://testfol.io/) cover US/global assets, not the SEC
Thailand fund universe, and none of them are wired to a locally cached,
reproducible NAV panel.

**Research question:** given a set of SEC-registered mutual funds, target
weights, a chosen simulation model (Historical, Forecasted, Statistical, or
Parameterized), a horizon, and an optional contribution/withdrawal/goal
policy, what is the resulting distribution of terminal outcomes — expressed as
percentile bands, survival probability, drawdown and return distributions,
and benchmark-relative risk statistics — computed transparently enough that
every model's assumptions are stated and every number traces back to the
engine code that produced it?

The project deliberately excludes portfolio optimization, efficient-frontier
construction, and live trading/broker execution — the scope is forward
simulation only, done across four distinct return-generating models so the
user can see how the outcome distribution shifts with the assumption set.

## 3. System Architecture

```text
SEC Open Data API
        │  explicit refresh only (scripts/sec_download_mvp.py)
        ▼
backend/app/sec/  →  fetch + normalize + validate
        │
        ▼
data/processed/fund_universe.csv
data/processed/nav_panel.parquet        (committed, reproducibility boundary)
        │  offline request path — normal app never calls SEC
        ▼
backend/app/data/sec_client.py          (cache readers, availability rules)
        ▼
backend/app/engine/                     (4 Monte Carlo models, pure computation)
  ├── historical.py        bootstrap resampling of realized annual returns
  ├── forecasted.py        historical bootstrap + forward drift/vol adjustment
  ├── statistical.py       Normal (GBM) or GARCH-simulated return paths
  ├── gbm.py                per-asset price-path GBM (drifting-weight, no rebalancing)
  ├── parameterized.py      user-supplied return/vol assumptions, no NAV required
  ├── glide_path_orchestration.py   age/horizon-based allocation glide paths
  ├── inflation.py          real-terms adjustment
  ├── goals.py               goal-hit probability across simulated paths
  ├── results.py             percentile/metric/risk aggregation
  └── orchestrator.py        request → engine config → SimulateResponse
        ▼
backend/app/api/                        (FastAPI REST, /api and /api/v1)
        ▼
frontend/src/                            (React + TypeScript wizard + result tabs)
        ▼
User's browser
```

Everything downstream of the parquet cache is a pure function of it: the
engine never calls the SEC API directly, so a simulation run is always
reproducible from `data/processed/` alone, and the app works fully offline
once the cache is populated. Each completed run is persisted to
`data/runs/<run_id>/{request.json,result.json}` and the run id is carried in
the frontend URL so a result can be reopened and shared — a saved run URL is
a public-by-link artifact: anyone holding the run id can read that portfolio
configuration and result.

**Tech stack**

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, hand-built SVG charting (no charting library dependency) |
| Backend | FastAPI, Pydantic v2, pandas, numpy, scipy, `arch` (GARCH) |
| Data | SEC Thailand Open Data API, cached locally as Parquet |
| Testing | pytest (backend engine + API), tsc (frontend type-check), Playwright (e2e) |

**Data flow:** SEC Open Data → `backend/app/sec/` fetch + normalize → local
Parquet cache → `backend/app/engine/` runs the selected Monte Carlo model
against the cached panel (or, for Parameterized, against user-supplied
assumptions only) → `backend/app/api/` serves the result contract →
the frontend renders it across seven result tabs (Overview, Growth,
Distribution, Metrics, Risk, Goals & Cashflows, Report).

## 4. Methodology

Four simulation models are implemented, selected via `simulation_model` in
the request:

| Model | File | Approach |
| --- | --- | --- |
| **Historical** | [`backend/app/engine/historical.py`](backend/app/engine/historical.py) | Bootstrap-resamples realized annual (or block-of-years / single-month) portfolio returns from the cached NAV history; the resampling unit is set by `bootstrap_model`. |
| **Forecasted** | [`backend/app/engine/forecasted.py`](backend/app/engine/forecasted.py) | Historical bootstrap with a forward-looking drift/volatility adjustment layered on top, for scenarios where the historical mean is not assumed to hold going forward. |
| **Statistical** | [`backend/app/engine/statistical.py`](backend/app/engine/statistical.py) / [`gbm.py`](backend/app/engine/gbm.py) | Simulates return paths from a fitted stochastic process — Normal (Geometric Brownian Motion) or GARCH, chosen via `time_series_model`. The GBM path additionally combines *per-asset* price paths via `asset_paths @ weights`, which is a drifting-weight computation with no implicit rebalancing, unlike the other three models (which bootstrap already-portfolio-weighted returns, implicitly rebalancing every draw). |
| **Parameterized** | [`backend/app/engine/parameterized.py`](backend/app/engine/parameterized.py) | Assumption-only: expected return and volatility are supplied directly by the user, so this model requires no NAV history at all. Historical holding diagnostics are reported as unavailable for this model rather than silently substituted. |

Every run additionally applies, where requested: an inflation adjustment to
real terms ([`inflation.py`](backend/app/engine/inflation.py)), age/horizon
glide-path allocation shifts
([`glide_path_orchestration.py`](backend/app/engine/glide_path_orchestration.py)),
and goal-hit probability tracking across all simulated paths
([`goals.py`](backend/app/engine/goals.py)). The
[`orchestrator.py`](backend/app/engine/orchestrator.py) module assembles the
request into an engine config, runs the chosen model, and aggregates
percentiles, metrics, and risk statistics via
[`results.py`](backend/app/engine/results.py) into the final
`SimulateResponse`.

**Rebalancing** is currently supported only when `simulation_model ==
"statistical"` with `time_series_model == "normal"`; every other
model/sub-model combination must request `rebalancing: "none"` until each
model's portfolio-level rebalancing semantics are implemented — the frontend
surfaces a hint rather than silently ignoring the field.

The in-app **Report** tab exposes the audit trail for each run: the model
used, every input, and the stated assumptions/limitations for that model —
downloadable as the raw `Result JSON`. Formula-level verification of the
engine's TWRR, CAGR, volatility, Sharpe/Sortino, and goal-cashflow
calculations against independently recomputed reference values is documented
in [`docs/manual-verification-formula-audit.md`](docs/manual-verification-formula-audit.md)
and [`docs/manual-verification-refs.md`](docs/manual-verification-refs.md).

## 5. Features

- **Guided 3-step workflow** — Portfolio → Parameters → Results, with a top
  stepper bar; each step validates before the next unlocks (e.g. weights
  must sum to 100% before continuing).
- **Search-driven fund picker** — browse the full cached SEC universe or
  filter by `proj_id`, fund name, class, or fund category; an allocation
  view updates live as weights change.
- **Four simulation models** — Historical, Forecasted, Statistical
  (Normal/GARCH), and Parameterized, each with its own required/optional
  inputs and stated assumptions (see [§4](#4-methodology)).
- **Seven-tab result view** — Overview, Growth, Distribution, Metrics, Risk,
  Goals & Cashflows (shown when goals are configured), Report.
- **Percentile-band and terminal-distribution charting** — histogram,
  percentile-range, and target-probability charts with hover tooltips and
  full date-labeled axes.
- **Survival probability & goal tracking** — probability of not depleting
  the portfolio, and per-goal hit-probability across all simulated paths,
  for withdrawal and multi-goal scenarios.
- **Inflation and glide-path modeling** — optional real-terms adjustment and
  age/horizon-based allocation glide paths.
- **Benchmark risk decomposition and correlation matrix** — risk metrics and
  a fund-to-fund correlation matrix over the simulated/underlying return
  series.
- **Rebalancing simulation** — none / monthly / quarterly / annual, currently
  scoped to Statistical Normal only (see [§4](#4-methodology) and
  [§11](#11-limitations--known-issues)).
- **Reproducibility by design** — every completed run persists
  `request.json` and `result.json` under `data/runs/<run_id>/`; the run id is
  carried in the URL so a result can be reopened and shared, with a `Result
  JSON` download in the Results view.
- **Dark theme** — the only theme; the DarkVeil animated background renders
  behind the wizard.

## 6. Installation & Setup

**Requirements:** Python 3.11+, Node.js 20+, `npm`, and (optionally) Docker.

```bash
# Backend — create the venv outside this directory, since its path contains
# ":" and Python refuses to create a venv inside such a path
python3 -m venv /private/tmp/monte_carlo_sec_venv
source /private/tmp/monte_carlo_sec_venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"

# Frontend
npm --prefix frontend ci
```

Copy `.env.example` to `.env` only if you need to refresh SEC data — running
a simulation against the committed local NAV cache does **not** call the SEC
API and does not require a key.

```text
SEC_API_KEY=...            # or SEC_OPENDATA_API_KEY; SEC_API_KEY takes precedence if both are set
SEC_API_BASE_URL=https://api.sec.or.th   # optional, this is the default
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000
MAX_PERSISTED_RUNS=500
```

### Keeping the cached NAV data fresh (optional)

`.github/workflows/refresh-sec-data.yml` re-downloads NAV for the funds in
the committed curated universe and commits the refreshed Parquet cache back
to `main` — only if the download *and* the full test suite both succeed, so a
bad or partial SEC response never gets committed. This is optional: the app
works fine off whatever NAV snapshot is already committed; the refresh just
keeps it current without anyone running the script by hand. To enable it on
your fork, add `SEC_API_KEY` (required) and optionally `SEC_API_BASE_URL`
under **Settings → Secrets and variables → Actions**.

### Docker (recommended for deployment)

```bash
docker compose up -d --build
```

This builds the frontend and backend into a single multi-stage image — FastAPI
serves the built static frontend itself, so there's nothing extra to host or
configure CORS for — and starts the app at `http://localhost:8001`. The
container listens on port `8000` internally; Compose maps it to host port
`8001` deliberately, so this app can run alongside the sibling Backtest
application on host port `8000`.

Compose mounts the named `mc-data` volume at `/app/data`, seeded from the
image's own baked-in `data/` on first start, so the NAV cache and saved
`data/runs` artifacts survive rebuilds. A host bind mount (`./data:/app/data`)
is deliberately **not** used: Docker Desktop's bind-mount path parsing breaks
when the host path contains a `:`, as this project's own directory name does.

To build and run without Compose:

```bash
docker build -t monte-carlo-sec .
docker run -p 8001:8000 -v mc-data:/app/data monte-carlo-sec
```

## 7. Usage

**Run the dev servers** (from the repository root, so cache/run-artifact
paths resolve correctly):

```bash
python3 -m uvicorn backend.app.main:app --reload --port 8001
npm --prefix frontend run dev
```

Open the frontend dev server URL and follow the 3-step workflow: build a
portfolio (search and add SEC funds until weights sum to 100%), choose a
simulation model and configure its parameters (horizon, cashflows,
rebalancing, goals, inflation), then run the simulation.

**API routes** are available under both `/api` and `/api/v1`:

- `GET /health`
- `GET /funds`
- `GET /data-status`
- `POST /simulate`
- `GET /simulate/{run_id}`

**Refresh SEC data manually:**

```bash
SEC_API_KEY="..." python3 scripts/sec_download_mvp.py
```

The refresh reads the current curated fund universe, downloads all NAV
pages, validates every fund and the final Parquet schema, and only then
atomically replaces the NAV cache — it updates the NAV panel for the
committed curated universe, it does not silently replace that universe with
an unreviewed set of SEC profiles. A failed or partial refresh leaves the
previous cache untouched.

## 8. Project Structure

```text
backend/
  app/
    api/          # FastAPI routes: funds, data-status, simulate, health
    data/          # Offline cache readers (sec_client.py)
    domain/        # Pydantic schemas, enums, error codes
    engine/        # 4 Monte Carlo models + inflation, glide paths, goals, results
    sec/           # Explicit-refresh SEC client and normalizers
  tests/           # Backend regression suite
tests/             # Legacy notebook-era compatibility smoke tests
frontend/
  src/
    components/    # PortfolioStep, ParametersStep, ResultsView, RunOverlay, Stepper, DarkVeil, charts
data/
  processed/       # Committed SEC NAV cache (nav_panel.parquet, fund_universe.csv)
  raw/              # Gitignored raw download cache
  runs/             # Gitignored persisted run artifacts (request.json, result.json)
docs/               # Manual verification, formula audit, methodology references
scripts/            # Explicit operational SEC refresh command
.github/workflows/  # CI and scheduled cache refresh
```

## 9. Testing & Validation

```bash
pytest -q                          # backend regression suite (backend/tests + tests)
ruff check .
mypy backend
npm --prefix frontend ci
npm --prefix frontend run build    # production build + frontend typecheck
```

The backend test suite covers each of the four Monte Carlo models,
portfolio/returns handling, results aggregation, and the SEC API client. The
root `tests/` directory holds the original notebook-era compatibility smoke
tests, targeting the canonical `backend.app.*` modules; the portfolio
optimizer and GARCH smoke tests are explicitly skipped where the
functionality or optional dependency is outside the shipped runtime scope.

**End-to-end (Playwright)** exercises the real app in a real browser against
the real backend and real cached SEC data:

```bash
cd frontend
npm run build                       # required: tests run against the production build
npx playwright install chromium     # first time only
npm run test:e2e
```

GitHub Actions (`.github/workflows/ci.yml`) runs backend tests, Ruff, mypy,
the frontend build, and the Playwright smoke suite on pushes and pull
requests to `main`. The scheduled refresh workflow is separate because it is
the only job allowed to call the SEC API and commit cache changes.

## 10. Example Output

Running a Historical-model simulation on a two-fund equal-weight portfolio
over a multi-year horizon produces, among other outputs, terminal-balance
percentile bands (p5/p25/p50/p75/p95), survival probability, annualized
return/volatility distributions, Sharpe/Sortino ratios, maximum-drawdown
distribution, and (when goals are configured) per-goal hit probability —
each traceable to the model that produced it in the Report tab. Independent
manual recomputation of a sample two-fund run is documented in
[`docs/manual-verification-run-result.json`](docs/manual-verification-run-result.json)
and [`docs/manual-verification-2026-08-06.xlsx`](docs/manual-verification-2026-08-06.xlsx).

## 11. Limitations & Known Issues

- **Not investment advice.** All outputs are model-based simulations, not
  predictions, forecasts, or guarantees of future results.
- **Simulated paths are model-dependent.** Changing the simulation model, its
  sub-model (bootstrap unit, Normal vs. GARCH), or its assumptions changes
  the output distribution; the Report tab states which model and assumptions
  produced a given run.
- **NAV gaps are hard errors, not interpolated.** SEC NAV history can contain
  genuine extended interior reporting outages; the application rejects a
  request whose window spans such a gap (`INSUFFICIENT_NAV_HISTORY`) rather
  than forward-filling a fabricated return. Only a bounded, isolated missing
  date caused by cross-fund calendar misalignment is tolerated and
  forward-filled, per the explicit threshold in
  `backend/app/data/returns.py`.
- **Fund selectability threshold.** A fund is only selectable for
  history-dependent models once its cached NAV has at least 252 distinct
  observations, computed server-side from the cache — the frontend picker
  must not reimplement this threshold independently.
- **Parameterized model has no historical dependency.** It is
  assumption-only and does not require NAV history; historical holding
  diagnostics are marked unavailable for that model rather than silently
  substituted.
- **Rebalancing scope is narrower than the original design.** Only
  Statistical Normal supports explicit rebalancing today; Historical,
  Forecasted, Parameterized, and Statistical GARCH requests must use
  `rebalancing: "none"` until their portfolio-level rebalancing semantics
  are implemented.
- **Statistical GBM combines per-asset paths, not portfolio-weighted
  returns.** `gbm.py`'s `asset_paths @ weights` is a drifting-weight
  computation with no implicit rebalancing, unlike the other three models,
  which bootstrap already-portfolio-weighted returns and implicitly
  rebalance every draw.
- **No live/real-time data.** The engine reads a locally cached NAV
  snapshot, refreshed via `.github/workflows/refresh-sec-data.yml` or
  manually via `scripts/sec_download_mvp.py`.
- **Scope.** No portfolio optimization, efficient-frontier construction, or
  live broker execution by design — this is the Monte Carlo counterpart to
  the sibling Backtest Portfolio app, which covers realized-path analysis.
- **Single-user, no persistence beyond `data/runs/`.** There is no account
  system or portfolio database; a saved run is addressable only by its run
  id, and a shared run URL is a public-by-link artifact — anyone with the id
  can read that configuration and result.

## 12. Roadmap

Planned next: portfolio-level rebalancing semantics for the remaining three
models, side-by-side multi-model comparison for the same portfolio, and
saved-portfolio templates. Contributions and discussion welcome via GitHub
Issues.

## 13. License

Released under the [MIT License](LICENSE).

## 14. Acknowledgments & Data Attribution

- **Author:** [Supachok Julaupay](https://github.com/bblank09) &mdash;
  [github.com/bblank09](https://github.com/bblank09).
- Fund NAV and profile data: [SEC Thailand Open Data](https://api.sec.or.th/)
  (Securities and Exchange Commission, Thailand).
- Sibling project: Backtest Portfolio Webull:SEC OPENAI — its UX shell
  (3-step wizard, design tokens, chart primitives) is the basis this app's
  frontend was copied from before its Monte Carlo internals diverged.
- Reference tools consulted during design:
  [Portfolio Visualizer's Monte Carlo simulation](https://www.portfoliovisualizer.com/monte-carlo-simulation),
  [testfol.io](https://testfol.io/).
