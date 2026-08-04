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

  const percentileTable = {
    ending_balance: Object.fromEntries(PERCENTILES.map((p) => [p, fanChart[String(p)][years]])),
    cagr: Object.fromEntries(PERCENTILES.map((p) => [p, Math.pow(fanChart[String(p)][years] / initial, 1 / years) - 1])),
  };

  const survivedCount = Math.round(500 * survivalOverTime[years]);

  const response: SimulateResponse = {
    overview: {
      n_paths: request.n_paths,
      survived_count: survivedCount,
      survival_rate: survivedCount / 500,
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
    },
    goals: request.multi_goal_enabled
      ? { summary: (request.goals ?? []).map((g: { purpose: string }) => ({ purpose: g.purpose, success_rate: 0.94 })) }
      : null,
    run_config: request as unknown as Record<string, unknown>,
  };

  return response;
}
