"""Financial data provider abstraction."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

import config
from utils.logging_config import setup_logging
from utils.models import CompanyFinancials, ConstituentInfo

logger = setup_logging(__name__)


def _safe_float(value: object) -> Optional[float]:
    """Convert a value to float, returning None for invalid inputs."""
    if value is None:
        return None
    try:
        result = float(value)
        if pd.isna(result):
            return None
        return result
    except (TypeError, ValueError):
        return None


def _extract_series(df: Optional[pd.DataFrame], row_label: str) -> list[float]:
    """Extract a numeric time series from a yfinance financial statement."""
    if df is None or df.empty or row_label not in df.index:
        return []
    values: list[float] = []
    for val in df.loc[row_label]:
        f = _safe_float(val)
        if f is not None:
            values.append(f)
    return values


class FinancialDataProvider(ABC):
    """Abstract interface for fetching company financial data."""

    @abstractmethod
    def get_financials(self, ticker: str) -> CompanyFinancials:
        """Fetch fundamental data for a single ticker."""

    @abstractmethod
    def get_financials_batch(self, tickers: list[str]) -> dict[str, CompanyFinancials]:
        """Fetch fundamentals for multiple tickers."""


class YFinanceProvider(FinancialDataProvider):
    """Default provider using yfinance."""

    def __init__(self, cache_hours: int = config.FINANCIALS_CACHE_HOURS) -> None:
        self.cache_hours = cache_hours
        self.cache_dir = Path(config.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, ticker: str) -> Path:
        return self.cache_dir / f"financials_{ticker.upper()}.json"

    def _load_cache(self, ticker: str) -> Optional[CompanyFinancials]:
        path = self._cache_path(ticker)
        if not path.exists():
            return None
        age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
        if age > timedelta(hours=self.cache_hours):
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return CompanyFinancials(**data)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Invalid cache for %s: %s", ticker, exc)
            return None

    def _save_cache(self, financials: CompanyFinancials) -> None:
        path = self._cache_path(financials.ticker)
        data = {
            "ticker": financials.ticker,
            "revenue": financials.revenue,
            "fcf": financials.fcf,
            "debt": financials.debt,
            "cash": financials.cash,
            "shares_outstanding": financials.shares_outstanding,
            "ebitda": financials.ebitda,
            "net_income": financials.net_income,
            "sector": financials.sector,
            "price": financials.price,
            "market_cap": financials.market_cap,
            "revenue_history": financials.revenue_history,
            "earnings_history": financials.earnings_history,
            "fcf_history": financials.fcf_history,
        }
        path.write_text(json.dumps(data), encoding="utf-8")

    def get_financials(self, ticker: str) -> CompanyFinancials:
        """Fetch fundamentals for one ticker with caching."""
        cached = self._load_cache(ticker)
        if cached is not None:
            return cached

        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            income = stock.financials
            cashflow = stock.cashflow
            balance = stock.balance_sheet

            revenue = _safe_float(info.get("totalRevenue"))
            if revenue is None and income is not None and not income.empty:
                revenue = _safe_float(
                    income.loc["Total Revenue"].iloc[0]
                    if "Total Revenue" in income.index
                    else None
                )

            fcf = None
            if cashflow is not None and not cashflow.empty:
                if "Free Cash Flow" in cashflow.index:
                    fcf = _safe_float(cashflow.loc["Free Cash Flow"].iloc[0])
                elif "Operating Cash Flow" in cashflow.index:
                    ocf = _safe_float(cashflow.loc["Operating Cash Flow"].iloc[0])
                    capex = _safe_float(
                        cashflow.loc["Capital Expenditure"].iloc[0]
                        if "Capital Expenditure" in cashflow.index
                        else 0
                    )
                    if ocf is not None:
                        fcf = ocf + (capex or 0)

            debt = _safe_float(info.get("totalDebt"))
            cash = _safe_float(info.get("totalCash"))
            shares = _safe_float(info.get("sharesOutstanding"))
            ebitda = _safe_float(info.get("ebitda"))
            net_income = _safe_float(info.get("netIncomeToCommon"))

            financials = CompanyFinancials(
                ticker=ticker.upper(),
                revenue=revenue,
                fcf=fcf,
                debt=debt,
                cash=cash,
                shares_outstanding=shares,
                ebitda=ebitda,
                net_income=net_income,
                sector=info.get("sector", "Unknown") or "Unknown",
                price=_safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
                market_cap=_safe_float(info.get("marketCap")),
                revenue_history=_extract_series(income, "Total Revenue"),
                earnings_history=_extract_series(income, "Net Income"),
                fcf_history=_extract_series(cashflow, "Free Cash Flow"),
            )
            self._save_cache(financials)
            return financials

        except Exception as exc:
            logger.error("Failed to fetch financials for %s: %s", ticker, exc)
            return CompanyFinancials(ticker=ticker.upper(), sector="Unknown")

    def get_financials_batch(self, tickers: list[str]) -> dict[str, CompanyFinancials]:
        """Fetch fundamentals for a list of tickers with rate limiting."""
        results: dict[str, CompanyFinancials] = {}
        for i, ticker in enumerate(tickers):
            results[ticker.upper()] = self.get_financials(ticker)
            if (i + 1) % 10 == 0:
                time.sleep(0.5)
        return results

    def get_index_price(self, ticker: str = config.INDEX_PROXY_TICKER) -> Optional[float]:
        """Fetch current index or proxy price."""
        try:
            data = yf.Ticker(ticker).history(period="5d")
            if data.empty:
                return None
            return float(data["Close"].iloc[-1])
        except Exception as exc:
            logger.error("Failed to fetch index price: %s", exc)
            return None


def get_default_provider() -> FinancialDataProvider:
    """Return the default financial data provider."""
    return YFinanceProvider()
