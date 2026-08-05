# Frontend Parity Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Monte Carlo frontend's Portfolio/Parameters/Results wizard into structural parity with `../Backtest Portfolio Webull:SEC OPENAI`'s frontend — by copying its actual JSX/CSS patterns as the base for each section — instead of the independently-designed version that shipped in Phase 1 and has since drifted from it.

**Architecture:** No new components or files. Every task edits existing files in place: `backend/app/api/funds.py`, `frontend/src/types/simulate.ts`, `frontend/src/components/PortfolioStep.tsx`, `frontend/src/components/ParametersStep.tsx`, `frontend/src/components/RunOverlay.tsx`, `frontend/src/components/ResultsView.tsx`, `frontend/src/styles.css`. Each task's reference material is Backtest's equivalent file at the paths noted in that task.

**Tech Stack:** FastAPI + Pydantic v2 (backend), React 19 + TypeScript + Vite 6 (frontend), no new dependencies.

## Global Constraints

- Keep Monte Carlo's existing file names (`ParametersStep.tsx`, `ResultsView.tsx`, `App.tsx`) — do not rename to match Backtest's (`AssumptionsStep.tsx`, `RunSummary.tsx`, `pages/BacktestWorkspace.tsx`).
- No change to simulation engine, calculations, or API response shape beyond adding `policy_desc` to the funds list (a pure additive field) — see spec `docs/superpowers/specs/2026-08-05-frontend-parity-rebuild-design.md`.
- No new features beyond what's needed to reach structural parity (no shareable-link/`?run=` persistence).
- `npm run build` (tsc typecheck + vite build) must pass after every frontend task.
- `pytest backend/tests` must pass after every backend task.

---

### Task 1: Backend — add `policy_desc` to the funds list

**Files:**
- Modify: `backend/app/api/funds.py`
- Modify: `frontend/src/types/simulate.ts`
- Test: `backend/tests/api/test_funds_endpoint.py`

