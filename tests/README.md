# Legacy test compatibility

The root `tests/` directory contains the original notebook-era smoke tests. The
imports now target the canonical `backend.app.*` modules so `pytest tests -q`
remains a useful compatibility check. The portfolio optimizer test and the GARCH
smoke test are explicitly skipped when their functionality or optional dependency
is outside the shipped runtime scope. `backend/tests/` contains the product
regression suite; both directories are discovered by `pyproject.toml`.
