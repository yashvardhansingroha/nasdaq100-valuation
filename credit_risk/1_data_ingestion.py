"""Bulk-load Lending Club accepted loans CSV into PostgreSQL (chunked)."""

from __future__ import annotations

import sys

import pandas as pd
from sqlalchemy import create_engine, text

import config


def _clean_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """Drop footer / summary rows that are not real loans."""
    out = chunk.copy()
    # Lending Club files append text summary lines after the data
    out = out[out["id"].notna()]
    out = out[~out["id"].astype(str).str.contains("Total amount funded", case=False, na=False)]
    out["id"] = pd.to_numeric(out["id"], errors="coerce")
    out = out[out["id"].notna()]
    out["id"] = out["id"].astype("int64")
    return out


def main() -> None:
    if "YOUR_PASSWORD" in config.DATABASE_URL:
        print(
            "ERROR: Set CREDIT_RISK_DATABASE_URL in the repo root .env "
            "(replace YOUR_PASSWORD with your PostgreSQL password)."
        )
        sys.exit(1)

    if not config.CSV_PATH.exists():
        print(f"ERROR: CSV not found at {config.CSV_PATH}")
        print("Download Lending Club accepted_2007_to_2018Q4.csv(.gz) and set CREDIT_RISK_CSV_PATH.")
        sys.exit(1)

    print(f"Streaming CSV into PostgreSQL from {config.CSV_PATH}...")
    read_kwargs = {
        "usecols": config.COLUMNS_TO_KEEP,
        "low_memory": False,
        "chunksize": config.TO_SQL_CHUNKSIZE,
    }
    if config.CSV_PATH.suffix == ".gz":
        read_kwargs["compression"] = "gzip"

    engine = create_engine(config.DATABASE_URL)

    with engine.begin() as conn:
        conn.execute(text("DROP VIEW IF EXISTS vw_vintage_cohorts CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS vw_grade_segments CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS vw_clean_loan_data CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS loan_data_raw CASCADE"))

    total_rows = 0
    first_chunk = True

    for chunk in pd.read_csv(config.CSV_PATH, **read_kwargs):
        chunk = _clean_chunk(chunk)
        if chunk.empty:
            continue
        chunk.to_sql(
            "loan_data_raw",
            engine,
            if_exists="replace" if first_chunk else "append",
            index=False,
            method="multi",
            chunksize=2_000,
        )
        total_rows += len(chunk)
        first_chunk = False
        print(f"  loaded {total_rows:,} rows...", flush=True)

    if first_chunk:
        print("ERROR: No valid loan rows were loaded.")
        sys.exit(1)

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM loan_data_raw")).scalar()
    print(f"Database ingestion complete. loan_data_raw row count: {count:,}")


if __name__ == "__main__":
    main()
