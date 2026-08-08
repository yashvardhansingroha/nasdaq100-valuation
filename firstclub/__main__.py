"""CLI entry point for FirstClub funnel analysis pipeline."""

from __future__ import annotations

import argparse
import json

from firstclub.cac_ltv_simulator import scenario_comparison, simulate_ltv, UnitEconomicsInputs
from firstclub.competitive import competitive_benchmarks, gap_vs_competitors
from firstclub.config import OUTPUT_DIR
from firstclub.experiments import experiments_dataframe
from firstclub.funnel_analysis import compute_funnel, funnel_by_dimension, identify_acquisition_gaps
from firstclub.generate_data import save_datasets
from firstclub.review_synthesis import review_theme_summary, trust_gap_signals

import pandas as pd


def run_pipeline(force: bool = False) -> None:
    paths = save_datasets(force=force)
    orders = pd.read_parquet(paths["orders"])
    reviews = pd.read_parquet(paths["reviews"])

    funnel = compute_funnel(orders)
    gaps = identify_acquisition_gaps(funnel)
    by_city = funnel_by_dimension(orders, "city")
    by_channel = funnel_by_dimension(orders, "channel")
    themes = review_theme_summary(reviews)
    trust = trust_gap_signals(reviews)
    benchmarks = competitive_benchmarks()
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    comp_gaps = gap_vs_competitors(summary)
    experiments = experiments_dataframe()
    ltv = simulate_ltv(UnitEconomicsInputs())
    scenarios = scenario_comparison()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    funnel.to_csv(OUTPUT_DIR / "funnel_conversion.csv", index=False)
    by_city.to_csv(OUTPUT_DIR / "funnel_by_city.csv", index=False)
    by_channel.to_csv(OUTPUT_DIR / "funnel_by_channel.csv", index=False)
    themes.to_csv(OUTPUT_DIR / "review_themes.csv", index=False)
    benchmarks.to_csv(OUTPUT_DIR / "competitive_benchmarks.csv", index=False)
    comp_gaps.to_csv(OUTPUT_DIR / "competitive_gaps.csv", index=False)
    experiments.to_csv(OUTPUT_DIR / "experiments_ice.csv", index=False)
    scenarios.to_csv(OUTPUT_DIR / "ltv_scenarios.csv", index=False)
    ltv.monthly_cohort_df.to_csv(OUTPUT_DIR / "ltv_cohort_curve.csv", index=False)

    report = {
        "top_funnel_gaps": gaps[:3],
        "trust_gaps": trust,
        "ltv_cac_ratio": ltv.ltv_cac_ratio,
        "payback_months": ltv.payback_months,
        "experiment_count": len(experiments),
    }
    (OUTPUT_DIR / "pipeline_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Pipeline complete. Outputs in {OUTPUT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="FirstClub funnel teardown pipeline")
    parser.add_argument("--force", action="store_true", help="Regenerate synthetic datasets")
    args = parser.parse_args()
    run_pipeline(force=args.force)


if __name__ == "__main__":
    main()
