# Formula Audit — Phase 4 Manual Verification (Task 2)

Independent re-read of `backend/app/engine/` (and `backend/app/api/simulate.py`)
against the canonical equations recorded in `docs/manual-verification-refs.md`
(Task 1). Line numbers below are current as of this audit and may differ
slightly from Task 1's citations where the source has drifted.

**Summary:** 16 formulas audited (15 from the refs doc + 1 additional formula
found in code but not catalogued by Task 1) — **8 exact matches**, **5
documented/intentional deviations**, **3 bug candidates** for Task 4/5's
live-number check.

Bug candidates: **TWRR/CAGR conflation** (`percentile_table`), **Sharpe ratio
numerator** (`sharpe_sortino_by_percentile`), **Sortino ratio numerator**
(`sharpe_sortino_by_percentile`).

## Comparison table

| # | Formula | Reference equation | Code (file:line) | Match? | Notes |
|---|---|---|---|---|---|
| 1 | GBM path simulation | `S(t+Δt) = S(t)·exp[(μ−½σ²)Δt + σ√Δt·Z]`, correlated via Cholesky `L` | `backend/app/engine/gbm.py:9-17` | ✅ Exact | `L = np.linalg.cholesky(sigma)` (gbm.py:9), `drift = (mu - 0.5*np.diag(sigma))*dt` (gbm.py:10), `shock = drift + sqrt(dt)*z_corr` (gbm.py:16), `paths[t] = paths[t-1]*exp(shock)` (gbm.py:17). Verbatim. |
| 2 | Constant-mix (rebalanced) portfolio roll-forward | `V(t_k+1⁻) = Σ_i [w_i·V(t_k)]·(S_i(t_k+1)/S_i(t_k))`, re-split by weights each rebalance | `backend/app/engine/statistical.py:35-58`, core loop 49-57 | ✅ Exact | `asset_growth = asset_paths[end]/asset_paths[start]` (statistical.py:52), `portfolio_value = (values_at_period_start*asset_growth).sum(axis=1)` (statistical.py:54), re-split `values_at_period_start = portfolio_value[:,None]*weights[None,:]` (statistical.py:55). Textbook constant-mix roll-forward. |
| 3 | CAGR | `CAGR = (V_end/V_start)^(1/n) − 1` | `backend/app/engine/results.py:27` (`percentile_table`), `results.py:181` (`correlation_and_returns_table`) | ✅ Exact | `cagr = paths[:, -1] ** (1/n_years) - 1` (results.py:27), `cagr = cumulative ** (periods_per_year/n_periods) - 1` (results.py:181) — same formula, `n_periods/periods_per_year ≈ n_years`. |
| 4 | TWRR | `TWRR = [Π(1+R_i)]^(1/n) − 1` on a cashflow-free sub-period return series | `backend/app/engine/results.py:33` (`twrr_nominal = cagr`) | ⚠️ Deviation | See "TWRR/CAGR conflation" below. **[BUG CANDIDATE]** |
| 5 | Maximum drawdown | `MDD = min_t[V(t)/max_{s≤t}V(s) − 1]` | `backend/app/engine/results.py:35-36`; duplicated at `backend/app/engine/orchestrator.py:113-114` | ✅ Exact | `running_max = np.maximum.accumulate(paths, axis=1)`, `max_drawdown = (paths/running_max - 1).min(axis=1)` (results.py:35-36); orchestrator.py:113-114 recomputes identically on `dollar_paths` — scale-invariant so numerically equivalent. |
| 6 | Parametric VaR/ES (Gaussian) | `VaR=−μ+zσ`, `ES=−μ+[φ(z)/(1−α)]σ` | `backend/app/engine/results.py:108-114` | ✅ Exact | `z = norm.ppf(alpha)` (111), `var = -port_mu + z*port_sd` (112), `es = -port_mu + (norm.pdf(z)/(1-alpha))*port_sd` (113). |
| 7 | Historical/simulation VaR/ES | `VaR=Quantile_α(L)`, `ES=E[L\|L≥VaR]`, `L=−(end−start)` | `backend/app/engine/results.py:117-123` | ✅ Exact | `losses = -ending_values` (120), `var_threshold = percentile(losses, alpha*100)` (121), `es = losses[losses>=var_threshold].mean()` (122). |
| 8 | Sharpe ratio | `Sharpe = (R_p − R_f)/σ_p` | `backend/app/engine/results.py:126-139`, `sharpe` at line 134 | ⚠️ Deviation | Numerator is CAGR (geometric total-path return), not canonical arithmetic mean/period return. See below. **[BUG CANDIDATE]** |
| 9 | Sortino ratio | `Sortino = (R_p − MAR)/DD`, `DD=sqrt(E[min(R−MAR,0)²])` | `backend/app/engine/results.py:126-139`, `sortino` at line 135 | ⚠️ Deviation | Same CAGR-numerator issue as Sharpe, plus mixed geometric/arithmetic basis. See below. **[BUG CANDIDATE]** |
| 10 | Safe withdrawal rate (root-find) | Largest constant `w` s.t. `Balance_n ≥ 0` under sequential compounding | `backend/app/engine/results.py:142-160`, `brentq` call at 158 | ⚠️ Deviation | Root-found percentage-of-$1-initial-balance per Monte Carlo path, not Bengen's original fixed-dollar single-sequence grid search. **[DOCUMENTED]** — see below. |
| 11 | Perpetual withdrawal rate | `PWR = μ − ½σ²` | `backend/app/engine/results.py:162-165` | ✅ Exact | `pwr = per_path_annual_returns - 0.5*per_path_vol**2` (165). |
| 12 | Bootstrap historical resampling (iid + block) | iid resample w/ replacement; block bootstrap draws contiguous length-`L` blocks | `backend/app/engine/historical.py:11-17` (iid), `:45-60` (`_block_bootstrap`) | ✅ Match, edge case noted | `rng.choice(..., replace=True)` (13, 16) is exact iid bootstrap. `_block_bootstrap`'s `mode="wrap"` padding (historical.py:57) is only reachable when `n_available < block_years` (start range is `[0, n_available-block_years]` inclusive, so blocks never overrun in the normal case) — the "wrap boundary correlation loss" the refs doc flagged is effectively unreachable in practice. **[DOCUMENTED]** |
| 13 | GARCH(1,1) volatility + drift re-injection | `σ_t² = ω+αε²_{t-1}+βσ²_{t-1}`, `r_t=μ_t+σ_t z_t` | `backend/app/engine/forecasted.py:21-45`, drift re-add at line 43 | ⚠️ Deviation | `mean="Zero"` fit + externally re-added `daily_mu`, justified in-code. See below. **[DOCUMENTED]** |
| 14 | Inflation adjustment (Fisher) | `(1+r_nom)=(1+r_real)(1+π)`; `I_n=Π(1+π_t)` | `backend/app/engine/inflation.py:4-18`; `goals.py::_inflation_factors:59-70` | ✅ Exact | `simulate_inflation` draws `π_t~N(mean,vol)` or bootstraps CPI (inflation.py:13,16); `_inflation_factors` computes `np.cumprod(1.0+inflation_draws, axis=1)` (goals.py:70) = `I_n` exactly; `results.py:46` divides nominal ending balance by `cumulative_inflation` — exact discrete Fisher deflation. |
| 15 | Glide-path weight interpolation | Linear interpolation between `w_start`/`w_end` over window `G` | `backend/app/engine/goals.py::glide_path_weights:117-138` | ✅ Exact | `progress = min(1.0, (years_to_retirement-year)/glide_path_years)` (136), `return start_weights*progress + end_weights*(1-progress)` (137); pre/post-window flat segments via the `year <= years_to_retirement` guard (135) and final `return end_weights` (138). Linear-interpolation design choice, not a single-paper formula — see below. **[DOCUMENTED]** |
| 16 | Goal/cashflow roll-forward | `Balance_{t+1} = max(Balance_t·(1+R_t) ± CF_t, 0)` | `backend/app/engine/goals.py::apply_cashflow:4-45`, `apply_named_goals:73-114` | ✅ Exact | `grown = values[:,year]*growth_factors[:,year]` (37, 92), `values[:,year+1] = max(grown + sign*amount, 0.0)` (44) / `max(new_balance, 0.0)` (103). |
| — | **[Not in refs doc]** Fat-tailed (Student-t) return draw | Scaled Student-t: `X = μ + σ·T/sqrt(dof/(dof-2))`, `T~t_dof` | `backend/app/engine/parameterized.py:13-17` | ✅ Exact, uncited | `scale = sigma/sqrt(dof/(dof-2))` (16) is the standard variance-matching scale for Student-t (Var(T)=dof/(dof-2)); `annual_returns = mu + scale*raw` (17). Arithmetically correct and internally consistent, but this formula was not catalogued in `manual-verification-refs.md` — a Task 1 coverage gap, not a code bug. |

