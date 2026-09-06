from pathlib import Path
import sqlite3
import pandas as pd

DB_PATH = Path("data/market.db")


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            adj_close REAL NOT NULL,
            PRIMARY KEY (ticker, date)
        )
        """
    )
    return conn


def load_prices(ticker: str, start: str, end: str) -> pd.Series:
    with _connect() as conn:
        df = pd.read_sql_query(
            """
            SELECT date, adj_close
            FROM prices
            WHERE ticker = ?
              AND date >= ?
              AND date <= ?
            ORDER BY date
            """,
            conn,
            params=(ticker.upper(), start, end),
        )

    if df.empty:
        return pd.Series(dtype=float, name=ticker.upper())

    df["date"] = pd.to_datetime(df["date"])
    return pd.Series(
        df["adj_close"].values,
        index=df["date"],
        name=ticker.upper(),
        dtype=float,
    )


def save_prices(ticker: str, series: pd.Series) -> None:
    ticker = ticker.upper()
    rows = [
        (ticker, pd.Timestamp(idx).strftime("%Y-%m-%d"), float(value))
        for idx, value in series.dropna().items()
    ]

    if not rows:
        return

    with _connect() as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO prices (ticker, date, adj_close)
            VALUES (?, ?, ?)
            """,
            rows,
        )
        conn.commit()
