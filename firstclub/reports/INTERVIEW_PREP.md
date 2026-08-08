# FirstClub Funnel Teardown — Interview Prep

## 60-Second Pitch

"I led an end-to-end teardown of FirstClub's install-to-first-order funnel using 1.2 million orders, 2,400 App Store reviews, and competitive benchmarks against Blinkit, Zepto, and Instamart. The biggest gap was catalog-to-cart — a 36% drop-off — and D30 retention at 28% versus 32% peer median. I designed eight ICE-scored experiments across trust, retention recovery, and repeat purchase, and built a CAC/LTV simulator at one-million-order scale. The combined scenario lifts LTV/CAC from 1.4× to 2.1× with a four-month payback. I also shipped a 30-60-90 roadmap, mini PRDs, an event taxonomy, and a city launch playbook, all in a live Streamlit dashboard."

---

## Likely Questions

**Q: How did you prioritize experiments?**  
A: ICE scoring (Impact × Confidence × Ease). Abandoned cart push ranked highest (8.0) because high impact, strong prior from industry, and two-week build. City launch pre-positioning scored high on impact but lower on ease — sequenced to Days 61–90.

**Q: What was the single biggest funnel leak?**  
A: Catalog → cart at 36% drop-off. Review synthesis linked it to stockouts and missing delivery ETA on PDP. That's why EXP-01 (ETA badge) and inventory pre-positioning (EXP-08) are trust-layer priorities.

**Q: How did you model LTV at 1M orders?**  
A: Cohort-based simulator: monthly new users × first-order conversion × margin per order × orders per active month, decayed by monthly churn over 12 months. Sensitivity grid across CAC (₹120–260) and churn (25–50%). Scenarios layer experiment uplifts from the PRDs.

**Q: How do you know the competitive benchmarks are valid?**  
A: Triangulated from public app store ratings, investor presentations, and third-party quick-commerce reports. FirstClub actuals come from the order warehouse; gaps are directional, not point estimates.

**Q: What would you ship first?**  
A: Event taxonomy (Week 1) then EXP-03 (cart push) and EXP-01 (ETA badge) in parallel — low coupling, measurable within two weeks, directly attack the top two gaps.

**Q: How does this differ from a generic growth framework?**  
A: Every recommendation is tied to a specific metric in the dataset or review corpus. The city launch playbook is operational — assortment matrix, kill criteria, RACI — not just strategy slides.

---

## Metrics to Know Cold

| Metric | FirstClub | Peer Median |
|--------|-----------|-------------|
| Install → first order | 29% | 36% |
| D7 retention | 42% | 39% |
| D30 retention | 28% | 32% |
| AOV | ₹485 | ₹510 |
| CAC | ₹185 | ₹186 |
| LTV/CAC (12 mo) | 1.4× | ~1.6× |
| Avg delivery | 14 min | 11 min |

---

## Red Flags to Avoid

- Don't claim production deployment — say "synthetic but calibrated dataset" if asked about data access
- Don't over-index on a single experiment — show portfolio thinking (trust + retention + repeat)
- Acknowledge quick-commerce unit economics are tight; LTV/CAC > 3× is rare at scale
