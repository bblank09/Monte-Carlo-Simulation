# Notebook 01 — Monte Carlo Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline, interactive) to implement this plan task-by-task. **DO NOT use subagent-driven-development** — spec section 10 ("Implementation Mode") explicitly forbids dispatching a subagent to bulk-produce the notebook. Every task must be executed in the main conversation, one section at a time, with a markdown explanation of the equation BEFORE the code that implements it, and a pause for the user to confirm understanding before moving to the next task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `notebooks/01_monte_carlo_simulation.ipynb` — a stand-alone, professionally-written Jupyter notebook that replicates every input/output field of [Portfolio Visualizer's Monte Carlo Simulation tool](https://www.portfoliovisualizer.com/monte-carlo-simulation), using a portfolio of real Thai stocks (Webull TH) + Thai mutual funds (SEC Open Data), with every equation derived from CQF Module 1-2 before it is coded.

**Architecture:** Data acquisition (SEC Open Data REST API + Webull TH CSV export) → return/covariance estimation → GBM/Euler simulation engine (with GARCH(1,1) volatility option) → Markowitz portfolio construction → 4 PV-parity simulation models (Historical/Forecasted/Statistical/Parameterized) → percentile/VaR/ES results → live benchmark against portfoliovisualizer.com.

**Tech Stack:** Python 3, `numpy`, `pandas`, `scipy`, `matplotlib`, `arch` (GARCH), `riskfolio-lib` (cross-check only), `requests` (SEC API), `python-dotenv` (secrets), Jupyter.

## Global Constraints

- Notebook must be stand-alone: no `import` from any file outside itself (per spec section 2). Helper functions live in notebook cells, not in a shared `.py` module the notebook imports at runtime.
- Every equation gets a markdown cell explaining its derivation from `learn.cqf/CQF Module 1-2 Master Overview.md` **before** the code cell that implements it.
- All Portfolio Visualizer input fields (spec section 5.1 full list) must appear in one editable `CONFIG` dict — never hardcoded inline.
- Secrets (SEC Open Data API key, Webull App Key/Secret) load from a local `.env` file via `python-dotenv` — **never** hardcoded in the notebook or committed to git.
- Development-time verification: for every numerical function, first prove it correct with a quick `assert`-based check in a scratch cell/script under `tests/` (deletable, not part of the shipped notebook), then paste the verified code into the notebook cell.
- Follow the notebook template from spec section 4 exactly (Intro → Theoretical Background → Methodology → Implementation → Results → Discussion → Conclusion → Appendix).

---

## Task 1: Project Scaffolding & Secrets

**Files:**
- Create: `data/raw/.gitkeep`, `data/processed/.gitkeep`
- Create: `notebooks/01_monte_carlo_simulation.ipynb` (empty skeleton with markdown section headers only, no content yet)
- Create: `benchmarks/monte_carlo/.gitkeep`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `tests/test_scaffold.py`

**Interfaces:**
- Produces: directory layout every later task writes into; `.env` variable names `SEC_OPENDATA_API_KEY`, `WEBULL_APP_KEY`, `WEBULL_APP_SECRET` that Task 2/4 read.

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p "data/raw" "data/processed" "notebooks" "benchmarks/monte_carlo" "tests"
touch "data/raw/.gitkeep" "data/processed/.gitkeep" "benchmarks/monte_carlo/.gitkeep"
```

- [ ] **Step 2: Write `.env.example` (template — the real `.env` with actual secrets is never committed)**

```
SEC_OPENDATA_API_KEY=your_sec_opendata_key_here
WEBULL_APP_KEY=your_webull_app_key_here
WEBULL_APP_SECRET=your_webull_app_secret_here
```

Then create the real `.env` (copy of the template, fill in your actual SEC Open Data key that you already obtained):

```bash
cp .env.example .env
```

Edit `.env` by hand and paste the real key after `SEC_OPENDATA_API_KEY=`.

- [ ] **Step 3: Write `.gitignore`**

```
.env
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
.ipynb_checkpoints/
__pycache__/
```

- [ ] **Step 4: Write the failing test — confirm `.env` loads and required keys exist**

`tests/test_scaffold.py`:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

def test_env_has_sec_key():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    assert os.environ.get("SEC_OPENDATA_API_KEY"), "SEC_OPENDATA_API_KEY missing from .env"

def test_directory_layout_exists():
    root = Path(__file__).resolve().parent.parent
    for p in ["data/raw", "data/processed", "notebooks", "benchmarks/monte_carlo"]:
        assert (root / p).is_dir(), f"missing directory: {p}"
```

- [ ] **Step 5: Install dependencies and run the test**

```bash
pip install python-dotenv pandas numpy scipy matplotlib arch riskfolio-lib requests pytest jupyter
pytest tests/test_scaffold.py -v
```

Expected: both tests PASS (if `SEC_OPENDATA_API_KEY` test fails, go fill in `.env` first).

- [ ] **Step 6: Create the notebook skeleton**

Create `notebooks/01_monte_carlo_simulation.ipynb` with markdown-only cells, no code yet, in this exact order (matches spec section 4 template):

```
# Monte Carlo Simulation — Portfolio Growth & Survival (Thai Stocks + Funds)
## Executive Summary
(one paragraph, fill in after Task 14)
## 1. Introduction
## 2. Theoretical Background
## 3. Methodology
### 3.1 Data Source & Acquisition
### 3.2 Parameter Estimation
### 3.3 Portfolio Construction
### 3.4 Simulation Model Configuration
### 3.5 Algorithm Summary
## 4. Implementation
## 5. Results
### 5.1 Output
### 5.2 Benchmark Comparison
## 6. Discussion
## 7. Conclusion & Limitations
## Appendix
```

- [ ] **Step 7: Commit**

```bash
git add -A -- ':!.env'
git commit -m "chore: scaffold project structure and notebook skeleton for 01_monte_carlo_simulation"
```

(If this is not yet a git repo, run `git init` first and confirm with the user before committing.)

---

## Task 2: SEC Open Data — Fund Discovery

**Files:**
- Create: `tests/test_sec_api.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (add cells under section 3.1)

**Interfaces:**
- Consumes: `SEC_OPENDATA_API_KEY` from `.env` (Task 1)
- Produces: `find_equity_funds(search_term: str, page_size: int = 20) -> list[dict]` — each dict has `proj_id`, `name_th`, `name_en` — used by Task 3

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sec_api.py
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
API_KEY = os.environ["SEC_OPENDATA_API_KEY"]
BASE_URL = "https://api.sec.or.th/FundFactsheet/fund"  # verify exact base host in Step 2 below before trusting this

def test_can_list_amcs():
    from sec_opendata_client import get_amcs
    amcs = get_amcs()
    assert isinstance(amcs, list)
    assert len(amcs) > 0
    assert "company_name_th" in amcs[0]
```

