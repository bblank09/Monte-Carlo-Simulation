# Monte Carlo Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing, already-verified Monte Carlo engine (currently scratch modules under `tests/`) into a public FastAPI + React/TypeScript web app where a user builds their own portfolio and runs one of 4 objective-preset Monte Carlo simulations end-to-end.

**Architecture:** Promote the existing engine code from `tests/*.py` into a real `backend/app/engine/` package (data → cache → engine → API → frontend, mirroring the sibling Portfolio-Backtester repo). Build one FastAPI endpoint (`POST /api/simulate`) that accepts a portfolio + objective + assumptions and returns percentile/risk results. Build a React/TS frontend with 4 screens (Portfolio Builder → Objective Picker → Assumptions Review → Results) reusing the sibling repo's design tokens.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pandas, numpy, scipy, `arch` (GARCH), yfinance, requests, python-dotenv, pytest — React 18, TypeScript, Vite, hand-built SVG charts, vitest.

## Global Constraints

- Backend package lives at `backend/app/`, tests at `backend/tests/` — mirrors `docs/superpowers/specs/2026-07-29-monte-carlo-webapp-design.md` section 3 promotion table exactly (file-for-file).
- The web app engine package **may share imports across files** — the notebook's "no shared imports" constraint was a teaching-only rule for the standalone notebook and does not apply here (spec section 8, resolved item).
- No new tickers/funds are hardcoded — portfolio input is free-form per spec section 2.
- Selecting an objective preset auto-fills config fields but never removes/disables any input (spec section 2) — the full 4-simulation-model config must always remain in the request payload.
- Every simulation result must be reproducible given the same `seed` in the request (existing engine functions already take `config["seed"]`; preserve this exactly).
- `.env` holds `SEC_OPENDATA_API_KEY`; never hardcode secrets; `.env` stays gitignored (already true).
- Visual tokens for the frontend: Inter font, accent `#5b21d6` / hover `#4c1bb3` / active `#401793`, gray scale `--gray-25` `#fcfcfd` through `--gray-900` `#14151a`, semantic `--success` `#0f7a4f`, `--warn` `#92620a`, `--danger` `#b42318`, radii `--r-sm` 6px / `--r-md` 10px / `--r-lg` 14px — copied from the sibling repo's `frontend/src/styles.css`.

---

## Task 1: Backend package scaffolding + promote pure-math engine files

**Files:**
- Create: `pyproject.toml`
- Create: `backend/__init__.py`, `backend/app/__init__.py`, `backend/app/engine/__init__.py`
- Create: `backend/app/engine/gbm_engine.py` (moved from `tests/gbm_engine.py`, unchanged)
- Create: `backend/app/engine/portfolio_lib.py` (moved from `tests/portfolio_lib.py`, unchanged)
- Create: `backend/app/engine/returns_lib.py` (moved from `tests/returns_lib.py`, unchanged)
- Create: `backend/tests/__init__.py`, `backend/tests/engine/__init__.py`
- Create: `backend/tests/engine/test_gbm_engine.py` (moved from `tests/test_gbm_engine.py`, import path updated)
- Create: `backend/tests/engine/test_portfolio.py` (moved from `tests/test_portfolio.py`, import path updated)
- Create: `backend/tests/engine/test_returns.py` (moved from `tests/test_returns.py`, import path updated)
- Delete: `tests/gbm_engine.py`, `tests/portfolio_lib.py`, `tests/returns_lib.py`, `tests/test_gbm_engine.py`, `tests/test_portfolio.py`, `tests/test_returns.py`

**Interfaces:**
- Produces: `backend.app.engine.gbm_engine.simulate_gbm_paths(S0, mu, sigma, n_years, steps_per_year, n_paths, seed=None) -> np.ndarray`
- Produces: `backend.app.engine.portfolio_lib.min_variance_weights(sigma: np.ndarray) -> np.ndarray`
- Produces: `backend.app.engine.portfolio_lib.tangency_weights(mu: np.ndarray, sigma: np.ndarray, rf: float) -> np.ndarray`
- Produces: `backend.app.engine.returns_lib.build_price_panel(nav_df: pd.DataFrame, webull_df: pd.DataFrame) -> pd.DataFrame`
- Produces: `backend.app.engine.returns_lib.log_returns(price_panel: pd.DataFrame) -> pd.DataFrame`
- Produces: `backend.app.engine.returns_lib.estimate_mu_sigma(returns_df: pd.DataFrame, periods_per_year: int = 252) -> tuple[np.ndarray, np.ndarray]`

- [ ] **Step 1: Read the existing test files to capture their exact assertions before moving anything**

```bash
cat "tests/test_gbm_engine.py" "tests/test_portfolio.py" "tests/test_returns.py"
```

Copy their contents verbatim into a scratch note — you'll paste them into the new locations in Step 4, changing only the import line.

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[project]
name = "monte-carlo-webapp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.8",
    "pandas>=2.2",
    "numpy>=1.26",
    "scipy>=1.13",
    "arch>=7.0",
    "yfinance>=0.2",
    "requests>=2.32",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27"]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
```

- [ ] **Step 3: Create package `__init__.py` files (all empty)**

```bash
mkdir -p backend/app/engine backend/tests/engine
touch backend/__init__.py backend/app/__init__.py backend/app/engine/__init__.py
touch backend/tests/__init__.py backend/tests/engine/__init__.py
```

- [ ] **Step 4: Move the three pure-math files verbatim (no content changes)**

```bash
git mv tests/gbm_engine.py backend/app/engine/gbm_engine.py
git mv tests/portfolio_lib.py backend/app/engine/portfolio_lib.py
git mv tests/returns_lib.py backend/app/engine/returns_lib.py
```

- [ ] **Step 5: Move the three matching test files, updating only their import line**

```bash
git mv tests/test_gbm_engine.py backend/tests/engine/test_gbm_engine.py
git mv tests/test_portfolio.py backend/tests/engine/test_portfolio.py
git mv tests/test_returns.py backend/tests/engine/test_returns.py
```

Then edit each moved test file: change `from gbm_engine import ...` to `from backend.app.engine.gbm_engine import ...` (and equivalently for `portfolio_lib` / `returns_lib`). Do not change any assertion.

- [ ] **Step 6: Install the package in editable mode and run the moved tests**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest backend/tests/engine -v
```

