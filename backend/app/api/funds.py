from fastapi import APIRouter

from backend.app.data.sec_client import find_funds

router = APIRouter()


@router.get("/funds")
def list_funds() -> dict:
    """Expose the same complete SEC universe contract as Backtest Portfolio."""
    return {
        "data_source": "sec_open_data",
        "funds": find_funds(),
    }
