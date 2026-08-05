"""Performance metrics for portfolio return series."""

from __future__ import annotations

import numpy as np
import pandas as pd

from meta_portfolio import config


def _to_simple(log_returns: pd.Series) -> pd.Series:
    """Convert log returns to simple returns for compounding metrics."""
    return np.expm1(log_returns)


def cumulative_wealth(returns: pd.Series, log_input: bool = True) -> pd.Series:
    """Equity curve starting at 1.0. If log_input, convert first."""
    r = _to_simple(returns) if log_input else returns
    return (1.0 + r.fillna(0.0)).cumprod()


def max_drawdown(wealth: pd.Series) -> float:
    peak = wealth.cummax()
    dd = wealth / peak - 1.0
    return float(dd.min())


def cagr(wealth: pd.Series, periods_per_year: int | None = None) -> float:
    periods_per_year = periods_per_year or config.TRADING_DAYS_PER_YEAR
    if len(wealth) < 2 or wealth.iloc[-1] <= 0:
        return 0.0
    years = len(wealth) / periods_per_year
    if years <= 0:
        return 0.0
    return float(wealth.iloc[-1] ** (1.0 / years) - 1.0)


def annualized_vol(returns: pd.Series, log_input: bool = True) -> float:
    r = _to_simple(returns) if log_input else returns
    return float(r.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR))


def sharpe_ratio(
    returns: pd.Series,
    rf: float | None = None,
    log_input: bool = True,
) -> float:
    rf = config.RISK_FREE_RATE if rf is None else rf
    r = _to_simple(returns) if log_input else returns
    ann_ret = cagr(cumulative_wealth(returns, log_input=log_input))
    vol = annualized_vol(returns, log_input=log_input)
    if vol <= 0:
        return 0.0
    return float((ann_ret - rf) / vol)


def sortino_ratio(
    returns: pd.Series,
    rf: float | None = None,
    log_input: bool = True,
) -> float:
    rf = config.RISK_FREE_RATE if rf is None else rf
    r = _to_simple(returns) if log_input else returns
    ann_ret = cagr(cumulative_wealth(returns, log_input=log_input))
    downside = r[r < 0]
    if len(downside) == 0:
        return float("nan")
    down_vol = float(downside.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR))
    if down_vol <= 0:
        return float("nan")
    return float((ann_ret - rf) / down_vol)


def calmar_ratio(returns: pd.Series, log_input: bool = True) -> float:
    wealth = cumulative_wealth(returns, log_input=log_input)
    mdd = abs(max_drawdown(wealth))
    if mdd <= 0:
        return float("nan")
    return float(cagr(wealth) / mdd)


def information_ratio(
    returns: pd.Series,
    benchmark: pd.Series,
    log_input: bool = True,
) -> float:
    r = _to_simple(returns) if log_input else returns
    b = _to_simple(benchmark) if log_input else benchmark
    active = r.align(b, join="inner")[0] - b.align(r, join="inner")[0]
    te = float(active.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR))
    if te <= 0:
        return 0.0
    active_ann = float(active.mean() * config.TRADING_DAYS_PER_YEAR)
    return float(active_ann / te)


def historical_var(
    returns: pd.Series,
    confidence: float = 0.95,
    log_input: bool = True,
) -> float:
    """
    Historical daily VaR at the given confidence level.

    Returns a negative number (loss) as a fraction of portfolio value,
    e.g. -0.02 means a 2% daily loss at the 95th percentile.
    """
    r = _to_simple(returns) if log_input else returns
    r = r.dropna()
    if r.empty:
        return float("nan")
    return float(np.quantile(r, 1.0 - confidence))


def summarize_performance(
    returns: pd.Series,
    benchmark: pd.Series | None = None,
    turnover: pd.Series | None = None,
    costs: pd.Series | None = None,
    name: str = "Portfolio",
    log_input: bool = True,
) -> dict[str, float | str]:
    wealth = cumulative_wealth(returns, log_input=log_input)
    metrics: dict[str, float | str] = {
        "Strategy": name,
        "Ann. Return": cagr(wealth),
        "Ann. Vol": annualized_vol(returns, log_input=log_input),
        "Sharpe": sharpe_ratio(returns, log_input=log_input),
        "Sortino": sortino_ratio(returns, log_input=log_input),
        "Max Drawdown": max_drawdown(wealth),
        "Calmar": calmar_ratio(returns, log_input=log_input),
        "VaR 95% (1d)": historical_var(returns, confidence=0.95, log_input=log_input),
    }
    if benchmark is not None:
        metrics["Info Ratio vs EW"] = information_ratio(
            returns, benchmark, log_input=log_input
        )
    if turnover is not None:
        metrics["Ann. Turnover"] = float(turnover.mean() * config.TRADING_DAYS_PER_YEAR)
    if costs is not None:
        metrics["Total Cost Drag"] = float(costs.sum())
        # Approximate annualized cost drag from cumulative compound effect
        metrics["Ann. Cost Drag"] = float(costs.mean() * config.TRADING_DAYS_PER_YEAR)
    return metrics


def metrics_table(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows).set_index("Strategy")
    return df
