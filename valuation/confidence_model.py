"""Confidence scoring for valuation results."""

from __future__ import annotations

from typing import Optional

import numpy as np

import config
from utils.logging_config import setup_logging
from utils.models import CompanyFinancials

logger = setup_logging(__name__)


def _coefficient_of_variation(values: list[float]) -> float:
    """Return coefficient of variation; lower is more stable."""
    if len(values) < 2:
        return 1.0
    arr = np.array(values, dtype=float)
    mean = np.mean(arr)
    if mean == 0:
        return 1.0
    return float(np.std(arr) / abs(mean))


def _agreement_score(dcf: Optional[float], multiples: Optional[float]) -> float:
    """Score agreement between DCF and multiples (0-100)."""
    if dcf is None or multiples is None or dcf <= 0 or multiples <= 0:
        return 30.0
    diff_pct = abs(dcf - multiples) / ((dcf + multiples) / 2)
    if diff_pct <= 0.10:
        return 100.0
    if diff_pct <= 0.20:
        return 80.0
    if diff_pct <= 0.35:
        return 50.0
    return 20.0


def _completeness_score(financials: CompanyFinancials) -> float:
    """Score data availability (0-100)."""
    fields = [
        financials.revenue,
        financials.fcf,
        financials.shares_outstanding,
        financials.net_income,
        financials.ebitda,
        financials.debt,
        financials.cash,
    ]
    available = sum(1 for f in fields if f is not None)
    return (available / len(fields)) * 100


def _positive_fcf_score(fcf: Optional[float]) -> float:
    """Score based on positive free cash flow."""
    if fcf is None:
        return 20.0
    return 100.0 if fcf > 0 else 10.0


def _stability_score(values: list[float]) -> float:
    """Score earnings/revenue stability (0-100)."""
    if len(values) < 2:
        return 40.0
    cv = _coefficient_of_variation(values)
    if cv <= 0.15:
        return 100.0
    if cv <= 0.30:
        return 75.0
    if cv <= 0.50:
        return 50.0
    return 25.0


def compute_confidence(
    financials: CompanyFinancials,
    dcf_value: Optional[float],
    multiples_value: Optional[float],
) -> tuple[float, str]:
    """
    Calculate confidence score (0-100) and label (High/Medium/Low).
    """
    weights = {
        "agreement": 0.25,
        "completeness": 0.25,
        "positive_fcf": 0.15,
        "earnings_stability": 0.20,
        "revenue_consistency": 0.15,
    }

    scores = {
        "agreement": _agreement_score(dcf_value, multiples_value),
        "completeness": _completeness_score(financials),
        "positive_fcf": _positive_fcf_score(financials.fcf),
        "earnings_stability": _stability_score(financials.earnings_history),
        "revenue_consistency": _stability_score(financials.revenue_history),
    }

    total = sum(scores[k] * weights[k] for k in weights)
    total = max(0.0, min(100.0, total))

    if total >= config.CONFIDENCE_HIGH:
        label = "High"
    elif total >= config.CONFIDENCE_MEDIUM:
        label = "Medium"
    else:
        label = "Low"

    return round(total, 1), label
