"""NASDAQ-100 Valuation Platform — 4-tab Streamlit app (self-bootstrapping)."""
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import config

MIN_DAYS = 60


@st.cache_data
def _fetch(query: str) -> pd.DataFrame:
    with sqlite3.connect(config.DATABASE_PATH) as con:
        return pd.read_sql(query, con)


@st.cache_data
def load_data() -> dict:
    """Load history tables; if the DB is missing or short, run generate_history.py first."""
    db = Path(config.DATABASE_PATH)
    n = 0
    if db.exists():
        n = int(_fetch("SELECT COUNT(DISTINCT date) AS n FROM daily_index")["n"].iloc[0])
    if n < MIN_DAYS:
        subprocess.run([sys.executable, str(ROOT / "generate_history.py")], check=True, cwd=str(ROOT))
        _fetch.clear()
    return {
        "idx": _fetch("SELECT * FROM daily_index ORDER BY date"),
        "latest": _fetch("SELECT * FROM daily_company_values WHERE date=(SELECT MAX(date) FROM daily_company_values)"),
        "sent": _fetch("SELECT date, ticker, overall_sentiment, news_score FROM sentiment ORDER BY date"),
    }


st.set_page_config(page_title="NASDAQ-100 Valuation", layout="wide")
st.title("NASDAQ-100 Intrinsic Value Platform")
st.caption("Intrinsic value comes only from fundamentals (DCF + multiples). Sentiment is tracked separately and never feeds valuation.")

d = load_data()
idx, comp, sent = d["idx"], d["latest"], d["sent"]
last = idx.iloc[-1]
t1, t2, t3, t4 = st.tabs([
    "Index Overview & Fair-Value Gap",
    "DCF Bear/Base/Bull vs Multiples",
    "Sector Attribution",
    "60-Day Historical Trend & Sentiment",
])

with t1:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(f"NDX Level ({last.date})", f"{last.index_price:,.0f}")
    m2.metric("Index Intrinsic Value", f"{last.intrinsic_value:,.0f}")
    m3.metric("Fair-Value Ratio", f"{last.fair_value_ratio:.3f}", f"{(last.fair_value_ratio - 1) * 100:+.1f}% vs 1.0")
    m4.metric("Bear / Bull Ratio", f"{last.fair_value_ratio_bear:.2f} / {last.fair_value_ratio_bull:.2f}")
    m5.metric("Coverage", f"{last.coverage * 100:.0f}%")
    top = pd.concat([comp.nlargest(8, "upside"), comp.nsmallest(8, "upside")]).sort_values("upside")
    fig = go.Figure(go.Bar(x=top.upside * 100, y=top.ticker, orientation="h",
                           marker_color=["#22a06b" if u > 0 else "#d64545" for u in top.upside]))
    fig.update_layout(title="Widest gaps vs intrinsic (upside %, latest snapshot)", height=430, margin=dict(l=10, r=10, t=50, b=10))
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(fig, use_container_width=True)
    c2.dataframe(comp.nlargest(15, "upside")[["ticker", "sector", "price", "blended_value", "upside", "confidence_score"]]
                 .assign(upside=lambda x: (x.upside * 100).round(1)).rename(columns={"upside": "upside %"}), use_container_width=True)

with t2:
    top25 = comp.nlargest(25, "index_weight").reset_index(drop=True)
    pick = st.selectbox("Ticker", top25.ticker.tolist(), index=0)
    row = comp[comp.ticker == pick].iloc[0]
    vals = {"Market price": row.price, "Multiples": row.multiples_value, "DCF bear": row.dcf_bear_value,
            "DCF base": row.dcf_base_value, "DCF bull": row.dcf_bull_value, "Blended": row.blended_value,
            "Blended bear": row.blended_bear_value, "Blended bull": row.blended_bull_value}
    fig = go.Figure(go.Bar(x=list(vals), y=[v for v in vals.values()],
                           marker_color=["#555"] + ["#888"] * 3 + ["#2b6cb0"] * 4, text=[f"{v:,.0f}" if pd.notna(v) else "" for v in vals.values()], textposition="outside"))
    fig.update_layout(title=f"{pick} — price vs intrinsic estimates (USD/share)", height=420, margin=dict(l=10, r=10, t=50, b=10))
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(fig, use_container_width=True)
    both = comp.dropna(subset=["dcf_base_value", "multiples_value"])
    dcf_vs_px = (both.dcf_base_value > both.price).mean() * 100
    spread = ((both.dcf_base_value / both.multiples_value - 1) * 100).median()
    c2.metric("Companies with DCF base > price", f"{dcf_vs_px:.0f}%")
    c2.metric("Median DCF-base vs multiples spread", f"{spread:+.0f}%")
    c2.caption(f"{pick}: blended {row.blended_value:,.0f} vs price {row.price:,.0f} → upside {(row.blended_value / row.price - 1) * 100:+.0f}% | confidence {row.confidence_score:.0f}/100 ({row.valuation_method})")

