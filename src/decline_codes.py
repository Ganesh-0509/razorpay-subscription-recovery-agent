"""
Real Razorpay card decline codes (razorpay.com/docs/errors/payments/cards/)
and the recovery policy we apply to each one.

This table is the deterministic ground truth. The agent's LLM proposes an
action per subscription, but the gate (see gate.py) checks every proposal
against ALLOWED_ACTIONS here and overrides anything out of policy. The LLM
never gets the final word on a money action.

RecoveryAction values:
  IMMEDIATE_RETRY      - transient failure, safe to retry right away
  DELAYED_RETRY        - customer-side issue likely to clear with time
                          (e.g. payday), retry after a cooldown
  PAYMENT_LINK_NUDGE   - can't safely auto-retry; send the customer a
                          payment link to fix it themselves
  NO_ACTION_FRAUD      - risk-flagged; never retry, flag to merchant only
  NO_ACTION_UNRECOVERABLE - customer-cancelled or blocked; nothing to do
"""

from dataclasses import dataclass
from enum import Enum


class RecoveryAction(str, Enum):
    IMMEDIATE_RETRY = "immediate_retry"
    DELAYED_RETRY = "delayed_retry"
    PAYMENT_LINK_NUDGE = "payment_link_nudge"
    NO_ACTION_FRAUD = "no_action_fraud"
    NO_ACTION_UNRECOVERABLE = "no_action_unrecoverable"


class DeclineSource(str, Enum):
    CUSTOMER = "customer"
    BANK = "bank"
    GATEWAY = "gateway"
    NETWORK = "network"


@dataclass(frozen=True)
class DeclineCode:
    code: str
    description: str
    source: DeclineSource
    allowed_action: RecoveryAction
    # Rough probability a nudge/retry actually succeeds, used ONLY by the
    # synthetic customer-response simulator in generate_data.py. This is a
    # labeled assumption, not a measured real-world rate - see BUILD_LOG.md §6.2.
    simulated_success_rate: float


DECLINE_CODES: dict[str, DeclineCode] = {
    "insufficient_funds": DeclineCode(
        "insufficient_funds",
        "The customer's bank account did not have enough funds",
        DeclineSource.CUSTOMER,
        RecoveryAction.DELAYED_RETRY,
        0.55,
    ),
    "card_expired": DeclineCode(
        "card_expired",
        "Customer's card has passed its expiration date",
        DeclineSource.CUSTOMER,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.35,
    ),
    "card_not_enrolled": DeclineCode(
        "card_not_enrolled",
        "Card lacks activation for digital transactions",
        DeclineSource.BANK,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.30,
    ),
    "card_disabled_for_online_payments": DeclineCode(
        "card_disabled_for_online_payments",
        "Card not enabled for online transaction use",
        DeclineSource.CUSTOMER,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.30,
    ),
    "incorrect_cvv": DeclineCode(
        "incorrect_cvv",
        "The customer entered an incorrect CVV",
        DeclineSource.CUSTOMER,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.45,
    ),
    "authentication_failed": DeclineCode(
        "authentication_failed",
        "Incorrect OTP entry or browser closure during verification",
        DeclineSource.CUSTOMER,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.40,
    ),
    "debit_instrument_blocked": DeclineCode(
        "debit_instrument_blocked",
        "Card blocked by customer or bank",
        DeclineSource.BANK,
        RecoveryAction.NO_ACTION_UNRECOVERABLE,
        0.0,
    ),
    "debit_instrument_inactive": DeclineCode(
        "debit_instrument_inactive",
        "Card not activated for online use",
        DeclineSource.BANK,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.25,
    ),
    "transaction_limit_exceeded": DeclineCode(
        "transaction_limit_exceeded",
        "The customer has already reached the maximum transaction limit for the day",
        DeclineSource.CUSTOMER,
        RecoveryAction.DELAYED_RETRY,
        0.60,
    ),
    "payment_timed_out": DeclineCode(
        "payment_timed_out",
        "The payment could not be completed as the customer exceeded the time limit",
        DeclineSource.NETWORK,
        RecoveryAction.IMMEDIATE_RETRY,
        0.50,
    ),
    "gateway_technical_error": DeclineCode(
        "gateway_technical_error",
        "Partner bank downtime prevented payment processing",
        DeclineSource.GATEWAY,
        RecoveryAction.IMMEDIATE_RETRY,
        0.65,
    ),
    "bank_technical_error": DeclineCode(
        "bank_technical_error",
        "Customer's bank experienced downtime",
        DeclineSource.BANK,
        RecoveryAction.IMMEDIATE_RETRY,
        0.60,
    ),
    "card_declined": DeclineCode(
        "card_declined",
        "The payment was declined by the customer's bank",
        DeclineSource.BANK,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.25,
    ),
    "payment_risk_check_failed": DeclineCode(
        "payment_risk_check_failed",
        "The customer's bank declined the payment, citing it as fraudulent",
        DeclineSource.BANK,
        RecoveryAction.NO_ACTION_FRAUD,
        0.0,
    ),
    "payment_cancelled": DeclineCode(
        "payment_cancelled",
        "Customer terminated the transaction or navigated away during processing",
        DeclineSource.CUSTOMER,
        RecoveryAction.NO_ACTION_UNRECOVERABLE,
        0.0,
    ),
    "payment_failed": DeclineCode(
        "payment_failed",
        "The payment was declined by the customer's bank",
        DeclineSource.BANK,
        RecoveryAction.PAYMENT_LINK_NUDGE,
        0.20,
    ),
}


def get_decline_code(code: str) -> DeclineCode:
    if code not in DECLINE_CODES:
        raise KeyError(f"Unknown decline code: {code!r}")
    return DECLINE_CODES[code]