- [ ] **Step 2: Confirm the real base URL and header name for the API key**

Before writing `sec_opendata_client.py`, open a browser to `https://secopendata.sec.or.th/sec-open-apis?user=user&type=user-intro&id=ug-what-is`, log in with the account you registered, and find the "API Key" or "Ocp-Apim-Subscription-Key" section of your account dashboard (SEC Open Data's platform is Azure API Management, so the header is very likely `Ocp-Apim-Subscription-Key: <your key>` rather than `Authorization: Bearer`). Copy the exact base URL shown there (e.g. `https://api.sec.or.th` or similar) — **do not guess**; paste it into `sec_opendata_client.py` in Step 3.

- [ ] **Step 3: Write `sec_opendata_client.py` as a scratch verification script (not part of the notebook yet)**

`tests/sec_opendata_client.py`:
```python
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
API_KEY = os.environ["SEC_OPENDATA_API_KEY"]
BASE_URL = "https://api.sec.or.th"  # replace with the exact host confirmed in Step 2

def _headers():
    return {"Ocp-Apim-Subscription-Key": API_KEY}

def get_amcs():
    resp = requests.get(f"{BASE_URL}/v2/fund/general-info/amcs", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()["items"]

def find_equity_funds(search_term: str, page_size: int = 20):
    params = {"search": search_term, "page_size": page_size}
    resp = requests.get(f"{BASE_URL}/v2/fund/general-info/profiles", headers=_headers(), params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["items"]
```

- [ ] **Step 4: Run the test**

```bash
pytest tests/test_sec_api.py -v
```

Expected: PASS with a real list of AMCs. If you get `401`, the header name or base URL from Step 2 is wrong — re-check the account dashboard. If you get `403`, the key hasn't propagated yet (Azure APIM keys can take a few minutes to activate).

- [ ] **Step 5: Use `find_equity_funds` to pick 2 real Thai equity funds**

Run interactively (e.g. in a Python REPL or scratch notebook cell) — not a permanent test:
```python
from sec_opendata_client import find_equity_funds
candidates = find_equity_funds("หุ้น", page_size=20)
for c in candidates[:20]:
    print(c.get("proj_id"), c.get("fund_name_th") or c.get("name_th"))
```

Read the printed list with the user, pick 2 fund `proj_id` values together (equity funds with long history preferred), and write them down — they are pasted into `CONFIG` in Task 9.

- [ ] **Step 6: Copy the verified client code into the notebook (section 3.1)**

Add a code cell to `notebooks/01_monte_carlo_simulation.ipynb` with the exact working `_headers`, `get_amcs`, `find_equity_funds` functions from Step 3 (with the confirmed `BASE_URL`), preceded by a markdown cell explaining: SEC Open Data is the Thai regulator's public dataset, `/v2/fund/general-info/profiles` returns fund metadata, `proj_id` is the primary key used by every other Fund endpoint.

- [ ] **Step 7: Commit**

```bash
git add tests/test_sec_api.py tests/sec_opendata_client.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: add SEC Open Data fund discovery client"
```

---

## Task 3: SEC Open Data — Daily NAV Fetch

**Files:**
- Create: `tests/test_nav_fetch.py`
- Modify: `tests/sec_opendata_client.py` (add `get_daily_nav`)
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 3.1)
- Create: `data/raw/sec_fund_nav.csv` (generated by running the notebook cell, not hand-written)

**Interfaces:**
- Consumes: `proj_id` values chosen in Task 2, `_headers()` from Task 2
- Produces: `get_daily_nav(proj_id: str, start_date: str, end_date: str) -> pd.DataFrame` with columns `nav_date, proj_id, last_val`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_nav_fetch.py
from sec_opendata_client import get_daily_nav

def test_get_daily_nav_returns_dataframe(monkeypatch=None):
    df = get_daily_nav("M0000_2552", "2024-01-01", "2024-01-31")  # replace with a proj_id chosen in Task 2
    assert list(df.columns) == ["nav_date", "proj_id", "last_val"]
    assert len(df) > 0
    assert df["last_val"].dtype.kind == "f"
```

- [ ] **Step 2: Implement `get_daily_nav` in `tests/sec_opendata_client.py`**

```python
import pandas as pd

