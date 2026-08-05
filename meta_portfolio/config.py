"""Configuration for the Dynamic Multi-Strategy Allocation Engine."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DATA_DIR = PACKAGE_ROOT / "data"

# Strategy proxies (real ETF return streams)
TICKERS = {
    "A": "MTUM",  # Momentum
    "B": "USMV",  # Min-vol / defensive
    "C": "VIXY",  # Crisis / vol
}
TICKER_LABELS = {
    "A": "Momentum (MTUM)",
    "B": "Min Vol (USMV)",
    "C": "Vol / Crisis (VIXY)",
}

START_DATE = "2019-01-01"
END_DATE = None  # None = through latest available

# Risk engine
ROLLING_WINDOW = 60
TRADING_DAYS_PER_YEAR = 252
VOL_FLOOR = 1e-6  # avoid division by zero

# Allocator bounds (long-only, fully invested)
WEIGHT_MIN = 0.05
WEIGHT_MAX = 0.60

# Transaction costs: 10 bps per unit of one-way turnover
TRANSACTION_COST = 0.0010

# Risk-free rate for Sharpe / Sortino
RISK_FREE_RATE = 0.045

# Static benchmarks
EQUAL_WEIGHT = 1.0 / 3.0
BENCH_60_40 = {"A": 0.60, "B": 0.40, "C": 0.0}

# Regime windows for stress / cycle analysis
REGIMES = {
    "COVID Crash": ("2020-02-15", "2020-03-31"),
    "2021 Bull": ("2021-01-01", "2021-12-31"),
    "2022 Rate Shock": ("2022-01-01", "2022-12-31"),
    "2023 Recovery": ("2023-01-01", "2023-12-31"),
}

# Cache
PRICE_CACHE_FILE = DATA_DIR / "etf_prices.parquet"
RETURNS_CACHE_FILE = DATA_DIR / "etf_returns.parquet"

# Quant Club, BITS Pilani — case study branding (memo / deck)
CLUB_NAME = "Quant Club, BITS Pilani"
CASE_STUDY_TITLE = "Multi-Strategy Portfolio Allocation"
CASE_STUDY_VERTICAL = "Research Case Study | Portfolio Construction"
AUTHOR_NAME = "Yashvardhan"  # update if needed
CASE_STUDY_DATE = "August 2026"
