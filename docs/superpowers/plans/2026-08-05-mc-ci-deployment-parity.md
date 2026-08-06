# Monte Carlo CI and Deployment Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Bring the Monte Carlo project to operational parity with the Backtest project for CI, Docker data bootstrapping, SEC cache refresh, production safeguards, repository hygiene, and documentation while preserving Monte Carlo-specific paths and host port `8001`.

**Architecture:** Add a push/PR GitHub Actions workflow that runs the existing backend and frontend gates. Make the committed `data/processed` cache available to the container image, while retaining the named `/app/data` volume for persisted run artifacts. Add a Monte Carlo-specific SEC refresh script and scheduled/manual workflow that refreshes `data/processed` only after a successful test run. Add the smallest production hardening layer needed by the existing API, then document and test the contracts.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pandas/pyarrow, pytest, Ruff, mypy, React 19, TypeScript, Vite, Playwright, Docker, GitHub Actions.

## Global Constraints

- Preserve Monte Carlo semantics; do not copy Backtest-only cashflow/rebalancing behavior into the simulation engine.
- Preserve MC host port `8001`; Backtest remains on `8000`.
- Keep the committed SEC cache at `data/processed/fund_universe.csv` and `data/processed/nav_panel.parquet`.
- Keep run persistence under `data/runs` on the named Docker volume.
- Do not call the live SEC API during a normal simulation; refresh is an explicit script/workflow operation.
- Use `apply_patch` for source and documentation edits.

### Task 1: Baseline and repository contract tests

**Files:**
- Create: `backend/tests/test_ci_workflow.py`
- Create: `backend/tests/test_dockerfile.py`
- Create: `backend/tests/test_repository_contract.py`

- [ ] **Step 1: Add tests for the required workflow and Docker contracts**

Assert that `.github/workflows/ci.yml` exists, triggers push and pull request events for `main`, installs Python 3.11, runs `pytest`, installs frontend dependencies with `npm ci`, and runs `npm run build`. Assert that the Dockerfile copies `data/` before the final image, exposes port 8000 internally, has a healthcheck against `/api/health`, and starts `backend.app.main:app`. Assert that `README.md`, `LICENSE`, `.github/workflows/refresh-sec-data.yml`, and `scripts/sec_download_mvp.py` exist after their implementation tasks.

- [ ] **Step 2: Run the new tests and record the expected initial failures**

Run `pytest backend/tests/test_ci_workflow.py backend/tests/test_dockerfile.py backend/tests/test_repository_contract.py -q`. The workflow, data-copy, README, LICENSE, and refresh assertions should fail before implementation.

### Task 2: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `backend/tests/test_ci_workflow.py`

- [ ] **Step 1: Implement the CI workflow**

Mirror the Backtest workflow with `actions/checkout@v4`, `actions/setup-python@v5` on Python 3.11, `pip install -e ".[dev]"`, and `pytest`; add a Node 20 job using `actions/setup-node@v4` with npm cache and `frontend/package-lock.json`, then run `npm ci` and `npm run build` from `frontend`. Trigger on push and pull request to `main`.

- [ ] **Step 2: Run the CI contract test**

Run `pytest backend/tests/test_ci_workflow.py -q` and require all assertions to pass.

### Task 3: Docker image and cache bootstrapping

**Files:**
- Modify: `.dockerignore`
- Modify: `Dockerfile`
- Modify: `backend/tests/test_dockerfile.py`
- Modify: `docker-compose.yml` only if needed to document the existing `8001:8000` mapping

- [ ] **Step 1: Allow the committed cache into the Docker build context**

Remove the `data/processed` exclusion from `.dockerignore` while continuing to exclude `data/raw`, generated caches, and `data/runs`.

- [ ] **Step 2: Seed the runtime image with the committed cache**

Add `COPY data/ ./data/` to the runtime stage after the backend source and before the frontend distribution. Keep the named volume mounted at `/app/data` so Docker seeds an empty volume from the image on first start and persists generated run artifacts afterward.

- [ ] **Step 3: Harden the healthcheck without changing the host port**

Add `ENV PORT=8000`, use `${PORT}` in the command and healthcheck, and include interval, timeout, start-period, and retries matching the Backtest deployment contract. The compose mapping remains `8001:8000`.

- [ ] **Step 4: Run Docker contract tests**

Run `pytest backend/tests/test_dockerfile.py -q` and inspect `docker build` if Docker is available.

### Task 4: Monte Carlo SEC refresh pipeline

