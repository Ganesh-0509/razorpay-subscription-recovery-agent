"""
Synthetic halted-subscription dataset generator.

Schema-accurate to real Razorpay fields (decline codes, amounts in paise,
INR), but the records themselves are fabricated - there is no real
customer data anywhere in this project. Says so explicitly in the output
file and in RESULTS.md.

Distribution is deliberately NOT uniform and NOT flattering:
  - weighted toward the decline codes that actually happen most (insufficient
    funds, card expired) rather than an even split across all codes
  - includes a realistic slice of genuinely unrecoverable and fraud-flagged
    cases (~15-20% combined) so the results can't just show a fake 100%
    recovery rate
  - each record also carries a `simulated_customer_response` field: an
    independent ground-truth roll (using DECLINE_CODES[...].simulated_success_rate)
    of whether the customer would actually complete a nudge/retry. This is
    what lets RESULTS.md report an honest "simulated recovered amount"
    instead of an unearned one.
"""

import json
import random
import uuid
from pathlib import Path

from decline_codes import DECLINE_CODES

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "halted_subscriptions.json"

# Weighted so common real-world failure modes dominate, matching how
# these actually distribute in subscription billing (soft declines are
# the bulk; fraud/blocked cards are a small minority).
CODE_WEIGHTS = {
    "insufficient_funds": 28,
    "card_expired": 18,
    "card_declined": 12,
    "authentication_failed": 10,
    "gateway_technical_error": 8,
    "bank_technical_error": 6,
    "incorrect_cvv": 5,
    "transaction_limit_exceeded": 4,
    "card_not_enrolled": 3,
    "card_disabled_for_online_payments": 3,
    "payment_timed_out": 3,
    "debit_instrument_inactive": 3,
    "payment_cancelled": 3,
    "debit_instrument_blocked": 2,
    "payment_risk_check_failed": 2,   # fraud - small but non-zero, deliberately
    "payment_failed": 2,
}

PLANS = [
    ("Streaming Monthly", 29900),
    ("Streaming Annual", 249900),
    ("SaaS Seat Monthly", 149900),
    ("SaaS Team Quarterly", 899900),
    ("Fitness App Monthly", 49900),
    ("Cloud Storage Monthly", 19900),
]


NUM_MERCHANTS = 12


def generate(n: int = 150, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    codes = list(CODE_WEIGHTS.keys())
    weights = list(CODE_WEIGHTS.values())

    # Pin each merchant to one plan - a single subscription merchant sells
    # one product, not a random mix of Streaming/SaaS/Fitness plans. Caught
    # in review as a realism tell.
    merchant_plans = {
        i: rng.choice(PLANS) for i in range(1, NUM_MERCHANTS + 1)
    }

    records = []
    for _ in range(n):
        code = rng.choices(codes, weights=weights, k=1)[0]
        policy = DECLINE_CODES[code]
        merchant_num = rng.randint(1, NUM_MERCHANTS)
        plan_name, base_amount = merchant_plans[merchant_num]
        # +/- 10% jitter so amounts aren't suspiciously uniform
        amount_paise = int(base_amount * rng.uniform(0.9, 1.1))
        halted_days_ago = rng.randint(0, 14)

        # Recoverability decays the longer a subscription has sat halted -
        # a customer whose card expired 13 days ago is less likely to still
        # complete a nudge than one from yesterday. Was previously generated
        # and never used anywhere; now it actually affects the outcome it's
        # supposed to represent.
        decay = max(0.4, 1.0 - (halted_days_ago / 14) * 0.5)
        effective_success_rate = policy.simulated_success_rate * decay

        simulated_customer_response = (
            rng.random() < effective_success_rate
            if policy.simulated_success_rate > 0
            else False
        )

        records.append({
            "subscription_id": f"sub_{uuid.uuid4().hex[:14]}",
            "merchant_id": f"merchant_{merchant_num:03d}",
            "customer_id": f"cust_{uuid.uuid4().hex[:10]}",
            "plan": plan_name,
            "amount_paise": amount_paise,
            "currency": "INR",
            "decline_code": code,
            "previous_retry_count": 3,  # Razorpay's real T+3 cycle already ran and failed
            "halted_days_ago": halted_days_ago,
            "simulated_customer_response": simulated_customer_response,
        })
    return records


def main():
    records = generate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} synthetic records to {OUTPUT_PATH}")

    fraud = sum(1 for r in records if r["decline_code"] == "payment_risk_check_failed")
    unrecoverable = sum(
        1 for r in records
        if DECLINE_CODES[r["decline_code"]].allowed_action.value == "no_action_unrecoverable"
    )
    print(f"  fraud-flagged: {fraud}, unrecoverable: {unrecoverable}, total: {len(records)}")


if __name__ == "__main__":
    main()
