"""Tests for database repository."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pytest

from database.database import HistoryRepository
from utils.models import IndexSnapshot, SentimentResult, ValuationResult


@pytest.fixture
def repo() -> HistoryRepository:
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    return HistoryRepository(db_path=tmp.name)


@pytest.fixture
def sample_valuation() -> ValuationResult:
    return ValuationResult(
        ticker="TEST",
        price=100.0,
        dcf_value=110.0,
        multiples_value=105.0,
        blended_value=107.5,
        upside=0.075,
        valuation_method="blended",
        confidence_score=75.0,
        confidence_label="High",
        status="success",
        sector="Technology",
        market_cap=1e12,
        index_weight=0.05,
    )


def test_save_and_retrieve_company_values(repo: HistoryRepository, sample_valuation: ValuationResult) -> None:
    as_of = date(2026, 1, 15)
    inserted = repo.save_company_values(as_of, [sample_valuation])
    assert inserted == 1

    df = repo.get_company_values_by_date(as_of)
    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "TEST"
    assert df.iloc[0]["blended_value"] == 107.5


def test_append_only_no_duplicate(repo: HistoryRepository, sample_valuation: ValuationResult) -> None:
    as_of = date(2026, 1, 15)
    repo.save_company_values(as_of, [sample_valuation])
    inserted = repo.save_company_values(as_of, [sample_valuation])
    assert inserted == 0

    df = repo.get_company_values_by_date(as_of)
    assert len(df) == 1


def test_save_index_snapshot(repo: HistoryRepository) -> None:
    snapshot = IndexSnapshot(
        date=date(2026, 1, 15),
        index_price=15000.0,
        intrinsic_value=14500.0,
        fair_value_ratio=0.967,
        coverage=0.95,
        total_market_cap=20e12,
        intrinsic_value_bear=14000.0,
        intrinsic_value_base=14500.0,
        intrinsic_value_bull=15000.0,
        fair_value_ratio_bear=0.933,
        fair_value_ratio_base=0.967,
        fair_value_ratio_bull=1.0,
    )
    assert repo.save_index_snapshot(snapshot) is True
    assert repo.save_index_snapshot(snapshot) is False

    latest = repo.get_latest_date()
    assert latest == date(2026, 1, 15)


def test_save_sentiment(repo: HistoryRepository) -> None:
    result = SentimentResult(
        ticker="TEST",
        date=date(2026, 1, 15),
        analyst_score=70.0,
        news_score=55.0,
        options_score=60.0,
        institutional_score=65.0,
        overall_sentiment=62.5,
        sentiment_label="Bullish",
    )
    inserted = repo.save_sentiment([result])
    assert inserted == 1

    df = repo.get_sentiment_by_date(date(2026, 1, 15))
    assert len(df) == 1
