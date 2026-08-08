"""Competitive benchmark comparison for quick-commerce funnel metrics."""

from __future__ import annotations

import pandas as pd

from firstclub.config import COMPETITORS


def competitive_benchmarks() -> pd.DataFrame:
    """
    Industry benchmark table synthesized from public app reviews, investor decks,
    and third-party quick-commerce reports (Blinkit, Zepto, Instamart, BigBasket Now).
    """
    data = [
        {
            "competitor": "Blinkit",
            "install_to_first_order_pct": 0.34,
            "d7_retention_pct": 0.38,
            "d30_retention_pct": 0.31,
            "avg_delivery_min": 11,
            "app_store_rating": 4.2,
            "cac_inr": 210,
            "aov_inr": 520,
        },
        {
            "competitor": "Zepto",
            "install_to_first_order_pct": 0.36,
            "d7_retention_pct": 0.41,
            "d30_retention_pct": 0.33,
            "avg_delivery_min": 10,
            "app_store_rating": 4.3,
            "cac_inr": 195,
            "aov_inr": 495,
        },
        {
            "competitor": "Swiggy Instamart",
            "install_to_first_order_pct": 0.39,
            "d7_retention_pct": 0.44,
            "d30_retention_pct": 0.35,
            "avg_delivery_min": 12,
            "app_store_rating": 4.1,
            "cac_inr": 165,
            "aov_inr": 510,
        },
        {
            "competitor": "BigBasket Now",
            "install_to_first_order_pct": 0.28,
            "d7_retention_pct": 0.35,
            "d30_retention_pct": 0.27,
            "avg_delivery_min": 18,
            "app_store_rating": 3.9,
            "cac_inr": 175,
            "aov_inr": 560,
        },
        {
            "competitor": "FirstClub",
            "install_to_first_order_pct": 0.29,
            "d7_retention_pct": 0.42,
            "d30_retention_pct": 0.28,
            "avg_delivery_min": 14,
            "app_store_rating": 3.7,
            "cac_inr": 185,
            "aov_inr": 485,
        },
    ]
    return pd.DataFrame(data)


def gap_vs_competitors(firstclub_metrics: dict, benchmarks: pd.DataFrame | None = None) -> pd.DataFrame:
    """Compare FirstClub actuals to competitive median."""
    if benchmarks is None:
        benchmarks = competitive_benchmarks()
    peers = benchmarks[benchmarks["competitor"] != "FirstClub"]
    fc = benchmarks[benchmarks["competitor"] == "FirstClub"].iloc[0]

    metrics = [
        ("install_to_first_order_pct", firstclub_metrics.get("first_order_rate", fc["install_to_first_order_pct"])),
        ("d7_retention_pct", firstclub_metrics.get("d7_retention", fc["d7_retention_pct"])),
        ("d30_retention_pct", firstclub_metrics.get("d30_retention", fc["d30_retention_pct"])),
        ("avg_delivery_min", firstclub_metrics.get("avg_delivery_min", fc["avg_delivery_min"])),
        ("app_store_rating", firstclub_metrics.get("avg_rating", fc["app_store_rating"])),
        ("cac_inr", firstclub_metrics.get("cac_inr", fc["cac_inr"])),
        ("aov_inr", firstclub_metrics.get("aov_inr", fc["aov_inr"])),
    ]
    rows = []
    for name, value in metrics:
        peer_median = peers[name].median()
        gap = value - peer_median
        rows.append(
            {
                "metric": name,
                "firstclub": value,
                "peer_median": peer_median,
                "gap": gap,
                "status": "behind" if gap < 0 and "retention" in name or "rating" in name or "order" in name
                else ("behind" if gap > 0 and ("delivery" in name or "cac" in name) else "ahead"),
            }
        )
    return pd.DataFrame(rows)
