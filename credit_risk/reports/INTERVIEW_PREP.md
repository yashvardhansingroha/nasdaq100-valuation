# Interview Prep — Lending Club Credit Risk Case Study

Target audience: **credit risk**, **risk analytics**, **IB / finance** roles that care about PD models and IFRS 9 language.  
Lead with **risk and capital framing**. Mention Python / PostgreSQL only if asked about implementation.

---

## 60-second pitch

> “I built an end-to-end retail credit risk case study on ~2.2 million Lending Club loans. I engineered a PostgreSQL ETL view for closed loans, trained a stratified logistic PD model (about 0.74 ROC-AUC / 0.65 F1, with Gini and KS), and translated scores into IFRS 9 expected credit loss using PD × 60% LGD × loan amount. I also built a WOE/IV application scorecard, monitored train–test stability with PSI, flagged underpriced loans where contractual spread doesn’t cover expected loss, and stressed portfolio ECL under adverse and severe scenarios — all feeding a Power BI dashboard for grade and vintage segmentation.”

---

## Resume bullets

**Quant / risk analytics variant**

> Built a Lending Club PD / ECL pipeline on 2.2M loans: stratified logistic regression (~0.74 AUC), WOE/IV scorecard, PSI stability checks, risk-adjusted pricing flags, and IFRS 9-style ECL with adverse/severe stress scenarios; delivered PostgreSQL views and Power BI DAX for grade–vintage portfolio reporting.

**Finance internship variant**

> Analyzed retail credit risk on Lending Club data using a PD model and IFRS 9 expected-loss framework (PD × LGD × EAD); assessed pricing adequacy vs grade benchmarks, stress-tested portfolio ECL, and summarized findings in a risk memo and dashboard-ready dataset.

---

## Q&A bank

### Walk me through the project

Closed-loan outcomes only (Fully Paid vs Charged Off/Default). SQL cleans employment length and term, builds vintage year. Logistic PD with stratified split and balanced class weights. Validate with AUC, F1, Gini, KS. Convert PD to ECL with 60% LGD. Scorecard (WOE/IV) for interpretability. PSI for monitoring language. Pricing adequacy to connect risk to yield. Stress multiples for reserve sensitivity. Power BI for portfolio storytelling.

### Why logistic regression instead of XGBoost?

For retail credit and many risk committees, **interpretability and auditability** matter. Logistic coefficients and WOE bins are easier to challenge and document than a black-box booster. Gradient boosting can lift AUC, but I’d use it after a transparent baseline and with strong governance (feature stability, adverse action reasons).

### What is Gini vs AUC?

Gini = **2 × AUC − 1**. Same ranking information, different industry scale. Credit risk teams often quote Gini; data science teams often quote AUC. Report both.

### Why stratified sampling?

Defaults are the minority class. A random split can under-represent defaults in the test set and inflate apparent performance. Stratify so both folds keep the same default rate.

### What is WOE and IV?

**WOE** measures how a bin’s good/bad mix differs from the portfolio average (`ln(%good/%bad)`). **IV** sums WOE-weighted differences across bins to score how predictive a feature is. Used in application scorecards for regulatory-friendly binning and variable selection.

### What is PSI and when does it alarm?

PSI compares score or feature distributions between two populations (here, train vs test as a demo of monitoring). Industry rules of thumb: **&lt;0.10 stable**, **0.10–0.25 moderate**, **&gt;0.25 significant** — investigate data drift or retrain.

### How do you interpret ECL?

ECL ≈ expected dollars lost if today’s PDs realize at a 60% LGD. It is a **portfolio reserve intensity** metric, not a cash forecast. Compare ECL % of exposure across grades and vintages; stress it to see buffer needs.

### How do you assess if a loan is underpriced?

Compare the loan’s rate to the **grade benchmark**, subtract **PD × LGD**. If that margin is negative and PD is elevated, the contractual spread may not compensate for modeled expected loss (simplified — ignores funding cost).

### Walk me through a stress test

Take each loan’s PD, apply a scenario (e.g. ×1.5 adverse, ×2.0 severe, or +5pp recession), cap at 99%, recompute ECL = stressed PD × LGD × EAD, and report delta vs base. Use that for “how much more reserve would we need in a downturn?”

### What would you do with more time?

Estimate LGD from recoveries; add macro overlays / through-the-cycle vs PIT PD; SICR staging for full IFRS 9; calibration plots; challenger model (GBM) with explainability; reject inference for applicant-level underwriting; automated monitoring alerts on PSI.

### What’s wrong with using only AUC?

AUC ignores **cost of errors** and **dollar exposure**. A model can rank well while still underpricing large loans. That’s why ECL, pricing adequacy, and stress matter alongside discrimination metrics.

---

## One-line dashboard story

“Grade and vintage drive observed defaults; the PD model concentrates ECL in weaker grades; stress scenarios show how fast that ECL can grow; pricing flags show where yield may not cover risk.”
