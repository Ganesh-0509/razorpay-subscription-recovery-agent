"""
Unit tests for decline_codes.py - the deterministic policy table the gate
checks every LLM proposal against. If this table is wrong, the gate
enforces the wrong thing with total confidence, which is worse than no
gate at all.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from decline_codes import DECLINE_CODES, RecoveryAction, get_decline_code


def test_every_code_has_a_valid_recovery_action():
    for code, info in DECLINE_CODES.items():
        assert isinstance(info.allowed_action, RecoveryAction)


def test_fraud_code_is_never_a_retry_action():
    fraud = get_decline_code("payment_risk_check_failed")
    assert fraud.allowed_action == RecoveryAction.NO_ACTION_FRAUD
    assert fraud.simulated_success_rate == 0.0


def test_no_action_policies_have_zero_simulated_success_rate():
    for code, info in DECLINE_CODES.items():
        if info.allowed_action in (RecoveryAction.NO_ACTION_FRAUD, RecoveryAction.NO_ACTION_UNRECOVERABLE):
            assert info.simulated_success_rate == 0.0, f"{code} is a no-action policy but has a nonzero success rate"


def test_actionable_policies_have_a_plausible_success_rate():
    for code, info in DECLINE_CODES.items():
        if info.allowed_action not in (RecoveryAction.NO_ACTION_FRAUD, RecoveryAction.NO_ACTION_UNRECOVERABLE):
            assert 0.0 < info.simulated_success_rate <= 1.0, f"{code} has an implausible success rate"


def test_unknown_code_raises_keyerror():
    try:
        get_decline_code("not_a_real_code")
        assert False, "expected KeyError"
    except KeyError:
        pass


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
