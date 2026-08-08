"""App Store review synthesis and theme extraction."""

from __future__ import annotations

import pandas as pd


def review_theme_summary(reviews: pd.DataFrame) -> pd.DataFrame:
    """Aggregate ratings and sentiment by theme."""
    summary = (
        reviews.groupby("theme")
        .agg(
            count=("review_id", "count"),
            avg_rating=("rating", "mean"),
            pct_negative=("sentiment", lambda s: (s == "negative").mean()),
            pct_positive=("sentiment", lambda s: (s == "positive").mean()),
        )
        .reset_index()
    )
    summary["share_of_reviews"] = summary["count"] / len(reviews)
    return summary.sort_values("pct_negative", ascending=False)


def review_by_platform(reviews: pd.DataFrame) -> pd.DataFrame:
    return (
        reviews.groupby("platform")
        .agg(avg_rating=("rating", "mean"), count=("review_id", "count"))
        .reset_index()
    )


def trust_gap_signals(reviews: pd.DataFrame) -> list[dict]:
    """Map negative review themes to product trust gaps."""
    theme_summary = review_theme_summary(reviews)
    trust_themes = ["trust_safety", "delivery_speed", "product_freshness", "support"]
    signals = []
    for _, row in theme_summary.iterrows():
        if row["theme"] not in trust_themes:
            continue
        signals.append(
            {
                "theme": row["theme"],
                "avg_rating": round(row["avg_rating"], 2),
                "negative_share": round(row["pct_negative"] * 100, 1),
                "review_volume": int(row["count"]),
                "gap_severity": "high" if row["pct_negative"] > 0.45 else "medium",
            }
        )
    return sorted(signals, key=lambda x: x["negative_share"], reverse=True)
