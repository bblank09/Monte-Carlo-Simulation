from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.app.api import simulate, health, funds

app = FastAPI(title="Monte Carlo Simulation API")

for prefix in ("/api/v1", "/api"):
    app.include_router(simulate.router, prefix=prefix)
    app.include_router(health.router, prefix=prefix)
    app.include_router(funds.router, prefix=prefix)

_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
