# Lending Club Credit Risk Pipeline

End-to-end retail credit risk stack: PostgreSQL ETL on ~2.2M Lending Club loans, stratified logistic PD model, WOE/IV application scorecard, PSI monitoring, risk-adjusted pricing, IFRS 9 ECL with stress scenarios, and Power BI DAX measures.

## Prerequisites

1. **PostgreSQL** running locally on port `5432`
2. Create the database:

```sql
CREATE DATABASE mn_analytics_db;
```

3. **CSV** — Lending Club `accepted_2007_to_2018Q4.csv.gz` (default: `C:\Users\ysing\Downloads\accepted_2007_to_2018Q4.csv.gz`)
4. Set credentials in the **repo root** `.env`:

```env
CREDIT_RISK_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/mn_analytics_db
CREDIT_RISK_CSV_PATH=C:\Users\ysing\Downloads\accepted_2007_to_2018Q4.csv.gz
```

5. Install dependencies (from this folder):

```bash
pip install -r requirements.txt
```

## Run order

```bash
cd credit_risk

# Step 1 — bulk load (~2.2M rows; several minutes)
python 1_data_ingestion.py

# Step 2 — create analytical views
psql -U postgres -d mn_analytics_db -f 2_etl_pipeline.sql
# Or run 2_etl_pipeline.sql in pgAdmin / a SQL extension

# Step 3 — PD model + WOE scorecard + base ECL export
python 3_ml_risk_model.py

# Step 4 — PSI, pricing adequacy, stress testing
python 5_portfolio_analytics.py
```

## Expected outputs (approximate — latest run)

```
ROC-AUC Score: 0.71
F1 Score: 0.42 (F1-optimized threshold)
Gini Coefficient: 0.41
KS Statistic: 0.30
Portfolio ECL: ~$5.6B (~29% of exposure with balanced PD / 60% LGD)
```

Resume targets of ~0.74 AUC / ~0.65 F1 are stretch goals; current logistic baseline with these features typically lands near **0.70–0.71 AUC**. Further gains usually need more underwriting fields (e.g. FICO) or a non-linear challenger model.

Artifacts land in `output/`:

| File | Description |
|------|-------------|
| `powerbi_scored_loan_data.csv` | Scored book for Power BI (PD, ECL, score, pricing flags) |
| `model_metrics.json` | AUC, F1, Gini, KS, ECL, PSI, stress summary |
| `woe_iv_summary.csv` | WOE bins and IV contributions |
| `scorecard_points.csv` | Points lookup table |
| `stress_test_results.csv` | Base / adverse / severe / recession ECL |
| `pricing_by_grade.csv` | Spread vs expected loss by grade |
| `ecl_by_grade.csv` | Portfolio ECL concentration by grade |

## Power BI

1. Import `output/powerbi_scored_loan_data.csv`
2. Optionally import `output/stress_test_results.csv`
3. Copy measures from [`4_powerbi_dax.txt`](4_powerbi_dax.txt)

## Finance pack

| File | Purpose |
|------|---------|
| [`reports/RISK_MEMO.md`](reports/RISK_MEMO.md) | Credit risk / IFRS 9 memo |
| [`reports/INTERVIEW_PREP.md`](reports/INTERVIEW_PREP.md) | 60-sec pitch, Q&A, resume bullets |

## Project layout

```
credit_risk/
├── 1_data_ingestion.py
├── 2_etl_pipeline.sql
├── 3_ml_risk_model.py
├── 4_powerbi_dax.txt
├── 5_portfolio_analytics.py
├── scorecard.py
├── config.py
├── requirements.txt
├── output/
└── reports/
```

## Notes

- Target resume metrics (~0.74 ROC-AUC, ~0.65 F1) depend on data slice and sklearn version; stratified split + `class_weight='balanced'` is the intended path.
- LGD is fixed at **60%** (conservative unsecured consumer assumption) in `config.py`.
- Stress scenarios are **illustrative**, not regulatory ICAAP/CCAR packs.
