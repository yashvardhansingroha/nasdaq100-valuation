"""Institutional holdings sentiment — separate from intrinsic value."""

from __future__ import annotations

from typing import Optional

import yfinance as yf

import config
from utils.logging_config import setup_logging

logger = setup_logging(__name__)


def get_institutional_sentiment(ticker: str) -> Optional[float]:
    """
    Estimate institutional sentiment from holder concentration trends.

    Does NOT affect intrinsic value calculations.
    """
    if not config.ENABLE_INSTITUTIONAL_SENTIMENT:
        return None

    try:
        stock = yf.Ticker(ticker)
        holders = stock.institutional_holders
        if holders is None or holders.empty:
            info = stock.info or {}
            pct = info.get("heldPercentInstitutions")
            if pct is not None:
                score = 50 + (float(pct) - 0.5) * 60
                return max(0.0, min(100.0, score))
            return 50.0

        total_pct = 0.0
        count = 0
        for _, row in holders.iterrows():
            pct_str = str(row.get("pctHeld", ""))
            if pct_str and pct_str != "nan":
                try:
                    total_pct += float(pct_str.replace("%", ""))
                    count += 1
                except ValueError:
                    continue

        if count == 0:
            return 50.0

        avg_pct = total_pct / count
        score = 40 + min(avg_pct, 30) * 2
        return max(0.0, min(100.0, score))

    except Exception as exc:
        logger.warning("Institutional sentiment failed for %s: %s", ticker, exc)
        return 50.0
