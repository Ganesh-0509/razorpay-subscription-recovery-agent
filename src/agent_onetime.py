"""
The one-time-payment sibling of agent.py - proves the gate/policy/audit-log
pattern generalizes beyond subscriptions, using the exact same Gate,
decline-code policy (config/decline_policy.json), MCP server tools, and
Ollama proposal model. Nothing about the safety architecture changes; only
the situation description and record shape passed into propose_action do
(see ollama_client.py's propose_action docstring).

Key domain difference from agent.py, stated plainly: a subscription
reaches this codebase only AFTER Razorpay's own 3-day/3-attempt retry
cycle already failed (BUILD_LOG.md §1). A one-time payment has no such
cycle - Razorpay does nothing further automatically after a single failed
checkout attempt, so this agent is the first and only thing that ever
looks at the failure, not a last resort. The LLM is told this explicitly
via a different `situation` string, since "retry after Razorpay already
retried 3 times" and "retry after Razorpay never retried at all" are
different situations that could warrant different judgment.

Deliberately simpler than agent.py: no checkpoint/resume. The one-time
pipeline runs a small batch (default 30, not 150) as a stretch-goal
demonstration of reuse, not a second full production pipeline - see
BUILD_LOG.md §13 for why checkpointing wasn't considered worth building
twice for this scope.
"""

import asyncio
import json
from pathlib import Path

from mcp import Client

from audit_log import AuditLogger
from decline_codes import RecoveryAction, get_decline_code
from gate import Gate
from mcp_server import server as mcp_server
from ollama_client import propose_action

DATA_PATH = Path(__file__).parent.parent / "data" / "failed_onetime_payments.json"
AUDIT_PATH = Path(__file__).parent.parent / "logs" / "audit_log_onetime.jsonl"
RESULTS_PATH = Path(__file__).parent.parent / "RESULTS_ONETIME.md"

SITUATION = (
    "A one-time payment failed at checkout. Unlike a subscription, Razorpay "
    "has no automatic retry cycle for one-time payments - this failure is "
    "immediate and has not been retried by anything yet."
)

ACTION_TO_TOOL = {
    RecoveryAction.IMMEDIATE_RETRY: "create_retry_order",
    RecoveryAction.DELAYED_RETRY: "create_retry_order",
    RecoveryAction.PAYMENT_LINK_NUDGE: "create_payment_link",
    RecoveryAction.NO_ACTION_FRAUD: "flag_for_manual_review",
    RecoveryAction.NO_ACTION_UNRECOVERABLE: "flag_for_manual_review",
}


async def process_one(client: Client, gate: Gate, audit: AuditLogger, pay: dict) -> dict:
    policy = get_decline_code(pay["decline_code"])

    proposal = propose_action(
        pay,
        policy.description,
        policy.source.value,
        situation=SITUATION,
        id_field="payment_id",
        record_label="Payment",
    )
    llm_action_raw = proposal["action"]

    if llm_action_raw is None:
        audit.log(
            "llm_parse_failure",
            payment_id=pay["payment_id"],
            note=proposal["reasoning"],
            fallback_action=RecoveryAction.NO_ACTION_UNRECOVERABLE.value,
        )
        llm_action = RecoveryAction.NO_ACTION_UNRECOVERABLE
    else:
        try:
            llm_action = RecoveryAction(llm_action_raw)
        except ValueError:
            audit.log(
                "llm_invalid_action",
                payment_id=pay["payment_id"],
                raw_action=llm_action_raw,
                fallback_action=RecoveryAction.NO_ACTION_UNRECOVERABLE.value,
            )
            llm_action = RecoveryAction.NO_ACTION_UNRECOVERABLE

    decision = gate.evaluate(
        subscription_id=pay["payment_id"],  # Gate is domain-agnostic - just a string key
        decline_code=pay["decline_code"],
        proposed_action=llm_action,
        amount_paise=pay["amount_paise"],
    )

    audit.log(
        "gate_decision",
        payment_id=pay["payment_id"],
        decline_code=pay["decline_code"],
        llm_proposed_action=llm_action.value,
        llm_reasoning=proposal["reasoning"],
        llm_matched_policy=decision.llm_matched_policy,
        gate_execute=decision.execute,
        gate_reason=decision.reason,
        final_action=decision.final_action.value,
    )

    tool_result = None
    if decision.execute and decision.final_action in (
        RecoveryAction.IMMEDIATE_RETRY,
        RecoveryAction.DELAYED_RETRY,
        RecoveryAction.PAYMENT_LINK_NUDGE,
    ):
        tool_name = ACTION_TO_TOOL[decision.final_action]
        if tool_name == "create_payment_link":
            args = {
                "subscription_id": pay["payment_id"],  # MCP tools use this key name generically
                "amount_paise": pay["amount_paise"],
                "description": f"Complete your payment for {pay['item']}",
            }
        else:
            args = {"subscription_id": pay["payment_id"], "amount_paise": pay["amount_paise"]}
        call = await client.call_tool(tool_name, args)
        tool_result = call.content[0].text if call.content else None
        audit.log("mcp_tool_call", payment_id=pay["payment_id"], tool=tool_name, arguments=args, result=tool_result)
    elif decision.final_action in (RecoveryAction.NO_ACTION_FRAUD, RecoveryAction.NO_ACTION_UNRECOVERABLE):
        call = await client.call_tool(
            "flag_for_manual_review", {"subscription_id": pay["payment_id"], "reason": decision.reason}
        )
        tool_result = call.content[0].text if call.content else None
        audit.log("mcp_tool_call", payment_id=pay["payment_id"], tool="flag_for_manual_review", result=tool_result)

    return {
        "payment_id": pay["payment_id"],
        "amount_paise": pay["amount_paise"],
        "decline_code": pay["decline_code"],
        "final_action": decision.final_action.value,
        "gate_executed": decision.execute,
        "llm_matched_policy": decision.llm_matched_policy,
        "simulated_customer_response": pay["simulated_customer_response"],
    }


