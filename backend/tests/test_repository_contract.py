from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_operational_files_exist():
    required = [
        ROOT / "README.md",
        ROOT / "LICENSE",
        ROOT / "scripts" / "__init__.py",
        ROOT / "scripts" / "sec_download_mvp.py",
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / ".github" / "workflows" / "refresh-sec-data.yml",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, f"Missing operational files: {missing}"


def test_refresh_workflow_is_manual_and_scheduled_and_runs_the_safe_script():
    workflow = (ROOT / ".github" / "workflows" / "refresh-sec-data.yml").read_text(encoding="utf-8")
    assert "schedule:" in workflow
    assert "workflow_dispatch" in workflow
    assert "python scripts/sec_download_mvp.py" in workflow
    assert "run: pytest" in workflow
    assert "git add data/processed/" in workflow


def test_repository_ignores_generated_tooling_outputs():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in (".mypy_cache/", ".ruff_cache/", "*.pyc", "frontend/node_modules/", "frontend/dist/"):
        assert entry in gitignore
    frontend_ignore = (ROOT / "frontend" / ".gitignore").read_text(encoding="utf-8")
    assert "tsconfig.tsbuildinfo" in frontend_ignore
    assert "playwright-report" in frontend_ignore
