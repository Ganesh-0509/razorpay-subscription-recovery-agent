# INTEGRATED_RESULTS

One run, one shared in-process MCP client session, ONE mixed and
interleaved stream of records drawn from all four recovery domains -
dispatched per-record to the domain's own real, unmodified,
already-tested `process_one()` purely by identifying which of the
four known ID fields the record carries (`integrated_pipeline.py`'s
`identify_domain()`). Each domain's gate, policy table, and audit
log remain completely separate by design - see this file's module
docstring and BUILD_LOG.md §18 for exactly what 'integrated' does
and does not mean here. Same honesty caveat as every other results
file in this repo: `simulated_customer_response` is a labeled
synthetic assumption, not a real customer outcome.

- Records processed across all 4 domains (one mixed, interleaved stream): **16**
- Total value at risk across all domains: **Rs 715,110.36**
- Actions executed across all domains: **12**
- Simulated recovered value across all domains: **Rs 66,407.30**
- Dispatch correctness: **16/16** records carry the ID field their own bucket expects. This is 100% by construction, not a measured accuracy figure - `identify_domain()` raises before a record is ever processed if its domain can't be uniquely identified, so a record can never be silently misrouted; this line is a proof the guarantee held, not an estimate.

## By domain

| Domain | Records | Value at risk | Actions executed | Simulated recovered |
|---|---|---|---|---|
| subscription | 4 | Rs 912.56 | 4 | Rs 507.47 |
| one_time_payment | 4 | Rs 34,478.16 | 4 | Rs 18,891.39 |
| checkout_abandonment | 4 | Rs 1,607.27 | 2 | Rs 797.53 |
| overdue_receivable | 4 | Rs 678,112.37 | 2 | Rs 46,210.91 |