async def run():
    if not DATA_PATH.exists():
        raise SystemExit("No data found. Run `python generate_data_onetime.py` first.")

    payments = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    gate = Gate()
    audit = AuditLogger(AUDIT_PATH)
    audit.log("run_started", total_payments=len(payments))
    print(f"Processing {len(payments)} failed one-time payments...")

    results = []
    async with Client(mcp_server) as client:
        for pay in payments:
            try:
                result = await process_one(client, gate, audit, pay)
            except Exception as e:
                audit.log("record_processing_error", payment_id=pay["payment_id"], error=str(e))
                result = {
                    "payment_id": pay["payment_id"],
                    "amount_paise": pay["amount_paise"],
                    "decline_code": pay["decline_code"],
                    "final_action": "no_action_unrecoverable",
                    "gate_executed": False,
                    "llm_matched_policy": False,
                    "simulated_customer_response": False,
                }
            results.append(result)
            print(f"{pay['payment_id']}  {pay['decline_code']:24s} -> {result['final_action']}")

    audit.log("run_finished", total_processed=len(results))
    write_results(results)


def write_results(results: list[dict]):
    acted_actions = {"immediate_retry", "delayed_retry", "payment_link_nudge"}
    total_paise = sum(r["amount_paise"] for r in results)
    acted_on = [r for r in results if r["final_action"] in acted_actions and r["gate_executed"]]
    recovered = [r for r in acted_on if r["simulated_customer_response"]]
    recovered_paise = sum(r["amount_paise"] for r in recovered)
    overridden = [r for r in results if not r["llm_matched_policy"]]

    lines = [
        "# RESULTS_ONETIME",
        "",
        "Stretch goal: the same gate/policy/audit-log pattern applied to failed",
        "ONE-TIME payments instead of halted subscriptions - see `agent_onetime.py`",
        "and BUILD_LOG.md §13. Same honesty caveat as RESULTS.md: "
        "`simulated_customer_response` is a labeled synthetic assumption, not a",
        "real payment outcome.",
        "",
        f"- Total failed one-time payments processed: **{len(results)}**",
        f"- Total value: **Rs {total_paise/100:,.2f}**",
        f"- Actions executed (retries/nudges the gate let through): **{len(acted_on)}**",
        f"- Simulated recovered amount: **Rs {recovered_paise/100:,.2f}** "
        f"({len(recovered)}/{len(acted_on)} executed actions 'succeeded' in simulation)",
        f"- LLM proposals the gate had to override: **{len(overridden)}/{len(results)}** "
        f"({len(overridden)/len(results)*100:.0f}%)",
        "",
        "## By decline code",
        "",
        "| Decline code | Count | Final action |",
        "|---|---|---|",
    ]
    seen = {}
    for r in results:
        key = (r["decline_code"], r["final_action"])
        seen[key] = seen.get(key, 0) + 1
    for (code, action), count in sorted(seen.items()):
        lines.append(f"| {code} | {count} | {action} |")

    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {RESULTS_PATH}")


if __name__ == "__main__":
    asyncio.run(run())
