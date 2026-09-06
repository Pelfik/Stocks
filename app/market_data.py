from datetime import date, timedelta
import pandas as pd
import yfinance as yf

from .database import load_prices, save_prices


def _download_ticker(ticker: str, start: str, end: str) -> pd.Series:
    end_plus_one = (
        pd.Timestamp(end) + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    ticker_obj = yf.Ticker(ticker)

    df = ticker_obj.history(
        start=start,
        end=end_plus_one,
        auto_adjust=True,
        timeout=10,
    )

    if df.empty:
        raise ValueError(f"No market data found for {ticker}")

    close = df["Close"].dropna().astype(float)

    close.index = pd.to_datetime(close.index)

    if close.index.tz is not None:
        close.index = close.index.tz_localize(None)

    close.name = ticker.upper()

    save_prices(ticker, close)

    return close


def get_price_series(ticker: str, years: int = 5) -> pd.Series:
    ticker = ticker.upper().strip()
    if not ticker:
        raise ValueError("Ticker cannot be empty")

    end = date.today()
    start = end - timedelta(days=365 * years + 10)

    start_s = start.isoformat()
    end_s = end.isoformat()

    cached = load_prices(ticker, start_s, end_s)

    # Good enough for MVP: if cache contains recent data, use it.
    if not cached.empty:
        latest = cached.index.max().date()
        if latest >= end - timedelta(days=5):
            return cached

    return _download_ticker(ticker, start_s, end_s)


def get_price_frame(tickers: list[str], years: int = 5) -> pd.DataFrame:
    series = [get_price_series(ticker, years=years) for ticker in tickers]
    prices = pd.concat(series, axis=1).dropna()

    if len(prices) < 60:
        raise ValueError("Not enough overlapping price history for selected assets")

    return prices
