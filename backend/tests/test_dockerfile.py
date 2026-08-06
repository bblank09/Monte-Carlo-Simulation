from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile"


def test_dockerfile_seeds_the_committed_cache_and_serves_the_api():
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "COPY data/ ./data/" in text
    assert "EXPOSE 8000" in text
    assert "backend.app.main:app" in text
    assert text.index("COPY data/ ./data/") < text.index("COPY --from=frontend-build")


def test_dockerfile_healthcheck_is_explicit_and_precedes_cmd():
    text = DOCKERFILE.read_text(encoding="utf-8")
    start = text.index("HEALTHCHECK")
    end = text.index("\n\n", start)
    healthcheck = text[start:end]
    assert "--interval=30s" in healthcheck
    assert "--timeout=10s" in healthcheck
    assert "--start-period=20s" in healthcheck
    assert "--retries=3" in healthcheck
    assert "/api/health" in healthcheck
    assert text.index("HEALTHCHECK") < text.rindex("CMD")


def test_docker_context_keeps_processed_cache_but_excludes_generated_data():
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "data/processed" not in dockerignore
    assert "data/raw" in dockerignore
    assert "data/runs" in dockerignore

