"""Streamlit dashboard for NASDAQ-100 intrinsic value platform."""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from index.sector_analysis import analyze_sectors
from utils.history_queries import HistoryQueries


st.set_page_config(
    page_title="NASDAQ-100 Intrinsic Value",
    page_icon="📊",
    layout="wide",
)

queries = HistoryQueries()


def _load_latest() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return queries.get_latest_snapshot()


def page_overview() -> None:
    """Overview page with index vs intrinsic value."""
    st.header("Overview")
    companies, index_df, _ = _load_latest()

    if index_df.empty:
        st.warning("No data available. Run `python main.py --mode full` to populate the database.")
        return

    row = index_df.iloc[0]
    gap_pct = (row["intrinsic_value"] - row["index_price"]) / row["index_price"] * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Index Price", f"{row['index_price']:,.0f}")
    col2.metric("Intrinsic Value", f"{row['intrinsic_value']:,.0f}", f"{gap_pct:+.1f}%")
    col3.metric("Fair Value Ratio", f"{row['fair_value_ratio']:.3f}")
    col4.metric("Coverage", f"{row['coverage'] * 100:.1f}%")

    if "intrinsic_value_bear" in row and row["intrinsic_value_bull"]:
        st.subheader("Valuation Range (Bear / Base / Bull)")
        range_col1, range_col2, range_col3 = st.columns(3)
        range_col1.metric("Bear Case", f"{row['intrinsic_value_bear']:,.0f}")
        range_col2.metric("Base Case", f"{row['intrinsic_value_base']:,.0f}")
        range_col3.metric("Bull Case", f"{row['intrinsic_value_bull']:,.0f}")

        fig_range = go.Figure()
        fig_range.add_trace(
            go.Bar(
                x=["Bear", "Base", "Bull", "Market"],
                y=[
                    row.get("intrinsic_value_bear", 0),
                    row.get("intrinsic_value_base", 0),
                    row.get("intrinsic_value_bull", 0),
                    row["index_price"],
                ],
                marker_color=["#EF553B", "#00CC96", "#636EFA", "#AB63FA"],
            )
        )
        fig_range.update_layout(title="Index Valuation Range vs Market", yaxis_title="Index Level")
        st.plotly_chart(fig_range, use_container_width=True)

    if not companies.empty:
        avg_conf = companies["confidence_score"].mean()
        st.metric("Average Confidence", f"{avg_conf:.1f}")

    hist = queries.get_intrinsic_vs_actual()
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=hist["date"], y=hist["index_price"], name="Index Price", line=dict(color="#636EFA"))
        )
        fig.add_trace(
            go.Scatter(
                x=hist["date"],
                y=hist["intrinsic_value"],
                name="Intrinsic Value",
                line=dict(color="#00CC96"),
            )
        )
        fig.update_layout(title="Index Price vs Intrinsic Value", xaxis_title="Date", yaxis_title="Value")
        st.plotly_chart(fig, use_container_width=True)


def page_companies() -> None:
    """Sortable company valuation table."""
    st.header("Companies")
    companies, _, sentiment = _load_latest()

    if companies.empty:
        st.warning("No company data available.")
        return

    df = companies.copy()
    if not sentiment.empty:
        df = df.merge(sentiment[["ticker", "overall_sentiment"]], on="ticker", how="left")

    if "upside" in df.columns:
        df["upside_pct"] = df["upside"].apply(lambda x: f"{x * 100:+.1f}%" if pd.notna(x) else "N/A")

    display_cols = [
        "ticker",
        "price",
        "blended_bear_value",
        "blended_base_value",
        "blended_bull_value",
        "blended_value",
        "upside_pct",
        "confidence_score",
        "valuation_method",
        "sector",
    ]
    if "overall_sentiment" in df.columns:
        display_cols.append("overall_sentiment")

    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)


