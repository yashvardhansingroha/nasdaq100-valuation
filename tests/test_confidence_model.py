"""Tests for confidence model."""

from __future__ import annotations

from utils.models import CompanyFinancials
from valuation.confidence_model import compute_confidence


def test_high_confidence() -> None:
    fin = CompanyFinancials(
        ticker="GOOD",
        revenue=100e9,
        fcf=20e9,
        debt=10e9,
        cash=5e9,
        shares_outstanding=1e9,
        net_income=15e9,
        ebitda=25e9,
        fcf_history=[10e9, 12e9, 15e9, 18e9, 20e9],
        earnings_history=[8e9, 10e9, 12e9, 14e9, 15e9],
        revenue_history=[60e9, 70e9, 80e9, 90e9, 100e9],
    )
    score, label = compute_confidence(fin, 120.0, 115.0)
    assert 0 <= score <= 100
    assert label in ("High", "Medium", "Low")
    assert score >= 60


def test_low_confidence_missing_data() -> None:
    fin = CompanyFinancials(ticker="BAD")
    score, label = compute_confidence(fin, None, None)
    assert score < 70
    assert label in ("High", "Medium", "Low")


def test_score_bounds() -> None:
    fin = CompanyFinancials(
        ticker="X",
        revenue=1e9,
        fcf=0.1e9,
        shares_outstanding=1e9,
        net_income=0.05e9,
        ebitda=0.2e9,
    )
    score, _ = compute_confidence(fin, 50.0, 200.0)
    assert 0 <= score <= 100
