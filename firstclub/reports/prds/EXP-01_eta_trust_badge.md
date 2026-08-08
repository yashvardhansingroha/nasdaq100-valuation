# PRD: EXP-01 — Delivery ETA Trust Badge on PDP

**Status:** Ready for A/B | **ICE:** 7.0 | **Effort:** 3 weeks

## Problem
36% of users who view catalog never add to cart. App Store reviews cite "unclear when it will arrive" as a top blocker.

## Solution
Show real-time delivery ETA badge on every PDP: "Delivered in ~12 min to [pincode]" with dark-store confidence indicator.

## Success Metrics
- **Primary:** Cart add rate (+8–12%)
- **Guardrail:** Delivery SLA breach rate (<5%)

## Scope
- ETA API from dark-store routing engine
- Badge component on PDP + cart
- A/B: 50/50 for new users in Bangalore

## Out of Scope
- Dynamic pricing by ETA
- Multi-store selection UI
