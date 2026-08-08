"""Tests for FirstClub funnel teardown package."""

from __future__ import annotations

import pandas as pd

from firstclub.cac_ltv_simulator import UnitEconomicsInputs, scenario_comparison, simulate_ltv
from firstclub.competitive import competitive_benchmarks, gap_vs_competitors
from firstclub.experiments import experiment_catalog, experiments_dataframe
from firstclub.funnel_analysis import compute_funnel, identify_acquisition_gaps
from firstclub.generate_data import generate_app_store_reviews, generate_orders


def test_generate_orders_shape():
    df = generate_orders(n=5000)
    assert len(df) <= 5000
    assert "order_id" in df.columns
    assert "is_first_order" in df.columns
    assert df["aov_inr"].min() > 0


def test_generate_reviews():
    df = generate_app_store_reviews(n=100)
    assert len(df) == 100
    assert set(df["sentiment"].unique()).issubset({"positive", "negative", "neutral"})


def test_funnel_monotonic():
    orders = generate_orders(n=3000)
    funnel = compute_funnel(orders)
    users = funnel["users"].tolist()
    assert users == sorted(users, reverse=True)
    gaps = identify_acquisition_gaps(funnel)
    assert len(gaps) >= 1


def test_experiments_ice_count():
    exps = experiment_catalog()
    assert len(exps) == 8
    df = experiments_dataframe()
    assert df["ice_score"].max() <= 10


def test_ltv_simulator_positive():
    result = simulate_ltv(UnitEconomicsInputs())
    assert result.cohort_ltv_inr > 0
    assert result.annual_orders == 1_000_000


def test_scenario_comparison():
    scenarios = scenario_comparison()
    assert len(scenarios) >= 4
    assert "ltv_cac_ratio" in scenarios.columns


def test_competitive_benchmarks():
    bench = competitive_benchmarks()
    assert "FirstClub" in bench["competitor"].values
    gaps = gap_vs_competitors({"first_order_rate": 0.29, "d7_retention": 0.42})
    assert len(gaps) >= 5
