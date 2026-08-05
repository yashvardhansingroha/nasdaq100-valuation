"""Tests for DCF valuation model."""

from __future__ import annotations

import pytest

from utils.models import CompanyFinancials
from valuation.dcf_model import run_dcf


@pytest.fixture
def healthy_financials() -> CompanyFinancials:
    return CompanyFinancials(
        ticker="AAPL",
        revenue=400e9,
        fcf=100e9,
        debt=100e9,
        cash=50e9,
        shares_outstanding=15e9,
        ebitda=130e9,
        net_income=95e9,
        sector="Technology",
        fcf_history=[60e9, 75e9, 85e9, 95e9, 100e9],
        revenue_history=[280e9, 320e9, 360e9, 380e9, 400e9],
    )


@pytest.fixture
def negative_fcf_financials() -> CompanyFinancials:
    return CompanyFinancials(
        ticker="LOSS",
        fcf=-5e9,
        shares_outstanding=1e9,
        debt=0,
        cash=10e9,
    )


@pytest.fixture
def missing_shares_financials() -> CompanyFinancials:
    return CompanyFinancials(
        ticker="NOSH",
        fcf=1e9,
        shares_outstanding=None,
    )


def test_dcf_positive_fcf(healthy_financials: CompanyFinancials) -> None:
    result = run_dcf(healthy_financials)
    assert result.status == "success"
    assert result.value is not None
    assert result.value > 0
    assert result.bear_value is not None
    assert result.base_value is not None
    assert result.bull_value is not None
    assert result.bear_value < result.base_value < result.bull_value


def test_dcf_negative_fcf(negative_fcf_financials: CompanyFinancials) -> None:
    result = run_dcf(negative_fcf_financials)
    assert result.value is None
    assert result.status == "negative_fcf"


def test_dcf_missing_shares(missing_shares_financials: CompanyFinancials) -> None:
    result = run_dcf(missing_shares_financials)
    assert result.value is None
    assert result.status == "missing_shares"


def test_dcf_missing_fcf() -> None:
    fin = CompanyFinancials(ticker="X", fcf=None, shares_outstanding=1e9)
    result = run_dcf(fin)
    assert result.value is None
    assert result.status == "missing_fcf"
