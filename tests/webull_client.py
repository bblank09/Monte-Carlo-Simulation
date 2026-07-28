import pandas as pd
import yfinance as yf

# NOTE: Webull TH's OpenAPI (App Key/Secret in webull/apikey/) proved unreliable in this
# session - token verification consistently expired (ERROR_CHECK_TOKEN, status EXPIRED)
# on 3 of 4 attempts, likely requiring a manual device-approval step not resolved here.
# Falling back to yfinance as the practical data source for US-listed tickers (SPY/QQQ/TLT).
# Verified: prices match what Webull returned for the one successful call (SPY close on
# 2026-07-24: 738.93 both sources).


def get_webull_prices(symbols: list[str], start: str = "2020-01-01", end: str = "2025-12-31") -> pd.DataFrame:
    """Fixed date range (matching the SEC NAV fetch window in Task 3) rather than a relative
    period like "5y" - a relative window shifts every time this is called (yfinance measures
    it from "now"), which silently changes mu/sigma estimates between runs and breaks
    reproducibility of every downstream result and the Portfolio Visualizer benchmark."""
    data = yf.download(symbols, start=start, end=end, interval="1d", auto_adjust=False, progress=False)
    close = data["Close"]
    long_df = close.reset_index().melt(id_vars="Date", var_name="ticker", value_name="close")
    long_df = long_df.rename(columns={"Date": "date"}).dropna(subset=["close"])
    return long_df[["date", "ticker", "close"]].sort_values(["ticker", "date"]).reset_index(drop=True)
