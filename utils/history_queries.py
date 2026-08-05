"""Historical time-series query helpers."""

from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd

import config
from database.database import HistoryRepository
from utils.logging_config import setup_logging

logger = setup_logging(__name__)


class HistoryQueries:
    """Convenience wrapper for historical data retrieval."""

    def __init__(self, repo: Optional[HistoryRepository] = None) -> None:
        self.repo = repo or HistoryRepository()

    def get_intrinsic_vs_actual(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> pd.DataFrame:
        """Return time series of index price vs intrinsic value."""
        df = self.repo.get_index_history(start, end)
        if df.empty:
            return df
        df["valuation_gap_pct"] = (df["intrinsic_value"] - df["index_price"]) / df["index_price"] * 100
        return df

    def get_fair_value_ratio_history(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> pd.DataFrame:
        """Return fair value ratio over time."""
        df = self.repo.get_index_history(start, end)
        return df[["date", "fair_value_ratio"]] if not df.empty else df

    def get_coverage_history(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> pd.DataFrame:
        """Return coverage percentage over time."""
        df = self.repo.get_index_history(start, end)
        if df.empty:
            return df
        df["coverage_pct"] = df["coverage"] * 100
        return df[["date", "coverage_pct"]]

    def get_latest_snapshot(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Return latest company values, index snapshot, and sentiment."""
        latest = self.repo.get_latest_date()
        if latest is None:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        companies = self.repo.get_company_values_by_date(latest)
        index_hist = self.repo.get_index_history(start=latest, end=latest)
        sentiment = self.repo.get_sentiment_by_date(latest)
        return companies, index_hist, sentiment