Expected: all tests PASS (same assertions as before, just a new import path).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: promote gbm_engine/portfolio_lib/returns_lib into backend.app.engine package"
```

---

## Task 2: Promote the 4 simulation models + results library

**Files:**
- Create: `backend/app/engine/models/__init__.py`
- Create: `backend/app/engine/models/historical_sim.py` (moved from `tests/historical_sim.py`, unchanged)
- Create: `backend/app/engine/models/forecasted_sim.py` (moved from `tests/forecasted_sim.py`, unchanged)
- Create: `backend/app/engine/models/statistical_sim.py` (moved from `tests/statistical_sim.py`, import paths updated)
- Create: `backend/app/engine/models/parameterized_sim.py` (moved from `tests/parameterized_sim.py`, unchanged)
- Create: `backend/app/engine/results_lib.py` (moved from `tests/results_lib.py`, unchanged)
- Create: `backend/tests/engine/models/__init__.py`
- Create: `backend/tests/engine/models/test_historical.py`, `test_forecasted.py`, `test_statistical.py`, `test_parameterized.py` (moved, import paths updated)
- Create: `backend/tests/engine/test_results.py` (moved, import path updated)
- Delete: the 5 original `tests/*_sim.py` + `tests/results_lib.py` + their 5 matching `tests/test_*.py` files

**Interfaces:**
- Consumes: `backend.app.engine.gbm_engine.simulate_gbm_paths` (Task 1)
- Produces: `backend.app.engine.models.historical_sim.simulate_historical(returns_df: pd.DataFrame, weights: np.ndarray, config: dict) -> np.ndarray`
- Produces: `backend.app.engine.models.forecasted_sim.simulate_forecasted(mu, sigma, weights, config, returns_df=None) -> np.ndarray`
- Produces: `backend.app.engine.models.statistical_sim.simulate_statistical(mu, sigma, weights, config, returns_df=None) -> np.ndarray`
- Produces: `backend.app.engine.models.parameterized_sim.simulate_parameterized(config: dict) -> np.ndarray`
- Produces: `backend.app.engine.results_lib.percentile_table(paths: np.ndarray, initial_amount: float) -> pd.DataFrame`
- Produces: `backend.app.engine.results_lib.parametric_var_es(weights, mu, sigma, alpha=0.90) -> tuple[float, float]`
- Produces: `backend.app.engine.results_lib.compute_var_es(ending_values: np.ndarray, alpha=0.90) -> tuple[float, float]`
- All four `simulate_*` functions return an `np.ndarray` of shape `(n_paths, n_years + 1)` where column 0 is always `1.0` (normalized starting value) — this is the shared contract Task 3's orchestrator relies on.

- [ ] **Step 1: Move the 4 simulation model files into `backend/app/engine/models/`**

```bash
mkdir -p backend/app/engine/models backend/tests/engine/models
touch backend/app/engine/models/__init__.py backend/tests/engine/models/__init__.py
git mv tests/historical_sim.py backend/app/engine/models/historical_sim.py
git mv tests/forecasted_sim.py backend/app/engine/models/forecasted_sim.py
git mv tests/statistical_sim.py backend/app/engine/models/statistical_sim.py
git mv tests/parameterized_sim.py backend/app/engine/models/parameterized_sim.py
git mv tests/results_lib.py backend/app/engine/results_lib.py
```

- [ ] **Step 2: Fix internal imports in the moved files**

In `backend/app/engine/models/statistical_sim.py`, change:
```python
from gbm_engine import simulate_gbm_paths
from forecasted_sim import _garch_annual_returns
```
to:
```python
from backend.app.engine.gbm_engine import simulate_gbm_paths
from backend.app.engine.models.forecasted_sim import _garch_annual_returns
```

`historical_sim.py`, `forecasted_sim.py`, and `parameterized_sim.py` have no internal cross-module imports — move them unchanged.

- [ ] **Step 3: Move the matching test files, updating import lines only**

```bash
git mv tests/test_historical.py backend/tests/engine/models/test_historical.py
git mv tests/test_forecasted.py backend/tests/engine/models/test_forecasted.py
git mv tests/test_statistical.py backend/tests/engine/models/test_statistical.py
git mv tests/test_parameterized.py backend/tests/engine/models/test_parameterized.py
git mv tests/test_results.py backend/tests/engine/test_results.py
```

Update each moved test's import line to the new `backend.app.engine...` path, matching the pattern from Step 2. Do not change any assertion.

- [ ] **Step 4: Run the full engine test suite**

```bash
pytest backend/tests/engine -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: promote 4 simulation models + results_lib into backend.app.engine package"
```

---

## Task 3: Promote data clients + write the simulation orchestrator

**Files:**
- Create: `backend/app/data/__init__.py`
- Create: `backend/app/data/sec_opendata_client.py` (moved from `tests/sec_opendata_client.py`, `.env` path updated)
- Create: `backend/app/data/price_client.py` (moved from `tests/webull_client.py`, renamed — it uses yfinance, not Webull, per spec section 3)
- Create: `backend/tests/data/__init__.py`
- Create: `backend/tests/data/test_sec_api.py`, `test_price_client.py` (moved, updated)
- Create: `backend/app/engine/orchestrator.py`
- Create: `backend/tests/engine/test_orchestrator.py`
- Delete: `tests/sec_opendata_client.py`, `tests/webull_client.py`, `tests/test_sec_api.py`, `tests/test_webull_import.py`, `tests/test_nav_fetch.py`, `tests/test_scaffold.py`

**Interfaces:**
- Consumes: all 4 `simulate_*` functions (Task 2), `percentile_table`/`parametric_var_es`/`compute_var_es` (Task 2), `estimate_mu_sigma` (Task 1)
- Produces: `backend.app.data.price_client.get_prices(symbols: list[str], start: str, end: str) -> pd.DataFrame` (renamed from `get_webull_prices`, same signature/behavior)
- Produces: `backend.app.data.sec_opendata_client.get_daily_nav(proj_id, start_date, end_date) -> pd.DataFrame`, `.find_equity_funds(...)`, `.get_amcs()`
- Produces: `backend.app.engine.orchestrator.run_simulation(request: dict) -> dict` — the single entry point Task 5's API route calls. `request` shape:
  ```python
  {
    "weights": {"SPY": 0.6, "QQQ": 0.4},   # ticker -> weight, must sum to 1.0
    "price_panel": pd.DataFrame,            # wide panel, columns = tickers, index = dates
    "simulation_model": "statistical",      # "historical" | "forecasted" | "statistical" | "parameterized"
    "time_series_model": "normal",          # "normal" | "garch" (ignored for historical/parameterized)
    "distribution": "normal",               # "normal" | "fat_tailed" (parameterized only)
    "degrees_of_freedom": 5,                # required if distribution == "fat_tailed"
    "expected_return": 0.08,                # required if simulation_model == "parameterized"
    "expected_volatility": 0.15,             # required if simulation_model == "parameterized"
    "initial_amount": 1_000_000.0,
    "simulation_period_years": 30,
    "n_paths": 5000,
    "seed": 42,
  }
  ```
  Return shape:
  ```python
  {
    "percentile_table": {"ending_balance": {"10": ..., "25": ..., "50": ..., "75": ..., "90": ...},
                          "cagr": {"10": ..., ..., "90": ...}},
    "var_es": {"var": float, "es": float},
    "ending_balances": list[float],   # full array, for histogram rendering client-side
    "fan_chart": {"years": list[int], "p10": list[float], "p25": [...], "p50": [...], "p75": [...], "p90": [...]},
  }
  ```

- [ ] **Step 1: Move the two data client files**

```bash
mkdir -p backend/app/data backend/tests/data
touch backend/app/data/__init__.py backend/tests/data/__init__.py
git mv tests/sec_opendata_client.py backend/app/data/sec_opendata_client.py
git mv tests/webull_client.py backend/app/data/price_client.py
```

- [ ] **Step 2: Update the `.env` path in `sec_opendata_client.py`**

Change:
```python
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
```
to:
```python
load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")
```
(one extra `.parent` because the file moved one directory deeper: `tests/` → `backend/app/data/`).

- [ ] **Step 3: Rename the function in `price_client.py`**

Change `def get_webull_prices(...)` to `def get_prices(...)` (same body, same signature) — the name was misleading since it uses yfinance, not Webull (see the docstring already in the file explaining why).

- [ ] **Step 4: Move and fix the matching test files**

```bash
git mv tests/test_sec_api.py backend/tests/data/test_sec_api.py
git mv tests/test_webull_import.py backend/tests/data/test_price_client.py
```

Update imports (`from sec_opendata_client import ...` → `from backend.app.data.sec_opendata_client import ...`) and rename any call to `get_webull_prices` → `get_prices`. Delete `tests/test_nav_fetch.py` and `tests/test_scaffold.py` — both tested scaffolding concerns (`.env` presence, directory layout) that Task 6's `.env.example` and this plan's directory structure already supersede.

```bash
rm tests/test_nav_fetch.py tests/test_scaffold.py
```

- [ ] **Step 5: Write the failing orchestrator test**

`backend/tests/engine/test_orchestrator.py`:
```python
import numpy as np
import pandas as pd
import pytest
from backend.app.engine.orchestrator import run_simulation


def _price_panel():
    dates = pd.date_range("2020-01-01", periods=1300, freq="B")
    rng = np.random.default_rng(0)
    spy = 100 * np.cumprod(1 + rng.normal(0.0003, 0.01, len(dates)))
    qqq = 100 * np.cumprod(1 + rng.normal(0.0004, 0.014, len(dates)))
    return pd.DataFrame({"SPY": spy, "QQQ": qqq}, index=dates)


def test_run_simulation_statistical_normal_returns_expected_shape():
    request = {
        "weights": {"SPY": 0.6, "QQQ": 0.4},
        "price_panel": _price_panel(),
        "simulation_model": "statistical",
        "time_series_model": "normal",
        "initial_amount": 1_000_000.0,
        "simulation_period_years": 10,
        "n_paths": 200,
        "seed": 42,
    }
    result = run_simulation(request)
    assert set(result.keys()) == {"percentile_table", "var_es", "ending_balances", "fan_chart"}
    assert len(result["ending_balances"]) == 200
    assert len(result["fan_chart"]["years"]) == 11
    assert result["percentile_table"]["ending_balance"]["50"] > 0


def test_run_simulation_parameterized_requires_expected_return_and_volatility():
    request = {
        "weights": {"SPY": 1.0},
        "price_panel": _price_panel(),
        "simulation_model": "parameterized",
        "distribution": "normal",
        "initial_amount": 100_000.0,
        "simulation_period_years": 5,
        "n_paths": 50,
        "seed": 1,
    }
    with pytest.raises(KeyError):
        run_simulation(request)


def test_run_simulation_rejects_weights_not_summing_to_one():
    request = {
        "weights": {"SPY": 0.5, "QQQ": 0.3},
        "price_panel": _price_panel(),
        "simulation_model": "statistical",
        "time_series_model": "normal",
        "initial_amount": 1_000_000.0,
        "simulation_period_years": 5,
        "n_paths": 50,
        "seed": 1,
    }
    with pytest.raises(ValueError, match="weights must sum to 1.0"):
        run_simulation(request)
```

- [ ] **Step 6: Run it to verify it fails**

```bash
pytest backend/tests/engine/test_orchestrator.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.engine.orchestrator'`.

- [ ] **Step 7: Write `backend/app/engine/orchestrator.py`**

```python
import numpy as np

from backend.app.engine.returns_lib import log_returns, estimate_mu_sigma
from backend.app.engine.results_lib import percentile_table, compute_var_es
from backend.app.engine.models.historical_sim import simulate_historical
from backend.app.engine.models.forecasted_sim import simulate_forecasted
from backend.app.engine.models.statistical_sim import simulate_statistical
from backend.app.engine.models.parameterized_sim import simulate_parameterized

_MODEL_FUNCS = {
    "historical": simulate_historical,
    "forecasted": simulate_forecasted,
    "statistical": simulate_statistical,
    "parameterized": simulate_parameterized,
}


def run_simulation(request: dict) -> dict:
    weights_map = request["weights"]
    if abs(sum(weights_map.values()) - 1.0) > 1e-6:
        raise ValueError("weights must sum to 1.0")

    tickers = list(weights_map.keys())
    weights = np.array([weights_map[t] for t in tickers])
    price_panel = request["price_panel"][tickers]
    returns_df = log_returns(price_panel)
    mu, sigma = estimate_mu_sigma(returns_df)

    model = request["simulation_model"]
    config = {k: v for k, v in request.items() if k not in ("weights", "price_panel")}

    if model == "historical":
        paths = simulate_historical(returns_df, weights, config)
    elif model == "forecasted":
        paths = simulate_forecasted(mu, sigma, weights, config, returns_df=returns_df)
    elif model == "statistical":
        paths = simulate_statistical(mu, sigma, weights, config, returns_df=returns_df)
    elif model == "parameterized":
        paths = simulate_parameterized(config)
    else:
        raise ValueError(f"unknown simulation_model: {model}")

    initial_amount = request["initial_amount"]
    pct_table = percentile_table(paths, initial_amount)
    ending_values = paths[:, -1] * initial_amount
    var, es = compute_var_es(ending_values)

    years = list(range(paths.shape[1]))
    values = paths * initial_amount
    fan_chart = {
        "years": years,
        "p10": np.percentile(values, 10, axis=0).tolist(),
        "p25": np.percentile(values, 25, axis=0).tolist(),
        "p50": np.percentile(values, 50, axis=0).tolist(),
        "p75": np.percentile(values, 75, axis=0).tolist(),
        "p90": np.percentile(values, 90, axis=0).tolist(),
    }

    return {
        "percentile_table": {
            "ending_balance": {str(p): float(pct_table[p]["ending_balance"]) for p in pct_table.columns},
            "cagr": {str(p): float(pct_table[p]["cagr"]) for p in pct_table.columns},
        },
        "var_es": {"var": float(var), "es": float(es)},
        "ending_balances": ending_values.tolist(),
        "fan_chart": fan_chart,
    }
```

- [ ] **Step 8: Run the test again to verify it passes**

```bash
pytest backend/tests/engine/test_orchestrator.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 9: Run the entire backend suite to confirm nothing broke**

```bash
pytest backend/tests -v
```

Expected: all PASS.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "feat: add simulation orchestrator; promote data clients into backend.app.data"
```

---

## Task 4: FastAPI app with `/api/simulate` endpoint

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/schemas.py`
- Create: `backend/app/api/simulate.py`
- Create: `backend/tests/api/__init__.py`
- Create: `backend/tests/api/test_simulate.py`

**Interfaces:**
- Consumes: `backend.app.engine.orchestrator.run_simulation` (Task 3), `backend.app.data.price_client.get_prices` (Task 3)
- Produces: `POST /api/simulate` — request body validated by `SimulateRequest` (Pydantic), response validated by `SimulateResponse`. This is the only HTTP contract the frontend (Task 6+) talks to.

- [ ] **Step 1: Write the failing API test**

`backend/tests/api/test_simulate.py`:
```python
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_simulate_statistical_returns_200_with_expected_shape():
    payload = {
        "tickers": ["SPY", "QQQ"],
        "weights": [0.6, 0.4],
        "start_date": "2020-01-01",
        "end_date": "2025-12-31",
        "simulation_model": "statistical",
        "time_series_model": "normal",
        "initial_amount": 1000000.0,
        "simulation_period_years": 10,
        "n_paths": 200,
        "seed": 42,
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "percentile_table" in body
    assert "fan_chart" in body
    assert len(body["fan_chart"]["years"]) == 11


def test_simulate_rejects_weights_not_summing_to_one():
    payload = {
        "tickers": ["SPY", "QQQ"],
        "weights": [0.5, 0.3],
        "start_date": "2020-01-01",
        "end_date": "2025-12-31",
        "simulation_model": "statistical",
        "time_series_model": "normal",
        "initial_amount": 1000000.0,
        "simulation_period_years": 10,
        "n_paths": 200,
        "seed": 42,
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 422
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest backend/tests/api/test_simulate.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.main'`.

- [ ] **Step 3: Write `backend/app/api/schemas.py`**

```python
from typing import Literal, Optional
from pydantic import BaseModel, model_validator


class SimulateRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    start_date: str
    end_date: str
    simulation_model: Literal["historical", "forecasted", "statistical", "parameterized"]
    time_series_model: Optional[Literal["normal", "garch"]] = "normal"
    distribution: Optional[Literal["normal", "fat_tailed"]] = "normal"
    degrees_of_freedom: Optional[float] = None
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None
    initial_amount: float
    simulation_period_years: int
    n_paths: int
    seed: int

    @model_validator(mode="after")
    def weights_sum_to_one(self):
        if abs(sum(self.weights) - 1.0) > 1e-6:
            raise ValueError("weights must sum to 1.0")
        if len(self.tickers) != len(self.weights):
            raise ValueError("tickers and weights must be the same length")
        return self


class PercentileTable(BaseModel):
    ending_balance: dict[str, float]
    cagr: dict[str, float]


class VarEs(BaseModel):
    var: float
    es: float


class FanChart(BaseModel):
    years: list[int]
    p10: list[float]
    p25: list[float]
    p50: list[float]
    p75: list[float]
    p90: list[float]


class SimulateResponse(BaseModel):
    percentile_table: PercentileTable
    var_es: VarEs
    ending_balances: list[float]
    fan_chart: FanChart
```

- [ ] **Step 4: Write `backend/app/api/simulate.py`**

```python
from fastapi import APIRouter
from backend.app.api.schemas import SimulateRequest, SimulateResponse
from backend.app.data.price_client import get_prices
from backend.app.engine.orchestrator import run_simulation

router = APIRouter()


@router.post("/api/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest) -> SimulateResponse:
    price_panel = get_prices(request.tickers, start=request.start_date, end=request.end_date)
    wide_panel = price_panel.pivot(index="date", columns="ticker", values="close").ffill().dropna()

    orchestrator_request = {
        "weights": dict(zip(request.tickers, request.weights)),
        "price_panel": wide_panel,
        "simulation_model": request.simulation_model,
        "time_series_model": request.time_series_model,
        "distribution": request.distribution,
        "degrees_of_freedom": request.degrees_of_freedom,
        "expected_return": request.expected_return,
        "expected_volatility": request.expected_volatility,
        "initial_amount": request.initial_amount,
        "simulation_period_years": request.simulation_period_years,
        "n_paths": request.n_paths,
        "seed": request.seed,
    }
    result = run_simulation(orchestrator_request)
    return SimulateResponse(**result)
```

- [ ] **Step 5: Write `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.simulate import router as simulate_router

app = FastAPI(title="Monte Carlo Portfolio Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulate_router)
```

- [ ] **Step 6: Run the API tests to verify they pass**

```bash
pytest backend/tests/api/test_simulate.py -v
```

Expected: both tests PASS. (The 200 test makes a real `yfinance` network call — if it fails due to network access, note that in the task result and move on; Task 5 adds caching to remove this dependency.)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add FastAPI /api/simulate endpoint"
```

---

## Task 5: Price caching layer (remove live-network dependency from every request)

**Files:**
- Create: `backend/app/data/cache.py`
- Modify: `backend/app/api/simulate.py`
- Create: `backend/tests/data/test_cache.py`

**Interfaces:**
- Consumes: `backend.app.data.price_client.get_prices` (Task 3)
- Produces: `backend.app.data.cache.get_cached_prices(tickers: list[str], start: str, end: str, cache_dir: Path = Path("data/processed")) -> pd.DataFrame` — same return shape as `get_prices` (long format: `date, ticker, close`), but reads from `data/processed/prices_cache.parquet` first and only calls `get_prices` for tickers/date-ranges not already cached, then persists the merged result back.

- [ ] **Step 1: Write the failing cache test**

`backend/tests/data/test_cache.py`:
```python
import pandas as pd
from pathlib import Path
from backend.app.data.cache import get_cached_prices


def test_get_cached_prices_writes_and_reuses_cache(tmp_path, monkeypatch):
    calls = []

    def fake_get_prices(symbols, start, end):
        calls.append(symbols)
        dates = pd.date_range(start, end, freq="B")
        rows = [{"date": d, "ticker": t, "close": 100.0} for t in symbols for d in dates]
        return pd.DataFrame(rows)

    monkeypatch.setattr("backend.app.data.cache.get_prices", fake_get_prices)

    df1 = get_cached_prices(["SPY"], "2020-01-01", "2020-01-10", cache_dir=tmp_path)
    assert len(calls) == 1
    assert not df1.empty

    df2 = get_cached_prices(["SPY"], "2020-01-01", "2020-01-10", cache_dir=tmp_path)
    assert len(calls) == 1  # second call served entirely from cache, no new fetch
    pd.testing.assert_frame_equal(df1.reset_index(drop=True), df2.reset_index(drop=True))
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest backend/tests/data/test_cache.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.data.cache'`.

- [ ] **Step 3: Write `backend/app/data/cache.py`**

```python
from pathlib import Path
import pandas as pd
from backend.app.data.price_client import get_prices

_CACHE_FILE = "prices_cache.parquet"


def get_cached_prices(tickers: list[str], start: str, end: str, cache_dir: Path = Path("data/processed")) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / _CACHE_FILE

    if cache_path.exists():
        cached = pd.read_parquet(cache_path)
    else:
        cached = pd.DataFrame(columns=["date", "ticker", "close"])

    cached["date"] = pd.to_datetime(cached["date"]) if not cached.empty else cached["date"]
    requested_range = pd.date_range(start, end, freq="B")

    missing_tickers = [t for t in tickers if t not in cached["ticker"].unique()]
    if not cached.empty:
        have_range = cached.groupby("ticker")["date"].agg(["min", "max"])
        for t in tickers:
            if t in have_range.index:
                covers = (have_range.loc[t, "min"] <= requested_range.min()) and (
                    have_range.loc[t, "max"] >= requested_range.max()
                )
                if not covers and t not in missing_tickers:
                    missing_tickers.append(t)

    if missing_tickers:
        fresh = get_prices(missing_tickers, start=start, end=end)
        fresh["date"] = pd.to_datetime(fresh["date"])
        cached = pd.concat([cached, fresh], ignore_index=True)
        cached = cached.drop_duplicates(subset=["date", "ticker"], keep="last")
        cached.to_parquet(cache_path, index=False)

    result = cached[
        cached["ticker"].isin(tickers)
        & (cached["date"] >= pd.Timestamp(start))
        & (cached["date"] <= pd.Timestamp(end))
    ]
    return result.sort_values(["ticker", "date"]).reset_index(drop=True)
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
pytest backend/tests/data/test_cache.py -v
```

Expected: PASS.

- [ ] **Step 5: Wire the cache into the API route**

In `backend/app/api/simulate.py`, change:
```python
from backend.app.data.price_client import get_prices
```
to:
```python
from backend.app.data.cache import get_cached_prices
```
and change the call inside `simulate()`:
```python
price_panel = get_prices(request.tickers, start=request.start_date, end=request.end_date)
```
to:
```python
price_panel = get_cached_prices(request.tickers, start=request.start_date, end=request.end_date)
```

- [ ] **Step 6: Re-run the API tests**

```bash
pytest backend/tests/api backend/tests/data -v
```

Expected: all PASS (first run may hit the network once per new ticker/date-range; subsequent test runs reuse `data/processed/prices_cache.parquet`).

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: add price cache so repeated simulate requests don't re-fetch yfinance"
```

---

## Task 6: `.env.example`, dev scripts, and root README pointer

**Files:**
- Modify: `.env.example`
- Create: `Makefile`
- Modify: `README.md` (create if it doesn't exist yet)

**Interfaces:**
- Consumes: nothing new
- Produces: `make backend-dev`, `make backend-test` — the commands every later frontend task assumes are available to start/verify the backend.

- [ ] **Step 1: Check whether `README.md` already exists**

```bash
ls README.md 2>&1
```

- [ ] **Step 2: Update `.env.example`**

```
SEC_OPENDATA_API_KEY=your_sec_opendata_key_here
```

(Webull App Key/Secret entries are removed — `price_client.py` uses yfinance only, per Task 3 Step 3 and spec section 3.)

- [ ] **Step 3: Write `Makefile`**

```makefile
.PHONY: backend-dev backend-test frontend-dev frontend-test

backend-dev:
	uvicorn backend.app.main:app --reload

backend-test:
	pytest backend/tests -v

frontend-dev:
	npm --prefix frontend run dev

frontend-test:
	npx --prefix frontend tsc -b
```

- [ ] **Step 4: Write or extend `README.md`** with at minimum:

```markdown
# Monte Carlo Portfolio Simulator

Public web app: build your own portfolio, pick an objective, run a real Monte Carlo simulation.

See `docs/superpowers/specs/2026-07-29-monte-carlo-webapp-design.md` for the full design.

## Setup

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    cp .env.example .env   # fill in SEC_OPENDATA_API_KEY if you need live Thai fund data

## Run

    make backend-dev    # http://localhost:8000
    make frontend-dev   # http://localhost:5173 (after Task 7+)

## Test

    make backend-test
    make frontend-test
```

- [ ] **Step 5: Verify the Makefile targets work**

```bash
make backend-test
```

Expected: PASS (same result as `pytest backend/tests -v`).

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "docs: add README, Makefile dev scripts, update .env.example for yfinance-only data source"
```

---

## Task 7: Frontend scaffold + design tokens

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`

**Interfaces:**
- Produces: `frontend/src/api/client.ts` exports `simulate(request: SimulateRequest): Promise<SimulateResponse>` — the only function later components call to talk to the backend.
- Produces: `frontend/src/api/types.ts` exports the `SimulateRequest` / `SimulateResponse` TypeScript interfaces, mirroring `backend/app/api/schemas.py` field-for-field (Task 4).

- [ ] **Step 1: Scaffold the Vite React-TS project**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
```

- [ ] **Step 2: Write `frontend/src/api/types.ts`**

```typescript
export interface SimulateRequest {
  tickers: string[];
  weights: number[];
  start_date: string;
  end_date: string;
  simulation_model: "historical" | "forecasted" | "statistical" | "parameterized";
  time_series_model?: "normal" | "garch";
  distribution?: "normal" | "fat_tailed";
  degrees_of_freedom?: number;
  expected_return?: number;
  expected_volatility?: number;
  initial_amount: number;
  simulation_period_years: number;
  n_paths: number;
  seed: number;
}

export interface PercentileTable {
  ending_balance: Record<string, number>;
  cagr: Record<string, number>;
}

export interface FanChart {
  years: number[];
  p10: number[];
  p25: number[];
  p50: number[];
  p75: number[];
  p90: number[];
}

export interface SimulateResponse {
  percentile_table: PercentileTable;
  var_es: { var: number; es: number };
  ending_balances: number[];
  fan_chart: FanChart;
}
```

- [ ] **Step 3: Write `frontend/src/api/client.ts`**

```typescript
import type { SimulateRequest, SimulateResponse } from "./types";

const BASE_URL = "http://localhost:8000";

export async function simulate(request: SimulateRequest): Promise<SimulateResponse> {
  const resp = await fetch(`${BASE_URL}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(`simulate failed: ${resp.status} ${JSON.stringify(body)}`);
  }
  return resp.json();
}
```

- [ ] **Step 4: Write `frontend/src/styles.css`** (design tokens copied from the sibling Portfolio-Backtester repo, per the design spec's visual-language section)

```css
:root {
  --gray-25: #fcfcfd;
  --gray-50: #f8f9fb;
  --gray-100: #f1f2f5;
  --gray-200: #e4e7ec;
  --gray-300: #d0d5dd;
  --gray-400: #9aa1ac;
  --gray-500: #6b7280;
  --gray-600: #4b5259;
  --gray-700: #34383e;
  --gray-900: #14151a;

  --accent: #5b21d6;
  --accent-hover: #4c1bb3;
  --accent-active: #401793;
  --accent-soft: #f3effc;
  --accent-soft-border: #ddd0f7;

  --success: #0f7a4f;
  --success-soft: #e7f6ee;
  --success-soft-border: #bfe6d1;

  --warn: #92620a;
  --warn-soft: #fff6e0;
  --warn-soft-border: #f3dfa0;

  --danger: #b42318;
  --danger-soft: #fdeeec;
  --danger-soft-border: #f3c6bf;

  --bg: var(--gray-50);
  --surface: #ffffff;
  --surface-2: var(--gray-50);
  --border: var(--gray-200);
  --border-strong: var(--gray-300);
  --text-primary: var(--gray-900);
  --text-secondary: var(--gray-500);
  --text-tertiary: var(--gray-400);

  --shadow-xs: 0 1px 2px rgba(16, 24, 40, 0.05);
  --shadow-sm: 0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 6px rgba(16, 24, 40, 0.04);
  --shadow-md: 0 6px 16px rgba(16, 24, 40, 0.08), 0 1px 2px rgba(16, 24, 40, 0.04);

  --r-sm: 6px;
  --r-md: 10px;
  --r-lg: 14px;
  --r-pill: 999px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text-primary);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
```

- [ ] **Step 5: Write a minimal `frontend/src/App.tsx`** that proves the API wiring works end-to-end:

```tsx
import { useState } from "react";
import { simulate } from "./api/client";
import type { SimulateResponse } from "./api/types";
import "./styles.css";

export default function App() {
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function runDemo() {
    setError(null);
    try {
      const res = await simulate({
        tickers: ["SPY", "QQQ"],
        weights: [0.6, 0.4],
        start_date: "2020-01-01",
        end_date: "2025-12-31",
        simulation_model: "statistical",
        time_series_model: "normal",
        initial_amount: 1000000,
        simulation_period_years: 10,
        n_paths: 500,
        seed: 42,
      });
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>Monte Carlo Portfolio Simulator</h1>
      <button onClick={runDemo}>Run demo simulation</button>
      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      {result && (
        <pre>{JSON.stringify(result.percentile_table, null, 2)}</pre>
      )}
    </div>
  );
}
```

- [ ] **Step 6: Verify the full stack end-to-end**

```bash
make backend-dev &
cd frontend && npm run dev
```

Open the Vite dev URL, click "Run demo simulation", confirm a percentile table JSON renders with no console errors. Stop both servers.

- [ ] **Step 7: Type-check the frontend**

```bash
npx --prefix frontend tsc -b
```

Expected: no type errors.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: scaffold React+TS frontend with API client and design tokens"
```

---

## Task 8: Portfolio Builder screen

**Files:**
- Create: `frontend/src/components/PortfolioBuilder.tsx`
- Create: `frontend/src/components/PortfolioBuilder.test.tsx`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/vitest.config.ts`
- Modify: `frontend/package.json` (add `vitest`, `@testing-library/react`, `@testing-library/jest-dom`)

**Interfaces:**
- Consumes: nothing external
- Produces: `PortfolioBuilder` component with props `{ onChange: (holdings: { ticker: string; weight: number }[]) => void }` — Task 9's Objective Picker screen reads its output via this callback.

- [ ] **Step 1: Add test dependencies**

```bash
npm --prefix frontend install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

- [ ] **Step 2: Write `frontend/vitest.config.ts`**

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: { environment: "jsdom", globals: true },
});
```

- [ ] **Step 3: Write the failing component test**

`frontend/src/components/PortfolioBuilder.test.tsx`:
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import PortfolioBuilder from "./PortfolioBuilder";

describe("PortfolioBuilder", () => {
  it("starts with one empty row and calls onChange as fields are filled", () => {
    const onChange = vi.fn();
    render(<PortfolioBuilder onChange={onChange} />);
    const tickerInput = screen.getAllByLabelText("Ticker")[0];
    const weightInput = screen.getAllByLabelText("Weight %")[0];

    fireEvent.change(tickerInput, { target: { value: "SPY" } });
    fireEvent.change(weightInput, { target: { value: "100" } });

    expect(onChange).toHaveBeenLastCalledWith([{ ticker: "SPY", weight: 1.0 }]);
  });

  it("shows a validation warning when weights do not sum to 100%", () => {
    const onChange = vi.fn();
    render(<PortfolioBuilder onChange={onChange} />);
    fireEvent.change(screen.getAllByLabelText("Ticker")[0], { target: { value: "SPY" } });
    fireEvent.change(screen.getAllByLabelText("Weight %")[0], { target: { value: "50" } });

    expect(screen.getByText(/weights must sum to 100%/i)).toBeInTheDocument();
  });

  it("adds a new row when Add Asset is clicked", () => {
    const onChange = vi.fn();
    render(<PortfolioBuilder onChange={onChange} />);
    fireEvent.click(screen.getByText("Add Asset"));
    expect(screen.getAllByLabelText("Ticker")).toHaveLength(2);
  });
});
```

- [ ] **Step 4: Add the test script to `frontend/package.json`**

Add under `"scripts"`: `"test": "vitest run"`.

- [ ] **Step 5: Run it to verify it fails**

```bash
npm --prefix frontend test
```

Expected: FAIL — `PortfolioBuilder` module doesn't exist.

- [ ] **Step 6: Write `frontend/src/components/PortfolioBuilder.tsx`**

```tsx
import { useState, useEffect } from "react";

interface Holding {
  ticker: string;
  weightPct: string;
}

interface Props {
  onChange: (holdings: { ticker: string; weight: number }[]) => void;
}

export default function PortfolioBuilder({ onChange }: Props) {
  const [rows, setRows] = useState<Holding[]>([{ ticker: "", weightPct: "" }]);

  const totalPct = rows.reduce((sum, r) => sum + (parseFloat(r.weightPct) || 0), 0);
  const isValid = rows.every((r) => r.ticker.trim() !== "") && Math.abs(totalPct - 100) < 1e-6;

  useEffect(() => {
    if (isValid) {
      onChange(rows.map((r) => ({ ticker: r.ticker.trim(), weight: parseFloat(r.weightPct) / 100 })));
    }
  }, [rows]);

  function updateRow(index: number, field: keyof Holding, value: string) {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, [field]: value } : r)));
  }

  function addRow() {
    setRows((prev) => [...prev, { ticker: "", weightPct: "" }]);
  }

  function removeRow(index: number) {
    setRows((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <div>
      {rows.map((row, i) => (
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <label>
            Ticker
            <input
              aria-label="Ticker"
              value={row.ticker}
              onChange={(e) => updateRow(i, "ticker", e.target.value.toUpperCase())}
            />
          </label>
          <label>
            Weight %
            <input
              aria-label="Weight %"
              type="number"
              value={row.weightPct}
              onChange={(e) => updateRow(i, "weightPct", e.target.value)}
            />
          </label>
          {rows.length > 1 && (
            <button type="button" onClick={() => removeRow(i)}>Remove</button>
          )}
        </div>
      ))}
      <button type="button" onClick={addRow}>Add Asset</button>
      {!isValid && rows.some((r) => r.weightPct !== "") && (
        <p style={{ color: "var(--danger)" }}>Weights must sum to 100% (currently {totalPct}%).</p>
      )}
    </div>
  );
}
```

- [ ] **Step 7: Run the tests again to verify they pass**

```bash
npm --prefix frontend test
```

Expected: all 3 tests PASS.

- [ ] **Step 8: Wire `PortfolioBuilder` into `App.tsx`**, replacing the hardcoded `tickers`/`weights` in the demo `runDemo` call with state from `PortfolioBuilder`'s `onChange`. Keep everything else in `App.tsx` from Task 7 working (the button still runs `simulate`).

- [ ] **Step 9: Type-check and commit**

```bash
npx --prefix frontend tsc -b
git add -A
git commit -m "feat: add PortfolioBuilder component with weight validation"
```

---

## Task 9: Objective Picker + Assumptions form

**Files:**
- Create: `frontend/src/objectives/presets.ts`
- Create: `frontend/src/components/ObjectivePicker.tsx`
- Create: `frontend/src/components/ObjectivePicker.test.tsx`
- Create: `frontend/src/components/AssumptionsForm.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `Holding[]` from `PortfolioBuilder` (Task 8)
- Produces: `frontend/src/objectives/presets.ts` exports `OBJECTIVES: ObjectivePreset[]` where
  ```typescript
  interface ObjectivePreset {
    id: "growth" | "withdrawal" | "goal" | "risk";
    label: string;
    question: string;
    defaults: Partial<SimulateRequest>;
  }
  ```
- Produces: `ObjectivePicker` component with props `{ onSelect: (objective: ObjectivePreset) => void }`.
- Produces: `AssumptionsForm` component with props `{ initial: Partial<SimulateRequest>; onSubmit: (request: Omit<SimulateRequest, "tickers" | "weights">) => void }`.

- [ ] **Step 1: Write `frontend/src/objectives/presets.ts`** (the 4 v1 objectives, per spec section 2's table)

```typescript
import type { SimulateRequest } from "../api/types";

export interface ObjectivePreset {
  id: "growth" | "withdrawal" | "goal" | "risk";
  label: string;
  question: string;
  defaults: Partial<SimulateRequest>;
}

export const OBJECTIVES: ObjectivePreset[] = [
  {
    id: "growth",
    label: "Growth Projection",
    question: "If I keep this portfolio, what could it be worth in N years?",
    defaults: {
      simulation_model: "statistical",
      time_series_model: "normal",
      simulation_period_years: 30,
      n_paths: 5000,
    },
  },
  {
    id: "withdrawal",
    label: "Retirement Withdrawal",
    question: "If I withdraw money regularly, will it last?",
    defaults: {
      simulation_model: "statistical",
      time_series_model: "normal",
      simulation_period_years: 30,
      n_paths: 5000,
    },
  },
  {
    id: "goal",
    label: "Goal Probability",
    question: "What's the probability I reach my target amount by a given year?",
    defaults: {
      simulation_model: "statistical",
      time_series_model: "normal",
      simulation_period_years: 20,
      n_paths: 5000,
    },
  },
  {
    id: "risk",
    label: "Risk / Tail-Risk Check",
    question: "How bad could the bad case be?",
    defaults: {
      simulation_model: "statistical",
      time_series_model: "normal",
      simulation_period_years: 10,
      n_paths: 5000,
    },
  },
];
```

Note: "Retirement Withdrawal" and "Goal Probability" auto-fill the shared simulation config only in v1 — the withdrawal-amount/target-amount cashflow injection into the orchestrator itself is out of scope for this plan (see spec section 2/8: cashflow modeling was part of the original notebook's Financial Goals tool, not yet ported). Document this as a known v1 limitation in Task 10's Results screen rather than silently faking it.

- [ ] **Step 2: Write the failing `ObjectivePicker` test**

`frontend/src/components/ObjectivePicker.test.tsx`:
```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ObjectivePicker from "./ObjectivePicker";

describe("ObjectivePicker", () => {
  it("renders all 4 objective cards and calls onSelect with the clicked one", () => {
    const onSelect = vi.fn();
    render(<ObjectivePicker onSelect={onSelect} />);

    expect(screen.getByText("Growth Projection")).toBeInTheDocument();
    expect(screen.getByText("Retirement Withdrawal")).toBeInTheDocument();
    expect(screen.getByText("Goal Probability")).toBeInTheDocument();
    expect(screen.getByText("Risk / Tail-Risk Check")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Growth Projection"));
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: "growth" }));
  });
});
```

- [ ] **Step 3: Run it to verify it fails**

```bash
npm --prefix frontend test -- ObjectivePicker
```

Expected: FAIL — module doesn't exist.

- [ ] **Step 4: Write `frontend/src/components/ObjectivePicker.tsx`**

```tsx
import { OBJECTIVES, type ObjectivePreset } from "../objectives/presets";

interface Props {
  onSelect: (objective: ObjectivePreset) => void;
}

export default function ObjectivePicker({ onSelect }: Props) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
      {OBJECTIVES.map((obj) => (
        <button
          key={obj.id}
          onClick={() => onSelect(obj)}
          style={{
            textAlign: "left",
            padding: 16,
            borderRadius: "var(--r-md)",
            border: "1px solid var(--border)",
            background: "var(--surface)",
            cursor: "pointer",
          }}
        >
          <strong>{obj.label}</strong>
          <p style={{ color: "var(--text-secondary)", margin: "8px 0 0" }}>{obj.question}</p>
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: Run the test again to verify it passes**

```bash
npm --prefix frontend test -- ObjectivePicker
```

Expected: PASS.

- [ ] **Step 6: Write `frontend/src/components/AssumptionsForm.tsx`** — a plain controlled form (no test required here; it's a straightforward form binding, covered end-to-end by Task 10's integration check) that renders every field from `SimulateRequest` except `tickers`/`weights`, pre-filled from `initial`, with `simulation_model`, `time_series_model`, and `distribution` as `<select>` dropdowns and the rest as number/date inputs, calling `onSubmit` with the full assembled object on a "Review" button click.

- [ ] **Step 7: Wire both components into `App.tsx`**: render `PortfolioBuilder` → once valid, render `ObjectivePicker` → once an objective is selected, render `AssumptionsForm` pre-filled with `objective.defaults` → on submit, call `simulate()` with tickers/weights from `PortfolioBuilder` merged with the assumptions form's output.

- [ ] **Step 8: Type-check and commit**

```bash
npx --prefix frontend tsc -b
git add -A
git commit -m "feat: add ObjectivePicker and AssumptionsForm, wire into App flow"
```

---

## Task 10: Results screen (fan chart, distribution, risk table)

**Files:**
- Create: `frontend/src/components/FanChart.tsx`
- Create: `frontend/src/components/FanChart.test.tsx`
- Create: `frontend/src/components/ResultsView.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `SimulateResponse` (Task 4/7)
- Produces: `FanChart` component with props `{ data: SimulateResponse["fan_chart"] }` rendering an inline SVG.
- Produces: `ResultsView` component with props `{ result: SimulateResponse; objectiveId: ObjectivePreset["id"] }`.

- [ ] **Step 1: Write the failing `FanChart` test**

`frontend/src/components/FanChart.test.tsx`:
```tsx
import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import FanChart from "./FanChart";

describe("FanChart", () => {
  it("renders one polyline per percentile band", () => {
    const data = {
      years: [0, 1, 2],
      p10: [1000000, 1050000, 1100000],
      p25: [1000000, 1080000, 1150000],
      p50: [1000000, 1100000, 1200000],
      p75: [1000000, 1150000, 1300000],
      p90: [1000000, 1200000, 1400000],
    };
    const { container } = render(<FanChart data={data} />);
    expect(container.querySelectorAll("polyline")).toHaveLength(5);
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
npm --prefix frontend test -- FanChart
```

Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write `frontend/src/components/FanChart.tsx`**

```tsx
import type { FanChart as FanChartData } from "../api/types";

interface Props {
  data: FanChartData;
}

const WIDTH = 600;
const HEIGHT = 300;
const BANDS: (keyof FanChartData)[] = ["p10", "p25", "p50", "p75", "p90"];
const COLORS: Record<string, string> = {
  p10: "var(--gray-400)",
  p25: "var(--gray-500)",
  p50: "var(--accent)",
  p75: "var(--gray-500)",
  p90: "var(--gray-400)",
};

export default function FanChart({ data }: Props) {
  const allValues = BANDS.flatMap((b) => data[b] as number[]);
  const minV = Math.min(...allValues);
  const maxV = Math.max(...allValues);
  const n = data.years.length;

  function toPoints(series: number[]): string {
    return series
      .map((v, i) => {
        const x = (i / (n - 1)) * WIDTH;
        const y = HEIGHT - ((v - minV) / (maxV - minV)) * HEIGHT;
        return `${x},${y}`;
      })
      .join(" ");
  }

  return (
    <svg width={WIDTH} height={HEIGHT} role="img" aria-label="Portfolio percentile fan chart">
      {BANDS.map((band) => (
        <polyline
          key={band}
          points={toPoints(data[band] as number[])}
          fill="none"
          stroke={COLORS[band]}
          strokeWidth={band === "p50" ? 2 : 1}
        />
      ))}
    </svg>
  );
}
```

- [ ] **Step 4: Run the test again to verify it passes**

```bash
npm --prefix frontend test -- FanChart
```

Expected: PASS.

- [ ] **Step 5: Write `frontend/src/components/ResultsView.tsx`**

```tsx
import type { SimulateResponse } from "../api/types";
import type { ObjectivePreset } from "../objectives/presets";
import FanChart from "./FanChart";

interface Props {
  result: SimulateResponse;
  objectiveId: ObjectivePreset["id"];
}

const OBJECTIVE_SUMMARY_LABEL: Record<ObjectivePreset["id"], string> = {
  growth: "Projected ending balance (median case)",
  withdrawal: "Median ending balance under this simulation config",
  goal: "Median ending balance vs. your target",
  risk: "Value at Risk / Expected Shortfall (90% confidence)",
};

export default function ResultsView({ result, objectiveId }: Props) {
  return (
    <div>
      <h2>{OBJECTIVE_SUMMARY_LABEL[objectiveId]}</h2>
      {(objectiveId === "withdrawal" || objectiveId === "goal") && (
        <p style={{ color: "var(--warn)" }}>
          Note: cashflow (withdrawal amount / goal target) modeling is not yet wired into the
          simulation engine in this version — results below reflect the portfolio's growth
          simulation only, without a withdrawal or goal-target overlay. This is a known v1
          limitation.
        </p>
      )}
      <FanChart data={result.fan_chart} />
      <table>
        <thead>
          <tr><th>Percentile</th><th>Ending Balance</th><th>CAGR</th></tr>
        </thead>
        <tbody>
          {Object.keys(result.percentile_table.ending_balance).map((p) => (
            <tr key={p}>
              <td>{p}th</td>
              <td>{result.percentile_table.ending_balance[p].toLocaleString()}</td>
              <td>{(result.percentile_table.cagr[p] * 100).toFixed(2)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>VaR (90%): {result.var_es.var.toLocaleString()} — ES: {result.var_es.es.toLocaleString()}</p>
    </div>
  );
}
```

- [ ] **Step 6: Wire `ResultsView` into `App.tsx`**, replacing the raw `<pre>` JSON dump from Task 7 with `<ResultsView result={result} objectiveId={selectedObjective.id} />`.

- [ ] **Step 7: Manual end-to-end check**

```bash
make backend-dev &
cd frontend && npm run dev
```

Open the app: build a 2-asset portfolio, pick "Growth Projection", submit assumptions, confirm the fan chart and percentile table render with real numbers. Try "Retirement Withdrawal" and confirm the v1-limitation warning banner shows.

- [ ] **Step 8: Type-check, run full test suite, and commit**

```bash
npx --prefix frontend tsc -b
npm --prefix frontend test
pytest backend/tests -v
git add -A
git commit -m "feat: add FanChart and ResultsView, complete v1 end-to-end flow for all 4 objectives"
```

---

## Task 11: Update `tests/` directory cleanup and root project docs

**Files:**
- Modify: `README.md`
- Delete: `tests/` directory (should now be empty except `__pycache__`, already gitignored)
- Modify: `docs/superpowers/specs/2026-07-29-monte-carlo-webapp-design.md` (mark section 3's promotion table as completed)

**Interfaces:**
- Consumes: nothing new — this is a documentation/cleanup task confirming the promotion from Tasks 1–3 is complete.

- [ ] **Step 1: Confirm `tests/` only contains promoted/deleted files, nothing left behind**

```bash
find tests -type f
```

Expected: no output (directory empty or gone) — everything was moved to `backend/tests/` or explicitly deleted in Tasks 1–3.

- [ ] **Step 2: Remove the now-empty `tests/` directory**

```bash
rmdir tests 2>/dev/null || true
```

- [ ] **Step 3: Add a completion note to the design spec's promotion table**

In `docs/superpowers/specs/2026-07-29-monte-carlo-webapp-design.md` section 3, after the promotion table, add:

```markdown
**Status: promotion complete** (see `docs/superpowers/plans/2026-07-29-monte-carlo-webapp.md` Tasks 1–3) — all engine/data modules now live under `backend/app/`, with matching tests under `backend/tests/`.
```

- [ ] **Step 4: Final full-stack verification**

```bash
pytest backend/tests -v
npx --prefix frontend tsc -b
npm --prefix frontend test
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove empty tests/ directory, mark engine promotion complete in design spec"
```
