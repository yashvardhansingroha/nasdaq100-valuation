"""Fetch NASDAQ-100 constituents and compute index weights."""

from __future__ import annotations

import io
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup

import config
from utils.logging_config import setup_logging
from utils.models import ConstituentInfo

logger = setup_logging(__name__)

WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/Nasdaq-100"


def _fetch_tickers_from_wikipedia() -> list[str]:
    """Scrape NASDAQ-100 tickers from Wikipedia."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; NASDAQ100Valuation/1.0)"}
    response = requests.get(WIKIPEDIA_URL, headers=headers, timeout=30)
    response.raise_for_status()
    tables = pd.read_html(io.StringIO(response.text))
    for table in tables:
        for col in table.columns:
            col_str = str(col).lower()
            if "ticker" in col_str or "symbol" in col_str:
                tickers = table[col].dropna().astype(str).str.strip().tolist()
                tickers = [t.replace(".", "-") for t in tickers if t and t != "nan"]
                if len(tickers) >= 90:
                    return tickers
    raise ValueError("Could not find NASDAQ-100 ticker table on Wikipedia")


def _is_cache_valid(path: Path) -> bool:
    """Return True if cached constituents file is within TTL."""
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age < timedelta(hours=config.CONSTITUENTS_CACHE_HOURS)


def fetch_constituents(force_refresh: bool = False) -> pd.DataFrame:
    """
    Fetch NASDAQ-100 constituents with market caps and index weights.

    Returns DataFrame with columns:
    ticker, company_name, price, market_cap, shares_outstanding,
    index_weight, sector, as_of_date
    """
    cache_path = Path(config.CONSTITUENTS_CSV)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not force_refresh and _is_cache_valid(cache_path):
        logger.info("Loading constituents from cache: %s", cache_path)
        return pd.read_csv(cache_path, parse_dates=["as_of_date"])

    logger.info("Fetching NASDAQ-100 constituents from Wikipedia")
    tickers = _fetch_tickers_from_wikipedia()
    logger.info("Found %d tickers", len(tickers))

    rows: list[dict] = []
    as_of = date.today()

    for i, ticker in enumerate(tickers):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            price = info.get("currentPrice") or info.get("regularMarketPrice") or 0
            market_cap = info.get("marketCap") or 0
            shares = info.get("sharesOutstanding") or 0
            if price and shares and not market_cap:
                market_cap = price * shares

            rows.append(
                {
                    "ticker": ticker.upper(),
                    "company_name": info.get("shortName", ticker),
                    "price": float(price or 0),
                    "market_cap": float(market_cap or 0),
                    "shares_outstanding": float(shares or 0),
                    "sector": info.get("sector", "Unknown") or "Unknown",
                    "as_of_date": as_of,
                }
            )
        except Exception as exc:
            logger.warning("Failed to fetch data for %s: %s", ticker, exc)
            rows.append(
                {
                    "ticker": ticker.upper(),
                    "company_name": ticker,
                    "price": 0.0,
                    "market_cap": 0.0,
                    "shares_outstanding": 0.0,
                    "sector": "Unknown",
                    "as_of_date": as_of,
                }
            )

        if (i + 1) % 20 == 0:
            logger.info("Fetched %d / %d constituents", i + 1, len(tickers))

    df = pd.DataFrame(rows)
    total_mcap = df["market_cap"].sum()
    if total_mcap > 0:
        df["index_weight"] = df["market_cap"] / total_mcap
    else:
        df["index_weight"] = 1.0 / len(df)

    df.to_csv(cache_path, index=False)
    logger.info("Saved constituents to %s (weight sum=%.4f)", cache_path, df["index_weight"].sum())
    return df


def get_constituent_list(force_refresh: bool = False) -> list[ConstituentInfo]:
    """Return constituents as a list of ConstituentInfo dataclass objects."""
    df = fetch_constituents(force_refresh=force_refresh)
    constituents: list[ConstituentInfo] = []
    for _, row in df.iterrows():
        as_of = row["as_of_date"]
        if isinstance(as_of, pd.Timestamp):
            as_of = as_of.date()
        elif not isinstance(as_of, date):
            as_of = date.today()

        constituents.append(
            ConstituentInfo(
                ticker=str(row["ticker"]),
                company_name=str(row["company_name"]),
                price=float(row["price"]),
                market_cap=float(row["market_cap"]),
                shares_outstanding=float(row["shares_outstanding"]),
                index_weight=float(row["index_weight"]),
                sector=str(row["sector"]),
                as_of_date=as_of,
            )
        )
    return constituents


def get_ticker_list(force_refresh: bool = False) -> list[str]:
    """Return list of NASDAQ-100 ticker symbols."""
    df = fetch_constituents(force_refresh=force_refresh)
    return df["ticker"].tolist()
