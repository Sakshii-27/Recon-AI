"""Reconciliation Service Layer.

Manages running the reconciliation engine and caching the latest run in-memory.
"""
from typing import Any, Dict, List, Optional
import time

from backend.app.data_generation.generator import SyntheticDataGenerator
from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.reconciliation.types import ReconciliationStatus
from backend.app.api.schemas.reconciliation import (
    ReconciliationRunRequest,
    ReconciliationResponse,
    ReconciliationSummary,
)
from backend.app.api.schemas.exceptions import ExceptionListResponse, ExceptionDetail, ExceptionEvidence
from backend.app.api.schemas.finance import FinancialSummaryResponse


class ReconciliationService:
    """Service layer for reconciliation operations."""
    
    def __init__(self):
        # In-memory store for the latest reconciliation result.
        self._latest_run: Optional[Dict[str, Any]] = None

    def run_reconciliation(self, request: ReconciliationRunRequest) -> ReconciliationResponse:
        """Generates synthetic data and runs the reconciliation engine."""
        # 1. Generate Data
        generator = SyntheticDataGenerator(seed=request.seed)
        erp_orders, gateway_txns, settlements, bank_txns, _ = generator.generate_dataset(request.records)

        # 2. Run Engine
        engine = ReconciliationEngine()
        start_time = time.time()
        engine_output = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
        engine_time_ms = (time.time() - start_time) * 1000.0

        results = engine_output["reconciliation_results"]

        # 3. Categorize results
        matches = []
        exceptions = []
        decisions = []
        
        resolved_count = 0
        
        # Calculate financial coverage from the results
        total_expected_settlement = 0.0
        total_bank_settlement = 0.0
        total_unreconciled_value = 0.0

        for r in results:
            decision_dict = {
                "id": r.reconciliation_id,
                "status": r.status.value,
                "match_type": r.match_type.value,
                "root_cause": r.root_cause.value,
                "expected_amount": r.expected_amount,
                "actual_amount": r.actual_amount,
                "difference": r.difference,
                "confidence": r.confidence,
                "gateway_ids": r.gateway_transaction_ids,
                "bank_ids": r.bank_transaction_ids
            }
            decisions.append(decision_dict)
            
            if r.status == ReconciliationStatus.RESOLVED or r.root_cause.value == "EXACT_MATCH":
                matches.append(decision_dict)
                if r.status == ReconciliationStatus.RESOLVED:
                    resolved_count += 1
            else:
                exceptions.append(decision_dict)

        # Calculate high-level summary
        total_results = len(results)
        
        # Financial accumulators (Fixed for dashboard)
        from backend.app.domain.finance_rules import calculate_expected_net_settlement
        total_expected_settlement = sum(
            calculate_expected_net_settlement(g.captured_amount, refund_amount=g.refund_amount, chargeback_amount=g.chargeback_amount)
            for g in gateway_txns
        )
        total_bank_settlement = sum((b.credit_amount - b.debit_amount) for b in bank_txns)
        total_reconciled_value = sum(abs(r.expected_amount) for r in results if r.expected_amount and (r.status == ReconciliationStatus.RESOLVED or r.root_cause.value == "EXACT_MATCH"))
        total_unreconciled_value = max(0.0, total_expected_settlement - total_reconciled_value)
        
        # Match rate: Percentage of reconciliation transactions that successfully matched
        match_rate = (len(matches) / total_results * 100) if total_results else 0.0
        
        # Autonomous rate: Percentage of total reconciliation cases handled without human review
        # Note: The dashboard label says "Safe Autonomous", but without ground truth it calculates "Autonomous Rate".
        safe_autonomous_rate = (resolved_count / total_results * 100) if total_results else 0.0
        value_reconciled_pct = (total_reconciled_value / total_expected_settlement * 100) if total_expected_settlement else 0.0
        
        # Additional raw metrics for financial summary
        # Assuming sum of all gateway captured amount is gross sales
        gross_sales = sum([g.captured_amount for g in gateway_txns])
        gateway_fees = sum([g.gateway_fee for g in gateway_txns])
        gateway_gst = sum([g.gst_on_fee for g in gateway_txns])

        summary = ReconciliationSummary(
            total_records=request.records,
            matched=len(matches),
            exceptions=len(exceptions),
            match_rate=match_rate,
            value_reconciled=value_reconciled_pct,
            safe_autonomous_rate=safe_autonomous_rate
        )

        financial_summary = {
            "gross_sales": gross_sales,
            "gateway_captured": gross_sales,
            "gateway_fees": gateway_fees,
            "gateway_gst": gateway_gst,
            "expected_settlement": total_expected_settlement,
            "bank_settlement": total_bank_settlement,
            "unreconciled_value": total_unreconciled_value
        }
        
        response = ReconciliationResponse(
            summary=summary,
            matches=matches,
            exceptions=exceptions,
            decisions=decisions,
            financial_summary=financial_summary,
            metadata={
                "seed": request.seed,
                "engine_time_ms": engine_time_ms,
                "erp_count": len(erp_orders),
                "gateway_count": len(gateway_txns),
                "settlement_count": len(settlements),
                "bank_count": len(bank_txns)
            }
        )

        # 4. Cache latest run in memory
        self._latest_run = {
            "response": response,
            "raw_results": results,
            "erp_orders": erp_orders,
            "gateway_txns": gateway_txns,
            "settlements": settlements,
            "bank_txns": bank_txns
        }

        return response

    def get_latest_run_data(self) -> Optional[Dict[str, Any]]:
        """Returns the complete latest run cache including raw lists."""
        return self._latest_run

    def get_summary(self) -> Optional[ReconciliationSummary]:
        """Returns the summary of the latest run."""
        if not self._latest_run:
            return None
        return self._latest_run["response"].summary

    def get_exceptions(self, type_filter: Optional[str] = None) -> ExceptionListResponse:
        """Retrieves exceptions from the latest run."""
        if not self._latest_run:
            return ExceptionListResponse(total_exceptions=0, exceptions=[])
        
        exceptions_list = []
        raw_results = self._latest_run["raw_results"]
        
        for r in raw_results:
            if r.status != ReconciliationStatus.RESOLVED and r.root_cause.value != "EXACT_MATCH":
                if type_filter and r.root_cause.value != type_filter:
                    continue
                
                evidence = ExceptionEvidence(
                    matched_by=r.evidence.matched_by if r.evidence else [],
                    erp_evidence=r.evidence.erp_evidence if r.evidence else [],
                    gateway_evidence=r.evidence.gateway_evidence if r.evidence else [],
                    bank_evidence=r.evidence.bank_evidence if r.evidence else [],
                    financial_evidence=r.evidence.financial_evidence.model_dump() if r.evidence and r.evidence.financial_evidence else None
                )
                
                exc_detail = ExceptionDetail(
                    id=r.reconciliation_id,
                    type=r.root_cause.value,
                    status=r.status.value,
                    amount=abs(r.expected_amount) if r.expected_amount else 0.0,
                    difference=r.difference,
                    confidence=r.confidence,
                    evidence=evidence,
                    related_records={
                        "gateway_ids": r.gateway_transaction_ids,
                        "bank_ids": r.bank_transaction_ids,
                        "erp_ids": getattr(r, "erp_order_ids", [])  # Handle missing if any
                    }
                )
                exceptions_list.append(exc_detail)
                
        return ExceptionListResponse(
            total_exceptions=len(exceptions_list),
            exceptions=exceptions_list
        )

    def get_exception(self, exception_id: str) -> Optional[ExceptionDetail]:
        """Retrieves a single exception by ID."""
        if not self._latest_run:
            return None
            
        raw_results = self._latest_run["raw_results"]
        for r in raw_results:
            if r.reconciliation_id == exception_id and (r.status != ReconciliationStatus.RESOLVED and r.root_cause.value != "EXACT_MATCH"):
                evidence = ExceptionEvidence(
                    matched_by=r.evidence.matched_by if r.evidence else [],
                    erp_evidence=r.evidence.erp_evidence if r.evidence else [],
                    gateway_evidence=r.evidence.gateway_evidence if r.evidence else [],
                    bank_evidence=r.evidence.bank_evidence if r.evidence else [],
                    financial_evidence=r.evidence.financial_evidence.model_dump() if r.evidence and r.evidence.financial_evidence else None
                )
                return ExceptionDetail(
                    id=r.reconciliation_id,
                    type=r.root_cause.value,
                    status=r.status.value,
                    amount=abs(r.expected_amount) if r.expected_amount else 0.0,
                    difference=r.difference,
                    confidence=r.confidence,
                    evidence=evidence,
                    related_records={
                        "gateway_ids": r.gateway_transaction_ids,
                        "bank_ids": r.bank_transaction_ids,
                    }
                )
        return None

    def get_financial_summary(self) -> FinancialSummaryResponse:
        """Retrieves the financial summary of the latest run."""
        if not self._latest_run:
            return FinancialSummaryResponse()
            
        summary_dict = self._latest_run["response"].financial_summary
        return FinancialSummaryResponse(**summary_dict)


# Global singleton instance for in-memory state
reconciliation_service = ReconciliationService()
