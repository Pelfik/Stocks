import numpy as np
import pandas as pd
from scipy.optimize import minimize


TRADING_DAYS = 252


def _portfolio_stats(weights, expected_returns, covariance, risk_free_rate):
    ret = float(weights @ expected_returns)
    vol = float(np.sqrt(weights @ covariance @ weights))
    sharpe = (ret - risk_free_rate) / vol if vol > 0 else np.nan
    return ret, vol, sharpe


def _minimize_volatility(expected_returns, covariance, target_return=None):
    n = len(expected_returns)
    x0 = np.repeat(1 / n, n)
    bounds = [(0.0, 1.0)] * n

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    if target_return is not None:
        constraints.append(
            {
                "type": "eq",
                "fun": lambda w: float(w @ expected_returns) - target_return,
            }
        )

    result = minimize(
        lambda w: np.sqrt(w @ covariance @ w),
        x0=x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-10},
    )

    if not result.success:
        raise ValueError(f"Optimization failed: {result.message}")

    return result.x


def optimize(prices: pd.DataFrame, risk_free_rate: float = 0.03):
    returns = prices.pct_change().dropna()

    expected_returns = returns.mean().to_numpy() * TRADING_DAYS
    covariance = returns.cov().to_numpy() * TRADING_DAYS
    tickers = list(prices.columns)
    n = len(tickers)

    if n < 2:
        raise ValueError("Select at least two assets")

    x0 = np.repeat(1 / n, n)
    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    max_sharpe_result = minimize(
        lambda w: -_portfolio_stats(
            w, expected_returns, covariance, risk_free_rate
        )[2],
        x0=x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-10},
    )

    if not max_sharpe_result.success:
        raise ValueError(f"Max Sharpe optimization failed: {max_sharpe_result.message}")

    min_var_weights = _minimize_volatility(expected_returns, covariance)

    max_sharpe_stats = _portfolio_stats(
        max_sharpe_result.x, expected_returns, covariance, risk_free_rate
    )
    min_var_stats = _portfolio_stats(
        min_var_weights, expected_returns, covariance, risk_free_rate
    )

    # Efficient frontier between minimum-variance return and max individual expected return.
    target_min = min_var_stats[0]
    target_max = float(np.max(expected_returns))
    target_returns = np.linspace(target_min, target_max, 40)

    frontier = []
    for target in target_returns:
        try:
            w = _minimize_volatility(
                expected_returns, covariance, target_return=float(target)
            )
            ret, vol, _ = _portfolio_stats(
                w, expected_returns, covariance, risk_free_rate
            )
            frontier.append(
                {
                    "return": ret,
                    "volatility": vol,
                }
            )
        except ValueError:
            continue

    def pack(weights, stats):
        ret, vol, sharpe = stats
        return {
            "return": ret,
            "volatility": vol,
            "sharpe": sharpe,
            "weights": {
                ticker: float(weight)
                for ticker, weight in zip(tickers, weights)
            },
        }

    annual_asset_returns = {
        ticker: float(value)
        for ticker, value in zip(tickers, expected_returns)
    }

    return {
        "assets": tickers,
        "asset_expected_returns": annual_asset_returns,
        "max_sharpe": pack(max_sharpe_result.x, max_sharpe_stats),
        "min_variance": pack(min_var_weights, min_var_stats),
        "frontier": frontier,
    }
