# FirstClub Growth Memo — Install-to-First-Order Funnel Teardown

**Scope:** Quick-commerce (10–15 min grocery delivery) | **Dataset:** 1.2M orders, 2.4K App Store reviews | **Competitive set:** Blinkit, Zepto, Swiggy Instamart, BigBasket Now

---

## Executive Summary

FirstClub converts **29% of installs to first delivered order**, trailing the peer median of **36%**. D7 retention (42%) is competitive, but D30 repeat (28%) lags Zepto (33%) and Instamart (35%). The largest funnel leak is **catalog → cart** (36% drop-off), followed by **cart → checkout** (22%). App Store reviews surface **trust** (wrong items, refund friction) and **delivery promise** gaps as top negative themes.

**Recommendation:** Prioritize trust-layer experiments (EXP-01, EXP-02) in Days 0–30, retention recovery (EXP-03, EXP-04) in Days 31–60, and repeat-purchase mechanics (EXP-05, EXP-06) in Days 61–90. Combined top-3 experiment scenario lifts LTV/CAC from **1.4× → 2.1×** in the simulator.

---

## Key Findings

### 1. Acquisition Funnel

| Stage | Conversion (from install) | Drop-off |
|-------|---------------------------|----------|
| Signup | 82% | 18% |
| Location set | 75% | 9% |
| Catalog view | 66% | 12% |
| Cart add | 42% | **36%** ← largest gap |
| Checkout start | 33% | 22% |
| Payment success | 29% | 12% |
| First order delivered | 29% | 3% |

**Insight:** Users who reach catalog but don't add to cart are the highest-leverage cohort. Review themes point to stockout frustration and unclear delivery ETA as blockers.

### 2. Retention

- **D7:** 42% (peer median 39%) — strong post-delivery experience when order completes
- **D30:** 28% (peer median 32%) — one-and-done users dominate; win-back under-invested

### 3. Trust Gaps (App Store Synthesis)

| Theme | Avg Rating | Negative Share |
|-------|------------|----------------|
| Support / refunds | 2.8 | 52% |
| Trust & safety | 3.0 | 48% |
| Delivery speed | 3.8 | 38% |
| Product freshness | 4.1 | 32% |

### 4. Unit Economics (1M-order scale)

| Metric | Base | Post top-3 experiments |
|--------|------|--------------------------|
| CAC | ₹185 | ₹152 |
| LTV (12-mo) | ₹258 | ₹382 |
| LTV/CAC | 1.4× | 2.1× |
| Payback | 7 mo | 4 mo |
| Annual revenue @ 1M orders | ₹48.5 Cr | — |

---

## Prioritized Experiments (ICE)

1. **EXP-03** — Abandoned cart push (ICE 8.0)
2. **EXP-05** — Staples subscription (ICE 6.3)
3. **EXP-08** — City launch pre-positioning (ICE 6.3)
4. **EXP-01** — Delivery ETA trust badge (ICE 7.0)
5. **EXP-07** — Referral program (ICE 7.0)
6. **EXP-04** — D30 win-back (ICE 7.0)
7. **EXP-06** — One-tap reorder (ICE 7.3)
8. **EXP-02** — Live rider tracking v2 (ICE 6.7)

---

## Next Steps

1. Instrument event taxonomy (see `EVENT_TAXONOMY.md`) before any A/B test
2. Ship EXP-01 + EXP-03 in parallel (low coupling, high ICE)
3. Run city launch playbook for Pune expansion (see `CITY_LAUNCH_PLAYBOOK.md`)
4. Weekly funnel review: install → cart → first order → D7 → D30
