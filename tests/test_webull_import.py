def test_get_webull_prices_schema():
    from webull_client import get_webull_prices
    df = get_webull_prices(["SPY", "QQQ", "TLT"])
    assert list(df.columns) == ["date", "ticker", "close"]
    assert df["ticker"].nunique() == 3
    assert df.groupby("ticker")["date"].count().min() > 500  # roughly 2+ years of trading days per ticker
