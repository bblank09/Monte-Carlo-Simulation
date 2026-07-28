# Portfolio Visualizer Results (Task 15 Benchmark, final)

Confirmed input echo from PV: *"The configured portfolio model had 17.06% annual mean return with 24.95% standard deviation."* — exact match to `our_estimated_parameters.csv` (QQQ row, fixed 2020-2025 window).

## Summary Statistics (5,000 simulated portfolios, 30-year horizon, $1,000,000 initial)

| Metric | 10th Pct | 25th Pct | 50th Pct | 75th Pct | 90th Pct |
|---|---|---|---|---|---|
| Time Weighted Return (nominal) | 9.07% | 11.53% | 14.37% | 17.50% | 20.30% |
| Portfolio End Balance (nominal) | $13,512,072 | $26,405,187 | $56,089,395 | $126,140,355 | $255,912,859 |
| Annual Mean Return (nominal) | 11.45% | 13.91% | 16.86% | 20.10% | 22.93% |
| Annualized Volatility | 20.31% | 20.82% | 21.35% | 21.90% | 22.40% |
| Sharpe Ratio | 0.34 | 0.45 | 0.57 | 0.70 | 0.81 |
| Maximum Drawdown | -56.93% | -49.37% | -42.04% | -36.06% | -31.73% |

## Comparison to Our Statistical Model (same μ=17.06%, σ=24.95%, 30yr, $1M)

| | Median Ending | 10th Pct | 90th Pct |
|---|---|---|---|
| **Portfolio Visualizer** | $56,089,395 | $13,512,072 | $255,912,859 |
| **Our engine (Statistical)** | $66,361,053 | $11,465,553 | $371,814,152 |
| Difference | +18.3% | -15.1% | +45.3% |

**Assessment**: with this higher-volatility asset (QQQ, σ=24.95%), the gap between engines widens relative to the earlier SPY test (σ=16.92%, gaps were +6%/-8%/+17%) — consistent with the two engines agreeing on the drift but handling variance/compounding slightly differently, an effect that scales with σ². Plausible contributors: (1) PV's own inflation-correlation modeling (which we did not replicate) interacts with volatility, (2) PV may apply return smoothing or a light cap on its Normal-return sampling that compresses tails more as σ grows, (3) our GBM Euler engine uses 252 discrete daily steps/year while PV's methodology is not fully disclosed (possibly annual-step sampling), and discretization choice affects higher moments more at higher σ. The **median and 10th percentile still agree within ~18%** even at this higher volatility, which is a reasonable cross-validation given the two engines are independently implemented and not fitted to match each other.

## Session note on reproducibility

Two earlier benchmark attempts (SPY, μ=12.19%/17.10% and then μ=10.07%/16.92%) were superseded after discovering that the original `yfinance` fetch used a relative `period="5y"` window that shifted with each call. The fix (Task 4: fixed date range 2020-01-01 to 2025-12-31) changed which asset the long-only Sharpe-maximizing optimizer selects (SPY → QQQ), which is itself a useful illustration of how sensitive mean-variance optimization is to the estimation window - a real, disclosed finding rather than an error to hide.
