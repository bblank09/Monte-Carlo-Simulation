from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from backend.app.domain.enums import ErrorCode


class AppHTTPException(HTTPException):
    """HTTP error that carries a stable machine-readable error code."""

    def __init__(self, status_code: int, detail: str, code: ErrorCode | str) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code.value if isinstance(code, ErrorCode) else str(code)


async def app_http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppHTTPException):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "code": ErrorCode.INTERNAL_ERROR.value},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )
