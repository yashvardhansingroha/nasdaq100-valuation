"""Portfolio construction, transaction costs, and multi-strategy backtest."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from meta_portfolio import config
from meta_portfolio.allocator import (
    compute_dynamic_weights,
    static_60_40_weights,
    static_equal_weights,
)
from meta_portfolio.costs import apply_transaction_costs
from meta_portfolio.metrics import metrics_table, summarize_performance


@dataclass
class BacktestResult:
    returns: pd.DataFrame  # strategy asset log returns
    portfolio_gross: dict[str, pd.Series] = field(default_factory=dict)
    portfolio_net: dict[str, pd.Series] = field(default_factory=dict)
    weights: dict[str, pd.DataFrame] = field(default_factory=dict)
    turnover: dict[str, pd.Series] = field(default_factory=dict)
    costs: dict[str, pd.Series] = field(default_factory=dict)
    metrics: pd.DataFrame | None = None


def portfolio_log_return(weights: pd.DataFrame, asset_returns: pd.DataFrame) -> pd.Series:
    """Portfolio log return = log(1 + w·simple), with asset log returns converted first."""
    simple = np.expm1(asset_returns)
    aligned_w = weights.reindex(simple.index).fillna(0.0)
    port_simple = (aligned_w * simple).sum(axis=1)
    warm = weights.isna().any(axis=1)
    port_simple = port_simple.mask(warm)
    return np.log1p(port_simple)


def run_backtest(
    returns: pd.DataFrame,
    window: int | None = None,
    cost_rate: float | None = None,
) -> BacktestResult:
    """
    Run InvVol / MinVar / MaxDiv vs EqualWeight and 60/40.

    Dynamic methods are net of transaction costs; static benchmarks have zero turnover cost.
    """
    window = window or config.ROLLING_WINDOW
    cost_rate = config.TRANSACTION_COST if cost_rate is None else cost_rate

    dynamic = compute_dynamic_weights(returns, window=window)
    weights = {
        **dynamic,
        "EqualWeight": static_equal_weights(returns),
        "60/40": static_60_40_weights(returns),
    }

    result = BacktestResult(returns=returns, weights=weights)

    for name, w in weights.items():
        gross = portfolio_log_return(w, returns)
        is_dynamic = name in ("InvVol", "MinVar", "MaxDiv")
        if is_dynamic:
            net, turnover, costs = apply_transaction_costs(gross, w, cost_rate=cost_rate)
            # Warm-up NaNs stay NaN
            net = net.where(gross.notna())
            result.portfolio_gross[name] = gross
            result.portfolio_net[name] = net
            result.turnover[name] = turnover
            result.costs[name] = costs
        else:
            result.portfolio_gross[name] = gross
            result.portfolio_net[name] = gross
            result.turnover[name] = pd.Series(0.0, index=returns.index)
            result.costs[name] = pd.Series(0.0, index=returns.index)

    # Metrics on common valid period (after warm-up)
    ew = result.portfolio_net["EqualWeight"].dropna()
    rows = []
    for name, series in result.portfolio_net.items():
        s = series.dropna()
        if s.empty:
            continue
        # Align to intersection with EW for IR
        common = s.index.intersection(ew.index)
        rows.append(
            summarize_performance(
                s.loc[common],
                benchmark=ew.loc[common],
                turnover=result.turnover[name].reindex(common).fillna(0.0),
                costs=result.costs[name].reindex(common).fillna(0.0),
                name=name,
                log_input=True,
            )
        )
    result.metrics = metrics_table(rows)
    return result
