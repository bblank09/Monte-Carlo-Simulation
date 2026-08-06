from typing import Any


def records(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("data", "result", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [payload]
    return []


def pick(record: dict, names: list[str], required: bool = True):
    for name in names:
        if name in record and record[name] not in (None, ""):
            return record[name]
    if required:
        raise KeyError(f"None of the expected SEC fields were present: {names}")
    return None


def to_float(value):
    if value in (None, "", "-"):
        return None
    return float(str(value).replace(",", ""))


def normalize_daily_nav_record(record: dict, proj_id: str | None = None) -> dict:
    resolved_proj_id = str(proj_id or pick(record, ["proj_id", "PROJ_ID", "project_id"]))
    nav_date = str(pick(record, ["nav_date", "NAV_DATE", "date"]))
    nav_per_unit = to_float(pick(record, ["last_val", "LAST_VAL", "nav_per_unit", "NAV_PER_UNIT"]))
    if nav_per_unit is None or nav_per_unit <= 0:
        raise ValueError(f"Invalid NAV for {resolved_proj_id} {nav_date}: {nav_per_unit}")
    return {
        "proj_id": resolved_proj_id,
        "unique_id": str(pick(record, ["unique_id", "UNIQUE_ID"], required=False) or ""),
        "fund_class_name": str(pick(record, ["fund_class_name", "FUND_CLASS_NAME"], required=False) or ""),
        "nav_date": nav_date,
        "nav_per_unit": nav_per_unit,
        "net_asset": to_float(pick(record, ["net_asset", "NET_ASSET", "net_assets"], required=False)),
        "sell_price": to_float(pick(record, ["sell_price", "SELL_PRICE"], required=False)),
        "buy_price": to_float(pick(record, ["buy_price", "BUY_PRICE"], required=False)),
        "last_upd_date": pick(record, ["last_upd_date", "LAST_UPD_DATE", "updated_at"], required=False),
    }
