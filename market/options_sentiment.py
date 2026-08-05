"""Options market sentiment — separate from intrinsic value."""

from __future__ import annotations

from typing import Optional

import yfinance as yf

import config
from utils.logging_config import setup_logging

logger = setup_logging(__name__)


def get_options_sentiment(ticker: str) -> Optional[float]:
    """
    Estimate options sentiment from put/call volume ratio.

    Lower put/call ratio = more bullish (higher score).
    Does NOT affect intrinsic value calculations.
    """
    if not config.ENABLE_OPTIONS_SENTIMENT:
        return None

    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options
        if not expirations:
            return 50.0

        chain = stock.option_chain(expirations[0])
        calls = chain.calls
        puts = chain.puts

        call_volume = calls["volume"].sum() if "volume" in calls.columns else 0
        put_volume = puts["volume"].sum() if "volume" in puts.columns else 0

        if call_volume == 0 and put_volume == 0:
            return 50.0

        if call_volume == 0:
            return 20.0

        pc_ratio = put_volume / call_volume
        if pc_ratio <= 0.5:
            return 80.0
        if pc_ratio <= 0.8:
            return 65.0
        if pc_ratio <= 1.0:
            return 50.0
        if pc_ratio <= 1.5:
            return 35.0
        return 20.0

    except Exception as exc:
        logger.warning("Options sentiment failed for %s: %s", ticker, exc)
        return 50.0
