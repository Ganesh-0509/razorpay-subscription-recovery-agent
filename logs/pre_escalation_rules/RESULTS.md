# RESULTS

Generated from a run against synthetic, schema-accurate-but-fabricated
data. `simulated_customer_response` is a labeled synthetic assumption
(see decline_codes.py `simulated_success_rate`), not a real payment
outcome - test mode cannot produce a real customer completing a charge.
This file reports it honestly as simulated throughout.

- Total halted subscriptions processed: **150**
- Total value of halted subscriptions: **Rs 150,729.35**
- Actions executed (retries/nudges the gate let through): **143**
- Simulated recovered amount: **Rs 54,362.43** (50/143 executed actions 'succeeded' in simulation)
- LLM proposals the gate had to override (policy mismatch): **1/150** (1% - the gate, not the model, is what makes this safe)
- Hard-blocked by gate (spending cap / duplicate): **0**
- Correctly refused as fraud-flagged (never retried): **1**
- Correctly identified as unrecoverable (no action taken): **6**

## By decline code

| Decline code | Count | Final action |
|---|---|---|
| authentication_failed | 17 | payment_link_nudge |
| bank_technical_error | 7 | immediate_retry |
| card_declined | 11 | payment_link_nudge |
| card_disabled_for_online_payments | 7 | payment_link_nudge |
| card_expired | 26 | payment_link_nudge |
| debit_instrument_blocked | 1 | no_action_unrecoverable |
| debit_instrument_inactive | 3 | payment_link_nudge |
| gateway_technical_error | 8 | immediate_retry |
| incorrect_cvv | 8 | payment_link_nudge |
| insufficient_funds | 41 | delayed_retry |
| payment_cancelled | 5 | no_action_unrecoverable |
| payment_failed | 5 | payment_link_nudge |
| payment_risk_check_failed | 1 | no_action_fraud |
| payment_timed_out | 5 | immediate_retry |
| transaction_limit_exceeded | 5 | delayed_retry |
