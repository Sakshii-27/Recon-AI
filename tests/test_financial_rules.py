"""Tests for centralized financial calculations and deterministic rules."""

import pytest
from backend.app.domain.finance_rules import (
    DEFAULT_GST_ON_MDR,
    DEFAULT_MDR_RATE,
    calculate_expected_net_settlement,
    calculate_gst_on_mdr,
    calculate_mdr,
    calculate_total_fee,
    round_currency,
)


def test_standard_mdr_gst_example_from_specification():
    """Validates the exact example from specification:
    Capture = ₹10,000
    MDR (2%) = ₹200
    GST on MDR (18%) = ₹36
    Expected Net = ₹9,764.00
    """
    captured = 10000.00
    mdr = calculate_mdr(captured, DEFAULT_MDR_RATE)
    assert mdr == 200.00

    gst = calculate_gst_on_mdr(mdr, DEFAULT_GST_ON_MDR)
    assert gst == 36.00

    net = calculate_expected_net_settlement(captured, DEFAULT_MDR_RATE, DEFAULT_GST_ON_MDR)
    assert net == 9764.00


def test_calculate_total_fee():
    captured = 25000.00
    mdr, gst, total = calculate_total_fee(captured, 0.02, 0.18)
    assert mdr == 500.00
    assert gst == 90.00
    assert total == 590.00


def test_settlement_with_refund_and_chargeback():
    captured = 12500.00
    refund = 2500.00
    chargeback = 1000.00
    mdr = calculate_mdr(captured, 0.02)      # 250.00
    gst = calculate_gst_on_mdr(mdr, 0.18)    # 45.00
    expected = 12500.00 - 250.00 - 45.00 - 2500.00 - 1000.00  # 8705.00

    net = calculate_expected_net_settlement(
        captured,
        0.02,
        0.18,
        refund_amount=refund,
        chargeback_amount=chargeback,
    )
    assert net == expected


def test_round_currency_half_up():
    assert round_currency(10.004) == 10.00
    assert round_currency(10.005) == 10.01
    assert round_currency(10.006) == 10.01