**Interfaces:**
- Consumes: `backend/app/data/sec_client.find_equity_funds()` — already returns dicts with a `policy_desc`-shaped raw field named `"policy_desc"` per fund (confirm via `data/processed/fund_universe.csv`'s column of the same name; `sec_client._load_fund_universe()` reads the CSV directly with pandas so the column survives into each row dict... *actually* `find_equity_funds()` in `backend/app/data/sec_client.py` currently returns only `proj_id`, `proj_name_th`, `comp_name_th` per fund — it filters the universe by `policy_desc` but does not include it in the returned dict. Add `policy_desc` to the dict it returns.
- Produces: `GET /api/funds` response items gain a `policy_desc: string` field; `FundSummary` TS type gains `policy_desc?: string`.

- [ ] **Step 1: Write the failing backend test**

Add this test to `backend/tests/api/test_funds_endpoint.py`:

```python
@patch("backend.app.api.funds.find_equity_funds")
def test_funds_endpoint_includes_policy_desc(mock_find):
    mock_find.return_value = [{"proj_id": "M0027_2535", "proj_name_th": "K หุ้นทุน", "comp_name_th": "AMC", "policy_desc": "ตราสารทุน"}]
    resp = client.get("/api/funds")
    assert resp.status_code == 200
    assert resp.json()[0]["policy_desc"] == "ตราสารทุน"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/api/test_funds_endpoint.py -v`
Expected: FAIL — `KeyError: 'policy_desc'` (funds.py's mapping doesn't include it yet).

- [ ] **Step 3: Add `policy_desc` to `sec_client.find_equity_funds()`'s returned dicts**

In `backend/app/data/sec_client.py`, in `find_equity_funds()`, change the returned dict to include `policy_desc`:

```python
    return [
        {
            "proj_id": row["proj_id"],
            "proj_name_th": row["display_name"],
            "comp_name_th": row["amc_name_th"],
            "policy_desc": row["policy_desc"],
        }
        for _, row in matched.iterrows()
    ]
```

- [ ] **Step 4: Map `policy_desc` through in `funds.py`**

In `backend/app/api/funds.py`, add `"policy_desc"` to the returned dict:

```python
    return [
        {
            "proj_id": item.get("proj_id"),
            "proj_name_thai": item.get("proj_name_th"),
            "amc_name_thai": item.get("comp_name_th"),
            "policy_desc": item.get("policy_desc"),
        }
        for item in find_equity_funds()
    ]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest backend/tests/api/test_funds_endpoint.py backend/tests/data/test_sec_client.py -v`
Expected: PASS (all tests, including the existing `test_find_equity_funds_filters_policy_and_main_class` in `test_sec_client.py`, which will need its fixture assertion extended — add `assert funds[0]["policy_desc"] == "ตราสารทุน"` to that existing test).

- [ ] **Step 6: Add `policy_desc` to the frontend `FundSummary` type**

In `frontend/src/types/simulate.ts`, extend the `FundSummary` interface:

```typescript
export interface FundSummary {
  proj_id: string;
  proj_name_thai?: string;
  amc_name_thai?: string;
  policy_desc?: string;
}
```

- [ ] **Step 7: Run the full backend suite and frontend typecheck**

Run: `pytest backend/tests -q && npm --prefix frontend run build`
Expected: PASS (both).

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/funds.py backend/app/data/sec_client.py backend/tests/api/test_funds_endpoint.py backend/tests/data/test_sec_client.py frontend/src/types/simulate.ts
git commit -m "feat: expose policy_desc on /api/funds for the category filter"
```

---

### Task 2: Portfolio step — add the fund-category filter facet (parity with Backtest)

**Files:**
- Modify: `frontend/src/components/PortfolioStep.tsx`

**Reference:** `../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/PortfolioStep.tsx` (its `CATEGORY_LABELS_EN`, two-arg `buildFacets`, and the `categoryFacets`/`FacetGroup` wiring around lines 17-120 and 396-420).

**Interfaces:**
- Consumes: `FundSummary.policy_desc` from Task 1.
- Produces: no change to `PortfolioStep`'s public `Props` — this is purely internal.

- [ ] **Step 1: Add the Thai→English category label map**

In `frontend/src/components/PortfolioStep.tsx`, above `function fundDisplayName`, add:

```typescript
// SEC's policy_desc is a Thai-language category label from the API. Mirrors
// ../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/PortfolioStep.tsx's
// CATEGORY_LABELS_EN -- verified against the same underlying SEC fund universe.
const CATEGORY_LABELS_EN: Record<string, string> = {
  "ตราสารทุน": "Equity",
  "ตราสารหนี้": "Fixed Income",
  "ผสม": "Mixed",
  "ทรัพย์สินทางเลือก": "Alternative Assets",
  "อื่น ๆ": "Other",
  "ไม่ระบุ เนื่องจากเป็นกองทุนรวมอีทีเอฟแบบ leveraged management หรือ inverse management": "Unspecified (Leveraged/Inverse ETF)"
};

function categoryLabel(value: string) {
  return CATEGORY_LABELS_EN[value] ?? value;
}
```

- [ ] **Step 2: Change `buildFacets` to support cross-filtering between two facets**

Replace the current single-arg `buildFacets`:

```typescript
function buildFacets(funds: FundSummary[], field: "amc_name_thai") {
  const counts = new Map<string, number>();
  for (const fund of funds) {
    const key = fund[field];
    if (!key) continue;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => a.value.localeCompare(b.value));
}
```

with:

```typescript
function buildFacets(
  funds: FundSummary[],
  field: "amc_name_thai" | "policy_desc",
  otherFilter: Set<string>,
  otherField: "amc_name_thai" | "policy_desc"
) {
  const counts = new Map<string, number>();
  for (const fund of funds) {
    const key = fund[field];
    if (!key) continue;
    if (otherFilter.size && !otherFilter.has(fund[otherField] ?? "")) continue;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => a.value.localeCompare(b.value));
}
```

- [ ] **Step 3: Add `categoryFilter` state and `categoryFacets`, update `amcFacets` and `filteredFunds`**

In the `PortfolioStep` component body, replace:

```typescript
  const [amcFilter, setAmcFilter] = useState<Set<string>>(new Set());
```

with:

```typescript
  const [amcFilter, setAmcFilter] = useState<Set<string>>(new Set());
  const [categoryFilter, setCategoryFilter] = useState<Set<string>>(new Set());
```

Replace:

```typescript
  const amcFacets = useMemo(() => buildFacets(funds, "amc_name_thai"), [funds]);

  const filteredFunds = useMemo(
    () =>
      funds.filter((fund) => {
        if (amcFilter.size && (!fund.amc_name_thai || !amcFilter.has(fund.amc_name_thai))) return false;
        return true;
      }),
    [funds, amcFilter]
  );
```

with:

```typescript
  const amcFacets = useMemo(
    () => buildFacets(funds, "amc_name_thai", categoryFilter, "policy_desc"),
    [funds, categoryFilter]
  );
  const categoryFacets = useMemo(
    () => buildFacets(funds, "policy_desc", amcFilter, "amc_name_thai"),
    [funds, amcFilter]
  );

  const filteredFunds = useMemo(
    () =>
      funds.filter((fund) => {
        if (amcFilter.size && (!fund.amc_name_thai || !amcFilter.has(fund.amc_name_thai))) return false;
        if (categoryFilter.size && (!fund.policy_desc || !categoryFilter.has(fund.policy_desc))) return false;
        return true;
      }),
    [funds, amcFilter, categoryFilter]
  );
```

- [ ] **Step 4: Generalize `toggleAmcFilter`/`clearAllFilters` to both facets**

Replace:

```typescript
  function toggleAmcFilter(value: string) {
    setAmcFilter((current) => {
      const next = new Set(current);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  }

  function clearAllFilters() {
    setAmcFilter(new Set());
  }
```

with:

```typescript
  function toggleFilter(setter: (updater: (current: Set<string>) => Set<string>) => void, value: string) {
    setter((current) => {
      const next = new Set(current);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  }

  function clearAllFilters() {
    setAmcFilter(new Set());
    setCategoryFilter(new Set());
  }
```

- [ ] **Step 5: Pass the new facet/filter props down to `HoldingsRow`**

In the `rows.map((row) => (<HoldingsRow ...>))` call inside the main render, add `categoryFacets`, `categoryFilter`, and change the toggle callbacks:

```typescript
                amcFacets={amcFacets}
                amcFilter={amcFilter}
                categoryFacets={categoryFacets}
                categoryFilter={categoryFilter}
                onToggleAmc={(value) => toggleFilter(setAmcFilter, value)}
                onToggleCategory={(value) => toggleFilter(setCategoryFilter, value)}
                onClearFilters={clearAllFilters}
```

- [ ] **Step 6: Update `HoldingsRow`'s props and render both `FacetGroup`s**

In `HoldingsRow`'s destructured props and its type annotation, add `categoryFacets: Facet[]`, `categoryFilter: Set<string>`, `onToggleCategory: (value: string) => void` alongside the existing `amcFacets`/`amcFilter`/`onToggleAmc`. Update:

```typescript
  const activeFilterCount = amcFilter.size;
```

to:

```typescript
  const activeFilterCount = amcFilter.size + categoryFilter.size;
```

Replace the filter-dropdown JSX condition and body:

```typescript
          {amcFacets.length ? (
            <div className="fund-suggest-filters">
              ...
                  <FacetGroup label="AMC" facets={amcFacets} selected={amcFilter} onToggle={onToggleAmc} />
                </div>
              ) : null}
            </div>
          ) : null}
```

with:

```typescript
          {amcFacets.length || categoryFacets.length ? (
            <div className="fund-suggest-filters">
              <button
                className="fund-suggest-filter-toggle"
                onClick={() => setFiltersOpen((current) => !current)}
                onMouseDown={(event) => event.preventDefault()}
                type="button"
              >
                <SlidersHorizontal size={12} />
                Filters{activeFilterCount ? ` (${activeFilterCount})` : ""}
                <ChevronDown className={filtersOpen ? "chev open" : "chev"} size={12} />
              </button>
              {filtersOpen ? (
                <div className="fund-suggest-filter-body">
                  {activeFilterCount ? (
                    <button className="filter-clear-all" onClick={onClearFilters} onMouseDown={(event) => event.preventDefault()} type="button">
                      Clear all filters
                    </button>
                  ) : null}
                  {amcFacets.length ? (
                    <FacetGroup label="AMC" facets={amcFacets} selected={amcFilter} onToggle={onToggleAmc} />
                  ) : null}
                  {categoryFacets.length ? (
                    <FacetGroup facets={categoryFacets} formatLabel={categoryLabel} label="Fund category" onToggle={onToggleCategory} selected={categoryFilter} />
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
```

(Keep the existing `<input>` combobox and the `<div aria-label="Fund suggestions" ...>` listbox exactly as they are — only the filter-dropdown block above them changes.)

- [ ] **Step 7: Add `formatLabel` support to `FacetGroup`**

Replace `FacetGroup`'s signature:

```typescript
function FacetGroup({
  label,
  facets,
  selected,
  onToggle
}: {
  label: string;
  facets: Facet[];
  selected: Set<string>;
  onToggle: (value: string) => void;
}) {
  const [query, setQuery] = useState("");
  const visible = query.trim()
    ? facets.filter((facet) => facet.value.toLowerCase().includes(query.trim().toLowerCase()))
    : facets;
```

with:

```typescript
function FacetGroup({
  label,
  facets,
  selected,
  onToggle,
  formatLabel = (value: string) => value
}: {
  label: string;
  facets: Facet[];
  selected: Set<string>;
  onToggle: (value: string) => void;
  formatLabel?: (value: string) => string;
}) {
  const [query, setQuery] = useState("");
  const visible = query.trim()
    ? facets.filter((facet) => formatLabel(facet.value).toLowerCase().includes(query.trim().toLowerCase()))
    : facets;
```

And in its render, change `<span className="filter-check-label">{facet.value}</span>` to `<span className="filter-check-label">{formatLabel(facet.value)}</span>`.

- [ ] **Step 8: Typecheck and build**

Run: `npm --prefix frontend run build`
Expected: PASS, no TypeScript errors.

- [ ] **Step 9: Manual verification via Browser pane**

Start the backend (`uvicorn backend.app.main:app --port 8001`) and open `http://127.0.0.1:8001` in the Browser pane. Click into a fund search box, click "Filters", and confirm both "AMC" and "Fund category" facet groups render with checkboxes and counts, matching `http://127.0.0.1:8000` (Backtest's dev server, if running) side by side. Take a screenshot for the record.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/components/PortfolioStep.tsx
git commit -m "feat: add fund-category filter facet to Portfolio step (parity with Backtest)"
```

---

### Task 3: Parameters step — complete inline field validation

**Files:**
- Modify: `frontend/src/components/ParametersStep.tsx`

**Reference:** `../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/AssumptionsStep.tsx`'s `fieldError()`/`.field-error` pattern (already present in Monte Carlo's `ParametersStep.tsx` for 3 fields — this task extends it to the remaining ones named in the design spec).

**Interfaces:**
- Consumes: `SimulateRequest`, `NamedGoal` types (unchanged).
- Produces: no change to `ParametersStep`'s public `Props`.

- [ ] **Step 1: Extend the `fieldErrors` validation object**

In `ParametersStep`, the `fieldErrors` object currently only covers `initial_amount`, `simulation_period_years`, `n_paths`. Replace:

```typescript
  const fieldErrors: Record<string, string> = {};
  if (value.initial_amount <= 0) {
    fieldErrors.initial_amount = "Initial amount must be greater than 0.";
  }
  if (value.simulation_period_years < 5 || value.simulation_period_years > 75) {
    fieldErrors.simulation_period_years = "Simulation period must be between 5 and 75 years.";
  }
  if (value.n_paths > 20000) {
    fieldErrors.n_paths = "Number of paths cannot exceed 20,000.";
  } else if (value.n_paths < 1000) {
    fieldErrors.n_paths = "Fewer than 1,000 paths gives statistically unreliable percentile estimates.";
  }
```

with (adding the new checks after the existing ones, unchanged logic kept intact):

```typescript
  const fieldErrors: Record<string, string> = {};
  if (value.initial_amount <= 0) {
    fieldErrors.initial_amount = "Initial amount must be greater than 0.";
  }
  if (value.simulation_period_years < 5 || value.simulation_period_years > 75) {
    fieldErrors.simulation_period_years = "Simulation period must be between 5 and 75 years.";
  }
  if (value.n_paths > 20000) {
    fieldErrors.n_paths = "Number of paths cannot exceed 20,000.";
  } else if (value.n_paths < 1000) {
    fieldErrors.n_paths = "Fewer than 1,000 paths gives statistically unreliable percentile estimates.";
  }
  if (!multiGoal && value.cashflow_mode !== "none" && !((value.cashflow_amount ?? 0) > 0)) {
    fieldErrors.cashflow_amount = "Cashflow amount must be greater than 0.";
  }
  if (multiGoal) {
    if (!(value.years_to_retirement && value.years_to_retirement >= 1)) {
      fieldErrors.years_to_retirement = "Years to retirement must be at least 1.";
    }
    if (!(value.glide_path_years && value.glide_path_years >= 1)) {
      fieldErrors.glide_path_years = "Glide path years must be at least 1.";
    }
    const retirementTotal = (value.retirement_holdings ?? []).reduce((sum, h) => sum + (h.weight || 0), 0);
    if (!(value.retirement_holdings && value.retirement_holdings.length) || Math.abs(retirementTotal - 100) > 0.05) {
      fieldErrors.retirement_holdings = `Retirement allocation weights must sum to 100% (currently ${retirementTotal.toFixed(1)}%).`;
    }
  }
  if (value.simulation_model === "parameterized") {
    if (value.expected_return === undefined || value.expected_return === null) {
      fieldErrors.expected_return = "Expected return is required.";
    }
    if (!((value.expected_volatility ?? 0) > 0)) {
      fieldErrors.expected_volatility = "Expected volatility must be greater than 0.";
    }
    if (value.distribution === "fat_tailed" && !((value.degrees_of_freedom ?? 0) > 2)) {
      fieldErrors.degrees_of_freedom = "Degrees of freedom must be greater than 2 for a fat-tailed distribution.";
    }
  }
```

- [ ] **Step 2: Wire `onBlur={() => markTouched(...)}` and inline `field-error` divs to each newly-validated field**

For each field below, add `onBlur={() => markTouched("<field>")}` to its `<input>`/`<select>` and a `{fieldError("<field>") && <div className="field-error">{fieldError("<field>")}</div>}` immediately after it (matching the exact pattern already used for `initial_amount`).

- **Cashflow amount** (single-cashflow mode, id `cashflow_amount`): add `onBlur={() => markTouched("cashflow_amount")}` to its `<input>`, and after it:
  ```tsx
  {fieldError("cashflow_amount") && <div className="field-error">{fieldError("cashflow_amount")}</div>}
  ```
- **Years to Retirement** (id `years_to_retirement`): add `onBlur={() => markTouched("years_to_retirement")}`, and after it:
  ```tsx
  {fieldError("years_to_retirement") && <div className="field-error">{fieldError("years_to_retirement")}</div>}
  ```
- **Glide Path Years** (id `glide_path_years`): add `onBlur={() => markTouched("glide_path_years")}`, and after it:
  ```tsx
  {fieldError("glide_path_years") && <div className="field-error">{fieldError("glide_path_years")}</div>}
  ```
- **Expected Return** (id `expected_return`): add `onBlur={() => markTouched("expected_return")}`, and after it:
  ```tsx
  {fieldError("expected_return") && <div className="field-error">{fieldError("expected_return")}</div>}
  ```
- **Expected Volatility** (id `expected_volatility`): add `onBlur={() => markTouched("expected_volatility")}`, and after it:
  ```tsx
  {fieldError("expected_volatility") && <div className="field-error">{fieldError("expected_volatility")}</div>}
  ```
- **Degrees of Freedom** (id `degrees_of_freedom`): add `onBlur={() => markTouched("degrees_of_freedom")}`, and after it:
  ```tsx
  {fieldError("degrees_of_freedom") && <div className="field-error">{fieldError("degrees_of_freedom")}</div>}
  ```

- [ ] **Step 3: Show the retirement-holdings weight error under `RetirementAllocationTable`**

Immediately after the `<RetirementAllocationTable ... />` call inside the `multiGoal &&` block, add:

```tsx
            {fieldError("retirement_holdings") && <div className="field-error">{fieldError("retirement_holdings")}</div>}
```

This requires the field to be marked touched once the table's own weight total changes — add a `useEffect` right after the `fieldErrors` object definition:

```typescript
  useEffect(() => {
    if (multiGoal && (value.retirement_holdings ?? []).length > 0) markTouched("retirement_holdings");
  }, [multiGoal, value.retirement_holdings]);
```

(Add `useEffect` to the existing `import { useState } from "react";` line at the top of the file: `import { useEffect, useState } from "react";`.)

- [ ] **Step 4: Add per-goal amount/year-range validation to `GoalsTable`**

In `GoalsTable`, inside the `goals.map((goal, index) => (...))` render, add inline error messages under the Amount and Ends-year inputs. Replace:

```tsx
          <input className="field" type="number" placeholder="Amount" value={goal.amount} onChange={(e) => updateGoal(index, { amount: Number(e.target.value) })} />
          <input className="field" type="number" placeholder="Starts (year)" value={goal.starts_year} onChange={(e) => updateGoal(index, { starts_year: Number(e.target.value) })} />
          <input className="field" type="number" placeholder="Ends (year)" value={goal.ends_year} onChange={(e) => updateGoal(index, { ends_year: Number(e.target.value) })} />
```

with (wrapping each in a `<div className="form-field">` so the error can render beneath it, matching the pattern used elsewhere in this file):

```tsx
          <div className="form-field">
            <input className="field" type="number" placeholder="Amount" value={goal.amount} onChange={(e) => updateGoal(index, { amount: Number(e.target.value) })} />
            {!(goal.amount > 0) && <div className="field-error">Amount must be greater than 0.</div>}
          </div>
          <div className="form-field">
            <input className="field" type="number" placeholder="Starts (year)" value={goal.starts_year} onChange={(e) => updateGoal(index, { starts_year: Number(e.target.value) })} />
          </div>
          <div className="form-field">
            <input className="field" type="number" placeholder="Ends (year)" value={goal.ends_year} onChange={(e) => updateGoal(index, { ends_year: Number(e.target.value) })} />
            {goal.ends_year <= goal.starts_year && <div className="field-error">End year must be after start year.</div>}
          </div>
```

(These are shown unconditionally rather than gated on `touched`/blur, since each goal row is added already-invalid by construction — matching how `RetirementAllocationTable`'s "incomplete" pill works.)

- [ ] **Step 5: Typecheck and build**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [ ] **Step 6: Manual verification via Browser pane**

Load the app, select "Parameterized Returns" and leave Expected Return/Volatility at their defaults, click into and out of each field without entering a value, and confirm inline red error text appears exactly as it does for "Initial Amount" today. Repeat for Multiple Goals mode (retirement holdings not summing to 100%, a goal with `ends_year <= starts_year`). Screenshot for the record.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ParametersStep.tsx
git commit -m "feat: complete inline field validation on Parameters step (parity with Backtest's AssumptionsStep)"
```

---

### Task 4: Multi-goal editor — restyle to match the row-repeater pattern used elsewhere

**Files:**
- Modify: `frontend/src/components/ParametersStep.tsx`
- Modify: `frontend/src/styles.css`

**Reference:** `frontend/src/styles.css`'s own `.holdings-row`/`.holdings-head`/`.holdings-foot` rules (used by `PortfolioStep.tsx`'s fund rows and this file's own `RetirementAllocationTable`) — the goal-row editor should look like a variant of the *same* row-repeater pattern already used twice elsewhere in this app, not a visually distinct bordered-card component.

**Interfaces:** No prop/type changes — this task is CSS + JSX structure only, `NamedGoal`'s shape is unchanged.

- [ ] **Step 1: Replace `.goal-row`'s CSS with a `.holdings-row`-style rule**

In `frontend/src/styles.css`, replace:

```css
.goals-table { display: flex; flex-direction: column; gap: 10px; }
.goal-row { display: grid; grid-template-columns: 1fr 120px 110px 110px 110px 110px 54px; gap: 10px; align-items: center; padding: 12px; border: 1px solid var(--border); border-radius: var(--r-md); background: var(--surface-2); }
.goal-row input, .goal-row select { border: 1px solid var(--border-strong); border-radius: var(--r-sm); padding: 8px 10px; background: var(--surface); color: var(--text-primary); font-size: 13px; width: 100%; }
.goal-row input:focus, .goal-row select:focus { outline: none; box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent); border-color: var(--accent); }
.goal-row button { border: 1px solid var(--border); background: var(--surface); border-radius: var(--r-sm); height: 44px; padding: 0 12px; color: var(--text-tertiary); cursor: pointer; font-size: 13px; transition: background .15s, border-color .15s; }
.goal-row button:hover { background: var(--danger-soft); color: var(--danger); border-color: var(--danger-soft-border); }
@media (max-width: 900px) { .goal-row { grid-template-columns: 1fr; gap: 8px; } .goal-row input, .goal-row select, .goal-row button { width: 100%; } }
```

with:

```css
.goals-table { display: flex; flex-direction: column; gap: 10px; }
.goals-head, .goal-row { display: grid; grid-template-columns: 1.4fr 120px 100px 100px 100px 120px 36px; gap: 10px; align-items: start; }
.goals-head { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; color: var(--text-secondary); padding: 0 2px; }
.goal-row { padding: 0; border: 0; border-bottom: 1px solid var(--border); background: none; padding-bottom: 12px; margin-bottom: 2px; }
.goal-row input, .goal-row select { border: 1px solid var(--border); border-radius: var(--r-sm); padding: 9px 10px; background: var(--surface); color: var(--text-primary); font-size: 13px; width: 100%; height: 38px; }
.goal-row input:focus, .goal-row select:focus { outline: none; box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent); border-color: var(--accent); }
.goal-row .icon-btn { border: 1px solid var(--border); background: var(--surface); border-radius: var(--r-sm); height: 38px; width: 36px; display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); cursor: pointer; transition: background .15s, border-color .15s; }
.goal-row .icon-btn:hover { background: var(--danger-soft); color: var(--danger); border-color: var(--danger-soft-border); }
@media (max-width: 900px) {
  .goals-head { display: none; }
  .goal-row { grid-template-columns: 1fr; gap: 8px; }
}
```

(This matches `.holdings-row`'s "plain grid row with a bottom border, no card background" look, `.holdings-foot`'s `.icon-btn` remove-button style, and `.holdings-head`'s uppercase column-label convention — all already defined and used by `PortfolioStep.tsx`.)

- [ ] **Step 2: Add a column-header row and switch the remove button to an icon button**

In `ParametersStep.tsx`'s `GoalsTable`, import `X` from `lucide-react` at the top of the file (extend the existing `import { Info } from "lucide-react";` to `import { Info, X } from "lucide-react";`). Replace `GoalsTable`'s return JSX:

```tsx
  return (
    <div className="goals-table">
      {goals.map((goal, index) => (
        <div className="goal-row" key={index}>
```

with:

```tsx
  return (
    <div className="goals-table">
      <div className="goals-head">
        <div>Purpose</div>
        <div>Type</div>
        <div>Amount</div>
        <div>Starts</div>
        <div>Ends</div>
        <div>Frequency</div>
        <div />
      </div>
      {goals.map((goal, index) => (
        <div className="goal-row" key={index}>
```

And replace the remove button:

```tsx
          <button className="btn btn-ghost" type="button" onClick={() => removeGoal(index)}>Remove</button>
```

with:

```tsx
          <button aria-label="Remove goal" className="icon-btn" type="button" onClick={() => removeGoal(index)}>
            <X size={15} />
          </button>
```

- [ ] **Step 3: Match the "+ Add" button style to `PortfolioStep`'s "+ Add fund"**

Replace:

```tsx
      <button type="button" className="link-btn" onClick={addGoal}>+ Add goal</button>
```

with:

```tsx
      <button type="button" className="add-asset" onClick={addGoal}>+ Add goal</button>
```

(`.add-asset` is the same class `PortfolioStep.tsx`'s "+ Add fund" button uses — already defined in `styles.css`.)

- [ ] **Step 4: Typecheck and build**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [ ] **Step 5: Manual verification via Browser pane**

Load the app, switch Cashflow mode to "Multiple goals", add 2-3 goals, and confirm the row layout, spacing, column headers, and remove-button style visually match `PortfolioStep`'s fund-holdings table (same border/spacing rhythm, no card background). Screenshot for the record.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ParametersStep.tsx frontend/src/styles.css
git commit -m "fix: restyle multi-goal editor to match the holdings-row pattern used elsewhere"
```

---

### Task 5: Fix "Running backtest…" copy-paste leftover in `RunOverlay`

**Files:**
- Modify: `frontend/src/components/RunOverlay.tsx`

**Context:** `RunOverlay.tsx` was copied from Backtest and never had its copy adapted — it currently says "Running backtest…" and "Computing backtest" even though this app runs Monte Carlo simulations, not backtests. Discovered via a live e2e run's error snapshot during this project's Task 21 (see the SDD ledger) but never fixed until now.

**Interfaces:** No prop/type changes.

- [ ] **Step 1: Fix the stage labels and heading**

Replace:

```typescript
const STAGES = ["Validating inputs", "Loading SEC NAV cache", "Computing backtest", "Preparing report"];
```

with:

```typescript
const STAGES = ["Validating inputs", "Loading SEC NAV cache", "Running simulation paths", "Preparing report"];
```

Replace:

```tsx
        <h4>Running backtest&hellip;</h4>
```

with:

```tsx
        <h4>Running simulation&hellip;</h4>
```

- [ ] **Step 2: Typecheck and build**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [ ] **Step 3: Manual verification**

Trigger a simulation run in the Browser pane and confirm the overlay reads "Running simulation…" with a "Running simulation paths" stage, not "backtest" anywhere.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/RunOverlay.tsx
git commit -m "fix: replace leftover 'backtest' copy in RunOverlay with simulation-appropriate text"
```

---

### Task 6: Results view — panel/grid layout parity (Growth tab)

**Files:**
- Modify: `frontend/src/components/ResultsView.tsx`

**Reference:** `../Backtest Portfolio Webull:SEC OPENAI/frontend/src/components/RunSummary.tsx`'s tab bodies, which lay sibling `.chartPanel` sections (each already self-contained via `AxisCurve`/`DataTable`, including their own `<h3>`/`.panelHeader compact`) inside a `.panelGrid` wrapper for a responsive 2-up grid, with NO outer `.card`/`<h2>` wrapper around the whole tab body. Monte Carlo's `charts.tsx#AxisCurve` already renders `.chartPanel`/`.panelHeader compact`/`<h3>{title}</h3>` internally (confirmed identical to Backtest's own chart panels) — the mismatch is purely at the call site in `ResultsView.tsx`, which wraps everything in an extra `<div className="card"><h2>Growth</h2>...`.

**Interfaces:** No prop/type changes.

- [ ] **Step 1: Remove the outer card/h2 wrapper and use `.panelGrid` for the Growth tab**

Replace `GrowthTab`'s return JSX:

```tsx
  return (
    <div className="card">
      <h2>Growth</h2>
      <AxisCurve
        title="Simulated Portfolio Balances"
        series={fanSeries}
        valueFormat={(v) => v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        xFormat={(v) => `Yr ${v}`}
      />
      <AxisCurve
        title="Portfolio Survival Over Time"
        series={survivalSeries}
        valueFormat={(v) => `${v.toFixed(1)}%`}
        xFormat={(v) => `Yr ${v}`}
      />
    </div>
  );
```

with:

```tsx
  return (
    <div className="panelGrid">
      <AxisCurve
        title="Simulated Portfolio Balances"
        series={fanSeries}
        valueFormat={(v) => v.toLocaleString(undefined, { maximumFractionDigits: 0 })}
        xFormat={(v) => `Yr ${v}`}
      />
      <AxisCurve
        title="Portfolio Survival Over Time"
        series={survivalSeries}
        valueFormat={(v) => `${v.toFixed(1)}%`}
        xFormat={(v) => `Yr ${v}`}
      />
    </div>
  );
```

- [ ] **Step 2: Typecheck and build**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [ ] **Step 3: Manual verification via Browser pane**

Run a simulation, open the Growth tab, and confirm the two charts now render as a responsive 2-up grid (side by side on desktop width, stacked on narrow width) matching Backtest's Drawdown tab's `.panelGrid` behavior, rather than stacked full-width cards. Screenshot for the record.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ResultsView.tsx
git commit -m "fix: use panelGrid layout for Growth tab charts (parity with Backtest's RunSummary)"
```

---

### Task 7: Results view — panel/grid layout parity (Distribution, Metrics, Risk & Correlation tabs)

**Files:**
- Modify: `frontend/src/components/ResultsView.tsx`

**Interfaces:** No prop/type changes.

- [ ] **Step 1: Read the current structure of the three tabs**

```bash
sed -n '/function DistributionTab/,/^function MetricsTab/p' frontend/src/components/ResultsView.tsx
sed -n '/function MetricsTab/,/^function RiskTab/p' frontend/src/components/ResultsView.tsx
sed -n '/function RiskTab/,/^function GoalsTab/p' frontend/src/components/ResultsView.tsx
```

- [ ] **Step 2: Apply the same fix pattern as Task 6 to each tab**

For each of `DistributionTab`, `MetricsTab`, `RiskTab`: if the tab's return JSX wraps its content in `<div className="card"><h2>...</h2>...</div>`, remove that outer wrapper. Any pair (or more) of sibling elements that are themselves already self-contained panel components (an `AxisCurve` call, a `Histogram` call, or a `<section className="chartPanel">...</section>` block) should be grouped inside `<div className="panelGrid">...</div>` instead of being direct children of a `<div className="card">`. Elements that are full-width by nature (e.g. a wide `DataTable`/`.tables` grid, or a single chart meant to span the row) stay outside `.panelGrid`, as their own top-level sibling — matching how Backtest's `RunSummary.tsx` mixes full-width `DataTable`s with `.panelGrid`-wrapped chart pairs (see the reference lines noted in Task 6).

Do not change any data-fetching, calculation, or the charts' own internal rendering (`AxisCurve`, `Histogram`, `CorrelationMatrix`, `DataTable` in `charts.tsx` are out of scope for this task) — only the wrapper JSX around them in `ResultsView.tsx`.

- [ ] **Step 3: Typecheck and build after each tab's edit**

Run: `npm --prefix frontend run build`
Expected: PASS after each of the three tabs is edited.

- [ ] **Step 4: Manual verification via Browser pane, tab by tab**

For each of Distribution, Metrics, and Risk & Correlation: run a simulation, open the tab, take a screenshot, and compare against Backtest's closest-matching tab (Returns tab for Distribution/Metrics-style content, Metrics tab for Risk & Correlation) opened in a second Browser pane tab. Confirm panel spacing, card grid behavior at desktop width, and typography scale (section headings, panel titles) visually match. Note and fix any remaining mismatch before moving to the next tab.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ResultsView.tsx
git commit -m "fix: use panelGrid layout for Distribution/Metrics/Risk tabs (parity with Backtest's RunSummary)"
```

---

### Task 8: Full verification and final commit

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `pytest backend/tests -q`
Expected: PASS (all tests, including Task 1's new/updated ones).

- [ ] **Step 2: Run the frontend build**

Run: `npm --prefix frontend run build`
Expected: PASS, no TypeScript errors.

- [ ] **Step 3: Re-run the Playwright e2e suite against the real backend**

Start the backend (`uvicorn backend.app.main:app --port 8001`), then:

```bash
cd frontend && node_modules/.bin/playwright test
```

Expected: `1 passed`.

- [ ] **Step 4: Full side-by-side visual pass**

Open Monte Carlo (`http://127.0.0.1:8001`) and Backtest's dev server side by side in two Browser pane tabs. Walk through all 3 steps of both wizards, and the Results/Summary tabs of both, confirming spacing, typography, filter behavior, and multi-goal/goal-row layout now read as visually consistent (same design system, different content) rather than as two independently-designed apps. Note any remaining mismatch as a follow-up item — do not silently skip it.

- [ ] **Step 5: Update the SDD ledger**

Append a summary entry to `.superpowers/sdd/2026-08-04-monte-carlo-webapp/progress.md` (or a new dated ledger file if that one is considered closed) recording this frontend-parity-rebuild plan's completion, the 4 root causes identified, and confirmation of the final e2e + visual pass.

- [ ] **Step 6: Final commit (if the ledger update produced a trackable file)**

```bash
git add -A
git commit -m "docs: record frontend-parity-rebuild completion in SDD ledger" || true
```
