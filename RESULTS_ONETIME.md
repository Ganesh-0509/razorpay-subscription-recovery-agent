# RESULTS_ONETIME

Stretch goal: the same gate/policy/audit-log pattern applied to failed
ONE-TIME payments instead of halted subscriptions - see `agent_onetime.py`
and BUILD_LOG.md §13. Same honesty caveat as RESULTS.md: `simulated_customer_response` is a labeled synthetic assumption, not a
real payment outcome.

- Total failed one-time payments processed: **30**
- Total value: **Rs 211,964.29**
- Actions executed (retries/nudges the gate let through): **29**
- Simulated recovered amount: **Rs 130,770.89** (18/29 executed actions 'succeeded' in simulation)
- LLM proposals the gate had to override: **7/30** (23%)

## By decline code

| Decline code | Count | Final action |
|---|---|---|
| authentication_failed | 4 | payment_link_nudge |
| bank_technical_error | 1 | immediate_retry |
| card_declined | 7 | payment_link_nudge |
| card_expired | 2 | payment_link_nudge |
| card_not_enrolled | 1 | payment_link_nudge |
| gateway_technical_error | 1 | immediate_retry |
| incorrect_cvv | 6 | payment_link_nudge |
| insufficient_funds | 6 | delayed_retry |
| payment_risk_check_failed | 1 | no_action_fraud |
| payment_timed_out | 1 | immediate_retry |
