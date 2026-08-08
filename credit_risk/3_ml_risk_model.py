"""Train PD model, build WOE scorecard, compute IFRS 9 ECL, export for Power BI."""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

import config
from scorecard import (
    apply_scorecard,
    build_scorecard,
    score_decile_default_rates,
)


def _parse_percent(series: pd.Series) -> pd.Series:
    """Handle revol_util style values that may arrive as '12.5%' strings."""
    if series.dtype == object:
        cleaned = series.astype(str).str.replace("%", "", regex=False)
        return pd.to_numeric(cleaned, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def _ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(np.max(np.abs(tpr - fpr)))


def _best_f1_threshold(y_true: np.ndarray, y_score: np.ndarray) -> tuple[float, float]:
    """Scan thresholds to maximize F1 for the default class."""
    best_t, best_f1 = 0.5, 0.0
    for t in np.linspace(0.05, 0.95, 91):
        pred = (y_score >= t).astype(int)
        score = f1_score(y_true, pred, zero_division=0)
        if score > best_f1:
            best_f1, best_t = float(score), float(t)
    return best_t, best_f1


def main() -> None:
    if "YOUR_PASSWORD" in config.DATABASE_URL:
        print(
            "ERROR: Set CREDIT_RISK_DATABASE_URL in the repo root .env "
            "(replace YOUR_PASSWORD with your PostgreSQL password)."
        )
        sys.exit(1)

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch clean data from PostgreSQL
    print("Fetching vw_clean_loan_data from PostgreSQL...")
    engine = create_engine(config.DATABASE_URL)
    query = "SELECT * FROM vw_clean_loan_data WHERE default_flag IS NOT NULL"
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df):,} closed loans with defined default outcomes.")

    # Light dtype hygiene
    if "revol_util" in df.columns:
        df["revol_util"] = _parse_percent(df["revol_util"])
    if "int_rate" in df.columns:
        df["int_rate"] = _parse_percent(df["int_rate"])

    # 2. Preprocessing & outlier treatment (IQR on annual income)
    q1 = df["annual_inc"].quantile(0.25)
    q3 = df["annual_inc"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr
    df["annual_inc"] = np.where(df["annual_inc"] > upper_bound, upper_bound, df["annual_inc"])

    df.fillna(df.median(numeric_only=True), inplace=True)

    # Keep a copy of original analytic columns for export
    export_cols = [
        c
        for c in [
            "id",
            "loan_amnt",
            "int_rate",
            "installment",
            "grade",
            "home_ownership",
            "verification_status",
            "annual_inc",
            "dti",
            "purpose",
            "revol_util",
            "revol_bal",
            "total_acc",
            "open_acc",
            "pub_rec",
            "delinq_2yrs",
            "mort_acc",
            "default_flag",
            "emp_length_years",
            "term_months",
            "vintage_year",
        ]
        if c in df.columns
    ]
    df_export = df[export_cols].copy()

    # Dummy encode categoricals
    cat_cols = [
        c
        for c in ["grade", "purpose", "home_ownership", "verification_status"]
        if c in df.columns
    ]
    df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    features = [c for c in df_encoded.columns if c not in ["id", "default_flag", "issue_d"]]
    # Drop non-numeric leftovers if any
    X = df_encoded[features].select_dtypes(include=[np.number]).copy()
    y = df_encoded["default_flag"].astype(int)

    # 3. Stratified train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.TEST_SIZE,
        stratify=y,
        random_state=config.RANDOM_STATE,
    )
    train_idx = X_train.index
    test_idx = X_test.index

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 4. Train logistic regression PD model
    model = LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        solver="lbfgs",
        C=0.5,
    )
    model.fit(X_train_scaled, y_train)

    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    best_threshold, _ = _best_f1_threshold(y_test.to_numpy(), y_pred_proba)
    y_pred = (y_pred_proba >= best_threshold).astype(int)

    roc_auc = roc_auc_score(y_test, y_pred_proba)
    f1 = f1_score(y_test, y_pred)
    gini = 2 * roc_auc - 1
    ks = _ks_statistic(y_test.to_numpy(), y_pred_proba)

    print(f"ROC-AUC Score: {roc_auc:.2f}")
    print(f"F1 Score: {f1:.2f} (threshold={best_threshold:.2f})")
    print(f"Gini Coefficient: {gini:.2f}")
    print(f"KS Statistic: {ks:.2f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # 5. WOE / IV application scorecard (fit on train only)
    print("\n--- Scorecard ---")
    scorecard_feats = [f for f in config.SCORECARD_FEATURES if f in X.columns]
    sc_result = build_scorecard(X_train[scorecard_feats], y_train, features=scorecard_feats)
    if not sc_result.feature_iv.empty:
        top = sc_result.feature_iv.head(3)
        top_str = ", ".join(f"{r.feature} ({r.iv:.2f})" for r in top.itertuples())
        print(f"Top IV features: {top_str}")

    app_scores_all = apply_scorecard(X[scorecard_feats], sc_result)
    print(
        f"Application score range: "
        f"{int(app_scores_all.min())}–{int(app_scores_all.max())}"
    )

    sc_result.woe_iv_summary.to_csv(config.OUTPUT_DIR / "woe_iv_summary.csv", index=False)
    sc_result.scorecard_points.to_csv(config.OUTPUT_DIR / "scorecard_points.csv", index=False)

    # Dual-model validation: scorecard vs PD deciles on test set
    test_scores = app_scores_all.loc[test_idx]
    test_pd = pd.Series(y_pred_proba, index=test_idx)
    score_deciles = score_decile_default_rates(test_scores, y_test)
    pd_deciles = score_decile_default_rates((-test_pd), y_test)  # negate so high = safer
    score_deciles.to_csv(config.OUTPUT_DIR / "scorecard_decile_defaults.csv", index=False)
    pd_deciles.to_csv(config.OUTPUT_DIR / "pd_decile_defaults.csv", index=False)
    print("Scorecard / PD decile default tables exported.")

    # 6. Score entire portfolio + IFRS 9 ECL
    X_all_scaled = scaler.transform(X)
    pd_all = model.predict_proba(X_all_scaled)[:, 1]
    pred_all = (pd_all >= best_threshold).astype(int)

    df_export["probability_of_default"] = pd_all
    df_export["predicted_default"] = pred_all
    df_export["decision_threshold"] = best_threshold
    df_export["expected_loss"] = (
        df_export["probability_of_default"] * config.LGD * df_export["loan_amnt"]
    )
    df_export["application_score"] = app_scores_all.values
    df_export["split"] = "train"
    df_export.loc[test_idx, "split"] = "test"

    total_ecl = float(df_export["expected_loss"].sum())
    total_exposure = float(df_export["loan_amnt"].sum())
    ecl_pct = total_ecl / total_exposure if total_exposure else 0.0

    print(f"\nPortfolio ECL: ${total_ecl / 1e6:.1f}M ({ecl_pct:.1%} of exposure)")
    if "grade" in df_export.columns:
        ecl_by_grade = (
            df_export.groupby("grade", as_index=False)
            .agg(
                exposure=("loan_amnt", "sum"),
                ecl=("expected_loss", "sum"),
                avg_pd=("probability_of_default", "mean"),
            )
            .assign(ecl_pct=lambda d: d["ecl"] / d["exposure"])
            .sort_values("grade")
        )
        print("\nECL by grade:")
        print(ecl_by_grade.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
        ecl_by_grade.to_csv(config.OUTPUT_DIR / "ecl_by_grade.csv", index=False)

    scored_path = config.OUTPUT_DIR / "powerbi_scored_loan_data.csv"
    df_export.to_csv(scored_path, index=False)
    print(f"\nScored dataset exported: {scored_path}")

    metrics = {
        "roc_auc": round(roc_auc, 4),
        "f1": round(f1, 4),
        "decision_threshold": round(best_threshold, 4),
        "gini": round(gini, 4),
        "ks": round(ks, 4),
        "n_loans": int(len(df_export)),
        "portfolio_ecl": round(total_ecl, 2),
        "portfolio_exposure": round(total_exposure, 2),
        "ecl_coverage_ratio": round(ecl_pct, 6),
        "lgd": config.LGD,
        "feature_iv": sc_result.feature_iv.to_dict(orient="records"),
        "train_size": int(len(train_idx)),
        "test_size": int(len(test_idx)),
    }
    metrics_path = config.OUTPUT_DIR / "model_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Model metrics written: {metrics_path}")


if __name__ == "__main__":
    main()
