# Formula Reference Citations — Phase 4 Manual Verification (Task 1)

This document enumerates every distinct quantitative formula implemented in
`backend/app/engine/` and pairs it with one authoritative citation, for Task 2
(code-vs-citation audit) to consume row-by-row. Citations were verified via
`hyperresearch fetch` (per repo `CLAUDE.md`) wherever a live, non-paywalled
page was reachable; canonical textbook/journal citations that could not be
fetched directly (paywalled JSTOR/ScienceDirect, 404s) are recorded from
well-established bibliographic record and flagged below.

## Geometric Brownian Motion path simulation
- **Code:** `backend/app/engine/gbm.py::simulate_gbm_paths` (lines 4–18)
- **Citation:** Hull, J.C., *Options, Futures, and Other Derivatives*, 9th ed., Pearson, 2014, ch. 14 ("The Black–Scholes–Merton Model"), §14.3 "The Lognormal Property of Stock Prices"; corroborated by Glasserman, P., *Monte Carlo Methods in Financial Engineering*, Springer, 2003, ch. 3 §3.2 "Brownian Motion and Geometric Brownian Motion". Cross-checked against: "Geometric Brownian motion", Wikipedia (fetched via hyperresearch, `research/notes/geometric-brownian-motion-wikipedia.md`), which cites the identical discretization.
- **Canonical equation:** For a driftless-in-log GBM, the exact discretized SDE solution is
  `S(t+Δt) = S(t) · exp[(μ − ½σ²)Δt + σ√Δt · Z]`, `Z ~ N(0,1)`.
  For a correlated multi-asset system with covariance Σ = L Lᵀ (Cholesky), the correlated shocks are `z_corr = L z_indep`, giving per-asset
  `S_i(t+Δt) = S_i(t) · exp[(μ_i − ½Σ_ii)Δt + √Δt · (L z)_i]`.
- **Code match:** `gbm.py` lines 9–17 implement exactly this — `L = cholesky(sigma)`, `drift = (mu - 0.5*diag(sigma))*dt`, `shock = drift + sqrt(dt)*z_corr`, `paths[t] = paths[t-1] * exp(shock)`. Verbatim match to the Hull/Glasserman discretization.

