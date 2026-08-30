# Razorpay AI Buildathon — Subscription Recovery Agent

[![tests](https://github.com/Ganesh-0509/razorpay-subscription-recovery-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/Ganesh-0509/razorpay-subscription-recovery-agent/actions/workflows/tests.yml)

**Track 1: AI Growth & Agentic Commerce**

An agent that picks up exactly where Razorpay's own subscription engine
gives up. Razorpay auto-retries a failed recurring payment 3 times over 3
days (T+3); if all 3 fail, the subscription moves to a `halted` state and
nothing tries again automatically. This project builds a small, honest,
guardrailed agent that decides what to do with those halted subscriptions
next — modeled after the pattern in Razorpay's own [Agent Studio][studio]
(built on Anthropic's Claude Agent SDK, exposed via MCP), but running
entirely free and local.

Razorpay's Agent Studio already ships a production Subscription Recovery
Agent — we picked this exact problem on purpose, not to compete with it,
but to prove the same proposal/execution-separation and audit-trail
pattern from first principles. Full reasoning in `BUILD_LOG.md` §1.1.

| | Their Subscription Recovery Agent | This project |
|---|---|---|
| Recovery mechanism | Voice call to the subscriber (ElevenLabs) | Payment link / automated retry |
| Guardrail logic | Internal certification process (closed) | One human-readable Python table, `decline_codes.py` |
| Audit trail | Hosted dashboard summary ("what/when") | Raw per-decision JSONL, LLM reasoning + gate override reasoning both logged |
| Access | Sales-assisted early access (Typeform) | Runs today, $0, personal test-mode account |

[studio]: https://razorpay.com/agent-studio/

## Known limitations (said up front, not buried)

- **Single point of enforcement, not defense-in-depth.** The gate is only
  ever consulted because `agent.py` chooses to call it — the MCP tools
  themselves have no policy checks of their own. Fine for this project's
  scope; a real multi-caller production system would need the check moved
  inside the tool itself.
- **Idempotency is unit-tested but never exercised at batch scale.** No
  `subscription_id` repeats in the synthetic 150-record set by
  construction, so `RESULTS.md`'s "hard-blocked: 0" proves the check
  passes in isolation (`tests/test_gate.py`), not that it's been
  triggered under real batch conditions.
- **Simulate-mode is the only path that has processed all 150 records so
  far.** The official-MCP-server integration is implemented and its tool
  schemas verified live, but a real end-to-end call with real test-mode
  keys is still pending — see `BUILD_LOG.md` §12 for the full list.

Full project docs: [`BUILD_LOG.md`](BUILD_LOG.md) (problem statement, every
technical decision with reasoning, architecture, protocol, gate design,
real results — the single source of truth) ·
[`EASY_EXPLAINER.md`](EASY_EXPLAINER.md) (plain-language walkthrough, one
running example throughout) ·
[`GLOSSARY.md`](GLOSSARY.md) (every term used, defined) ·
[`METRICS.md`](METRICS.md) (every number verified directly against the raw
audit log, including the LLM's exact error patterns)

## The policy is one editable table, not a black box

A merchant doesn't need to retrain anything to change how a decline code is
handled — `src/decline_codes.py` is a plain Python dict. For example, to
stop nudging expired cards with a payment link and switch to an immediate
retry instead, the entire change is:

```diff
     "card_expired": DeclineCode(
         "card_expired",
         "Customer's card has passed its expiration date",
         DeclineSource.CUSTOMER,
-        RecoveryAction.PAYMENT_LINK_NUDGE,
+        RecoveryAction.IMMEDIATE_RETRY,
         0.35,
     ),
```

`tests/test_decline_codes.py` and the gate's own unit tests still pass
unchanged — the policy table and the enforcement code are fully decoupled.

## Architecture

```
Synthetic halted-subscription data
        │
        ▼
   Agent (Ollama, local, tool-calling model)  ── proposes an action
        │
        ▼
   GATE  (plain deterministic code, no LLM)   ── validates/overrides
        │  spending cap · decline-code policy · idempotency
        ▼
   OUR MCP SERVER  (real MCP protocol)         ── executes
        │  create_payment_link · create_retry_order · flag_for_manual_review
        ▼
   real keys set? ──▶ Razorpay's OWN OFFICIAL MCP server (razorpay/razorpay-mcp-server)
        │
   no keys?        ──▶ in-process simulate mode (razorpay_client.py)
        ▼
   audit_log.jsonl  ◄── every decision (act or refuse) from every step above
```

The gate is the load-bearing safety design: the LLM only ever *proposes* a
structured decision through a single `record_decision` tool call — it never
directly calls a money-moving tool. A separate, deterministic layer checks
every proposal against a fixed decline-code policy table and hard spending
caps before anything reaches Razorpay, and overrides the LLM whenever it's
wrong (which, with a small local model, happens often — see `RESULTS.md`
after a run for the real override rate).

When real test-mode keys are set, the two money-moving tools
(`create_payment_link`, `create_retry_order`) route through **Razorpay's
own official MCP server** (github.com/razorpay/razorpay-mcp-server, Docker
image `mcp/razorpay`) instead of a hand-rolled SDK wrapper — see
`razorpay_mcp_client.py` and `BUILD_LOG.md` §2.2. Its full tool list was checked
directly and has no Route/transfer tools, so the Route stretch goal below
still goes through our own SDK wrapper.

## Stretch goal: Route (split settlement)

```bash
cd src
python route_demo.py   # writes ROUTE_RESULTS.md
```

Standalone scenario, separate from the main pipeline: a referral partner
earns a percentage of a recovered subscription via a Razorpay Route
transfer, split at order-creation time. Uses a simulated Linked Account ID
by default (`acc_sim_partner001`) since onboarding a real one is a manual
Razorpay dashboard step; also demonstrates the same spending-cap gate
blocking an oversized transfer.

## Cost: $0

Everything here runs free — see `BUILD_LOG.md` §2.1 for the full breakdown.
Razorpay test mode needs no KYC, no payment method, no live keys. The agent
model runs locally via Ollama, not a paid API.

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# Optional: real Razorpay test-mode keys (free, no KYC, from dashboard.razorpay.com)
# If skipped, everything runs in simulate mode automatically.
copy .env.example .env
# edit .env with your rzp_test_ keys

# Requires Ollama running locally with a tool-calling model pulled, e.g.:
ollama pull llama3.1:8b
```

## Run

```bash
cd src
python generate_data.py   # writes data/halted_subscriptions.json (synthetic)
python agent.py            # runs the full pipeline, writes RESULTS.md and logs/audit_log.jsonl
```

## Tests

```bash
python tests/test_gate.py
python tests/test_decline_codes.py
```

The gate has unit tests independent of the LLM — it must be correct even
when the model isn't, since that's the entire point of having it. The
decline-code policy table is tested separately: if that table is wrong,
the gate enforces the wrong thing with total confidence.

## What broke during development

Documented in full in `BUILD_LOG.md` §3.6/§12, kept in because it's real:
1. First version of the gate conflated "the LLM's proposal was denied" with
   "no action should be taken" — meaning every LLM policy mismatch silently
   skipped execution instead of running the corrected action. Caught by a
   5-record smoke test before the full run, fixed by splitting the gate's
   decision into `llm_matched_policy` (a metric on the model) and `execute`
   (whether the corrected action actually runs).
2. The first full 150-record run crashed outright on a transient Ollama 500
   — traced to the model being reloaded from disk on every single call
   (~20s each) instead of staying resident, which also made the whole run
   impractically slow. Fixed with `keep_alive`, request retry/backoff, and
   a per-record try/except so one bad record can never take down the batch.
3. The batch run got killed by the execution environment mid-run, twice.
   Rather than just relaunch and hope, made the pipeline checkpointed and
   resumable (`logs/results_checkpoint.jsonl`) — confirmed working when a
   second kill at 141/150 resumed and finished cleanly with zero lost work.
4. An independent audit caught that the LLM's ~87% policy-override rate was
   partly self-inflicted: the tool schema gave the model an action enum
   with no per-value explanation, so it was reading `no_action_fraud` as a
   generic "no action needed" bucket rather than "this is specifically
   fraud" — confirmed by sampling cases where its own stated reasoning said
   "not fraudulent" right before it picked `no_action_fraud` anyway. Fixed
   by spelling out exactly what each action means (and when not to use it)
   in the tool schema.
