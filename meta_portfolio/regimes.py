"""Regime-sliced performance analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd

from meta_portfolio import config
from meta_portfolio.metrics import cumulative_wealth, max_drawdown


def slice_returns(returns: pd.Series, start: str, end: str) -> pd.Series:
    return returns.loc[start:end].dropna()


def _period_total_return(log_returns: pd.Series) -> float:
    """Non-annualized total return over the slice (avoids CAGR blow-ups on short windows)."""
    wealth = cumulative_wealth(log_returns, log_input=True)
    if wealth.empty:
        return 0.0
    return float(wealth.iloc[-1] / wealth.iloc[0] - 1.0)


def _period_vol(log_returns: pd.Series) -> float:
    simple = np.expm1(log_returns)
    return float(simple.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR))


def _period_sharpe(log_returns: pd.Series, rf: float | None = None) -> float:
    """Annualized Sharpe from daily simple returns (stable on short windows)."""
    rf = config.RISK_FREE_RATE if rf is None else rf
    simple = np.expm1(log_returns)
    vol = float(simple.std() * np.sqrt(config.TRADING_DAYS_PER_YEAR))
    if vol <= 0:
        return 0.0
    ann_mean = float(simple.mean() * config.TRADING_DAYS_PER_YEAR)
    return float((ann_mean - rf) / vol)


def regime_metrics_table(
    portfolio_net: dict[str, pd.Series],
    regimes: dict[str, tuple[str, str]] | None = None,
) -> pd.DataFrame:
    """
    Build a MultiIndex table: (Regime, Strategy) → key metrics.

    Uses total period return (not CAGR) so short regimes stay interpretable.
    """
    regimes = regimes or config.REGIMES
    rows = []
    for regime_name, (start, end) in regimes.items():
        for strat, series in portfolio_net.items():
            s = slice_returns(series, start, end)
            if len(s) < 5:
                continue
            wealth = cumulative_wealth(s, log_input=True)
            rows.append(
                {
                    "Regime": regime_name,
                    "Strategy": strat,
                    "Total Return": _period_total_return(s),
                    "Sharpe": _period_sharpe(s),
                    "Max Drawdown": max_drawdown(wealth),
                    "Ann. Vol": _period_vol(s),
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).set_index(["Regime", "Strategy"])
