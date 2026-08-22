import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from backend.app.api import data_status, funds, health, simulate
from backend.app.core.config import settings
from backend.app.core.errors import AppHTTPException, app_http_exception_handler
from backend.app.core.limiter import limiter
from backend.app.domain.enums import ErrorCode

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("app")

app = FastAPI(title="Monte Carlo Simulation API", version="0.1.0")
app.state.limiter = limiter


async def rate_limit_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # FastAPI's add_exception_handler requires handlers typed to accept the
    # base Exception (it's contravariant in the handler's parameter type);
    # RateLimitExceeded is the only exception ever routed here.
    assert isinstance(exc, RateLimitExceeded)
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many simulation requests. Try again later.", "code": ErrorCode.RATE_LIMIT_EXCEEDED.value},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": ErrorCode.INTERNAL_ERROR.value},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors()), "code": ErrorCode.VALIDATION_ERROR.value},
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(AppHTTPException, app_http_exception_handler)

_allowed_origins = settings.allowed_origins_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_allowed_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for prefix in ("/api/v1", "/api"):
    app.include_router(simulate.router, prefix=prefix)
    app.include_router(health.router, prefix=prefix)
    app.include_router(funds.router, prefix=prefix)
    app.include_router(data_status.router, prefix=prefix)

_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.is_dir():
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str) -> FileResponse:
        # An unknown API path must remain a real 404. Returning index.html here
        # would make typos and path-traversal probes look like successful API
        # responses to clients and tests.
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = _frontend_dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_frontend_dist / "index.html")
