"""Install-to-first-order funnel conversion analysis."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from firstclub.config import FUNNEL_STAGES


@dataclass
class FunnelStep:
    stage: str
    users: int
    conversion_from_previous: float
    conversion_from_install: float


def compute_funnel(orders: pd.DataFrame) -> pd.DataFrame:
    """Compute funnel conversion from first-order cohort."""
    first = orders.loc[orders["is_first_order"]].drop_duplicates("user_id")
    n_install = len(first)

    stage_cols = {
        "install": pd.Series(True, index=first.index),
        "signup": first["funnel_signup"],
        "location_set": first["funnel_location"],
        "catalog_view": first["funnel_catalog"],
        "cart_add": first["funnel_cart"],
        "checkout_start": first["funnel_checkout"],
        "payment_success": first["funnel_payment"],
        "first_order_delivered": first["funnel_delivered"],
    }

    rows = []
    prev_count = n_install
    for stage in FUNNEL_STAGES:
        mask = stage_cols[stage]
        count = int(mask.sum())
        conv_prev = count / prev_count if prev_count else 0.0
        conv_install = count / n_install if n_install else 0.0
        rows.append(
            {
                "stage": stage,
                "users": count,
                "conversion_from_previous": round(conv_prev, 4),
                "conversion_from_install": round(conv_install, 4),
                "drop_off_from_previous": round(1 - conv_prev, 4),
            }
        )
        prev_count = count

    return pd.DataFrame(rows)


def funnel_by_dimension(orders: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Funnel first-order delivery rate by city, channel, or platform."""
    first = orders.loc[orders["is_first_order"]].drop_duplicates("user_id")
    grouped = (
        first.groupby(dimension)
        .agg(
            installs=("user_id", "count"),
            first_orders=("funnel_delivered", "sum"),
            avg_days_to_order=("days_install_to_first_order", "mean"),
            d7_retention=("retained_d7", "mean"),
            d30_retention=("retained_d30", "mean"),
        )
        .reset_index()
    )
    grouped["first_order_rate"] = grouped["first_orders"] / grouped["installs"]
    return grouped.sort_values("first_order_rate", ascending=False)


def identify_acquisition_gaps(funnel_df: pd.DataFrame) -> list[dict]:
    """Surface largest relative drop-offs for prioritization."""
    gaps = []
    for _, row in funnel_df.iterrows():
        if row["stage"] == "install":
            continue
        gaps.append(
            {
                "stage": row["stage"],
                "drop_off_pct": row["drop_off_from_previous"] * 100,
                "users_lost": int(funnel_df.loc[funnel_df["stage"] == "install", "users"].iloc[0]
                                  - row["users"]),
            }
        )
    gaps.sort(key=lambda x: x["drop_off_pct"], reverse=True)
    return gaps
