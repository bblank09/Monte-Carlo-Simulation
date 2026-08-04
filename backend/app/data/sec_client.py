import os
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
API_KEY = os.environ["SEC_OPENDATA_API_KEY"]
BASE_URL = "https://api.sec.or.th"


def _headers():
    return {"Ocp-Apim-Subscription-Key": API_KEY}


def get_amcs():
    resp = requests.get(f"{BASE_URL}/v2/fund/general-info/amcs", headers=_headers(), timeout=10)
    resp.raise_for_status()
    return resp.json()["items"]


def find_equity_funds(policy_desc: str = "ตราสารทุน", max_pages: int = 40, page_size: int = 100):
    candidates = []
    cursor = None
    for _ in range(max_pages):
        params = {"page_size": page_size}
        if cursor:
            params["next_cursor"] = cursor
        resp = requests.get(f"{BASE_URL}/v2/fund/general-info/profiles", headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for item in data["items"]:
            if (item.get("policy_desc") == policy_desc
                    and item.get("fund_status") == "Registered"
                    and item.get("fund_class_name") == "main"):
                candidates.append(item)
        cursor = data.get("next_cursor")
        if not cursor:
            break
    return candidates


def get_daily_nav(proj_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    items = []
    cursor = None
    while True:
        params = {"proj_id": proj_id, "start_nav_date": start_date, "end_nav_date": end_date, "page_size": 100}
        if cursor:
            params["next_cursor"] = cursor
        resp = requests.get(f"{BASE_URL}/v2/fund/daily-info/nav", headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        items.extend(payload["items"])
        cursor = payload.get("next_cursor")
        if not cursor:
            break
    df = pd.DataFrame(items)[["nav_date", "proj_id", "last_val"]]
    df["nav_date"] = pd.to_datetime(df["nav_date"])
    return df.sort_values("nav_date").reset_index(drop=True)
