from backend.app.data.sec_client import find_funds


def test_can_list_cached_sec_funds():
    funds = find_funds()
    assert isinstance(funds, list)
    assert len(funds) > 0
    assert "proj_id" in funds[0]
