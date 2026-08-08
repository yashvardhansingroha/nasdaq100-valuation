"""PSI monitoring, risk-adjusted pricing, and IFRS 9 stress testing."""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

import config


def _psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index using expected (train) quantile edges."""
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if len(expected) == 0 or len(actual) == 0:
        return float("nan")

    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        lo, hi = float(np.min(expected)), float(np.max(expected))
        edges = np.linspace(lo, hi + 1e-9, bins + 1)

    exp_counts, _ = np.histogram(expected, bins=edges)
    act_counts, _ = np.histogram(actual, bins=edges)

    exp_pct = exp_counts / max(exp_counts.sum(), 1)
    act_pct = act_counts / max(act_counts.sum(), 1)

    # Avoid zeros for log
    exp_pct = np.clip(exp_pct, 1e-6, None)
    act_pct = np.clip(act_pct, 1e-6, None)
    # renormalize after clip
    exp_pct = exp_pct / exp_pct.sum()
    act_pct = act_pct / act_pct.sum()

    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def _psi_label(psi: float) -> str:
    if np.isnan(psi):
        return "n/a"
    if psi < config.PSI_THRESHOLDS["stable"]:
        return "stable"
    if psi < config.PSI_THRESHOLDS["moderate"]:
        return "moderate"
    return "significant"


def _psi_categorical(expected: pd.Series, actual: pd.Series) -> float:
    cats = sorted(set(expected.dropna().unique()) | set(actual.dropna().unique()))
    if not cats:
        return float("nan")
    exp_pct = expected.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    act_pct = actual.value_counts(normalize=True).reindex(cats, fill_value=0).to_numpy()
    exp_pct = np.clip(exp_pct, 1e-6, None)
    act_pct = np.clip(act_pct, 1e-6, None)
    exp_pct = exp_pct / exp_pct.sum()
    act_pct = act_pct / act_pct.sum()
    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def compute_psi(df: pd.DataFrame) -> dict:
    train = df[df["split"] == "train"]
    test = df[df["split"] == "test"]
    if train.empty or test.empty:
        print("WARNING: split column missing or empty — PSI skipped.")
        return {}

    score_psi = _psi(
        train["probability_of_default"].to_numpy(dtype=float),
        test["probability_of_default"].to_numpy(dtype=float),
    )
    dti_psi = _psi(
        train["dti"].to_numpy(dtype=float),
        test["dti"].to_numpy(dtype=float),
    )
    grade_psi = _psi_categorical(train["grade"], test["grade"]) if "grade" in df.columns else float("nan")

    results = {
        "score_psi": round(score_psi, 4),
        "score_psi_label": _psi_label(score_psi),
        "dti_psi": round(dti_psi, 4),
        "dti_psi_label": _psi_label(dti_psi),
        "grade_psi": round(grade_psi, 4) if not np.isnan(grade_psi) else None,
        "grade_psi_label": _psi_label(grade_psi),
    }

    print("\n--- PSI (train vs test) ---")
    print(f"Score PSI: {results['score_psi']:.4f} ({results['score_psi_label']})")
    print(f"DTI PSI: {results['dti_psi']:.4f} ({results['dti_psi_label']})")
    if results["grade_psi"] is not None:
        print(f"Grade mix PSI: {results['grade_psi']:.4f} ({results['grade_psi_label']})")
    return results


def risk_adjusted_pricing(df: pd.DataFrame) -> pd.DataFrame:
    """Compare contractual rate to grade benchmark and model expected loss."""
    out = df.copy()

    # Exposure-weighted average int_rate by grade
    def wavg(g: pd.DataFrame) -> float:
        w = g["loan_amnt"].to_numpy(dtype=float)
        r = g["int_rate"].to_numpy(dtype=float)
        # int_rate may be percent (12.5) or fraction (0.125)
        if np.nanmedian(r) > 1.0:
            r = r / 100.0
        return float(np.average(r, weights=w)) if w.sum() else float("nan")

    benchmarks = {
        grade: wavg(g) for grade, g in out.groupby("grade", sort=False)
    }
    out["benchmark_rate"] = out["grade"].map(benchmarks)

    int_rate = out["int_rate"].to_numpy(dtype=float)
    if np.nanmedian(int_rate) > 1.0:
        int_rate = int_rate / 100.0
    out["int_rate_decimal"] = int_rate

    out["risk_spread"] = out["int_rate_decimal"] - out["benchmark_rate"]
    out["expected_loss_rate"] = out["probability_of_default"] * config.LGD
    # Economic margin proxy: contractual yield vs modeled expected loss
    out["pricing_adequacy"] = out["int_rate_decimal"] - out["expected_loss_rate"]

    median_pd = out["probability_of_default"].median()
    out["underpriced_flag"] = (
        (out["pricing_adequacy"] < 0) & (out["probability_of_default"] > median_pd)
    ).astype(int)

    under_exp = out.loc[out["underpriced_flag"] == 1, "loan_amnt"].sum()
    total_exp = out["loan_amnt"].sum()
    print("\n--- Pricing ---")
    print(
        f"Underpriced exposure: {under_exp / total_exp:.1%} of portfolio "
        f"(${under_exp / 1e6:.1f}M)"
    )

    by_grade = (
        out.groupby("grade", as_index=False)
        .agg(
            avg_risk_spread=("risk_spread", "mean"),
            avg_pd=("probability_of_default", "mean"),
            avg_pricing_adequacy=("pricing_adequacy", "mean"),
            underpriced_share=("underpriced_flag", "mean"),
            exposure=("loan_amnt", "sum"),
        )
        .sort_values("grade")
    )
    print("Avg pricing adequacy by grade:")
    for row in by_grade.itertuples():
        print(
            f"  {row.grade}: adequacy={row.avg_pricing_adequacy:+.1%}, "
            f"spread={row.avg_risk_spread:+.1%}, PD={row.avg_pd:.1%}"
        )
    by_grade.to_csv(config.OUTPUT_DIR / "pricing_by_grade.csv", index=False)
    return out


def stress_test(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute portfolio ECL under config stress scenarios."""
    base_ecl = float((df["probability_of_default"] * config.LGD * df["loan_amnt"]).sum())
    total_exposure = float(df["loan_amnt"].sum())
    rows = []

    print("\n--- Stress Test ---")
    for name, params in config.STRESS_SCENARIOS.items():
        stressed_pd = np.minimum(
            df["probability_of_default"] * params["pd_multiplier"] + params["pd_additive"],
            0.99,
        )
        stressed_ecl = float((stressed_pd * config.LGD * df["loan_amnt"]).sum())
        delta = stressed_ecl - base_ecl
        delta_pct = delta / base_ecl if base_ecl else 0.0
        coverage = stressed_ecl / total_exposure if total_exposure else 0.0
        rows.append(
            {
                "scenario": name,
                "pd_multiplier": params["pd_multiplier"],
                "pd_additive": params["pd_additive"],
                "total_ecl": round(stressed_ecl, 2),
                "ecl_pct_of_exposure": round(coverage, 6),
                "delta_vs_base": round(delta, 2),
                "delta_pct_vs_base": round(delta_pct, 6),
            }
        )
        tag = ""
        if name != "base":
            tag = f" ({delta_pct:+.0%} vs base)"
        print(f"{name.capitalize():10s} ECL: ${stressed_ecl / 1e6:.1f}M{tag}")

    result = pd.DataFrame(rows)
    out_path = config.OUTPUT_DIR / "stress_test_results.csv"
    result.to_csv(out_path, index=False)
    print(f"Stress results exported: {out_path}")
    return result


