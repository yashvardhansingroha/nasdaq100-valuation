"""Blend DCF and multiples valuations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import config
from utils.logging_config import setup_logging

logger = setup_logging(__name__)


@dataclass
class BlendResult:
    """Blended intrinsic values across bear/base/bull scenarios."""

    blended_value: Optional[float]
    blended_bear_value: Optional[float]
    blended_base_value: Optional[float]
    blended_bull_value: Optional[float]
    upside: Optional[float]
    valuation_method: str


def _blend_pair(
    dcf_value: Optional[float],
    multiples_value: Optional[float],
) -> tuple[Optional[float], str]:
    """Blend one DCF scenario with multiples using configured weights."""
    w_dcf = config.DCF_WEIGHT
    w_mult = config.MULTIPLES_WEIGHT

    if dcf_value is not None and dcf_value > 0 and multiples_value is not None and multiples_value > 0:
        return w_dcf * dcf_value + w_mult * multiples_value, "blended"
    if dcf_value is not None and dcf_value > 0:
        return dcf_value, "dcf_only"
    if multiples_value is not None and multiples_value > 0:
        return multiples_value, "multiples_only"
    return None, "failed"


def blend_valuation(
    price: float,
    dcf_value: Optional[float],
    multiples_value: Optional[float],
    dcf_bear_value: Optional[float] = None,
    dcf_base_value: Optional[float] = None,
    dcf_bull_value: Optional[float] = None,
) -> BlendResult:
    """
    Combine DCF and multiples into blended intrinsic values per scenario.

    When both DCF and multiples are valid, each scenario uses 50/50 blending.
    Fallbacks mirror single-model logic when only one method is available.
    """
    blended_bear, _ = _blend_pair(dcf_bear_value, multiples_value)
    blended_base, method = _blend_pair(dcf_base_value or dcf_value, multiples_value)
    blended_bull, _ = _blend_pair(dcf_bull_value, multiples_value)

    # Primary blended value: use probability-weighted DCF when available
    blended, primary_method = _blend_pair(dcf_value, multiples_value)
    if blended is None:
        blended = blended_base
    valuation_method = primary_method if blended is not None else method

    upside = None
    if blended is not None and price and price > 0:
        upside = (blended - price) / price

    return BlendResult(
        blended_value=blended,
        blended_bear_value=blended_bear,
        blended_base_value=blended_base,
        blended_bull_value=blended_bull,
        upside=upside,
        valuation_method=valuation_method,
    )
