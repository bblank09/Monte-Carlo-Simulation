def test_get_daily_nav_returns_dataframe():
    from sec_opendata_client import get_daily_nav
    df = get_daily_nav("M0027_2535", "2024-01-01", "2024-01-31")
    assert list(df.columns) == ["nav_date", "proj_id", "last_val"]
    assert len(df) > 0
    assert df["last_val"].dtype.kind == "f"
