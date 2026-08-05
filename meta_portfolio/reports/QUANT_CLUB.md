# Quant Club Research Case Study — Multi-Strategy Portfolio Allocation

| | |
|--|--|
| **Affiliation** | Quant Club, BITS Pilani |
| **Vertical** | Portfolio Construction / Risk |
| **Format** | Independent research case study |
| **Period studied** | 2019–present (COVID, 2021 bull, 2022 rate shock, 2023 recovery) |

---

## Research question

How should capital be allocated across **momentum**, **defensive**, and **crisis** strategy sleeves when market risk regimes shift — and when does a permanent vol sleeve help versus hurt?

---

## Data and methods

| Element | Choice |
|---------|--------|
| Momentum sleeve | MTUM (iShares MSCI USA Momentum Factor ETF) |
| Defensive sleeve | USMV (iShares MSCI USA Min Vol Factor ETF) |
| Crisis / vol sleeve | VIXY (ProShares VIX Short-Term Futures ETF) |
| Risk engine | 60-day rolling volatility and covariance (no lookahead) |
| Dynamic methods | Inverse-volatility risk parity; minimum variance; max diversification |
| Benchmarks | Equal-weight (1/3 each); static 60/40 (MTUM/USMV, no VIXY) |
| Friction | 10 bps per unit of one-way turnover on dynamic methods |

---

## Key findings (net of costs)

1. **Inverse-vol beats equal-weight on risk-adjusted terms** — Sharpe ~0.30 vs −0.50; max drawdown ~−23% vs −57%. Dynamic risk budgeting shrinks high-vol sleeves after stress.
2. **Static 60/40 leads on absolute return** (~15% ann.) because it holds **zero VIXY** and avoids long-run futures roll / contango decay.
3. **Crisis convexity is regime-dependent** — VIXY earns its keep in sharp vol spikes (e.g. March 2020) but is expensive insurance in calm and grinding bears (e.g. 2022 rates). Mandate design matters more than a single full-sample winner.

---

## Limitations

- VIXY is a futures product with structural carry cost — not a free permanent hedge  
- ETF proxies approximate strategy *styles*, not live multi-strat P&L  
- Daily rebalancing overstates typical institutional turnover  
- Long-only, fully invested; no leverage, shorting, or cash sleeve  

---

## Your role (finance-first)

- Framed the research question as a multi-strat **capital allocation** problem  
- Selected and justified the three strategy proxies in factor / macro language  
- Designed the comparison (InvVol / MinVar vs equal-weight / 60/40) under realistic costs  
- Interpreted results across COVID and 2022 regimes  
- Authored the investment memo, Excel pack, and club presentation  

Python was used to run a reproducible backtest; the contribution for Quant Club is the **portfolio construction analysis**, not software engineering.

---

## Deliverables

| Artifact | Path |
|----------|------|
| Investment memo (PDF) | [allocation_memo.pdf](allocation_memo.pdf) |
| Excel workbook | [meta_portfolio_analysis.xlsx](meta_portfolio_analysis.xlsx) |
| Strategy rationale | [STRATEGY_RATIONALE.md](STRATEGY_RATIONALE.md) |
| Club deck (5 slides) | [quant_club_deck.md](quant_club_deck.md) |
| Interview prep | [INTERVIEW_PREP.md](INTERVIEW_PREP.md) |

---

## Resume line (Quant Club)

**Quant Club, BITS Pilani** | Portfolio Construction Case Study  

Researched dynamic capital allocation across momentum (MTUM), min-vol (USMV), and crisis-vol (VIXY) sleeves using 60-day rolling risk parity and minimum-variance methods; stress-tested net-of-cost performance across COVID and 2022 rate regimes; authored investment memo and Excel attribution pack presented to club members.

---

*Independent research case study under Quant Club, BITS Pilani. Not financial advice.*
