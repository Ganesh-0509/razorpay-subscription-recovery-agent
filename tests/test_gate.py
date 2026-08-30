"""
Unit tests for the gate - the one file in this project that must be
trustworthy independent of any LLM behaving correctly.
Run with: .venv/Scripts/python.exe -m pytest tests/ -v
(or just: .venv/Scripts/python.exe tests/test_gate.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from decline_codes import RecoveryAction
from gate import MAX_ACTION_AMOUNT_PAISE, Gate


def test_gate_executes_correct_policy_action():
    gate = Gate()
    decision = gate.evaluate("sub_1", "insufficient_funds", RecoveryAction.DELAYED_RETRY, 29900)
    assert decision.execute
    assert decision.llm_matched_policy
    assert decision.final_action == RecoveryAction.DELAYED_RETRY


def test_gate_overrides_llm_but_still_executes_corrected_action():
    gate = Gate()
    # insufficient_funds policy is DELAYED_RETRY, not IMMEDIATE_RETRY
    decision = gate.evaluate("sub_2", "insufficient_funds", RecoveryAction.IMMEDIATE_RETRY, 29900)
    assert not decision.llm_matched_policy
    assert decision.execute  # override, not a block - the corrected action still runs
    assert decision.final_action == RecoveryAction.DELAYED_RETRY


def test_gate_never_allows_retry_on_fraud_even_if_llm_proposes_it():
    gate = Gate()
    decision = gate.evaluate("sub_3", "payment_risk_check_failed", RecoveryAction.IMMEDIATE_RETRY, 29900)
    assert not decision.llm_matched_policy
    assert decision.final_action == RecoveryAction.NO_ACTION_FRAUD
    assert decision.execute  # "executing" a no-action policy just means refusing


def test_gate_respects_fraud_policy_when_llm_gets_it_right():
    gate = Gate()
    decision = gate.evaluate("sub_4", "payment_risk_check_failed", RecoveryAction.NO_ACTION_FRAUD, 29900)
    assert decision.llm_matched_policy
    assert decision.final_action == RecoveryAction.NO_ACTION_FRAUD


def test_gate_hard_blocks_amount_over_cap():
    gate = Gate()
    decision = gate.evaluate(
        "sub_5", "insufficient_funds", RecoveryAction.DELAYED_RETRY, MAX_ACTION_AMOUNT_PAISE + 1
    )
    assert not decision.execute
    assert decision.final_action == RecoveryAction.NO_ACTION_UNRECOVERABLE


def test_gate_hard_blocks_duplicate_action_same_run():
    gate = Gate()
    first = gate.evaluate("sub_6", "insufficient_funds", RecoveryAction.DELAYED_RETRY, 29900)
    second = gate.evaluate("sub_6", "insufficient_funds", RecoveryAction.DELAYED_RETRY, 29900)
    assert first.execute
    assert not second.execute


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    if failures:
        raise SystemExit(1)