def get_daily_nav(proj_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    items = []
    cursor = None
    while True:
        params = {
            "proj_id": proj_id,
            "start_nav_date": start_date,
            "end_nav_date": end_date,
            "page_size": 100,
        }
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

- [ ] **Step 3: Run the test**

```bash
pytest tests/test_nav_fetch.py -v
```

Expected: PASS. If `items` is empty, the `proj_id` or date range is wrong — verify the fund actually has NAV history in that window via `find_equity_funds`.

- [ ] **Step 4: Fetch and cache real NAV data for both chosen funds (5-year window)**

Run interactively:
```python
import pandas as pd
from sec_opendata_client import get_daily_nav

fund_ids = ["<proj_id_1>", "<proj_id_2>"]  # from Task 2 Step 5
frames = [get_daily_nav(pid, "2020-01-01", "2025-12-31") for pid in fund_ids]
nav_df = pd.concat(frames, ignore_index=True)
nav_df.to_csv("data/raw/sec_fund_nav.csv", index=False)
print(nav_df.groupby("proj_id")["nav_date"].agg(["min", "max", "count"]))
```

Confirm each fund has at least 3 years of daily data before proceeding — if not, pick a different fund in Task 2.

- [ ] **Step 5: Copy the verified `get_daily_nav` function into the notebook (section 3.1), with a markdown cell explaining `nav_date`/`last_val`/`proj_id` and why NAV-per-unit is the fund equivalent of a stock's closing price**

- [ ] **Step 6: Commit**

```bash
git add tests/test_nav_fetch.py tests/sec_opendata_client.py data/raw/sec_fund_nav.csv notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: fetch and cache daily NAV for 2 Thai equity funds"
```

---

## Task 4: Webull TH — Stock Price Import

**Files:**
- Create: `data/raw/webull_prices.csv` (manually exported by the user, not generated by code)
- Create: `tests/test_webull_import.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 3.1)

**Interfaces:**
- Produces: `load_webull_prices(csv_path: str) -> pd.DataFrame` with columns `date, ticker, close`

**Note on scope (updated after actual implementation):** Webull TH's OpenAPI (`webull-openapi-python-sdk`, region `"th"`, `Category.US_ETF`/`Timespan.D`) was implemented and worked on the first call, but token verification proved unreliable on repeat calls — `ERROR_CHECK_TOKEN status:EXPIRED` on 3 of 4 total attempts, even after pinning the token directory to an absolute path via `set_token_dir()`. Switched to **`yfinance`** as the data source for SPY/QQQ/TLT — verified prices match what Webull returned (SPY close 2026-07-24: 738.93 both sources), so this is a reliability substitution, not a data-quality one.

**Revised asset choice (confirmed with user):** originally planned to use Thai SET-listed stocks, but switched to **US-listed tickers via Webull TH's US market access** instead — Webull TH supports trading US stocks/ETFs, and using US tickers means they can be entered directly into Portfolio Visualizer for a true asset-to-asset benchmark comparison in Task 15 (SEC Open Data funds still can't be compared directly since PV has no Thai fund data — see spec section 7). Confirmed tickers: **SPY** (S&P 500 ETF), **QQQ** (Nasdaq 100 ETF), **TLT** (20+ Year Treasury Bond ETF) — chosen for visible diversification (equity market + bonds, low/negative correlation expected between SPY/QQQ and TLT).

- [ ] **Step 1: Export daily closing price history for SPY, QQQ, TLT from Webull TH**

In the Webull TH app or web chart, search each ticker, switch its chart to daily candles, 5-year range, and export/copy the data.

- [ ] **Step 2: Save as `data/raw/webull_prices.csv` with this exact schema**

```csv
date,ticker,close
2020-01-02,SPY,321.55
2020-01-03,SPY,321.00
...
2020-01-02,QQQ,213.91
...
2020-01-02,TLT,143.65
...
```

(One row per ticker per trading day. `date` in `YYYY-MM-DD`, `close` as a plain float.)

- [ ] **Step 3: Write the failing test**

```python
# tests/test_webull_import.py
import pandas as pd

def test_load_webull_prices_schema():
    from webull_loader import load_webull_prices
    df = load_webull_prices("data/raw/webull_prices.csv")
    assert list(df.columns) == ["date", "ticker", "close"]
    assert df["ticker"].nunique() == 3
    assert df.groupby("ticker")["date"].count().min() > 500  # roughly 2+ years of trading days per ticker
```

- [ ] **Step 4: Implement `webull_loader.py`**

```python
# tests/webull_loader.py
import pandas as pd

def load_webull_prices(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    assert set(df.columns) == {"date", "ticker", "close"}
    return df.sort_values(["ticker", "date"]).reset_index(drop=True)
```

- [ ] **Step 5: Run the test**

```bash
pytest tests/test_webull_import.py -v
```

Expected: PASS. If `nunique() != 3` or row counts are too low, the CSV export from Step 2 is incomplete — go back and export more history or check all 3 tickers were included.

- [ ] **Step 6: Copy the verified `load_webull_prices` function into the notebook (section 3.1), with a markdown cell explaining why this project mixes an API-fetched asset class (SEC funds) with a manually-exported one (Webull stocks), and noting the OpenAPI automation path as a stated limitation**

- [ ] **Step 7: Commit**

```bash
git add tests/test_webull_import.py tests/webull_loader.py data/raw/webull_prices.csv notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: import Webull TH stock prices (manual CSV export)"
```

---

## Task 5: Return Matrix, μ, Σ Estimation

**Files:**
- Create: `tests/test_returns.py`, `tests/returns_lib.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 3.2)

**Interfaces:**
- Consumes: `nav_df` (Task 3), `webull_df` (Task 4) — both have a date column and a price-like column
- Produces: `build_price_panel(nav_df, webull_df) -> pd.DataFrame` (dates × 5 asset columns, forward-filled to a common daily index), `log_returns(price_panel) -> pd.DataFrame`, `estimate_mu_sigma(returns_df, periods_per_year=252) -> tuple[np.ndarray, np.ndarray]` (annualized mean vector, annualized covariance matrix)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_returns.py
import numpy as np
import pandas as pd

def test_log_returns_and_moments():
    from returns_lib import log_returns, estimate_mu_sigma
    dates = pd.date_range("2024-01-01", periods=252, freq="B")
    rng = np.random.default_rng(42)
    prices = pd.DataFrame({
        "A": 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, 252))),
        "B": 50 * np.exp(np.cumsum(rng.normal(0.0002, 0.015, 252))),
    }, index=dates)
    rets = log_returns(prices)
    assert rets.shape == (251, 2)
    mu, sigma = estimate_mu_sigma(rets, periods_per_year=252)
    assert mu.shape == (2,)
    assert sigma.shape == (2, 2)
    assert np.allclose(sigma, sigma.T)  # covariance matrix must be symmetric
    assert np.all(np.linalg.eigvalsh(sigma) >= -1e-10)  # positive semi-definite
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_returns.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'returns_lib'`

- [ ] **Step 3: Implement `tests/returns_lib.py`**

```python
import numpy as np
import pandas as pd

def build_price_panel(nav_df: pd.DataFrame, webull_df: pd.DataFrame) -> pd.DataFrame:
    nav_wide = nav_df.pivot(index="nav_date", columns="proj_id", values="last_val")
    webull_wide = webull_df.pivot(index="date", columns="ticker", values="close")
    panel = nav_wide.join(webull_wide, how="outer").sort_index()
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

- [ ] **Step 4: Run the test again**

```bash
pytest tests/test_returns.py -v
```

Expected: PASS

- [ ] **Step 5: Run on the real combined data and cache the result**

```python
from returns_lib import build_price_panel, log_returns, estimate_mu_sigma
import pandas as pd

nav_df = pd.read_csv("data/raw/sec_fund_nav.csv", parse_dates=["nav_date"])
webull_df = pd.read_csv("data/raw/webull_prices.csv", parse_dates=["date"])
panel = build_price_panel(nav_df, webull_df)
rets = log_returns(panel)
mu, sigma = estimate_mu_sigma(rets)
panel.to_csv("data/processed/price_panel.csv")
rets.to_csv("data/processed/log_returns.csv")
print("mu (annual):", mu)
print("sigma (annual):\n", sigma)
```

Sanity-check with the user: annualized mean returns should be roughly in the 0-30% range and annualized volatilities roughly 10-40% for Thai equities/funds — if a number is wildly off (e.g. 500%), there's a units bug (check for duplicate dates or a missing `ffill`).

- [ ] **Step 6: Copy `build_price_panel`, `log_returns`, `estimate_mu_sigma` into the notebook (section 3.2), preceded by a markdown cell deriving the log-return convention `r_t = ln(P_t/P_{t-1})` and why annualizing multiplies mean by `T` and covariance by `T` (JA251.1 √δt scaling — variance scales linearly in time, so SD scales as √T; here we scale the covariance matrix, which is a variance-like quantity, by `T` directly)**

- [ ] **Step 7: Commit**

```bash
git add tests/test_returns.py tests/returns_lib.py data/processed/ notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: compute log returns and annualized mu/sigma from combined asset panel"
```

---

## Task 6: GBM & Itô's Lemma — Theoretical Background (no code, markdown only)

**Files:**
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 2, "Theoretical Background")

**Interfaces:** None (markdown-only task; unblocks Task 7 which implements what this task derives)

