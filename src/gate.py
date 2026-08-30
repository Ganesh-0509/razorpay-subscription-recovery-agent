"""
The gate: plain deterministic code, no LLM involved. Every action the agent
wants to take passes through here before anything touches Razorpay.

Three checks, in order:
  1. Policy check   - is this action even allowed for this decline code?
                       (overrides the LLM if it proposed something off-policy)
  2. Spending cap    - does this action's amount exceed the hard per-action
                       and per-run limits?
  3. Idempotency     - has this exact (subscription_id, action) already been
                       executed in this run? Refuse to double-act.

This is deliberately the least "AI" file in the whole project. A gate that
depends on the model behaving isn't a gate.
"""

from dataclasses import dataclass

from decline_codes import RecoveryAction, get_decline_code

MAX_ACTION_AMOUNT_PAISE = 50_000 * 100      # ₹50,000 per single action
MAX_RUN_TOTAL_PAISE = 5_00_000 * 100        # ₹5,00,000 total per run


@dataclass
class GateDecision:
    # Whether the LLM's raw proposal matched policy exactly (a metric on the
    # model, not on the system - the system may still `execute` a corrected
    # action even when this is False).
    llm_matched_policy: bool
    # Whether the gate will actually carry out `final_action` at all. Only
    # False for the hard blocks: spending cap exceeded or duplicate action.
    execute: bool
    reason: str
    final_action: RecoveryAction


class Gate:
    def __init__(self):
        self._seen: set[tuple[str, str]] = set()
        self._run_total_paise = 0

    def seed_from_checkpoint(self, already_spent_paise: int, seen_keys: set[tuple[str, str]]):
        """
        Resumed runs skip re-evaluating checkpointed records entirely, so
        the gate's in-memory spending/idempotency state would otherwise
        start from zero and under-count what a resumed run has already
        committed. Call this once, right after construction, with totals
        derived from the checkpoint.
        """
        self._run_total_paise = already_spent_paise
        self._seen |= seen_keys

    def evaluate(
        self,
        subscription_id: str,
        decline_code: str,
        proposed_action: RecoveryAction,
        amount_paise: int,
    ) -> GateDecision:
        policy = get_decline_code(decline_code)
        llm_matched_policy = proposed_action == policy.allowed_action
        final_action = policy.allowed_action  # policy always wins, LLM never does

        override_note = (
            "" if llm_matched_policy else
            f" (LLM proposed '{proposed_action.value}', policy overrode to "
            f"'{final_action.value}')"
        )

        # A policy-mandated no-action never touches money - nothing to gate
        # on amount/idempotency, always executes (the "action" is refusing).
        if final_action in (RecoveryAction.NO_ACTION_FRAUD, RecoveryAction.NO_ACTION_UNRECOVERABLE):
            return GateDecision(
                llm_matched_policy=llm_matched_policy,
                execute=True,
                reason=f"No-action policy for '{decline_code}' ({policy.source.value} source){override_note}.",
                final_action=final_action,
            )

        # Hard block: per-action spending cap.
        if amount_paise > MAX_ACTION_AMOUNT_PAISE:
            return GateDecision(
                llm_matched_policy=llm_matched_policy,
                execute=False,
                reason=(
                    f"Amount {amount_paise/100:.2f} exceeds per-action cap "
                    f"of {MAX_ACTION_AMOUNT_PAISE/100:.2f}."
                ),
                final_action=RecoveryAction.NO_ACTION_UNRECOVERABLE,
            )

        # Hard block: run-total spending cap.
        if self._run_total_paise + amount_paise > MAX_RUN_TOTAL_PAISE:
            return GateDecision(
                llm_matched_policy=llm_matched_policy,
                execute=False,
                reason="Run-total spending cap would be exceeded.",
                final_action=RecoveryAction.NO_ACTION_UNRECOVERABLE,
            )

        # Hard block: idempotency - same subscription + same final action
        # already executed this run.
        key = (subscription_id, final_action.value)
        if key in self._seen:
            return GateDecision(
                llm_matched_policy=llm_matched_policy,
                execute=False,
                reason=f"Duplicate action for {subscription_id} - already processed this run.",
                final_action=RecoveryAction.NO_ACTION_UNRECOVERABLE,
            )

        self._seen.add(key)
        self._run_total_paise += amount_paise
        return GateDecision(
            llm_matched_policy=llm_matched_policy,
            execute=True,
            reason=f"Passed spending cap and idempotency checks{override_note}.",
            final_action=final_action,
        )
