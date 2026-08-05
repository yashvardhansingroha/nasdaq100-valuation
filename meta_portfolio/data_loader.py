"""Download and cache real ETF prices; compute aligned log returns."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from meta_portfolio import config


def _ensure_data_dir() -> Path:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return config.DATA_DIR


def download_prices(
    tickers: dict[str, str] | None = None,
    start: str | None = None,
    end: str | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """
    Fetch adjusted close prices for strategy proxy ETFs.

    Returns a DataFrame with columns keyed by strategy id (A/B/C),
    indexed by trading date.
    """
    tickers = tickers or config.TICKERS
    start = start or config.START_DATE
    end = end or config.END_DATE
    _ensure_data_dir()

    cache_path = config.PRICE_CACHE_FILE
    if cache_path.exists() and not force:
        prices = pd.read_parquet(cache_path)
        return prices

    symbols = list(tickers.values())
    raw = yf.download(
        symbols,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if raw.empty:
        raise RuntimeError(f"yfinance returned no data for {symbols}")

    # yfinance multi-ticker layout: columns are MultiIndex (Field, Ticker)
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"].copy()
    else:
        close = raw[["Close"]].copy()
        close.columns = symbols

    # Map ticker symbols back to strategy ids A/B/C
    rename = {sym: sid for sid, sym in tickers.items()}
    close = close.rename(columns=rename)
    close = close[[sid for sid in tickers.keys() if sid in close.columns]]
    close = close.dropna(how="any").sort_index()
    close.index = pd.to_datetime(close.index).tz_localize(None)

    close.to_parquet(cache_path)
    return close


def prices_to_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily log returns; first row dropped after differencing."""
    log_ret = np.log(prices / prices.shift(1)).dropna(how="any")
    return log_ret


def load_strategy_returns(
    force_download: bool = False,
    tickers: dict[str, str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """
    Return aligned daily log returns for strategies A, B, C.

    Uses parquet cache when available. Set force_download=True to refresh.
    """
    _ensure_data_dir()
    returns_cache = config.RETURNS_CACHE_FILE

    if returns_cache.exists() and not force_download:
        returns = pd.read_parquet(returns_cache)
        return returns

    prices = download_prices(tickers=tickers, start=start, end=end, force=force_download)
    returns = prices_to_log_returns(prices)
    returns.to_parquet(returns_cache)
    return returns


def load_fixture_returns(n_days: int = 300, seed: int = 42) -> pd.DataFrame:
    """
    Offline synthetic returns for unit tests (not used in production backtests).

    Shapes roughly mimic momentum / low-vol / crisis sleeves.
    """
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=n_days)
    a = 0.0008 + 0.015 * rng.standard_normal(n_days)
    # occasional crash days for A
    crash = rng.random(n_days) < 0.02
    a = np.where(crash, a - 0.06, a)
    b = 0.0003 + 0.006 * rng.standard_normal(n_days)
    # C spikes when A crashes
    c = 0.0001 + 0.020 * rng.standard_normal(n_days)
    c = np.where(crash, np.abs(rng.standard_normal(n_days)) * 0.08, c)
    return pd.DataFrame({"A": a, "B": b, "C": c}, index=idx)
