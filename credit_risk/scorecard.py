"""WOE / IV application scorecard utilities for retail credit risk."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

import config


def _iv_strength(iv: float) -> str:
    if iv < 0.02:
        return "weak"
    if iv < 0.10:
        return "medium"
    if iv < 0.30:
        return "strong"
    return "suspicious"


@dataclass
class ScorecardResult:
    woe_iv_summary: pd.DataFrame
    scorecard_points: pd.DataFrame
    feature_iv: pd.DataFrame
    bin_edges: dict[str, np.ndarray]
    bin_points: dict[str, dict[int, float]]


def _quantile_edges(series: pd.Series, n_bins: int) -> np.ndarray:
    """Equal-frequency edges; drop duplicate quantiles for sparse columns."""
    clean = series.dropna()
    qs = np.linspace(0, 1, n_bins + 1)
    edges = np.unique(np.quantile(clean, qs))
    if len(edges) < 3:
        # Fall back to equal-width if quantiles collapse
        lo, hi = float(clean.min()), float(clean.max())
        if lo == hi:
            return np.array([lo - 0.5, hi + 0.5])
        edges = np.linspace(lo, hi, min(n_bins, 3) + 1)
    return edges


def _assign_bin(values: pd.Series, edges: np.ndarray) -> pd.Series:
    return pd.cut(values, bins=edges, include_lowest=True, labels=False, duplicates="drop")


def build_scorecard(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    features: Iterable[str] | None = None,
    n_bins: int = config.SCORECARD_BINS,
) -> ScorecardResult:
    """Fit WOE bins and IV on the training fold only (no leakage)."""
    features = list(features or config.SCORECARD_FEATURES)
    y = y_train.astype(int)
    n_good = max((y == 0).sum(), 1)
    n_bad = max((y == 1).sum(), 1)

    woe_rows: list[dict] = []
    points_rows: list[dict] = []
    bin_edges: dict[str, np.ndarray] = {}
    bin_points: dict[str, dict[int, float]] = {}
    iv_rows: list[dict] = []

    weight_per_feature = 100.0 / max(len(features), 1)

    for feature in features:
        if feature not in X_train.columns:
            continue

        series = pd.to_numeric(X_train[feature], errors="coerce")
        edges = _quantile_edges(series, n_bins)
        bins = _assign_bin(series, edges)
        bin_edges[feature] = edges

        feature_woe: dict[int, float] = {}
        feature_iv = 0.0

        for bin_id in sorted(bins.dropna().unique()):
            mask = bins == bin_id
            goods = ((y == 0) & mask).sum() + 0.5  # Laplace smoothing
            bads = ((y == 1) & mask).sum() + 0.5
            pct_good = goods / (n_good + 0.5 * len(edges))
            pct_bad = bads / (n_bad + 0.5 * len(edges))
            woe = float(np.log(pct_good / pct_bad))
            iv_contrib = (pct_good - pct_bad) * woe
            feature_woe[int(bin_id)] = woe
            feature_iv += iv_contrib

            left = edges[int(bin_id)] if int(bin_id) < len(edges) else edges[-2]
            right = edges[min(int(bin_id) + 1, len(edges) - 1)]
            woe_rows.append(
                {
                    "feature": feature,
                    "bin_id": int(bin_id),
                    "bin_low": left,
                    "bin_high": right,
                    "n_obs": int(mask.sum()),
                    "n_good": int(((y == 0) & mask).sum()),
                    "n_bad": int(((y == 1) & mask).sum()),
                    "pct_good": pct_good,
                    "pct_bad": pct_bad,
                    "woe": woe,
                    "iv_contribution": iv_contrib,
                }
            )

        # Scale WOE to points within feature
        woes = list(feature_woe.values())
        woe_min, woe_max = min(woes), max(woes)
        span = (woe_max - woe_min) if woe_max != woe_min else 1.0
        pts_map: dict[int, float] = {}
        for bin_id, woe in feature_woe.items():
            pts = ((woe - woe_min) / span) * weight_per_feature
            pts_map[bin_id] = pts
            points_rows.append(
                {
                    "feature": feature,
                    "bin_id": bin_id,
                    "woe": woe,
                    "points": pts,
                }
            )
        bin_points[feature] = pts_map

        iv_rows.append(
            {
                "feature": feature,
                "iv": feature_iv,
                "strength": _iv_strength(feature_iv),
            }
        )

    woe_iv_summary = pd.DataFrame(woe_rows)
    scorecard_points = pd.DataFrame(points_rows)
    feature_iv = pd.DataFrame(iv_rows).sort_values("iv", ascending=False)

    # Attach total IV onto each WOE row for export convenience
    if not woe_iv_summary.empty and not feature_iv.empty:
        iv_map = feature_iv.set_index("feature")["iv"].to_dict()
        woe_iv_summary["feature_iv"] = woe_iv_summary["feature"].map(iv_map)

    return ScorecardResult(
        woe_iv_summary=woe_iv_summary,
        scorecard_points=scorecard_points,
        feature_iv=feature_iv,
        bin_edges=bin_edges,
        bin_points=bin_points,
    )


def apply_scorecard(
    X: pd.DataFrame,
    result: ScorecardResult,
    score_min: int = config.SCORECARD_MIN,
    score_max: int = config.SCORECARD_MAX,
) -> pd.Series:
    """Map features to application scores (FICO-style 300–850)."""
    raw = pd.Series(0.0, index=X.index)
    for feature, edges in result.bin_edges.items():
        if feature not in X.columns:
            continue
        series = pd.to_numeric(X[feature], errors="coerce")
        bins = _assign_bin(series, edges)
        pts_map = result.bin_points[feature]
        # Missing / out-of-range bins get mid-weight (neutral)
        default_pts = np.mean(list(pts_map.values())) if pts_map else 0.0
        raw += bins.map(pts_map).fillna(default_pts)

    # raw typically in [0, 100]; scale to [score_min, score_max]
    r_min, r_max = float(raw.min()), float(raw.max())
    if r_max == r_min:
        return pd.Series(float((score_min + score_max) / 2), index=X.index)
    scaled = score_min + (raw - r_min) / (r_max - r_min) * (score_max - score_min)
    return scaled.round(0).astype(int)


def score_decile_default_rates(
    scores: pd.Series,
    y: pd.Series,
    n_deciles: int = 10,
) -> pd.DataFrame:
    """Validate monotonicity: higher score bands should have lower default rates."""
    df = pd.DataFrame({"score": scores, "default": y.astype(int)})
    df = df.dropna()
    try:
        df["decile"] = pd.qcut(df["score"], q=n_deciles, labels=False, duplicates="drop")
    except ValueError:
        df["decile"] = pd.cut(df["score"], bins=n_deciles, labels=False, duplicates="drop")
    return (
        df.groupby("decile", as_index=False)
        .agg(
            n_obs=("default", "size"),
            default_rate=("default", "mean"),
            avg_score=("score", "mean"),
        )
        .sort_values("decile")
    )
