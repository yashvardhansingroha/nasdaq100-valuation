"""Transaction cost model based on portfolio turnover."""

from __future__ import annotations

import numpy as np
import pandas as pd

from meta_portfolio import config


def daily_turnover(weights: pd.DataFrame) -> pd.Series:
    """One-way turnover: sum_i |w_{i,t} - w_{i,t-1}|."""
    delta = weights.diff().abs().sum(axis=1)
    delta.iloc[0] = 0.0
    return delta


def apply_transaction_costs(
    gross_returns: pd.Series,
    weights: pd.DataFrame,
    cost_rate: float | None = None,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Net returns = gross - turnover * cost_rate.

    Returns (net_returns, turnover, costs).
    """
    cost_rate = config.TRANSACTION_COST if cost_rate is None else cost_rate
    turnover = daily_turnover(weights)
    # Align: cost paid when weights change at t, deducted from return earned at t
    costs = turnover * cost_rate
    net = gross_returns - costs.reindex(gross_returns.index).fillna(0.0)
    return net, turnover, costs
