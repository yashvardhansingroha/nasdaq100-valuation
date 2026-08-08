"""ICE-scored growth experiment catalog."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Experiment:
    id: str
    name: str
    pillar: str
    hypothesis: str
    impact: int  # 1-10
    confidence: int  # 1-10
    ease: int  # 1-10
    primary_metric: str
    guardrail_metric: str
    effort_weeks: int

    @property
    def ice_score(self) -> float:
        return round((self.impact + self.confidence + self.ease) / 3, 2)


def experiment_catalog() -> list[Experiment]:
    """Eight prioritized growth experiments across trust, retention, and repeat purchase."""
    return [
        Experiment(
            id="EXP-01",
            name="Delivery ETA trust badge on PDP",
            pillar="trust",
            hypothesis="Showing real-time ETA + rider assignment on product pages reduces checkout anxiety and lifts first-order conversion by 8–12%.",
            impact=8,
            confidence=7,
            ease=6,
            primary_metric="install_to_first_order_rate",
            guardrail_metric="delivery_sla_breach_rate",
            effort_weeks=3,
        ),
        Experiment(
            id="EXP-02",
            name="Live rider photo + order tracking v2",
            pillar="trust",
            hypothesis="Post-checkout rider identity and live map reduce 'where is my order' support tickets and improve D7 retention by 5%.",
            impact=7,
            confidence=8,
            ease=5,
            primary_metric="d7_retention",
            guardrail_metric="csat_post_delivery",
            effort_weeks=4,
        ),
        Experiment(
            id="EXP-03",
            name="Abandoned cart push within 30 min",
            pillar="retention_recovery",
            hypothesis="Timely push with ₹50 off first order recovers 15% of cart abandoners who never completed checkout.",
            impact=9,
            confidence=7,
            ease=8,
            primary_metric="cart_to_payment_conversion",
            guardrail_metric="discount_burn_rate",
            effort_weeks=2,
        ),
        Experiment(
            id="EXP-04",
            name="D30 win-back offer for churned first-timers",
            pillar="retention_recovery",
            hypothesis="Segmented win-back (staples bundle at cost) lifts D30 repeat rate from 28% to 34% among one-and-done users.",
            impact=8,
            confidence=6,
            ease=7,
            primary_metric="d30_repeat_rate",
            guardrail_metric="contribution_margin",
            effort_weeks=3,
        ),
        Experiment(
            id="EXP-05",
            name="Staples subscription (weekly auto-reorder)",
            pillar="repeat_purchase",
            hypothesis="Subscribe-and-save on top 20 SKUs increases orders per active month from 2.4 to 3.1.",
            impact=9,
            confidence=6,
            ease=4,
            primary_metric="orders_per_active_month",
            guardrail_metric="inventory_waste_rate",
            effort_weeks=6,
        ),
        Experiment(
            id="EXP-06",
            name="One-tap reorder carousel on home",
            pillar="repeat_purchase",
            hypothesis="Surfacing last 5 purchased items with single-tap reorder lifts repeat purchase rate by 10%.",
            impact=7,
            confidence=8,
            ease=7,
            primary_metric="repeat_order_rate_14d",
            guardrail_metric="home_screen_load_time",
            effort_weeks=2,
        ),
        Experiment(
            id="EXP-07",
            name="Referral: give ₹100 / get ₹100 on first order",
            pillar="acquisition",
            hypothesis="Double-sided referral reduces blended CAC by 18% while maintaining first-order quality (AOV within 5% of paid).",
            impact=8,
            confidence=7,
            ease=6,
            primary_metric="blended_cac",
            guardrail_metric="referral_fraud_rate",
            effort_weeks=4,
        ),
        Experiment(
            id="EXP-08",
            name="City launch: hyperlocal dark-store pre-positioning",
            pillar="city_launch",
            hypothesis="Pre-stocking top 200 SKUs by micro-cluster before marketing spend improves launch-week first-order rate by 20%.",
            impact=9,
            confidence=7,
            ease=3,
            primary_metric="launch_week_first_order_rate",
            guardrail_metric="stockout_rate",
            effort_weeks=8,
        ),
    ]


def experiments_dataframe() -> pd.DataFrame:
    exps = experiment_catalog()
    return pd.DataFrame(
        [
            {
                "id": e.id,
                "name": e.name,
                "pillar": e.pillar,
                "hypothesis": e.hypothesis,
                "impact": e.impact,
                "confidence": e.confidence,
                "ease": e.ease,
                "ice_score": e.ice_score,
                "primary_metric": e.primary_metric,
                "guardrail_metric": e.guardrail_metric,
                "effort_weeks": e.effort_weeks,
            }
            for e in exps
        ]
    ).sort_values("ice_score", ascending=False)
