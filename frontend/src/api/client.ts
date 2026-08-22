import type { FundSummary, SimulateRequest, SimulateResponse } from "../types/simulate";
import { mockFunds, mockSimulateResponse } from "./mockData";

const API_BASE = "/api";

// USE_MOCK is an optional deterministic fixture switch for local UI development.
// Production keeps it false so the SEC-backed API remains the source of truth; no
// component that imports postSimulate/getFunds needs to change when the switch changes.
const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export async function postSimulate(request: SimulateRequest): Promise<SimulateResponse> {
  if (USE_MOCK) {
    await new Promise((resolve) => setTimeout(resolve, 600)); // simulate network latency for RunOverlay
    return mockSimulateResponse(request);
  }
  const resp = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`simulate failed: ${resp.status} ${body}`);
  }
  return resp.json();
}

export async function fetchSimulationByRunId(runId: string): Promise<SimulateResponse> {
  const resp = await fetch(`${API_BASE}/simulate/${encodeURIComponent(runId)}`);
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`simulation run load failed: ${resp.status} ${body}`);
  }
  return resp.json();
}

export async function getFunds(): Promise<FundSummary[]> {
  if (USE_MOCK) return mockFunds;
  const resp = await fetch(`${API_BASE}/funds`);
  if (!resp.ok) throw new Error(`funds fetch failed: ${resp.status}`);
  const payload = (await resp.json()) as { data_source?: string; funds?: FundSummary[] };
  if (payload.data_source && payload.data_source !== "sec_open_data") {
    throw new Error("Production app accepts SEC Open Data funds only.");
  }
  return payload.funds ?? [];
}
