"""Database repository for append-only historical data."""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
from sqlalchemy.exc import IntegrityError

import config
from database.schema import DailyCompanyValue, DailyIndex, Sentiment, get_session_factory
from utils.logging_config import setup_logging
from utils.models import IndexSnapshot, SentimentResult, ValuationResult

logger = setup_logging(__name__)


class HistoryRepository:
    """Append-only repository for valuation and sentiment history."""

    def __init__(self, db_path: str = config.DATABASE_PATH) -> None:
        self.Session = get_session_factory(db_path)

    def save_company_values(self, as_of_date: date, results: list[ValuationResult]) -> int:
        """Insert daily company valuation rows. Skips duplicates."""
        session = self.Session()
        inserted = 0
        try:
            for r in results:
                row = DailyCompanyValue(
                    date=as_of_date,
                    ticker=r.ticker,
                    price=r.price,
                    dcf_value=r.dcf_value,
                    multiples_value=r.multiples_value,
                    blended_value=r.blended_value,
                    blended_bear_value=r.blended_bear_value,
                    blended_base_value=r.blended_base_value,
                    blended_bull_value=r.blended_bull_value,
                    upside=r.upside,
                    valuation_method=r.valuation_method,
                    confidence_score=r.confidence_score,
                    sector=r.sector,
                    market_cap=r.market_cap,
                    index_weight=r.index_weight,
                    dcf_bear_value=r.dcf_bear_value,
                    dcf_base_value=r.dcf_base_value,
                    dcf_bull_value=r.dcf_bull_value,
                )
                session.add(row)
                try:
                    session.commit()
                    inserted += 1
                except IntegrityError:
                    session.rollback()
                    logger.debug("Skipping duplicate company row: %s %s", as_of_date, r.ticker)
            logger.info("Saved %d company value rows for %s", inserted, as_of_date)
            return inserted
        finally:
            session.close()

    def save_index_snapshot(self, snapshot: IndexSnapshot) -> bool:
        """Insert index-level snapshot. Returns False if duplicate."""
        session = self.Session()
        try:
            row = DailyIndex(
                date=snapshot.date,
                index_price=snapshot.index_price,
                intrinsic_value=snapshot.intrinsic_value,
                fair_value_ratio=snapshot.fair_value_ratio,
                fair_value_ratio_bear=snapshot.fair_value_ratio_bear,
                fair_value_ratio_base=snapshot.fair_value_ratio_base,
                fair_value_ratio_bull=snapshot.fair_value_ratio_bull,
                intrinsic_value_bear=snapshot.intrinsic_value_bear,
                intrinsic_value_base=snapshot.intrinsic_value_base,
                intrinsic_value_bull=snapshot.intrinsic_value_bull,
                coverage=snapshot.coverage,
                total_market_cap=snapshot.total_market_cap,
            )
            session.add(row)
            session.commit()
            logger.info("Saved index snapshot for %s", snapshot.date)
            return True
        except IntegrityError:
            session.rollback()
            logger.debug("Skipping duplicate index row for %s", snapshot.date)
            return False
        finally:
            session.close()

    def save_sentiment(self, results: list[SentimentResult]) -> int:
        """Insert sentiment rows. Skips duplicates."""
        session = self.Session()
        inserted = 0
        try:
            for r in results:
                row = Sentiment(
                    date=r.date,
                    ticker=r.ticker,
                    analyst_score=r.analyst_score,
                    news_score=r.news_score,
                    options_score=r.options_score,
                    institutional_score=r.institutional_score,
                    overall_sentiment=r.overall_sentiment,
                )
                session.add(row)
                try:
                    session.commit()
                    inserted += 1
                except IntegrityError:
                    session.rollback()
                    logger.debug("Skipping duplicate sentiment row: %s %s", r.date, r.ticker)
            logger.info("Saved %d sentiment rows", inserted)
            return inserted
        finally:
            session.close()

    def get_latest_date(self) -> Optional[date]:
        """Return the most recent date in daily_index."""
        session = self.Session()
        try:
            row = session.query(DailyIndex).order_by(DailyIndex.date.desc()).first()
            return row.date if row else None
        finally:
            session.close()

    def get_index_history(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> pd.DataFrame:
        """Return index history as DataFrame."""
        session = self.Session()
        try:
            query = session.query(DailyIndex)
            if start:
                query = query.filter(DailyIndex.date >= start)
            if end:
                query = query.filter(DailyIndex.date <= end)
            rows = query.order_by(DailyIndex.date).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame(
                [
                    {
                        "date": r.date,
                        "index_price": r.index_price,
                        "intrinsic_value": r.intrinsic_value,
                        "intrinsic_value_bear": r.intrinsic_value_bear,
                        "intrinsic_value_base": r.intrinsic_value_base,
                        "intrinsic_value_bull": r.intrinsic_value_bull,
                        "fair_value_ratio": r.fair_value_ratio,
                        "fair_value_ratio_bear": r.fair_value_ratio_bear,
                        "fair_value_ratio_base": r.fair_value_ratio_base,
                        "fair_value_ratio_bull": r.fair_value_ratio_bull,
                        "coverage": r.coverage,
                        "total_market_cap": r.total_market_cap,
                    }
                    for r in rows
                ]
            )
        finally:
            session.close()

    def get_company_values_by_date(self, as_of_date: date) -> pd.DataFrame:
        """Return all company valuations for a given date."""
        session = self.Session()
        try:
            rows = (
                session.query(DailyCompanyValue)
                .filter(DailyCompanyValue.date == as_of_date)
                .all()
            )
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame(
                [
                    {
                        "date": r.date,
                        "ticker": r.ticker,
                        "price": r.price,
                        "dcf_value": r.dcf_value,
                        "dcf_bear_value": r.dcf_bear_value,
                        "dcf_base_value": r.dcf_base_value,
                        "dcf_bull_value": r.dcf_bull_value,
                        "multiples_value": r.multiples_value,
                        "blended_value": r.blended_value,
                        "blended_bear_value": r.blended_bear_value,
                        "blended_base_value": r.blended_base_value,
                        "blended_bull_value": r.blended_bull_value,
                        "upside": r.upside,
                        "valuation_method": r.valuation_method,
                        "confidence_score": r.confidence_score,
                        "sector": r.sector,
                        "market_cap": r.market_cap,
                        "index_weight": r.index_weight,
                    }
                    for r in rows
                ]
            )
        finally:
            session.close()

    def get_sentiment_by_date(self, as_of_date: date) -> pd.DataFrame:
        """Return sentiment data for a given date."""
        session = self.Session()
        try:
            rows = session.query(Sentiment).filter(Sentiment.date == as_of_date).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame(
                [
                    {
                        "date": r.date,
                        "ticker": r.ticker,
                        "analyst_score": r.analyst_score,
                        "news_score": r.news_score,
                        "options_score": r.options_score,
                        "institutional_score": r.institutional_score,
                        "overall_sentiment": r.overall_sentiment,
                    }
                    for r in rows
                ]
            )
        finally:
            session.close()