- [ ] **Step 1: Write the markdown derivation cells in section 2**, following `learn.cqf/CQF Module 1-2 Master Overview.md` JA251.1 → JA251.4 → JA251.5 exactly:
  1. Why modeling returns (not raw price) as `R_i = mean + SD·φ` forces `mean ∝ δt` and `SD ∝ √δt` in continuous time
  2. The resulting SDE: `dS = μS dt + σS dX` (Geometric Brownian Motion)
  3. Itô's Lemma rule `dX² = dt` and the general form `dF = (∂F/∂X)dX + ½(∂²F/∂X²)dt`
  4. Applying Itô's Lemma to `F = ln S` to get the closed-form solution `S(t) = S₀ exp((μ − ½σ²)t + σX(t))`
  5. The Euler discretization recipe: `S_{t+Δt} = S_t exp((μ − ½σ²)Δt + σ√Δt · Z)`, `Z ~ N(0,1)`
  6. Correlated multi-asset simulation via Cholesky decomposition: if `Σ = LL'`, then `Z_correlated = L·Z_independent` produces draws with covariance `Σ`

- [ ] **Step 2: Read the markdown aloud with the user (or have them read it) and confirm they can restate points 2, 4, and 6 in their own words before proceeding to Task 7.** This is a comprehension checkpoint, not a code step — do not skip it.

- [ ] **Step 3: Commit**

```bash
git add notebooks/01_monte_carlo_simulation.ipynb
git commit -m "docs: derive GBM, Ito's Lemma, and Euler discretization in notebook section 2"
```

---

## Task 7: Euler Simulation Engine (Correlated GBM)

**Files:**
- Create: `tests/test_gbm_engine.py`, `tests/gbm_engine.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 4)

**Interfaces:**
- Consumes: `mu: np.ndarray (n_assets,)`, `sigma: np.ndarray (n_assets, n_assets)` from Task 5
- Produces: `simulate_gbm_paths(S0: np.ndarray, mu: np.ndarray, sigma: np.ndarray, n_years: int, steps_per_year: int, n_paths: int, seed: int) -> np.ndarray` shape `(n_paths, n_years*steps_per_year + 1, n_assets)`

- [ ] **Step 1: Write the failing test — verify the simulated mean and covariance converge to the theoretical inputs**

```python
# tests/test_gbm_engine.py
import numpy as np

def test_gbm_paths_shape_and_moments():
    from gbm_engine import simulate_gbm_paths
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.01], [0.01, 0.0225]])  # vol 20% and 15%, corr 0.333
    S0 = np.array([100.0, 100.0])
    paths = simulate_gbm_paths(S0, mu, sigma, n_years=1, steps_per_year=252, n_paths=20000, seed=7)
    assert paths.shape == (20000, 253, 2)
    log_returns_1y = np.log(paths[:, -1, :] / paths[:, 0, :])
    sample_mean = log_returns_1y.mean(axis=0)
    sample_cov = np.cov(log_returns_1y.T)
    expected_mean = mu - 0.5 * np.diag(sigma)
    assert np.allclose(sample_mean, expected_mean, atol=0.01)
    assert np.allclose(sample_cov, sigma, atol=0.005)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_gbm_engine.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `tests/gbm_engine.py`**

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

- [ ] **Step 4: Run the test again**

```bash
pytest tests/test_gbm_engine.py -v
```

Expected: PASS (sample mean/cov within the `atol` tolerance of the theoretical values — this is a Monte Carlo estimate so it will not be exact, but with 20,000 paths it should be close)

- [ ] **Step 5: Copy `simulate_gbm_paths` into the notebook (section 4), preceded by a markdown cell mapping every line back to the Euler recipe derived in Task 6 (the `drift` line is `(μ − ½σ²)Δt`, the `L = cholesky(sigma)` line is the correlated-random-walk trick, the `paths[:, t, :] = ... * exp(shock)` line is the discretized SDE step)**

- [ ] **Step 6: Commit**

```bash
git add tests/test_gbm_engine.py tests/gbm_engine.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: implement correlated GBM Euler simulation engine"
```

---

## Task 8: Markowitz Portfolio Construction

**Files:**
- Create: `tests/test_portfolio.py`, `tests/portfolio_lib.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (sections 2 and 4)

**Interfaces:**
- Consumes: `mu`, `sigma` (Task 5)
- Produces: `min_variance_weights(sigma) -> np.ndarray`, `tangency_weights(mu, sigma, rf) -> np.ndarray` (both sum to 1)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_portfolio.py
import numpy as np

def test_tangency_and_min_variance_weights_sum_to_one():
    from portfolio_lib import min_variance_weights, tangency_weights
    mu = np.array([0.08, 0.05, 0.10])
    sigma = np.array([
        [0.04, 0.006, 0.01],
        [0.006, 0.0225, 0.004],
        [0.01, 0.004, 0.09],
    ])
    w_min = min_variance_weights(sigma)
    w_tan = tangency_weights(mu, sigma, rf=0.02)
    assert np.isclose(w_min.sum(), 1.0)
    assert np.isclose(w_tan.sum(), 1.0)
    # min-variance portfolio must have lower variance than any single asset
    var_min = w_min @ sigma @ w_min
    assert var_min <= min(np.diag(sigma))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_portfolio.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `tests/portfolio_lib.py` (closed-form Lagrange solution, JA252.2)**

```python
import numpy as np

def min_variance_weights(sigma: np.ndarray) -> np.ndarray:
    ones = np.ones(len(sigma))
    sigma_inv = np.linalg.inv(sigma)
    w = sigma_inv @ ones
    return w / (ones @ sigma_inv @ ones)

def tangency_weights(mu: np.ndarray, sigma: np.ndarray, rf: float) -> np.ndarray:
    excess = mu - rf
    sigma_inv = np.linalg.inv(sigma)
    w = sigma_inv @ excess
    return w / (np.ones(len(mu)) @ sigma_inv @ excess)
```

- [ ] **Step 4: Run the test again**

```bash
pytest tests/test_portfolio.py -v
```

Expected: PASS

- [ ] **Step 5: Cross-check `tangency_weights` against `riskfolio-lib`'s optimizer on the real data**

```python
import riskfolio as rp
import pandas as pd

rets = pd.read_csv("data/processed/log_returns.csv", index_col=0, parse_dates=True)
port = rp.Portfolio(returns=rets)
port.assets_stats(method_mu="hist", method_cov="hist")
w_riskfolio = port.optimization(model="Classic", rm="MV", obj="Sharpe", rf=0.02/252)
print(w_riskfolio)
# compare w_riskfolio['weights'].to_numpy() against tangency_weights(mu, sigma, rf=0.02) from Step 3
# they should agree to within ~1-2 percentage points (riskfolio-lib may add long-only/box constraints ours doesn't)
```

Discuss with the user: if they disagree substantially, the likely cause is `riskfolio-lib` defaulting to a long-only (no-short-selling) constraint that our closed-form solution doesn't impose — note this in the notebook's Discussion section.

- [ ] **Step 6: Copy `min_variance_weights` and `tangency_weights` into the notebook (section 4), preceded by a markdown cell in section 2 deriving the Lagrangian: minimize `½w'Σw` subject to `w'1=1` (and `w'μ=m` for the full efficient-frontier case) → `∂/∂w [½w'Σw − λ(w'1−1)] = 0 → w = λΣ⁻¹1` → solve for `λ` using the constraint (JA252.2)**

- [ ] **Step 7: Commit**

```bash
git add tests/test_portfolio.py tests/portfolio_lib.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: implement closed-form Markowitz min-variance and tangency portfolio weights"
```

---

## Task 9: Simulation Model Configuration Cell

**Files:**
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 3.4)

