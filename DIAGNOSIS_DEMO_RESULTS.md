# DIAGNOSIS_DEMO_RESULTS

Live run of the new root-cause diagnosis stage (diagnose.py) against
the real local Ollama server (llama3.1:8b, temperature 0) - not mocked.

Records processed: **30** (the first 30 of the seeded, already-committed 150-record `data/halted_subscriptions.json` - a deterministic slice, not cherry-picked). This does NOT re-run the full 150-record flagship batch - see BUILD_LOG.md and README.md §6 for why, and for exactly what this subset does and does not prove.

- **Diagnosis accuracy (diagnosed_decline_code == true decline_code): 27/30 (90.0%)**
- Misdiagnoses: **3/30**, of which diagnosis failures (no usable tool call / unrecognized code returned): **0**
- Misdiagnoses that changed the final recovery action versus what ground truth's own policy would have given: **0/30** in this particular slice - a coincidence of which ambiguity clusters happened to appear in these 30 records, not evidence that a wrong diagnosis can't change the outcome. Said plainly: this does NOT mean a wrong diagnosis can't change the final action - it means none of this specific slice's 3 misdiagnoses happened to cross an action boundary. The actual proof that a wrong diagnosis has real downstream consequences is `tests/test_diagnosis_pipeline.py::test_wrong_diagnosis_changes_the_final_action_real_downstream_consequences`, which mocks exactly that case and asserts the gate executes the wrong policy's action.

## Per-record detail

| Subscription | Raw message | True code | Diagnosed code | Match | Final action |
|---|---|---|---|---|---|
| sub_2c794247ffee4f | Transaction expired - payment session timed out before completion. | payment_timed_out | payment_timed_out | yes | immediate_retry |
| sub_ab3172c242d241 | Decline reason from issuer: low balance at time of debit. | insufficient_funds | insufficient_funds | yes | delayed_retry |
| sub_8611bd9d249947 | Payment gateway reported an internal processing error; no funds were debited. | gateway_technical_error | gateway_technical_error | yes | immediate_retry |
| sub_49211741b37b4d | Bank response: transaction exceeds the daily/per-transaction limit set on this card. | transaction_limit_exceeded | transaction_limit_exceeded | yes | delayed_retry |
| sub_bd31c471dfd343 | Issuer declined - card expiry date has lapsed. | card_expired | card_expired | yes | no_action_unrecoverable |
| sub_d003227e889948 | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | delayed_retry |
| sub_f5451c0fee9045 | Issuer declined: spend limit reached for this account today. | transaction_limit_exceeded | transaction_limit_exceeded | yes | delayed_retry |
| sub_c93b04be438e43 | Issuer declined - card expiry date has lapsed. | card_expired | card_expired | yes | payment_link_nudge |
| sub_7a6094c0a34f42 | Bank declined: card not enabled for card-not-present use. | card_disabled_for_online_payments | card_not_enrolled | no | payment_link_nudge |
| sub_bc7b22e318c14c | Decline reason from issuer: low balance at time of debit. | insufficient_funds | insufficient_funds | yes | no_action_unrecoverable |
| sub_4024e87a918948 | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | no_action_unrecoverable |
| sub_a3a50e248e6941 | Card verification failed: card has passed its valid-thru date. | card_expired | card_expired | yes | payment_link_nudge |
| sub_55c13f2df11347 | Acquirer-side technical failure while routing this transaction. | gateway_technical_error | gateway_technical_error | yes | immediate_retry |
| sub_589bcac10e9946 | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | no_action_unrecoverable |
| sub_d1ee5fb009ef49 | OTP/3-D Secure verification failed for this transaction. | authentication_failed | authentication_failed | yes | no_action_unrecoverable |
| sub_3ae01a69857f40 | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | delayed_retry |
| sub_cb994cd3103b49 | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | delayed_retry |
| sub_56a63b4669ee4e | Generic decline from issuing bank - no error detail returned. | card_declined | card_declined | yes | payment_link_nudge |
| sub_e6654c94707e46 | Issuer declined: CVV/CVV2 verification failed. | incorrect_cvv | incorrect_cvv | yes | payment_link_nudge |
| sub_a3bc4fbcedf048 | Payment did not go through during the authentication step. | authentication_failed | authentication_failed | yes | payment_link_nudge |
| sub_43bea9822b6349 | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | delayed_retry |
| sub_95e4149b2b204a | Bank response: transaction exceeds the daily/per-transaction limit set on this card. | transaction_limit_exceeded | transaction_limit_exceeded | yes | delayed_retry |
| sub_70c1f0e5586143 | Bank declined this transaction with no further reason provided. | payment_failed | payment_failed | yes | payment_link_nudge |
| sub_7a7404c44b634d | Decline reason from issuer: low balance at time of debit. | insufficient_funds | insufficient_funds | yes | no_action_unrecoverable |
| sub_5e6c66817dca42 | Card verification failed: card has passed its valid-thru date. | card_expired | card_expired | yes | payment_link_nudge |
| sub_735194aa7e6b4a | Issuer response: do not honor. | card_declined | payment_failed | no | payment_link_nudge |
| sub_3e678a7ea0454b | Issuer declined: CVV/CVV2 verification failed. | incorrect_cvv | incorrect_cvv | yes | no_action_unrecoverable |
| sub_ec9f21acd72240 | Issuer response: online/e-commerce transactions are disabled on this card. | card_disabled_for_online_payments | card_not_enrolled | no | payment_link_nudge |
| sub_38e038dd811a48 | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | delayed_retry |
| sub_c5982eb23f824f | Bank response: insufficient balance in account to complete this transaction. | insufficient_funds | insufficient_funds | yes | no_action_unrecoverable |
