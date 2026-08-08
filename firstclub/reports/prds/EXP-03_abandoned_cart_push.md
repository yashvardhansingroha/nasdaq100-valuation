# PRD: EXP-03 — Abandoned Cart Push (30 min)

**Status:** Ready for A/B | **ICE:** 8.0 | **Effort:** 2 weeks

## Problem
22% drop-off from cart to checkout. Users add items but don't complete payment.

## Solution
Push notification 30 min after cart abandon: "Your cart is waiting — ₹50 off your first order. Expires in 2 hours."

## Success Metrics
- **Primary:** Cart-to-payment conversion (+15% recovery)
- **Guardrail:** Discount burn (<8% of first-order GMV)

## Scope
- Cart abandon detection (server-side)
- Push template + deep link to cart
- A/B: offer vs no-offer vs control

## Out of Scope
- SMS/email channels (Phase 2)
- Personalized SKU recommendations in push
