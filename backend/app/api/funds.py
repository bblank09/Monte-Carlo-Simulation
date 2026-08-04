from fastapi import APIRouter
from backend.app.data.sec_client import find_equity_funds

router = APIRouter()


@router.get("/funds")
def list_funds():
    return find_equity_funds()
