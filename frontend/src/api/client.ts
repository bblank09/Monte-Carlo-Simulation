import type { FundSummary, SimulateRequest, SimulateResponse } from "../types/simulate";
import { mockFunds, mockSimulateResponse } from "./mockData";

const API_BASE = "/api";

// USE_MOCK is the single switch between Phase 1 (UX/UI on mock data) and Phase 3
// (real backend wired in). Flip via VITE_USE_MOCK=false in .env.local, or the Task 19b
// wiring step removes the mock branch entirely once the backend is ready. No component
// that imports postSimulate/getFunds needs to change either way.
const USE_MOCK = import.meta.env.VITE_USE_MOCK !== "false";

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

export async function getFunds(): Promise<FundSummary[]> {
  if (USE_MOCK) return mockFunds;
  const resp = await fetch(`${API_BASE}/funds`);
  if (!resp.ok) throw new Error(`funds fetch failed: ${resp.status}`);
  return resp.json();
}