def main() -> None:
    scored_path = config.OUTPUT_DIR / "powerbi_scored_loan_data.csv"
    if not scored_path.exists():
        print(f"ERROR: {scored_path} not found. Run 3_ml_risk_model.py first.")
        sys.exit(1)

    print(f"Loading scored portfolio from {scored_path}...")
    df = pd.read_csv(scored_path, low_memory=False)
    print(f"Loaded {len(df):,} loans.")

    psi_results = compute_psi(df)
    df = risk_adjusted_pricing(df)
    stress_df = stress_test(df)

    # Persist enriched scored file for Power BI
    drop_cols = [c for c in ["int_rate_decimal"] if c in df.columns]
    df.drop(columns=drop_cols, inplace=True, errors="ignore")
    df.to_csv(scored_path, index=False)
    print(f"\nUpdated scored dataset with pricing columns: {scored_path}")

    # Merge analytics into model_metrics.json
    metrics_path = config.OUTPUT_DIR / "model_metrics.json"
    metrics = {}
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["psi"] = psi_results
    metrics["stress_test"] = stress_df.to_dict(orient="records")
    under_exp = float(df.loc[df["underpriced_flag"] == 1, "loan_amnt"].sum())
    total_exp = float(df["loan_amnt"].sum())
    metrics["underpriced_exposure"] = round(under_exp, 2)
    metrics["underpriced_exposure_pct"] = round(under_exp / total_exp, 6) if total_exp else 0.0
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Updated metrics: {metrics_path}")


if __name__ == "__main__":
    main()