def page_sectors() -> None:
    """Sector analysis charts."""
    st.header("Sector Analysis")
    companies, _, sentiment = _load_latest()

    if companies.empty:
        st.warning("No data available.")
        return

    from utils.models import ValuationResult

    results = [
        ValuationResult(
            ticker=row["ticker"],
            price=row["price"],
            dcf_value=row.get("dcf_value"),
            multiples_value=row.get("multiples_value"),
            blended_value=row.get("blended_value"),
            upside=row.get("upside"),
            valuation_method=row.get("valuation_method", ""),
            confidence_score=row.get("confidence_score", 0),
            confidence_label="",
            status="",
            sector=row.get("sector", "Unknown"),
            market_cap=row.get("market_cap", 0),
            index_weight=row.get("index_weight", 0),
        )
        for _, row in companies.iterrows()
    ]

    sector_df = analyze_sectors(results, sentiment)
    if sector_df.empty:
        st.warning("No sector data.")
        return

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            sector_df,
            x="sector",
            y="avg_upside",
            title="Average Upside by Sector",
            color="avg_upside",
            color_continuous_scale="RdYlGn",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            sector_df,
            x="sector",
            y="weight_contribution",
            title="Index Weight by Sector",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(sector_df, use_container_width=True, hide_index=True)


def page_history() -> None:
    """Historical charts."""
    st.header("History")
    hist = queries.get_intrinsic_vs_actual()

    if hist.empty:
        st.warning("No historical data available.")
        return

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=hist["date"], y=hist["fair_value_ratio"], name="Fair Value Ratio"))
    fig1.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig1.update_layout(title="Fair Value Ratio Over Time", yaxis_title="Ratio")
    st.plotly_chart(fig1, use_container_width=True)

    coverage = queries.get_coverage_history()
    if not coverage.empty:
        fig2 = px.line(coverage, x="date", y="coverage_pct", title="Coverage Over Time")
        st.plotly_chart(fig2, use_container_width=True)


def page_sentiment() -> None:
    """Sentiment analysis page."""
    st.header("Market Sentiment")
    st.caption("Sentiment is reported separately and does NOT affect intrinsic value.")

    _, _, sentiment = _load_latest()
    if sentiment.empty:
        st.warning("No sentiment data available.")
        return

    df = sentiment.copy()
    if "overall_sentiment" in df.columns:
        df["label"] = df["overall_sentiment"].apply(
            lambda x: "Bullish" if x >= 60 else ("Bearish" if x <= 40 else "Neutral")
        )

    st.dataframe(df, use_container_width=True, hide_index=True)

    if "overall_sentiment" in df.columns:
        fig = px.histogram(df, x="overall_sentiment", nbins=20, title="Sentiment Distribution")
        st.plotly_chart(fig, use_container_width=True)


def page_settings() -> None:
    """Configuration display and pipeline trigger."""
    st.header("Settings")
    st.subheader("Valuation Assumptions")
    st.json(
        {
            "DISCOUNT_RATE": config.DISCOUNT_RATE,
            "TERMINAL_GROWTH": config.TERMINAL_GROWTH,
            "PROJECTION_YEARS": config.PROJECTION_YEARS,
            "DCF_WEIGHT": config.DCF_WEIGHT,
            "MULTIPLES_WEIGHT": config.MULTIPLES_WEIGHT,
            "INDEX_PROXY_TICKER": config.INDEX_PROXY_TICKER,
            "DATABASE_PATH": config.DATABASE_PATH,
        }
    )

    st.subheader("Run Pipeline")
    st.code("python main.py --mode full", language="bash")
    st.info("Run the command above in a terminal to refresh data.")


def main() -> None:
    """Main dashboard entry point."""
    st.sidebar.title("NASDAQ-100 Platform")
    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "Companies", "Sector Analysis", "History", "Sentiment", "Settings"],
    )

    pages = {
        "Overview": page_overview,
        "Companies": page_companies,
        "Sector Analysis": page_sectors,
        "History": page_history,
        "Sentiment": page_sentiment,
        "Settings": page_settings,
    }
    pages[page]()


if __name__ == "__main__":
    main()
