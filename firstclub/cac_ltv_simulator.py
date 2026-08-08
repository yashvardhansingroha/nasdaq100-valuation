"""CAC/LTV unit economics simulator at 1M-order scale."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from firstclub.config import (
    DEFAULT_AOV,
    DEFAULT_CAC,
    DEFAULT_GROSS_MARGIN,
    DEFAULT_MONTHLY_CHURN,
    DEFAULT_ORDERS_PER_ACTIVE_MONTH,
    SIMULATOR_ORDER_SCALE,
)


@dataclass
class UnitEconomicsInputs:
    monthly_new_users: int = 80_000
    cac_inr: float = DEFAULT_CAC
    aov_inr: float = DEFAULT_AOV
    gross_margin_pct: float = DEFAULT_GROSS_MARGIN
    monthly_churn_pct: float = DEFAULT_MONTHLY_CHURN
    orders_per_active_month: float = DEFAULT_ORDERS_PER_ACTIVE_MONTH
    horizon_months: int = 12
    first_order_conversion: float = 0.29


@dataclass
class SimulationResult:
    cohort_ltv_inr: float
    ltv_cac_ratio: float
    payback_months: float
    monthly_contribution_inr: float
    annual_orders: int
    annual_revenue_inr: float
    monthly_cohort_df: pd.DataFrame


def simulate_ltv(inputs: UnitEconomicsInputs) -> SimulationResult:
    """Project cohort LTV over horizon with monthly churn decay."""
    margin_per_order = inputs.aov_inr * inputs.gross_margin_pct
    monthly_revenue_per_user = margin_per_order * inputs.orders_per_active_month

    cohort_size = inputs.monthly_new_users * inputs.first_order_conversion
    remaining = cohort_size
    total_margin = 0.0
    payback = None
    cumulative = 0.0
    rows = []

    for month in range(1, inputs.horizon_months + 1):
        month_margin = remaining * monthly_revenue_per_user
        total_margin += month_margin
        cumulative += month_margin
        if payback is None and cumulative >= cohort_size * inputs.cac_inr:
            payback = month
        rows.append(
            {
                "month": month,
                "active_users": round(remaining, 0),
                "contribution_inr": round(month_margin, 2),
                "cumulative_contribution_inr": round(cumulative, 2),
            }
        )
        remaining *= 1 - inputs.monthly_churn_pct

    ltv = total_margin / cohort_size if cohort_size else 0.0
    ltv_cac = ltv / inputs.cac_inr if inputs.cac_inr else 0.0

    annual_orders = int(SIMULATOR_ORDER_SCALE)
    annual_revenue = annual_orders * inputs.aov_inr

    return SimulationResult(
        cohort_ltv_inr=round(ltv, 2),
        ltv_cac_ratio=round(ltv_cac, 2),
        payback_months=payback or inputs.horizon_months,
        monthly_contribution_inr=round(monthly_revenue_per_user, 2),
        annual_orders=annual_orders,
        annual_revenue_inr=round(annual_revenue, 0),
        monthly_cohort_df=pd.DataFrame(rows),
    )


def sensitivity_grid(
    base: UnitEconomicsInputs,
    cac_range: tuple[float, float] = (120, 260),
    churn_range: tuple[float, float] = (0.25, 0.50),
    steps: int = 8,
) -> pd.DataFrame:
    """LTV/CAC heatmap inputs across CAC and churn."""
    cac_vals = np.linspace(cac_range[0], cac_range[1], steps)
    churn_vals = np.linspace(churn_range[0], churn_range[1], steps)
    rows = []
    for cac in cac_vals:
        for churn in churn_vals:
            inp = UnitEconomicsInputs(
                monthly_new_users=base.monthly_new_users,
                cac_inr=float(cac),
                aov_inr=base.aov_inr,
                gross_margin_pct=base.gross_margin_pct,
                monthly_churn_pct=float(churn),
                orders_per_active_month=base.orders_per_active_month,
                horizon_months=base.horizon_months,
                first_order_conversion=base.first_order_conversion,
            )
            res = simulate_ltv(inp)
            rows.append(
                {
                    "cac_inr": round(cac, 0),
                    "monthly_churn_pct": round(churn, 3),
                    "ltv_inr": res.cohort_ltv_inr,
                    "ltv_cac_ratio": res.ltv_cac_ratio,
                    "payback_months": res.payback_months,
                }
            )
    return pd.DataFrame(rows)


def scenario_comparison() -> pd.DataFrame:
    """Base vs experiment uplift scenarios."""
    base = UnitEconomicsInputs()
    scenarios = [
        ("base", base),
        ("exp03_cart_recovery", UnitEconomicsInputs(first_order_conversion=0.33)),
        ("exp04_d30_winback", UnitEconomicsInputs(monthly_churn_pct=0.32)),
        ("exp05_subscription", UnitEconomicsInputs(orders_per_active_month=3.1)),
        ("exp07_referral_cac", UnitEconomicsInputs(cac_inr=152)),
        ("combined_top3", UnitEconomicsInputs(
            first_order_conversion=0.33,
            monthly_churn_pct=0.32,
            orders_per_active_month=3.1,
            cac_inr=152,
        )),
    ]
    rows = []
    for name, inp in scenarios:
        res = simulate_ltv(inp)
        rows.append(
            {
                "scenario": name,
                "ltv_inr": res.cohort_ltv_inr,
                "ltv_cac_ratio": res.ltv_cac_ratio,
                "payback_months": res.payback_months,
                "annual_revenue_inr_cr": res.annual_revenue_inr / 1e7,
            }
        )
    return pd.DataFrame(rows)
