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
                    "description": (
                        "Choose exactly one. "
                        "'immediate_retry' = transient technical/network failure, safe to retry now. "
                        "'delayed_retry' = customer-side issue likely to clear with time (e.g. low balance), retry after a cooldown. "
                        "'payment_link_nudge' = can't safely auto-retry; ask the customer to fix it themselves via a link. "
                        "'no_action_fraud' = ONLY if this specific decline was flagged by the bank as fraud/risk — never retry, flag for human review. Do NOT use this for ordinary technical or funds failures that are simply not worth retrying; that is a different option. "
                        "'no_action_unrecoverable' = customer cancelled, or the card/instrument is blocked — nothing to do, and it is NOT a fraud case."
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


def propose_action(subscription: dict, decline_description: str, decline_source: str) -> dict:
    """
    Ask the local model to propose an action for one halted subscription.
    Returns {"action": str, "reasoning": str} or {"action": None, "reasoning": "<failure note>"}
    on ANY failure - malformed tool call, HTTP error, timeout, whatever. This
    function is designed to never raise: the caller (agent.py) treats a None
    action as "fall back to the safest policy action", which keeps a single
    Ollama hiccup from crashing a 150-record batch run. This retry+fallback
    behavior exists because it was missing during the first real batch run
    and Ollama's transient 500 killed the whole run - see BUILD_LOG.md.
    """
    prompt = (
        f"A subscription payment was halted after Razorpay's automatic 3-day "
        f"retry cycle failed 3 times.\n\n"
        f"Subscription: {subscription['subscription_id']}\n"
        f"Amount: Rs {subscription['amount_paise'] / 100:.2f}\n"
        f"Decline code: {subscription['decline_code']}\n"
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