**Files:**
- Create: `scripts/sec_download_mvp.py`
- Create: `scripts/__init__.py`
- Create: `.github/workflows/refresh-sec-data.yml`
- Create: `backend/tests/test_sec_download_mvp.py`
- Modify: `backend/app/data/sec_client.py` only if the script needs a shared cache helper

- [ ] **Step 1: Define the refresh contract with tests**

Test a mocked SEC response containing fund records and NAV records, verify that the script writes `data/processed/fund_universe.csv` and `data/processed/nav_panel.parquet`, preserves the expected column/index contract consumed by `find_funds()` and `load_nav_panel()`, and does not replace either cache file when the download raises an exception.

- [ ] **Step 2: Implement the refresh script**

Read `SEC_API_KEY` and optional `SEC_API_BASE_URL` from the environment, derive the current fund universe using the same SEC client contract as the application, download NAV data for that universe, write temporary files in `data/processed`, validate that both files can be loaded by the existing application readers, then atomically replace the committed cache files. Keep the normal app path offline and make all network access explicit to this script.

- [ ] **Step 3: Add the scheduled/manual workflow**

Use the Backtest schedule and `workflow_dispatch`, install Python 3.11 and `.[dev]`, run the refresh script with `SEC_API_KEY` and optional `SEC_API_BASE_URL`, run `pytest`, then `git add data/processed/` and commit/push only when the refreshed cache and tests succeed.

- [ ] **Step 4: Run refresh tests with network mocked**

Run `pytest backend/tests/test_sec_download_mvp.py -q` and require no live SEC request.

### Task 5: Backend operational parity

**Files:**
- Modify: `pyproject.toml`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/health.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/errors.py`
- Create: `backend/app/core/limiter.py`
- Create: `backend/tests/test_api_versioning.py`
- Create: `backend/tests/test_error_handling.py`
- Create: `backend/tests/test_rate_limiting.py`

- [ ] **Step 1: Add the operational dependencies and tests**

Add `slowapi` to runtime dependencies and `pyyaml` to dev dependencies. Test that versioned and unversioned aliases remain available, health includes `data_source`, invalid API input returns JSON error data, and the simulation POST has the Backtest-equivalent request limit without affecting GET routes.

- [ ] **Step 2: Add settings, error, CORS, and rate-limit layers**

Use `pydantic-settings` for allowed origins with a safe default, add a `Limiter` keyed by remote address, return a stable JSON body for unhandled exceptions, register the rate-limit and application exception handlers, and apply the limit to the expensive simulation POST route only.

- [ ] **Step 3: Add the data-status endpoint for cache observability**

Expose `/api/v1/data-status` and `/api/data-status` using the MC `data/processed` cache. Return `data_source`, NAV start/end, and fund count; return a structured 503 when either cache is missing or invalid.

- [ ] **Step 4: Run the operational tests**

Run `pytest backend/tests/test_api_versioning.py backend/tests/test_error_handling.py backend/tests/test_rate_limiting.py -q`.

### Task 6: Repository hygiene and documentation

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Modify: `.gitignore`
- Modify: `frontend/.gitignore`
- Modify: `backend/tests/test_repository_contract.py`

- [ ] **Step 1: Add repository ignore rules**

Ignore `.mypy_cache`, `.ruff_cache`, `*.pyc`, frontend dependencies/build outputs, TypeScript build info, Playwright cache/output, and generated run artifacts while preserving the committed `data/processed` cache.

- [ ] **Step 2: Add the project README**

Document the Monte Carlo scope, offline cache/data flow, local commands, `8001` development URL, Docker commands, named-volume behavior, explicit SEC refresh workflow, result URL/JSON behavior, testing, and known model limitations.

- [ ] **Step 3: Add a permissive project license file**

Use the same MIT license text and copyright holder convention as the sibling Backtest repository.

- [ ] **Step 4: Run repository contract tests**

Run `pytest backend/tests/test_repository_contract.py -q`.

### Task 7: Full verification

**Files:**
- No new source files; verify all changed files.

- [ ] **Step 1: Run backend tests and static checks**

Run `pytest -q`, `ruff check .`, and `mypy backend`.

- [ ] **Step 2: Build the frontend**

Run `npm ci` and `npm run build` in `frontend`.

- [ ] **Step 3: Run E2E against the MC port**

Run `npm run test:e2e` in `frontend` with the configured `8001` server.

- [ ] **Step 4: Validate workflow and Docker configuration**

Run the workflow/Docker/repository contract tests, `git diff --check`, and `docker build` when the Docker daemon is available. Report any unavailable Docker verification separately rather than treating it as passed.
