"""Noise generation and realistic formatting variations for Recon-AI.

Introduces controlled real-world messiness into descriptions, references,
and payment narratives without corrupting data integrity.
"""

import random
from typing import List

PAYMENT_METHODS: List[str] = ["UPI", "Card", "NetBanking", "Wallet"]
PAYMENT_METHOD_WEIGHTS: List[float] = [0.55, 0.25, 0.15, 0.05]

BANK_NARRATION_TEMPLATES: List[str] = [
    "RAZORPAY SETTLEMENT {settlement_id}",
    "RZP PAYOUT {ref} UTR:{utr}",
    "PAYMENT GATEWAY CREDIT {settlement_id} VIA NEFT",
    "RAZORPAY NEFT SETTLEMENT {ref}",
    "CMS/RAZORPAY/{settlement_id}/NODAL",
    "SETTLEMENT REF {ref} / {utr}",
    "NEFT-RZP-PAYOUT-{settlement_id}",
    "COLLECTION CREDIT RZP {ref}",
]


def generate_order_reference(rng: random.Random, index: int) -> str:
    """Generates a realistic checkout or merchant reference string."""
    prefixes = ["WEB", "ORD", "INV", "CHK", "APP"]
    prefix = rng.choice(prefixes)
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    random_str = "".join(rng.choices(chars, k=5))
    return f"{prefix}-{random_str}"


def generate_utr(rng: random.Random) -> str:
    """Generates a standard Indian banking UTR (Unique Transaction Reference)."""
    bank_code = rng.choice(["HDFC", "ICIC", "UTIB", "SBIN", "KKBK", "PUNB"])
    digits = "".join(rng.choices("0123456789", k=12))
    return f"{bank_code}{digits}"


def generate_bank_description(
    rng: random.Random,
    settlement_id: str,
    ref: str,
    utr: str
) -> str:
    """Creates a realistic bank statement narration line with natural variability."""
    template = rng.choice(BANK_NARRATION_TEMPLATES)
    narration = template.format(settlement_id=settlement_id, ref=ref, utr=utr)

    # Controlled real-world noise: occasional uppercase/spacing variation
    rand_val = rng.random()
    if rand_val < 0.10:
        narration = narration + " "
    elif rand_val < 0.20:
        narration = narration.lower()
    return narration


def select_payment_method(rng: random.Random) -> str:
    """Picks a payment method matching realistic Indian fintech distributions."""
    return rng.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS, k=1)[0]
