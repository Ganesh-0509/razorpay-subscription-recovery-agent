# CHECKOUT_ABANDONMENT_RESULTS

A NEW, standalone domain: checkout abandonment (a customer who started
checkout but never completed a payment attempt at all - no decline_code
exists here by definition). Closes one of the two previously-undisclosed
category-scope gaps (PS_REQUIREMENTS_DEBATE.md; README.md §6). Kept
separate from the 150-record flagship pipeline, exactly like
agent_onetime.py and route_demo.py already are - see
checkout_abandonment_agent.py's module docstring for what is and isn't
shared with that pipeline. Same honesty caveat as RESULTS.md/RESULTS_ONETIME.md:
`simulated_customer_response` is a labeled synthetic assumption, not a real
customer outcome.

- Abandoned checkouts processed: **30**
- Total abandoned cart value: **Rs 21,669.80**
- **Diagnosis accuracy (diagnosed_reason == true abandonment_reason): 21/30 (70.0%)**
- Misdiagnoses that changed the final action versus what ground truth's own policy would have given: **9/30** - the concrete proof that a wrong diagnosis has real downstream consequences here too, mirroring DIAGNOSIS_DEMO_RESULTS.md's own measurement.
- Actions executed (payment-link nudges the gate let through): **20**
- Simulated recovered amount: **Rs 5,916.13** (8/20 executed actions 'succeeded' in simulation)

## By final action

| Final action | Count |
|---|---|
| delayed_nudge_no_discount | 3 |
| discounted_incentive_nudge | 5 |
| immediate_payment_link_resend | 2 |
| no_action_low_value | 4 |
| no_action_respect_hesitation | 6 |
| payment_link_alternate_methods_nudge | 10 |

## Per-cart detail

| Cart | True reason | Diagnosed reason | Match | Final action |
|---|---|---|---|---|
| cart_8ed678386a0748 | price_shock | price_shock | yes | discounted_incentive_nudge |
| cart_d10a9a382b6d43 | otp_delay_or_failure | payment_method_unsupported | no | payment_link_alternate_methods_nudge |
| cart_dd4ab4b28b0344 | payment_method_unsupported | trust_or_security_concern | no | no_action_respect_hesitation |
| cart_d02fccdbf0144a | price_shock | price_shock | yes | no_action_low_value |
| cart_2ba24ca48f0545 | price_shock | price_shock | yes | discounted_incentive_nudge |
| cart_e5ef3ba921814b | payment_method_unsupported | payment_method_unsupported | yes | payment_link_alternate_methods_nudge |
| cart_46dde9c381224b | distraction_or_multitasking | payment_method_unsupported | no | payment_link_alternate_methods_nudge |
| cart_c0573ffd441d4d | price_shock | price_shock | yes | discounted_incentive_nudge |
| cart_427454819e6a43 | price_shock | price_shock | yes | discounted_incentive_nudge |
| cart_88b26b86886b45 | distraction_or_multitasking | distraction_or_multitasking | yes | delayed_nudge_no_discount |
| cart_b599a3faabc94c | price_shock | price_shock | yes | no_action_low_value |
| cart_640f957251b942 | payment_method_unsupported | trust_or_security_concern | no | no_action_respect_hesitation |
| cart_d234248cfc904f | payment_method_unsupported | trust_or_security_concern | no | no_action_respect_hesitation |
| cart_563addb82eb64d | distraction_or_multitasking | distraction_or_multitasking | yes | delayed_nudge_no_discount |
| cart_b19ee84b734a40 | distraction_or_multitasking | payment_method_unsupported | no | payment_link_alternate_methods_nudge |
| cart_df356b478e3744 | payment_method_unsupported | payment_method_unsupported | yes | payment_link_alternate_methods_nudge |
| cart_de894adfb1d84f | otp_delay_or_failure | payment_method_unsupported | no | payment_link_alternate_methods_nudge |
| cart_205574e490b148 | otp_delay_or_failure | otp_delay_or_failure | yes | immediate_payment_link_resend |
| cart_4d35be6023f24d | otp_delay_or_failure | payment_method_unsupported | no | payment_link_alternate_methods_nudge |
| cart_7c39787b5bfc49 | payment_method_unsupported | payment_method_unsupported | yes | payment_link_alternate_methods_nudge |
| cart_921935d1dae349 | price_shock | price_shock | yes | discounted_incentive_nudge |
| cart_9271e0fbed644a | payment_method_unsupported | payment_method_unsupported | yes | no_action_low_value |
| cart_17013e5e572d47 | distraction_or_multitasking | distraction_or_multitasking | yes | delayed_nudge_no_discount |
| cart_aaf5c0ff496a4e | trust_or_security_concern | trust_or_security_concern | yes | no_action_respect_hesitation |
| cart_f50b509fc06341 | trust_or_security_concern | trust_or_security_concern | yes | no_action_respect_hesitation |
| cart_cb63a1c72aed47 | trust_or_security_concern | trust_or_security_concern | yes | no_action_respect_hesitation |
| cart_b660d5bf4bd244 | otp_delay_or_failure | otp_delay_or_failure | yes | immediate_payment_link_resend |
| cart_f8c4958041504c | payment_method_unsupported | payment_method_unsupported | yes | payment_link_alternate_methods_nudge |
| cart_b95c29f0d42c46 | otp_delay_or_failure | payment_method_unsupported | no | payment_link_alternate_methods_nudge |
| cart_30d1293e3e3b40 | otp_delay_or_failure | otp_delay_or_failure | yes | no_action_low_value |
