"""Deterministic, offline sentiment engine — all scores in [-1.0, +1.0].

Every pillar score is a pure function of (pillar, ticker, date): a stable
per-ticker bias plus a small date-seeded drift, so the same input always
yields the same score with no live-API calls or randomness.
"""

from __future__ import annotations

import random
from datetime import date
from typing import Optional

import pandas as pd

import config
from market.news_sentiment import get_news_sentiment
from utils.models import SentimentResult

MARKET_PILLARS = ("analyst", "options", "institutional")


def _pillar_score(pillar: str, ticker: str, as_of: date) -> float:
    """Deterministic pillar score in [-1, 1]: per-ticker bias + small daily drift."""
    bias = random.Random(f"{pillar}|{ticker}").uniform(-0.6, 0.6)
    drift = random.Random(f"{pillar}|{ticker}|{as_of}").uniform(-0.25, 0.25)
    return round(max(-1.0, min(1.0, bias + drift)), 4)


def _weighted_overall(scores: dict[str, Optional[float]]) -> float:
    """Config-weighted mean of available pillar scores, in [-1, 1]."""
    pairs = [(config.SENTIMENT_WEIGHTS[k], s) for k, s in scores.items() if s is not None]
    total_weight = sum(w for w, _ in pairs)
    if not pairs or total_weight == 0:
        return 0.0
    return sum(w * s for w, s in pairs) / total_weight


def _sentiment_label(score: float) -> str:
    """Bullish/Neutral/Bearish label on the [-1, 1] scale."""
    if score >= 0.15:
        return "Bullish"
    if score <= -0.15:
        return "Bearish"
    return "Neutral"


def deterministic_scores(ticker: str, as_of: Optional[date] = None) -> dict:
    """All four pillar scores plus weighted overall, all in [-1, +1]. Pure function."""
    as_of = as_of or date.today()
    scores = {p: _pillar_score(p, ticker, as_of) for p in MARKET_PILLARS}
    scores["news"] = get_news_sentiment(ticker, as_of)
    overall = _weighted_overall(scores)
    return {
        "analyst": scores["analyst"],
        "news": scores["news"],
        "options": scores["options"],
        "institutional": scores["institutional"],
        "overall": round(overall, 4),
        "label": _sentiment_label(overall),
    }


class SentimentEngine:
    """Collects market opinion signals.

    IMPORTANT: This engine NEVER feeds into intrinsic value calculations.
    """

    def run_sentiment(
        self,
        tickers: list[str],
        as_of_date: Optional[date] = None,
    ) -> list[SentimentResult]:
        """Run deterministic sentiment analysis for all tickers."""
        as_of = as_of_date or date.today()
        results = []
        for ticker in tickers:
            s = deterministic_scores(ticker, as_of)
            results.append(
                SentimentResult(
                    ticker=ticker,
                    date=as_of,
                    analyst_score=s["analyst"],
                    news_score=s["news"],
                    options_score=s["options"],
                    institutional_score=s["institutional"],
                    overall_sentiment=s["overall"],
                    sentiment_label=s["label"],
                )
            )
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
