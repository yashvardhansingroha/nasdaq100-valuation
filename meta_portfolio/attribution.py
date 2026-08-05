"""Performance attribution: strategy contribution and cost drag."""

from __future__ import annotations

import numpy as np
import pandas as pd


def strategy_contributions(
    weights: pd.DataFrame,
    asset_log_returns: pd.DataFrame,
) -> pd.DataFrame:
    """
    Daily contribution of each sleeve using simple returns: w_i * r_i_simple.

    Sum across columns approximates portfolio simple return before costs.
    """
    simple = np.expm1(asset_log_returns)
    w = weights.reindex(simple.index)
    return w * simple


def attribution_summary(
    weights: pd.DataFrame,
    asset_log_returns: pd.DataFrame,
    costs: pd.Series | None = None,
) -> pd.DataFrame:
    """
    Aggregate attribution over the backtest window.

    Columns: total contribution per strategy, share of gross, cost drag.
    """
    contrib = strategy_contributions(weights, asset_log_returns).dropna(how="all")
    totals = contrib.sum()
    gross = float(totals.sum())
    rows = []
    for col in totals.index:
        rows.append(
            {
                "Component": col,
                "Total Contribution": float(totals[col]),
                "Share of Gross": float(totals[col] / gross) if gross != 0 else 0.0,
            }
        )
    if costs is not None:
        rows.append(
            {
                "Component": "Transaction Costs",
                "Total Contribution": float(-costs.reindex(contrib.index).fillna(0).sum()),
                "Share of Gross": float(
                    -costs.reindex(contrib.index).fillna(0).sum() / gross
                )
                if gross != 0
                else 0.0,
            }
        )
    return pd.DataFrame(rows).set_index("Component")


def vs_equal_weight_active(
    dynamic_net: pd.Series,
    equal_weight: pd.Series,
) -> pd.Series:
    """Active (dynamic − equal-weight) simple return series."""
    d = np.expm1(dynamic_net)
    e = np.expm1(equal_weight)
    aligned = d.align(e, join="inner")
    return aligned[0] - aligned[1]
