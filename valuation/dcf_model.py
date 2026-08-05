"""Discounted Cash Flow valuation model with bear/base/bull scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import config
from utils.logging_config import setup_logging
from utils.models import CompanyFinancials

logger = setup_logging(__name__)


@dataclass
class DcfResult:
    """Scenario DCF output for one company."""

    value: Optional[float]
    bear_value: Optional[float]
    base_value: Optional[float]
    bull_value: Optional[float]
    status: str


def _derive_fcf_growth(financials: CompanyFinancials) -> float:
    """Estimate FCF growth rate from historical data, capped to reasonable bounds."""
    history = financials.fcf_history
    if len(history) >= 2:
        positive = [v for v in history if v > 0]
        if len(positive) >= 2:
            start, end = positive[-1], positive[0]
            years = len(positive) - 1
            if start > 0 and years > 0:
                growth = (end / start) ** (1 / years) - 1
                return max(config.MIN_FCF_GROWTH, min(config.MAX_FCF_GROWTH, growth))

    if financials.revenue and financials.revenue > 0:
        rev_history = financials.revenue_history
        if len(rev_history) >= 2 and rev_history[-1] > 0:
            years = len(rev_history) - 1
            growth = (rev_history[0] / rev_history[-1]) ** (1 / years) - 1
            return max(config.MIN_FCF_GROWTH, min(config.MAX_FCF_GROWTH, growth))

    return 0.05


def _run_dcf_core(
    financials: CompanyFinancials,
    growth_adjustment: float = 0.0,
    discount_adjustment: float = 0.0,
) -> Optional[float]:
    """Run a single-scenario FCF DCF with optional growth and discount adjustments."""
    fcf = financials.fcf
    shares = financials.shares_outstanding

    if fcf is None or shares is None or shares <= 0 or fcf <= 0:
        return None

    growth = _derive_fcf_growth(financials) + growth_adjustment
    growth = max(config.MIN_FCF_GROWTH, min(config.MAX_FCF_GROWTH, growth))
    discount = config.DISCOUNT_RATE + discount_adjustment
    terminal = config.TERMINAL_GROWTH
    years = config.PROJECTION_YEARS

    if discount <= terminal:
        return None

    projected_fcfs: list[float] = []
    current_fcf = fcf
    for _ in range(years):
        current_fcf *= 1 + growth
        projected_fcfs.append(current_fcf)

    pv_fcfs = sum(f / (1 + discount) ** (i + 1) for i, f in enumerate(projected_fcfs))

    terminal_fcf = projected_fcfs[-1] * (1 + terminal)
    terminal_value = terminal_fcf / (discount - terminal)
    pv_terminal = terminal_value / (1 + discount) ** years

    enterprise_value = pv_fcfs + pv_terminal
    debt = financials.debt or 0
    cash = financials.cash or 0
    equity_value = enterprise_value - debt + cash

    if equity_value <= 0:
        return None

    return equity_value / shares


def _weighted_scenario_value(scenario_values: dict[str, Optional[float]]) -> Optional[float]:
    """Probability-weighted average of valid positive scenario values."""
    valid = {
        name: value
        for name, value in scenario_values.items()
        if value is not None and value > 0
    }
    if not valid:
        return None
    total_prob = sum(config.SCENARIO_PROBABILITIES[name] for name in valid)
    return sum(value * config.SCENARIO_PROBABILITIES[name] for name, value in valid.items()) / total_prob


def run_dcf(financials: CompanyFinancials) -> DcfResult:
    """
    Run bear/base/bull scenario DCF and return probability-weighted value.

    Returns DcfResult with per-scenario values and overall status.
    """
    fcf = financials.fcf
    shares = financials.shares_outstanding

    if fcf is None:
        return DcfResult(None, None, None, None, "missing_fcf")
    if shares is None or shares <= 0:
        return DcfResult(None, None, None, None, "missing_shares")
    if fcf <= 0:
        return DcfResult(None, None, None, None, "negative_fcf")

    scenario_values: dict[str, Optional[float]] = {}
    for name, adj in config.SCENARIO_ADJUSTMENTS.items():
        scenario_values[name] = _run_dcf_core(
            financials,
            growth_adjustment=adj["growth"],
            discount_adjustment=adj["discount"],
        )

    bear = scenario_values["bear"]
    base = scenario_values["base"]
    bull = scenario_values["bull"]
    weighted = _weighted_scenario_value(scenario_values)

    if weighted is None:
        return DcfResult(None, bear, base, bull, "negative_equity")

    return DcfResult(weighted, bear, base, bull, "success")
