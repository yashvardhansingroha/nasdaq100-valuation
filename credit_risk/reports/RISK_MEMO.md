# Credit Risk Memo — Lending Club PD / ECL Case Study

**Vertical:** Retail credit risk / IFRS 9 expected credit loss  
**Universe:** Lending Club accepted loans (closed outcomes: Fully Paid / Charged Off / Default)  
**Stack:** PostgreSQL ETL → stratified logistic PD → WOE/IV scorecard → PSI → pricing adequacy → stress ECL → Power BI

---

## 1. Problem framing

Unsecured consumer lending requires three linked answers: (1) which applicants are more likely to default (**PD**), (2) how much of the book is at risk in dollar terms (**ECL**), and (3) whether contractual pricing compensates for that risk. This case study builds that chain on ~2.2M Lending Club loans and packages the outputs for a portfolio dashboard.

## 2. IFRS 9 lens

| Component | Definition in this project | Assumption / source |
|-----------|----------------------------|---------------------|
| **PD** | Model probability of default | Logistic regression with `class_weight='balanced'` |
| **LGD** | Loss given default | **60%** fixed (conservative unsecured consumer) |
| **EAD** | Exposure at default | `loan_amnt` at origination |
| **ECL** | Expected credit loss | `PD × LGD × EAD` per loan |

This is a **Stage-style loss estimate** for illustration — not a full lifetime ECL engine with prepayment, recovery timing, or SICR staging.

## 3. Model summary

- **Target:** `default_flag` = 1 if Charged Off / Default; 0 if Fully Paid (current loans excluded).
- **Features:** amount, rate, installment, income, DTI, revol util, accounts, employment length, term, grade & purpose dummies.
- **Preprocessing:** IQR cap on `annual_inc`; median imputation; standardized features.
- **Validation design:** 70/30 **stratified** train-test split (`random_state=42`) so default prevalence is preserved in both folds.
- **Headline metrics (target / typical):** ROC-AUC ~**0.74**, F1 ~**0.65**, Gini = 2×AUC−1, KS on the score distribution.

**Interpretation:** 0.74 AUC means useful **rank-ordering** for underwriting and portfolio sorting — not a claim that every predicted default will realize.

## 4. Application scorecard (WOE / IV)

Alongside the logistic PD, a classic retail scorecard bins continuous drivers (`dti`, `annual_inc`, `revol_util`, `emp_length_years`, `term_months`), computes **Weight of Evidence** per bin, and rolls **Information Value** to rank predictors.

- High IV → stronger separation of goods vs bads (watch IV > 0.3 for instability / overfit).
- WOE points are scaled to a FICO-style **application score (300–850)** for interview-friendly walkthroughs.
- Decile default rates on the test fold should be roughly monotonic: worse scores → higher observed default rates.

## 5. Model stability (PSI)

**Population Stability Index** compares train vs test distributions of model PD, DTI, and grade mix.

| PSI | Reading |
|-----|---------|
| < 0.10 | Stable |
| 0.10–0.25 | Moderate shift — investigate |
| > 0.25 | Significant drift — retrain / recalibrate |

Random stratified splits usually land in the stable band; PSI still demonstrates the **monitoring** language used in production credit models.

## 6. Pricing economics

For each loan:

- `benchmark_rate` = exposure-weighted average `int_rate` within Lending Club **grade**
- `risk_spread` = loan rate − grade benchmark
- `expected_loss_rate` = PD × LGD
- `pricing_adequacy` = risk_spread − expected_loss_rate

Loans with **negative adequacy** and **above-median PD** are flagged `underpriced_flag = 1`. This is a simplified economic margin proxy (no funding cost, opex, or NIM), but it supports the interview question: *“Where is the book not paid for the risk?”*

## 7. Stress testing

| Scenario | Shock | Purpose |
|----------|-------|---------|
| Base | none | Current ECL |
| Adverse | PD × 1.5 | Moderate downturn |
| Severe | PD × 2.0 | Deep recession |
| Recession | PD + 5pp | Absolute regulatory-style shift |

Stressed ECL = `min(PD×m + a, 0.99) × LGD × EAD`. Deltas vs base frame **capital / reserve buffer** conversations without claiming CCAR/ICAAP compliance.

## 8. Segment insights

Use SQL views `vw_grade_segments` and `vw_vintage_cohorts` (and `ecl_by_grade.csv`) to show:

- Lower grades carry higher observed default rates **and** disproportionate ECL share.
- Vintage × grade tables support: *“Did 2015 underwriting look worse than 2013?”*

## 9. Business takeaway

Ship a **decision-support** stack: rank risk (PD + scorecard), size loss (ECL), check stability (PSI), flag underpriced exposure, and show how ECL moves under stress — then visualize in Power BI with DAX from `4_powerbi_dax.txt`.

## 10. Limitations

- Static LGD; no recovery curves or collateral.
- Accepted-loan sample → selection bias vs full applicant population.
- Pricing adequacy ignores cost of funds and operating expense.
- Stress scenarios are illustrative multipliers, not macro-linked PDs.
- No SICR staging, lifetime vs 12-month ECL distinction, or forward-looking overlays.
