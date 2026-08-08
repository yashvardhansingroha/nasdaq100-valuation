"""Generate synthetic FirstClub order and funnel dataset (~1.2M orders)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from firstclub.config import (
    CITIES,
    DATA_DIR,
    ORDER_COUNT,
    OUTPUT_DIR,
    RANDOM_SEED,
)


def _rng() -> np.random.Generator:
    return np.random.default_rng(RANDOM_SEED)


def generate_orders(n: int = ORDER_COUNT) -> pd.DataFrame:
    """Create representative order-level dataset with funnel flags."""
    rng = _rng()
    start = datetime(2024, 1, 1)
    end = datetime(2025, 6, 30)
    days = (end - start).days

    user_ids = np.arange(1, int(n * 0.42) + 1)
    orders_per_user = rng.poisson(2.85, size=len(user_ids)) + 1
    orders_per_user = np.minimum(orders_per_user, 18)  # cap heavy users

    rows: list[dict] = []
    order_id = 1
    for uid, count in zip(user_ids, orders_per_user):
        install_day = rng.integers(0, days)
        install_ts = start + timedelta(days=int(install_day))
        city = rng.choice(CITIES, p=[0.28, 0.22, 0.20, 0.12, 0.10, 0.08])
        channel = rng.choice(
            ["paid_social", "referral", "organic", "influencer", "offline"],
            p=[0.35, 0.18, 0.28, 0.12, 0.07],
        )
        platform = rng.choice(["android", "ios"], p=[0.72, 0.28])

        # Funnel conversion with realistic drop-offs
        signup = rng.random() < 0.82
        location = signup and rng.random() < 0.91
        catalog = location and rng.random() < 0.88
        cart = catalog and rng.random() < 0.64
        checkout = cart and rng.random() < 0.78
        payment = checkout and rng.random() < 0.89
        delivered = payment and rng.random() < 0.96

        if not delivered:
            continue

        first_order_ts = install_ts + timedelta(hours=int(rng.integers(2, 96)))
        for i in range(count):
            if order_id > n:
                break
            order_ts = first_order_ts + timedelta(days=int(rng.integers(0, 120) * i / max(count, 1)))
            aov = float(np.clip(rng.normal(485, 140), 99, 2200))
            discount = float(rng.choice([0, 50, 75, 100, 150], p=[0.55, 0.15, 0.12, 0.10, 0.08]))
            rows.append(
                {
                    "order_id": order_id,
                    "user_id": int(uid),
                    "order_ts": order_ts,
                    "install_ts": install_ts,
                    "city": city,
                    "channel": channel,
                    "platform": platform,
                    "is_first_order": i == 0,
                    "aov_inr": round(aov - discount, 2),
                    "discount_inr": discount,
                    "delivery_minutes": int(np.clip(rng.normal(14, 5), 6, 45)),
                    "items_count": int(rng.integers(3, 22)),
                    "category": rng.choice(
                        ["staples", "snacks", "dairy", "produce", "personal_care", "household"],
                        p=[0.28, 0.18, 0.16, 0.14, 0.12, 0.12],
                    ),
                    "funnel_signup": signup,
                    "funnel_location": location,
                    "funnel_catalog": catalog,
                    "funnel_cart": cart,
                    "funnel_checkout": checkout,
                    "funnel_payment": payment,
                    "funnel_delivered": delivered,
                    "days_install_to_first_order": max(0, (first_order_ts - install_ts).days),
                    "retained_d7": rng.random() < (0.42 if i == 0 else 0.55),
                    "retained_d30": rng.random() < (0.28 if i == 0 else 0.48),
                }
            )
            order_id += 1
        if order_id > n:
            break

    df = pd.DataFrame(rows)
    if len(df) < n:
        # Pad with additional single-order users if needed
        extra = n - len(df)
        for j in range(extra):
            uid = len(user_ids) + j + 1
            install_ts = start + timedelta(days=int(rng.integers(0, days)))
            rows.append(
                {
                    "order_id": order_id + j,
                    "user_id": uid,
                    "order_ts": install_ts + timedelta(hours=12),
                    "install_ts": install_ts,
                    "city": rng.choice(CITIES),
                    "channel": "organic",
                    "platform": "android",
                    "is_first_order": True,
                    "aov_inr": 420.0,
                    "discount_inr": 0,
                    "delivery_minutes": 13,
                    "items_count": 8,
                    "category": "staples",
                    "funnel_signup": True,
                    "funnel_location": True,
                    "funnel_catalog": True,
                    "funnel_cart": True,
                    "funnel_checkout": True,
                    "funnel_payment": True,
                    "funnel_delivered": True,
                    "days_install_to_first_order": 0,
                    "retained_d7": False,
                    "retained_d30": False,
                }
            )
        df = pd.DataFrame(rows)

    return df.head(n)


def generate_app_store_reviews(n: int = 2400) -> pd.DataFrame:
    """Synthetic App Store / Play Store review corpus aligned to funnel pain points."""
    rng = _rng()
    themes = {
        "delivery_speed": (0.22, 3.8, ["fast delivery", "10 min promise", "late order", "delayed"]),
        "product_freshness": (0.18, 4.1, ["fresh vegetables", "expired", "quality", "damaged"]),
        "pricing_value": (0.15, 3.5, ["expensive", "good deals", "discount", "overpriced"]),
        "app_ux": (0.14, 3.2, ["crash", "slow app", "easy to use", "search broken"]),
        "trust_safety": (0.12, 3.0, ["wrong items", "rider behavior", "refund", "trust"]),
        "selection": (0.10, 3.9, ["out of stock", "variety", "brands", "limited"]),
        "support": (0.09, 2.8, ["customer care", "no response", "resolved quickly", "chat"]),
    }
    rows = []
    for i in range(n):
        theme = rng.choice(list(themes.keys()), p=[v[0] for v in themes.values()])
        base_rating, keywords = themes[theme][1], themes[theme][2]
        rating = int(np.clip(round(rng.normal(base_rating, 1.1)), 1, 5))
        platform = rng.choice(["google_play", "app_store"], p=[0.68, 0.32])
        rows.append(
            {
                "review_id": i + 1,
                "platform": platform,
                "rating": rating,
                "theme": theme,
                "keyword": rng.choice(keywords),
                "city": rng.choice(CITIES),
                "review_date": datetime(2024, 6, 1) + timedelta(days=int(rng.integers(0, 400))),
                "sentiment": "positive" if rating >= 4 else ("negative" if rating <= 2 else "neutral"),
            }
        )
    return pd.DataFrame(rows)


def save_datasets(force: bool = False) -> dict[str, Path]:
    """Write parquet datasets to data/ and summary JSON to output/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    orders_path = DATA_DIR / "orders.parquet"
    reviews_path = DATA_DIR / "app_reviews.parquet"

    if force or not orders_path.exists():
        orders = generate_orders()
        orders.to_parquet(orders_path, index=False)
    else:
        orders = pd.read_parquet(orders_path)

    if force or not reviews_path.exists():
        reviews = generate_app_store_reviews()
        reviews.to_parquet(reviews_path, index=False)
    else:
        reviews = pd.read_parquet(reviews_path)

    summary = {
        "order_count": len(orders),
        "unique_users": int(orders["user_id"].nunique()),
        "first_order_rate": float(orders.groupby("user_id")["is_first_order"].any().mean()),
        "avg_aov_inr": float(orders["aov_inr"].mean()),
        "avg_delivery_min": float(orders["delivery_minutes"].mean()),
        "d7_retention": float(orders.loc[orders["is_first_order"], "retained_d7"].mean()),
        "d30_retention": float(orders.loc[orders["is_first_order"], "retained_d30"].mean()),
        "review_count": len(reviews),
        "avg_rating": float(reviews["rating"].mean()),
    }
    summary_path = OUTPUT_DIR / "dataset_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {"orders": orders_path, "reviews": reviews_path, "summary": summary_path}


if __name__ == "__main__":
    paths = save_datasets(force=True)
    print("Wrote:", {k: str(v) for k, v in paths.items()})
