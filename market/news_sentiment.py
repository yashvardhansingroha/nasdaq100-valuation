"""Deterministic news sentiment in [-1.0, +1.0] — offline, no live API.

The same (ticker, date) input always yields the same score: headlines are
drawn from a fixed template corpus by a seed derived from the input itself,
then scored with a keyword polarity function.
"""

from __future__ import annotations

import random
import re
from datetime import date
from typing import Optional

POSITIVE = {"beat", "surge", "growth", "upgrade", "bullish", "record", "profit", "gain", "strong", "expand"}
NEGATIVE = {"miss", "decline", "loss", "downgrade", "bearish", "cut", "weak", "fall", "lawsuit", "recall", "halt"}

TEMPLATES = (
    "{t} beats estimates as profit growth accelerates",
    "Analysts upgrade {t} after a record quarter",
    "{t} guidance points to strong gains ahead",
    "Institutional buyers add {t} on bullish momentum",
    "{t} shares fall after a weak outlook cut",
    "Regulators weigh a lawsuit against {t}",
    "{t} slips as bearish notes pile up",
    "{t} holds steady in a mixed quarter",
    "{t} revenue decline sparks downgrade talk",
    "{t} expands margins, surprising on the upside",
)


def _simple_polarity(text: str) -> float:
    """Keyword polarity in [-1.0, +1.0]; 0.0 when no sentiment words are present."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    pos, neg = len(words & POSITIVE), len(words & NEGATIVE)
    return (pos - neg) / (pos + neg) if pos + neg else 0.0


def news_headlines(ticker: str, as_of: date, count: int = 6) -> list[str]:
    """Deterministic headline corpus for one ticker-day."""
    rng = random.Random(f"news|{ticker}|{as_of}")
    picks = rng.choices(sorted(TEMPLATES), k=count)
    return [tpl.format(t=ticker) for tpl in picks]


def get_news_sentiment(ticker: str, as_of_date: Optional[date] = None) -> Optional[float]:
    """Mean headline polarity in [-1.0, +1.0]. Same input -> same score, always."""
    as_of = as_of_date or date.today()
    scores = [_simple_polarity(h) for h in news_headlines(ticker, as_of)]
    return round(sum(scores) / len(scores), 4)
