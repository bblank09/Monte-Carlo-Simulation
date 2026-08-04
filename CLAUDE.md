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
