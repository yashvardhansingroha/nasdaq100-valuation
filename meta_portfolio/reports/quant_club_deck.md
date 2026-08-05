# Quant Club Deck — Multi-Strategy Portfolio Allocation

**Affiliation:** Quant Club, BITS Pilani | Portfolio Construction  
**Use:** Club meetings, placement folders, recruiter screen-share  
**Rule:** Finance only — no code screenshots.

Copy each slide into Google Slides / PowerPoint / Canva. Insert `../data/equity_curve.png` on Slide 4 after running `python -m meta_portfolio`.

---

## Slide 1 — Title

**Title:** Multi-Strategy Portfolio Allocation  
**Subtitle:** Dynamic risk budgeting across momentum, defensive, and crisis sleeves  

**Footer line:** Quant Club, BITS Pilani | Independent Research Case Study  

**Research question (large text):**  
*How should capital be allocated across strategy sleeves when risk regimes shift?*

---

## Slide 2 — Three strategy sleeves

| Sleeve | Proxy | Economic role |
|--------|-------|-----------------|
| Momentum | **MTUM** | Equity factor tilt — participates in trends |
| Defensive | **USMV** | Low-beta ballast — capital preservation |
| Crisis / vol | **VIXY** | Convexity in panics — carry cost in peacetime |

**Talking point:** Multi-strat books allocate across *return streams*, not single stocks. These ETFs are transparent proxies so we can study real history (COVID, 2022).

---

## Slide 3 — Methodology

```
60-day rolling vol + covariance
        |
        v
  Weights for day t (info through t-1 only)
        |
        +-- Inverse-vol (risk parity)
        +-- Min variance (uses covariance)
        +-- Max diversification
        |
        v
  Portfolio returns − 10bps × turnover
        |
        v
  Compare vs Equal-weight and 60/40
```

**Talking point:** No lookahead. Friction included. Bounds 5%–60% per sleeve, fully invested, long-only.

---

## Slide 4 — Results

**Insert chart:** cumulative equity curve (`meta_portfolio/data/equity_curve.png`)

**Table (net of costs):**

| Method | Ann. Return | Sharpe | Max DD |
|--------|-------------|--------|--------|
| InvVol | 7.8% | 0.30 | −23% |
| EqualWeight | −4.6% | −0.50 | −57% |
| 60/40 | 15.3% | 0.56 | −34% |

**Caption:** InvVol improves risk-adjusted outcomes vs equal-weight; 60/40 wins CAGR by holding no VIXY.

---

## Slide 5 — Conclusion and limitations

**Recommendation**

- **Risk-conscious mandate + crisis sleeve** → inverse-vol risk parity  
- **Return-seeking, hedges optional** → static 60/40 (momentum + min-vol)

**Limitations (keep visible)**

1. VIXY roll / contango decay  
2. ETF proxies ≠ live fund P&L  
3. Daily rebal overstates institutional turnover  

**Close:** *Mandate design decides the winner — not a single backtest trophy.*

**Questions?**

---

## Presenter notes (do not put on slides)

- Open with Quant Club affiliation; never lead with Python.  
- If asked about code: “I used Python to run the backtest; the work was designing the comparison and interpreting regimes.”  
- If asked team vs solo: “Independent research case study under Quant Club.”  
- Own the 60/40 result — it shows research maturity.
