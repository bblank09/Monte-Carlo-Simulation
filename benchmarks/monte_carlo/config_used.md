# Portfolio Visualizer Benchmark Config (Task 15)

**Method**: engine-vs-engine comparison (spec section 7). PV cannot use Thai `proj_id`s, so we feed PV our own estimated statistical parameters (Task 5) via its "Forecasted Returns" model instead of asking it to fetch historical data itself.

**Portfolio composition note**: the Sharpe-maximizing (tangency) weights computed via `riskfolio-lib` (Task 8) concentrate 100% in a single asset (0% everywhere else), because the two Thai funds (K หุ้นทุน / K SET50) are ~89% correlated with each other and neither offered a better risk-adjusted return than the best US ETF once short-selling was disallowed. This benchmark therefore reduces to an effectively single-asset test — this is disclosed here rather than hidden, and is itself a legitimate finding about this particular 5-asset universe, not a simplification chosen for convenience.

**Reproducibility fix applied (see Task 4 markdown)**: the data window is now a fixed date range (2020-01-01 to 2025-12-31) instead of a relative `period="5y"` that shifted every time it was fetched. With the earlier (drifting) window the winning asset was SPY (μ=10.07%/σ=16.92%, then briefly 12.19%/17.10% in an even earlier fetch); with the final fixed window it is **QQQ** (μ=17.06%/σ=24.95%). All three sets of numbers were genuinely produced at different points in this session — only the fixed-window QQQ result below is final and reproducible going forward.

## PV Field Values (final)

| PV Field | Value |
|---|---|
| Portfolio Type | Tickers |
| Asset 1 | QQQ, allocation 100% |
| Initial Amount | 1,000,000 |
| Cashflows | No contributions or withdrawals |
| Simulation Period in Years | 30 |
| Tax Treatment | Pre-tax Returns |
| Simulation Model | Forecasted Returns |
| Use Historical Volatility | No |
| Expected Return (Asset 1) | 17.06% |
| Expected Volatility (Asset 1) | 24.95% |
| Rebalancing | Rebalance annually |

Source numbers: `benchmarks/monte_carlo/our_estimated_parameters.csv` (row QQQ), from the notebook's final run with the fixed 2020-01-01 to 2025-12-31 date window (Task 5 cell output).
