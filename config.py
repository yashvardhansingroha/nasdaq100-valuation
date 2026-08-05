"""Central configuration for the NASDAQ-100 valuation platform."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

# Valuation assumptions
DISCOUNT_RATE = 0.10
TERMINAL_GROWTH = 0.025
PROJECTION_YEARS = 5
DCF_WEIGHT = 0.50
MULTIPLES_WEIGHT = 0.50
MAX_FCF_GROWTH = 0.25
MIN_FCF_GROWTH = -0.05

# Scenario DCF probabilities and adjustments (bear / base / bull)
SCENARIO_PROBABILITIES = {"bear": 0.20, "base": 0.60, "bull": 0.20}
SCENARIO_ADJUSTMENTS = {
    "bear": {"growth": -0.05, "discount": 0.01},
    "base": {"growth": 0.0, "discount": 0.0},
    "bull": {"growth": 0.05, "discount": -0.01},
}

# Confidence thresholds
CONFIDENCE_HIGH = 70
CONFIDENCE_MEDIUM = 40

# Paths
DATABASE_PATH = str(PROJECT_ROOT / "database" / "history.db")
CACHE_DIR = str(PROJECT_ROOT / "data" / "cache")
PROCESSED_DIR = str(PROJECT_ROOT / "data" / "processed")
RAW_DIR = str(PROJECT_ROOT / "data" / "raw")
REPORTS_DIR = str(PROJECT_ROOT / "reports")
LOG_DIR = str(PROJECT_ROOT / "logs")
CONSTITUENTS_CSV = str(PROJECT_ROOT / "data" / "processed" / "nasdaq100_weights.csv")

# Cache TTL (hours)
CONSTITUENTS_CACHE_HOURS = 24
FINANCIALS_CACHE_HOURS = 12

# Index proxy ticker for market price
INDEX_PROXY_TICKER = "^NDX"

# API keys (optional)
FMP_API_KEY = os.getenv("FMP_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")

# Sentiment feature flags
ENABLE_ANALYST_SENTIMENT = True
ENABLE_NEWS_SENTIMENT = bool(NEWSAPI_KEY)
ENABLE_OPTIONS_SENTIMENT = True
ENABLE_INSTITUTIONAL_SENTIMENT = True

# Sentiment weights for overall score
SENTIMENT_WEIGHTS = {
    "analyst": 0.30,
    "news": 0.25,
    "options": 0.20,
    "institutional": 0.25,
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = str(PROJECT_ROOT / "logs" / "platform.log")
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

# Scheduler
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "06:30")
