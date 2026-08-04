import type { FundSummary, SimulateRequest, SimulateResponse } from "../types/simulate";

export const mockFunds: FundSummary[] = [
  { proj_id: "M0027_2535", proj_name_thai: "K หุ้นทุน", amc_name_thai: "บลจ.กสิกรไทย" },
  { proj_id: "M0209_2548", proj_name_thai: "K SET50", amc_name_thai: "บลจ.กสิกรไทย" },
  { proj_id: "M0088_2540", proj_name_thai: "ไทยพาณิชย์หุ้นทุน", amc_name_thai: "บลจ.ไทยพาณิชย์" },
  { proj_id: "M0154_2544", proj_name_thai: "บัวหลวงตราสารหนี้", amc_name_thai: "บลจ.บัวหลวง" },
  { proj_id: "M0301_2551", proj_name_thai: "กรุงศรีตราสารหนี้ระยะสั้น", amc_name_thai: "บลจ.กรุงศรี" },
];

const PERCENTILES = [10, 25, 50, 75, 90] as const;

// A fixed pseudo-random generator (mulberry32) so every call with the same request
// produces the same fixture — reviewers should see stable numbers, not flicker on
// re-render.
function seededRandom(seed: number) {
  let t = seed;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

export function mockSimulateResponse(request: SimulateRequest): SimulateResponse {
  const rand = seededRandom(request.seed ?? 42);
  const years = request.simulation_period_years;
  const initial = request.initial_amount;

  // Median annual return/vol vary slightly by model so the mock visibly reacts to the
  // Parameters step, without pretending to be a real simulation.
  const baseReturn = request.simulation_model === "parameterized" ? (request.expected_return ?? 0.07) : 0.075;
  const baseVol = request.simulation_model === "parameterized" ? (request.expected_volatility ?? 0.15) : 0.14;

  const fanChart: Record<string, number[]> = {};
  for (const p of PERCENTILES) {
    const drift = baseReturn + (p - 50) / 1000; // higher percentiles drift up
    const path = [initial];
    for (let y = 1; y <= years; y++) {
      path.push(path[y - 1] * (1 + drift + (rand() - 0.5) * 0.01));
    }
    fanChart[String(p)] = path;
  }

  const survivalOverTime = Array.from({ length: years + 1 }, (_, y) =>
    Math.max(0.7, 1 - y * (0.002 + baseVol / 500))
  );

  const endingBalances = Array.from({ length: 500 }, () => {
    const z = (rand() + rand() + rand() - 1.5) * 2; // roughly normal-ish via CLT
    return Math.max(0, initial * Math.exp(baseReturn * years + baseVol * Math.sqrt(years) * z * 0.3));
  });

  // Max drawdown histogram — negative percentages, worse for higher volatility
  const maxDrawdownHistogram = Array.from({ length: 500 }, () => {
    const z = (rand() + rand() + rand() - 1.5) * 2;
    const meanDrawdown = -0.25 - baseVol * 0.5; // worse drawdowns with higher vol
    return Math.min(-0.02, meanDrawdown + z * 0.12);
  });

  const horizons = [1, 3, 5, 10, 15, 20, 25, 30] as const;
  const thresholds = {
    "0%": 0,
    "2.5%": 0.025,
    "5%": 0.05,
    "7.5%": 0.075,
    "10%": 0.1,
    "12.5%": 0.125,
  };

  // Expected return by horizon: wider ranges at shorter horizons, narrower at longer
  const expectedReturnByHorizon: Record<string, Record<string, number>> = {};
  for (const h of horizons) {
    const hStr = String(h);
    expectedReturnByHorizon[hStr] = {};
    for (const p of PERCENTILES) {
      const horizon_spread = Math.max(0.02, 0.25 * Math.exp(-h / 15)); // narrows with longer horizon
      const p_offset = (p - 50) / 50; // -1 to 1
      expectedReturnByHorizon[hStr][p] = baseReturn + p_offset * horizon_spread;
    }
  }

  // Annual return probability: prob of meeting/exceeding threshold over each horizon
  const annualReturnProbability: Record<string, Record<string, number>> = {};
  for (const thresholdLabel in thresholds) {
    const threshold = thresholds[thresholdLabel as keyof typeof thresholds];
    annualReturnProbability[thresholdLabel] = {};
    for (const h of horizons) {
      // Probability increases with horizon (law of large numbers)
      // Decreases as threshold rises
      const baseProbability = 0.98 - Math.pow(threshold, 0.5) * 0.3;
      const horizonFactor = Math.min(1, Math.sqrt(h / 30));
      annualReturnProbability[thresholdLabel][h] = Math.max(0, baseProbability * horizonFactor);
    }
  }

  // Loss probability: split by including/excluding cashflows and within/end of period
  const lossProbability: {
    excluding_cashflows: { within_period: Record<string, number>; end_of_period: Record<string, number> };
    including_cashflows: { within_period: Record<string, number>; end_of_period: Record<string, number> };
  } = {
    excluding_cashflows: { within_period: {}, end_of_period: {} },
    including_cashflows: { within_period: {}, end_of_period: {} },
  };
  for (const thresholdLabel in thresholds) {
    const threshold = thresholds[thresholdLabel as keyof typeof thresholds];
    lossProbability.excluding_cashflows.within_period[thresholdLabel] = Math.min(0.5, threshold * 0.6);
    lossProbability.excluding_cashflows.end_of_period[thresholdLabel] = Math.min(0.35, threshold * 0.4);
    lossProbability.including_cashflows.within_period[thresholdLabel] = Math.min(0.6, threshold * 0.7);
    lossProbability.including_cashflows.end_of_period[thresholdLabel] = Math.min(0.45, threshold * 0.5);
  }

  const percentileTable = {
    ending_balance: Object.fromEntries(PERCENTILES.map((p) => [p, fanChart[String(p)][years]])),
    cagr: Object.fromEntries(PERCENTILES.map((p) => [p, Math.pow(fanChart[String(p)][years] / initial, 1 / years) - 1])),
    twrr_nominal: Object.fromEntries(PERCENTILES.map((p) => [p, Math.pow(fanChart[String(p)][years] / initial, 1 / years) - 1])), // approximate as CAGR
    twrr_real: Object.fromEntries(PERCENTILES.map((p) => [p, Math.pow(fanChart[String(p)][years] / initial, 1 / years) - 1 - 0.025])), // nominal minus ~2.5% inflation
    max_drawdown: Object.fromEntries(PERCENTILES.map((p) => [p, -0.15 - (90 - p) / 100 * 0.4])), // 10th: -0.55, 50th: -0.30, 90th: -0.15
    max_drawdown_excl_cashflows: Object.fromEntries(PERCENTILES.map((p) => [p, (-0.15 - (90 - p) / 100 * 0.4) * 0.8])), // 80% of magnitude
  };

  const survivedCount = Math.round(request.n_paths * survivalOverTime[years]);

  const response: SimulateResponse = {
    overview: {
      n_paths: request.n_paths,
      survived_count: survivedCount,
      survival_rate: survivedCount / request.n_paths,
      median_ending_balance: percentileTable.ending_balance[50],
      median_cagr: percentileTable.cagr[50],
      holdings: request.holdings,
    },
    growth: {
      fan_chart: fanChart,
      survival_over_time: survivalOverTime,
    },
    distribution: {
      ending_balance_histogram: endingBalances,
      max_drawdown_histogram: maxDrawdownHistogram,
    },
    metrics: {
      percentile_table: percentileTable,
      sharpe: Object.fromEntries(PERCENTILES.map((p) => [p, 0.3 + (p - 10) / 200])),
      sortino: Object.fromEntries(PERCENTILES.map((p) => [p, 0.45 + (p - 10) / 180])),
      safe_withdrawal_rate: Object.fromEntries(PERCENTILES.map((p) => [p, 0.03 + (p - 10) / 2000])),
      perpetual_withdrawal_rate: Object.fromEntries(PERCENTILES.map((p) => [p, 0.025 + (p - 10) / 2500])),
    },
    risk: {
      correlation_and_returns: {
        correlation: Object.fromEntries(
          request.holdings.map((a: { proj_id: string; weight: number }) => [
            a.proj_id,
            Object.fromEntries(request.holdings.map((b: { proj_id: string; weight: number }) => [b.proj_id, a.proj_id === b.proj_id ? 1 : 0.3])),
          ])
        ),
        stats: Object.fromEntries(
          request.holdings.map((h: { proj_id: string; weight: number }) => [h.proj_id, { cagr: 0.08, expected_return: 0.09, volatility: 0.18 }])
        ),
      },
      value_at_risk: initial * 0.18,
      expected_shortfall: initial * 0.24,
      expected_return_by_horizon: expectedReturnByHorizon,
      annual_return_probability: annualReturnProbability,
      loss_probability: lossProbability,
    },
    goals: request.multi_goal_enabled
      ? (() => {
          // Compute cashflows from goals
          const cashflows_nominal = Array.from({ length: years + 1 }, () => 0);
          const cashflows_present_dollar = Array.from({ length: years + 1 }, () => 0);

          if (request.goals) {
            for (const goal of request.goals) {
              const frequency_years = goal.frequency === "monthly" ? 1 / 12 : goal.frequency === "quarterly" ? 0.25 : 1;
              const sign = goal.is_withdrawal ? -1 : 1;

              for (let y = goal.starts_year; y <= Math.min(goal.ends_year, years); y++) {
                const annual_contribution = sign * goal.amount / frequency_years;
                cashflows_nominal[y] = (cashflows_nominal[y] ?? 0) + annual_contribution;
                // Present dollar: discount back at ~2.5% inflation
                cashflows_present_dollar[y] = (cashflows_present_dollar[y] ?? 0) + annual_contribution / Math.pow(1.025, y);
              }
            }
          }

          // Build glide path if retirement info is present
          let glide_path: { years: number[]; allocations: Record<string, number[]> } | undefined;
          if (request.years_to_retirement !== undefined && request.retirement_holdings !== undefined) {
            const glide_path_years = request.glide_path_years ?? 10;
            const glide_years_array = Array.from({ length: years + 1 }, (_, i) => i);
            const allocations: Record<string, number[]> = {};

            for (const holding of request.holdings) {
              const start_weight = holding.weight;
              const retire_holding = request.retirement_holdings.find((h: { proj_id: string; weight: number }) => h.proj_id === holding.proj_id);
              const end_weight = retire_holding?.weight ?? 0;

              allocations[holding.proj_id] = glide_years_array.map((y) => {
                if (y <= request.years_to_retirement!) {
                  // Linear interpolation from start to retirement
                  const progress = Math.min(1, (request.years_to_retirement! - y) / glide_path_years);
                  return start_weight * progress + end_weight * (1 - progress);
                } else {
                  // After retirement, hold steady at retirement weight
                  return end_weight;
                }
              });
            }
            glide_path = { years: glide_years_array, allocations };
          }

          const goalsObj: Record<string, unknown> = {
            summary: (request.goals ?? []).map((g: { purpose: string }) => ({ purpose: g.purpose, success_rate: 0.94 })),
            cashflows_nominal,
            cashflows_present_dollar,
          };
          if (glide_path) {
            goalsObj.glide_path = glide_path;
          }
          return goalsObj;
        })()
      : null,
    run_config: request as unknown as Record<string, unknown>,
  };

  return response;
}
