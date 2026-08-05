"""Streamlit dashboard for the Meta-Portfolio allocation engine."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from meta_portfolio.attribution import attribution_summary
from meta_portfolio.backtest import run_backtest
from meta_portfolio.data_loader import load_strategy_returns
from meta_portfolio.regimes import regime_metrics_table
from meta_portfolio.visualize import (
    correlation_figure,
    equity_curve_figure,
    regime_sharpe_figure,
    weights_area_figure,
)

st.set_page_config(
    page_title="Meta-Portfolio Engine",
    page_icon="📈",
    layout="wide",
)

st.title("Dynamic Multi-Strategy Allocation Engine")
st.caption(
    "Risk-parity and covariance-optimized allocation across MTUM / USMV / VIXY "
    "— net of 10bps turnover costs."
)


@st.cache_data(show_spinner="Loading ETF returns…")
def _load(force: bool) -> object:
    return load_strategy_returns(force_download=force)


@st.cache_data(show_spinner="Running backtest…")
def _backtest(force: bool) -> object:
    returns = _load(force)
    return run_backtest(returns), returns


force = st.sidebar.checkbox("Force refresh from yfinance", value=False)
method = st.sidebar.selectbox(
    "Weight chart method",
    ["MinVar", "InvVol", "MaxDiv"],
    index=0,
)

result, returns = _backtest(force)

st.subheader("Performance summary")
if result.metrics is not None:
    st.dataframe(
        result.metrics.style.format(
            {
                "Ann. Return": "{:.2%}",
                "Ann. Vol": "{:.2%}",
                "Sharpe": "{:.2f}",
                "Sortino": "{:.2f}",
                "Max Drawdown": "{:.2%}",
                "Calmar": "{:.2f}",
                "VaR 95% (1d)": "{:.2%}",
                "Info Ratio vs EW": "{:.2f}",
                "Ann. Turnover": "{:.2f}",
                "Total Cost Drag": "{:.4f}",
                "Ann. Cost Drag": "{:.2%}",
            },
            na_rep="—",
        ),
        use_container_width=True,
    )

st.caption(
    "**Exhibit 1 — Equity curve:** Dynamic InvVol cuts drawdown vs equal-weight "
    "despite lower return than static 60/40 (which holds no VIXY)."
)
st.plotly_chart(
    equity_curve_figure(result.portfolio_net),
    use_container_width=True,
)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(
        weights_area_figure(
            result.weights[method],
            title=f"Capital Weights — {method}",
        ),
        use_container_width=True,
    )
    st.caption(
        "**Exhibit 2 — Weight stack:** VIXY allocation rises when trailing volatility "
        "spikes (e.g. March 2020), shrinking momentum exposure automatically."
    )
with col2:
    st.plotly_chart(
        correlation_figure(returns, pair=("A", "C")),
        use_container_width=True,
    )
    st.caption(
        "**Exhibit 3 — A–C correlation:** Crisis sleeve (VIXY) often diversifies when "
        "momentum sells off; correlation is regime-dependent, not constant."
    )

st.subheader("Regime analysis")
regime_df = regime_metrics_table(result.portfolio_net)
st.dataframe(
    regime_df.style.format(
        {
            "Total Return": "{:.2%}",
            "Sharpe": "{:.2f}",
            "Max Drawdown": "{:.2%}",
            "Ann. Vol": "{:.2%}",
        }
    ),
    use_container_width=True,
)
st.plotly_chart(regime_sharpe_figure(regime_df), use_container_width=True)

st.subheader(f"Attribution — {method}")
attr = attribution_summary(
    result.weights[method],
    returns,
    costs=result.costs.get(method),
)
st.dataframe(attr.style.format("{:.4f}"), use_container_width=True)
