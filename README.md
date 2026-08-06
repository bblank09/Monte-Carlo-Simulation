# Monte Carlo Simulation

Forward-looking portfolio simulation for Thai mutual funds using SEC Thailand
Open Data NAV history. This is the Monte Carlo counterpart to the sibling
Backtest Portfolio application: Backtest answers “what happened?”, while this
application estimates “what could happen?” across many simulated paths.

## What it does

- Builds a portfolio from the cached SEC fund universe.
- Runs Historical, Forecasted, Statistical, or Parameterized simulation models.
- Reports terminal balance percentiles, survival probability, distributions,
  risk metrics, correlations, goals, and an auditable report.
- Persists each completed result as `data/runs/<run_id>/request.json` and
  `result.json`.
- Adds the run id to the URL so a result can be reopened and shared; the
  Results view also provides a `Result JSON` download.

The simulation is not investment advice and does not guarantee future results.

## Architecture and data flow

```text
SEC Open Data API
        │  explicit refresh only
        ▼
scripts/sec_download_mvp.py
        │
        ▼
data/processed/fund_universe.csv
data/processed/nav_panel.parquet
        │  offline request path
        ▼
backend/app/data/sec_client.py
        ▼
backend/app/engine/  →  backend/app/api/  →  frontend/src/
```

The normal application request path never calls SEC. The committed cache is
the reproducibility boundary for simulation runs. The refresh command reads
the current curated fund universe, downloads all NAV pages, validates every
fund and the final Parquet schema, and only then atomically replaces the NAV
cache. A failed or partial refresh leaves the previous cache untouched.

## Local setup

Requirements: Python 3.11+, Node.js 20+, npm, and (optionally) Docker.

```bash
python3 -m venv /private/tmp/monte_carlo_sec_venv
source /private/tmp/monte_carlo_sec_venv/bin/activate
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"

cd frontend
npm ci
cd ..
```

Copy `.env.example` to `.env` only when a live SEC refresh is needed. The
application can run against the committed cache without an API key.

Supported SEC key names are `SEC_API_KEY` and the original MC name
`SEC_OPENDATA_API_KEY`. `SEC_API_BASE_URL` is optional and defaults to
`https://api.sec.or.th`. `ALLOWED_ORIGINS` accepts a comma-separated list and
defaults to `*`.

## Run locally

Start the backend from the project root:

```bash
python3 -m uvicorn backend.app.main:app --reload --port 8001
```

Start the frontend separately when developing UI:

```bash
npm --prefix frontend run dev
```

The production build is served by FastAPI. The MC host port is intentionally
`8001` so it can run beside the Backtest application on `8000`.

Useful API routes are available under both `/api` and `/api/v1`:

- `GET /health`
- `GET /funds`
- `GET /data-status`
- `POST /simulate`
- `GET /simulate/{run_id}`

## Refresh SEC data

Refresh the existing curated fund universe manually:

```bash
SEC_API_KEY="..." python3 scripts/sec_download_mvp.py
```

The same operation is available from `.github/workflows/refresh-sec-data.yml`,
which can run daily or through `workflow_dispatch`. Add `SEC_API_KEY` as a
GitHub Actions secret and optionally set `SEC_API_BASE_URL`. The workflow runs
the full test suite before committing changes under `data/processed/`.

The refresh intentionally updates the NAV panel for the committed curated fund
universe; it does not silently replace the curated fund universe with an
unreviewed set of SEC profiles.

## Docker

```bash
docker compose up -d --build
```

Open `http://localhost:8001`. The container listens on port `8000` internally
and Compose maps it to MC host port `8001`.

The image includes the committed `data/processed` cache. Compose mounts the
named `mc-data` volume at `/app/data`; Docker seeds an empty volume from the
image on first start, and the volume then preserves both the cache and saved
`data/runs` artifacts across rebuilds. A host bind mount is deliberately not
used because the project directory name contains `:`.

## Tests and quality gates

```bash
pytest -q
ruff check .
mypy backend
npm --prefix frontend ci
npm --prefix frontend run build
```

Playwright runs against the production frontend served by FastAPI:

```bash
cd frontend
npx playwright install chromium   # first run only
npm run test:e2e
```

GitHub Actions runs the backend test suite and frontend build on pushes and
pull requests to `main`. The scheduled refresh workflow is separate because it
is the only job allowed to call the SEC API and commit cache changes.

## Repository structure

```text
backend/app/api/       FastAPI routes and persistence
backend/app/data/      Offline cache readers
backend/app/domain/    Pydantic schemas and error codes
backend/app/engine/    Monte Carlo models and result calculations
backend/app/sec/       Explicit refresh client and normalizers
frontend/src/          React wizard and result tabs
scripts/               Explicit operational refresh command
data/processed/        Committed SEC cache
data/runs/             Ignored persisted run artifacts
.github/workflows/     CI and scheduled cache refresh
```

## Known limitations

- Simulated paths are model-dependent estimates, not forecasts or guarantees.
- SEC NAV history can contain gaps; the application rejects unusable histories
  rather than fabricating returns through interpolation.
- Historical and statistical model assumptions are documented in the code and
  the in-app Report tab; changing assumptions changes the distribution.
- No account system, broker execution, portfolio optimization, or live market
  pricing is included.

## License and data attribution

Code is released under the [MIT License](LICENSE). Fund metadata and NAV data
come from [SEC Thailand Open Data](https://api.sec.or.th/).
