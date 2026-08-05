# Strategy Rationale — MTUM / USMV / VIXY

This note explains the **economic** role of each sleeve in the Meta-Portfolio case study. It is written for IB / general finance interviews, not for a coding walkthrough.

## Why three sleeves (not one stock portfolio)

A multi-strategy allocator thinks in **return streams**, not tickers. The question is: *How do we budget risk across styles that behave differently across regimes?* Public ETFs give transparent, liquid proxies for those styles so the allocation problem can be studied with real market history (COVID, 2022 rate shock, recovery).

---

## Sleeve A — Momentum (MTUM)

| | |
|--|--|
| **Instrument** | iShares MSCI USA Momentum Factor ETF |
| **Finance framing** | Equity **factor tilt** toward recent relative winners |
| **Economic role** | Participate in trending markets; earn momentum risk premium |
| **Typical behavior** | Strong in extended bulls; vulnerable to sharp reversals and factor crashes |
| **Risk language** | Higher beta / higher drawdown vs defensive sleeve |

**Macro tie-in:** In the **2021 bull**, momentum participated in the risk-on rally. In the **2022 rate shock**, rising discount rates and factor rotation hurt growth/momentum-tilted books — allocation engines that only chase trailing winners without a risk governor get punished.

---

## Sleeve B — Defensive / Min-Vol (USMV)

| | |
|--|--|
| **Instrument** | iShares MSCI USA Min Vol Factor ETF |
| **Finance framing** | **Low-beta / defensive** equity exposure (not classic pairs mean-reversion, but the same *capital preservation* role in a multi-strat book) |
| **Economic role** | Stabilize portfolio vol; cushion risk-off periods |
| **Typical behavior** | Steadier path, lower upside in melt-up markets |
| **Risk language** | Lower standalone volatility; often smaller contribution to portfolio VaR |

**Macro tie-in:** In risk-off or high-uncertainty windows, min-vol tends to hold up better than high-beta momentum. That is why inverse-vol and min-variance methods naturally **raise USMV weight** when MTUM volatility spikes.

---

## Sleeve C — Crisis / Vol (VIXY)

| | |
|--|--|
| **Instrument** | ProShares VIX Short-Term Futures ETF |
| **Finance framing** | **Convexity / crisis** proxy — positive when equity implied/realized vol spikes |
| **Economic role** | Diversify equity sleeves in panic; approximate a “tail / vol arb” sleeve without running an options book |
| **Typical behavior** | Spikes in crashes (e.g. March 2020); **decays in calm markets** via futures roll / contango |
| **Risk language** | Negative correlation to risk-on *in crises*; positive carry cost otherwise |

**Macro tie-in:**
- **COVID crash:** VIXY illustrated crisis alpha — equal-weight portfolios with a permanent vol sleeve can print large positive returns while 60/40 (no VIXY) sells off.
- **Calm / recovery years:** The same sleeve is a **drag**. That is why static **60/40** (MTUM + USMV only) often wins on long-run CAGR: it refuses to pay permanent hedge carry.
- **2022 rate shock:** Vol rose, but the path was a grinding equity bear driven by rates — not always a clean VIX spike like March 2020. Crisis sleeves help less when the shock is slow and multifactor.

---

## Regime cheat sheet (interview table)

| Regime | What happened to sleeves | Allocator implication |
|--------|--------------------------|------------------------|
| COVID crash (Feb–Mar 2020) | Equities down; VIXY up sharply | Crisis sleeve earns its keep; equal-weight can look “lucky” on VIXY |
| 2021 bull | Momentum / risk-on strong | Paying for VIXY hurts relative performance |
| 2022 rate shock | Broad risk-off; factors rotate | Dynamic risk cuts help drawdowns; hedges not a free lunch |
| 2023 recovery | Risk-on returns | Static 60/40 often leads on absolute return |

---

## One sentence for each sleeve (memorize)

1. **MTUM** — “My growth/trend sleeve.”
2. **USMV** — “My defensive ballast.”
3. **VIXY** — “My crisis convexity — powerful in panics, expensive in peacetime.”

That framing is what turns “I downloaded three ETFs” into a **portfolio construction** story.
