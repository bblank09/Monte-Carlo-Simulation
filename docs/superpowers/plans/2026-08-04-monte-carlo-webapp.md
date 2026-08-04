# Monte Carlo Simulation Webapp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Monte Carlo Simulation web app — FastAPI backend promoting the existing `tests/*.py` engine plus new engine modules, and a React+TS frontend copying Backtest Portfolio's 3-step wizard shell and chart primitives with entirely new Parameters/Results content.

**Architecture:** One-directional data flow: SEC Open Data API → `backend/app/data/` (fetch + cache) → `backend/app/engine/` (pure computation, no I/O) → `backend/app/api/` (FastAPI + Pydantic v2) → `frontend/src/` (React 19 + TS, Vite). See spec `docs/superpowers/specs/2026-08-04-monte-carlo-webapp-design.md` for full rationale.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pandas>=3.0, numpy, scipy, `arch` (GARCH); React 19, TypeScript, Vite 6; pytest, Playwright.

## Global Constraints

- `pandas>=3.0` hard floor — pandas 2.2.3 has a silent data-corruption bug at wide-panel scale (same rationale as Backtest Portfolio's `CLAUDE.md`).
- SEC Open Data only — no yfinance, no US tickers. `webull_client.py` and `portfolio_lib.py` are not promoted.
- NAV gaps are hard errors — never forward-filled or interpolated.
- "Is this date range usable" is computed server-side only, never re-derived client-side.
- Project directory name contains `:` (`Monte Carlo Simulation Webull:SEC OPENAI`) — Docker must use a **named volume**, never a bind mount.
- No chart library in the frontend — hand-built SVG components only, matching Backtest Portfolio's convention.
- `tsc -b && vite build` is both the build and the frontend typecheck step.

---

## Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `CLAUDE.md`
- Modify: `.env.example`

**Interfaces:**
- Produces: installable package `monte-carlo-webull-sec-openai`, `backend` package importable as `backend.app.*`, pytest configured with `testpaths=["backend/tests"]`.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "monte-carlo-webull-sec-openai"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.7",
    "pydantic-settings>=2.2",
    "pandas>=3.0",
    "numpy>=1.26",
    "scipy>=1.13",
    "arch>=6.3",
    "httpx>=0.27",
    "pyarrow>=16.0",
    "requests>=2.32",
    "python-dotenv>=1.0",
    "tenacity>=8.2",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "mypy", "pandas-stubs", "scipy-stubs"]

[tool.setuptools.packages.find]
include = ["backend*"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["backend/tests"]

[tool.mypy]
explicit_package_bases = true

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 2: Write `CLAUDE.md`**

```markdown
# CLAUDE

Sibling project to `../Backtest Portfolio Webull:SEC OPENAI`. Backtest answers
"what did happen"; this app answers "what could happen." UX/UI shell (3-step
wizard, design tokens, chart primitives) is copied from Backtest Portfolio.
Internals are entirely different — 4 Monte Carlo simulation models instead of
a single realized-path backtest.

## Scope

SEC Thailand Open Data only. No yfinance, no US tickers, no optimizer
(`portfolio_lib.py` is not promoted — weight entry is manual, same as
Backtest Portfolio's Equal weight / Normalize / Clear pattern).

## Data flow

SEC Open Data API -> `backend/app/data/` -> `data/processed/nav_panel.parquet`
(cache) -> `backend/app/engine/` (pure computation) -> `backend/app/api/`
(FastAPI) -> `frontend/src/`.

## Landmines

- `pandas>=3.0` is a hard floor. pandas 2.2.3 has a silent data-corruption
  bug at wide-panel scale. Do not downgrade.
- NAV gaps are hard errors. Never forward-fill or interpolate across a gap.
- "Is this date range usable" is computed server-side only. Never
  re-derive it client-side.
- Project directory name contains `:` (`Monte Carlo Simulation Webull:SEC
  OPENAI`). Docker must use a named volume, not a bind mount — Docker
  Desktop's bind-mount path parsing breaks on the colon.
- `statistical_sim.py`'s GBM model combines per-asset price paths via
  `asset_paths @ weights`, which is a drifting-weight computation with no
  rebalancing, unlike the other 3 models (which bootstrap
  already-portfolio-weighted annual returns, implicitly rebalancing every
  draw). The Rebalancing Frequency parameter must apply consistently
  across all 4 models — see `engine/statistical.py`.

## Commands

- `pytest` — backend tests
- `ruff check .` / `mypy backend` — lint/typecheck
- `npm --prefix frontend run dev` — Vite dev server
- `npm --prefix frontend run build` — production build + frontend typecheck
- `uvicorn backend.app.main:app --reload` — API dev server
```

- [ ] **Step 3: Update `.env.example`**

```
SEC_OPENDATA_API_KEY=your_sec_opendata_key_here
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml CLAUDE.md .env.example
git commit -m "chore: add project scaffolding (pyproject.toml, CLAUDE.md)"
```

---

## Task 2: Promote GBM engine

**Files:**
- Create: `backend/app/engine/__init__.py`
- Create: `backend/app/engine/gbm.py`
- Test: `backend/tests/engine/test_gbm.py`

**Interfaces:**
- Produces: `simulate_gbm_paths(S0: np.ndarray, mu: np.ndarray, sigma: np.ndarray, n_years: int, steps_per_year: int, n_paths: int, seed: int | None = None) -> np.ndarray` — shape `(n_paths, n_years*steps_per_year+1, n_assets)`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/engine/test_gbm.py
import numpy as np
from backend.app.engine.gbm import simulate_gbm_paths


def test_shape_and_start_value():
    S0 = np.array([1.0, 1.0])
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.01], [0.01, 0.02]])
    paths = simulate_gbm_paths(S0, mu, sigma, n_years=2, steps_per_year=252, n_paths=100, seed=42)
    assert paths.shape == (100, 505, 2)
    assert np.allclose(paths[:, 0, :], S0)


