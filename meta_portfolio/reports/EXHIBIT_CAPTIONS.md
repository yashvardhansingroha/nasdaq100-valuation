# Exhibit Captions — Annotated Chart Pack

Use these one-liners under charts in the memo, slides, or Streamlit demo. They turn plots into **finance exhibits**.

---

## Exhibit 1 — Cumulative equity curve (Dynamic vs Benchmarks)

**Caption:**  
*Dynamic inverse-volatility allocation improves risk-adjusted outcomes versus equal-weight by shrinking high-vol sleeves after stress, but static 60/40 (no VIXY) leads on absolute return because it avoids the long-run carry cost of a permanent crisis sleeve.*

**What to say in 15 seconds:**  
“Five lines: three dynamic methods and two benchmarks. InvVol beats equal-weight on Sharpe and drawdown. 60/40 wins CAGR — and that gap is mostly VIXY decay, not a bug in the optimizer.”

**Chart source:** `python -m meta_portfolio` → `meta_portfolio/data/equity_curve.png` or Streamlit equity panel.

---

## Exhibit 2 — Stacked capital weights over time

**Caption:**  
*Capital weights are not static: when trailing 60-day volatility spikes (notably March 2020), the allocator automatically raises the crisis/defensive mix and cuts momentum — the mechanical expression of risk budgeting.*

**What to say in 15 seconds:**  
“Watch the stack during COVID. VIXY and/or USMV rise as MTUM vol jumps. That is the engine doing its job: risk parity in motion.”

**Chart source:** Streamlit “Capital Weights” panel (toggle InvVol / MinVar / MaxDiv).

---

## Exhibit 3 — Rolling correlation (Momentum A vs Crisis C)

**Caption:**  
*Correlation between momentum and the crisis sleeve is regime-dependent: diversification appears when equities panic and VIX futures rally, which is exactly when a multi-strat book needs a non-equity return stream.*

**What to say in 15 seconds:**  
“I don’t assume constant correlation. The A–C rolling corr shows when the hedge actually diversifies — interviewers care that you checked this instead of trusting a lifetime correlation number.”

**Chart source:** Streamlit correlation panel (A vs C).

---

## Optional Exhibit 4 — Regime Sharpe bar chart

**Caption:**  
*Method rankings flip by regime: crisis convexity can dominate a short crash window, while peacetime and recovery favor equity-heavy static blends — so mandate design matters more than a single full-sample Sharpe.*

**What to say in 15 seconds:**  
“I don’t sell one winner across all regimes. COVID rewards the vol sleeve; calm years punish it. That’s the PM conversation.”

---

## Slide / memo layout suggestion

```
[ Exhibit 1: Equity curve          ]
  Caption (one sentence)

[ Exhibit 2: Weights | Exhibit 3: Corr ]
  Caption                Caption
```

Keep captions **under** the chart, not in the title. Interviewers skim titles; they remember the takeaway line.
