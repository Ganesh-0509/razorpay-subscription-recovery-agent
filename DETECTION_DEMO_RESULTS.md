# DETECTION_DEMO_RESULTS

Live run of the new revenue-at-risk DETECTION stage (detect.py) against
the real local Ollama server (llama3.1:8b, temperature 0) - not mocked.

Records processed: **30** - a mixed pool of synthetic subscriptions (generate_detection_pool.py): some genuinely healthy (no decline_code, no retries, a recent successful charge), some genuinely at-risk (real retries, a stale gap since the last successful charge, a real decline code assigned as ground truth ONLY for scoring - never given to detect.py). This does NOT touch the 150-record flagship batch or the 30-record diagnosis demo - see BUILD_LOG.md and README.md §6 for what this subset does and does not prove.

- **Detection accuracy (classification matches ground truth): 30/30 (100.0%)**
- Detection failures (no usable tool call): **0**
- **False positives (healthy, wrongly flagged 'needs_recovery_attention'): 0** - of which **0** genuinely proceeded into the pipeline and triggered a real, wasted MCP tool call (typically flag_for_manual_review) on a customer who needed no such thing.
- **False negatives (at-risk, wrongly cleared 'leave_alone'): 0** - representing **Rs 0.00** of genuinely at-risk subscription value that was never diagnosed, gated, or attempted at all as a direct result of the wrong detection call.
- True positives: **16**, true negatives: **14**

## Per-record detail

| Subscription | Ground truth | Detected | Match | Final action |
|---|---|---|---|---|
| sub_e48794fdcfe44b | at_risk | needs_recovery_attention | yes | payment_link_nudge |
| sub_e3c656a0bc2d40 | at_risk | needs_recovery_attention | yes | payment_link_nudge |
| sub_702f5bd2a6324d | healthy | leave_alone | yes | left_alone_by_detection |
| sub_93e6556b9fbc47 | healthy | leave_alone | yes | left_alone_by_detection |
| sub_a8d47650f12c4a | healthy | leave_alone | yes | left_alone_by_detection |
| sub_031bffd9c60546 | healthy | leave_alone | yes | left_alone_by_detection |
| sub_b6a3b3adccdc4c | healthy | leave_alone | yes | left_alone_by_detection |
| sub_c71adf30dcd94c | at_risk | needs_recovery_attention | yes | payment_link_nudge |
| sub_f5086caf0c5749 | at_risk | needs_recovery_attention | yes | payment_link_nudge |
| sub_fa43efba3c1541 | at_risk | needs_recovery_attention | yes | no_action_unrecoverable |
| sub_4b63549606574d | healthy | leave_alone | yes | left_alone_by_detection |
| sub_86e64039cffd43 | at_risk | needs_recovery_attention | yes | delayed_retry |
| sub_dfd76f1e3b2842 | healthy | leave_alone | yes | left_alone_by_detection |
| sub_435cd48c9c364d | healthy | leave_alone | yes | left_alone_by_detection |
| sub_232b32f9d77646 | at_risk | needs_recovery_attention | yes | payment_link_nudge |
| sub_3d2c912b001442 | at_risk | needs_recovery_attention | yes | payment_link_nudge |
| sub_8bd77f8acde746 | at_risk | needs_recovery_attention | yes | no_action_unrecoverable |
| sub_fc92e4af871745 | healthy | leave_alone | yes | left_alone_by_detection |
| sub_7daf9ed867404e | at_risk | needs_recovery_attention | yes | no_action_unrecoverable |
| sub_434ae9de275740 | healthy | leave_alone | yes | left_alone_by_detection |
| sub_0ec8ff8d17b140 | at_risk | needs_recovery_attention | yes | payment_link_nudge |
| sub_9f529d8c418b4c | healthy | leave_alone | yes | left_alone_by_detection |
| sub_59853a39f0724b | at_risk | needs_recovery_attention | yes | delayed_retry |
| sub_116bebc701af40 | at_risk | needs_recovery_attention | yes | delayed_retry |
| sub_eb5948b0133043 | at_risk | needs_recovery_attention | yes | delayed_retry |
| sub_db9e026e8d1b48 | healthy | leave_alone | yes | left_alone_by_detection |
| sub_70ed737d1d444f | healthy | leave_alone | yes | left_alone_by_detection |
| sub_a9a27164ac284f | at_risk | needs_recovery_attention | yes | no_action_unrecoverable |
| sub_2da5f1b55b7c41 | healthy | leave_alone | yes | left_alone_by_detection |
| sub_ac7c0a7714d343 | at_risk | needs_recovery_attention | yes | payment_link_nudge |
