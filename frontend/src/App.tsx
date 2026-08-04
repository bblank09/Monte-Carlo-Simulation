import { useEffect, useState } from "react";
import { Stepper } from "./components/Stepper";
import { RunOverlay } from "./components/RunOverlay";
import { PortfolioStep } from "./components/PortfolioStep";
import { ParametersStep } from "./components/ParametersStep";
import { ResultsView } from "./components/ResultsView";
import { postSimulate, getFunds } from "./api/client";
import type { FundSummary, Holding, SimulateRequest, SimulateResponse } from "./types/simulate";

const DEFAULT_REQUEST: SimulateRequest = {
  holdings: [],
  initial_amount: 1_000_000,
  simulation_period_years: 30,
  tax_treatment: "pre_tax",
  simulation_model: "historical",
  n_paths: 10000,
  rebalancing: "annual",
  bootstrap_model: "single_year",
  use_full_history: true,
  sequence_of_returns_risk: 0,
  cashflow_mode: "none",
  multi_goal_enabled: false,
  inflation_model: "historical",
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

export function App() {
  const initialSession = loadStoredSession();
  const [stepIndex, setStepIndex] = useState(initialSession?.stepIndex ?? 0);
  const [unlockedStep, setUnlockedStep] = useState(initialSession?.unlockedStep ?? 0);
  const [funds, setFunds] = useState<FundSummary[]>([]);
  const [fundsLoading, setFundsLoading] = useState(true);
  const [holdings, setHoldings] = useState<Holding[]>(initialSession?.holdings ?? []);
  const [params, setParams] = useState<SimulateRequest>(initialSession?.params ?? DEFAULT_REQUEST);
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">(() => (localStorage.getItem("mc-theme") === "dark" ? "dark" : "light"));

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("mc-theme", theme);
  }, [theme]);

  useEffect(() => {
    getFunds()
      .then(setFunds)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load funds"))
      .finally(() => setFundsLoading(false));
  }, []);

  useEffect(() => {
    const snapshot: StoredSession = { holdings, params, stepIndex, unlockedStep };
    localStorage.setItem(SESSION_KEY, JSON.stringify(snapshot));
  }, [holdings, params, stepIndex, unlockedStep]);

  const step: Step = STEPS[stepIndex];

  function goToStep(index: number) {
    if (index <= unlockedStep) setStepIndex(index);
  }

  async function runSimulation() {
    const request: SimulateRequest = { ...params, holdings };
    setRunning(true);
    setError(null);
    try {
      const response = await postSimulate(request);
      setResult(response);
      setUnlockedStep(2);
      setStepIndex(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setRunning(false);
    }
  }

  function retrySimulation() {
    void runSimulation();
  }

  function startOver() {
    setHoldings([]);
    setParams(DEFAULT_REQUEST);
    setResult(null);
    setError(null);
    setUnlockedStep(0);
    setStepIndex(0);
    localStorage.removeItem(SESSION_KEY);
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <img alt="Monte Carlo Simulation" className="mark" src="/brand/topbar-mark.png" />
          <span>Monte Carlo Simulation</span>
          <span className="tag">Forward-looking portfolio simulation</span>
        </div>
        <Stepper currentStep={stepIndex} unlockedStep={unlockedStep} onStepClick={goToStep} />
        <button className="theme-toggle" onClick={() => setTheme((current) => (current === "light" ? "dark" : "light"))} type="button">
          Toggle theme
        </button>
      </header>

      <div className="main">
        {error && (
          <div className="banner danger">
            <span className="ic">&#9888;</span>
            <div className="banner-body">
              <p className="banner-message">We couldn&rsquo;t run the simulation. Please try again.</p>
              <details className="banner-detail">
                <summary>Technical details</summary>
                <span>{error}</span>
              </details>
              <button className="btn btn-ghost btn-sm" onClick={retrySimulation} type="button">
                Try again
              </button>
            </div>
          </div>
        )}
        {step === "portfolio" && (
          <PortfolioStep
            funds={funds}
            fundsLoading={fundsLoading}
            active
            onHoldingsChange={setHoldings}
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
            funds={funds}
            running={running}
          />
        )}
        {step === "results" && result && (
          <div className="page active">
            <ResultsView result={result} />
            <div className="actions">
              <button className="btn btn-ghost" onClick={() => goToStep(1)} type="button">&larr; Adjust parameters</button>
              <button className="btn btn-danger" onClick={startOver} type="button">Start a new portfolio</button>
            </div>
          </div>
        )}
      </div>

      <footer className="app-footer">
        <img alt="Supachok Julaupay signature mark" className="app-footer-mark" src={theme === "dark" ? "/brand/author-logo-dark.png" : "/brand/author-logo-light.png"} />
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
