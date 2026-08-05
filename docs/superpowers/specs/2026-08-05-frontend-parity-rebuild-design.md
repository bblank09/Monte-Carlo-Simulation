# Frontend Parity Rebuild — Design

Date: 2026-08-05

## Problem

The Monte Carlo webapp's frontend was built independently during Phase 1
(mock-data phase) rather than copied structurally from its sibling,
`../Backtest Portfolio Webull:SEC OPENAI`. Despite many rounds of UX/product
review during Phase 1, the two frontends have drifted in ways that read as
bugs when compared side by side:

1. **Portfolio step filter is incomplete.** Backtest's `PortfolioStep.tsx`
   has two facet filters (AMC + fund category/`policy_desc`) behind a
   "Filters (N)" dropdown with per-facet search + checklist. Monte Carlo's
   `PortfolioStep.tsx` only has one facet (AMC) — because the backend's
   `FundSummary` contract never included `policy_desc` in the first place,
   not because the frontend chose to omit it. The CSS for both facets
   (`.filter-mini-group`, `.filter-checklist`, `.fund-suggest-filter-toggle`,
   etc.) already exists identically in both projects' `styles.css` — only the
   data and the second `FacetGroup` wiring are missing.
2. **Parameters step field validation is incomplete.** Backtest's
   `AssumptionsStep.tsx` shows an inline `.field-error` message under every
   validatable field (start/end date, initial capital, benchmark, cashflow
   amount). Monte Carlo's `ParametersStep.tsx` has the same `fieldError()`
   mechanism and CSS class already, but only wires it to 3 fields
   (`initial_amount`, `simulation_period_years`, `n_paths`) — cashflow
   amount, each goal's fields, glide-path years, retirement-holdings
   weights, and the Parameterized model's `expected_return` /
   `expected_volatility` / `degrees_of_freedom` have no inline validation.
3. **Multi-goal "Add Goal" editor UI is irregular.** This feature has no
   Backtest equivalent (Backtest only has a single cashflow, not named
   goals), so it was designed from scratch and its spacing/layout doesn't
   match the row-repeater pattern used elsewhere in the app.
4. **Results view layout doesn't match Backtest's spacing/typography
   system.** `RunSummary.tsx` (8 tabs: Summary, Growth, Drawdown, Returns,
   Metrics, Cashflows, Rebalancing, Report) and Monte Carlo's
   `ResultsView.tsx` (6 tabs: Overview, Growth, Distribution, Metrics, Risk
   & Correlation, Report) cover close to a 1:1 tab mapping, but the actual
   section-title spacing, card grids, and typography scale inside each tab
   were not built by copying Backtest's implementation.

## Goal

Bring the Monte Carlo frontend into structural parity with Backtest
Portfolio by copying its actual JSX/CSS as the base for each of the 3
wizard steps + Results view, then substituting only the content that must
differ because the two apps answer different questions (Backtest: "what did
happen" / Monte Carlo: "what could happen"). Do not redesign from scratch a
second time — every layout/spacing/component-structure decision should
trace back to what Backtest already does, except where Monte Carlo has no
Backtest equivalent (multi-goal editor), in which case Backtest's closest
analogous pattern (the repeatable-row editor in `PortfolioStep.tsx`) is the
template.

## Scope decisions (confirmed with user)

- **Copy real files, then adapt** (not "rebuild from scratch to match") —
  pull actual JSX/CSS blocks from Backtest's components as the starting
  point for each section, then edit only what must differ semantically.
- **Full 3-step wizard + Results**, not just the 4 specifically-named
  issues — every section gets a structural comparison pass, not only the
  ones the user happened to notice.
- **Keep Monte Carlo's existing file names** (`ParametersStep.tsx`,
  `ResultsView.tsx`, `App.tsx`) — do not rename to match Backtest's
  (`AssumptionsStep.tsx`, `RunSummary.tsx`, `pages/BacktestWorkspace.tsx`).
  Only the JSX structure, CSS classes, spacing, and layout patterns inside
  those files need to become structurally identical to their Backtest
  counterpart; import sites (`App.tsx`, `frontend/e2e/happy-path.spec.ts`)
  are unaffected by this choice.

## Work breakdown

### A. Portfolio step filter parity

- **Backend:** add `policy_desc` to `backend/app/api/funds.py`'s response
  mapping (already present in `data/processed/fund_universe.csv`, no new
  data fetch needed) and to `FundSummary` in
  `frontend/src/types/simulate.ts`.
- **Frontend:** add a second `categoryFacets` filter to
  `PortfolioStep.tsx`, matching Backtest's `buildFacets()` /
  `FacetGroup` two-facet pattern exactly (AMC facet stays as-is; add the
  category facet alongside it, both behind the same "Filters (N)"
  dropdown). No new CSS needed — the classes already exist identically in
  both projects.

### B. Parameters step field validation completeness

Add `.field-error` messages (reusing the existing `fieldError()` mechanism
and CSS class already present in `ParametersStep.tsx`) for every field that
can actually be invalid and currently has no inline feedback:

- Cashflow amount (must be > 0 when a cashflow mode other than "none" is
  selected)
- Each goal's fields in the multi-goal editor (amount > 0,
  `starts_year < ends_year`)
- Glide-path years, years-to-retirement (already schema-validated
  server-side; this adds the matching client-side inline message)
- Retirement-holdings weights (must sum to 100%, mirroring the primary
  holdings validation already shown)
- Parameterized model: `expected_return`, `expected_volatility`,
  `degrees_of_freedom` (required when `distribution === "fat_tailed"`)

### C. Multi-goal "Add Goal" editor — restyle using Backtest's row-repeater pattern

No direct Backtest equivalent exists (single-cashflow only), so the visual
template is Backtest's `PortfolioStep.tsx` repeatable-row pattern (row
border/spacing, `+ Add fund`-style add button, inline `×` remove button).
Rebuild the goal-row markup/CSS to match that pattern's structure exactly,
keeping the goal-specific fields (purpose, amount, is_withdrawal, frequency,
starts_year, ends_year) but fixing the current irregular spacing/layout.

### D. Results view layout parity

Go tab-by-tab, matching Monte Carlo's 6 tabs against Backtest's 8 (a close
but not exact 1:1 mapping — e.g. "Risk & Correlation" has no single
Backtest counterpart, closest is a blend of Backtest's Returns + Metrics
tabs' layout patterns). For each tab, adopt Backtest's section-title
spacing, card-grid structure, and typography scale from `RunSummary.tsx`
and its CSS, keeping Monte Carlo's actual data/metrics unchanged.

## Non-goals

- No change to simulation engine, calculations, or API response shape
  beyond adding `policy_desc` to the funds list (a pure additive field).
- No renaming of Monte Carlo's existing files/components.
- No new features beyond what's needed to reach structural parity (e.g. no
  shareable-link/`?run=` URL persistence — Backtest has this via
  `run_id`-backed persisted runs, which Monte Carlo's simulate endpoint
  doesn't currently support; out of scope for this rebuild).

## Verification

- Backend: add/update tests for `policy_desc` in `funds.py`'s response
  (`backend/tests/api/test_funds_endpoint.py`).
- Frontend: `npm run build` (typecheck) after each section's changes.
- Full Playwright e2e suite (`frontend/e2e/happy-path.spec.ts`) re-run
  after all changes land.
- Manual side-by-side visual verification via the Browser pane against the
  live Backtest Portfolio app, section by section, as has been done
  throughout this project's prior UX review rounds.

## Open questions / deferred

- None outstanding — all scope questions were resolved in the brainstorming
  dialogue above before this doc was written.
