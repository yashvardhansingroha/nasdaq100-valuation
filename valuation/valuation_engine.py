"""Orchestrates the full valuation pipeline."""

from __future__ import annotations

import time
from datetime import date
from typing import Optional

import pandas as pd

from utils.data_provider import FinancialDataProvider, get_default_provider
from utils.logging_config import setup_logging
from utils.models import CompanyFinancials, ConstituentInfo, ValuationResult
from valuation.blended_valuation import blend_valuation
from valuation.confidence_model import compute_confidence
from valuation.dcf_model import run_dcf
from valuation.multiples_model import compute_sector_medians, run_multiples

logger = setup_logging(__name__)


class ValuationEngine:
    """Runs DCF, multiples, blended, and confidence for a set of tickers."""

    def __init__(self, provider: Optional[FinancialDataProvider] = None) -> None:
        self.provider = provider or get_default_provider()

    def run_valuation(
        self,
        constituents: list[ConstituentInfo],
        as_of_date: Optional[date] = None,
    ) -> list[ValuationResult]:
        """
        Run full valuation pipeline for all constituents.

        Intrinsic value is computed ONLY from fundamentals — no sentiment.
        """
        as_of_date = as_of_date or date.today()
        tickers = [c.ticker for c in constituents]
        weight_map = {c.ticker: c for c in constituents}

        start = time.time()
        logger.info("Starting valuation for %d tickers on %s", len(tickers), as_of_date)

        financials_map = self.provider.get_financials_batch(tickers)

        for c in constituents:
            fin = financials_map.get(c.ticker)
            if fin:
                if not fin.price:
                    fin.price = c.price
                if not fin.market_cap:
                    fin.market_cap = c.market_cap
                if not fin.sector or fin.sector == "Unknown":
                    fin.sector = c.sector

        sector_medians = compute_sector_medians(financials_map)
        results: list[ValuationResult] = []

        for ticker in tickers:
            t_start = time.time()
            fin = financials_map.get(ticker, CompanyFinancials(ticker=ticker))
            const = weight_map.get(ticker)
            price = fin.price or (const.price if const else 0.0)

            dcf_result = run_dcf(fin)
            mult_value, mult_status = run_multiples(fin, sector_medians)
            blend = blend_valuation(
                price,
                dcf_result.value,
                mult_value,
                dcf_bear_value=dcf_result.bear_value,
                dcf_base_value=dcf_result.base_value,
                dcf_bull_value=dcf_result.bull_value,
            )
            confidence, label = compute_confidence(fin, dcf_result.value, mult_value)

            status_parts = []
            if dcf_result.status != "success":
                status_parts.append(f"dcf:{dcf_result.status}")
            if mult_status != "success":
                status_parts.append(f"mult:{mult_status}")
            status = "; ".join(status_parts) if status_parts else "success"

            if fin.revenue is None and fin.fcf is None:
                logger.warning("Missing data for %s", ticker)
                status = "missing_data"

            results.append(
                ValuationResult(
                    ticker=ticker,
                    price=price,
                    dcf_value=dcf_result.value,
                    multiples_value=mult_value,
                    blended_value=blend.blended_value,
                    upside=blend.upside,
                    valuation_method=blend.valuation_method,
                    confidence_score=confidence,
                    confidence_label=label,
                    status=status,
                    sector=fin.sector or (const.sector if const else "Unknown"),
                    market_cap=fin.market_cap or (const.market_cap if const else 0.0),
                    index_weight=const.index_weight if const else 0.0,
                    dcf_bear_value=dcf_result.bear_value,
                    dcf_base_value=dcf_result.base_value,
                    dcf_bull_value=dcf_result.bull_value,
                    blended_bear_value=blend.blended_bear_value,
                    blended_base_value=blend.blended_base_value,
                    blended_bull_value=blend.blended_bull_value,
                )
            )
            logger.debug("Valued %s in %.2fs — method=%s", ticker, time.time() - t_start, blend.valuation_method)

        valued = sum(1 for r in results if r.blended_value is not None)
        logger.info(
            "Valuation complete: %d/%d valued in %.1fs",
            valued,
            len(results),
            time.time() - start,
        )
        return results

    def results_to_dataframe(self, results: list[ValuationResult]) -> pd.DataFrame:
        """Convert valuation results to a pandas DataFrame."""
        return pd.DataFrame(
            [
                {
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
                    "confidence_label": r.confidence_label,
                    "status": r.status,
                    "sector": r.sector,
                    "market_cap": r.market_cap,
                    "index_weight": r.index_weight,
                }
                for r in results
            ]
        )
