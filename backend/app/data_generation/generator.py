"""Core synthetic data generator for Recon-AI.

Generates realistic ERP Orders, Gateway Transactions, Gateway Settlements,
and Bank Statement records, alongside strictly isolated Ground Truth metadata.
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.app.domain.finance_rules import (
    DEFAULT_CURRENCY,
    DEFAULT_GST_ON_MDR,
    DEFAULT_MDR_RATE,
    DEFAULT_SEED,
    calculate_expected_net_settlement,
    calculate_gst_on_mdr,
    calculate_mdr,
    calculate_total_fee,
    round_currency,
)
from backend.app.domain.models import (
    BankTransaction,
    ERPOrder,
    GatewaySettlement,
    GatewayTransaction,
    GroundTruthCase,
)
from backend.app.data_generation.noise import (
    generate_bank_description,
    generate_order_reference,
    generate_utr,
    select_payment_method,
)
from backend.app.data_generation.scenarios import (
    ScenarioType,
    plan_scenario_distribution,
)


class SyntheticDataGenerator:
    """Generates synthetic multi-source financial datasets with controlled edge cases."""

    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        mdr_rate: float = DEFAULT_MDR_RATE,
        gst_rate: float = DEFAULT_GST_ON_MDR,
        base_date: str = "2026-08-15",
        opening_balance: float = 500000.00,
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.mdr_rate = mdr_rate
        self.gst_rate = gst_rate
        self.base_date = datetime.strptime(base_date, "%Y-%m-%d")
        self.opening_balance = opening_balance

        # Sequence counters
        self.order_counter = 10001
        self.txn_counter = 50001
        self.settlement_counter = 1
        self.bank_counter = 80001
        self.case_counter = 1

    def _random_date(self, max_days_offset: int = 12) -> str:
        offset = self.rng.randint(0, max_days_offset)
        d = self.base_date + timedelta(days=offset)
        return d.strftime("%Y-%m-%d")

    def _add_days(self, date_str: str, days: int) -> str:
        d = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=days)
        return d.strftime("%Y-%m-%d")

    def _next_order_id(self) -> str:
        val = f"ORD-{self.order_counter}"
        self.order_counter += 1
        return val

    def _next_txn_id(self) -> str:
        val = f"TXN-{self.txn_counter}"
        self.txn_counter += 1
        return val

    def _next_settlement_id(self, date_str: str) -> str:
        date_clean = date_str.replace("-", "")
        val = f"SET-{date_clean}-{self.settlement_counter:03d}"
        self.settlement_counter += 1
        return val

    def _next_bank_id(self) -> str:
        val = f"BANK-{self.bank_counter}"
        self.bank_counter += 1
        return val

    def _next_case_id(self) -> str:
        val = f"CASE-{self.case_counter:04d}"
        self.case_counter += 1
        return val

    def generate_dataset(
        self, total_cases: int = 100
    ) -> Tuple[
        List[ERPOrder],
        List[GatewayTransaction],
        List[GatewaySettlement],
        List[BankTransaction],
        List[GroundTruthCase],
    ]:
        """Generates all 3 sources of data plus the isolated ground truth."""
        # Reset RNG with initial seed for deterministic output
        self.rng = random.Random(self.seed)

        erp_orders: List[ERPOrder] = []
        gateway_txns: List[GatewayTransaction] = []
        settlements: List[GatewaySettlement] = []
        bank_txns: List[BankTransaction] = []
        ground_truth: List[GroundTruthCase] = []

        scenario_counts = plan_scenario_distribution(total_cases)

        for scenario, count in scenario_counts.items():
            for i in range(count):
                self._generate_scenario_case(
                    scenario=scenario,
                    index=i,
                    erp_orders=erp_orders,
                    gateway_txns=gateway_txns,
                    settlements=settlements,
                    bank_txns=bank_txns,
                    ground_truth=ground_truth,
                )

        # Sort bank transactions chronologically and compute running balance
        bank_txns.sort(key=lambda b: (b.transaction_date, b.bank_transaction_id))
        current_balance = self.opening_balance
        for b in bank_txns:
            current_balance = round_currency(
                current_balance + b.credit_amount - b.debit_amount
            )
            b.balance = current_balance

        return erp_orders, gateway_txns, settlements, bank_txns, ground_truth

    def _generate_scenario_case(
        self,
        scenario: ScenarioType,
        index: int,
        erp_orders: List[ERPOrder],
        gateway_txns: List[GatewayTransaction],
        settlements: List[GatewaySettlement],
        bank_txns: List[BankTransaction],
        ground_truth: List[GroundTruthCase],
    ) -> None:
        case_id = self._next_case_id()
        order_date = self._random_date(10)
        pay_method = select_payment_method(self.rng)
        customer_id = f"CUS-{self.rng.randint(1000, 9999)}"

        # Realistic price tiers (₹350 to ₹65,000)
        base_amounts = [
            499.0, 750.0, 1200.0, 2450.0, 3999.0, 4850.0,
            6200.0, 8500.0, 12500.0, 18900.0, 24000.0, 35000.0
        ]
        gross = self.rng.choice(base_amounts)

        if scenario == ScenarioType.EXACT_MATCH:
            # 1:1 match where bank settlement equals exact captured amount (pre-paid/invoiced fee structure)
            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=0.0,
                gst_on_fee=0.0,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=0.0,
                total_gst=0.0,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=gross,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description=desc,
                reference=order_ref,
                credit_amount=gross,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr,
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="1_TO_1",
                    expected_net_amount=gross,
                    actual_bank_amount=gross,
                    root_cause=None,
                    is_exception=False,
                    description="Exact 1:1 match across ERP, Gateway, and Bank statement.",
                )
            )

        elif scenario == ScenarioType.MDR_GST:
            # Net settlement with standard MDR 2% + GST 18%
            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            mdr, gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)
            net = calculate_expected_net_settlement(gross, self.mdr_rate, self.gst_rate)

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=mdr,
                total_gst=gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=net,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description=desc,
                reference=settlement_id,
                credit_amount=net,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr,
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="1_TO_1",
                    expected_net_amount=net,
                    actual_bank_amount=net,
                    root_cause=None,
                    is_exception=False,
                    description=f"Standard settlement net of MDR (₹{mdr:.2f}) and GST (₹{gst:.2f}).",
                )
            )

        elif scenario in (ScenarioType.T_PLUS_1, ScenarioType.T_PLUS_2):
            days_delay = 1 if scenario == ScenarioType.T_PLUS_1 else 2
            settle_date = self._add_days(order_date, days_delay)

            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(settle_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            mdr, gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)
            net = calculate_expected_net_settlement(gross, self.mdr_rate, self.gst_rate)

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=settle_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=settle_date,
                gross_amount=gross,
                total_mdr=mdr,
                total_gst=gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=net,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=settle_date,
                description=desc,
                reference=settlement_id,
                credit_amount=net,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr,
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="1_TO_1",
                    expected_net_amount=net,
                    actual_bank_amount=net,
                    root_cause=None,
                    is_exception=False,
                    description=f"Settled with {days_delay}-day delay on {settle_date}.",
                )
            )

        elif scenario == ScenarioType.BATCH_SETTLEMENT:
            # 2 to 4 transactions bundled into a single gateway settlement batch and one bank credit
            num_bundled = self.rng.choice([2, 3, 4])
            settle_date = self._add_days(order_date, 1)
            settlement_id = self._next_settlement_id(settle_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            batch_order_ids: List[str] = []
            batch_txn_ids: List[str] = []
            total_gross = 0.0
            total_mdr = 0.0
            total_gst = 0.0

            for _ in range(num_bundled):
                item_gross = self.rng.choice([1000.0, 2000.0, 2500.0, 3000.0, 4200.0, 5000.0])
                item_order_id = self._next_order_id()
                item_ref = generate_order_reference(self.rng, self.order_counter)
                item_txn_id = self._next_txn_id()
                item_method = select_payment_method(self.rng)

                mdr, gst, _ = calculate_total_fee(item_gross, self.mdr_rate, self.gst_rate)
                total_gross = round_currency(total_gross + item_gross)
                total_mdr = round_currency(total_mdr + mdr)
                total_gst = round_currency(total_gst + gst)

                erp = ERPOrder(
                    order_id=item_order_id,
                    order_reference=item_ref,
                    order_date=order_date,
                    customer_id=f"CUS-{self.rng.randint(1000, 9999)}",
                    gross_amount=item_gross,
                    currency=DEFAULT_CURRENCY,
                    payment_method=item_method,
                    order_status="PAID",
                )
                gtw = GatewayTransaction(
                    gateway_transaction_id=item_txn_id,
                    order_reference=item_ref,
                    captured_amount=item_gross,
                    transaction_date=order_date,
                    payment_status="CAPTURED",
                    payment_method=item_method,
                    gateway_fee=mdr,
                    gst_on_fee=gst,
                    refund_amount=0.0,
                    chargeback_amount=0.0,
                    settlement_id=settlement_id,
                    settlement_date=settle_date,
                )
                erp_orders.append(erp)
                gateway_txns.append(gtw)
                batch_order_ids.append(item_order_id)
                batch_txn_ids.append(item_txn_id)

            batch_net = round_currency(total_gross - total_mdr - total_gst)
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=settle_date,
                gross_amount=total_gross,
                total_mdr=total_mdr,
                total_gst=total_gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=batch_net,
                transaction_ids=batch_txn_ids,
            )
            desc = generate_bank_description(self.rng, settlement_id, settlement_id, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=settle_date,
                description=desc,
                reference=settlement_id,
                credit_amount=batch_net,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr,
            )
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=batch_order_ids,
                    gateway_transaction_ids=batch_txn_ids,
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="N_TO_1",
                    expected_net_amount=batch_net,
                    actual_bank_amount=batch_net,
                    root_cause=None,
                    is_exception=False,
                    description=f"Batch payout bundling {num_bundled} transactions into one deposit.",
                )
            )

        elif scenario == ScenarioType.REFUND:
            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            # Customer refund of 30% to 100%
            refund_amount = round_currency(gross * self.rng.choice([0.5, 1.0]))
            mdr, gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)
            net = calculate_expected_net_settlement(
                gross, self.mdr_rate, self.gst_rate, refund_amount=refund_amount
            )

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="REFUNDED" if refund_amount == gross else "PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="REFUNDED" if refund_amount == gross else "CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=refund_amount,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=mdr,
                total_gst=gst,
                refunds=refund_amount,
                chargebacks=0.0,
                net_settlement=net,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)

            # If full refund resulted in net <= 0, bank transaction might be 0 or small debit/credit
            credit_val = max(0.0, net)
            debit_val = abs(net) if net < 0 else 0.0

            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description=desc,
                reference=settlement_id,
                credit_amount=credit_val,
                debit_amount=debit_val,
                balance=0.0,
                bank_utr=utr,
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="1_TO_1",
                    expected_net_amount=net,
                    actual_bank_amount=credit_val - debit_val,
                    root_cause=None,
                    is_exception=False,
                    description=f"Transaction settlement reduced by refund of ₹{refund_amount:.2f}.",
                )
            )

        elif scenario == ScenarioType.CHARGEBACK:
            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            chargeback_amount = gross  # Full disputed amount
            mdr, gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)
            net = calculate_expected_net_settlement(
                gross, self.mdr_rate, self.gst_rate, chargeback_amount=chargeback_amount
            )

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method="Card",
                order_status="PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="DISPUTED",
                payment_method="Card",
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=chargeback_amount,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=mdr,
                total_gst=gst,
                refunds=0.0,
                chargebacks=chargeback_amount,
                net_settlement=net,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description=desc,
                reference=settlement_id,
                credit_amount=0.0,
                debit_amount=round_currency(abs(net)) if net < 0 else 0.0,
                balance=0.0,
                bank_utr=utr,
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="1_TO_1",
                    expected_net_amount=net,
                    actual_bank_amount=0.0,
                    root_cause="CHARGEBACK",
                    is_exception=True,
                    description=f"Chargeback dispute clawback of ₹{chargeback_amount:.2f}.",
                )
            )

        elif scenario == ScenarioType.PARTIAL_SETTLEMENT:
            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            net = calculate_expected_net_settlement(gross, self.mdr_rate, self.gst_rate)
            partial_credit = round_currency(net * 0.60)  # Bank received only 60%

            mdr, gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=mdr,
                total_gst=gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=net,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description=desc,
                reference=settlement_id,
                credit_amount=partial_credit,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr,
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="1_TO_1",
                    expected_net_amount=net,
                    actual_bank_amount=partial_credit,
                    root_cause="PARTIAL_SETTLEMENT",
                    is_exception=True,
                    description=f"Partial payout: expected ₹{net:.2f}, bank received ₹{partial_credit:.2f}.",
                )
            )

        elif scenario == ScenarioType.DUPLICATE:
            # Duplicate gateway capture for same ERP order (double charge)
            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id1 = self._next_txn_id()
            txn_id2 = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id1 = self._next_bank_id()
            utr1 = generate_utr(self.rng)

            mdr, gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)
            net = calculate_expected_net_settlement(gross, self.mdr_rate, self.gst_rate)

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="PAID",
            )
            gtw1 = GatewayTransaction(
                gateway_transaction_id=txn_id1,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            # Duplicate transaction record
            gtw2 = GatewayTransaction(
                gateway_transaction_id=txn_id2,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=mdr,
                total_gst=gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=net,
                transaction_ids=[txn_id1],
            )
            desc1 = generate_bank_description(self.rng, settlement_id, order_ref, utr1)
            bnk1 = BankTransaction(
                bank_transaction_id=bank_id1,
                transaction_date=order_date,
                description=desc1,
                reference=settlement_id,
                credit_amount=net,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr1,
            )
            erp_orders.append(erp)
            gateway_txns.extend([gtw1, gtw2])
            settlements.append(stl)
            bank_txns.append(bnk1)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id1, txn_id2],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id1],
                    expected_relationship="1_TO_N",
                    expected_net_amount=net,
                    actual_bank_amount=net,
                    root_cause="DUPLICATE",
                    is_exception=True,
                    description=f"Duplicate gateway capture ({txn_id2}) for single ERP order ({order_id}).",
                )
            )

        elif scenario == ScenarioType.MISSING_BANK:
            # Payment captured and settlement issued, but bank record never arrived!
            # Special highlighted case: SET-1042 / ₹48,200.00 for demo story if index == 0
            if index == 0:
                gross_missing = 50000.00
                settlement_id = "SET-1042"
                target_net = 48200.00  # ₹48,200 net
                mdr = 1525.42
                gst = 274.58
            else:
                gross_missing = gross
                settlement_id = self._next_settlement_id(order_date)
                mdr, gst, _ = calculate_total_fee(gross_missing, self.mdr_rate, self.gst_rate)
                target_net = calculate_expected_net_settlement(gross_missing, self.mdr_rate, self.gst_rate)

            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross_missing,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross_missing,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross_missing,
                total_mdr=mdr,
                total_gst=gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=target_net,
                transaction_ids=[txn_id],
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            # INTENTIONALLY NO BANK TRANSACTION ADDED

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[],
                    expected_relationship="1_TO_0",
                    expected_net_amount=target_net,
                    actual_bank_amount=None,
                    root_cause="MISSING_BANK",
                    is_exception=True,
                    description=f"Gateway settled ₹{target_net:.2f} but bank credit is missing.",
                )
            )

        elif scenario == ScenarioType.MISSING_ERP:
            # Gateway transaction exists and settles to bank, but no ERP order was recorded!
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            mdr, gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)
            net = calculate_expected_net_settlement(gross, self.mdr_rate, self.gst_rate)

            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=mdr,
                total_gst=gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=net,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description=desc,
                reference=settlement_id,
                credit_amount=net,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr,
            )
            # INTENTIONALLY NO ERP ORDER
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="0_TO_1",
                    expected_net_amount=net,
                    actual_bank_amount=net,
                    root_cause="MISSING_ERP",
                    is_exception=True,
                    description=f"Gateway captured ₹{gross:.2f} but no ERP order exists.",
                )
            )

        elif scenario == ScenarioType.FEE_ANOMALY:
            # Gateway charged non-contracted arbitrary fee (e.g. 5.5% instead of 2.0%)
            order_id = self._next_order_id()
            order_ref = generate_order_reference(self.rng, self.order_counter)
            txn_id = self._next_txn_id()
            settlement_id = self._next_settlement_id(order_date)
            bank_id = self._next_bank_id()
            utr = generate_utr(self.rng)

            # Contracted fee expectation
            expected_mdr, expected_gst, _ = calculate_total_fee(gross, self.mdr_rate, self.gst_rate)
            expected_net = calculate_expected_net_settlement(gross, self.mdr_rate, self.gst_rate)

            # Actual inflated fee
            anomalous_mdr = round_currency(gross * 0.055)
            anomalous_gst = round_currency(anomalous_mdr * 0.18)
            actual_net = round_currency(gross - anomalous_mdr - anomalous_gst)

            erp = ERPOrder(
                order_id=order_id,
                order_reference=order_ref,
                order_date=order_date,
                customer_id=customer_id,
                gross_amount=gross,
                currency=DEFAULT_CURRENCY,
                payment_method=pay_method,
                order_status="PAID",
            )
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference=order_ref,
                captured_amount=gross,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method=pay_method,
                gateway_fee=anomalous_mdr,
                gst_on_fee=anomalous_gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=settlement_id,
                settlement_date=order_date,
            )
            stl = GatewaySettlement(
                settlement_id=settlement_id,
                settlement_date=order_date,
                gross_amount=gross,
                total_mdr=anomalous_mdr,
                total_gst=anomalous_gst,
                refunds=0.0,
                chargebacks=0.0,
                net_settlement=actual_net,
                transaction_ids=[txn_id],
            )
            desc = generate_bank_description(self.rng, settlement_id, order_ref, utr)
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description=desc,
                reference=settlement_id,
                credit_amount=actual_net,
                debit_amount=0.0,
                balance=0.0,
                bank_utr=utr,
            )
            erp_orders.append(erp)
            gateway_txns.append(gtw)
            settlements.append(stl)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=settlement_id,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="1_TO_1",
                    expected_net_amount=expected_net,
                    actual_bank_amount=actual_net,
                    root_cause="FEE_ANOMALY",
                    is_exception=True,
                    description=f"MDR fee anomaly: charged ₹{anomalous_mdr:.2f} instead of contracted ₹{expected_mdr:.2f}.",
                )
            )

        elif scenario == ScenarioType.AMBIGUOUS:
            # Genuine insufficient evidence case: Two distinct ERP orders with identical amounts (₹1,500.00)
            # placed on the same day, with vague unmapped bank credit and missing references.
            order_id1 = self._next_order_id()
            order_id2 = self._next_order_id()
            ref1 = "WEB-AMBIG1"
            ref2 = "WEB-AMBIG2"
            txn_id = self._next_txn_id()
            bank_id = self._next_bank_id()

            ambig_amount = 1500.00
            net = calculate_expected_net_settlement(ambig_amount, self.mdr_rate, self.gst_rate)
            mdr, gst, _ = calculate_total_fee(ambig_amount, self.mdr_rate, self.gst_rate)

            erp1 = ERPOrder(
                order_id=order_id1,
                order_reference=ref1,
                order_date=order_date,
                customer_id="CUS-9901",
                gross_amount=ambig_amount,
                currency=DEFAULT_CURRENCY,
                payment_method="UPI",
                order_status="PAID",
            )
            erp2 = ERPOrder(
                order_id=order_id2,
                order_reference=ref2,
                order_date=order_date,
                customer_id="CUS-9902",
                gross_amount=ambig_amount,
                currency=DEFAULT_CURRENCY,
                payment_method="UPI",
                order_status="PAID",
            )
            # Gateway only recorded one capture with an obscured reference
            gtw = GatewayTransaction(
                gateway_transaction_id=txn_id,
                order_reference="REF-UNKNOWN",
                captured_amount=ambig_amount,
                transaction_date=order_date,
                payment_status="CAPTURED",
                payment_method="UPI",
                gateway_fee=mdr,
                gst_on_fee=gst,
                refund_amount=0.0,
                chargeback_amount=0.0,
                settlement_id=None,
                settlement_date=order_date,
            )
            bnk = BankTransaction(
                bank_transaction_id=bank_id,
                transaction_date=order_date,
                description="DIRECT UPI SETTLEMENT NO REF",
                reference="UPI-MISC-99",
                credit_amount=net,
                debit_amount=0.0,
                balance=0.0,
                bank_utr="UPI999999999999",
            )
            erp_orders.extend([erp1, erp2])
            gateway_txns.append(gtw)
            bank_txns.append(bnk)

            ground_truth.append(
                GroundTruthCase(
                    case_id=case_id,
                    scenario=scenario.value,
                    erp_order_ids=[order_id1, order_id2],
                    gateway_transaction_ids=[txn_id],
                    settlement_id=None,
                    bank_transaction_ids=[bank_id],
                    expected_relationship="UNKNOWN",
                    expected_net_amount=net,
                    actual_bank_amount=net,
                    root_cause="INSUFFICIENT_EVIDENCE",
                    is_exception=True,
                    description="Ambiguous matching candidates: multiple identical orders with obscured references.",
                )
            )


def save_dataset_to_disk(
    erp_orders: List[ERPOrder],
    gateway_txns: List[GatewayTransaction],
    settlements: List[GatewaySettlement],
    bank_txns: List[BankTransaction],
    ground_truth: List[GroundTruthCase],
    output_dir: Path,
) -> None:
    """Saves raw datasets to data/synthetic/ (JSON and CSV) and ground truth to data/ground_truth/ (JSON only)."""
    synthetic_dir = output_dir / "synthetic"
    ground_truth_dir = output_dir / "ground_truth"

    synthetic_dir.mkdir(parents=True, exist_ok=True)
    ground_truth_dir.mkdir(parents=True, exist_ok=True)

    # Helper to save JSON
    def save_json(filepath: Path, data: list):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([item.model_dump() for item in data], f, indent=2)

    # Helper to save CSV
    def save_csv(filepath: Path, data: list):
        if not data:
            return
        items = [item.model_dump() for item in data]
        # Flatten list fields if any
        for it in items:
            for k, v in it.items():
                if isinstance(v, list):
                    it[k] = ";".join(str(x) for x in v)
        fieldnames = list(items[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)

    # Save synthetic source datasets (JSON + CSV)
    save_json(synthetic_dir / "erp_orders.json", erp_orders)
    save_csv(synthetic_dir / "erp_orders.csv", erp_orders)

    save_json(synthetic_dir / "gateway_transactions.json", gateway_txns)
    save_csv(synthetic_dir / "gateway_transactions.csv", gateway_txns)

    save_json(synthetic_dir / "gateway_settlements.json", settlements)
    save_csv(synthetic_dir / "gateway_settlements.csv", settlements)

    save_json(synthetic_dir / "bank_transactions.json", bank_txns)
    save_csv(synthetic_dir / "bank_transactions.csv", bank_txns)

    # Save ground truth (JSON ONLY - isolated)
    save_json(ground_truth_dir / "ground_truth.json", ground_truth)
