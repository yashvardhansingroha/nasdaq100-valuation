"""Aggregate company valuations into index-level intrinsic value."""

from __future__ import annotations

from datetime import date
from typing import Optional

import config
from utils.data_provider import get_default_provider
from utils.logging_config import setup_logging
from utils.models import IndexSnapshot, ValuationResult

logger = setup_logging(__name__)


def _aggregate_scenario(
    results: list[ValuationResult],
    index_price: float,
    blended_field: str,
) -> tuple[float, float]:
    """Compute weighted intrinsic value and fair-value ratio for one scenario."""
    valued = [
        r
        for r in results
        if getattr(r, blended_field) is not None and r.price and r.price > 0
    ]
    intrinsic = 0.0
    for r in valued:
        blended = getattr(r, blended_field)
        ratio = blended / r.price  # type: ignore[operator]
        intrinsic += r.index_weight * ratio * index_price

    ratio = intrinsic / index_price if index_price > 0 and valued else 0.0
    return intrinsic, ratio


def aggregate_index_value(
    results: list[ValuationResult],
    as_of_date: Optional[date] = None,
    index_price: Optional[float] = None,
) -> IndexSnapshot:
    """
    Compute weighted index intrinsic value from company valuations.

    Produces bear/base/bull index ranges alongside the primary blended value.
    """
    as_of_date = as_of_date or date.today()

    if index_price is None:
        provider = get_default_provider()
        index_price = provider.get_index_price()
    if index_price is None or index_price <= 0:
        logger.warning("Index price unavailable; using sum of weighted intrinsic values")
        index_price = 1.0

    total_mcap = sum(r.market_cap for r in results)
    valued = [r for r in results if r.blended_value is not None and r.price and r.price > 0]
    coverage = len(valued) / len(results) if results else 0.0

    intrinsic, fair_value_ratio = _aggregate_scenario(results, index_price, "blended_value")
    intrinsic_bear, ratio_bear = _aggregate_scenario(results, index_price, "blended_bear_value")
    intrinsic_base, ratio_base = _aggregate_scenario(results, index_price, "blended_base_value")
    intrinsic_bull, ratio_bull = _aggregate_scenario(results, index_price, "blended_bull_value")

    snapshot = IndexSnapshot(
        date=as_of_date,
        index_price=index_price,
        intrinsic_value=intrinsic,
        fair_value_ratio=fair_value_ratio,
        coverage=coverage,
        total_market_cap=total_mcap,
        intrinsic_value_bear=intrinsic_bear,
        intrinsic_value_base=intrinsic_base,
        intrinsic_value_bull=intrinsic_bull,
        fair_value_ratio_bear=ratio_bear,
        fair_value_ratio_base=ratio_base,
        fair_value_ratio_bull=ratio_bull,
    )

    logger.info(
        "Index aggregation: price=%.2f intrinsic=%.2f (bear=%.2f base=%.2f bull=%.2f) "
        "ratio=%.3f coverage=%.1f%%",
        snapshot.index_price,
        snapshot.intrinsic_value,
        snapshot.intrinsic_value_bear,
        snapshot.intrinsic_value_base,
        snapshot.intrinsic_value_bull,
        snapshot.fair_value_ratio,
        snapshot.coverage * 100,
    )
    return snapshot
