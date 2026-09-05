# RESULTS

Generated from a run against synthetic, schema-accurate-but-fabricated
data. `simulated_customer_response` is a labeled synthetic assumption
(see decline_codes.py `simulated_success_rate`), not a real payment
outcome - test mode cannot produce a real customer completing a charge.
This file reports it honestly as simulated throughout.

- Total halted subscriptions processed: **150**
- Total value of halted subscriptions: **Rs 150,729.35**
- Actions executed (retries/nudges the gate let through): **108**
- Simulated recovered amount: **Rs 42,327.28** (43/108 executed actions 'succeeded' in simulation)
- LLM proposals the gate had to override (policy mismatch): **3/150** (2% - the gate, not the model, is what makes this safe)
- Hard-blocked by gate (spending cap / duplicate): **0**
- Correctly refused as fraud-flagged (never retried): **0**
- Correctly identified as unrecoverable (no action taken): **42**

## By decline code

| Decline code | Count | Final action |
|---|---|---|
| authentication_failed | 8 | no_action_unrecoverable |
| authentication_failed | 9 | payment_link_nudge |
| bank_technical_error | 6 | immediate_retry |
| bank_technical_error | 1 | no_action_unrecoverable |
| card_declined | 4 | no_action_unrecoverable |
| card_declined | 7 | payment_link_nudge |
| card_disabled_for_online_payments | 7 | payment_link_nudge |
| card_expired | 3 | no_action_unrecoverable |
| card_expired | 23 | payment_link_nudge |
| debit_instrument_blocked | 1 | no_action_unrecoverable |
| debit_instrument_inactive | 2 | no_action_unrecoverable |
| debit_instrument_inactive | 1 | payment_link_nudge |
| gateway_technical_error | 6 | immediate_retry |
| gateway_technical_error | 2 | no_action_unrecoverable |
| incorrect_cvv | 2 | no_action_unrecoverable |
| incorrect_cvv | 6 | payment_link_nudge |
| insufficient_funds | 28 | delayed_retry |
| insufficient_funds | 13 | no_action_unrecoverable |
| payment_cancelled | 3 | no_action_unrecoverable |
| payment_cancelled | 2 | payment_link_nudge |
| payment_failed | 5 | payment_link_nudge |
| payment_risk_check_failed | 1 | payment_link_nudge |
| payment_timed_out | 2 | immediate_retry |
| payment_timed_out | 3 | no_action_unrecoverable |
| transaction_limit_exceeded | 5 | delayed_retry |
