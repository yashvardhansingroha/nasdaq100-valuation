"""Configuration for the Lending Club credit-risk pipeline."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load root .env if present, then local overrides
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

CREDIT_RISK_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = CREDIT_RISK_ROOT / "output"

DATABASE_URL = os.getenv(
    "CREDIT_RISK_DATABASE_URL",
    "postgresql://postgres:YOUR_PASSWORD@localhost:5432/mn_analytics_db",
)

CSV_PATH = Path(
    os.getenv(
        "CREDIT_RISK_CSV_PATH",
        r"C:\Users\ysing\Downloads\accepted_2007_to_2018Q4.csv.gz",
    )
)

COLUMNS_TO_KEEP = [
    "id",
    "loan_amnt",
    "term",
    "int_rate",
    "installment",
    "grade",
    "emp_length",
    "home_ownership",
    "annual_inc",
    "verification_status",
    "issue_d",
    "loan_status",
    "purpose",
    "dti",
    "delinq_2yrs",
    "total_acc",
    "open_acc",
    "pub_rec",
    "revol_bal",
    "revol_util",
    "mort_acc",
]

# IFRS 9 — conservative LGD for unsecured consumer lending
LGD = 0.60

# Population Stability Index thresholds (industry convention)
PSI_THRESHOLDS = {"stable": 0.10, "moderate": 0.25}

# Illustrative stress scenarios (not regulatory-grade)
STRESS_SCENARIOS = {
    "base": {"pd_multiplier": 1.0, "pd_additive": 0.0},
    "adverse": {"pd_multiplier": 1.5, "pd_additive": 0.0},
    "severe": {"pd_multiplier": 2.0, "pd_additive": 0.0},
    "recession": {"pd_multiplier": 1.0, "pd_additive": 0.05},
}

# WOE / IV application scorecard
SCORECARD_FEATURES = [
    "dti",
    "annual_inc",
    "revol_util",
    "emp_length_years",
    "term_months",
]
SCORECARD_BINS = 5
SCORECARD_MIN = 300
SCORECARD_MAX = 850

RANDOM_STATE = 42
TEST_SIZE = 0.3
TO_SQL_CHUNKSIZE = 50_000
