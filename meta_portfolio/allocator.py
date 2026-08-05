"""Dynamic allocation methods: inverse-vol, minimum variance, max diversification."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from meta_portfolio import config
from meta_portfolio.risk_engine import covariance_at, rolling_covariance, rolling_volatility


def _normalize(weights: np.ndarray) -> np.ndarray:
    s = weights.sum()
    if s <= 0:
        return np.full_like(weights, 1.0 / len(weights))
    return weights / s


def inverse_vol_weights(vols: np.ndarray, vol_floor: float | None = None) -> np.ndarray:
    """w_i ∝ 1/σ_i, renormalized to sum to 1."""
    vol_floor = vol_floor if vol_floor is not None else config.VOL_FLOOR
    safe = np.maximum(vols, vol_floor)
    raw = 1.0 / safe
    return _normalize(raw)


def _optimize(objective, x0, bounds, constraints) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 200, "ftol": 1e-12, "disp": False},
        )
    weight_min = bounds[0][0]
    weight_max = bounds[0][1]
    if not result.success:
        return _normalize(x0)
    return _normalize(np.clip(result.x, weight_min, weight_max))


def minimum_variance_weights(
    cov: np.ndarray,
    weight_min: float | None = None,
    weight_max: float | None = None,
) -> np.ndarray:
    """Long-only minimum variance portfolio with box constraints."""
    weight_min = config.WEIGHT_MIN if weight_min is None else weight_min
    weight_max = config.WEIGHT_MAX if weight_max is None else weight_max
    n = cov.shape[0]
    x0 = np.full(n, 1.0 / n)

    def portfolio_variance(w: np.ndarray) -> float:
        return float(w @ cov @ w)

    return _optimize(
        portfolio_variance,
        x0,
        [(weight_min, weight_max)] * n,
        [{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
    )


def max_diversification_weights(
    cov: np.ndarray,
    vols: np.ndarray,
    weight_min: float | None = None,
    weight_max: float | None = None,
) -> np.ndarray:
    """Maximize diversification ratio: (w'σ) / sqrt(w'Σw)."""
    weight_min = config.WEIGHT_MIN if weight_min is None else weight_min
    weight_max = config.WEIGHT_MAX if weight_max is None else weight_max
    n = cov.shape[0]
    x0 = np.full(n, 1.0 / n)
    vol_floor = config.VOL_FLOOR
    safe_vols = np.maximum(vols, vol_floor)

    def neg_div_ratio(w: np.ndarray) -> float:
        port_vol = np.sqrt(max(float(w @ cov @ w), vol_floor))
        weighted_vol = float(w @ safe_vols)
        return -weighted_vol / port_vol

    return _optimize(
        neg_div_ratio,
        x0,
        [(weight_min, weight_max)] * n,
        [{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
    )

def compute_dynamic_weights(
    returns: pd.DataFrame,
    window: int | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Compute daily weight panels for InvVol, MinVar, MaxDiv.

    Lookahead rule: weights for day t use risk estimated on returns
    through t-1 (shift rolling metrics by 1), then apply to day-t returns.
    """
    window = window or config.ROLLING_WINDOW
    assets = list(returns.columns)
    vols = rolling_volatility(returns, window=window)
    cov_panel = rolling_covariance(returns, window=window)

    # Shift so day-t weights only use info available through t-1
    vols_lag = vols.shift(1)
    # Build weight frames
    methods = {
        "InvVol": pd.DataFrame(index=returns.index, columns=assets, dtype=float),
        "MinVar": pd.DataFrame(index=returns.index, columns=assets, dtype=float),
        "MaxDiv": pd.DataFrame(index=returns.index, columns=assets, dtype=float),
    }

    prev = {
        "InvVol": np.full(len(assets), 1.0 / len(assets)),
        "MinVar": np.full(len(assets), 1.0 / len(assets)),
        "MaxDiv": np.full(len(assets), 1.0 / len(assets)),
    }

    for dt in returns.index:
        v = vols_lag.loc[dt]
        if v.isna().any():
            continue

        # Covariance through t-1: use lagged date from cov panel
        # vols_lag at dt corresponds to rolling window ending at previous date
        loc = returns.index.get_loc(dt)
        if loc == 0:
            continue
        prev_dt = returns.index[loc - 1]
        cov = covariance_at(cov_panel, prev_dt, assets)
        vol_vec = v[assets].to_numpy(dtype=float)

        inv = inverse_vol_weights(vol_vec)
        methods["InvVol"].loc[dt] = inv
        prev["InvVol"] = inv

        if cov is None:
            methods["MinVar"].loc[dt] = prev["MinVar"]
            methods["MaxDiv"].loc[dt] = prev["MaxDiv"]
            continue

        # Annualize cov for optimizer consistency with annualized vols in MaxDiv
        # Use daily cov for variance minimization (scale cancels in min-var);
        # for MaxDiv, vols are annualized — convert cov to annualized.
        cov_ann = cov * config.TRADING_DAYS_PER_YEAR
        mv = minimum_variance_weights(cov_ann)
        md = max_diversification_weights(cov_ann, vol_vec)
        methods["MinVar"].loc[dt] = mv
        methods["MaxDiv"].loc[dt] = md
        prev["MinVar"] = mv
        prev["MaxDiv"] = md

    return methods


def static_equal_weights(returns: pd.DataFrame) -> pd.DataFrame:
    n = len(returns.columns)
    return pd.DataFrame(
        np.full((len(returns), n), 1.0 / n),
        index=returns.index,
        columns=returns.columns,
    )


def static_60_40_weights(returns: pd.DataFrame) -> pd.DataFrame:
    w = config.BENCH_60_40
    data = {col: w.get(col, 0.0) for col in returns.columns}
    return pd.DataFrame(data, index=returns.index)
