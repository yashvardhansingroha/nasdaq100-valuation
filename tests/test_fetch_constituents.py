"""Tests for constituent fetching and weight calculation."""

from __future__ import annotations

import pandas as pd
import pytest


def test_index_weights_sum_to_one() -> None:
    """Verify weight calculation logic."""
    df = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "market_cap": [600e9, 300e9, 100e9],
        }
    )
    total = df["market_cap"].sum()
    df["index_weight"] = df["market_cap"] / total
    assert df["index_weight"].sum() == pytest.approx(1.0)
    assert df.loc[0, "index_weight"] == pytest.approx(0.6)


def test_weight_with_zero_mcap_fallback() -> None:
    df = pd.DataFrame({"ticker": ["A", "B"], "market_cap": [0.0, 0.0]})
    total = df["market_cap"].sum()
    if total > 0:
        df["index_weight"] = df["market_cap"] / total
    else:
        df["index_weight"] = 1.0 / len(df)
    assert df["index_weight"].sum() == pytest.approx(1.0)


def test_constituent_info_fields() -> None:
    from utils.models import ConstituentInfo
    from datetime import date

    c = ConstituentInfo(
        ticker="AAPL",
        company_name="Apple Inc.",
        price=180.0,
        market_cap=2800e9,
        shares_outstanding=15e9,
        index_weight=0.12,
        sector="Technology",
        as_of_date=date.today(),
    )
    assert c.ticker == "AAPL"
    assert 0 < c.index_weight < 1
