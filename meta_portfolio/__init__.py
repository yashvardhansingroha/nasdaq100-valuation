"""Dynamic Multi-Strategy Allocation Engine (Meta-Portfolio)."""

from meta_portfolio.backtest import run_backtest
from meta_portfolio.data_loader import load_strategy_returns

__all__ = ["load_strategy_returns", "run_backtest"]
