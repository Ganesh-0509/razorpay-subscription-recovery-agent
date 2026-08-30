# REAL_MCP_RESULTS

Output of `real_mcp_demo.py` - real calls to Razorpay's test-mode
API through their own official MCP server (`razorpay/razorpay-mcp-server`
via Docker), using real `rzp_test_` keys. Unlike every other run in this
repo, nothing here is simulated: every ID below is a real object created
in a real (test-mode) Razorpay account.

| Subscription | Decline code | Action | Tool | Real Razorpay ID |
|---|---|---|---|---|
| sub_9acc7c13998447 | payment_timed_out | immediate_retry | create_retry_order | `order_TVya2xkz293ced` |
| sub_6290a50fdba748 | gateway_technical_error | immediate_retry | create_retry_order | `order_TVya4XdHthFVVR` |
| sub_cf5a67f7bcf846 | insufficient_funds | delayed_retry | create_retry_order | `order_TVya8ntYFOCcb7` |
| sub_f41bfcfd51474d | card_expired | payment_link_nudge | create_payment_link | `plink_TVyaB1NfbPJerN` |
| sub_140d9d8513774b | authentication_failed | payment_link_nudge | create_payment_link | `plink_TVyaCtXyLz50Rk` |
