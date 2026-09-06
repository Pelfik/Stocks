from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .market_data import get_price_frame
from .optimizer import optimize


app = FastAPI(title="Portfolio Optimizer")

STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class OptimizeRequest(BaseModel):
    tickers: list[str] = Field(min_length=2, max_length=12)
    years: int = Field(default=5, ge=1, le=15)
    risk_free_rate: float = Field(default=0.03, ge=-0.05, le=0.20)

    @field_validator("tickers")
    @classmethod
    def normalize_tickers(cls, values: list[str]):
        cleaned = []
        for value in values:
            ticker = value.strip().upper()
            if ticker and ticker not in cleaned:
                cleaned.append(ticker)

        if len(cleaned) < 2:
            raise ValueError("Choose at least two unique tickers")

        return cleaned


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/test-yahoo")
def test_yahoo():
    import yfinance as yf

    df = yf.download(
        "AAPL",
        period="5d",
        progress=False,
        threads=False,
    )

    return {
        "rows": len(df),
        "columns": list(map(str, df.columns)),
    }

@app.post("/api/optimize")
def api_optimize(request: OptimizeRequest):
    try:
        prices = get_price_frame(request.tickers, years=request.years)
        result = optimize(prices, risk_free_rate=request.risk_free_rate)
        result["observations"] = len(prices)
        result["start_date"] = prices.index.min().strftime("%Y-%m-%d")
        result["end_date"] = prices.index.max().strftime("%Y-%m-%d")
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
