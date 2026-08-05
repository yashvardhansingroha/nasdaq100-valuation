"""Tests for blended valuation."""

from __future__ import annotations

import pytest

from valuation.blended_valuation import blend_valuation


def test_blended_both_values() -> None:
    blend = blend_valuation(100.0, 120.0, 80.0, 100.0, 120.0, 140.0)
    assert blend.valuation_method == "blended"
    assert blend.blended_value == pytest.approx(100.0)
    assert blend.blended_bear_value == pytest.approx(90.0)
    assert blend.blended_base_value == pytest.approx(100.0)
    assert blend.blended_bull_value == pytest.approx(110.0)
    assert blend.upside == pytest.approx(0.0)


def test_blended_dcf_only() -> None:
    blend = blend_valuation(100.0, 150.0, None, 130.0, 150.0, 170.0)
    assert blend.valuation_method == "dcf_only"
    assert blend.blended_value == 150.0
    assert blend.blended_bear_value == 130.0
    assert blend.blended_bull_value == 170.0
    assert blend.upside == pytest.approx(0.5)


def test_blended_multiples_only() -> None:
    blend = blend_valuation(100.0, None, 90.0)
    assert blend.valuation_method == "multiples_only"
    assert blend.blended_value == 90.0
    assert blend.blended_bear_value == 90.0
    assert blend.blended_base_value == 90.0
    assert blend.blended_bull_value == 90.0
    assert blend.upside == pytest.approx(-0.1)


def test_blended_failed() -> None:
    blend = blend_valuation(100.0, None, None)
    assert blend.valuation_method == "failed"
    assert blend.blended_value is None
    assert blend.upside is None
