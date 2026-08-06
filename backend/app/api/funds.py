from fastapi import APIRouter

from backend.app.core.errors import AppHTTPException
from backend.app.data.sec_client import find_funds
from backend.app.domain.enums import ErrorCode

router = APIRouter()


@router.get("/funds")
def list_funds() -> dict:
    """Expose the same complete SEC universe contract as Backtest Portfolio."""
    try:
        funds = find_funds()
    except FileNotFoundError as exc:
        raise AppHTTPException(
            status_code=503,
            detail="SEC fund universe cache is missing. Run scripts/sec_download_mvp.py.",
            code=ErrorCode.FUND_UNIVERSE_CACHE_MISSING,
        ) from exc
    return {"data_source": "sec_open_data", "funds": funds}
