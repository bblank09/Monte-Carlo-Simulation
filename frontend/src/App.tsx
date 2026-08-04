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

export function App() {
  const [stepIndex, setStepIndex] = useState(0);
  const [unlockedStep, setUnlockedStep] = useState(0);
  const [funds, setFunds] = useState<FundSummary[]>([]);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [params, setParams] = useState<SimulateRequest>(DEFAULT_REQUEST);
  const [result, setResult] = useState<SimulateResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getFunds()
      .then(setFunds)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load funds"));
  }, []);

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

  return (
    <div className="app-shell">
      <Stepper currentStep={stepIndex} unlockedStep={unlockedStep} onStepClick={goToStep} />
      <RunOverlay open={running} />
      {error && <div className="banner danger">{error}</div>}
      {step === "portfolio" && (
        <PortfolioStep
          funds={funds}
          active
          onHoldingsChange={setHoldings}
          onContinue={() => {
            setUnlockedStep((current) => Math.max(current, 1));
            setStepIndex(1);
          }}
        />
      )}
      {step === "parameters" && (
        <ParametersStep active value={params} onChange={setParams} onContinue={runSimulation} />
      )}
      {step === "results" && result && <ResultsView result={result} />}
    </div>
  );
}
