"""Relative valuation using sector median multiples."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from utils.logging_config import setup_logging
from utils.models import CompanyFinancials

logger = setup_logging(__name__)


def _valid_median(values: list[float]) -> Optional[float]:
    """Compute median ignoring invalid values."""
    clean = [v for v in values if v is not None and v > 0 and not np.isnan(v) and not np.isinf(v)]
    if not clean:
        return None
    return float(np.median(clean))


def compute_sector_medians(financials_map: dict[str, CompanyFinancials]) -> dict[str, dict[str, float]]:
    """
    Compute sector median P/E, EV/EBITDA, and P/S multiples.

    Returns {sector: {pe, ev_ebitda, ps}}.
    """
    records: list[dict] = []
    for fin in financials_map.values():
        price = fin.price
        if not price or price <= 0:
            continue

        pe = None
        if fin.net_income and fin.net_income > 0 and fin.shares_outstanding:
            eps = fin.net_income / fin.shares_outstanding
            if eps > 0:
                pe = price / eps

        ev_ebitda = None
        if fin.ebitda and fin.ebitda > 0 and fin.market_cap:
            debt = fin.debt or 0
            cash = fin.cash or 0
            ev = fin.market_cap + debt - cash
            if ev > 0:
                ev_ebitda = ev / fin.ebitda

        ps = None
        if fin.revenue and fin.revenue > 0 and fin.shares_outstanding:
            sps = fin.revenue / fin.shares_outstanding
            if sps > 0:
                ps = price / sps

        records.append(
            {
                "sector": fin.sector or "Unknown",
                "pe": pe,
                "ev_ebitda": ev_ebitda,
                "ps": ps,
            }
        )

    if not records:
        return {}

    df = pd.DataFrame(records)
    medians: dict[str, dict[str, float]] = {}
    for sector, group in df.groupby("sector"):
        medians[str(sector)] = {
            "pe": _valid_median(group["pe"].tolist()) or 0,
            "ev_ebitda": _valid_median(group["ev_ebitda"].tolist()) or 0,
            "ps": _valid_median(group["ps"].tolist()) or 0,
        }

    global_medians = {
        "pe": _valid_median(df["pe"].tolist()) or 0,
        "ev_ebitda": _valid_median(df["ev_ebitda"].tolist()) or 0,
        "ps": _valid_median(df["ps"].tolist()) or 0,
    }
    medians["_global"] = global_medians
    return medians


def run_multiples(
    financials: CompanyFinancials,
    sector_medians: dict[str, dict[str, float]],
) -> tuple[Optional[float], str]:
    """
    Apply sector median multiples to company fundamentals.

    Returns (implied_price, status).
    """
    sector = financials.sector or "Unknown"
    medians = sector_medians.get(sector) or sector_medians.get("_global")
    if not medians:
        return None, "no_sector_medians"

    implied_values: list[float] = []
    shares = financials.shares_outstanding

    if shares and shares > 0:
        if medians.get("pe", 0) > 0 and financials.net_income and financials.net_income > 0:
            eps = financials.net_income / shares
            implied_values.append(medians["pe"] * eps)

        if medians.get("ps", 0) > 0 and financials.revenue and financials.revenue > 0:
            sps = financials.revenue / shares
            implied_values.append(medians["ps"] * sps)

    if medians.get("ev_ebitda", 0) > 0 and financials.ebitda and financials.ebitda > 0 and shares and shares > 0:
        debt = financials.debt or 0
        cash = financials.cash or 0
        implied_ev = medians["ev_ebitda"] * financials.ebitda
        implied_equity = implied_ev - debt + cash
        implied_values.append(implied_equity / shares)

    if not implied_values:
        return None, "insufficient_multiples"

    return float(np.mean(implied_values)), "success"
