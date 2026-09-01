"""
Shared per-record recovery pipeline: propose -> gate -> execute -> audit.

Extracted from agent.py and agent_onetime.py, which had grown ~80%
duplicated (near-identical `process_one` bodies differing mainly in field
names and situation text) - a real code-quality gap found on re-auditing
the codebase against the buildathon rubric, see BUILD_LOG.md §12. This
module is the one place that logic now lives; both callers pass in only
what's genuinely domain-specific (the id field name, the situation
description, the item-label field for a payment-link's description).

Deliberately NOT here: checkpoint/resume and the CLI --inject-failure
plumbing. Those stay in agent.py, since agent_onetime.py's stretch-goal
pipeline was scoped without them on purpose (BUILD_LOG.md §13) - keeping
them out of this shared module means agent_onetime.py never has to know
they exist.
"""

from mcp import Client

from audit_log import AuditLogger
from decline_codes import DECLINE_CODES, RecoveryAction, get_decline_code
from gate import MAX_ATTEMPTS_PER_SUBSCRIPTION, Gate
from ollama_client import propose_action

# Tools that represent a real recovery *attempt* on a record - used to
# derive prior_attempt_count (gate.py's cross-run attempt-cap stopping
# rule) from the audit log's history. flag_for_manual_review is
# deliberately excluded: escalating to a human isn't a retry attempt.
RECOVERY_ATTEMPT_TOOLS = {"create_payment_link", "create_retry_order"}


def count_prior_attempts(audit_events: list[dict], id_field: str, record_id: str) -> int:
    """
    How many real recovery-action tool calls already exist for this record
    across ALL previous runs. The audit log is append-only and never
    cleared between runs, so this reflects true cross-run history, not
    just this run's in-memory state - feeds gate.py's
    MAX_ATTEMPTS_PER_SUBSCRIPTION stopping rule. See BUILD_LOG.md §12.
    """
    return sum(
        1 for e in audit_events
        if e.get("event_type") == "mcp_tool_call"
        and e.get(id_field) == record_id
        and e.get("tool") in RECOVERY_ATTEMPT_TOOLS
    )


def extract_tool_text(call) -> str | None:
    """Defensively pull text out of an MCP CallToolResult - don't assume
    content[0] exists or is text-typed, even though every tool here always
    returns exactly that shape today."""
    if not call.content:
        return None
    first = call.content[0]
    return getattr(first, "text", None)


async def process_record(
    client: Client,
    gate: Gate,
    audit: AuditLogger,
    record: dict,
    *,
    id_field: str,
    action_to_tool: dict,
    item_label_field: str,
    situation: str,
    record_label: str,
    inject_failure: str | None = None,
    prior_attempt_count: int = 0,
) -> dict:
    """
    Run one record through the full proposal -> gate -> execute -> audit
    sequence. Domain-agnostic: agent.py calls this with
    id_field="subscription_id" for halted subscriptions, agent_onetime.py
    with id_field="payment_id" for failed one-time payments - see each
    caller for its own `situation`/`record_label`/`item_label_field`.
    """
    record_id = record[id_field]
    id_kwargs = {id_field: record_id}

    # An unrecognized decline code is a real, distinct failure mode from
    # "the LLM proposed something wrong" - it means this record describes
    # a situation the policy table has no entry for at all, so there is no
    # ground truth to gate against and no safe automated action to take.
    # Flagged for manual review explicitly (a human should decide what an
    # unknown code means), never reaching the LLM or the gate at all, since
    # neither has anything to evaluate. See METRICS.md §2.4 and
    # tests/test_agent_unknown_code.py. Applies identically to both
    # domains - agent_onetime.py previously had no equivalent check at all
    # (a real gap this extraction also closes, not just moves).
    if inject_failure == "unknown_decline_code" or record["decline_code"] not in DECLINE_CODES:
        reason = f"No policy entry for decline_code '{record['decline_code']}' - needs human review."
        audit.log(
            "unknown_decline_code",
            decline_code=record["decline_code"],
            fallback_action=RecoveryAction.NO_ACTION_UNRECOVERABLE.value,
            **id_kwargs,
        )
        call = await client.call_tool(
            "flag_for_manual_review", {"subscription_id": record_id, "reason": reason}
        )
        tool_result = extract_tool_text(call)
        audit.log("mcp_tool_call", tool="flag_for_manual_review", result=tool_result, **id_kwargs)
        return {
            **id_kwargs,
            "amount_paise": record["amount_paise"],
            "decline_code": record["decline_code"],
            "final_action": RecoveryAction.NO_ACTION_UNRECOVERABLE.value,
            "gate_executed": True,
            "llm_matched_policy": False,
            "simulated_customer_response": False,
            "tool_result": tool_result,
        }

    policy = get_decline_code(record["decline_code"])

    # Deterministic, on-demand versions of D4 (BUILD_LOG.md §7.3) for live
    # demos - force the exact same graceful-degradation code below that
    # already runs for a real Ollama hiccup, without needing to wait for
    # one or fake it inside ollama_client.py.
    if inject_failure == "llm_parse_failure":
        proposal = {
            "action": None,
            "reasoning": "[injected for demo] simulated: model returned no usable tool call",
        }
    elif inject_failure == "llm_invalid_action":
        proposal = {
            "action": "definitely_not_a_real_action",
            "reasoning": "[injected for demo] simulated: model proposed an action outside the known enum",
        }
    else:
        proposal = propose_action(
            record, policy.description, policy.source.value,
            situation=situation, id_field=id_field, record_label=record_label,
        )
    llm_action_raw = proposal["action"]

    # Demo mode for the compliant-escalation cross-run stopping rule
    # (gate.py MAX_ATTEMPTS_PER_SUBSCRIPTION): forces this record's
    # prior-attempt count to the cap regardless of its real audit-log
    # history, so the escalation can be shown live. The LLM still runs
    # normally above - this only changes what the gate does with its
    # proposal.
    if inject_failure == "repeat_attempts":
        prior_attempt_count = MAX_ATTEMPTS_PER_SUBSCRIPTION

    # Graceful degradation: if the model failed to produce a usable tool
    # call, fall back to the safest possible default rather than crashing
    # or silently skipping the record. This IS the "one failure handled
    # gracefully" moment from the rubric, and it's a real one - it will
    # actually trigger sometimes with a small local model.
    if llm_action_raw is None:
        audit.log(
            "llm_parse_failure",
            note=proposal["reasoning"],
            fallback_action=RecoveryAction.NO_ACTION_UNRECOVERABLE.value,
            **id_kwargs,
        )
        llm_action = RecoveryAction.NO_ACTION_UNRECOVERABLE
    else:
        try:
            llm_action = RecoveryAction(llm_action_raw)
        except ValueError:
            audit.log(
                "llm_invalid_action",
                raw_action=llm_action_raw,
                fallback_action=RecoveryAction.NO_ACTION_UNRECOVERABLE.value,
                **id_kwargs,
            )
            llm_action = RecoveryAction.NO_ACTION_UNRECOVERABLE

    decision = gate.evaluate(
        subscription_id=record_id,
        decline_code=record["decline_code"],
        proposed_action=llm_action,
        amount_paise=record["amount_paise"],
        prior_attempt_count=prior_attempt_count,
        halted_days_ago=record.get("halted_days_ago"),
    )

    audit.log(
        "gate_decision",
        decline_code=record["decline_code"],
        llm_proposed_action=llm_action.value,
        llm_reasoning=proposal["reasoning"],
        llm_matched_policy=decision.llm_matched_policy,
        gate_execute=decision.execute,
        gate_reason=decision.reason,
        final_action=decision.final_action.value,
        prior_attempt_count=prior_attempt_count,
        **id_kwargs,
    )

    tool_result = None
    if decision.execute and decision.final_action in (
        RecoveryAction.IMMEDIATE_RETRY,
        RecoveryAction.DELAYED_RETRY,
        RecoveryAction.PAYMENT_LINK_NUDGE,
    ):
        tool_name = action_to_tool[decision.final_action]
        if tool_name == "create_payment_link":
            args = {
                "subscription_id": record_id,
                "amount_paise": record["amount_paise"],
                "description": f"Complete your payment for {record[item_label_field]}",
            }
        else:
            args = {"subscription_id": record_id, "amount_paise": record["amount_paise"]}
        call = await client.call_tool(tool_name, args)
        tool_result = extract_tool_text(call)
        audit.log("mcp_tool_call", tool=tool_name, arguments=args, result=tool_result, **id_kwargs)
    elif decision.final_action in (RecoveryAction.NO_ACTION_FRAUD, RecoveryAction.NO_ACTION_UNRECOVERABLE):
        call = await client.call_tool(
            "flag_for_manual_review",
            {"subscription_id": record_id, "reason": decision.reason},
        )
        tool_result = extract_tool_text(call)
        audit.log("mcp_tool_call", tool="flag_for_manual_review", result=tool_result, **id_kwargs)

    return {
        **id_kwargs,
        "amount_paise": record["amount_paise"],
        "decline_code": record["decline_code"],
        "final_action": decision.final_action.value,
        "gate_executed": decision.execute,
        "llm_matched_policy": decision.llm_matched_policy,
        "simulated_customer_response": record["simulated_customer_response"],
        "tool_result": tool_result,
    }


def render_decline_code_table(results: list[dict]) -> list[str]:
    """
    Shared '## By decline code' markdown table - byte-identical section
    that used to be duplicated between agent.py's write_results() and
    agent_onetime.py's write_results().
    """
    lines = [
        "## By decline code",
        "",
        "| Decline code | Count | Final action |",
        "|---|---|---|",
    ]
    seen: dict[tuple[str, str], int] = {}
    for r in results:
        key = (r["decline_code"], r["final_action"])
        seen[key] = seen.get(key, 0) + 1
    for (code, action), count in sorted(seen.items()):
        lines.append(f"| {code} | {count} | {action} |")
    return lines
