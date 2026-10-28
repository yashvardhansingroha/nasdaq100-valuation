"""Daily report generation (CSV, Excel, PDF)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
from fpdf import FPDF

import config
from index.contribution_analysis import top_overvalued, top_undervalued
from index.sector_analysis import analyze_sectors
from utils.logging_config import setup_logging
from utils.models import IndexSnapshot, ValuationResult

logger = setup_logging(__name__)


class ReportGenerator:
    """Generate daily valuation reports in multiple formats."""

    def __init__(self, output_dir: str = config.REPORTS_DIR) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _date_str(self, as_of_date: date) -> str:
        return as_of_date.strftime("%Y-%m-%d")

    def generate_csv(
        self,
        results: list[ValuationResult],
        as_of_date: date,
        sentiment_df: pd.DataFrame | None = None,
    ) -> Path:
        """Generate daily CSV report."""
        records = []
        sentiment_map = {}
        if sentiment_df is not None and not sentiment_df.empty:
            sentiment_map = dict(zip(sentiment_df["ticker"], sentiment_df["overall_sentiment"]))

        for r in results:
            records.append(
                {
                    "date": as_of_date,
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
                    "sector": r.sector,
                    "market_cap": r.market_cap,
                    "index_weight": r.index_weight,
                    "overall_sentiment": sentiment_map.get(r.ticker),
                }
            )

        df = pd.DataFrame(records)
        path = self.output_dir / f"nasdaq100_{self._date_str(as_of_date)}.csv"
        df.to_csv(path, index=False)
        logger.info("Generated CSV report: %s", path)
        return path

    def generate_excel(
        self,
        results: list[ValuationResult],
        snapshot: IndexSnapshot,
        as_of_date: date,
        sentiment_df: pd.DataFrame | None = None,
    ) -> Path:
        """Generate multi-sheet Excel report."""
        path = self.output_dir / f"nasdaq100_{self._date_str(as_of_date)}.xlsx"

        companies_df = pd.DataFrame(
            [
                {
                    "ticker": r.ticker,
                    "price": r.price,
                    "blended_value": r.blended_value,
                    "upside": r.upside,
                    "confidence_score": r.confidence_score,
                    "valuation_method": r.valuation_method,
                    "sector": r.sector,
                }
                for r in results
            ]
        )

        overview = pd.DataFrame(
            [
                {
                    "date": as_of_date,
                    "index_price": snapshot.index_price,
                    "intrinsic_value": snapshot.intrinsic_value,
                    "intrinsic_value_bear": snapshot.intrinsic_value_bear,
                    "intrinsic_value_base": snapshot.intrinsic_value_base,
                    "intrinsic_value_bull": snapshot.intrinsic_value_bull,
                    "fair_value_ratio": snapshot.fair_value_ratio,
                    "fair_value_ratio_bear": snapshot.fair_value_ratio_bear,
                    "fair_value_ratio_base": snapshot.fair_value_ratio_base,
                    "fair_value_ratio_bull": snapshot.fair_value_ratio_bull,
                    "coverage": snapshot.coverage,
                    "total_market_cap": snapshot.total_market_cap,
                    "valuation_gap_pct": (
                        (snapshot.intrinsic_value - snapshot.index_price) / snapshot.index_price * 100
                        if snapshot.index_price
                        else 0
                    ),
                }
            ]
        )

        sectors_df = analyze_sectors(results, sentiment_df)

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            overview.to_excel(writer, sheet_name="Overview", index=False)
            companies_df.to_excel(writer, sheet_name="Companies", index=False)
            if not sectors_df.empty:
                sectors_df.to_excel(writer, sheet_name="Sectors", index=False)

        logger.info("Generated Excel report: %s", path)
        return path

    def generate_pdf(
        self,
        results: list[ValuationResult],
        snapshot: IndexSnapshot,
        as_of_date: date,
    ) -> Path:
        """Generate PDF summary report."""
        path = self.output_dir / f"nasdaq100_{self._date_str(as_of_date)}.pdf"

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "NASDAQ-100 Intrinsic Value Report", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 8, f"Date: {as_of_date}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        gap_pct = (
            (snapshot.intrinsic_value - snapshot.index_price) / snapshot.index_price * 100
            if snapshot.index_price
            else 0
        )
        pdf.cell(0, 7, f"Index Price: {snapshot.index_price:,.2f}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"Intrinsic Value: {snapshot.intrinsic_value:,.2f}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"Fair Value Ratio: {snapshot.fair_value_ratio:.3f}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"Valuation Gap: {gap_pct:+.1f}%", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"Coverage: {snapshot.coverage * 100:.1f}%", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Top 5 Undervalued", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        for _, row in top_undervalued(results, 5).iterrows():
            pdf.cell(
                0,
                6,
                f"  {row['ticker']}: upside {row['upside'] * 100:+.1f}%",
                new_x="LMARGIN",
                new_y="NEXT",
            )

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Top 5 Overvalued", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        for _, row in top_overvalued(results, 5).iterrows():
            pdf.cell(
                0,
                6,
                f"  {row['ticker']}: upside {row['upside'] * 100:+.1f}%",
                new_x="LMARGIN",
                new_y="NEXT",
            )

        pdf.output(str(path))
        logger.info("Generated PDF report: %s", path)
        return path

    def generate_all(
        self,
        results: list[ValuationResult],
        snapshot: IndexSnapshot,
        as_of_date: date,
        sentiment_df: pd.DataFrame | None = None,
    ) -> dict[str, Path]:
        """Generate all report formats."""
        return {
            "csv": self.generate_csv(results, as_of_date, sentiment_df),
            "excel": self.generate_excel(results, snapshot, as_of_date, sentiment_df),
            "pdf": self.generate_pdf(results, snapshot, as_of_date),
        }