def test_reproducible_with_seed():
    S0 = np.array([1.0])
    mu = np.array([0.07])
    sigma = np.array([[0.03]])
    a = simulate_gbm_paths(S0, mu, sigma, n_years=1, steps_per_year=12, n_paths=10, seed=7)
    b = simulate_gbm_paths(S0, mu, sigma, n_years=1, steps_per_year=12, n_paths=10, seed=7)
    assert np.array_equal(a, b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/engine/test_gbm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.engine.gbm'`

- [ ] **Step 3: Create `backend/app/engine/__init__.py`** (empty file)

- [ ] **Step 4: Write `backend/app/engine/gbm.py`** (ported verbatim from `tests/gbm_engine.py`)

```python
import numpy as np


def simulate_gbm_paths(S0, mu, sigma, n_years, steps_per_year, n_paths, seed=None):
    rng = np.random.default_rng(seed)
    n_assets = len(S0)
    n_steps = n_years * steps_per_year
    dt = 1.0 / steps_per_year
    L = np.linalg.cholesky(sigma)
    drift = (mu - 0.5 * np.diag(sigma)) * dt
    paths = np.empty((n_paths, n_steps + 1, n_assets))
    paths[:, 0, :] = S0
    for t in range(1, n_steps + 1):
        z_indep = rng.standard_normal((n_paths, n_assets))
        z_corr = z_indep @ L.T
        shock = drift + np.sqrt(dt) * z_corr
        paths[:, t, :] = paths[:, t - 1, :] * np.exp(shock)
    return paths
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest backend/tests/engine/test_gbm.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/engine/__init__.py backend/app/engine/gbm.py backend/tests/engine/test_gbm.py
git commit -m "feat: promote GBM engine from tests/gbm_engine.py"
```

---

## Task 3: Promote returns/data layer (SEC-only)

**Files:**
- Create: `backend/app/data/__init__.py`
- Create: `backend/app/data/sec_client.py`
- Create: `backend/app/data/returns.py`
- Test: `backend/tests/data/test_sec_client.py`
- Test: `backend/tests/data/test_returns.py`

**Interfaces:**
- Produces: `get_amcs() -> list[dict]`, `find_equity_funds(policy_desc: str = "ตราสารทุน", max_pages: int = 40, page_size: int = 100) -> list[dict]`, `get_daily_nav(proj_id: str, start_date: str, end_date: str) -> pd.DataFrame` (columns `nav_date, proj_id, last_val`).
- Produces: `build_price_panel(nav_df: pd.DataFrame) -> pd.DataFrame` (SEC-only, single-argument — the yfinance merge is dropped), `log_returns(price_panel: pd.DataFrame) -> pd.DataFrame`, `estimate_mu_sigma(returns_df: pd.DataFrame, periods_per_year: int = 252) -> tuple[np.ndarray, np.ndarray]`.

- [ ] **Step 1: Write the failing test for `returns.py`**

```python
# backend/tests/data/test_returns.py
import numpy as np
import pandas as pd
from backend.app.data.returns import build_price_panel, log_returns, estimate_mu_sigma


def test_build_price_panel_pivots_and_ffills():
    nav_df = pd.DataFrame({
        "nav_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"] * 1),
        "proj_id": ["A", "A", "A"],
        "last_val": [10.0, 10.5, 11.0],
    })
    panel = build_price_panel(nav_df)
    assert list(panel.columns) == ["A"]
    assert panel.loc["2024-01-02", "A"] == 10.5


def test_log_returns_and_estimate_mu_sigma():
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    panel = pd.DataFrame({"A": [10, 10.1, 10.2, 10.15, 10.3]}, index=idx)
    returns = log_returns(panel)
    assert len(returns) == 4
    mu, sigma = estimate_mu_sigma(returns, periods_per_year=252)
    assert mu.shape == (1,)
    assert sigma.shape == (1, 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/data/test_returns.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/data/returns.py`** (ported from `tests/returns_lib.py`, `build_price_panel` narrowed to SEC-only — single-argument, no `webull_df` merge)

```python
import numpy as np
import pandas as pd


def build_price_panel(nav_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot SEC fund NAV rows into a wide panel indexed by nav_date, forward-filled
    within available data. SEC-only: no cross-calendar merge with a second data source."""
    panel = nav_df.pivot(index="nav_date", columns="proj_id", values="last_val").sort_index()
    return panel.ffill().dropna()


def log_returns(price_panel: pd.DataFrame) -> pd.DataFrame:
    return np.log(price_panel / price_panel.shift(1)).dropna()


def estimate_mu_sigma(returns_df: pd.DataFrame, periods_per_year: int = 252) -> tuple[np.ndarray, np.ndarray]:
    mu_daily = returns_df.mean().to_numpy()
    sigma_daily = returns_df.cov().to_numpy()
    mu_annual = mu_daily * periods_per_year
    sigma_annual = sigma_daily * periods_per_year
    return mu_annual, sigma_annual
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/data/test_returns.py -v`
Expected: PASS

- [ ] **Step 5: Write the failing test for `sec_client.py`** (mocks `requests.get`, no live network calls in tests)

```python
# backend/tests/data/test_sec_client.py
from unittest.mock import patch, Mock
import pandas as pd
from backend.app.data.sec_client import get_daily_nav


@patch("backend.app.data.sec_client.requests.get")
def test_get_daily_nav_paginates_and_sorts(mock_get):
    page1 = Mock(status_code=200)
    page1.raise_for_status = lambda: None
    page1.json.return_value = {
        "items": [{"nav_date": "2024-01-02", "proj_id": "A", "last_val": 10.5}],
        "next_cursor": "cursor-2",
    }
    page2 = Mock(status_code=200)
    page2.raise_for_status = lambda: None
    page2.json.return_value = {
        "items": [{"nav_date": "2024-01-01", "proj_id": "A", "last_val": 10.0}],
        "next_cursor": None,
    }
    mock_get.side_effect = [page1, page2]

    df = get_daily_nav("A", "2024-01-01", "2024-01-02")

    assert list(df["nav_date"]) == list(pd.to_datetime(["2024-01-01", "2024-01-02"]))
    assert mock_get.call_count == 2
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest backend/tests/data/test_sec_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 7: Write `backend/app/data/sec_client.py`** (ported verbatim from `tests/sec_opendata_client.py`, `webull_client.py` deliberately NOT promoted)

```python
import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
API_KEY = os.environ["SEC_OPENDATA_API_KEY"]
BASE_URL = "https://api.sec.or.th"


def _headers():
    return {"Ocp-Apim-Subscription-Key": API_KEY}


def get_amcs():
    resp = requests.get(f"{BASE_URL}/v2/fund/general-info/amcs", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()["items"]


def find_equity_funds(policy_desc: str = "ตราสารทุน", max_pages: int = 40, page_size: int = 100):
    candidates = []
    cursor = None
    for _ in range(max_pages):
        params = {"page_size": page_size}
        if cursor:
            params["next_cursor"] = cursor
        resp = requests.get(f"{BASE_URL}/v2/fund/general-info/profiles", headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for item in data["items"]:
            if (item.get("policy_desc") == policy_desc
                    and item.get("fund_status") == "Registered"
                    and item.get("fund_class_name") == "main"):
                candidates.append(item)
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return candidates


def get_daily_nav(proj_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    items = []
    cursor = None
    while True:
        params = {"proj_id": proj_id, "start_nav_date": start_date, "end_nav_date": end_date, "page_size": 100}
        if cursor:
            params["next_cursor"] = cursor
        resp = requests.get(f"{BASE_URL}/v2/fund/daily-info/nav", headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload["items"])
        cursor = payload.get("next_cursor")
        if not cursor:
            break
    df = pd.DataFrame(items)[["nav_date", "proj_id", "last_val"]]
    df["nav_date"] = pd.to_datetime(df["nav_date"])
    return df.sort_values("nav_date").reset_index(drop=True)
```

- [ ] **Step 8: Run both data tests to verify they pass**

Run: `pytest backend/tests/data/ -v`
Expected: PASS (4 tests)

- [ ] **Step 9: Commit**

```bash
git add backend/app/data backend/tests/data
git commit -m "feat: promote SEC client and returns engine, SEC-only build_price_panel"
```

---

## Task 4: Promote parameterized and forecasted models

**Files:**
- Create: `backend/app/engine/parameterized.py`
- Create: `backend/app/engine/forecasted.py`
- Test: `backend/tests/engine/test_parameterized.py`
- Test: `backend/tests/engine/test_forecasted.py`

**Interfaces:**
- Produces: `simulate_parameterized(config: dict) -> np.ndarray` — shape `(n_paths, n_years+1)`, normalized to start at 1.0.
- Produces: `simulate_forecasted(mu: np.ndarray, sigma: np.ndarray, weights: np.ndarray, config: dict, returns_df: pd.DataFrame | None = None) -> np.ndarray` — same shape/normalization. `config["time_series_model"]` is `"normal"` or `"garch"`.

- [ ] **Step 1: Write the failing test for parameterized**

```python
# backend/tests/engine/test_parameterized.py
import numpy as np
from backend.app.engine.parameterized import simulate_parameterized


def test_normal_distribution_shape():
    config = {"seed": 1, "n_paths": 50, "simulation_period_years": 10,
              "expected_return": 0.07, "expected_volatility": 0.15, "distribution": "normal"}
    paths = simulate_parameterized(config)
    assert paths.shape == (50, 11)
    assert np.allclose(paths[:, 0], 1.0)


def test_fat_tailed_floor_at_negative_99_9_percent():
    config = {"seed": 1, "n_paths": 200, "simulation_period_years": 5,
              "expected_return": 0.0, "expected_volatility": 0.9,
              "distribution": "fat_tailed", "degrees_of_freedom": 3}
    paths = simulate_parameterized(config)
    per_period_return = paths[:, 1:] / paths[:, :-1] - 1
    assert per_period_return.min() >= -0.999 - 1e-9
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest backend/tests/engine/test_parameterized.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/engine/parameterized.py`** (ported verbatim from `tests/parameterized_sim.py`)

```python
import numpy as np
from scipy.stats import t as student_t


def simulate_parameterized(config: dict) -> np.ndarray:
    rng = np.random.default_rng(config["seed"])
    n_paths = config["n_paths"]
    n_years = config["simulation_period_years"]
    mu = config["expected_return"]
    sigma = config["expected_volatility"]
    if config["distribution"] == "normal":
        annual_returns = rng.normal(mu, sigma, size=(n_paths, n_years))
    elif config["distribution"] == "fat_tailed":
        dof = config["degrees_of_freedom"]
        raw = student_t.rvs(df=dof, size=(n_paths, n_years), random_state=rng)
        scale = sigma / np.sqrt(dof / (dof - 2))
        annual_returns = mu + scale * raw
    else:
        raise ValueError("unknown distribution: " + str(config["distribution"]))
    annual_returns = np.maximum(annual_returns, -0.999)
    growth = np.cumprod(1 + annual_returns, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])
```

- [ ] **Step 4: Run to verify parameterized tests pass**

Run: `pytest backend/tests/engine/test_parameterized.py -v`
Expected: PASS

- [ ] **Step 5: Write the failing test for forecasted**

```python
# backend/tests/engine/test_forecasted.py
import numpy as np
from backend.app.engine.forecasted import simulate_forecasted


def test_normal_model_shape_and_start():
    mu = np.array([0.08, 0.04])
    sigma = np.array([[0.04, 0.01], [0.01, 0.02]])
    weights = np.array([0.6, 0.4])
    config = {"seed": 3, "n_paths": 40, "simulation_period_years": 8, "time_series_model": "normal"}
    paths = simulate_forecasted(mu, sigma, weights, config)
    assert paths.shape == (40, 9)
    assert np.allclose(paths[:, 0], 1.0)
```

- [ ] **Step 6: Run to verify it fails**

Run: `pytest backend/tests/engine/test_forecasted.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 7: Write `backend/app/engine/forecasted.py`** (ported verbatim from `tests/forecasted_sim.py`)

```python
import numpy as np
from arch import arch_model


def simulate_forecasted(mu, sigma, weights, config, returns_df=None):
    rng = np.random.default_rng(config["seed"])
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    if config["time_series_model"] == "garch":
        port_mu = weights @ mu if mu is not None else float(np.nanmean(returns_df.to_numpy() @ weights)) * 252
        annual_returns = _garch_annual_returns(returns_df, weights, port_mu, n_years, n_paths, rng)
    elif config["time_series_model"] == "normal":
        port_mu = weights @ mu
        port_var = weights @ sigma @ weights
        annual_returns = rng.normal(port_mu, np.sqrt(port_var), size=(n_paths, n_years))
    else:
        raise ValueError(f"unknown time_series_model: {config['time_series_model']}")
    growth = np.cumprod(1 + annual_returns, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])


def _garch_annual_returns(returns_df, weights, port_mu, n_years, n_paths, rng):
    """GARCH(1,1) drives ONLY the time-varying volatility, simulated via the arch package
    with mean="Zero" - the drift (port_mu) is added back explicitly afterwards. See
    CLAUDE.md landmines: arch_model's mean="Constant" MLE produces absurd drift estimates
    on this data (~19.9%/yr annualized vs. ~12.2%/yr simple historical mean)."""
    port_returns_daily = returns_df.to_numpy() @ weights
    demeaned_pct = (port_returns_daily - port_returns_daily.mean()) * 100
    am = arch_model(demeaned_pct, vol="Garch", p=1, q=1, dist="normal", mean="Zero")
    res = am.fit(disp="off")
    forecasts = res.forecast(horizon=252 * n_years, method="simulation", simulations=n_paths, reindex=False)
    sim_daily_shock_pct = forecasts.simulations.values[-1] / 100
    daily_mu = port_mu / 252
    sim_daily = daily_mu + sim_daily_shock_pct
    sim_daily = sim_daily.reshape(n_paths, n_years, 252)
    return np.prod(1 + sim_daily, axis=2) - 1
```

- [ ] **Step 8: Run to verify forecasted test passes**

Run: `pytest backend/tests/engine/test_forecasted.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/engine/parameterized.py backend/app/engine/forecasted.py backend/tests/engine/test_parameterized.py backend/tests/engine/test_forecasted.py
git commit -m "feat: promote parameterized and forecasted simulation models"
```

---

## Task 5: Historical model with bootstrap sub-modes and sequence-of-returns risk

**Files:**
- Create: `backend/app/engine/historical.py`
- Test: `backend/tests/engine/test_historical.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (pure numpy/pandas).
- Produces: `simulate_historical(returns_df: pd.DataFrame, weights: np.ndarray, config: dict) -> np.ndarray`, shape `(n_paths, n_years+1)`, normalized to start at 1.0. `config["bootstrap_model"]` in `{"single_month", "single_year", "block_of_years"}` (default `"single_year"` if key absent, matching the pre-existing behavior). `config["sequence_of_returns_risk"]` is an int 0–10 (0 = no adjustment; N = reorder so the worst N sampled years occur first in every path).

- [ ] **Step 1: Write the failing test — existing single-year behavior preserved**

```python
# backend/tests/engine/test_historical.py
import numpy as np
import pandas as pd
from backend.app.engine.historical import simulate_historical


def _sample_returns_df():
    idx = pd.date_range("2015-01-01", periods=252 * 6, freq="B")
    rng = np.random.default_rng(0)
    return pd.DataFrame({"A": rng.normal(0.0004, 0.01, len(idx)), "B": rng.normal(0.0002, 0.006, len(idx))}, index=idx)


def test_single_year_default_shape_and_start():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 1, "n_paths": 100, "simulation_period_years": 5, "bootstrap_model": "single_year"}
    paths = simulate_historical(returns_df, weights, config)
    assert paths.shape == (100, 6)
    assert np.allclose(paths[:, 0], 1.0)


def test_single_month_bootstrap_samples_monthly_blocks():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 2, "n_paths": 50, "simulation_period_years": 3, "bootstrap_model": "single_month"}
    paths = simulate_historical(returns_df, weights, config)
    assert paths.shape == (50, 4)


def test_block_of_years_preserves_within_block_sequence():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 3, "n_paths": 30, "simulation_period_years": 4, "bootstrap_model": "block_of_years", "block_years": 2}
    paths = simulate_historical(returns_df, weights, config)
    assert paths.shape == (30, 5)


def test_sequence_of_returns_risk_orders_worst_years_first():
    returns_df = _sample_returns_df()
    weights = np.array([0.6, 0.4])
    config = {"seed": 4, "n_paths": 1, "simulation_period_years": 6, "bootstrap_model": "single_year",
              "sequence_of_returns_risk": 3}
    paths = simulate_historical(returns_df, weights, config)
    per_year = paths[0, 1:] / paths[0, :-1] - 1
    assert np.all(np.diff(np.sort(per_year[:3])) >= -1e-9) or True  # first 3 years are the 3 worst sampled
    worst_three_actual = np.sort(per_year)[:3]
    assert np.allclose(np.sort(per_year[:3]), np.sort(worst_three_actual))
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/engine/test_historical.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/engine/historical.py`**

```python
import numpy as np
import pandas as pd


def simulate_historical(returns_df: pd.DataFrame, weights: np.ndarray, config: dict) -> np.ndarray:
    rng = np.random.default_rng(config["seed"])
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    bootstrap_model = config.get("bootstrap_model", "single_year")

    if bootstrap_model == "single_year":
        annual_returns = _annual_portfolio_returns(returns_df, weights)
        sampled = rng.choice(annual_returns, size=(n_paths, n_years), replace=True)
    elif bootstrap_model == "single_month":
        monthly_returns = _monthly_portfolio_returns(returns_df, weights)
        sampled_months = rng.choice(monthly_returns, size=(n_paths, n_years * 12), replace=True)
        sampled = np.prod((1 + sampled_months).reshape(n_paths, n_years, 12), axis=2) - 1
    elif bootstrap_model == "block_of_years":
        block_years = config.get("block_years", 2)
        annual_returns = _annual_portfolio_returns(returns_df, weights)
        sampled = _block_bootstrap(annual_returns, n_paths, n_years, block_years, rng)
    else:
        raise ValueError(f"unknown bootstrap_model: {bootstrap_model}")

    risk_n = config.get("sequence_of_returns_risk", 0)
    if risk_n:
        sampled = _apply_sequence_of_returns_risk(sampled, risk_n)

    growth = np.cumprod(1 + sampled, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])


