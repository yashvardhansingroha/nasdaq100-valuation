"""Analyst rating sentiment — separate from intrinsic value."""

from __future__ import annotations

from typing import Optional

import requests
import yfinance as yf

import config
from utils.logging_config import setup_logging

logger = setup_logging(__name__)


def _score_from_recommendations(rec_map: dict[str, int]) -> float:
    """Convert recommendation counts to 0-100 score."""
    if not rec_map:
        return 50.0
    weights = {
        "strongBuy": 100,
        "buy": 80,
        "hold": 50,
        "sell": 20,
        "strongSell": 0,
    }
    total = sum(rec_map.values())
    if total == 0:
        return 50.0
    score = sum(weights.get(k, 50) * v for k, v in rec_map.items()) / total
    return max(0.0, min(100.0, score))


def _fetch_fmp_analyst(ticker: str) -> Optional[float]:
    """Fetch analyst consensus from FMP if API key available."""
    if not config.FMP_API_KEY:
        return None
    try:
        url = f"https://financialmodelingprep.com/api/v3/analyst-stock-recommendations/{ticker}"
        resp = requests.get(url, params={"apikey": config.FMP_API_KEY}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        latest = data[0]
        strong_buy = latest.get("analystRatingsStrongBuy", 0)
        buy = latest.get("analystRatingsbuy", 0) + latest.get("analystRatingsBuy", 0)
        hold = latest.get("analystRatingsHold", 0)
        sell = latest.get("analystRatingsSell", 0)
        strong_sell = latest.get("analystRatingsStrongSell", 0)
        rec_map = {
            "strongBuy": strong_buy,
            "buy": buy,
            "hold": hold,
            "sell": sell,
            "strongSell": strong_sell,
        }
        return _score_from_recommendations(rec_map)
    except Exception as exc:
        logger.warning("FMP analyst fetch failed for %s: %s", ticker, exc)
        return None


def get_analyst_sentiment(ticker: str) -> Optional[float]:
    """
    Return analyst sentiment score 0-100.

    Does NOT affect intrinsic value calculations.
    """
    if not config.ENABLE_ANALYST_SENTIMENT:
        return None

    fmp_score = _fetch_fmp_analyst(ticker)
    if fmp_score is not None:
        return fmp_score

    try:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations
        if recs is not None and not recs.empty:
            latest = recs.iloc[-1]
            rec_map = {}
            for col in recs.columns:
                val = latest.get(col, 0)
                if val and val > 0:
                    rec_map[str(col)] = int(val)
            if rec_map:
                return _score_from_recommendations(rec_map)

        info = stock.info or {}
        target = info.get("targetMeanPrice")
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if target and price and price > 0:
            upside = (target - price) / price
            score = 50 + upside * 100
            return max(0.0, min(100.0, score))

    except Exception as exc:
        logger.warning("Analyst sentiment failed for %s: %s", ticker, exc)

    return 50.0
