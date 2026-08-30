# ROUTE_RESULTS (stretch goal)

Two-sided split settlement via Razorpay Route. A referral partner earns 5% of each recovered subscription attributed to them, split at order-creation time via a Route transfer - not a manual payout step.

Linked Account used: `acc_sim_partner001` (simulated - no real Linked Account was onboarded for this build, see BUILD_LOG.md §7.4).

- Recoveries processed: **5**
- Route transfers executed: **4**
- Blocked by the spending-cap gate: **1** (demonstrates the cap applies here too, not just in the main pipeline)
- Total partner payout across executed transfers: **Rs 664.80**

## Per transaction

| Subscription | Referrer | Amount | Partner share | Status |
|---|---|---|---|---|
| sub_route_demo_001 | partner_affiliate_01 | Rs 1,499.00 | Rs 74.95 | executed |
| sub_route_demo_002 | partner_affiliate_02 | Rs 8,999.00 | Rs 449.95 | executed |
| sub_route_demo_003 | partner_affiliate_01 | Rs 299.00 | Rs 14.95 | executed |
| sub_route_demo_004 | partner_affiliate_03 | Rs 550,000.00 | Rs 27,500.00 | BLOCKED (cap) |
| sub_route_demo_005 | partner_affiliate_02 | Rs 2,499.00 | Rs 124.95 | executed |
