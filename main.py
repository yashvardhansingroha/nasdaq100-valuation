"""Main entry point for the NASDAQ-100 valuation platform."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from database.database import HistoryRepository
from index.aggregate_index_value import aggregate_index_value
from index.fetch_constituents import get_constituent_list
from market.sentiment_engine import SentimentEngine
from reports.generator import ReportGenerator
from utils.logging_config import setup_logging
from valuation.valuation_engine import ValuationEngine

logger = setup_logging("main")


def run_constituents(force_refresh: bool = False) -> list:
    """Fetch and cache NASDAQ-100 constituents."""
    logger.info("Fetching constituents (force_refresh=%s)", force_refresh)
    return get_constituent_list(force_refresh=force_refresh)


def run_valuation_pipeline(constituents: list, as_of_date: date) -> tuple:
    """Run valuation and index aggregation."""
    engine = ValuationEngine()
    results = engine.run_valuation(constituents, as_of_date)
    snapshot = aggregate_index_value(results, as_of_date)
    return results, snapshot


def run_sentiment_pipeline(tickers: list[str], as_of_date: date) -> list:
    """Run sentiment analysis (separate from valuation)."""
    engine = SentimentEngine()
    return engine.run_sentiment(tickers, as_of_date)


def save_to_database(
    repo: HistoryRepository,
    results: list,
    snapshot,
    sentiment_results: list | None,
    as_of_date: date,
) -> None:
    """Persist all results to SQLite."""
    repo.save_company_values(as_of_date, results)
    repo.save_index_snapshot(snapshot)
    if sentiment_results:
        repo.save_sentiment(sentiment_results)


def generate_reports(results, snapshot, as_of_date, sentiment_df=None) -> dict:
    """Generate daily reports."""
    generator = ReportGenerator()
    return generator.generate_all(results, snapshot, as_of_date, sentiment_df)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="NASDAQ-100 Intrinsic Value Platform")
    parser.add_argument(
        "--mode",
        choices=["full", "valuation", "constituents", "sentiment"],
        default="full",
        help="Pipeline mode to run",
    )
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh constituent cache")
    args = parser.parse_args()

    start = time.time()
    as_of_date = date.today()
    repo = HistoryRepository()

    logger.info("=== NASDAQ-100 Platform | mode=%s | date=%s ===", args.mode, as_of_date)

    if args.mode == "constituents":
        constituents = run_constituents(force_refresh=args.force_refresh)
        logger.info("Fetched %d constituents", len(constituents))
        return

    constituents = run_constituents(force_refresh=args.force_refresh)
    tickers = [c.ticker for c in constituents]

    if args.mode in ("full", "valuation"):
        results, snapshot = run_valuation_pipeline(constituents, as_of_date)
        save_to_database(repo, results, snapshot, None, as_of_date)

        sentiment_results = None
        sentiment_df = None

        if args.mode == "full":
            sentiment_results = run_sentiment_pipeline(tickers, as_of_date)
            repo.save_sentiment(sentiment_results)
            sentiment_engine = SentimentEngine()
            sentiment_df = sentiment_engine.results_to_dataframe(sentiment_results)

        generate_reports(results, snapshot, as_of_date, sentiment_df)
        logger.info(
            "Coverage: %.1f%% | Fair value ratio: %.3f (bear=%.3f base=%.3f bull=%.3f)",
            snapshot.coverage * 100,
            snapshot.fair_value_ratio,
            snapshot.fair_value_ratio_bear,
            snapshot.fair_value_ratio_base,
            snapshot.fair_value_ratio_bull,
        )

    elif args.mode == "sentiment":
        sentiment_results = run_sentiment_pipeline(tickers, as_of_date)
        repo.save_sentiment(sentiment_results)

    elapsed = time.time() - start
    logger.info("Pipeline completed in %.1f seconds", elapsed)


if __name__ == "__main__":
    main()
