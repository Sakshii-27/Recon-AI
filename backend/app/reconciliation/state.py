"""Reconciliation state tracking to prevent duplicate assignments."""

from typing import List, Set


class ReconciliationState:
    """Tracks which entities have been successfully matched to prevent double matching."""

    def __init__(self):
        self.used_erp_order_ids: Set[str] = set()
        self.used_gateway_transaction_ids: Set[str] = set()
        self.used_settlement_ids: Set[str] = set()
        self.used_bank_transaction_ids: Set[str] = set()

    def mark_erp_used(self, erp_ids: List[str]):
        for eid in erp_ids:
            self.used_erp_order_ids.add(eid)

    def mark_gateway_used(self, gateway_ids: List[str]):
        for gid in gateway_ids:
            self.used_gateway_transaction_ids.add(gid)

    def mark_settlement_used(self, settlement_id: str):
        if settlement_id:
            self.used_settlement_ids.add(settlement_id)

    def mark_bank_used(self, bank_ids: List[str]):
        for bid in bank_ids:
            self.used_bank_transaction_ids.add(bid)

    def is_erp_available(self, erp_id: str) -> bool:
        return erp_id not in self.used_erp_order_ids

    def is_gateway_available(self, gateway_id: str) -> bool:
        return gateway_id not in self.used_gateway_transaction_ids

    def is_bank_available(self, bank_id: str) -> bool:
        return bank_id not in self.used_bank_transaction_ids

    def is_settlement_available(self, settlement_id: str) -> bool:
        if not settlement_id:
            return True
        return settlement_id not in self.used_settlement_ids

    def are_gateway_ids_available(self, gateway_ids: List[str]) -> bool:
        return all(self.is_gateway_available(gid) for gid in gateway_ids)

    def mark_reconciled(
        self,
        erp_ids: List[str],
        gateway_ids: List[str],
        settlement_id: str,
        bank_ids: List[str]
    ):
        """Marks all entities from a successful reconciliation result as used."""
        self.mark_erp_used(erp_ids)
        self.mark_gateway_used(gateway_ids)
        self.mark_settlement_used(settlement_id)
        self.mark_bank_used(bank_ids)
