"""SQLAlchemy ORM schema definitions."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Date, Float, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class DailyCompanyValue(Base):
    """Append-only daily company valuation snapshot."""

    __tablename__ = "daily_company_values"
    __table_args__ = (UniqueConstraint("date", "ticker", name="uq_company_date_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    dcf_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    multiples_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    blended_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    blended_bear_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    blended_base_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    blended_bull_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    upside: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuation_method: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    sector: Mapped[str] = mapped_column(String(64), nullable=False, default="Unknown")
    market_cap: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    index_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dcf_bear_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    dcf_base_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    dcf_bull_value: Mapped[float | None] = mapped_column(Float, nullable=True)


class DailyIndex(Base):
    """Append-only daily index-level snapshot."""

    __tablename__ = "daily_index"
    __table_args__ = (UniqueConstraint("date", name="uq_index_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    index_price: Mapped[float] = mapped_column(Float, nullable=False)
    intrinsic_value: Mapped[float] = mapped_column(Float, nullable=False)
    fair_value_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    fair_value_ratio_bear: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fair_value_ratio_base: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fair_value_ratio_bull: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    intrinsic_value_bear: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    intrinsic_value_base: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    intrinsic_value_bull: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    coverage: Mapped[float] = mapped_column(Float, nullable=False)
    total_market_cap: Mapped[float] = mapped_column(Float, nullable=False)


class Sentiment(Base):
    """Daily market sentiment — separate from intrinsic value."""

    __tablename__ = "sentiment"
    __table_args__ = (UniqueConstraint("date", "ticker", name="uq_sentiment_date_ticker"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    analyst_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    news_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    options_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    institutional_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_sentiment: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


def create_db_engine(db_path: str):
    """Create SQLAlchemy engine for SQLite."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def migrate_schema(engine) -> None:
    """Add missing columns to existing databases."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    company_cols = {c["name"] for c in inspector.get_columns("daily_company_values")}
    index_cols = {c["name"] for c in inspector.get_columns("daily_index")}

    company_additions = {
        "blended_bear_value": "REAL",
        "blended_base_value": "REAL",
        "blended_bull_value": "REAL",
        "dcf_bear_value": "REAL",
        "dcf_base_value": "REAL",
        "dcf_bull_value": "REAL",
    }
    index_additions = {
        "fair_value_ratio_bear": "REAL DEFAULT 0.0",
        "fair_value_ratio_base": "REAL DEFAULT 0.0",
        "fair_value_ratio_bull": "REAL DEFAULT 0.0",
        "intrinsic_value_bear": "REAL DEFAULT 0.0",
        "intrinsic_value_base": "REAL DEFAULT 0.0",
        "intrinsic_value_bull": "REAL DEFAULT 0.0",
    }

    with engine.connect() as conn:
        for col, col_type in company_additions.items():
            if col not in company_cols:
                conn.execute(text(f"ALTER TABLE daily_company_values ADD COLUMN {col} {col_type}"))
        for col, col_type in index_additions.items():
            if col not in index_cols:
                conn.execute(text(f"ALTER TABLE daily_index ADD COLUMN {col} {col_type}"))
        conn.commit()


def get_session_factory(db_path: str):
    """Return a configured session factory."""
    engine = create_db_engine(db_path)
    Base.metadata.create_all(engine)
    migrate_schema(engine)
    return sessionmaker(bind=engine)
