from unittest.mock import patch, Mock
import pandas as pd
from backend.app.data.sec_client import get_daily_nav


@patch("backend.app.data.sec_client.requests.get")
def test_get_daily_nav_paginates_and_sorts(mock_get):
    page1 = Mock(status_code=200)
    page1.raise_for_status = lambda: None
    page1.json.return_value = {
        "items": [{"nav_date": "2024-01-02", "proj_id": "A", "last_val": 10.5}],
        "next_cursor": "cursor-2",
    }
    page2 = Mock(status_code=200)
    page2.raise_for_status = lambda: None
    page2.json.return_value = {
        "items": [{"nav_date": "2024-01-01", "proj_id": "A", "last_val": 10.0}],
        "next_cursor": None,
    }
    mock_get.side_effect = [page1, page2]

    df = get_daily_nav("A", "2024-01-01", "2024-01-02")

    assert list(df["nav_date"]) == list(pd.to_datetime(["2024-01-01", "2024-01-02"]))
    assert mock_get.call_count == 2
