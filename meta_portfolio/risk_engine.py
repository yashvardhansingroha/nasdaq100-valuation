"""Rolling risk metrics: annualized volatility, covariance, correlation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from meta_portfolio import config


def rolling_volatility(
    returns: pd.DataFrame,
    window: int | None = None,
    ann_factor: int | None = None,
) -> pd.DataFrame:
    """Trailing-window annualized volatility per strategy."""
    window = window or config.ROLLING_WINDOW
    ann_factor = ann_factor or config.TRADING_DAYS_PER_YEAR
    return returns.rolling(window=window, min_periods=window).std() * np.sqrt(ann_factor)


def rolling_covariance(
    returns: pd.DataFrame,
    window: int | None = None,
) -> pd.DataFrame:
    """
    Trailing-window covariance matrices stacked as MultiIndex (date, asset_i).

    For date t, matrix uses returns in [t-window+1, t] (pandas default).
    Callers applying weights to day t+1 should shift appropriately.
    """
    window = window or config.ROLLING_WINDOW
    return returns.rolling(window=window, min_periods=window).cov()


def rolling_correlation(
    returns: pd.DataFrame,
    window: int | None = None,
) -> pd.DataFrame:
    """Trailing-window correlation matrices (MultiIndex like rolling_covariance)."""
    window = window or config.ROLLING_WINDOW
    return returns.rolling(window=window, min_periods=window).corr()


def covariance_at(
    cov_panel: pd.DataFrame,
    date: pd.Timestamp,
    assets: list[str] | None = None,
) -> np.ndarray | None:
    """Extract the n×n covariance matrix for a single date from a rolling cov panel."""
    try:
        block = cov_panel.loc[date]
    except KeyError:
        return None
    if assets is None:
        assets = list(block.columns)
    mat = block.loc[assets, assets].to_numpy(dtype=float)
    if np.isnan(mat).any():
        return None
    return mat
