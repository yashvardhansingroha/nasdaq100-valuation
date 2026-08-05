"""Sector-level analysis of valuations and sentiment."""

from __future__ import annotations

import pandas as pd

from utils.logging_config import setup_logging
from utils.models import ValuationResult

logger = setup_logging(__name__)


def analyze_sectors(
    results: list[ValuationResult],
    sentiment_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Compute sector-level averages for upside, confidence, weight, and sentiment.
    """
    records = []
    for r in results:
        records.append(
            {
                "ticker": r.ticker,
                "sector": r.sector or "Unknown",
                "upside": r.upside,
                "confidence_score": r.confidence_score,
                "index_weight": r.index_weight,
                "blended_value": r.blended_value,
                "price": r.price,
            }
        )

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    if sentiment_df is not None and not sentiment_df.empty:
        df = df.merge(
            sentiment_df[["ticker", "overall_sentiment"]],
            on="ticker",
            how="left",
        )
    else:
        df["overall_sentiment"] = None

    sector_stats = (
        df.groupby("sector")
        .agg(
            avg_upside=("upside", "mean"),
            avg_confidence=("confidence_score", "mean"),
            avg_sentiment=("overall_sentiment", "mean"),
            weight_contribution=("index_weight", "sum"),
            company_count=("ticker", "count"),
            valued_count=("blended_value", lambda x: x.notna().sum()),
        )
        .reset_index()
        .sort_values("weight_contribution", ascending=False)
    )

    return sector_stats
