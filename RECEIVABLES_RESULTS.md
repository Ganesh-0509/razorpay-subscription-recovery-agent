# RECEIVABLES_RESULTS

A NEW, standalone domain: overdue receivables (a B2B invoice that has
gone unpaid past its due date - no decline_code and no checkout funnel
exist here by definition; this domain revolves around an aging clock,
`days_overdue`, plus a business's own payment-history and communication
signals). Closes the LAST of the three category-scope gaps
(PS_REQUIREMENTS_DEBATE.md; README.md §6). Kept separate from the
150-record flagship pipeline and from checkout_abandonment_agent.py,
exactly like agent_onetime.py/route_demo.py already are - see
receivables_agent.py's module docstring for what is and isn't shared
with those pipelines. Same honesty caveat as RESULTS.md/
CHECKOUT_ABANDONMENT_RESULTS.md: `simulated_customer_response` is a
labeled synthetic assumption, not a real customer outcome.

- Overdue invoices processed: **30**
- Total overdue invoice value: **Rs 6,729,457.00**
- **Diagnosis accuracy (diagnosed_case_reason == true case_reason): 24/30 (80.0%)**
- Misdiagnoses that changed the final action versus what ground truth's own policy would have given: **6/30** - the concrete proof that a wrong diagnosis has real downstream consequences here too, mirroring DIAGNOSIS_DEMO_RESULTS.md's/CHECKOUT_ABANDONMENT_RESULTS.md's own measurement.
- Actions executed (reminders/payment-plan offers/escalations the gate let through): **6**
- Simulated recovered amount: **Rs 123,397.53** (4/6 executed actions 'succeeded' in simulation)

## By final action

| Final action | Count |
|---|---|
| escalate_to_manual_collections | 3 |
| firm_reminder_with_deadline | 2 |
| no_action_needs_dispute_review | 4 |
| no_action_needs_human_review | 17 |
| payment_plan_offer | 4 |

## Per-invoice detail

| Invoice | True reason | Diagnosed reason | Match | Final action |
|---|---|---|---|---|
| inv_d60c673820d442 | chronic_late_payer_will_eventually_pay | chronic_late_payer_will_eventually_pay | yes | no_action_needs_human_review |
| inv_9084afb8c2d248 | cash_flow_delay | cash_flow_delay | yes | payment_plan_offer |
| inv_8a93ce36d25344 | chronic_late_payer_will_eventually_pay | cash_flow_delay | no | no_action_needs_human_review |
| inv_1f8da7d02a8141 | chronic_late_payer_will_eventually_pay | chronic_late_payer_will_eventually_pay | yes | firm_reminder_with_deadline |
| inv_3aacca8eba6148 | invoice_dispute_likely | invoice_dispute_likely | yes | no_action_needs_dispute_review |
| inv_69842c0f749c48 | invoice_dispute_likely | invoice_dispute_likely | yes | no_action_needs_dispute_review |
| inv_d4b64e9131404f | payment_process_friction | cash_flow_delay | no | no_action_needs_human_review |
| inv_69f5608ccf4140 | payment_process_friction | cash_flow_delay | no | no_action_needs_human_review |
| inv_aeb1e673745049 | cash_flow_delay | cash_flow_delay | yes | no_action_needs_human_review |
| inv_d37a2e2cb0cd48 | chronic_late_payer_will_eventually_pay | chronic_late_payer_will_eventually_pay | yes | no_action_needs_human_review |
| inv_9c6587bbc9da43 | cash_flow_delay | cash_flow_delay | yes | no_action_needs_human_review |
| inv_940ce7a03f1548 | chronic_late_payer_will_eventually_pay | chronic_late_payer_will_eventually_pay | yes | firm_reminder_with_deadline |
| inv_f087d88829c240 | payment_process_friction | cash_flow_delay | no | no_action_needs_human_review |
| inv_a8ff8624a8d541 | chronic_late_payer_will_eventually_pay | chronic_late_payer_will_eventually_pay | yes | no_action_needs_human_review |
| inv_bf46fb4876b547 | high_risk_non_payment | high_risk_non_payment | yes | escalate_to_manual_collections |
| inv_6fe3d33245ac48 | chronic_late_payer_will_eventually_pay | cash_flow_delay | no | payment_plan_offer |
| inv_8a831f7acf1d46 | invoice_dispute_likely | invoice_dispute_likely | yes | no_action_needs_dispute_review |
| inv_3a42989e09664b | high_risk_non_payment | high_risk_non_payment | yes | escalate_to_manual_collections |
| inv_0c7c5b63b17441 | cash_flow_delay | cash_flow_delay | yes | no_action_needs_human_review |
| inv_aec19c294b464d | payment_process_friction | payment_process_friction | yes | no_action_needs_human_review |
| inv_ad7f8b84e6bb47 | invoice_dispute_likely | high_risk_non_payment | no | escalate_to_manual_collections |
| inv_047b195e51ef4b | cash_flow_delay | cash_flow_delay | yes | no_action_needs_human_review |
| inv_4b4e1ad87bf347 | cash_flow_delay | cash_flow_delay | yes | payment_plan_offer |
| inv_621bb1c2c0cd4b | chronic_late_payer_will_eventually_pay | chronic_late_payer_will_eventually_pay | yes | no_action_needs_human_review |
| inv_7ae3013a610944 | chronic_late_payer_will_eventually_pay | chronic_late_payer_will_eventually_pay | yes | no_action_needs_human_review |
| inv_cb71c485ad4e44 | cash_flow_delay | cash_flow_delay | yes | no_action_needs_human_review |
| inv_724c5407295c4e | invoice_dispute_likely | invoice_dispute_likely | yes | no_action_needs_dispute_review |
| inv_526e022bc0cc46 | cash_flow_delay | cash_flow_delay | yes | no_action_needs_human_review |
| inv_3bfe06ba4f3448 | cash_flow_delay | cash_flow_delay | yes | no_action_needs_human_review |
| inv_39916565c81245 | cash_flow_delay | cash_flow_delay | yes | payment_plan_offer |