with t3:
    g = comp.assign(w=comp.index_weight, gap=comp.index_weight * (comp.blended_value / comp.price - 1).fillna(0), wup=comp.index_weight * comp.upside.fillna(0))
    sec = g.groupby("sector").agg(weight=("w", "sum"), companies=("ticker", "count"), avg_confidence=("confidence_score", "mean"), gap_contrib=("gap", "sum"), w_upside=("wup", "sum"))
    sec["weighted upside %"] = (sec.w_upside / sec.weight * 100).round(1)
    sec["gap contribution %"] = (sec.gap_contrib * 100).round(2)
    sec = sec.sort_values("gap contribution %")
    fig = go.Figure(go.Bar(x=sec["gap contribution %"], y=sec.index, orientation="h",
                           marker_color=["#d64545" if v < 0 else "#22a06b" for v in sec["gap contribution %"]]))
    fig.update_layout(title="Contribution to index fair-value gap by sector (weight × blended/price − 1)", height=430, margin=dict(l=10, r=10, t=50, b=10))
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(fig, use_container_width=True)
    c2.dataframe(sec[["weight", "companies", "avg_confidence", "weighted upside %", "gap contribution %"]].round(3), use_container_width=True)

with t4:
    s = sent.groupby("date", as_index=False)["overall_sentiment"].mean()
    fvr = idx.fair_value_ratio
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=idx.date, y=idx.intrinsic_value_bull, name="Intrinsic bull", line=dict(dash="dot", color="#2b6cb0")), secondary_y=False)
    fig.add_trace(go.Scatter(x=idx.date, y=idx.intrinsic_value_bear, name="Intrinsic bear", line=dict(dash="dot", color="#805ad5"), fill="tonexty", fillcolor="rgba(43,108,176,0.08)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=idx.date, y=idx.intrinsic_value, name="Intrinsic (blended)", line=dict(color="#2b6cb0", width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=idx.date, y=idx.index_price, name="NDX level", line=dict(color="#111", width=2)), secondary_y=False)
    fig.add_trace(go.Scatter(x=s.date, y=s.overall_sentiment, name="Avg sentiment [-1,1]", line=dict(color="#dd8800", width=2)), secondary_y=True)
    fig.add_hline(y=0, line=dict(color="#dd8800", width=1, dash="dot"), secondary_y=True)
    fig.update_layout(title=f"{len(idx)}-day index price vs intrinsic band, with sentiment overlay", height=460, margin=dict(l=10, r=10, t=50, b=10))
    fig.update_yaxes(title_text="Index level", secondary_y=False)
    fig.update_yaxes(title_text="Sentiment", range=[-1, 1], secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
    joined = idx.assign(ret=idx.index_price.pct_change()).merge(s, on="date")
    corr = float(joined.ret.corr(joined.overall_sentiment))
    c1, c2, c3 = st.columns(3)
    c1.metric("Fair-value ratio window", f"{fvr.min():.3f} → {fvr.max():.3f}")
    c2.metric("Mean daily sentiment", f"{s.overall_sentiment.mean():+.3f}")
    c3.metric("corr(daily sentiment, NDX return)", f"{corr:+.2f}")
    st.caption("Sentiment scores are deterministic functions of (ticker, date) in [-1, +1]; they never influence intrinsic values.")