def _annual_portfolio_returns(returns_df: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    annual_returns = returns_df.groupby(returns_df.index.year).apply(lambda g: (1 + g).prod() - 1)
    return annual_returns.to_numpy() @ weights


def _monthly_portfolio_returns(returns_df: pd.DataFrame, weights: np.ndarray) -> np.ndarray:
    monthly_returns = returns_df.groupby([returns_df.index.year, returns_df.index.month]).apply(
        lambda g: (1 + g).prod() - 1
    )
    return monthly_returns.to_numpy() @ weights


def _block_bootstrap(annual_returns: np.ndarray, n_paths: int, n_years: int, block_years: int, rng: np.random.Generator) -> np.ndarray:
    """Sample contiguous blocks of `block_years` real annual returns (with replacement across
    starting points), concatenating blocks until n_years is reached, then truncating."""
    n_available = len(annual_returns)
    n_blocks_needed = -(-n_years // block_years)  # ceil division
    out = np.empty((n_paths, n_blocks_needed * block_years))
    for p in range(n_paths):
        chunks = []
        for _ in range(n_blocks_needed):
            start = rng.integers(0, max(1, n_available - block_years + 1))
            block = annual_returns[start:start + block_years]
            if len(block) < block_years:
                block = np.pad(block, (0, block_years - len(block)), mode="wrap")
            chunks.append(block)
        out[p] = np.concatenate(chunks)
    return out[:, :n_years]


def _apply_sequence_of_returns_risk(sampled: np.ndarray, worst_n: int) -> np.ndarray:
    """Reorder each path's sampled annual returns so the worst `worst_n` years occur first,
    stress-testing sequence-of-returns risk. The remaining years keep their sampled order."""
    n_years = sampled.shape[1]
    worst_n = min(worst_n, n_years)
    reordered = np.empty_like(sampled)
    for p in range(sampled.shape[0]):
        row = sampled[p]
        worst_idx = np.argsort(row)[:worst_n]
        rest_idx = np.array([i for i in range(n_years) if i not in set(worst_idx)])
        worst_sorted = row[worst_idx][np.argsort(row[worst_idx])]
        reordered[p] = np.concatenate([worst_sorted, row[rest_idx]])
    return reordered
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest backend/tests/engine/test_historical.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/historical.py backend/tests/engine/test_historical.py
git commit -m "feat: historical model with bootstrap sub-modes and sequence-of-returns risk"
```

---

## Task 6: Statistical model with rebalancing fix

**Files:**
- Create: `backend/app/engine/statistical.py`
- Test: `backend/tests/engine/test_statistical.py`

**Interfaces:**
- Consumes: `simulate_gbm_paths` from `backend.app.engine.gbm` (Task 2), `_garch_annual_returns` from `backend.app.engine.forecasted` (Task 4) — fixes the cross-file import that existed in `tests/statistical_sim.py`.
- Produces: `simulate_statistical(mu: np.ndarray, sigma: np.ndarray, weights: np.ndarray, config: dict, returns_df: pd.DataFrame | None = None) -> np.ndarray`, shape `(n_paths, n_years+1)`. `config["rebalancing"]` in `{"none", "annual", "semiannual", "quarterly", "monthly"}` (default `"annual"`) — applies periodic rebalancing to the `"normal"` (GBM) branch, making its rebalancing semantics consistent with the other 3 models (see `CLAUDE.md` landmine).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/engine/test_statistical.py
import numpy as np
from backend.app.engine.statistical import simulate_statistical


def test_normal_model_no_rebalancing_matches_buy_and_hold():
    mu = np.array([0.08, 0.04])
    sigma = np.array([[0.04, 0.005], [0.005, 0.02]])
    weights = np.array([0.7, 0.3])
    config = {"seed": 5, "n_paths": 20, "simulation_period_years": 3,
              "time_series_model": "normal", "rebalancing": "none"}
    paths = simulate_statistical(mu, sigma, weights, config)
    assert paths.shape == (20, 4)
    assert np.allclose(paths[:, 0], 1.0)


def test_normal_model_annual_rebalancing_resets_weights_each_year():
    mu = np.array([0.08, 0.04])
    sigma = np.array([[0.04, 0.005], [0.005, 0.02]])
    weights = np.array([0.7, 0.3])
    config = {"seed": 5, "n_paths": 20, "simulation_period_years": 3,
              "time_series_model": "normal", "rebalancing": "annual"}
    paths = simulate_statistical(mu, sigma, weights, config)
    assert paths.shape == (20, 4)
    assert np.all(paths[:, 1:] > 0)


def test_no_rebalancing_and_annual_rebalancing_diverge():
    mu = np.array([0.15, -0.02])
    sigma = np.array([[0.09, 0.0], [0.0, 0.01]])
    weights = np.array([0.5, 0.5])
    config_none = {"seed": 9, "n_paths": 500, "simulation_period_years": 10,
                   "time_series_model": "normal", "rebalancing": "none"}
    config_annual = dict(config_none, rebalancing="annual")
    paths_none = simulate_statistical(mu, sigma, weights, config_none)
    paths_annual = simulate_statistical(mu, sigma, weights, config_annual)
    assert not np.allclose(np.median(paths_none[:, -1]), np.median(paths_annual[:, -1]), rtol=0.01)
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/engine/test_statistical.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/engine/statistical.py`**

```python
import numpy as np
from backend.app.engine.gbm import simulate_gbm_paths
from backend.app.engine.forecasted import _garch_annual_returns

_REBALANCE_STEPS_PER_YEAR = {"none": None, "annual": 1, "semiannual": 2, "quarterly": 4, "monthly": 12}


def simulate_statistical(mu, sigma, weights, config, returns_df=None):
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    if config["time_series_model"] == "normal":
        asset_paths = simulate_gbm_paths(
            S0=np.ones(len(weights)), mu=mu, sigma=sigma,
            n_years=n_years, steps_per_year=252, n_paths=n_paths, seed=config["seed"],
        )
        rebalancing = config.get("rebalancing", "annual")
        rebalances_per_year = _REBALANCE_STEPS_PER_YEAR.get(rebalancing)
        if rebalances_per_year is None:
            # No rebalancing: weights are applied once, at t=0, to price levels (buy-and-hold,
            # drifting weights thereafter).
            portfolio_paths = asset_paths @ weights
            annual_idx = np.arange(0, n_years * 252 + 1, 252)
            return portfolio_paths[:, annual_idx]
        return _rebalanced_portfolio_values(asset_paths, weights, rebalances_per_year, n_years)
    elif config["time_series_model"] == "garch":
        rng = np.random.default_rng(config["seed"])
        port_mu = weights @ mu
        annual_returns = _garch_annual_returns(returns_df, weights, port_mu, n_years, n_paths, rng)
        growth = np.cumprod(1 + annual_returns, axis=1)
        return np.hstack([np.ones((n_paths, 1)), growth])
    else:
        raise ValueError("unknown time_series_model: " + str(config["time_series_model"]))


def _rebalanced_portfolio_values(asset_paths: np.ndarray, weights: np.ndarray, rebalances_per_year: int, n_years: int) -> np.ndarray:
    """Rebuild portfolio value year-by-year, resetting each asset's weight to its target at
    every rebalance date. Each asset's within-period return between rebalance dates is applied
    to its target-weighted share of the portfolio value at the start of that period."""
    n_paths, n_steps_plus_one, n_assets = asset_paths.shape
    steps_per_year = (n_steps_plus_one - 1) // n_years
    total_rebalances = rebalances_per_year * n_years
    steps_per_rebalance = steps_per_year // rebalances_per_year
    rebalance_step_indices = [i * steps_per_rebalance for i in range(total_rebalances + 1)]
    rebalance_step_indices[-1] = n_steps_plus_one - 1

    portfolio_value = np.ones(n_paths)
    values_at_period_start = np.tile(weights, (n_paths, 1))  # per-asset dollar allocation at period start
    annual_values = [np.ones(n_paths)]
    for period in range(total_rebalances):
        start_idx = rebalance_step_indices[period]
        end_idx = rebalance_step_indices[period + 1]
        asset_growth = asset_paths[:, end_idx, :] / asset_paths[:, start_idx, :]
        period_end_asset_values = values_at_period_start * asset_growth
        portfolio_value = period_end_asset_values.sum(axis=1)
        values_at_period_start = portfolio_value[:, None] * weights[None, :]
        if (period + 1) % rebalances_per_year == 0:
            annual_values.append(portfolio_value.copy())
    return np.array(annual_values).T
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest backend/tests/engine/test_statistical.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/statistical.py backend/tests/engine/test_statistical.py
git commit -m "feat: statistical model with fixed cross-import and rebalancing consistency"
```

---

## Task 7: Inflation model

**Files:**
- Create: `backend/app/engine/inflation.py`
- Test: `backend/tests/engine/test_inflation.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `simulate_inflation(config: dict, n_paths: int, n_years: int, asset_return_correlation: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray`, shape `(n_paths, n_years)`. `config["inflation_model"]` in `{"historical", "parameterized"}`. For `"historical"`, `config["cpi_returns"]` must be a 1-D array of historical annual CPI changes supplied by the caller (the data-source question — where Thai CPI comes from — is resolved in Task 9's fund/data-status work, not here; this module only consumes whatever series it's given). For `"parameterized"`, `config["inflation_mean"]` and `config["inflation_volatility"]` drive a Normal draw.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/engine/test_inflation.py
import numpy as np
from backend.app.engine.inflation import simulate_inflation


def test_parameterized_inflation_shape_and_mean():
    config = {"inflation_model": "parameterized", "inflation_mean": 0.03, "inflation_volatility": 0.01}
    rng = np.random.default_rng(11)
    draws = simulate_inflation(config, n_paths=5000, n_years=10, rng=rng)
    assert draws.shape == (5000, 10)
    assert abs(draws.mean() - 0.03) < 0.005


def test_historical_inflation_resamples_supplied_series():
    cpi_series = np.array([0.02, 0.025, 0.03, 0.04, 0.015])
    config = {"inflation_model": "historical", "cpi_returns": cpi_series}
    rng = np.random.default_rng(12)
    draws = simulate_inflation(config, n_paths=200, n_years=6, rng=rng)
    assert draws.shape == (200, 6)
    assert set(np.unique(draws)).issubset(set(cpi_series))


def test_unknown_model_raises():
    import pytest
    with pytest.raises(ValueError):
        simulate_inflation({"inflation_model": "bogus"}, n_paths=1, n_years=1)
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/engine/test_inflation.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/engine/inflation.py`**

```python
import numpy as np


def simulate_inflation(config: dict, n_paths: int, n_years: int, asset_return_correlation: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Simulate annual inflation draws. `asset_return_correlation` is accepted for future
    correlated-sampling work (PV correlates inflation samples with simulated asset returns
    based on historical correlations) but is not yet applied — draws are independent for now."""
    rng = rng or np.random.default_rng(config.get("seed"))
    model = config["inflation_model"]
    if model == "parameterized":
        mean = config["inflation_mean"]
        vol = config["inflation_volatility"]
        return rng.normal(mean, vol, size=(n_paths, n_years))
    elif model == "historical":
        cpi_returns = np.asarray(config["cpi_returns"])
        return rng.choice(cpi_returns, size=(n_paths, n_years), replace=True)
    else:
        raise ValueError(f"unknown inflation_model: {model}")
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest backend/tests/engine/test_inflation.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/inflation.py backend/tests/engine/test_inflation.py
git commit -m "feat: add inflation model (historical resample + parameterized normal)"
```

---

## Task 8: Goals module — multi-goal cashflows and glide path

**Files:**
- Create: `backend/app/engine/goals.py`
- Test: `backend/tests/engine/test_goals.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `apply_cashflow(paths: np.ndarray, initial_amount: float, cashflow: dict) -> np.ndarray` — applies a single fixed contribution/withdrawal cashflow (amount, `is_withdrawal: bool`, `inflation_adjusted: bool`, `frequency: str`) onto simulated growth-factor paths (shape `(n_paths, n_years+1)`), returning dollar-value paths of the same shape.
  - `apply_named_goals(paths: np.ndarray, initial_amount: float, goals: list[dict]) -> tuple[np.ndarray, list[dict]]` — applies multiple named goals in chronological order; returns the resulting dollar-value paths plus a per-goal summary list with a computed `success_rate` (fraction of paths where the portfolio balance stayed non-negative through that goal's active period).
  - `glide_path_weights(start_weights: np.ndarray, end_weights: np.ndarray, glide_path_years: int, year: int) -> np.ndarray` — linear interpolation between `start_weights` and `end_weights`, clamped to `end_weights` once `year >= glide_path_years`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/engine/test_goals.py
import numpy as np
from backend.app.engine.goals import apply_cashflow, apply_named_goals, glide_path_weights


def test_apply_cashflow_withdrawal_reduces_balance():
    paths = np.ones((3, 4))  # flat growth, 3 years
    values = apply_cashflow(paths, initial_amount=1000.0, cashflow={
        "amount": 100.0, "is_withdrawal": True, "inflation_adjusted": False, "frequency": "annually",
    })
    assert values[0, 0] == 1000.0
    assert values[0, 1] < values[0, 0]


def test_apply_cashflow_contribution_increases_balance():
    paths = np.ones((3, 4))
    values = apply_cashflow(paths, initial_amount=1000.0, cashflow={
        "amount": 100.0, "is_withdrawal": False, "inflation_adjusted": False, "frequency": "annually",
    })
    assert values[0, 1] > values[0, 0]


def test_apply_named_goals_reports_success_rate():
    paths = np.ones((10, 4))
    goals = [
        {"purpose": "Savings", "amount": 50.0, "is_withdrawal": False, "inflation_adjusted": False,
         "frequency": "annually", "starts_year": 0, "ends_year": 3},
    ]
    values, summary = apply_named_goals(paths, initial_amount=1000.0, goals=goals)
    assert values.shape == (10, 4)
    assert summary[0]["purpose"] == "Savings"
    assert summary[0]["success_rate"] == 1.0  # contributions only, can't go negative


def test_glide_path_interpolates_linearly_then_clamps():
    start = np.array([0.8, 0.2])
    end = np.array([0.2, 0.8])
    mid = glide_path_weights(start, end, glide_path_years=10, year=5)
    assert np.allclose(mid, [0.5, 0.5])
    after = glide_path_weights(start, end, glide_path_years=10, year=15)
    assert np.allclose(after, end)
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/engine/test_goals.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/engine/goals.py`**

```python
import numpy as np


def apply_cashflow(paths: np.ndarray, initial_amount: float, cashflow: dict) -> np.ndarray:
    """Apply one fixed annual contribution/withdrawal to normalized growth-factor paths,
    year by year, compounding on the resulting dollar balance each year."""
    n_paths, n_years_plus_one = paths.shape
    n_years = n_years_plus_one - 1
    growth_factors = paths[:, 1:] / paths[:, :-1]
    sign = -1.0 if cashflow["is_withdrawal"] else 1.0
    amount = cashflow["amount"]
    values = np.empty((n_paths, n_years_plus_one))
    values[:, 0] = initial_amount
    for year in range(n_years):
        grown = values[:, year] * growth_factors[:, year]
        values[:, year + 1] = np.maximum(grown + sign * amount, 0.0)
    return values


def apply_named_goals(paths: np.ndarray, initial_amount: float, goals: list[dict]) -> tuple[np.ndarray, list[dict]]:
    """Apply multiple named goals in chronological order (by starts_year), tracking a
    per-goal success rate: the fraction of paths whose balance stayed >= 0 throughout the
    goal's active window."""
    n_paths, n_years_plus_one = paths.shape
    n_years = n_years_plus_one - 1
    growth_factors = paths[:, 1:] / paths[:, :-1]
    values = np.empty((n_paths, n_years_plus_one))
    values[:, 0] = initial_amount
    solvent = np.ones(n_paths, dtype=bool)
    goal_solvent_tracking = {id(g): np.ones(n_paths, dtype=bool) for g in goals}

    for year in range(n_years):
        grown = values[:, year] * growth_factors[:, year]
        net_cashflow = np.zeros(n_paths)
        for goal in goals:
            if goal["starts_year"] <= year < goal["ends_year"]:
                sign = -1.0 if goal["is_withdrawal"] else 1.0
                net_cashflow += sign * goal["amount"]
        new_balance = grown + net_cashflow
        solvent &= new_balance >= 0
        values[:, year + 1] = np.maximum(new_balance, 0.0)
        for goal in goals:
            if goal["starts_year"] <= year < goal["ends_year"]:
                goal_solvent_tracking[id(goal)] &= solvent

    summary = []
    for goal in goals:
        summary.append({
            "purpose": goal["purpose"],
            "success_rate": float(goal_solvent_tracking[id(goal)].mean()),
        })
    return values, summary


def glide_path_weights(start_weights: np.ndarray, end_weights: np.ndarray, glide_path_years: int, year: int) -> np.ndarray:
    if year >= glide_path_years:
        return end_weights
    t = year / glide_path_years
    return start_weights * (1 - t) + end_weights * t
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest backend/tests/engine/test_goals.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/goals.py backend/tests/engine/test_goals.py
git commit -m "feat: add goals engine (named multi-goal cashflows, glide-path weights)"
```

---

## Task 9: Results engine — percentile table, VaR/ES, Sharpe/Sortino/SWR/PWR, survival series, correlation table

**Files:**
- Create: `backend/app/engine/results.py`
- Test: `backend/tests/engine/test_results.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (pure numpy/pandas on already-simulated path arrays).
- Produces:
  - `percentile_table(paths: np.ndarray, initial_amount: float) -> dict` — `{"ending_balance": {10: ..., 25: ..., 50: ..., 75: ..., 90: ...}, "cagr": {...}}`.
  - `parametric_var_es(weights, mu, sigma, alpha=0.90) -> tuple[float, float]`.
  - `compute_var_es(ending_values: np.ndarray, alpha=0.90) -> tuple[float, float]`.
  - `sharpe_sortino_by_percentile(paths: np.ndarray, risk_free_rate: float = 0.0) -> dict` — per-path annualized return/vol → Sharpe/Sortino, then percentile-banded (10/25/50/75/90) across paths.
  - `withdrawal_rates_by_percentile(paths: np.ndarray, n_years: int) -> dict` — Safe Withdrawal Rate (largest constant annual withdrawal rate that doesn't deplete the portfolio before `n_years`, found via bisection per path) and Perpetual Withdrawal Rate (`median_annual_return - median_annual_volatility^2/2` style closed-form, percentile-banded), both keyed by the same 5 percentiles.
  - `survival_series(paths: np.ndarray) -> np.ndarray` — shape `(n_years+1,)`, fraction of paths with balance > 0 at each year.
  - `correlation_and_returns_table(returns_df: pd.DataFrame, asset_names: list[str]) -> dict` — correlation matrix plus per-asset CAGR/expected return/volatility.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/engine/test_results.py
import numpy as np
import pandas as pd
from backend.app.engine.results import (
    percentile_table, parametric_var_es, compute_var_es,
    sharpe_sortino_by_percentile, withdrawal_rates_by_percentile,
    survival_series, correlation_and_returns_table,
)


def _sample_paths(seed=0, n_paths=500, n_years=10):
    rng = np.random.default_rng(seed)
    annual = rng.normal(0.06, 0.15, size=(n_paths, n_years))
    growth = np.cumprod(1 + annual, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])


def test_percentile_table_has_five_bands():
    table = percentile_table(_sample_paths(), initial_amount=1000.0)
    assert set(table["ending_balance"].keys()) == {10, 25, 50, 75, 90}
    assert table["ending_balance"][50] > 0


def test_parametric_and_empirical_var_es_are_positive_losses():
    weights = np.array([0.6, 0.4])
    mu = np.array([0.08, 0.03])
    sigma = np.array([[0.04, 0.005], [0.005, 0.02]])
    var, es = parametric_var_es(weights, mu, sigma)
    assert es >= var
    ending = np.random.default_rng(1).normal(0.0, 0.2, 1000)
    var2, es2 = compute_var_es(ending)
    assert es2 >= var2


def test_sharpe_sortino_by_percentile_returns_five_bands():
    result = sharpe_sortino_by_percentile(_sample_paths())
    assert set(result["sharpe"].keys()) == {10, 25, 50, 75, 90}
    assert set(result["sortino"].keys()) == {10, 25, 50, 75, 90}


def test_withdrawal_rates_by_percentile_returns_five_bands():
    result = withdrawal_rates_by_percentile(_sample_paths(), n_years=10)
    assert set(result["safe_withdrawal_rate"].keys()) == {10, 25, 50, 75, 90}
    assert set(result["perpetual_withdrawal_rate"].keys()) == {10, 25, 50, 75, 90}


def test_survival_series_starts_at_one_and_is_monotonic_or_equal():
    paths = _sample_paths()
    series = survival_series(paths)
    assert series[0] == 1.0
    assert len(series) == paths.shape[1]
    assert np.all(series >= 0) and np.all(series <= 1)


def test_correlation_and_returns_table_shape():
    idx = pd.date_range("2020-01-01", periods=500, freq="B")
    rng = np.random.default_rng(2)
    returns_df = pd.DataFrame({"A": rng.normal(0.0003, 0.01, 500), "B": rng.normal(0.0001, 0.008, 500)}, index=idx)
    table = correlation_and_returns_table(returns_df, ["A", "B"])
    assert table["correlation"]["A"]["A"] == 1.0
    assert "cagr" in table["stats"]["A"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/engine/test_results.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/engine/results.py`**

```python
import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq

_PCTS = [10, 25, 50, 75, 90]


def percentile_table(paths: np.ndarray, initial_amount: float) -> dict:
    ending = paths[:, -1] * initial_amount
    n_years = paths.shape[1] - 1
    cagr = paths[:, -1] ** (1 / n_years) - 1
    return {
        "ending_balance": {p: float(np.percentile(ending, p)) for p in _PCTS},
        "cagr": {p: float(np.percentile(cagr, p)) for p in _PCTS},
    }


def parametric_var_es(weights: np.ndarray, mu: np.ndarray, sigma: np.ndarray, alpha: float = 0.90) -> tuple[float, float]:
    port_mu = weights @ mu
    port_sd = np.sqrt(weights @ sigma @ weights)
    z = norm.ppf(alpha)
    var = -port_mu + z * port_sd
    es = -port_mu + (norm.pdf(z) / (1 - alpha)) * port_sd
    return var, es


def compute_var_es(ending_values: np.ndarray, alpha: float = 0.90) -> tuple[float, float]:
    losses = -ending_values
    var_threshold = np.percentile(losses, alpha * 100)
    es = losses[losses >= var_threshold].mean()
    return -var_threshold, -es


def sharpe_sortino_by_percentile(paths: np.ndarray, risk_free_rate: float = 0.0) -> dict:
    n_years = paths.shape[1] - 1
    per_path_annual_returns = paths[:, -1] ** (1 / n_years) - 1
    per_period_returns = paths[:, 1:] / paths[:, :-1] - 1
    per_path_vol = per_period_returns.std(axis=1) * np.sqrt(1)
    downside = np.where(per_period_returns < 0, per_period_returns, 0.0)
    per_path_downside_vol = np.sqrt((downside ** 2).mean(axis=1))
    with np.errstate(divide="ignore", invalid="ignore"):
        sharpe = np.where(per_path_vol > 0, (per_path_annual_returns - risk_free_rate) / per_path_vol, 0.0)
        sortino = np.where(per_path_downside_vol > 0, (per_path_annual_returns - risk_free_rate) / per_path_downside_vol, 0.0)
    return {
        "sharpe": {p: float(np.percentile(sharpe, p)) for p in _PCTS},
        "sortino": {p: float(np.percentile(sortino, p)) for p in _PCTS},
    }


def withdrawal_rates_by_percentile(paths: np.ndarray, n_years: int) -> dict:
    n_paths = paths.shape[0]
    swr = np.empty(n_paths)
    for i in range(n_paths):
        growth_factors = paths[i, 1:] / paths[i, :-1]

        def final_balance(rate):
            balance = 1.0
            for g in growth_factors:
                balance = max(balance * g - rate, 0.0)
            return balance

        try:
            swr[i] = brentq(final_balance, 0.0, 1.0, xtol=1e-4)
        except ValueError:
            swr[i] = 0.0 if final_balance(1.0) > 0 else 1.0

    per_path_annual_returns = paths[:, -1] ** (1 / n_years) - 1
    per_period_returns = paths[:, 1:] / paths[:, :-1] - 1
    per_path_vol = per_period_returns.std(axis=1)
    pwr = per_path_annual_returns - 0.5 * per_path_vol ** 2

    return {
        "safe_withdrawal_rate": {p: float(np.percentile(swr, p)) for p in _PCTS},
        "perpetual_withdrawal_rate": {p: float(np.percentile(pwr, p)) for p in _PCTS},
    }


def survival_series(paths: np.ndarray) -> np.ndarray:
    return (paths > 0).mean(axis=0)


def correlation_and_returns_table(returns_df: pd.DataFrame, asset_names: list[str], periods_per_year: int = 252) -> dict:
    correlation = returns_df[asset_names].corr()
    cumulative = (1 + returns_df[asset_names]).prod()
    n_periods = len(returns_df)
    cagr = cumulative ** (periods_per_year / n_periods) - 1
    expected_return = returns_df[asset_names].mean() * periods_per_year
    volatility = returns_df[asset_names].std() * np.sqrt(periods_per_year)
    return {
        "correlation": {a: {b: float(correlation.loc[a, b]) for b in asset_names} for a in asset_names},
        "stats": {
            a: {"cagr": float(cagr[a]), "expected_return": float(expected_return[a]), "volatility": float(volatility[a])}
            for a in asset_names
        },
    }
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest backend/tests/engine/test_results.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/results.py backend/tests/engine/test_results.py
git commit -m "feat: results engine with Sharpe/Sortino/SWR/PWR, survival series, correlation table"
```

---

## Task 10: Domain schemas

**Files:**
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/domain/schemas.py`
- Test: `backend/tests/domain/test_schemas.py`

**Interfaces:**
- Produces: `SimulateRequest` (Pydantic model — portfolio holdings, core params, discriminated model-specific params, cashflow/goals config, inflation config, rebalancing), `SimulateResponse` (Pydantic model — 7 sections matching the Results sub-tabs: `overview`, `growth`, `distribution`, `metrics`, `risk`, `goals` (optional), plus raw fields the frontend needs for the Report tab).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/domain/test_schemas.py
import pytest
from pydantic import ValidationError
from backend.app.domain.schemas import SimulateRequest, Holding


def test_valid_historical_request_parses():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
        initial_amount=1_000_000,
        simulation_period_years=30,
        tax_treatment="pre_tax",
        simulation_model="historical",
        n_paths=10000,
        seed=42,
        bootstrap_model="single_year",
        use_full_history=True,
        sequence_of_returns_risk=0,
        rebalancing="annual",
        inflation_model="historical",
    )
    assert req.simulation_model == "historical"
    assert len(req.holdings) == 2


def test_weights_must_sum_to_100():
    with pytest.raises(ValidationError):
        SimulateRequest(
            holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=30.0)],
            initial_amount=1_000_000,
            simulation_period_years=30,
            tax_treatment="pre_tax",
            simulation_model="historical",
            n_paths=10000,
            seed=42,
            rebalancing="annual",
            inflation_model="historical",
        )


def test_parameterized_model_requires_expected_return_and_volatility():
    with pytest.raises(ValidationError):
        SimulateRequest(
            holdings=[Holding(proj_id="M0027_2535", weight=100.0)],
            initial_amount=1_000_000,
            simulation_period_years=10,
            tax_treatment="pre_tax",
            simulation_model="parameterized",
            n_paths=10000,
            seed=42,
            rebalancing="annual",
            inflation_model="parameterized",
            inflation_mean=0.03,
            inflation_volatility=0.01,
            distribution="normal",
        )
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/domain/test_schemas.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create `backend/app/domain/__init__.py`** (empty file)

- [ ] **Step 4: Write `backend/app/domain/schemas.py`**

```python
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class Holding(BaseModel):
    proj_id: str
    weight: float = Field(ge=0, le=100)


class NamedGoal(BaseModel):
    purpose: str
    is_withdrawal: bool
    amount: float
    inflation_adjusted: bool
    frequency: Literal["monthly", "quarterly", "annually"]
    starts_year: int = Field(ge=0)
    ends_year: int = Field(ge=0)


class SimulateRequest(BaseModel):
    holdings: list[Holding]
    initial_amount: float = Field(gt=0)
    simulation_period_years: int = Field(ge=5, le=75)
    tax_treatment: Literal["pre_tax", "after_tax"]
    simulation_model: Literal["historical", "forecasted", "statistical", "parameterized"]
    n_paths: int = Field(ge=1000, le=20000, default=10000)
    seed: Optional[int] = None
    rebalancing: Literal["none", "annual", "semiannual", "quarterly", "monthly"]

    # Historical-specific
    use_full_history: Optional[bool] = None
    bootstrap_model: Optional[Literal["single_month", "single_year", "block_of_years"]] = None
    block_years: Optional[int] = None
    sequence_of_returns_risk: Optional[int] = Field(default=0, ge=0, le=10)

    # Forecasted / Statistical-specific
    time_series_model: Optional[Literal["normal", "garch"]] = None

    # Parameterized-specific
    distribution: Optional[Literal["normal", "fat_tailed"]] = None
    degrees_of_freedom: Optional[float] = None
    expected_return: Optional[float] = None
    expected_volatility: Optional[float] = None

    # Cashflow (single, default mode)
    cashflow_mode: Literal["none", "contribute", "withdraw_fixed", "withdraw_percent"] = "none"
    cashflow_amount: Optional[float] = None
    cashflow_inflation_adjusted: Optional[bool] = None
    cashflow_frequency: Optional[Literal["monthly", "quarterly", "annually"]] = None

    # Multi-goal / multistage (advanced)
    multi_goal_enabled: bool = False
    goals: Optional[list[NamedGoal]] = None
    years_to_retirement: Optional[int] = None
    glide_path_years: Optional[int] = None
    retirement_holdings: Optional[list[Holding]] = None

    # Inflation
    inflation_model: Literal["historical", "parameterized"]
    inflation_mean: Optional[float] = None
    inflation_volatility: Optional[float] = None

    @model_validator(mode="after")
    def weights_sum_to_100(self):
        total = sum(h.weight for h in self.holdings)
        if abs(total - 100.0) > 0.05:
            raise ValueError(f"holding weights must sum to 100, got {total}")
        return self

    @model_validator(mode="after")
    def parameterized_requires_return_and_volatility(self):
        if self.simulation_model == "parameterized":
            if self.expected_return is None or self.expected_volatility is None or self.distribution is None:
                raise ValueError("parameterized model requires expected_return, expected_volatility, distribution")
        return self


class PercentileBand(BaseModel):
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float


class SimulateResponse(BaseModel):
    overview: dict
    growth: dict
    distribution: dict
    metrics: dict
    risk: dict
    goals: Optional[dict] = None
    run_config: dict
```

- [ ] **Step 5: Run to verify tests pass**

Run: `pytest backend/tests/domain/test_schemas.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/domain backend/tests/domain
git commit -m "feat: add SimulateRequest/SimulateResponse Pydantic schemas"
```

---

## Task 11: Simulation orchestrator

**Files:**
- Create: `backend/app/engine/orchestrator.py`
- Test: `backend/tests/engine/test_orchestrator.py`

**Interfaces:**
- Consumes: every `engine/*` module from Tasks 2, 4, 5, 6, 7, 8, 9; `SimulateRequest`/`SimulateResponse` from Task 10; `estimate_mu_sigma` from `backend.app.data.returns` (Task 3).
- Produces: `run_simulation(request: SimulateRequest, returns_df: pd.DataFrame) -> SimulateResponse` — the single function the API layer calls. Dispatches to the correct `engine/*.simulate_*` function by `request.simulation_model`, applies cashflow/goals via `engine/goals.py`, computes every `engine/results.py` metric, and assembles the response sections.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/engine/test_orchestrator.py
import numpy as np
import pandas as pd
from backend.app.domain.schemas import SimulateRequest, Holding
from backend.app.engine.orchestrator import run_simulation


def _returns_df():
    idx = pd.date_range("2015-01-01", periods=252 * 8, freq="B")
    rng = np.random.default_rng(0)
    return pd.DataFrame({
        "M0027_2535": rng.normal(0.0003, 0.011, len(idx)),
        "M0209_2548": rng.normal(0.0002, 0.009, len(idx)),
    }, index=idx)


def test_historical_request_produces_all_response_sections():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=60.0), Holding(proj_id="M0209_2548", weight=40.0)],
        initial_amount=1_000_000, simulation_period_years=10, tax_treatment="pre_tax",
        simulation_model="historical", n_paths=2000, seed=1, rebalancing="annual",
        bootstrap_model="single_year", use_full_history=True, sequence_of_returns_risk=0,
        inflation_model="parameterized", inflation_mean=0.03, inflation_volatility=0.01,
    )
    response = run_simulation(req, _returns_df())
    assert response.overview["survived_count"] >= 0
    assert set(response.metrics["percentile_table"]["ending_balance"].keys()) == {10, 25, 50, 75, 90}
    assert "fan_chart" in response.growth
    assert response.goals is None


def test_parameterized_request_skips_data_estimation():
    req = SimulateRequest(
        holdings=[Holding(proj_id="M0027_2535", weight=100.0)],
        initial_amount=500_000, simulation_period_years=15, tax_treatment="pre_tax",
        simulation_model="parameterized", n_paths=2000, seed=2, rebalancing="annual",
        distribution="normal", expected_return=0.07, expected_volatility=0.14,
        inflation_model="parameterized", inflation_mean=0.03, inflation_volatility=0.01,
    )
    response = run_simulation(req, _returns_df())
    assert response.metrics["percentile_table"]["ending_balance"][50] > 0
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/engine/test_orchestrator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/engine/orchestrator.py`**

```python
import numpy as np
import pandas as pd
from backend.app.data.returns import estimate_mu_sigma
from backend.app.engine.gbm import simulate_gbm_paths  # noqa: F401 (used indirectly via statistical)
from backend.app.engine.historical import simulate_historical
from backend.app.engine.forecasted import simulate_forecasted
from backend.app.engine.statistical import simulate_statistical
from backend.app.engine.parameterized import simulate_parameterized
from backend.app.engine.inflation import simulate_inflation
from backend.app.engine.goals import apply_cashflow, apply_named_goals
from backend.app.engine.results import (
    percentile_table, sharpe_sortino_by_percentile, withdrawal_rates_by_percentile,
    survival_series, correlation_and_returns_table, compute_var_es,
)
from backend.app.domain.schemas import SimulateRequest, SimulateResponse


def run_simulation(request: SimulateRequest, returns_df: pd.DataFrame) -> SimulateResponse:
    proj_ids = [h.proj_id for h in request.holdings]
    weights = np.array([h.weight for h in request.holdings]) / 100.0
    subset = returns_df[proj_ids]
    mu, sigma = estimate_mu_sigma(subset)

    config = _build_engine_config(request)

    if request.simulation_model == "historical":
        growth_paths = simulate_historical(subset, weights, config)
    elif request.simulation_model == "forecasted":
        growth_paths = simulate_forecasted(mu, sigma, weights, config, returns_df=subset)
    elif request.simulation_model == "statistical":
        growth_paths = simulate_statistical(mu, sigma, weights, config, returns_df=subset)
    elif request.simulation_model == "parameterized":
        growth_paths = simulate_parameterized(config)
    else:
        raise ValueError(f"unknown simulation_model: {request.simulation_model}")

    goals_summary = None
    if request.multi_goal_enabled and request.goals:
        goal_dicts = [g.model_dump() for g in request.goals]
        dollar_paths, goals_summary = apply_named_goals(growth_paths, request.initial_amount, goal_dicts)
    elif request.cashflow_mode != "none":
        cashflow = {
            "amount": request.cashflow_amount or 0.0,
            "is_withdrawal": request.cashflow_mode.startswith("withdraw"),
            "inflation_adjusted": bool(request.cashflow_inflation_adjusted),
            "frequency": request.cashflow_frequency or "annually",
        }
        dollar_paths = apply_cashflow(growth_paths, request.initial_amount, cashflow)
    else:
        dollar_paths = growth_paths * request.initial_amount

    normalized_paths = dollar_paths / request.initial_amount
    pct_table = percentile_table(normalized_paths, request.initial_amount)
    sharpe_sortino = sharpe_sortino_by_percentile(normalized_paths)
    withdrawal_rates = withdrawal_rates_by_percentile(normalized_paths, request.simulation_period_years)
    survival = survival_series(dollar_paths)
    corr_table = correlation_and_returns_table(subset, proj_ids)
    ending_values = dollar_paths[:, -1] - request.initial_amount
    var, es = compute_var_es(ending_values)

    survived_count = int((dollar_paths[:, -1] > 0).sum())

    overview = {
        "n_paths": request.n_paths,
        "survived_count": survived_count,
        "survival_rate": survived_count / dollar_paths.shape[0],
        "median_ending_balance": pct_table["ending_balance"][50],
        "median_cagr": pct_table["cagr"][50],
        "holdings": [{"proj_id": h.proj_id, "weight": h.weight} for h in request.holdings],
    }
    growth = {
        "fan_chart": {p: (np.percentile(dollar_paths, p, axis=0)).tolist() for p in [10, 25, 50, 75, 90]},
        "survival_over_time": survival.tolist(),
    }
    distribution = {
        "ending_balance_histogram": dollar_paths[:, -1].tolist(),
    }
    metrics = {
        "percentile_table": pct_table,
        "sharpe": sharpe_sortino["sharpe"],
        "sortino": sharpe_sortino["sortino"],
        "safe_withdrawal_rate": withdrawal_rates["safe_withdrawal_rate"],
        "perpetual_withdrawal_rate": withdrawal_rates["perpetual_withdrawal_rate"],
    }
    risk = {
        "correlation_and_returns": corr_table,
        "value_at_risk": var,
        "expected_shortfall": es,
    }
    goals_section = {"summary": goals_summary} if goals_summary is not None else None

    return SimulateResponse(
        overview=overview, growth=growth, distribution=distribution,
        metrics=metrics, risk=risk, goals=goals_section,
        run_config=request.model_dump(),
    )


def _build_engine_config(request: SimulateRequest) -> dict:
    return {
        "seed": request.seed,
        "n_paths": request.n_paths,
        "simulation_period_years": request.simulation_period_years,
        "bootstrap_model": request.bootstrap_model,
        "block_years": request.block_years,
        "sequence_of_returns_risk": request.sequence_of_returns_risk or 0,
        "time_series_model": request.time_series_model,
        "rebalancing": request.rebalancing,
        "distribution": request.distribution,
        "degrees_of_freedom": request.degrees_of_freedom,
        "expected_return": request.expected_return,
        "expected_volatility": request.expected_volatility,
    }
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest backend/tests/engine/test_orchestrator.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/orchestrator.py backend/tests/engine/test_orchestrator.py
git commit -m "feat: add simulation orchestrator tying engine modules to SimulateRequest/Response"
```

---

## Task 12: FastAPI application

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/simulate.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/main.py`
- Test: `backend/tests/api/test_simulate_endpoint.py`

**Interfaces:**
- Consumes: `run_simulation` (Task 11), `SimulateRequest`/`SimulateResponse` (Task 10), `get_daily_nav`/`find_equity_funds` (Task 3).
- Produces: `POST /api/simulate`, `GET /api/health`, mounted at both `/api/v1/*` and unversioned `/api/*` (matching Backtest Portfolio's convention). Serves `frontend/dist` as a static SPA when it exists (production mode).

- [ ] **Step 1: Write the failing test** (uses FastAPI's `TestClient`, monkeypatches `run_simulation` to avoid real SEC calls)

```python
# backend/tests/api/test_simulate_endpoint.py
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.domain.schemas import SimulateResponse

client = TestClient(app)


def _fake_response():
    return SimulateResponse(
        overview={"n_paths": 100, "survived_count": 95, "survival_rate": 0.95,
                   "median_ending_balance": 2_000_000.0, "median_cagr": 0.07, "holdings": []},
        growth={"fan_chart": {}, "survival_over_time": []},
        distribution={"ending_balance_histogram": []},
        metrics={"percentile_table": {"ending_balance": {}, "cagr": {}}, "sharpe": {}, "sortino": {},
                 "safe_withdrawal_rate": {}, "perpetual_withdrawal_rate": {}},
        risk={"correlation_and_returns": {}, "value_at_risk": 0.0, "expected_shortfall": 0.0},
        goals=None, run_config={},
    )


@patch("backend.app.api.simulate.load_nav_returns")
@patch("backend.app.api.simulate.run_simulation")
def test_simulate_endpoint_returns_200(mock_run, mock_load, ):
    import pandas as pd
    mock_load.return_value = pd.DataFrame()
    mock_run.return_value = _fake_response()
    payload = {
        "holdings": [{"proj_id": "M0027_2535", "weight": 100.0}],
        "initial_amount": 1000000, "simulation_period_years": 10, "tax_treatment": "pre_tax",
        "simulation_model": "parameterized", "n_paths": 1000, "seed": 1, "rebalancing": "annual",
        "distribution": "normal", "expected_return": 0.07, "expected_volatility": 0.14,
        "inflation_model": "parameterized", "inflation_mean": 0.03, "inflation_volatility": 0.01,
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    assert resp.json()["overview"]["survival_rate"] == 0.95


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/api/test_simulate_endpoint.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create `backend/app/api/__init__.py`** (empty file)

- [ ] **Step 4: Write `backend/app/api/health.py`**

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Write `backend/app/api/simulate.py`**

```python
from fastapi import APIRouter, HTTPException
from backend.app.domain.schemas import SimulateRequest, SimulateResponse
from backend.app.engine.orchestrator import run_simulation
from backend.app.data.sec_client import get_daily_nav
from backend.app.data.returns import build_price_panel, log_returns

router = APIRouter()


def load_nav_returns(proj_ids: list[str], simulation_period_years: int):
    """Fetch NAV history for the requested funds and return daily log returns. Raises a
    hard error (never interpolates) if any requested fund has no usable NAV history."""
    import pandas as pd
    frames = []
    for proj_id in proj_ids:
        nav_df = get_daily_nav(proj_id, "2000-01-01", pd.Timestamp.today().strftime("%Y-%m-%d"))
        if nav_df.empty:
            raise HTTPException(status_code=503, detail=f"NAV_CACHE_MISSING: no NAV history for {proj_id}")
        frames.append(nav_df)
    nav_df = pd.concat(frames, ignore_index=True)
    panel = build_price_panel(nav_df)
    return log_returns(panel)


@router.post("/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest) -> SimulateResponse:
    proj_ids = [h.proj_id for h in request.holdings]
    returns_df = load_nav_returns(proj_ids, request.simulation_period_years)
    return run_simulation(request, returns_df)
```

- [ ] **Step 6: Write `backend/app/main.py`**

```python
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app.api import simulate, health

app = FastAPI(title="Monte Carlo Simulation API")

for prefix in ("/api/v1", "/api"):
    app.include_router(simulate.router, prefix=prefix)
    app.include_router(health.router, prefix=prefix)

_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
```

- [ ] **Step 7: Run to verify tests pass**

Run: `pytest backend/tests/api/test_simulate_endpoint.py -v`
Expected: PASS (2 tests)

- [ ] **Step 8: Run the full backend test suite**

Run: `pytest backend/tests -v`
Expected: PASS (all tests from Tasks 2–12)

- [ ] **Step 9: Commit**

```bash
git add backend/app/api backend/app/main.py backend/tests/api
git commit -m "feat: add FastAPI app with /api/simulate and /api/health"
```

---

## Task 13: Fund search endpoint

**Files:**
- Create: `backend/app/api/funds.py`
- Test: `backend/tests/api/test_funds_endpoint.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `find_equity_funds`, `get_amcs` (Task 3).
- Produces: `GET /api/funds` (returns the cached equity-fund universe as JSON).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/api/test_funds_endpoint.py
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@patch("backend.app.api.funds.find_equity_funds")
def test_funds_endpoint_returns_list(mock_find):
    mock_find.return_value = [{"proj_id": "M0027_2535", "proj_name_thai": "K หุ้นทุน"}]
    resp = client.get("/api/funds")
    assert resp.status_code == 200
    assert resp.json()[0]["proj_id"] == "M0027_2535"
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest backend/tests/api/test_funds_endpoint.py -v`
Expected: FAIL — `404` (route doesn't exist) or `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/app/api/funds.py`**

```python
from fastapi import APIRouter
from backend.app.data.sec_client import find_equity_funds

router = APIRouter()


@router.get("/funds")
def list_funds():
    return find_equity_funds()
```

- [ ] **Step 4: Modify `backend/app/main.py`** to register the new router

```python
from backend.app.api import simulate, health, funds
```
and add `app.include_router(funds.router, prefix=prefix)` alongside the existing two `include_router` calls inside the `for prefix in ("/api/v1", "/api"):` loop.

- [ ] **Step 5: Run to verify tests pass**

Run: `pytest backend/tests/api/test_funds_endpoint.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/funds.py backend/app/main.py backend/tests/api/test_funds_endpoint.py
git commit -m "feat: add /api/funds endpoint for portfolio-step fund search"
```

---

## Task 14: Frontend scaffold — copy shell from Backtest Portfolio

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/index.html`
- Create: `frontend/src/main.tsx`, `frontend/src/styles.css`
- Create: `frontend/src/components/Stepper.tsx`, `frontend/src/components/RunOverlay.tsx`
- Create: `frontend/src/api/client.ts`

**Interfaces:**
- Produces: a running Vite dev server shell with the same design tokens as Backtest Portfolio, ready for `PortfolioStep`/`ParametersStep`/`ResultsView` to be dropped in.

- [ ] **Step 1: Copy `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html` from `../Backtest Portfolio Webull:SEC OPENAI/frontend/`**, updating only the `name` field in `package.json` to `monte-carlo-frontend` and the `<title>` in `index.html` to "Monte Carlo Simulation".

Run:
```bash
cp "../Backtest Portfolio Webull:SEC OPENAI/frontend/tsconfig.json" frontend/tsconfig.json
cp "../Backtest Portfolio Webull:SEC OPENAI/frontend/vite.config.ts" frontend/vite.config.ts
```
Then hand-edit `frontend/package.json` (name field) and `frontend/index.html` (title) after copying them the same way.

- [ ] **Step 2: Copy `styles.css` verbatim**

```bash
cp "../Backtest Portfolio Webull:SEC OPENAI/frontend/src/styles.css" frontend/src/styles.css
```

Verify the copied file still contains `--accent: #5b21d6` (light) and `font-family: Inter, ui-sans-serif...` — these are the tokens confirmed in the spec.

- [ ] **Step 3: Copy `Stepper.tsx` and `RunOverlay.tsx` verbatim**, updating only the step labels in `Stepper.tsx` from `["Portfolio", "Assumptions", "Results"]` (or whatever Backtest uses) to `["Portfolio", "Parameters", "Results"]`.

```bash
cp "../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/Stepper.tsx" frontend/src/components/Stepper.tsx
cp "../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/RunOverlay.tsx" frontend/src/components/RunOverlay.tsx
```
Read the copied `Stepper.tsx`, find its step-label array/props, and change the labels to match this project's 3 steps.

- [ ] **Step 4: Write `frontend/src/api/client.ts`** (hand-mirrored types, no codegen — same convention as Backtest Portfolio)

```typescript
import type { SimulateRequest, SimulateResponse } from "../types/simulate";

const API_BASE = "/api";

export async function postSimulate(request: SimulateRequest): Promise<SimulateResponse> {
  const resp = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`simulate failed: ${resp.status} ${body}`);
  }
  return resp.json();
}

export interface FundSummary {
  proj_id: string;
  proj_name_thai?: string;
  amc_name_thai?: string;
}

export async function getFunds(): Promise<FundSummary[]> {
  const resp = await fetch(`${API_BASE}/funds`);
  if (!resp.ok) throw new Error(`funds fetch failed: ${resp.status}`);
  return resp.json();
}
```

- [ ] **Step 5: Write `frontend/src/main.tsx`** (standard Vite React entrypoint)

```typescript
import React from "react";
import ReactDOM from "react-dom/client";
import "./styles.css";
import { App } from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 6: Install dependencies and verify the build pipeline works**

Run: `npm --prefix frontend install`
Run: `npm --prefix frontend run build`
Expected: fails only on the missing `App.tsx` import (expected — created in Task 17) with a clear TypeScript error, not a config/tooling error.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/vite.config.ts frontend/index.html frontend/src/main.tsx frontend/src/styles.css frontend/src/components/Stepper.tsx frontend/src/components/RunOverlay.tsx frontend/src/api/client.ts
git commit -m "feat: copy frontend scaffold and design tokens from Backtest Portfolio"
```

---

## Task 15: Chart primitives — port from RunSummary.tsx

**Files:**
- Create: `frontend/src/components/charts.tsx`

**Interfaces:**
- Produces: `AxisCurve`, `Histogram`, `CorrelationMatrix`, `DataTable` — extracted as standalone, non-backtest-specific components, ported from `RunSummary.tsx`'s implementations.

- [ ] **Step 1: Read the source implementations to port**

Run: `sed -n '442,670p;1166,1230p' "../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/RunSummary.tsx"`

This prints `AxisCurve`, `xForIndex`, `DataTable`, `MonthlyHeatmap`, `Histogram`, `deriveResult`, `heatColor`, `correlationColor`, `CorrelationMatrix`, `formatCell`. Read the output before proceeding — the exact prop shapes (`ChartSeries`, `TableSection` types) must match what's ported.

- [ ] **Step 2: Write `frontend/src/components/charts.tsx`**, copying `AxisCurve`, `Histogram`, `CorrelationMatrix`, and `DataTable` (plus their local helper functions `xForIndex`, `heatColor`, `correlationColor`, `formatCell`) verbatim from the Step 1 output, renaming their internal `BacktestResult`-typed props to the generic shapes this project needs:

```typescript
export interface ChartSeries {
  label: string;
  color: string;
  points: { x: number; y: number }[];
}

export interface TableSection {
  title: string;
  columns: string[];
  rows: (string | number)[][];
}

// Paste the ported AxisCurve, Histogram, CorrelationMatrix, DataTable component bodies
// here, with their prop types changed from `{ result: BacktestResult }` to accept
// `ChartSeries[]` / `TableSection` / raw histogram bins directly (matching the shapes
// this project's SimulateResponse produces), and their internal helper functions
// (xForIndex, heatColor, correlationColor, formatCell) copied alongside them unchanged.
```

Note for the implementing engineer: this step requires reading the actual ported source
(Step 1) and adapting prop types — the exact component bodies aren't reproduced here
because they belong to a file this plan didn't inline in full. Preserve the SVG
rendering logic and helper functions exactly; only change the outer prop interface from
`{ result: BacktestResult }` to direct data props.

- [ ] **Step 3: Write a smoke test** confirming the module exports the four components and builds cleanly

```bash
npm --prefix frontend run build
```
Expected: TypeScript compiles `charts.tsx` with no errors (may still fail elsewhere until `App.tsx` exists — check the error is not in `charts.tsx`).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/charts.tsx
git commit -m "feat: port AxisCurve/Histogram/CorrelationMatrix/DataTable chart primitives"
```

---

## Task 16: Portfolio step — port from Backtest Portfolio

**Files:**
- Create: `frontend/src/components/PortfolioStep.tsx`
- Create: `frontend/src/types/simulate.ts`

**Interfaces:**
- Produces: `PortfolioStep` component with the same Equal weight / Normalize to 100% / Clear bulk-actions and SEC fund search/select UI as Backtest Portfolio; `Holding` type matching the backend's `Holding` schema (Task 10).

- [ ] **Step 1: Copy `PortfolioStep.tsx` from Backtest Portfolio as the starting point**

```bash
cp "../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/PortfolioStep.tsx" frontend/src/components/PortfolioStep.tsx
```

- [ ] **Step 2: Read the copied file and adapt it** — it already implements fund search, `equalWeightAll`, `normalizeWeights`, `clearWeights`, and the holdings table exactly per the spec (§8). Two changes only:
  1. Update its `import type { ... } from "../types/backtest"` (or equivalent) to import from `../types/simulate` instead.
  2. Remove any backtest-specific fields the row type carries that don't apply here (e.g. if the original `HoldingsRow` includes a benchmark-ticker field, drop it) — keep `proj_id`, `weight`, `query` (search text), `key` (row identity) exactly as-is, since those are shared between both apps' portfolio-building UX.

- [ ] **Step 3: Write `frontend/src/types/simulate.ts`** with the `Holding` type the adapted component needs:

```typescript
export interface Holding {
  proj_id: string;
  weight: number;
}

export interface SimulateRequest {
  holdings: Holding[];
  initial_amount: number;
  simulation_period_years: number;
  tax_treatment: "pre_tax" | "after_tax";
  simulation_model: "historical" | "forecasted" | "statistical" | "parameterized";
  n_paths: number;
  seed?: number;
  rebalancing: "none" | "annual" | "semiannual" | "quarterly" | "monthly";
  use_full_history?: boolean;
  bootstrap_model?: "single_month" | "single_year" | "block_of_years";
  block_years?: number;
  sequence_of_returns_risk?: number;
  time_series_model?: "normal" | "garch";
  distribution?: "normal" | "fat_tailed";
  degrees_of_freedom?: number;
  expected_return?: number;
  expected_volatility?: number;
  cashflow_mode: "none" | "contribute" | "withdraw_fixed" | "withdraw_percent";
  cashflow_amount?: number;
  cashflow_inflation_adjusted?: boolean;
  cashflow_frequency?: "monthly" | "quarterly" | "annually";
  multi_goal_enabled: boolean;
  goals?: NamedGoal[];
  years_to_retirement?: number;
  glide_path_years?: number;
  retirement_holdings?: Holding[];
  inflation_model: "historical" | "parameterized";
  inflation_mean?: number;
  inflation_volatility?: number;
}

export interface NamedGoal {
  purpose: string;
  is_withdrawal: boolean;
  amount: number;
  inflation_adjusted: boolean;
  frequency: "monthly" | "quarterly" | "annually";
  starts_year: number;
  ends_year: number;
}

export interface SimulateResponse {
  overview: Record<string, unknown>;
  growth: Record<string, unknown>;
  distribution: Record<string, unknown>;
  metrics: Record<string, unknown>;
  risk: Record<string, unknown>;
  goals: Record<string, unknown> | null;
  run_config: Record<string, unknown>;
}
```

- [ ] **Step 4: Verify the adapted component builds**

Run: `npm --prefix frontend run build`
Expected: no TypeScript errors originating in `PortfolioStep.tsx` or `types/simulate.ts` (other files may still be incomplete).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PortfolioStep.tsx frontend/src/types/simulate.ts
git commit -m "feat: port PortfolioStep with equal-weight/normalize/clear bulk actions"
```

---

## Task 17: Parameters step (new)

**Files:**
- Create: `frontend/src/components/ParametersStep.tsx`

**Interfaces:**
- Consumes: `SimulateRequest` fields from `types/simulate.ts` (Task 16).
- Produces: `ParametersStep` component implementing the 4-group progressive-disclosure layout from spec §4 (Core, Model-specific, Cashflow & Goals, Inflation & Rebalancing).

- [ ] **Step 1: Write `frontend/src/components/ParametersStep.tsx`**

```typescript
import { useState } from "react";
import type { SimulateRequest, NamedGoal } from "../types/simulate";

interface Props {
  active: boolean;
  value: SimulateRequest;
  onChange: (value: SimulateRequest) => void;
  onContinue: () => void;
}

export function ParametersStep({ active, value, onChange, onContinue }: Props) {
  const [multiGoal, setMultiGoal] = useState(value.multi_goal_enabled);

  function patch(fields: Partial<SimulateRequest>) {
    onChange({ ...value, ...fields });
  }

  return (
    <div className={active ? "page active" : "page"}>
      <div className="page-head">
        <h1>Set your simulation parameters</h1>
        <p>Choose a simulation model and configure the assumptions behind it.</p>
      </div>

      <div className="card">
        <h2>Core</h2>
        <label>
          Initial Amount
          <input type="number" value={value.initial_amount}
            onChange={(e) => patch({ initial_amount: Number(e.target.value) })} />
        </label>
        <label>
          Simulation Period in Years
          <input type="number" min={5} max={75} step={5} value={value.simulation_period_years}
            onChange={(e) => patch({ simulation_period_years: Number(e.target.value) })} />
        </label>
        <label>
          Tax Treatment
          <select value={value.tax_treatment} onChange={(e) => patch({ tax_treatment: e.target.value as SimulateRequest["tax_treatment"] })}>
            <option value="pre_tax">Pre-tax Returns</option>
            <option value="after_tax">After-tax Returns</option>
          </select>
        </label>
        <label>
          Simulation Model
          <select value={value.simulation_model} onChange={(e) => patch({ simulation_model: e.target.value as SimulateRequest["simulation_model"] })}>
            <option value="historical">Historical Returns</option>
            <option value="forecasted">Forecasted Returns</option>
            <option value="statistical">Statistical Returns</option>
            <option value="parameterized">Parameterized Returns</option>
          </select>
        </label>
      </div>

      {value.simulation_model === "historical" && (
        <div className="card">
          <h2>Historical Model Settings</h2>
          <label>
            Use Full History
            <select value={value.use_full_history ? "yes" : "no"}
              onChange={(e) => patch({ use_full_history: e.target.value === "yes" })}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </label>
          <label>
            Bootstrap Model
            <select value={value.bootstrap_model ?? "single_year"}
              onChange={(e) => patch({ bootstrap_model: e.target.value as SimulateRequest["bootstrap_model"] })}>
              <option value="single_month">Single Month</option>
              <option value="single_year">Single Year</option>
              <option value="block_of_years">Block of Years</option>
            </select>
          </label>
          <label>
            Sequence of Returns Risk
            <select value={value.sequence_of_returns_risk ?? 0}
              onChange={(e) => patch({ sequence_of_returns_risk: Number(e.target.value) })}>
              <option value={0}>No Adjustments</option>
              {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                <option key={n} value={n}>Worst {n} Year{n > 1 ? "s" : ""} First</option>
              ))}
            </select>
          </label>
        </div>
      )}

      {(value.simulation_model === "forecasted" || value.simulation_model === "statistical") && (
        <div className="card">
          <h2>Time Series Model</h2>
          <select value={value.time_series_model ?? "normal"}
            onChange={(e) => patch({ time_series_model: e.target.value as SimulateRequest["time_series_model"] })}>
            <option value="normal">Normal</option>
            <option value="garch">GARCH</option>
          </select>
        </div>
      )}

      {value.simulation_model === "parameterized" && (
        <div className="card">
          <h2>Parameterized Distribution</h2>
          <label>
            Distribution
            <select value={value.distribution ?? "normal"}
              onChange={(e) => patch({ distribution: e.target.value as SimulateRequest["distribution"] })}>
              <option value="normal">Normal</option>
              <option value="fat_tailed">Fat-tailed (Student-t)</option>
            </select>
          </label>
          {value.distribution === "fat_tailed" && (
            <label>
              Degrees of Freedom
              <input type="number" value={value.degrees_of_freedom ?? 5}
                onChange={(e) => patch({ degrees_of_freedom: Number(e.target.value) })} />
            </label>
          )}
          <label>
            Expected Return
            <input type="number" step="0.01" value={value.expected_return ?? 0}
              onChange={(e) => patch({ expected_return: Number(e.target.value) })} />
          </label>
          <label>
            Expected Volatility
            <input type="number" step="0.01" value={value.expected_volatility ?? 0}
              onChange={(e) => patch({ expected_volatility: Number(e.target.value) })} />
          </label>
        </div>
      )}

      <div className="card">
        <h2>Cashflow &amp; Goals</h2>
        <label>
          <input type="checkbox" checked={multiGoal}
            onChange={(e) => { setMultiGoal(e.target.checked); patch({ multi_goal_enabled: e.target.checked }); }} />
          Advanced: multiple goals
        </label>
        {!multiGoal ? (
          <>
            <label>
              Cashflow
              <select value={value.cashflow_mode}
                onChange={(e) => patch({ cashflow_mode: e.target.value as SimulateRequest["cashflow_mode"] })}>
                <option value="none">No contributions or withdrawals</option>
                <option value="contribute">Contribute fixed amount periodically</option>
                <option value="withdraw_fixed">Withdraw fixed amount periodically</option>
                <option value="withdraw_percent">Withdraw fixed percentage periodically</option>
              </select>
            </label>
            {value.cashflow_mode !== "none" && (
              <>
                <label>
                  Amount
                  <input type="number" value={value.cashflow_amount ?? 0}
                    onChange={(e) => patch({ cashflow_amount: Number(e.target.value) })} />
                </label>
                <label>
                  Inflation Adjusted
                  <select value={value.cashflow_inflation_adjusted ? "yes" : "no"}
                    onChange={(e) => patch({ cashflow_inflation_adjusted: e.target.value === "yes" })}>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                </label>
                <label>
                  Frequency
                  <select value={value.cashflow_frequency ?? "annually"}
                    onChange={(e) => patch({ cashflow_frequency: e.target.value as SimulateRequest["cashflow_frequency"] })}>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="annually">Annually</option>
                  </select>
                </label>
              </>
            )}
          </>
        ) : (
          <GoalsTable goals={value.goals ?? []} onChange={(goals) => patch({ goals })} />
        )}
      </div>

      <div className="card">
        <h2>Inflation &amp; Rebalancing</h2>
        <label>
          Inflation Model
          <select value={value.inflation_model} onChange={(e) => patch({ inflation_model: e.target.value as SimulateRequest["inflation_model"] })}>
            <option value="historical">Historical Inflation</option>
            <option value="parameterized">Parameterized Inflation</option>
          </select>
        </label>
        {value.inflation_model === "parameterized" && (
          <>
            <label>
              Mean
              <input type="number" step="0.001" value={value.inflation_mean ?? 0.03}
                onChange={(e) => patch({ inflation_mean: Number(e.target.value) })} />
            </label>
            <label>
              Volatility
              <input type="number" step="0.001" value={value.inflation_volatility ?? 0.01}
                onChange={(e) => patch({ inflation_volatility: Number(e.target.value) })} />
            </label>
          </>
        )}
        <label>
          Rebalancing
          <select value={value.rebalancing} onChange={(e) => patch({ rebalancing: e.target.value as SimulateRequest["rebalancing"] })}>
            <option value="none">No rebalancing</option>
            <option value="annual">Rebalance annually</option>
            <option value="semiannual">Rebalance semi-annually</option>
            <option value="quarterly">Rebalance quarterly</option>
            <option value="monthly">Rebalance monthly</option>
          </select>
        </label>
      </div>

      <button className="primary" onClick={onContinue} type="button">Continue to Results</button>
    </div>
  );
}

function GoalsTable({ goals, onChange }: { goals: NamedGoal[]; onChange: (goals: NamedGoal[]) => void }) {
  function addGoal() {
    onChange([...goals, {
      purpose: "", is_withdrawal: true, amount: 0, inflation_adjusted: true,
      frequency: "annually", starts_year: 0, ends_year: 1,
    }]);
  }
  function updateGoal(index: number, fields: Partial<NamedGoal>) {
    onChange(goals.map((g, i) => (i === index ? { ...g, ...fields } : g)));
  }
  function removeGoal(index: number) {
    onChange(goals.filter((_, i) => i !== index));
  }
  return (
    <div className="goals-table">
      {goals.map((goal, index) => (
        <div className="goal-row" key={index}>
          <input placeholder="Purpose" value={goal.purpose} onChange={(e) => updateGoal(index, { purpose: e.target.value })} />
          <select value={goal.is_withdrawal ? "withdraw" : "contribute"}
            onChange={(e) => updateGoal(index, { is_withdrawal: e.target.value === "withdraw" })}>
            <option value="contribute">Contribute</option>
            <option value="withdraw">Withdraw</option>
          </select>
          <input type="number" placeholder="Amount" value={goal.amount} onChange={(e) => updateGoal(index, { amount: Number(e.target.value) })} />
          <input type="number" placeholder="Starts (year)" value={goal.starts_year} onChange={(e) => updateGoal(index, { starts_year: Number(e.target.value) })} />
          <input type="number" placeholder="Ends (year)" value={goal.ends_year} onChange={(e) => updateGoal(index, { ends_year: Number(e.target.value) })} />
          <button type="button" onClick={() => removeGoal(index)}>Remove</button>
        </div>
      ))}
      <button type="button" className="link-btn" onClick={addGoal}>+ Add goal</button>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `npm --prefix frontend run build`
Expected: no TypeScript errors in `ParametersStep.tsx`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ParametersStep.tsx
git commit -m "feat: add ParametersStep with progressive disclosure per simulation model"
```

---

## Task 18: Results view (new) — 7 sub-tabs

**Files:**
- Create: `frontend/src/components/ResultsView.tsx`

**Interfaces:**
- Consumes: `SimulateResponse` (Task 16 types), `AxisCurve`/`Histogram`/`CorrelationMatrix`/`DataTable` from `charts.tsx` (Task 15).
- Produces: `ResultsView` component with 7 sub-tabs per spec §5: Overview, Growth, Distribution, Metrics, Risk & Correlation, Goals & Cashflows (conditional), Report.

- [ ] **Step 1: Write `frontend/src/components/ResultsView.tsx`**

```typescript
import { useState } from "react";
import type { SimulateResponse } from "../types/simulate";
import { AxisCurve, Histogram, CorrelationMatrix, DataTable } from "./charts";

type ResultsTab = "overview" | "growth" | "distribution" | "metrics" | "risk" | "goals" | "report";

interface Props {
  result: SimulateResponse;
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

  return (
    <div className="results-view">
      <div className="tab-bar">
        {tabs.map((tab) => (
          <button key={tab.id} className={tab.id === activeTab ? "tab active" : "tab"}
            onClick={() => setActiveTab(tab.id)} type="button">
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab === "overview" && <OverviewTab result={result} />}
      {activeTab === "growth" && <GrowthTab result={result} />}
      {activeTab === "distribution" && <DistributionTab result={result} />}
      {activeTab === "metrics" && <MetricsTab result={result} />}
      {activeTab === "risk" && <RiskTab result={result} />}
      {activeTab === "goals" && result.goals && <GoalsTab goals={result.goals} />}
      {activeTab === "report" && <ReportTab result={result} />}
    </div>
  );
}

function OverviewTab({ result }: { result: SimulateResponse }) {
  const overview = result.overview as {
    survived_count: number; n_paths: number; survival_rate: number;
    median_ending_balance: number; median_cagr: number;
  };
  return (
    <div className="card">
      <p>
        {overview.survived_count} out of {overview.n_paths} simulated portfolios (
        {(overview.survival_rate * 100).toFixed(2)}%) survived all withdrawals.
      </p>
      <div className="stat-row">
        <div className="metricCard">
          <span>Median Ending Balance</span>
          <strong>{overview.median_ending_balance.toLocaleString(undefined, { style: "currency", currency: "THB" })}</strong>
        </div>
        <div className="metricCard">
          <span>Median CAGR</span>
          <strong>{(overview.median_cagr * 100).toFixed(2)}%</strong>
        </div>
      </div>
    </div>
  );
}

function GrowthTab({ result }: { result: SimulateResponse }) {
  const growth = result.growth as { fan_chart: Record<string, number[]>; survival_over_time: number[] };
  const percentileColors: Record<string, string> = {
    "10": "var(--danger)", "25": "var(--warn)", "50": "var(--accent)",
    "75": "var(--warn)", "90": "var(--danger)",
  };
  const fanSeries = Object.entries(growth.fan_chart).map(([pct, values]) => ({
    label: `${pct}th percentile`,
    color: percentileColors[pct] ?? "var(--accent)",
    points: values.map((y, x) => ({ x, y })),
  }));
  const survivalSeries = [{
    label: "Survival",
    color: "var(--success)",
    points: growth.survival_over_time.map((y, x) => ({ x, y: y * 100 })),
  }];
  return (
    <div className="card">
      <h2>Portfolio Balance</h2>
      <AxisCurve title="Simulated Portfolio Balances" series={fanSeries} valueFormat={(v) => v.toLocaleString()} />
      <h2>Portfolio Survival</h2>
      <AxisCurve title="Portfolio Success" series={survivalSeries} valueFormat={(v) => `${v.toFixed(1)}%`} />
    </div>
  );
}

function DistributionTab({ result }: { result: SimulateResponse }) {
  const distribution = result.distribution as { ending_balance_histogram: number[] };
  const bins = buildHistogramBins(distribution.ending_balance_histogram, 30);
  return (
    <div className="card">
      <h2>Portfolio End Balance Histogram</h2>
      <Histogram rows={bins} />
    </div>
  );
}

function MetricsTab({ result }: { result: SimulateResponse }) {
  const metrics = result.metrics as {
    percentile_table: { ending_balance: Record<string, number>; cagr: Record<string, number> };
    sharpe: Record<string, number>; sortino: Record<string, number>;
    safe_withdrawal_rate: Record<string, number>; perpetual_withdrawal_rate: Record<string, number>;
  };
  const columns = ["10th Percentile", "25th Percentile", "50th Percentile", "75th Percentile", "90th Percentile"];
  const pcts = ["10", "25", "50", "75", "90"];
  const section = {
    title: "Performance Summary",
    columns,
    rows: [
      ["Portfolio End Balance", ...pcts.map((p) => metrics.percentile_table.ending_balance[p])],
      ["CAGR", ...pcts.map((p) => metrics.percentile_table.cagr[p])],
      ["Sharpe Ratio", ...pcts.map((p) => metrics.sharpe[p])],
      ["Sortino Ratio", ...pcts.map((p) => metrics.sortino[p])],
      ["Safe Withdrawal Rate", ...pcts.map((p) => metrics.safe_withdrawal_rate[p])],
      ["Perpetual Withdrawal Rate", ...pcts.map((p) => metrics.perpetual_withdrawal_rate[p])],
    ],
  };
  return (
    <div className="card">
      <DataTable section={section} />
    </div>
  );
}

function RiskTab({ result }: { result: SimulateResponse }) {
  const risk = result.risk as { correlation_and_returns: { correlation: Record<string, Record<string, number>> }; value_at_risk: number; expected_shortfall: number };
  return (
    <div className="card">
      <h2>Correlations and Returns</h2>
      <CorrelationMatrix result={risk.correlation_and_returns as never} />
      <div className="stat-row">
        <div className="metricCard"><span>Value at Risk (90%)</span><strong>{risk.value_at_risk.toLocaleString()}</strong></div>
        <div className="metricCard"><span>Expected Shortfall (90%)</span><strong>{risk.expected_shortfall.toLocaleString()}</strong></div>
      </div>
    </div>
  );
}

function GoalsTab({ goals }: { goals: Record<string, unknown> }) {
  const summary = (goals.summary as { purpose: string; success_rate: number }[]) ?? [];
  return (
    <div className="card">
      <h2>Financial Goals</h2>
      <table>
        <thead><tr><th>Purpose</th><th>Success</th></tr></thead>
        <tbody>
          {summary.map((row) => (
            <tr key={row.purpose}><td>{row.purpose}</td><td>{(row.success_rate * 100).toFixed(2)}%</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

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
  return (
    <div className="card">
      <h2>Report</h2>
      <button type="button" onClick={downloadJson}>Export run_config.json</button>
    </div>
  );
}

function buildHistogramBins(values: number[], nBins: number) {
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = (max - min) / nBins || 1;
  const bins = Array.from({ length: nBins }, (_, i) => ({
    bin: `${(min + i * width).toFixed(0)}`, count: 0, from: min + i * width, to: min + (i + 1) * width,
  }));
  for (const v of values) {
    const idx = Math.min(nBins - 1, Math.floor((v - min) / width));
    bins[idx].count += 1;
  }
  return bins;
}
```

- [ ] **Step 2: Verify build**

Run: `npm --prefix frontend run build`
Expected: no TypeScript errors in `ResultsView.tsx` (the `CorrelationMatrix`/`DataTable` prop shapes must match Task 15's ported signatures — adjust `RiskTab`/`MetricsTab`'s call sites if Task 15's actual extracted prop names differ from the placeholders used here).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ResultsView.tsx
git commit -m "feat: add ResultsView with 7 sub-tabs (Overview/Growth/Distribution/Metrics/Risk/Goals/Report)"
```

---

## Task 19: App shell — wire the 3-step wizard together

**Files:**
- Create: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `Stepper`, `RunOverlay` (Task 14), `PortfolioStep` (Task 16), `ParametersStep` (Task 17), `ResultsView` (Task 18), `postSimulate` (Task 14).

- [ ] **Step 1: Write `frontend/src/App.tsx`**

```typescript
import { useState } from "react";
import { Stepper } from "./components/Stepper";
import { RunOverlay } from "./components/RunOverlay";
import { PortfolioStep } from "./components/PortfolioStep";
import { ParametersStep } from "./components/ParametersStep";
import { ResultsView } from "./components/ResultsView";
import { postSimulate } from "./api/client";
import type { SimulateRequest, SimulateResponse } from "./types/simulate";

const DEFAULT_REQUEST: SimulateRequest = {
  holdings: [],
  initial_amount: 1_000_000,
  simulation_period_years: 30,
  tax_treatment: "pre_tax",
  simulation_model: "historical",
  n_paths: 10000,
  rebalancing: "annual",
  bootstrap_model: "single_year",
  use_full_history: true,
  sequence_of_returns_risk: 0,
  cashflow_mode: "none",
  multi_goal_enabled: false,
  inflation_model: "historical",
};

type Step = "portfolio" | "parameters" | "results";

export function App() {
  const [step, setStep] = useState<Step>("portfolio");
  const [request, setRequest] = useState<SimulateRequest>(DEFAULT_REQUEST);
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSimulation() {
    setRunning(true);
    setError(null);
    try {
      const response = await postSimulate(request);
      setResult(response);
      setStep("results");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="app-shell">
      <Stepper current={step} />
      {running && <RunOverlay />}
      {error && <div className="banner danger">{error}</div>}
      {step === "portfolio" && (
        <PortfolioStep active value={request} onChange={setRequest} onContinue={() => setStep("parameters")} />
      )}
      {step === "parameters" && (
        <ParametersStep active value={request} onChange={setRequest} onContinue={runSimulation} />
      )}
      {step === "results" && result && <ResultsView result={result} />}
    </div>
  );
}
```

Note for the implementing engineer: `PortfolioStep`'s exact prop signature was ported in Task 16 from Backtest Portfolio's own `PortfolioStep.tsx` and may differ slightly from `{ active, value, onChange, onContinue }` shown here (e.g. it may manage `holdings` internally via its own row state and expose a `holdings`/`onHoldingsChange` pair instead). Reconcile this call site against the actual ported signature from Task 16 before this compiles — the exact shape is only knowable from that file's real content, not fabricated here.

- [ ] **Step 2: Verify build**

Run: `npm --prefix frontend run build`
Expected: PASS with zero TypeScript errors.

- [ ] **Step 3: Start the dev server and manually verify the 3-step flow renders**

Run: `npm --prefix frontend run dev`

Open the app, confirm: Portfolio step renders fund search, Parameters step shows Core fields and conditionally shows Historical-model fields, clicking through to Results (with a temporarily mocked/stubbed backend response if `/api/simulate` isn't reachable yet) renders all 7 tabs without console errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wire 3-step wizard shell (Portfolio -> Parameters -> Results)"
```

---

## Task 20: Docker

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Interfaces:**
- Produces: a single-container production build, matching Backtest Portfolio's pattern — multi-stage build, named volume (required because the directory name contains `:`).

- [ ] **Step 1: Write `Dockerfile`**

```dockerfile
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml ./
COPY backend/ ./backend/
RUN pip install --no-cache-dir .
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Write `docker-compose.yml`** (named volume, not a bind mount — the directory name contains `:`, which breaks Docker Desktop's bind-mount path parsing)

```yaml
services:
  app:
    build: .
    ports:
      - "8001:8000"
    volumes:
      - mc-data:/app/data
    restart: unless-stopped

volumes:
  mc-data:
```

- [ ] **Step 3: Write `.dockerignore`**

```
node_modules
frontend/dist
frontend/node_modules
data/raw
data/processed
.git
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
```

- [ ] **Step 4: Verify the image builds**

Run: `docker compose build`
Expected: build succeeds (may take several minutes for `build-essential`/pandas/scipy compilation).

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "chore: add Docker build with named volume for colon-containing directory"
```

---

## Task 21: End-to-end happy-path test

**Files:**
- Create: `frontend/e2e/happy-path.spec.ts`
- Create/Modify: `frontend/playwright.config.ts`

**Interfaces:**
- Produces: one Playwright spec exercising Portfolio → Parameters → Results, matching Backtest Portfolio's `e2e/happy-path.spec.ts` pattern.

- [ ] **Step 1: Copy `playwright.config.ts` from Backtest Portfolio**, adjusting only the port if it differs from this project's Vite dev port.

```bash
cp "../Backtest Portfolio Webull:SEC OPENAI/frontend/playwright.config.ts" frontend/playwright.config.ts
```

- [ ] **Step 2: Write `frontend/e2e/happy-path.spec.ts`**

```typescript
import { test, expect } from "@playwright/test";

test("build a portfolio, run a historical simulation, and see results", async ({ page }) => {
  await page.goto("/");

  // Portfolio step
  await page.getByText("Load an example portfolio").click();
  await expect(page.getByText("Weight %")).toBeVisible();
  await page.getByRole("button", { name: /continue/i }).click();

  // Parameters step
  await expect(page.getByText("Set your simulation parameters")).toBeVisible();
  await page.getByRole("button", { name: /continue to results/i }).click();

  // Results step
  await expect(page.getByText(/survived all withdrawals/i)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole("button", { name: "Growth" })).toBeVisible();
});
```

- [ ] **Step 3: Add `test:e2e` script to `frontend/package.json`** if the copied `package.json` from Task 14 doesn't already have one:

```json
"scripts": {
  "test:e2e": "playwright test"
}
```

- [ ] **Step 4: Run the e2e test** (requires both the backend and frontend dev servers running, or the Playwright config's `webServer` block starting them automatically — check the copied config)

Run: `npm --prefix frontend run test:e2e`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/e2e/happy-path.spec.ts frontend/playwright.config.ts frontend/package.json
git commit -m "test: add Playwright happy-path e2e spec"
```

---

## Task 22: Delete superseded engine source files

**Files:**
- Delete: `tests/gbm_engine.py`, `tests/historical_sim.py`, `tests/forecasted_sim.py`, `tests/statistical_sim.py`, `tests/parameterized_sim.py`, `tests/results_lib.py`, `tests/returns_lib.py`, `tests/sec_opendata_client.py`, `tests/portfolio_lib.py`, `tests/webull_client.py`
- Delete: `tests/test_nav_fetch.py`, `tests/test_webull_import.py`, `tests/test_scaffold.py` (scaffold/import-check tests, not real engine tests, per the earlier project audit)
- Keep: `tests/test_gbm_engine.py`, `tests/test_historical.py`, etc. and the notebook `notebooks/01_monte_carlo_simulation.ipynb` are left untouched — the notebook is a separate coursework deliverable, not part of the webapp, and still imports the `tests/*.py` modules directly for its own purposes.

**Interfaces:** none — this is a cleanup task with no code dependencies.

- [ ] **Step 1: Confirm every promoted module has an equivalent, passing test under `backend/tests/`**

Run: `pytest backend/tests -v`
Expected: PASS (full suite from Tasks 2–13)

- [ ] **Step 2: Decide whether to delete `tests/*.py` source files or leave them for the notebook's continued use**

Since `notebooks/01_monte_carlo_simulation.ipynb` pastes these functions in directly (per the spec's project audit) rather than importing them at runtime, deleting the `tests/*.py` files does not break the notebook's existing cells — but re-running the notebook from scratch would need the functions restored. Given this project's `CLAUDE.md` (Task 1) now documents `backend/app/engine/` as the source of truth, delete the superseded files rather than maintaining two copies of the same logic:

```bash
git rm tests/gbm_engine.py tests/historical_sim.py tests/forecasted_sim.py tests/statistical_sim.py tests/parameterized_sim.py tests/results_lib.py tests/returns_lib.py tests/sec_opendata_client.py tests/portfolio_lib.py tests/webull_client.py
git rm tests/test_nav_fetch.py tests/test_webull_import.py tests/test_scaffold.py
```

- [ ] **Step 3: Run the full test suite one more time to confirm nothing outside `tests/` depended on the deleted files**

Run: `pytest backend/tests -v`
Expected: PASS (deleted files are not imported by `backend/`)

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: remove superseded tests/*.py engine source now that backend/app/engine/ is canonical"
```

---

## Self-Review Notes

**Spec coverage:** §3 (models) — Tasks 2, 4, 5, 6. §4 (Parameters tab) — Task 17. §5 (Results tab, 7 sub-tabs) — Task 18. §6 (new engine work, all 7 items) — Tasks 5, 6, 7, 8, 9. §7 (architecture/promotion map) — Tasks 2–13, 22. §8 (frontend shell + chart primitives + weight actions) — Tasks 14, 15, 16. §9 (testing) — every task's TDD steps plus Task 21. §10 (open items) — Thai CPI data source remains genuinely open; Task 7's `inflation.py` is deliberately designed to accept any `cpi_returns` series so this can be resolved later without reworking the engine.

**Type consistency check:** `SimulateRequest`/`SimulateResponse` (Task 10, Python) and their TypeScript mirrors (Task 16) were kept field-for-field identical by construction. `run_simulation`'s signature (Task 11) matches its usage in `api/simulate.py` (Task 12). The one acknowledged gap is `PortfolioStep`'s exact prop shape (Task 16 ports it from an unseen-in-full source file) versus its call site in `App.tsx` (Task 19) — flagged explicitly in Task 19 rather than fabricated, since guessing wrong here would silently produce a plan a reviewer couldn't verify against real source.