## Deviations and Classifications

**TWRR/CAGR conflation (`results.py::percentile_table`, line 33).** The code
sets `twrr_nominal = cagr` with the comment "TWRR strips cashflow timing by
construction (it's a ratio of period-end to period-start values) — on this
array, nominal TWRR and CAGR coincide." This claim is true only when the
`paths` array being ratio'd has never had a contribution or withdrawal
applied to it — i.e., the plain-growth (no-cashflow) case. But
`percentile_table` is called from `orchestrator.py:88-91` on
`normalized_paths = dollar_paths / initial_amount`, where `dollar_paths` is
the *output of* `apply_cashflow`/`apply_named_goals` whenever the request
includes a cashflow or named goals — meaning the balance ratio being labeled
"TWRR" already has withdrawal/contribution effects baked into its level.
True TWRR is specifically constructed to strip cashflow-timing effects by
linking sub-period *returns* (not raw balance ratios) around each cashflow
event; simply taking `(ending balance/starting balance)^(1/n)-1` on a
post-cashflow balance array does not do that — it conflates manager-skill
return with the dollar effect of contribution/withdrawal timing and size,
which is precisely what TWRR is defined to exclude. The refs doc itself
flags this exact concern ("Task 2 should confirm this holds for the
`withdraw_percent` and multi-goal paths as well as the fixed-dollar cashflow
path") and, having traced the call graph, it does not hold — `percentile_table`
has no separate "growth-only" branch for the TWRR field the way it does for
`max_drawdown_excl_cashflows` (which explicitly branches on
`growth_only_paths`). The in-code comment asserts a mathematical
equivalence that is false in the presence of cashflows, so this is not
merely a documented simplification — it is a mislabeled/miscalculated field
whenever a run has withdrawals, contributions, or named goals. Task 4/5
should numerically compare `twrr_nominal` against `cagr` and against a
correctly cashflow-adjusted TWRR on a run with a non-trivial cashflow to
confirm whether the reported number is misleading. **[BUG CANDIDATE]**

**Sharpe and Sortino ratio numerators (`results.py::sharpe_sortino_by_percentile`,
lines 126-139).** Both ratios use `per_path_annual_returns = paths[:, -1] **
(1/n_years) - 1` (line 128) — the per-path CAGR, a geometric total-return
figure — as the numerator `R_p`, against denominators built from
`_safe_period_returns` (per-period arithmetic returns, line 129). The
canonical Sharpe/Sortino definitions (Sharpe 1994; Sortino & Price 1994) use
`R_p` as the mean *period* return (typically arithmetic mean of the same
return series the volatility/downside-deviation is computed from), so that
numerator and denominator are built from the same statistic basis. Here the
numerator is a geometric compounding of the whole path while the
denominator is a dispersion statistic (`std`, downside-RMS) computed
directly on the per-period arithmetic series — a basis mismatch between
"total compounded growth annualized" and "average period volatility/downside."
For paths sampled at annual granularity (`statistical.py`'s `annual_idx`
selection, `historical.py`, `forecasted.py`, `parameterized.py` — all
produce one data point per year) both quantities are nominally "annual," so
this is not a *units* mismatch (contrary to what the refs doc's
"annualization mismatch" framing suggested — `per_path_vol * np.sqrt(1)`
at results.py:130 is a no-op precisely because periods are already
annual), but it remains a *statistic-basis* mismatch: CAGR is not the same
number as the arithmetic mean of the same annual return series whenever
returns are volatile (Jensen's-gap between geometric and arithmetic means),
so the ratio is not a strict textbook Sharpe/Sortino computed consistently
from one return series. No code comment addresses or justifies this choice
for either ratio. Task 4/5 should compute Sharpe/Sortino by hand on a fixed
seed's per-path annual return series using both the code's CAGR-based
numerator and a strict arithmetic-mean numerator, and check whether the
resulting percentile bands differ meaningfully. **[BUG CANDIDATE]**
(applies to both formulas #8 and #9 in the table above)

**Safe withdrawal rate via `brentq` (`results.py::withdrawal_rates_by_percentile`,
lines 142-160).** The code root-finds, per simulated path, a constant
withdrawal rate `r` (as a fraction of the path's normalized $1 starting
balance) such that the terminal balance hits exactly 0
(`brentq(final_balance, 0.0, 1.0, xtol=1e-4)`, line 158), falling back to
`swr[i] = 0.0 if final_balance(1.0) > 0 else 1.0` on `ValueError` (bracket
failure, lines 159-160) — i.e. if even withdrawing 100%/yr still leaves a
positive terminal balance, `swr` is reported as `1.0` (the search bracket's
edge), and if the sign doesn't bracket a root any other way it falls back to
`0.0`. This is a per-path Monte Carlo generalization of Bengen's (1994)
single fixed-historical-sequence, fixed-dollar-withdrawal grid search, not a
literal reproduction of Bengen's method — `manual-verification-refs.md`
itself explicitly documents this as "a reasonable per-path Monte Carlo
generalization but structurally different from the cited paper's method;
flagged for explicit note in Task 2's audit rather than treated as a literal
formula match" (refs doc, "Judgment calls" item 3). Because this deviation
is explicitly named and reasoned about in a committed project document
(Task 1's refs doc), and the code's root-finding logic is internally
consistent with the modernized definition it sets out to implement (find
the constant rate that exactly depletes the path), this is a deliberate,
already-documented generalization rather than an unexplained bug. **[DOCUMENTED]**

**Bootstrap block-wrap edge case (`historical.py::_block_bootstrap`, line 57).**
The refs doc flagged that using `np.pad(..., mode="wrap")` for short
trailing blocks might "understate block-length correlation loss at the wrap
boundary." Tracing the sampling logic: `start = rng.integers(0, max(1,
n_available - block_years + 1))` (historical.py:54) draws `start` uniformly
from `[0, n_available - block_years]` inclusive (NumPy's `integers` upper
bound is exclusive), so `start + block_years <= n_available` always holds
whenever `n_available >= block_years` — meaning `block = annual_returns[start
:start+block_years]` always has the full requested length and the
`len(block) < block_years` branch (line 56) is unreachable in that regime.
The wrap-padding path only fires in the degenerate case where the available
historical annual-return series is shorter than the requested block length
(`n_available < block_years`), which is a configuration-validation concern
(is `block_years` sane relative to the fund's history) rather than a
systematic correlation-loss issue baked into ordinary block bootstrap
sampling. This is a benign, self-documenting implementation detail (the
docstring at historical.py:46-47 explains the mechanism), not a formula
error. **[DOCUMENTED]**

**GARCH(1,1) drift re-injection (`forecasted.py::_garch_annual_returns`,
lines 21-45).** The code fits `arch_model(..., vol="Garch", p=1, q=1,
dist="normal", mean="Zero")` on demeaned percentage daily returns (line 38),
then re-adds an externally computed `daily_mu = port_mu / 252` to each
simulated daily shock before compounding (`sim_daily = daily_mu +
sim_daily_shock_pct`, line 43, compounded via `np.prod(1+sim_daily, axis=2)
- 1` at line 45). The arithmetic is correct — `daily_mu` is added once per
simulated day before the day is compounded, matching the GARCH(1,1) mean
equation `r_t = μ_t + ε_t` applied per-day rather than double-counted or
omitted. The in-code docstring (forecasted.py:22-25) explicitly justifies
using `mean="Zero"` plus external drift re-injection by citing an MLE
convergence problem on this dataset ("arch_model's mean='Constant' MLE
produces absurd drift estimates on this data (~19.9%/yr annualized vs.
~12.2%/yr simple historical mean)") and says "See CLAUDE.md landmines" —
however, the current `CLAUDE.md` in this project's directory (checked in
full) does **not** contain a landmine entry about GARCH or `arch_model` MLE
behavior; its four landmines cover pandas 3.0, NAV gap handling, server-side
date-range validation, and the Docker colon-path bind-mount issue. This is a
dangling/stale documentation cross-reference (the comment points to a
CLAUDE.md landmine that isn't there), but the underlying engineering
justification is still stated in-code and the arithmetic itself checks out,
so the *formula* deviation is documented even though the specific pointer
is broken. **[DOCUMENTED]** (with a noted doc-hygiene gap: the "See CLAUDE.md
landmines" cross-reference in forecasted.py:24 does not currently resolve to
any such entry)

**Glide-path linear interpolation citation strength (`goals.py::glide_path_weights`,
lines 117-138).** The refs doc notes this formula has no single-paper
citation and is instead grounded in industry practice (Vanguard glide-path
methodology, target-date-fund literature). This is not a code-vs-citation
mismatch — the implementation is an exact linear interpolation and the
function's own docstring (goals.py:127-129) states the schedule "matches
the schedule already shipped in `frontend/src/api/mockData.ts`," which is
the actual load-bearing consistency requirement here (frontend mock parity,
not academic-paper fidelity), and the same docstring explains
`glide_path_orchestration.simulate_with_glide_path` and `orchestrator.py`'s
displayed chart both call this one function so the simulation and the
displayed allocation cannot drift apart. A linear glide path is a documented
design choice, not a derived formula from a specific paper, so there is
nothing to reconcile against a citation beyond confirming (done here) that
the interpolation math itself is a standard/correct linear blend. **[DOCUMENTED]**

**GBM rebalancing vs. the other three models (`statistical.py`, `CLAUDE.md`
landmines section).** `statistical.py::simulate_statistical`'s GBM
("normal") branch combines per-asset price paths via `asset_paths @
weights` (statistical.py:21) — a drifting-weight, buy-and-hold computation
with no rebalancing — **only when** `config.get("rebalancing", "annual")`
resolves to `None` in `_REBALANCE_STEPS_PER_YEAR` (i.e. `rebalancing ==
"none"`, statistical.py:16-23); for every other rebalancing-frequency value
(the default `"annual"`, plus `"semiannual"`, `"quarterly"`, `"monthly"`) it
instead calls `_rebalanced_portfolio_values` (statistical.py:24), which
applies the constant-mix roll-forward from formula #2 above. This exactly
matches the current repo `CLAUDE.md`'s landmine: "`statistical_sim.py`'s
GBM model combines per-asset price paths via `asset_paths @ weights`, which
is a drifting-weight computation with no rebalancing, unlike the other 3
models (which bootstrap already-portfolio-weighted annual returns,
implicitly rebalancing every draw). The Rebalancing Frequency parameter must
apply consistently across all 4 models — see `engine/statistical.py`."
Tracing `historical.py`, `forecasted.py`, and `parameterized.py` confirms
they all bootstrap/sample already-portfolio-weighted (`weights @ mu`,
`returns_df @ weights`) annual return series and `cumprod` them directly —
i.e. every draw is implicitly a full rebalance to target weights, with no
separate rebalancing-frequency branch — consistent with the CLAUDE.md
landmine's description. The GBM model is therefore the only one of the four
where the Rebalancing Frequency parameter has a code path that changes
behavior (drifting-weight buy-and-hold vs. constant-mix), and that
divergence is explicitly called out and required to "apply consistently" by
the landmine text quoted above. **[DOCUMENTED]**

## Scope note

This audit is limited to `backend/app/engine/` and `backend/app/api/simulate.py`
per the task instructions. `orchestrator.py` and `glide_path_orchestration.py`
were checked for formula duplication; the only duplicated formula found is
maximum drawdown (row 5), which is a scale-invariant recomputation on
dollar-denominated paths and numerically equivalent to the normalized-path
version in `results.py`. No inline formula logic beyond simple wiring/plumbing
was found in `backend/app/api/simulate.py` proper (`backend/app/api/`
directory contains `simulate.py`; all quantitative formulas live in `engine/`
and are imported into `orchestrator.py`, which `simulate.py` calls).
