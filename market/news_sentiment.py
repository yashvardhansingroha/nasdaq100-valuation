"""News sentiment analysis — separate from intrinsic value."""

from __future__ import annotations

from typing import Optional

import requests

import config
from utils.logging_config import setup_logging

logger = setup_logging(__name__)


def _simple_polarity(text: str) -> float:
    """Basic keyword-based sentiment scoring (0-100)."""
    positive = {"beat", "surge", "growth", "upgrade", "bullish", "record", "profit", "gain", "strong"}
    negative = {"miss", "decline", "loss", "downgrade", "bearish", "cut", "weak", "fall", "lawsuit", "recall"}
    words = set(text.lower().split())
    pos = len(words & positive)
    neg = len(words & negative)
    if pos + neg == 0:
        return 50.0
    score = 50 + (pos - neg) / (pos + neg) * 50
    return max(0.0, min(100.0, score))


def get_news_sentiment(ticker: str) -> Optional[float]:
    """
    Return news sentiment score 0-100 from NewsAPI.

    Does NOT affect intrinsic value calculations.
    """
    if not config.ENABLE_NEWS_SENTIMENT or not config.NEWSAPI_KEY:
        return None

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": ticker,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 10,
            "apiKey": config.NEWSAPI_KEY,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        if not articles:
            return 50.0

        scores = []
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            scores.append(_simple_polarity(text))

        return sum(scores) / len(scores)

    except Exception as exc:
        logger.warning("News sentiment failed for %s: %s", ticker, exc)
        return None
