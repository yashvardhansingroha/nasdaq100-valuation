"""Orchestrates market sentiment collection — isolated from valuation."""

from __future__ import annotations

import time
from datetime import date
from typing import Optional

import pandas as pd

import config
from market.analyst_sentiment import get_analyst_sentiment
from market.institutional_sentiment import get_institutional_sentiment
from market.news_sentiment import get_news_sentiment
from market.options_sentiment import get_options_sentiment
from utils.logging_config import setup_logging
from utils.models import SentimentResult

logger = setup_logging(__name__)


def _sentiment_label(score: float) -> str:
    """Convert numeric score to Bullish/Neutral/Bearish label."""
    if score >= 60:
        return "Bullish"
    if score <= 40:
        return "Bearish"
    return "Neutral"


def _weighted_overall(scores: dict[str, Optional[float]]) -> float:
    """Compute weighted overall sentiment from sub-scores."""
    total_weight = 0.0
    weighted_sum = 0.0
    for key, weight in config.SENTIMENT_WEIGHTS.items():
        score = scores.get(key)
        if score is not None:
            weighted_sum += score * weight
            total_weight += weight
    if total_weight == 0:
        return 50.0
    return weighted_sum / total_weight


class SentimentEngine:
    """
    Collects market opinion signals.

    IMPORTANT: This engine NEVER feeds into intrinsic value calculations.
    """

    def run_sentiment(
        self,
        tickers: list[str],
        as_of_date: Optional[date] = None,
    ) -> list[SentimentResult]:
        """Run sentiment analysis for all tickers."""
        as_of_date = as_of_date or date.today()
        start = time.time()
        results: list[SentimentResult] = []

        for i, ticker in enumerate(tickers):
            analyst = get_analyst_sentiment(ticker)
            news = get_news_sentiment(ticker)
            options = get_options_sentiment(ticker)
            institutional = get_institutional_sentiment(ticker)

            scores = {
                "analyst": analyst,
                "news": news,
                "options": options,
                "institutional": institutional,
            }
            overall = _weighted_overall(scores)

            results.append(
                SentimentResult(
                    ticker=ticker,
                    date=as_of_date,
                    analyst_score=analyst,
                    news_score=news,
                    options_score=options,
                    institutional_score=institutional,
                    overall_sentiment=round(overall, 1),
                    sentiment_label=_sentiment_label(overall),
                )
            )

            if (i + 1) % 20 == 0:
                logger.info("Sentiment progress: %d / %d", i + 1, len(tickers))
                time.sleep(0.3)

        logger.info("Sentiment complete for %d tickers in %.1fs", len(tickers), time.time() - start)
        return results

    def results_to_dataframe(self, results: list[SentimentResult]) -> pd.DataFrame:
        """Convert sentiment results to DataFrame."""
        return pd.DataFrame(
            [
                {
                    "ticker": r.ticker,
                    "date": r.date,
                    "analyst_score": r.analyst_score,
                    "news_score": r.news_score,
                    "options_score": r.options_score,
                    "institutional_score": r.institutional_score,
                    "overall_sentiment": r.overall_sentiment,
                    "sentiment_label": r.sentiment_label,
                }
                for r in results
            ]
        )
