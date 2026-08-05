# Interview Prep — Multi-Strategy Allocation Case Study

Target audience: **IB** and **general finance** internships / placements.  
Affiliation framing: **Quant Club, BITS Pilani** (independent research case study).  
Lead with markets judgment. Mention Python only if asked.

---

## Quant Club 60-second pitch (preferred for club / IB)

> “Through Quant Club at BITS Pilani, I worked on a portfolio construction case study: how a multi-strat allocator should budget capital across momentum (MTUM), defensive min-vol (USMV), and a crisis/vol sleeve (VIXY) when regimes shift. Using a 60-day rolling risk engine, I compared inverse-volatility risk parity and minimum-variance methods against equal-weight and a 60/40 benchmark, net of 10bps costs, through COVID and the 2022 rate shock. Inverse-vol improved Sharpe and cut drawdowns versus equal-weight. Static 60/40 still won on absolute return because VIXY has a long-run roll cost. The takeaway is mandate-dependent: if you want crisis convexity, pay for it and risk-budget dynamically; if you want return, don’t hold a permanent vol sleeve.”

---

## 60-second pitch (generic / no club header)

> “I built a multi-strategy portfolio allocation case study. Instead of picking stocks, I allocate capital across three strategy sleeves — momentum (MTUM), defensive min-vol (USMV), and a crisis/vol sleeve (VIXY) — using a 60-day rolling risk engine. I compared inverse-volatility risk parity and minimum-variance optimization against equal-weight and a 60/40 benchmark, net of 10bps transaction costs, through COVID and the 2022 rate shock. Inverse-vol improved Sharpe and cut drawdowns versus equal-weight. Static 60/40 still won on absolute return because VIXY has a long-run roll cost. The takeaway is mandate-dependent: if you want crisis convexity, pay for it and risk-budget dynamically; if you want return, don’t hold a permanent vol sleeve.”

---

## Q1 — Walk me through this project

**Answer:**  
I framed the problem the way a multi-strat PM would: how do you budget risk across uncorrelated strategy return streams? I used liquid ETF proxies so the history is real and auditable. Risk is estimated on a trailing 60-day window with no lookahead. Dynamic methods reallocate when volatility or covariance shifts; I charge 10bps on turnover so the results aren’t frictionless. I then write the conclusion as a recommendation, not a backtest trophy — InvVol vs 60/40 is a trade-off, not a free alpha claim.

---

## Q2 — Why not just buy SPY?

**Answer:**  
SPY is a single equity beta bet. This project is about **capital allocation across styles** — momentum, defensive, and crisis convexity — and how those weights should change when risk regimes change. A buy-and-hold index fund doesn’t answer “how would a multi-strat book rebalance when vol spikes?” That’s the skill I’m demonstrating: portfolio construction and risk budgeting, not stock picking.

---

## Q3 — Why did 60/40 beat your dynamic model on return?

**Answer:**  
Because 60/40 holds **zero VIXY**. VIXY is great in a panic (March 2020) but bleeds in contango during calm markets. Equal-weight and any dynamic book that always keeps a crisis sleeve pays that carry. 60/40 is a cleaner risk-on blend of momentum + min-vol. So higher CAGR for 60/40 is economically expected — it doesn’t mean inverse-vol “failed”; it means the crisis sleeve’s insurance premium shows up in full-sample returns. On risk-adjusted metrics and drawdowns versus equal-weight, InvVol still adds value.

---

## Q4 — What’s wrong with VIXY as a hedge?

**Answer:**  
It’s a **futures-based** product, not a put option. You get vol exposure with **roll/contango costs**, path dependency, and structural decay in quiet markets. It’s a useful *public proxy* for a crisis sleeve, but a real fund might use options, variance swaps, or a dedicated tail book with clearer payoff design. I’d never present VIXY as a free or permanent hedge — I’d present it as episodic convexity with a known carry cost.

---

## Q5 — How would you improve this with more time?

**Answer (pick 3):**  
1. **Rebalance monthly** instead of daily to cut turnover and look more institutional.  
2. **Add a bond / duration sleeve** (e.g. TLT or a rates ETF) for classic risk-parity diversification beyond equity factors.  
3. **Replace or complement VIXY** with a cleaner tail proxy (e.g. put-write / TAIL-style product) and measure hedge efficiency vs carry.  
4. Report **gross vs net Sharpe** side-by-side and stress costs at 5bps / 20bps.  
5. Expand regime definitions with **macro labels** (inflation surprise, Fed hiking cycle) rather than calendar years only.

---

## Q6 — Was this a team project?

**Answer:**  
It was an **independent research case study under Quant Club at BITS Pilani**. I owned the research question, sleeve selection, comparison design, regime interpretation, and the investment memo. Club framing means it sits in our portfolio-construction vertical and can be presented to members — not that it was a multi-author coding sprint. I’m happy to walk through the economics without opening an IDE.

---

## Q7 — What was your technical contribution?

**Answer:**  
The contribution is **finance design and analysis**: choosing MTUM / USMV / VIXY as strategy proxies, specifying InvVol vs MinVar vs benchmarks under 10bps costs, stress-testing COVID and 2022, and writing a clear mandate-dependent recommendation. I used Python to run a reproducible backtest so the numbers are auditable — but in interviews I lead with the allocation trade-off (why InvVol helps vs equal-weight, why 60/40 wins CAGR), not scipy or package structure.

---

## Numbers to have ready (from latest backtest run)

| Method | Ann. Return | Sharpe | Max DD | VaR 95% (1d) |
|--------|-------------|--------|--------|--------------|
| InvVol | 7.8% | 0.30 | -22.8% | -0.86% |
| EqualWeight | -4.6% | -0.50 | -57.0% | -1.46% |
| 60/40 | 15.3% | 0.56 | -33.6% | -1.70% |

Refresh after each `python -m meta_portfolio` run from the Performance sheet in Excel.

---

## What to de-emphasize

- scipy.optimize internals  
- pytest / package layout  
- “I wrote 12 Python modules”

## What to emphasize

- Quant Club research framing  
- Mandate design (risk vs return)  
- Regime thinking (COVID vs 2022)  
- Transaction costs and hedge carry  
- Clear recommendation with limitations

---

## Resume bullets

### Quant Club (preferred for IB / general finance)

**Quant Club, BITS Pilani** | Portfolio Construction Case Study  

Researched dynamic capital allocation across momentum (MTUM), min-vol (USMV), and crisis-vol (VIXY) sleeves using 60-day rolling risk parity and minimum-variance methods; stress-tested net-of-cost performance across COVID and 2022 rate regimes; authored investment memo and Excel attribution pack presented to club members.

### Personal / technical (optional — quant-heavy roles only)

**Multi-Strategy Portfolio Allocation Case Study** | Python, Excel | 2026  

Analyzed dynamic capital allocation across momentum (MTUM), min-vol (USMV), and crisis-vol (VIXY) sleeves using 60-day rolling risk metrics; compared inverse-volatility and minimum-variance methods against equal-weight and 60/40 benchmarks net of transaction costs across COVID, 2022 rate shock, and recovery regimes; authored investment memo with regime attribution and allocator trade-off analysis.
