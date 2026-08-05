"""Tests for relative multiples valuation."""

from __future__ import annotations

import pytest

from utils.models import CompanyFinancials
from valuation.multiples_model import compute_sector_medians, run_multiples


@pytest.fixture
def financials_map() -> dict[str, CompanyFinancials]:
    return {
        "AAPL": CompanyFinancials(
            ticker="AAPL",
            revenue=400e9,
            net_income=95e9,
            ebitda=130e9,
            shares_outstanding=15e9,
            price=180.0,
            market_cap=2700e9,
            debt=100e9,
            cash=50e9,
            sector="Technology",
        ),
        "MSFT": CompanyFinancials(
            ticker="MSFT",
            revenue=200e9,
            net_income=70e9,
            ebitda=90e9,
            shares_outstanding=7.5e9,
            price=400.0,
            market_cap=3000e9,
            debt=80e9,
            cash=100e9,
            sector="Technology",
        ),
        "BAD": CompanyFinancials(
            ticker="BAD",
            revenue=-1e9,
            net_income=-5e9,
            ebitda=-2e9,
            shares_outstanding=1e9,
            price=10.0,
            market_cap=10e9,
            sector="Technology",
        ),
    }


def test_sector_medians_ignore_invalid(financials_map: dict) -> None:
    medians = compute_sector_medians(financials_map)
    assert "Technology" in medians
    assert medians["Technology"]["pe"] > 0
    assert "_global" in medians


def test_multiples_valid_company(financials_map: dict) -> None:
    medians = compute_sector_medians(financials_map)
    value, status = run_multiples(financials_map["AAPL"], medians)
    assert status == "success"
    assert value is not None
    assert value > 0


def test_multiples_invalid_company(financials_map: dict) -> None:
    medians = compute_sector_medians(financials_map)
    value, status = run_multiples(financials_map["BAD"], medians)
    assert value is None
    assert status == "insufficient_multiples"