## Portfolio rebalancing value roll-forward
- **Code:** `backend/app/engine/statistical.py::_rebalanced_portfolio_values` (lines 35–58)
- **Citation:** This is a standard periodic-rebalancing roll-forward, not itself a named theorem; the underlying reference is the same GBM asset-path construction as above (Hull ch. 14 / Glasserman ch. 3), combined with the mechanics of "buy-and-hold vs. constant-mix (rebalanced) portfolios" as described in Perold, A. & Sharpe, W. (1988), "Dynamic Strategies for Asset Allocation," *Financial Analysts Journal*, 44(1), 16–27 (constant-mix rebalancing definition — value at each rebalance date is redistributed to target weights, then compounded by each asset's subsequent return).
- **Canonical equation:** At each rebalance date `t_k`, dollar allocation to asset `i` is reset to `w_i · V(t_k)`. Over the following sub-period, `V(t_k+1⁻) = Σ_i [w_i · V(t_k)] · (S_i(t_k+1)/S_i(t_k))`, then re-split by weights again at `t_k+1`.
- **Code match:** `_rebalanced_portfolio_values` lines 46–58: `values_at_period_start = weights * portfolio_value` at each rebalance step, `asset_growth = asset_paths[end]/asset_paths[start]`, `portfolio_value = (values_at_period_start * asset_growth).sum(axis=1)`. This is the textbook constant-mix roll-forward.

## CAGR (Compound Annual Growth Rate)
- **Code:** `backend/app/engine/results.py::percentile_table` (line 27, `cagr = paths[:, -1] ** (1/n_years) - 1`) and `results.py::correlation_and_returns_table` (line 181)
- **Citation:** Standard finance-textbook definition; e.g. Bodie, Z., Kane, A., Marcus, A., *Investments*, 12th ed., McGraw-Hill, ch. 5 "Learning About Return and Risk from the Historical Record". Also documented in CFA Institute's Global Investment Performance Standards (GIPS) glossary as the geometric compounding basis for annualized return (attempted direct fetch of `gipsstandards.org` returned 404; citation retained from CFA curriculum standard).
- **Canonical equation:** `CAGR = (V_end / V_start)^(1/n) − 1`, where `n` is the number of years.
- **Code match:** exact — `paths[:, -1]` is `V_end/V_start` (paths are normalized to start at 1.0), so `paths[:,-1]**(1/n_years) - 1` matches directly.

## Time-Weighted Rate of Return (TWRR)
- **Code:** `backend/app/engine/results.py::percentile_table` (lines 31–33, `twrr_nominal = cagr`)
- **Citation:** CFA Institute, *Global Investment Performance Standards (GIPS)*, "Time-Weighted Rate of Return" definition — geometric linking of sub-period returns that removes the distorting effect of external cashflow timing/size. (Direct fetch of the GIPS glossary page and CFA Institute refresher-reading URL both 404'd during this session; the definition below is the well-established GIPS standard and is cross-referenced in Bodie/Kane/Marcus ch. 24 "Portfolio Performance Evaluation," §"Time-Weighted Returns versus Dollar-Weighted Returns.")
- **Canonical equation:** `TWRR = [(1+R_1)(1+R_2)···(1+R_n)]^(1/n) − 1`, where each `R_i` is a sub-period return computed on a cashflow-free (or cashflow-adjusted) basis.
- **Code match / judgment call:** The code comment at `results.py` line 31–32 explicitly notes: "TWRR strips cashflow timing by construction (it's a ratio of period-end to period-start values) — on this array, nominal TWRR and CAGR coincide." This is only strictly true because `paths` here is the *normalized growth-factor* array (post-cashflow dollar balance divided by initial amount), not a true sub-period-linked return series that isolates manager skill from cashflow timing — see Task 2 audit note below.

## Maximum drawdown
- **Code:** `backend/app/engine/results.py::percentile_table` (lines 35–36) and `orchestrator.py` (lines 113–114)
- **Citation:** Magdon-Ismail, M. & Atiya, A.F. (2004), "Maximum Drawdown," *Risk*, 17(10), 99–102. Practitioner-level corroboration fetched via hyperresearch: "Understanding Maximum Drawdown (MDD): Key Insights and Formula," Investopedia (`research/notes/understanding-maximum-drawdown-mdd-key-insights-and-formula.md`), which states the identical running-peak-to-trough definition.
- **Canonical equation:** `MDD = min_{0≤t≤T} [ V(t) / max_{0≤s≤t} V(s) − 1 ]`, i.e. the largest peak-to-trough percentage decline over the observed path.
- **Code match:** exact — `running_max = maximum.accumulate(paths, axis=1)`, `max_drawdown = (paths/running_max - 1).min(axis=1)`.

## Parametric VaR / Expected Shortfall (Gaussian)
- **Code:** `backend/app/engine/results.py::parametric_var_es` (lines 108–114)
- **Citation:** Jorion, P., *Value at Risk: The New Benchmark for Managing Financial Risk*, 3rd ed., McGraw-Hill, 2007, ch. 5 ("Portfolio Risk: Analytical Methods") and ch. 6 ("Identifying Risk: Coherent Risk Measures"); J.P. Morgan/Reuters, *RiskMetrics — Technical Document*, 4th ed., 1996, §"Forecasting Volatility and Correlations" (attempted direct RiskMetrics PDF fetch not performed this session — well-established as the origin of the parametric normal-VaR methodology; Jorion ch. 5 is the standard textbook restatement).
- **Canonical equation:** For portfolio return `R ~ N(μ_p, σ_p²)` and confidence level `α`:
  `VaR_α = −μ_p + z_α·σ_p`, where `z_α = Φ⁻¹(α)`.
  `ES_α = −μ_p + [φ(z_α)/(1−α)]·σ_p`, where `φ` is the standard normal PDF (this is the closed-form Gaussian tail-expectation formula, e.g. Jorion ch. 5, eq. for "Expected Shortfall under Normality," also derivable from the truncated-normal mean).
- **Code match:** exact — `z = norm.ppf(alpha)`, `var = -port_mu + z*port_sd`, `es = -port_mu + (norm.pdf(z)/(1-alpha))*port_sd`.

## Historical/simulation VaR and Expected Shortfall
- **Code:** `backend/app/engine/results.py::compute_var_es` (lines 117–123)
- **Citation:** Jorion, P., *Value at Risk*, 3rd ed., 2007, ch. 9 ("Monte Carlo Methods") and ch. 4 ("Historical Simulation Method") — VaR as the empirical quantile of a simulated/historical loss distribution, ES as the conditional mean of losses beyond that quantile.
- **Canonical equation:** `VaR_α = Quantile_α(L)` where `L = −(ending value − initial value)` is the loss distribution across simulated paths; `ES_α = E[L | L ≥ VaR_α]`.
- **Code match:** exact — `losses = -ending_values`, `var_threshold = percentile(losses, alpha*100)`, `es = losses[losses >= var_threshold].mean()`.

## Sharpe ratio
- **Code:** `backend/app/engine/results.py::sharpe_sortino_by_percentile` (lines 126–139, `sharpe` branch)
- **Citation:** Sharpe, W.F. (1994), "The Sharpe Ratio," *The Journal of Portfolio Management*, 21(1), 49–58. Verified via hyperresearch fetch: "Sharpe Ratio: Definition, Formula, and Examples," Investopedia (`research/notes/sharpe-ratio-definition-formula-and-examples.md`), which states the same reward-to-variability definition and attributes it to Sharpe (1994) generalizing his 1966 "reward-to-variability ratio."
- **Canonical equation:** `Sharpe = (R_p − R_f) / σ_p`, where `R_p` is portfolio return, `R_f` the risk-free rate, `σ_p` the standard deviation of portfolio returns.
- **Code match:** exact — `sharpe = (per_path_annual_returns - risk_free_rate) / per_path_vol`, with `per_path_vol` the std-dev of per-period returns and `risk_free_rate` defaulting to 0.

## Sortino ratio
- **Code:** `backend/app/engine/results.py::sharpe_sortino_by_percentile` (lines 126–139, `sortino` branch)
- **Citation:** Sortino, F.A. & Price, L.N. (1994), "Performance Measurement in a Downside Risk Framework," *The Journal of Investing*, 3(3), 59–64. Verified via hyperresearch fetch: "Sortino Ratio: A Comprehensive Definition and Calculation Guide," Investopedia (`research/notes/sortino-ratio-a-comprehensive-definition-and-calculation-guide.md`), attributing the downside-deviation-only ratio to Sortino & Price (1994) and Sortino & van der Meer (1991).
- **Canonical equation:** `Sortino = (R_p − MAR) / DD`, where `MAR` is the minimum acceptable return (0 here) and `DD = sqrt( E[min(R − MAR, 0)²] )` is the downside deviation.
- **Code match:** exact — `downside = where(per_period_returns < 0, per_period_returns, 0.0)`, `per_path_downside_vol = sqrt((downside**2).mean(axis=1))`, `sortino = (per_path_annual_returns - risk_free_rate) / per_path_downside_vol`. Judgment call: the code uses `per_path_annual_returns` (annualized total-path CAGR) as the numerator against a per-period downside vol denominator — a mixed annualization the Task 2 audit should check against Sortino's original per-period specification.

## Safe withdrawal rate (root-finding depletion rate)
- **Code:** `backend/app/engine/results.py::withdrawal_rates_by_percentile` (lines 142–160, `swr` via `brentq`)
- **Citation:** Bengen, W.P. (1994), "Determining Withdrawal Rates Using Historical Data," *Journal of Financial Planning*, 7(4), 171–180 — the original "4% rule" paper, defining the safe withdrawal rate as the highest constant (real) withdrawal rate that does not exhaust a portfolio over a fixed horizon under historical/simulated return sequences. Corroborated via hyperresearch fetch of "Trinity study," Wikipedia (`research/notes/trinity-study-wikipedia.md`), which documents Bengen's methodology and the follow-on Cooley/Hubbard/Walz (1998) "Trinity Study" that formalized it via Monte Carlo/historical-simulation success-rate testing — directly analogous to this engine's per-path root-find.
- **Canonical equation:** Find the constant annual withdrawal rate `w` such that, applying `Balance_{t+1} = max(Balance_t · (1+R_t) − w · Balance_0, 0)` for all `t = 1..n`, `Balance_n ≥ 0` (typically the largest such `w`, found by search/root-finding across candidate rates, as in Bengen's iterative historical testing).
- **Code match:** exact in spirit — the code finds, per simulated path, the rate `r ∈ [0,1]` (as a fraction of the *initial* $1 balance, compounding growth factors and subtracting a constant `r` each year) such that terminal balance is exactly 0, via Brent's root-finding method (`scipy.optimize.brentq`) rather than Bengen's original grid search. Bengen's original formulation withdrew a fixed dollar amount from a single historical sequence; this code generalizes it to a root-found percentage-of-initial-balance rate per Monte Carlo path — a reasonable modernization, flagged for Task 2 to confirm sign conventions and boundary handling (`swr[i]=0` vs `1` at `brentq` failure, lines 157–160).

## Perpetual withdrawal rate
- **Code:** `backend/app/engine/results.py::withdrawal_rates_by_percentile` (lines 162–165, `pwr`)
- **Citation:** This is the standard perpetuity / geometric-Brownian-motion "safe withdrawal in perpetuity" approximation, `w ≈ μ − σ²/2` (the long-run/geometric growth rate under lognormal compounding — a direct application of the Itô correction term also used in GBM, see Hull ch. 14 and the Kelly-criterion / geometric-mean maximization literature, e.g. Merton, R.C. (1969), "Lifetime Portfolio Selection under Uncertainty," *Review of Economics and Statistics*, 51(3), 247–257, for the continuous-time consumption/withdrawal analogue).
- **Canonical equation:** `PWR = μ_annual − ½σ_annual²`, the geometric (compound) growth rate implied by an arithmetic mean `μ` and variance `σ²`, which is the maximum constant real withdrawal rate sustainable in perpetuity if the portfolio's expected growth exactly offsets withdrawals.
- **Code match:** exact — `pwr = per_path_annual_returns - 0.5 * per_path_vol**2`.

## Bootstrap historical resampling
- **Code:** `backend/app/engine/historical.py` (`simulate_historical`, `_annual_portfolio_returns`, `_monthly_portfolio_returns`, `_block_bootstrap`)
- **Citation:** Efron, B. & Tibshirani, R.J. (1993), *An Introduction to the Bootstrap*, Chapman & Hall/CRC Monographs on Statistics and Applied Probability 57. For the block-bootstrap variant specifically (contiguous multi-year blocks, sampled with replacement, to preserve serial dependence): Künsch, H.R. (1989), "The Jackknife and the Bootstrap for General Stationary Observations," *The Annals of Statistics*, 17(3), 1217–1241 (moving block bootstrap).
- **Canonical equation:** IID bootstrap: draw `R*_1, ..., R*_n` i.i.d. with replacement from the empirical set `{R_1,...,R_N}` of historical returns. Block bootstrap: draw overlapping/non-overlapping contiguous blocks of length `L` from the historical series with replacement, concatenate to length `n`.
- **Code match:** `simulate_historical`'s `single_year`/`single_month` branches (lines 12–17) are the classic i.i.d. bootstrap (`rng.choice(..., replace=True)`); `_block_bootstrap` (lines 45–60) is the moving/circular block bootstrap (wrapping short trailing blocks via `np.pad(..., mode="wrap")`), matching Künsch's block-bootstrap construction, though using random block starts with wraparound rather than strictly non-overlapping blocks — a design choice for Task 2 to confirm doesn't understate block-length correlation loss at the wrap boundary.

## GARCH(1,1) volatility simulation
- **Code:** `backend/app/engine/forecasted.py::_garch_annual_returns` (lines 21–45)
- **Citation:** Bollerslev, T. (1986), "Generalized Autoregressive Conditional Heteroskedasticity," *Journal of Econometrics*, 31(3), 307–327 (introduces GARCH(p,q), generalizing Engle, R.F. (1982), "Autoregressive Conditional Heteroscedasticity with Estimates of the Variance of United Kingdom Inflation," *Econometrica*, 50(4), 987–1007, the original ARCH model). Corroborated via hyperresearch fetch: "Autoregressive conditional heteroskedasticity," Wikipedia (`research/notes/autoregressive-conditional-heteroskedasticity-wikipedia.md`), which states the GARCH(1,1) recursion identically and credits Bollerslev 1986 / Engle 1982.
- **Canonical equation:** GARCH(1,1): `r_t = μ_t + ε_t`, `ε_t = σ_t·z_t`, `z_t ~ N(0,1)` i.i.d., `σ_t² = ω + α·ε_{t-1}² + β·σ_{t-1}²`.
- **Code match:** the code fits `arch_model(..., vol="Garch", p=1, q=1, dist="normal", mean="Zero")` from the `arch` Python package (Sheppard, K., *ARCH: Autoregressive Conditional Heteroskedasticity Package*, implements exactly Bollerslev's GARCH(1,1) recursion) on demeaned percentage daily returns, simulates via `res.forecast(..., method="simulation")`, and re-adds the drift `port_mu` explicitly afterward (`mean="Zero"` + externally supplied `daily_mu`). This is a documented, intentional deviation from a plain `mean="Constant"` GARCH fit — see the in-code comment (lines 22–25) citing an MLE drift-estimation problem on this dataset; Task 2 should independently verify the drift-injection arithmetic (`sim_daily = daily_mu + sim_daily_shock_pct`) against the GARCH(1,1) mean equation.

## Inflation adjustment (parameterized / historical)
- **Code:** `backend/app/engine/inflation.py::simulate_inflation`, `goals.py::_inflation_factors`
- **Citation:** Standard real/nominal conversion via the Fisher relation, Fisher, I. (1930), *The Theory of Interest*, Macmillan, ch. II. The i.i.d. normal / historical-bootstrap draw structure mirrors the same bootstrap citation as above (Efron & Tibshirani 1993) applied to a CPI series instead of asset returns.
- **Canonical equation:** Fisher approximation: `(1+r_nominal) = (1+r_real)(1+π)`, so `r_real ≈ r_nominal − π` for small `π`. Cumulative inflation factor over `n` years: `I_n = Π_{t=1}^{n} (1+π_t)`.
- **Code match:** `inflation.py` draws `π_t ~ N(mean, vol)` (parameterized) or bootstraps historical CPI returns; `goals.py::_inflation_factors` computes `cumprod(1+inflation_draws, axis=1)` = `I_n` exactly, and `results.py::percentile_table` divides nominal ending balance by `cumulative_inflation` to get `ending_real` — the exact discrete Fisher deflation, not the log-additive approximation.

## Glide-path weight interpolation
- **Code:** `backend/app/engine/goals.py::glide_path_weights` (lines 117–138)
- **Citation:** This is a linear target-date-fund glide-path schedule; the industry-standard reference is Vanguard Research / Target-Retirement-Fund glide-path methodology, e.g. Vanguard, "Vanguard's approach to target-date funds," Vanguard Research, 2021 (linear de-risking glide path from an accumulation to a retirement allocation over a defined transition window) and academically, Basu, A.K., Byrne, A. & Drew, M.E. (2011), "Dynamic Lifecycle Strategies for Target Date Retirement Funds," *Journal of Portfolio Management*, 37(2), 83–96. No live fetch performed for this item (industry-practice convention, not a single-paper formula); flagged as a judgment call below.
- **Canonical equation:** Linear interpolation between `w_start` (at `t ≤ T − G`) and `w_end` (at `t ≥ T`), where `T` = years to retirement, `G` = glide-path window length:
  `w(t) = w_start · [(T−t)/G] + w_end · [1 − (T−t)/G]` for `T−G ≤ t ≤ T`, clamped to `w_start` before and `w_end` after.
- **Code match:** exact — `progress = min(1.0, (years_to_retirement - year)/glide_path_years)`, `return start_weights*progress + end_weights*(1-progress)`, with the pre-window and post-window flat segments handled by the `year <= years_to_retirement` guard and the final `return end_weights`.

## Goal/cashflow application (contribution / withdrawal roll-forward)
- **Code:** `backend/app/engine/goals.py::apply_cashflow` (lines 4–45), `apply_named_goals` (lines 73–114)
- **Citation:** Standard retirement-planning cashflow-simulation mechanics as used in Monte Carlo retirement calculators; see Cooley, P.L., Hubbard, C.M. & Walz, D.T. (1998), "Retirement Savings: Choosing a Withdrawal Rate That Is Sustainable," *AAII Journal*, 20(2), 16–21 (the "Trinity Study," which models exactly this per-year "grow-then-withdraw, floor at zero" balance roll-forward under simulated/historical returns) — same source family as the Bengen SWR citation above and corroborated by the same Wikipedia "Trinity study" fetch.
- **Canonical equation:** `Balance_{t+1} = max( Balance_t · (1+R_t) ± CF_t, 0 )`, where `CF_t` is that year's net contribution (+) or withdrawal (−), optionally inflation-scaled or expressed as a percentage of `Balance_t·(1+R_t)`.
- **Code match:** exact — `grown = values[:,year] * growth_factors[:,year]`; `values[:,year+1] = max(grown + sign*amount, 0.0)` in both `apply_cashflow` and `apply_named_goals` (multi-goal net-cashflow variant, lines 91–103).

---

## Judgment calls and open flags for Task 2

1. **TWRR/CAGR coincidence** (`results.py::percentile_table`): the code's in-line comment justifies treating `twrr_nominal = cagr` because the input array is already a normalized growth-factor path; this is only rigorous if no interim cashflow ever changes the *shares* held (i.e., all cashflow effects are captured in the dollar-balance array being ratio'd start-to-end). Task 2 should confirm this holds for the `withdraw_percent` and multi-goal paths as well as the fixed-dollar cashflow path.
2. **Sortino ratio annualization mismatch**: numerator is a full-period CAGR (annualized), denominator is a raw per-period downside deviation (not annualized) — Task 2 should check this against Sortino's original per-period specification and confirm the units are consistent (or intentionally left this way, as with Sharpe's identical treatment in the same function).
3. **Safe withdrawal rate found via `brentq` root-finding on a normalized $1 starting balance**, generalizing (not literally reproducing) Bengen's original single-historical-sequence, fixed-dollar-withdrawal grid search — a reasonable per-path Monte Carlo generalization but structurally different from the cited paper's method; flagged for explicit note in Task 2's audit rather than treated as a literal formula match.
4. **GARCH drift re-injection** (`forecasted.py::_garch_annual_returns`): fitting with `mean="Zero"` and adding back an externally-estimated `port_mu` is a deliberate, documented deviation from textbook GARCH-in-mean specification, justified in-code by an MLE convergence problem on this dataset. Task 2 should independently verify the arithmetic combining `daily_mu` with the simulated shocks does not double-count or omit compounding.
5. **Glide-path interpolation** has no single-paper formula citation — cited to industry practice (Vanguard glide-path methodology) and academic target-date-fund literature rather than a specific equation-defining paper, since linear interpolation is a design choice, not a derived result.
6. **Fetch failures**: `gipsstandards.org` (404), CFA Institute refresher-reading URL (404), ScienceDirect Bollerslev original article (403 paywall), JSTOR Sharpe/Sortino original articles (cookie/boilerplate block), and `retailinvestor.org`'s Bengen PDF mirror (SSL cert error) were all attempted via `hyperresearch fetch` and failed; those citations rely on well-established bibliographic record (author/year/title/journal/volume/pages are standard, frequently-cited facts) rather than a live-fetched primary source. Successful fetches are noted per-section above with their `research/notes/*.md` paths.