**Interfaces:**
- Produces: `CONFIG: dict` — read by Tasks 10-13

- [ ] **Step 1: Write the `CONFIG` dict as a single editable code cell, with every key mapped 1:1 to a Portfolio Visualizer field (spec section 5.1 full list) via an inline comment**

```python
CONFIG = {
    "portfolio_type": "tickers",                 # PV: Portfolio Type
    "assets": ["SPY", "QQQ", "TLT", "M0027_2535", "M0209_2548"],  # SPY/QQQ/TLT via Webull TH (US), 2 funds via SEC Open Data (TH)
    "initial_amount": 1_000_000,                  # PV: Initial Amount (THB)
    "cashflow_type": "none",                      # PV: Cashflows — "none"|"contribute"|"withdraw_fixed"|"withdraw_pct"|"rolling_avg"|"geometric"|"life_expectancy"|"import"
    "withdrawal_amount": 0.0,                     # PV: Withdrawal/Contribution Amount
    "inflation_adjusted": True,                   # PV: Inflation Adjusted
    "withdrawal_frequency": "annually",           # PV: Withdrawal Frequency — "monthly"|"quarterly"|"annually"
    "simulation_period_years": 30,                # PV: Simulation Period in Years
    "tax_treatment": "pre_tax",                   # PV: Tax Treatment — "pre_tax"|"after_tax"
    "investment_horizon": "simulated_period",     # PV: Investment Horizon — "simulated_period"|"perpetual"
    "simulation_model": "statistical",            # PV: Simulation Model — "historical"|"forecasted"|"statistical"|"parameterized"
    "time_series_model": "normal",                # PV: Time Series Model — "normal"|"garch"
    "risk_free_rate": 0.02,                       # PV: Risk-Free Rate
    "use_historical_volatility": True,            # PV: Use Historical Volatility
    "use_historical_correlations": True,          # PV: Use Historical Correlations
    "use_full_history": True,                     # PV: Use Full History
    "start_year": 2020, "end_year": 2025,          # PV: Start Year / End Year
    "bootstrap_model": "single_year",             # PV: Bootstrap Model — "single_month"|"single_year"|"block"
    "block_min_years": 2, "block_max_years": 5,    # PV: Block Min./Max. Years
    "circular_bootstrap": False,                  # PV: Circular Bootstrapping
    "distribution": "normal",                     # PV: Distribution — "normal"|"fat_tailed"
    "degrees_of_freedom": 5,                      # PV: Degrees of Freedom (fat-tailed only)
    "sequence_of_returns_risk": "none",           # PV: Sequence of Returns Risk — "none"|"worst_1"|...|"worst_10"
    "inflation_model": "historical",              # PV: Inflation Model — "historical"|"parameterized"
    "inflation_mean": 0.025, "inflation_volatility": 0.01,  # PV: Inflation Mean/Volatility
    "rebalancing": "annual",                      # PV: Rebalancing — "none"|"annual"|"semiannual"|"quarterly"|"monthly"
    "n_paths": 10000,                              # matches PV's "10,000 portfolios" wording seen in the live results
    "seed": 42,
}
```

- [ ] **Step 2: Add a markdown cell above it with a table: PV field name (Thai/English) → `CONFIG` key → what it controls**, copied from spec section 5.1's full field list so nothing is missing.

- [ ] **Step 3: Commit**

```bash
git add notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: add PV-parity CONFIG dict for simulation model configuration"
```

---

## Task 10: Simulation Model 1 — Historical Returns (Bootstrap)

**Files:**
- Create: `tests/test_historical.py`, `tests/historical_sim.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 4)

**Interfaces:**
- Consumes: `returns_df` (Task 5), `CONFIG` (Task 9)
- Produces: `simulate_historical(returns_df, config) -> np.ndarray` shape `(n_paths, n_years+1, n_assets)` of **portfolio index values** (not per-asset — apply weights inside)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_historical.py
import numpy as np
import pandas as pd

def test_historical_bootstrap_shape():
    from historical_sim import simulate_historical
    rng = np.random.default_rng(1)
    dates = pd.date_range("2015-01-01", periods=1500, freq="B")
    rets = pd.DataFrame(rng.normal(0.0003, 0.01, (1500, 2)), index=dates, columns=["A", "B"])
    config = {"simulation_period_years": 5, "n_paths": 500, "seed": 1, "bootstrap_model": "single_year"}
    weights = np.array([0.6, 0.4])
    paths = simulate_historical(rets, weights, config)
    assert paths.shape == (500, 6)  # 5 years + initial value, single portfolio-value column per path
    assert np.all(paths[:, 0] == 1.0)  # normalized to start at 1.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_historical.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `tests/historical_sim.py`**

```python
import numpy as np
import pandas as pd

def simulate_historical(returns_df: pd.DataFrame, weights: np.ndarray, config: dict) -> np.ndarray:
    rng = np.random.default_rng(config["seed"])
    annual_returns = returns_df.groupby(returns_df.index.year).apply(lambda g: (1 + g).prod() - 1)
    portfolio_annual_returns = annual_returns.to_numpy() @ weights  # shape (n_years_available,)
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    sampled = rng.choice(portfolio_annual_returns, size=(n_paths, n_years), replace=True)
    growth = np.cumprod(1 + sampled, axis=1)
    paths = np.hstack([np.ones((n_paths, 1)), growth])
    return paths
```

- [ ] **Step 4: Run the test again**

```bash
pytest tests/test_historical.py -v
```

Expected: PASS

- [ ] **Step 5: Run on real data with the tangency weights from Task 8 and `CONFIG`, sanity-check the median ending value is within a plausible range (e.g. 1.5x-4x over 30 years for a ~7-9% CAGR portfolio)**

- [ ] **Step 6: Copy into the notebook (section 4) with a markdown cell explaining: this is exactly PV's "Historical Returns" model — randomly resampling real observed annual returns (with replacement) instead of assuming a distribution, hence "Historical"**

- [ ] **Step 7: Commit**

```bash
git add tests/test_historical.py tests/historical_sim.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: implement Historical Returns bootstrap simulation model"
```

---

## Task 11: Simulation Model 2 — Forecasted Returns (Normal + GARCH)

**Files:**
- Create: `tests/test_forecasted.py`, `tests/forecasted_sim.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (sections 2 and 4)

