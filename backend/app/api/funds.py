from fastapi import APIRouter
from backend.app.data.sec_client import find_equity_funds

router = APIRouter()


@router.get("/funds")
def list_funds():
    # SEC Open Data returns raw fund-profile records (proj_name_th, comp_name_th, ...).
    # The frontend's FundSummary contract (frontend/src/types/simulate.ts, shared by
    # client.ts/mockData.ts/PortfolioStep.tsx/ParametersStep.tsx) expects proj_id,
    # proj_name_thai, amc_name_thai. Map here so the API is the contract's source of
    # truth rather than leaking SEC's raw field names to the frontend.
    return [
        {
            "proj_id": item.get("proj_id"),
            "proj_name_thai": item.get("proj_name_th"),
            "amc_name_thai": item.get("comp_name_th"),
            "policy_desc": item.get("policy_desc"),
        }
        for item in find_equity_funds()
    ]
