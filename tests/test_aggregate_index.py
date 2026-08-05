"""Tests for index aggregation."""

from __future__ import annotations

from datetime import date

import pytest

from index.aggregate_index_value import aggregate_index_value
from utils.models import ValuationResult


@pytest.fixture
def sample_results() -> list[ValuationResult]:
    return [
        ValuationResult(
            ticker="A",
            price=100.0,
            dcf_value=120.0,
            multiples_value=110.0,
            blended_value=115.0,
            upside=0.15,
            valuation_method="blended",
            confidence_score=80.0,
            confidence_label="High",
            status="success",
            sector="Tech",
            market_cap=1000e9,
            index_weight=0.6,
            blended_bear_value=105.0,
            blended_base_value=115.0,
            blended_bull_value=125.0,
        ),
        ValuationResult(
            ticker="B",
            price=50.0,
            dcf_value=40.0,
            multiples_value=45.0,
            blended_value=42.5,
            upside=-0.15,
            valuation_method="blended",
            confidence_score=70.0,
            confidence_label="High",
            status="success",
            sector="Tech",
            market_cap=500e9,
            index_weight=0.4,
            blended_bear_value=38.0,
            blended_base_value=42.5,
            blended_bull_value=47.0,
        ),
        ValuationResult(
            ticker="C",
            price=30.0,
            dcf_value=None,
            multiples_value=None,
            blended_value=None,
            upside=None,
            valuation_method="failed",
            confidence_score=20.0,
            confidence_label="Low",
            status="missing_data",
            sector="Health",
            market_cap=100e9,
            index_weight=0.0,
        ),
    ]


def test_aggregate_index_value(sample_results: list[ValuationResult]) -> None:
    snapshot = aggregate_index_value(sample_results, date(2026, 1, 1), index_price=15000.0)
    assert snapshot.index_price == 15000.0
    assert snapshot.intrinsic_value > 0
    assert snapshot.intrinsic_value_bear > 0
    assert snapshot.intrinsic_value_base > 0
    assert snapshot.intrinsic_value_bull > 0
    assert snapshot.intrinsic_value_bear < snapshot.intrinsic_value_base < snapshot.intrinsic_value_bull
    assert snapshot.coverage == pytest.approx(2 / 3)
    assert snapshot.fair_value_ratio == pytest.approx(snapshot.intrinsic_value / 15000.0)


def test_aggregate_empty() -> None:
    snapshot = aggregate_index_value([], date.today(), index_price=100.0)
    assert snapshot.intrinsic_value == 0.0
    assert snapshot.coverage == 0.0