**Interfaces:**
- Consumes: `returns_df` (Task 5), user-specified `mu`/`sigma` overrides, `CONFIG["time_series_model"]`
- Produces: `simulate_forecasted(mu, sigma, weights, config, returns_df=None) -> np.ndarray` — same shape convention as Task 10

- [ ] **Step 1: Write the failing test (Normal path first)**

```python
# tests/test_forecasted.py
import numpy as np

def test_forecasted_normal_shape_and_mean():
    from forecasted_sim import simulate_forecasted
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.006], [0.006, 0.0225]])
    weights = np.array([0.5, 0.5])
    config = {"simulation_period_years": 10, "n_paths": 20000, "seed": 3, "time_series_model": "normal"}
    paths = simulate_forecasted(mu, sigma, weights, config)
    assert paths.shape == (20000, 11)
    ending = paths[:, -1]
    assert 1.0 < np.median(ending) < 5.0
```

- [ ] **Step 2: Run test to verify it fails, then implement the Normal branch**

```python
# tests/forecasted_sim.py
import numpy as np

def simulate_forecasted(mu, sigma, weights, config, returns_df=None):
    rng = np.random.default_rng(config["seed"])
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    port_mu = weights @ mu
    port_var = weights @ sigma @ weights
    if config["time_series_model"] == "normal":
        annual_returns = rng.normal(port_mu, np.sqrt(port_var), size=(n_paths, n_years))
    elif config["time_series_model"] == "garch":
        annual_returns = _garch_annual_returns(returns_df, weights, n_years, n_paths, rng)
    else:
        raise ValueError(f"unknown time_series_model: {config['time_series_model']}")
    growth = np.cumprod(1 + annual_returns, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])
```

Run:
```bash
pytest tests/test_forecasted.py -v
```
Expected: FAIL first (no `forecasted_sim` module / no `_garch_annual_returns`), then implement the Normal branch only and re-run — expected PASS for the Normal test (the GARCH function can `raise NotImplementedError` for now; Step 3 fills it in with its own test).

- [ ] **Step 3: Write the failing GARCH test**

```python
def test_forecasted_garch_shape():
    import pandas as pd
    from forecasted_sim import simulate_forecasted
    rng = np.random.default_rng(9)
    dates = pd.date_range("2015-01-01", periods=1500, freq="B")
    rets = pd.DataFrame(rng.normal(0.0003, 0.01, (1500, 2)), index=dates, columns=["A", "B"])
    weights = np.array([0.5, 0.5])
    config = {"simulation_period_years": 5, "n_paths": 2000, "seed": 3, "time_series_model": "garch"}
    paths = simulate_forecasted(None, None, weights, config, returns_df=rets)
    assert paths.shape == (2000, 6)
```

- [ ] **Step 4: Implement `_garch_annual_returns` using the `arch` package (JA252.5 GARCH(1,1))**

```python
from arch import arch_model

def _garch_annual_returns(returns_df, weights, n_years, n_paths, rng):
    port_returns = (returns_df.to_numpy() @ weights) * 100  # arch package expects returns in % for numerical stability
    am = arch_model(port_returns, vol="Garch", p=1, q=1, dist="normal", mean="Constant")
    res = am.fit(disp="off")
    forecasts = res.forecast(horizon=252 * n_years, method="simulation", simulations=n_paths, reindex=False)
    sim_daily_pct = forecasts.simulations.values[-1] / 100  # shape (n_paths, 252*n_years)
    sim_daily = sim_daily_pct.reshape(n_paths, n_years, 252)
    annual_returns = np.prod(1 + sim_daily, axis=2) - 1
    return annual_returns
```

- [ ] **Step 5: Run all forecasted tests**

```bash
pytest tests/test_forecasted.py -v
```

Expected: both PASS. GARCH fitting can occasionally emit convergence warnings on short/synthetic series — that's fine for the synthetic test; note in the notebook that the real 5-year Thai return series should fit more stably.

- [ ] **Step 6: Copy both functions into the notebook (sections 2 and 4)** — in section 2, add a markdown cell deriving GARCH(1,1): `h_t = ω + α(r_{t-1}-μ)² + β·h_{t-1}` (JA252.5), explain that `arch_model` performs Maximum Likelihood Estimation of `ω, α, β` for us (deriving the MLE by hand is out of scope, but the model equation and what MLE is optimizing must be explained). In section 4, add the code with a comment explaining `method="simulation"` produces genuine bootstrapped-innovation GARCH paths, not just a point forecast.

- [ ] **Step 7: Commit**

```bash
git add tests/test_forecasted.py tests/forecasted_sim.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: implement Forecasted Returns model with Normal and GARCH(1,1) time series options"
```

---

## Task 12: Simulation Model 3 — Statistical Returns

**Files:**
- Create: `tests/test_statistical.py`, `tests/statistical_sim.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 4)

**Interfaces:**
- Consumes: `simulate_gbm_paths` (Task 7), `mu`/`sigma` (Task 5), `CONFIG`
- Produces: `simulate_statistical(mu, sigma, weights, config, returns_df=None) -> np.ndarray`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_statistical.py
import numpy as np

def test_statistical_uses_gbm_engine_and_matches_moments():
    from statistical_sim import simulate_statistical
    mu = np.array([0.08, 0.05])
    sigma = np.array([[0.04, 0.006], [0.006, 0.0225]])
    weights = np.array([0.5, 0.5])
    config = {"simulation_period_years": 1, "n_paths": 20000, "seed": 5, "time_series_model": "normal"}
    paths = simulate_statistical(mu, sigma, weights, config)
    assert paths.shape == (20000, 2)
    port_mu = weights @ mu
    port_var = weights @ sigma @ weights
    log_ret = np.log(paths[:, -1])
    assert np.isclose(log_ret.mean(), port_mu - 0.5 * port_var, atol=0.01)
```

- [ ] **Step 2: Run test to verify it fails, then implement `tests/statistical_sim.py` — this model is exactly the GBM engine from Task 7, applied at the portfolio-weight level (this is the direct CQF-native model: JA251.1 + JA251.4-5 + JA252.1)**

```python
import numpy as np
from gbm_engine import simulate_gbm_paths

def simulate_statistical(mu, sigma, weights, config, returns_df=None):
    n_years = config["simulation_period_years"]
    n_paths = config["n_paths"]
    if config["time_series_model"] == "normal":
        asset_paths = simulate_gbm_paths(
            S0=np.ones(len(weights)), mu=mu, sigma=sigma,
            n_years=n_years, steps_per_year=252, n_paths=n_paths, seed=config["seed"],
        )
        portfolio_paths = asset_paths @ weights  # weighted sum across assets at every time step
        annual_idx = np.arange(0, n_years * 252 + 1, 252)
        return portfolio_paths[:, annual_idx]
    elif config["time_series_model"] == "garch":
        from forecasted_sim import _garch_annual_returns
        rng = np.random.default_rng(config["seed"])
        annual_returns = _garch_annual_returns(returns_df, weights, n_years, n_paths, rng)
        growth = np.cumprod(1 + annual_returns, axis=1)
        return np.hstack([np.ones((n_paths, 1)), growth])
    else:
        raise ValueError(f"unknown time_series_model: {config['time_series_model']}")
```

