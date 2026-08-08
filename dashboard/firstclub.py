"""Streamlit dashboard for FirstClub install-to-first-order funnel teardown."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from firstclub.cac_ltv_simulator import (
    UnitEconomicsInputs,
    scenario_comparison,
    sensitivity_grid,
    simulate_ltv,
)
from firstclub.competitive import competitive_benchmarks, gap_vs_competitors
from firstclub.experiments import experiments_dataframe
from firstclub.funnel_analysis import compute_funnel, funnel_by_dimension, identify_acquisition_gaps
from firstclub.generate_data import save_datasets
from firstclub.review_synthesis import review_theme_summary, trust_gap_signals

st.set_page_config(
    page_title="FirstClub Funnel Teardown",
    page_icon="🛒",
    layout="wide",
)

st.title("FirstClub — Install-to-First-Order Funnel Teardown")
st.caption(
    "App Store review synthesis · 1.2M+ order dataset · competitive benchmarks · "
    "8 ICE-scored experiments · CAC/LTV simulator at 1M-order scale"
)

tab_funnel, tab_reviews, tab_competitive, tab_experiments, tab_ltv, tab_roadmap = st.tabs(
    ["Funnel", "App Store Reviews", "Competitive", "Experiments (ICE)", "CAC/LTV Simulator", "Roadmap"]
)


@st.cache_data(show_spinner="Generating 1.2M order dataset…")
def _load_data(force: bool) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    paths = save_datasets(force=force)
    orders = pd.read_parquet(paths["orders"])
    reviews = pd.read_parquet(paths["reviews"])
    import json
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    return orders, reviews, summary


force = st.sidebar.checkbox("Regenerate synthetic data", value=False)
orders, reviews, summary = _load_data(force)

with tab_funnel:
    funnel = compute_funnel(orders)
    gaps = identify_acquisition_gaps(funnel)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Orders", f"{summary['order_count']:,}")
    col2.metric("Install → 1st Order", f"{summary.get('first_order_rate', 0.29):.0%}")
    col3.metric("D7 Retention", f"{summary['d7_retention']:.0%}")
    col4.metric("D30 Retention", f"{summary['d30_retention']:.0%}")

    fig = go.Figure(go.Funnel(
        y=funnel["stage"],
        x=funnel["users"],
        textinfo="value+percent initial",
    ))
    fig.update_layout(title="Install → First Order Funnel", height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Funnel Gaps")
    st.dataframe(pd.DataFrame(gaps), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        by_city = funnel_by_dimension(orders, "city")
        fig_city = px.bar(by_city, x="city", y="first_order_rate", title="First-Order Rate by City")
        st.plotly_chart(fig_city, use_container_width=True)
    with c2:
        by_channel = funnel_by_dimension(orders, "channel")
        fig_ch = px.bar(by_channel, x="channel", y="first_order_rate", title="First-Order Rate by Channel")
        st.plotly_chart(fig_ch, use_container_width=True)

with tab_reviews:
    themes = review_theme_summary(reviews)
    trust = trust_gap_signals(reviews)

    col1, col2 = st.columns(2)
    col1.metric("Reviews Analyzed", f"{len(reviews):,}")
    col2.metric("Avg Rating", f"{reviews['rating'].mean():.2f}")

    fig_themes = px.bar(
        themes.sort_values("pct_negative", ascending=True),
        x="pct_negative",
        y="theme",
        orientation="h",
        title="Negative Sentiment Share by Theme",
        labels={"pct_negative": "Negative %"},
    )
    st.plotly_chart(fig_themes, use_container_width=True)

    st.subheader("Trust Gap Signals")
    st.dataframe(pd.DataFrame(trust), use_container_width=True)

with tab_competitive:
    benchmarks = competitive_benchmarks()
    comp_gaps = gap_vs_competitors(summary)

    fig_comp = px.scatter(
        benchmarks,
        x="install_to_first_order_pct",
        y="d30_retention_pct",
        size="aov_inr",
        color="competitor",
        text="competitor",
        title="Competitive Position: Conversion vs D30 Retention",
    )
    fig_comp.update_traces(textposition="top center")
    st.plotly_chart(fig_comp, use_container_width=True)

    st.subheader("Gap vs Peer Median")
    st.dataframe(comp_gaps, use_container_width=True)

with tab_experiments:
    exps = experiments_dataframe()
    fig_ice = px.scatter(
        exps,
        x="impact",
        y="ease",
        size="confidence",
        color="pillar",
        hover_name="name",
        text="id",
        title="ICE Experiment Portfolio",
    )
    fig_ice.update_traces(textposition="top center")
    st.plotly_chart(fig_ice, use_container_width=True)
    st.dataframe(
        exps[["id", "name", "pillar", "ice_score", "impact", "confidence", "ease", "effort_weeks"]],
        use_container_width=True,
    )

with tab_ltv:
    st.subheader("Unit Economics Simulator (1M-order scale)")

    c1, c2, c3 = st.columns(3)
    cac = c1.slider("CAC (₹)", 100, 300, 185)
    churn = c2.slider("Monthly Churn %", 20, 55, 38) / 100
    aov = c3.slider("AOV (₹)", 300, 700, 485)

    inputs = UnitEconomicsInputs(cac_inr=cac, monthly_churn_pct=churn, aov_inr=aov)
    result = simulate_ltv(inputs)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("LTV (12 mo)", f"₹{result.cohort_ltv_inr:,.0f}")
    m2.metric("LTV/CAC", f"{result.ltv_cac_ratio:.2f}×")
    m3.metric("Payback", f"{result.payback_months} mo")
    m4.metric("Annual Revenue @ 1M orders", f"₹{result.annual_revenue_inr/1e7:.1f} Cr")

    fig_curve = px.line(
        result.monthly_cohort_df,
        x="month",
        y="cumulative_contribution_inr",
        title="Cohort Cumulative Contribution (₹)",
    )
    st.plotly_chart(fig_curve, use_container_width=True)

    st.subheader("Experiment Scenarios")
    scenarios = scenario_comparison()
    st.dataframe(scenarios, use_container_width=True)

    grid = sensitivity_grid(inputs)
    pivot = grid.pivot(index="monthly_churn_pct", columns="cac_inr", values="ltv_cac_ratio")
    fig_heat = px.imshow(
        pivot,
        labels=dict(x="CAC (₹)", y="Monthly Churn", color="LTV/CAC"),
        title="LTV/CAC Sensitivity",
        aspect="auto",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab_roadmap:
    st.markdown("""
### 30-60-90 Day Roadmap

**Days 0–30:** Trust & conversion — EXP-01 (ETA badge), EXP-03 (cart push), EXP-06 (reorder)  
**Days 31–60:** Retention recovery — EXP-02 (rider tracking), EXP-04 (D30 win-back), EXP-07 (referral)  
**Days 61–90:** Repeat & scale — EXP-05 (subscription), EXP-08 (Pune city launch)

See full deliverables in `firstclub/reports/`:
- `GROWTH_MEMO.md` — executive summary
- `ROADMAP_30_60_90.md` — phased plan
- `EVENT_TAXONOMY.md` — analytics schema
- `CITY_LAUNCH_PLAYBOOK.md` — expansion runbook
- `prds/` — 8 mini PRDs
    """)

    reports_dir = ROOT / "firstclub" / "reports"
    for md_file in sorted(reports_dir.glob("*.md")):
        with st.expander(md_file.stem.replace("_", " ").title()):
            st.markdown(md_file.read_text(encoding="utf-8"))
