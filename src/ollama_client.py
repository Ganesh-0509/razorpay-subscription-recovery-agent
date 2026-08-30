"""
Minimal wrapper around Ollama's local /api/chat endpoint (free, runs on
your machine, no API key, no bill). The agent uses this ONLY to get the
model to propose a structured decision - it never lets the model call the
real Razorpay-facing MCP tools directly. See BUILD_LOG.md §3.1/§5 for why
that split matters.
"""

import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

DECIDE_ACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "record_decision",
        "description": (
            "Record your decision for what to do about this halted subscription. "
            "This does NOT execute anything by itself - a separate policy gate "
            "reviews and can override this decision before any real action happens."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "immediate_retry",
                        "delayed_retry",
                        "payment_link_nudge",
                        "no_action_fraud",
                        "no_action_unrecoverable",
                    ],
                    # Per-value meanings spelled out explicitly. Root-caused a
                    # real bug from this: without this, the model was reading
                    # "no_action_fraud" as a generic "no action needed" bucket
                    # and picking it for cases it explicitly reasoned were NOT
                    # fraud (e.g. reasoning "not a fraudulent transaction" ->
                    # action no_action_fraud). See BUILD_LOG.md.
                    # Rewritten as an ordered decision rule + worked examples after
                    # analyzing 69 real gate overrides: the plain per-value
                    # descriptions below still left two systematic biases -
                    # (a) reading any customer-fixable card issue (expired,
                    # disabled, wrong CVV) as "unrecoverable" instead of
                    # "nudge them to fix it", and (b) ignoring decline_source
                    # and defaulting to "wait and retry" for technical/bank
                    # failures that should retry immediately, or for
                    # ambiguous declines that actually need a payment link.
                    # See METRICS.md §2.2 for the exact confusion counts this
                    # targets.
                    "description": (
                        "Choose exactly one action. Apply these rules in order:\n"
                        "1. Bank flagged this decline specifically as fraud/risk -> 'no_action_fraud'.\n"
                        "2. The CUSTOMER must personally do something before this can ever succeed "
                        "(supply a new/updated card, enter a correct CVV, re-authenticate, activate "
                        "the card for online use) -> 'payment_link_nudge'. This includes an expired "
                        "card, a card disabled or inactive for online use, a wrong CVV, or a failed "
                        "OTP/authentication. These are customer-FIXABLE, not unrecoverable.\n"
                        "3. decline_source is 'network', 'gateway', or 'bank' AND it's a system/"
                        "infrastructure failure (timeout, downtime, technical error) that is nobody's "
                        "fault and may already be resolved -> 'immediate_retry'.\n"
                        "4. decline_source is 'customer' AND the issue is about available funds or a "
                        "transaction limit, not the payment method itself -> 'delayed_retry' (give it "
                        "time to clear, e.g. next payday).\n"
                        "5. ONLY if the customer explicitly cancelled/walked away, or the bank has "
                        "permanently blocked/closed the instrument with no customer fix available -> "
                        "'no_action_unrecoverable'. Do NOT use this for a merely expired, disabled, "
                        "inactive, or wrong-CVV card - those are rule 2.\n\n"
                        "Worked examples: card_expired -> payment_link_nudge (customer supplies a new "
                        "card, not unrecoverable). payment_timed_out, source=network -> immediate_retry "
                        "(infra failure, nobody's fault). insufficient_funds, source=customer -> "
                        "delayed_retry (funds issue, may clear with time). customer cancelled the "
                        "transaction -> no_action_unrecoverable."
                    ),
                },
                "reasoning": {
                    "type": "string",
                    "description": "One or two sentences on why this action fits this case.",
                },
            },
            "required": ["action", "reasoning"],
        },
    },
}


MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 3


DEFAULT_SITUATION = (
    "A subscription payment was halted after Razorpay's automatic 3-day "
    "retry cycle failed 3 times."
)


def propose_action(
    record: dict,
    decline_description: str,
    decline_source: str,
    situation: str = DEFAULT_SITUATION,
    id_field: str = "subscription_id",
    record_label: str = "Subscription",
) -> dict:
    """
    Ask the local model to propose an action for one failed payment record.
    Returns {"action": str, "reasoning": str} or {"action": None, "reasoning": "<failure note>"}
    on ANY failure - malformed tool call, HTTP error, timeout, whatever. This
    function is designed to never raise: the caller (agent.py) treats a None
    action as "fall back to the safest policy action", which keeps a single
    Ollama hiccup from crashing a 150-record batch run. This retry+fallback
    behavior exists because it was missing during the first real batch run
    and Ollama's transient 500 killed the whole run - see BUILD_LOG.md.

    `situation`/`id_field`/`record_label` default to reproduce the original
    halted-subscription prompt exactly (agent.py calls this with only the
    first three positional args). agent_onetime.py passes different values
    to reuse this same function - and the same gate, policy, and MCP tools -
    for a domain where Razorpay has no automatic retry cycle at all: a
    failed one-time payment. See BUILD_LOG.md §13.
    """
    prompt = (
        f"{situation}\n\n"
        f"{record_label}: {record[id_field]}\n"
        f"Amount: Rs {record['amount_paise'] / 100:.2f}\n"
        f"Decline code: {record['decline_code']}\n"
        f"Decline description: {decline_description}\n"
        f"Decline source: {decline_source}\n\n"
        f"Call record_decision with the single best next action and a short reason."
    )

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "tools": [DECIDE_ACTION_TOOL],
                    "stream": False,
                    # Keep the model resident between calls - without this,
                    # Ollama was reloading ~5GB from disk on every single
                    # call (~20s each) and eventually 500'd under the churn.
                    "keep_alive": "30m",
                    # This is a policy classification task, not creative
                    # generation - deterministic output is the correct
                    # default here, not Ollama's ~0.8 sampling temperature.
                    "options": {"temperature": 0},
                },
                timeout=120,
            )
            resp.raise_for_status()
            message = resp.json().get("message", {})
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                return {"action": None, "reasoning": "Model returned no tool call."}

            args = tool_calls[0].get("function", {}).get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    return {"action": None, "reasoning": "Model returned malformed tool-call arguments."}

            action = args.get("action")
            reasoning = args.get("reasoning", "")
            if not action:
                return {"action": None, "reasoning": "Model tool call missing 'action' field."}

            return {"action": action, "reasoning": reasoning}

        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    return {"action": None, "reasoning": f"Ollama request failed after {MAX_RETRIES} attempts: {last_error}"}
