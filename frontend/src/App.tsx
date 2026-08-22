import { useEffect, useState } from "react";
import DarkVeil from "./components/DarkVeil";
import { Stepper } from "./components/Stepper";
import { RunOverlay } from "./components/RunOverlay";
import { PortfolioStep } from "./components/PortfolioStep";
import { ParametersStep } from "./components/ParametersStep";
import { ResultsView } from "./components/ResultsView";
import { fetchSimulationByRunId, postSimulate, getFunds } from "./api/client";
import type { FundSummary, Holding, SimulateRequest, SimulateResponse } from "./types/simulate";

const DEFAULT_REQUEST: SimulateRequest = {
  holdings: [],
  initial_amount: 1_000_000,
  simulation_period_years: 30,
  tax_treatment: "pre_tax",
  tax_rate: 0.2,
  simulation_model: "historical",
  n_paths: 10000,
  rebalancing: "none",
  bootstrap_model: "single_year",
  use_full_history: true,
  sequence_of_returns_risk: 0,
  time_series_model: "normal",
  degrees_of_freedom: 5,
  expected_return: 0.07,
  expected_volatility: 0.15,
  inflation_model: "historical",
  inflation_mean: 0.03,
  inflation_volatility: 0.01,
  cashflow_mode: "none",
  cashflow_frequency: "annually",
  // Parameterized model requires distribution/expected_return/expected_volatility
  // server-side (backend/app/domain/schemas.py). The Parameters form renders
  // "Normal" as the visible default for the Distribution select, but a <select>
  // only fires onChange on user interaction, so without a real default here the
  // field stayed undefined in the request payload until the user touched the
  // dropdown -- causing a 422 from the real backend the first time someone chose
  // Parameterized Returns and just clicked through (mock mode never caught this
  // because it doesn't validate the request against the schema).
  distribution: "normal",
};

const STEPS = ["portfolio", "parameters", "results"] as const;
type Step = (typeof STEPS)[number];

const SESSION_KEY = "mc-session";
type StoredSession = {
  holdings: Holding[];
  params: SimulateRequest;
  stepIndex: number;
  unlockedStep: number;
};

type AppErrorKind = "funds" | "shared_run" | "simulation";
type AppError = { kind: AppErrorKind; message: string; detail: string };

function loadStoredSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    return parsed as StoredSession;
  } catch {
    return null;
  }
}

function initialParameters(session: StoredSession | null): SimulateRequest {
  const stored = (session?.params ?? {}) as unknown as Record<string, unknown>;
  const merged = { ...DEFAULT_REQUEST, ...stored } as SimulateRequest;
  const supportedCashflowModes = new Set(["none", "contribute", "withdraw_fixed", "withdraw_percent"]);
  if (!supportedCashflowModes.has(merged.cashflow_mode ?? "none")) merged.cashflow_mode = "none";
  if (merged.simulation_model !== "statistical") merged.rebalancing = "none";
  if (merged.simulation_model === "statistical" && merged.time_series_model !== "normal") merged.rebalancing = "none";
  if (merged.simulation_model !== "historical") merged.use_full_history = undefined;
  return merged;
}

