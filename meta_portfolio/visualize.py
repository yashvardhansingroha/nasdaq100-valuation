"""Plotly and matplotlib figure builders for the meta-portfolio backtest."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from meta_portfolio import config
from meta_portfolio.metrics import cumulative_wealth
from meta_portfolio.risk_engine import rolling_correlation


def equity_curve_figure(
    portfolio_net: dict[str, pd.Series],
    title: str = "Cumulative Wealth: Dynamic Allocators vs Benchmarks",
) -> go.Figure:
    fig = go.Figure()
    for name, series in portfolio_net.items():
        s = series.dropna()
        if s.empty:
            continue
        wealth = cumulative_wealth(s, log_input=True)
        fig.add_trace(
            go.Scatter(x=wealth.index, y=wealth.values, mode="lines", name=name)
        )
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Growth of $1",
        legend_title="Method",
        hovermode="x unified",
        template="plotly_white",
    )
    return fig


def weights_area_figure(
    weights: pd.DataFrame,
    title: str = "Dynamic Capital Weights",
) -> go.Figure:
    w = weights.dropna(how="all")
    fig = go.Figure()
    labels = config.TICKER_LABELS
    for col in w.columns:
        fig.add_trace(
            go.Scatter(
                x=w.index,
                y=w[col],
                mode="lines",
                stackgroup="one",
                name=labels.get(col, col),
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Weight",
        yaxis=dict(range=[0, 1]),
        hovermode="x unified",
        template="plotly_white",
    )
    return fig


def correlation_figure(
    returns: pd.DataFrame,
    pair: tuple[str, str] = ("A", "C"),
    window: int | None = None,
) -> go.Figure:
    window = window or config.ROLLING_WINDOW
    corr_panel = rolling_correlation(returns, window=window)
    # Extract pairwise series
    a, b = pair
    series = []
    for dt in returns.index:
        try:
            series.append((dt, float(corr_panel.loc[(dt, a), b])))
        except (KeyError, TypeError, ValueError):
            series.append((dt, float("nan")))
    cdf = pd.DataFrame(series, columns=["date", "corr"]).set_index("date")
    fig = go.Figure(
        go.Scatter(x=cdf.index, y=cdf["corr"], mode="lines", name=f"{a}–{b} corr")
    )
    fig.update_layout(
        title=f"{window}-Day Rolling Correlation ({a} vs {b})",
        xaxis_title="Date",
        yaxis_title="Correlation",
        template="plotly_white",
    )
    return fig


def regime_sharpe_figure(regime_table: pd.DataFrame) -> go.Figure:
    if regime_table.empty:
        return go.Figure()
    df = regime_table.reset_index()
    fig = go.Figure()
    for strat in df["Strategy"].unique():
        sub = df[df["Strategy"] == strat]
        fig.add_trace(go.Bar(name=strat, x=sub["Regime"], y=sub["Sharpe"]))
    fig.update_layout(
        barmode="group",
        title="Sharpe Ratio by Regime",
        xaxis_title="Regime",
        yaxis_title="Sharpe",
        template="plotly_white",
    )
    return fig


def export_equity_png(
    portfolio_net: dict[str, pd.Series],
    path: str | Path,
) -> Path:
    """Static matplotlib export for resume / PDF decks."""
    import matplotlib.pyplot as plt

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, series in portfolio_net.items():
        s = series.dropna()
        if s.empty:
            continue
        wealth = cumulative_wealth(s, log_input=True)
        ax.plot(wealth.index, wealth.values, label=name)
    ax.set_title("Cumulative Wealth: Dynamic Allocators vs Benchmarks")
    ax.set_ylabel("Growth of $1")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def combined_dashboard_figure(
    portfolio_net: dict[str, pd.Series],
    weights: pd.DataFrame,
) -> go.Figure:
    """Equity curve + weight stack in one figure."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.6, 0.4],
        subplot_titles=("Cumulative Wealth", "Capital Weights"),
        vertical_spacing=0.08,
    )
    for name, series in portfolio_net.items():
        s = series.dropna()
        if s.empty:
            continue
        wealth = cumulative_wealth(s, log_input=True)
        fig.add_trace(
            go.Scatter(x=wealth.index, y=wealth.values, mode="lines", name=name),
            row=1,
            col=1,
        )
    w = weights.dropna(how="all")
    labels = config.TICKER_LABELS
    for col in w.columns:
        fig.add_trace(
            go.Scatter(
                x=w.index,
                y=w[col],
                mode="lines",
                stackgroup="one",
                name=labels.get(col, col),
                showlegend=True,
            ),
            row=2,
            col=1,
        )
    fig.update_layout(template="plotly_white", hovermode="x unified", height=700)
    fig.update_yaxes(title_text="Growth of $1", row=1, col=1)
    fig.update_yaxes(title_text="Weight", range=[0, 1], row=2, col=1)
    return fig
