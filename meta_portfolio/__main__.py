"""CLI entry: python -m meta_portfolio [--force-download]."""

from __future__ import annotations

import argparse
import sys

from meta_portfolio.attribution import attribution_summary
from meta_portfolio.backtest import run_backtest
from meta_portfolio.data_loader import load_strategy_returns
from meta_portfolio.export_excel import export_workbook
from meta_portfolio.memo_pdf import generate_memo_pdf
from meta_portfolio.regimes import regime_metrics_table
from meta_portfolio.visualize import export_equity_png


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Meta-Portfolio allocation backtest")
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Refresh ETF prices from yfinance",
    )
    parser.add_argument(
        "--export-png",
        default="meta_portfolio/data/equity_curve.png",
        help="Path for static equity curve PNG",
    )
    parser.add_argument(
        "--skip-reports",
        action="store_true",
        help="Skip Excel workbook and PDF memo export",
    )
    args = parser.parse_args(argv)

    print("Loading strategy returns (MTUM / USMV / VIXY)...")
    returns = load_strategy_returns(force_download=args.force_download)
    print(
        f"  {len(returns)} days from {returns.index.min().date()} "
        f"to {returns.index.max().date()}"
    )

    print("Running backtest (InvVol / MinVar / MaxDiv vs EW / 60-40)...")
    result = run_backtest(returns)
    assert result.metrics is not None

    print("\n=== Performance (net of 10bps costs for dynamic methods) ===")
    print(result.metrics.round(4).to_string())

    print("\n=== Regime Sharpe / Max DD ===")
    print(regime_metrics_table(result.portfolio_net).round(4).to_string())

    print("\n=== Attribution (MinVar) ===")
    print(
        attribution_summary(
            result.weights["MinVar"],
            returns,
            costs=result.costs["MinVar"],
        )
        .round(4)
        .to_string()
    )

    path = export_equity_png(result.portfolio_net, args.export_png)
    print(f"\nSaved equity curve: {path}")

    if not args.skip_reports:
        xlsx = export_workbook(result)
        print(f"Saved Excel workbook: {xlsx}")
        pdf = generate_memo_pdf(result)
        print(f"Saved investment memo: {pdf}")

    print("Dashboard: streamlit run dashboard/meta_portfolio.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