- [ ] **Step 3: Run the test**

```bash
pytest tests/test_statistical.py -v
```

Expected: PASS

- [ ] **Step 4: Copy into the notebook (section 4) with a markdown cell explicitly stating: "This is the model this entire notebook was built to derive from first principles — every other model (Historical, Forecasted, Parameterized) is a variation PV also offers, but Statistical Returns *is* the GBM/Itô/Euler machinery from section 2, applied with the Markowitz weights from section 3.3."**

- [ ] **Step 5: Commit**

```bash
git add tests/test_statistical.py tests/statistical_sim.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: implement Statistical Returns model as the core GBM engine applied at portfolio level"
```

---

## Task 13: Simulation Model 4 — Parameterized Returns (Normal / Fat-Tailed)

**Files:**
- Create: `tests/test_parameterized.py`, `tests/parameterized_sim.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (sections 2 and 4)

**Interfaces:**
- Consumes: `CONFIG` only (user-specified mean/volatility, no data estimation)
- Produces: `simulate_parameterized(config) -> np.ndarray`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_parameterized.py
import numpy as np

def test_parameterized_fat_tailed_has_higher_kurtosis_than_normal():
    from parameterized_sim import simulate_parameterized
    from scipy.stats import kurtosis
    base_config = {"simulation_period_years": 1, "n_paths": 20000, "seed": 11,
                   "expected_return": 0.07, "expected_volatility": 0.15, "degrees_of_freedom": 5}
    normal_paths = simulate_parameterized({**base_config, "distribution": "normal"})
    fat_paths = simulate_parameterized({**base_config, "distribution": "fat_tailed"})
    normal_ret = np.log(normal_paths[:, -1])
    fat_ret = np.log(fat_paths[:, -1])
    assert kurtosis(fat_ret) > kurtosis(normal_ret) + 0.5  # fat-tailed must show excess kurtosis
```

- [ ] **Step 2: Run test to verify it fails, then implement `tests/parameterized_sim.py` (JA252.4 — Student-t as the fat-tail distribution, scaled to match the target volatility)**

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
        scale = sigma / np.sqrt(dof / (dof - 2))  # rescale so variance matches target sigma
        annual_returns = mu + scale * raw
    else:
        raise ValueError(f"unknown distribution: {config['distribution']}")
    growth = np.cumprod(1 + annual_returns, axis=1)
    return np.hstack([np.ones((n_paths, 1)), growth])
```

- [ ] **Step 3: Run the test**

```bash
pytest tests/test_parameterized.py -v
```

Expected: PASS

- [ ] **Step 4: Copy into the notebook (sections 2 and 4)** — in section 2, add a markdown cell deriving why Student-t has fatter tails than Normal (finite degrees of freedom → higher probability of extreme draws) and connect it to JA252.4's stylized fact that real returns show excess kurtosis (>3) versus the Normal distribution's kurtosis of exactly 3.

- [ ] **Step 5: Commit**

```bash
git add tests/test_parameterized.py tests/parameterized_sim.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: implement Parameterized Returns model with Normal and Fat-Tailed (Student-t) distributions"
```

---

## Task 14: Results — Percentile Table, Fan Chart, Histogram, VaR/ES

**Files:**
- Create: `tests/test_results.py`, `tests/results_lib.py`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 5.1)

**Interfaces:**
- Consumes: any `paths` array (shape `(n_paths, n_years+1)`) from Tasks 10-13, `CONFIG["initial_amount"]`
- Produces: `percentile_table(paths, initial_amount) -> pd.DataFrame`, `compute_var_es(ending_values, alpha=0.90) -> tuple[float, float]`, `plot_fan_chart(paths, initial_amount)`, `plot_ending_histogram(paths, initial_amount)`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_results.py
import numpy as np

def test_percentile_table_and_var_es():
    from results_lib import percentile_table, compute_var_es
    rng = np.random.default_rng(1)
    paths = np.cumprod(1 + rng.normal(0.07, 0.15, (5000, 30)), axis=1)
    paths = np.hstack([np.ones((5000, 1)), paths])
    table = percentile_table(paths, initial_amount=1_000_000)
    assert list(table.columns) == [10, 25, 50, 75, 90]
    assert table.loc["ending_balance", 10] < table.loc["ending_balance", 90]
    ending_values = paths[:, -1] * 1_000_000
    var, es = compute_var_es(ending_values, alpha=0.90)
    assert es <= var  # Expected Shortfall must be at least as extreme as VaR (JA252.3)
```

- [ ] **Step 2: Run test to verify it fails, then implement `tests/results_lib.py`**

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def percentile_table(paths: np.ndarray, initial_amount: float) -> pd.DataFrame:
    pcts = [10, 25, 50, 75, 90]
    ending = paths[:, -1] * initial_amount
    n_years = paths.shape[1] - 1
    cagr = (paths[:, -1]) ** (1 / n_years) - 1
    return pd.DataFrame({p: [np.percentile(ending, p), np.percentile(cagr, p)] for p in pcts},
                         index=["ending_balance", "cagr"])

def compute_var_es(ending_values: np.ndarray, alpha: float = 0.90) -> tuple[float, float]:
    losses = -ending_values  # convention: VaR/ES are stated on losses
    var_threshold = np.percentile(losses, alpha * 100)
    es = losses[losses >= var_threshold].mean()
    return -var_threshold, -es  # return back in "ending value" terms (a low/negative number is the bad tail)

def plot_fan_chart(paths: np.ndarray, initial_amount: float):
    pcts = [10, 25, 50, 75, 90]
    values = paths * initial_amount
    years = np.arange(paths.shape[1])
    fig, ax = plt.subplots(figsize=(9, 5))
    for p in pcts:
        ax.plot(years, np.percentile(values, p, axis=0), label=f"{p}th percentile")
    ax.set_xlabel("Year"); ax.set_ylabel("Portfolio Balance"); ax.legend()
    return fig

def plot_ending_histogram(paths: np.ndarray, initial_amount: float):
    ending = paths[:, -1] * initial_amount
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(ending, bins=60)
    ax.set_xlabel("End Balance"); ax.set_ylabel("Frequency")
    return fig