export function App() {
  const initialSession = loadStoredSession();
  // Keep the user's draft inputs across a refresh, but always start a fresh
  // browser visit at Portfolio. Persisting the last navigation state here
  // made an old completed run unlock Assumptions and Results immediately on
  // the next visit, so the top-bar stepper appeared clickable before the
  // current workflow had passed those steps. A shared `?run=` link still
  // unlocks the full flow below after its saved result is loaded.
  const [stepIndex, setStepIndex] = useState(0);
  const [unlockedStep, setUnlockedStep] = useState(0);
  const [funds, setFunds] = useState<FundSummary[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>(initialSession?.holdings ?? []);
  const [params, setParams] = useState<SimulateRequest>(() => ({
    ...initialParameters(initialSession),
    holdings: initialSession?.holdings ?? [],
  }));
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<AppError | null>(null);
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    // Dark is the only supported theme now -- no toggle, no stored
    // preference. Still set explicitly so :root[data-theme="dark"] wins
    // over a light prefers-color-scheme system setting.
    document.documentElement.setAttribute("data-theme", "dark");
  }, []);

  useEffect(() => {
    void loadFunds();
  }, []);

  useEffect(() => {
    const runId = new URLSearchParams(window.location.search).get("run");
    if (!runId) return;
    void loadSharedRun(runId);
  }, []);

  useEffect(() => {
    const snapshot: StoredSession = { holdings, params, stepIndex, unlockedStep };
    localStorage.setItem(SESSION_KEY, JSON.stringify(snapshot));
  }, [holdings, params, stepIndex, unlockedStep]);

  const step: Step = STEPS[stepIndex];
  const navAsOf = funds.reduce<string | null>((latest, fund) => {
    if (!fund.nav_end) return latest;
    return !latest || fund.nav_end > latest ? fund.nav_end : latest;
  }, null);

  function goToStep(index: number) {
    if (index <= unlockedStep) setStepIndex(index);
  }

  function errorDetail(errorValue: unknown): string {
    return errorValue instanceof Error ? errorValue.message : "Unknown error";
  }

  async function loadFunds() {
    try {
      const loadedFunds = await getFunds();
      setFunds(loadedFunds);
      setError((current) => (current?.kind === "funds" ? null : current));
    } catch (e) {
      setError({ kind: "funds", message: "We couldn’t load fund data.", detail: errorDetail(e) });
    }
  }

  async function loadSharedRun(runId: string) {
    setRunning(true);
    setError(null);
    try {
      const response = await fetchSimulationByRunId(runId);
      const savedRequest = initialParameters({
        holdings: [],
        params: response.run_config as unknown as SimulateRequest,
        stepIndex: 2,
        unlockedStep: 2,
      });
      setResult(response);
      setParams({ ...DEFAULT_REQUEST, ...savedRequest });
      setHoldings(savedRequest.holdings ?? []);
      setUnlockedStep(2);
      setStepIndex(2);
    } catch (e) {
      setError({ kind: "shared_run", message: `We couldn’t load shared run "${runId}".`, detail: errorDetail(e) });
    } finally {
      setRunning(false);
    }
  }

  async function runSimulation() {
    const request: SimulateRequest = { ...params, holdings };
    setRunning(true);
    setError(null);
    try {
      const response = await postSimulate(request);
      setResult(response);
      const url = new URL(window.location.href);
      url.searchParams.set("run", response.run_id);
      window.history.replaceState(null, "", url);
      setUnlockedStep(2);
      setStepIndex(2);
    } catch (e) {
      setError({ kind: "simulation", message: "We couldn’t run the simulation.", detail: errorDetail(e) });
    } finally {
      setRunning(false);
    }
  }

  function retrySimulation() {
    if (error?.kind === "funds") {
      void loadFunds();
    } else if (error?.kind === "shared_run") {
      const runId = new URLSearchParams(window.location.search).get("run");
      if (runId) void loadSharedRun(runId);
    } else {
      void runSimulation();
    }
  }

  function startOver() {
    setHoldings([]);
    setParams(DEFAULT_REQUEST);
    setResult(null);
    setError(null);
    setUnlockedStep(0);
    setStepIndex(0);
    setLinkCopied(false);
    localStorage.removeItem(SESSION_KEY);
    const url = new URL(window.location.href);
    url.searchParams.delete("run");
    window.history.replaceState(null, "", url);
  }

  async function copyShareLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setLinkCopied(true);
      window.setTimeout(() => setLinkCopied(false), 2000);
    } catch {
      // Clipboard access can be denied by the browser; the URL remains
      // available in the address bar for manual copying.
    }
  }

  return (
    <div className="shell">
      <div className="app-veil" aria-hidden="true">
        <DarkVeil hueShift={342} speed={1.5} scanlineFrequency={0.5} />
      </div>
      <header className="topbar">
        <div className="brand">
          <img alt="Monte Carlo Simulation" className="mark" src="/brand/topbar-mark.png" />
          <span>Monte Carlo Simulation</span>
          <span className="tag">Forward-looking portfolio simulation</span>
          {navAsOf ? <span className="tag nav-as-of">NAV data as of {formatNavDate(navAsOf)}</span> : null}
        </div>
        <Stepper currentStep={stepIndex} unlockedStep={unlockedStep} onStepClick={goToStep} />
      </header>

      <div className="main">
        {error && (
          <div className="errorBanner" role="alert">
            <span className="ic">&#9888;</span>
            <div className="banner-body">
              <p className="banner-message">{error.message}</p>
              <details className="banner-detail">
                <summary>Technical details</summary>
                <span>{error.detail}</span>
              </details>
              <button className="btn btn-ghost btn-sm" onClick={retrySimulation} type="button">
                {error.kind === "funds" ? "Retry fund loading" : error.kind === "shared_run" ? "Retry shared run loading" : "Try simulation again"}
              </button>
            </div>
          </div>
        )}
        {step === "portfolio" && (
          <PortfolioStep
            funds={funds}
            active
            onHoldingsChange={(nextHoldings) => {
              setHoldings(nextHoldings);
              setParams((current) => ({ ...current, holdings: nextHoldings }));
            }}
            onContinue={() => {
              setUnlockedStep((current) => Math.max(current, 1));
              setStepIndex(1);
            }}
          />
        )}
        {step === "parameters" && (
          <ParametersStep
            active
            value={params}
            onChange={setParams}
            onBack={() => goToStep(0)}
            onContinue={runSimulation}
            running={running}
          />
        )}
        {step === "results" && result && (
          <div className="page active">
            <ResultsView result={result} />
            <div className="actions">
              <button className="btn btn-ghost" onClick={() => goToStep(1)} type="button">&larr; Adjust assumptions</button>
              <button className="btn btn-ghost" onClick={startOver} type="button">Start a new portfolio</button>
              <button className="btn btn-ghost" onClick={copyShareLink} type="button">
                {linkCopied ? "Link copied" : "Copy shareable link"}
              </button>
            </div>
          </div>
        )}
      </div>

      <footer className="app-footer">
        <img alt="Supachok Julaupay signature mark" className="app-footer-mark" src="/brand/author-logo-dark.png" />
        <div className="app-footer-text">
          <span className="app-footer-name">Supachok Julaupay</span>
          <a href="https://github.com/bblank09" rel="noreferrer" target="_blank">github.com/bblank09</a>
          <span className="app-footer-legal">
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
          </span>
        </div>
      </footer>

      <RunOverlay open={running} />
    </div>
  );
}

function formatNavDate(isoDate: string): string {
  const parsed = new Date(`${isoDate}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return isoDate;
  return parsed.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
}
