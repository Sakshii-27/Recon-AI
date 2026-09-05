"""Centralized financial rules, rates, and deterministic calculation routines for Recon-AI.

All mathematical logic for fee deductions, GST withholding, and expected settlement
is strictly deterministic to ensure financial accuracy.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

# Default configurable financial constants
DEFAULT_MDR_RATE: float = 0.02         # 2.0% Merchant Discount Rate
DEFAULT_GST_ON_MDR: float = 0.18       # 18.0% GST on MDR fee
DEFAULT_CURRENCY: str = "INR"
DEFAULT_SEED: int = 42
DEFAULT_ROUNDING_TOLERANCE: float = 0.01  # Tolerance in currency units (1 paisa)


def round_currency(value: float) -> float:
    """Rounds a float value to 2 decimal places using standard half-up accounting rounding."""
    d = Decimal(str(value))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_mdr(captured_amount: float, mdr_rate: float = DEFAULT_MDR_RATE) -> float:
    """Calculates Merchant Discount Rate fee for a given captured amount.

    MDR = captured_amount * mdr_rate
    """
    return round_currency(captured_amount * mdr_rate)


def calculate_gst_on_mdr(mdr_amount: float, gst_rate: float = DEFAULT_GST_ON_MDR) -> float:
    """Calculates GST on the MDR fee.

    GST = MDR * gst_rate
    """
    return round_currency(mdr_amount * gst_rate)


def calculate_total_fee(
    captured_amount: float,
    mdr_rate: float = DEFAULT_MDR_RATE,
    gst_rate: float = DEFAULT_GST_ON_MDR
) -> Tuple[float, float, float]:
    """Calculates MDR, GST on MDR, and the combined gateway fee.

    Returns:
        (mdr, gst, total_fee)
    """
    mdr = calculate_mdr(captured_amount, mdr_rate)
    gst = calculate_gst_on_mdr(mdr, gst_rate)
    total_fee = round_currency(mdr + gst)
    return mdr, gst, total_fee


def calculate_expected_net_settlement(
    captured_amount: float,
    mdr_rate: float = DEFAULT_MDR_RATE,
    gst_rate: float = DEFAULT_GST_ON_MDR,
    refund_amount: float = 0.0,
    chargeback_amount: float = 0.0
) -> float:
    """Calculates the deterministic expected net payout from gateway to bank.

    Expected Net = Captured Amount - MDR - GST - Refund - Chargeback
    """
    mdr, gst, _ = calculate_total_fee(captured_amount, mdr_rate, gst_rate)
    net = captured_amount - mdr - gst - refund_amount - chargeback_amount
    return round_currency(net)
