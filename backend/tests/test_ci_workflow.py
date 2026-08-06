from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "ci.yml"


def _load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_ci_workflow_exists_and_is_valid_yaml():
    assert WORKFLOW_PATH.is_file()
    workflow = _load_workflow()
    assert workflow["jobs"]


def test_ci_workflow_triggers_on_push_and_pr_to_main():
    workflow = _load_workflow()
    # PyYAML 1.1 parses the bare key `on:` as boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert triggers["push"]["branches"] == ["main"]
    assert triggers["pull_request"]["branches"] == ["main"]


def test_ci_workflow_runs_backend_and_frontend_gates():
    workflow = _load_workflow()
    jobs = workflow["jobs"]
    assert {"backend-tests", "frontend-build"}.issubset(jobs)

    backend_steps = jobs["backend-tests"]["steps"]
    backend_runs = " ".join(step.get("run", "") for step in backend_steps)
    backend_setup = " ".join(str(step.get("with", {})) for step in backend_steps)
    assert "python-version: \"3.11\"" in backend_setup or "3.11" in backend_setup
    assert 'pip install -e ".[dev]"' in backend_runs
    assert "pytest" in backend_runs

    frontend_steps = jobs["frontend-build"]["steps"]
    frontend_runs = " ".join(step.get("run", "") for step in frontend_steps)
    frontend_setup = " ".join(str(step.get("with", {})) for step in frontend_steps)
    assert "node-version: \"20\"" in frontend_setup or "20" in frontend_setup
    assert "npm ci" in frontend_runs
    assert "npm run build" in frontend_runs

