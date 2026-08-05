"""Analyze which companies contribute most to index mispricing."""

from __future__ import annotations

import pandas as pd

from utils.logging_config import setup_logging
from utils.models import ValuationResult

logger = setup_logging(__name__)


def compute_contributions(results: list[ValuationResult]) -> pd.DataFrame:
    """
    Compute each company's weighted contribution to index mispricing.

    contribution = index_weight * upside
    """
    records = []
    for r in results:
        if r.upside is None or r.blended_value is None:
            continue
        records.append(
            {
                "ticker": r.ticker,
                "sector": r.sector,
                "price": r.price,
                "blended_value": r.blended_value,
                "upside": r.upside,
                "index_weight": r.index_weight,
                "contribution": r.index_weight * r.upside,
                "confidence_score": r.confidence_score,
            }
        )

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records).sort_values("contribution", ascending=False)
    return df


def top_overvalued(results: list[ValuationResult], n: int = 10) -> pd.DataFrame:
    """Return top N overvalued companies (most negative upside)."""
    df = compute_contributions(results)
    if df.empty:
        return df
    return df.nsmallest(n, "upside")


def top_undervalued(results: list[ValuationResult], n: int = 10) -> pd.DataFrame:
    """Return top N undervalued companies (highest upside)."""
    df = compute_contributions(results)
    if df.empty:
        return df
    return df.nlargest(n, "upside")


def largest_contributors(results: list[ValuationResult], n: int = 10) -> pd.DataFrame:
    """Return companies with largest absolute contribution to mispricing."""
    df = compute_contributions(results)
    if df.empty:
        return df
    df["abs_contribution"] = df["contribution"].abs()
    return df.nlargest(n, "abs_contribution")
