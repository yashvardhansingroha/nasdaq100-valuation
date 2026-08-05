"""Export backtest outputs to an IB-friendly Excel workbook."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from meta_portfolio import config
from meta_portfolio.attribution import attribution_summary
from meta_portfolio.backtest import BacktestResult
from meta_portfolio.regimes import regime_metrics_table


def _weights_long(weights: dict[str, pd.DataFrame], methods: list[str]) -> pd.DataFrame:
    """Stack selected weight panels into a long table with Method column."""
    frames = []
    for name in methods:
        if name not in weights:
            continue
        w = weights[name].dropna(how="all").copy()
        w = w.reset_index()
        date_col = w.columns[0]
        w = w.rename(columns={date_col: "Date"})
        w.insert(0, "Method", name)
        frames.append(w)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def export_workbook(
    result: BacktestResult,
    path: str | Path | None = None,
) -> Path:
    """
    Write Returns / Weights / Performance / Regimes / Attribution sheets.

    Uses openpyxl via pandas ExcelWriter.
    """
    reports_dir = config.PACKAGE_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = Path(path) if path else reports_dir / "meta_portfolio_analysis.xlsx"

    returns = result.returns.copy()
    returns.index.name = "Date"
    returns_out = returns.rename(columns=config.TICKER_LABELS).reset_index()

    weights_out = _weights_long(
        result.weights,
        methods=["InvVol", "MinVar", "MaxDiv"],
    )

    perf = result.metrics.copy() if result.metrics is not None else pd.DataFrame()
    regimes = regime_metrics_table(result.portfolio_net).reset_index()

    attr_frames = []
    for method in ("InvVol", "MinVar", "MaxDiv"):
        if method not in result.weights:
            continue
        attr = attribution_summary(
            result.weights[method],
            result.returns,
            costs=result.costs.get(method),
        ).reset_index()
        attr.insert(0, "Method", method)
        attr_frames.append(attr)
    attribution = pd.concat(attr_frames, ignore_index=True) if attr_frames else pd.DataFrame()

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        returns_out.to_excel(writer, sheet_name="Returns", index=False)
        weights_out.to_excel(writer, sheet_name="Weights", index=False)
        perf.to_excel(writer, sheet_name="Performance", index=True)
        regimes.to_excel(writer, sheet_name="Regimes", index=False)
        attribution.to_excel(writer, sheet_name="Attribution", index=False)

    return path
