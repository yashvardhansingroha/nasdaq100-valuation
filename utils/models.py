"""Shared domain dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class CompanyFinancials:
    """Fundamental financial data for a single company."""

    ticker: str
    revenue: Optional[float] = None
    fcf: Optional[float] = None
    debt: Optional[float] = None
    cash: Optional[float] = None
    shares_outstanding: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    sector: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    revenue_history: list[float] = field(default_factory=list)
    earnings_history: list[float] = field(default_factory=list)
    fcf_history: list[float] = field(default_factory=list)


@dataclass
class ConstituentInfo:
    """NASDAQ-100 constituent with index weight."""

    ticker: str
    company_name: str
    price: float
    market_cap: float
    shares_outstanding: float
    index_weight: float
    sector: str
    as_of_date: date


@dataclass
class ValuationResult:
    """Output of the valuation pipeline for one company."""

    ticker: str
    price: float
    dcf_value: Optional[float]
    multiples_value: Optional[float]
    blended_value: Optional[float]
    upside: Optional[float]
    valuation_method: str
    confidence_score: float
    confidence_label: str
    status: str
    sector: str = ""
    market_cap: float = 0.0
    index_weight: float = 0.0
    dcf_bear_value: Optional[float] = None
    dcf_base_value: Optional[float] = None
    dcf_bull_value: Optional[float] = None
    blended_bear_value: Optional[float] = None
    blended_base_value: Optional[float] = None
    blended_bull_value: Optional[float] = None


@dataclass
class IndexSnapshot:
    """Aggregated index-level valuation snapshot."""

    date: date
    index_price: float
    intrinsic_value: float
    fair_value_ratio: float
    coverage: float
    total_market_cap: float
    intrinsic_value_bear: float = 0.0
    intrinsic_value_base: float = 0.0
    intrinsic_value_bull: float = 0.0
    fair_value_ratio_bear: float = 0.0
    fair_value_ratio_base: float = 0.0
    fair_value_ratio_bull: float = 0.0


@dataclass
class SentimentResult:
    """Market sentiment scores — separate from intrinsic value."""

    ticker: str
    date: date
    analyst_score: Optional[float]
    news_score: Optional[float]
    options_score: Optional[float]
    institutional_score: Optional[float]
    overall_sentiment: float
    sentiment_label: str