```

- [ ] **Step 3: Run the test**

```bash
pytest tests/test_results.py -v
```

Expected: PASS

- [ ] **Step 4: Copy all four functions into the notebook (section 5.1), preceded by a markdown cell deriving the parametric VaR/ES formulas from JA252.3 (`VaR = −x'μ + Φ⁻¹(α)√(x'Σx)`, `ES = −x'μ + [φ(Φ⁻¹(α))/(1−α)]√(x'Σx)`) and explaining that `compute_var_es` here computes them empirically from the simulated distribution instead — note both approaches in the notebook and compare their numbers for at least one simulation model as a cross-check**

- [ ] **Step 5: Run all four simulation models (Tasks 10-13) with the real `CONFIG` and portfolio weights, produce the percentile table + fan chart + histogram + VaR/ES for each, and write the Results section 5.1 narrative comparing the four models' spread (Historical vs Statistical vs Forecasted vs Parameterized should show visibly different tail behavior, especially Parameterized/Fat-Tailed vs the rest)**

- [ ] **Step 6: Commit**

```bash
git add tests/test_results.py tests/results_lib.py notebooks/01_monte_carlo_simulation.ipynb
git commit -m "feat: add percentile table, VaR/ES, fan chart, and histogram results for all 4 simulation models"
```

---

## Task 15: Live Benchmark Against Portfolio Visualizer

**Files:**
- Create: `benchmarks/monte_carlo/config_used.md`, `benchmarks/monte_carlo/pv_screenshot.png`, `benchmarks/monte_carlo/pv_results_summary.md`
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (section 5.2)

**Interfaces:** None (this task uses a browser, not code)

**Revised approach (engine-vs-engine, not asset-vs-asset):** PV cannot accept Thai SET tickers or SEC fund `proj_id`s, so there is no way to feed it "the same assets." Instead we feed PV the exact same μ/σ/correlation numbers our engine estimated in Task 5, using PV's own **Forecasted Returns** model (which accepts custom Expected Return/Volatility per asset) plus **Use Historical Correlations = No + Correlation Matrix upload**. This isolates the comparison to "does our simulation math match PV's simulation math," independent of which real market the numbers came from.

- [ ] **Step 1: Export our estimated `mu`, `sigma` (Task 5) and portfolio weights (Task 8) to a small file `benchmarks/monte_carlo/our_estimated_parameters.csv`** — one row per asset with `asset_name, weight, expected_return, expected_volatility`, plus a separate `correlation_matrix.csv` (assets × assets).

- [ ] **Step 2: Write `benchmarks/monte_carlo/config_used.md` documenting every PV field value to enter**: Portfolio Type=Tickers (use 5 placeholder US tickers just to create 5 asset slots — their historical data is irrelevant since we override Expected Return/Volatility), Simulation Model=**Forecasted Returns**, Use Historical Volatility=No (enter our `expected_volatility` per asset), Use Historical Correlations=No (upload `correlation_matrix.csv`), Initial Amount/Simulation Period/Rebalancing matching `CONFIG` exactly.

- [ ] **Step 3: Open `https://www.portfoliovisualizer.com/monte-carlo-simulation` in a browser, enter the documented config exactly, upload the correlation matrix, click "Run Simulation," and save a screenshot to `benchmarks/monte_carlo/pv_screenshot.png`**

- [ ] **Step 4: Copy PV's Summary Statistics table (10th/25th/50th/75th/90th percentile ending balance, CAGR) into `benchmarks/monte_carlo/pv_results_summary.md` as a markdown table**

- [ ] **Step 5: In the notebook section 5.2, embed the screenshot, reproduce the PV summary table, and place it next to our own `percentile_table` output for the Statistical Returns model (same μ/σ/correlation inputs) — the two should be close; write a short discussion of any remaining gap (expected source: random sampling/seed differences, not a modeling error, since both engines received identical statistical inputs)**

- [ ] **Step 5: Commit**

```bash
git add benchmarks/monte_carlo/ notebooks/01_monte_carlo_simulation.ipynb
git commit -m "docs: add live Portfolio Visualizer benchmark comparison for notebook 01"
```

---

## Task 16: Discussion, Conclusion, Appendix — Final Polish

**Files:**
- Modify: `notebooks/01_monte_carlo_simulation.ipynb` (sections 6, 7, Appendix, Executive Summary)

**Interfaces:** None (writing task)

- [ ] **Step 1: Write section 6 (Discussion)** covering: (a) benchmark gap explanation from Task 15, (b) Historical vs Statistical vs Forecasted vs Parameterized comparison from Task 14, (c) known limitations — GARCH fit stability on a 5-year Thai series, Webull data being a manual CSV rather than live API.

- [ ] **Step 2: Write section 7 (Conclusion & Limitations)** — one paragraph summarizing what was built and what CQF concepts it demonstrates (JA251.1, JA251.4-5, JA252.1-3, JA252.4-5), one paragraph of stated limitations (no tax modeling, no after-tax return modeling, Webull data source is manual).

- [ ] **Step 3: Write the Appendix glossary** — one row per formula used in the notebook (GBM SDE, Itô's Lemma, Euler discretization, min-variance/tangency weights, GARCH(1,1), Student-t fat tail, VaR/ES), each with a one-line plain-English restatement, in the same style as `learn.cqf/CQF Module 1-2 Master Overview.md`'s glossary.

- [ ] **Step 4: Go back and write the Executive Summary** (top of the notebook, one paragraph) now that every section exists — summarize the notebook's purpose and headline finding.

- [ ] **Step 5: Execute the full notebook top-to-bottom to confirm no cell errors**

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/01_monte_carlo_simulation.ipynb
```

Expected: completes without raising; if a cell errors, fix it before calling the notebook done.

- [ ] **Step 6: Final commit**

```bash
git add notebooks/01_monte_carlo_simulation.ipynb
git commit -m "docs: finish discussion, conclusion, appendix, and executive summary for notebook 01"
```

---

## Self-Review Notes (for whoever executes this plan)

- **Spec coverage:** Tasks 1-16 cover spec section 5.1's full field list (Tasks 9-13), section 4's template (all tasks map to a template section), section 6's data pipeline (Tasks 2-4), section 7's benchmark protocol (Task 15), and section 10's teaching requirement (every task has a markdown-before-code step and Task 6 has an explicit comprehension checkpoint).
- **Known open risk carried into Task 2:** the exact SEC Open Data base URL and auth header name (`Ocp-Apim-Subscription-Key` vs `Authorization: Bearer`) is a best guess from the Azure APIM pattern observed during spec research — Task 2 Step 2 requires manually confirming this against the real developer dashboard before trusting the client code.
- **Known deliberate scope cut carried into Task 4:** Webull TH OpenAPI SDK automation is not implemented — manual CSV export is the primary path, stated as a limitation rather than hidden.
- **Not yet planned:** Notebook 02 (`02_financial_goals.ipynb`) and Notebook 03 (`03_asset_liability_modeling.ipynb`) — per spec section 10, these get their own implementation plans only after notebook 01 is complete and understood.
