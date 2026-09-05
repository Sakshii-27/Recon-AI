"""Context routing and builder for the Finance Copilot."""

import re
from typing import Dict, Any, Optional

from backend.app.services.reconciliation_service import reconciliation_service
from backend.app.finance.cash_position import calculate_cash_position
from backend.app.finance.forecast import calculate_cash_forecast
from backend.app.ai.resolver import investigate_exception


class CopilotContextBuilder:
    def __init__(self):
        pass

    def build_context(self, question: str, exception_id: Optional[str] = None) -> Dict[str, Any]:
        """Routes the natural language question to the authoritative backend outputs."""
        latest_run_data = reconciliation_service.get_latest_run_data()
        if not latest_run_data:
            return {"error": "No reconciliation run available"}

        q_lower = question.lower()
        context = {
            "intent": "unknown",
            "data": {},
            "source": []
        }

        # Intent Routing
        
        # 1. Exception specific
        if exception_id or re.search(r'\b(why|explain|this)\b.*\b(exception|exc-\d+|transaction|unresolved)\b', q_lower):
            context["intent"] = "exception_investigation"
            context["source"] = ["Exception Workbench", "Phase 7 AI Resolver"]
            
            # Find the specific exception
            target_id = exception_id
            if not target_id:
                # Try to extract an EXC-XXX or REC-XXX or TXN-XXX from the string
                match = re.search(r'(REC-\d{5}|EXC-\d{4}|TXN-\d{5})', question, re.IGNORECASE)
                if match:
                    target_id = match.group(1).upper()
            
            if target_id:
                exceptions_res = reconciliation_service.get_exceptions()
                exc_detail = next((e for e in exceptions_res.exceptions if e.id == target_id or target_id in e.related_records.get("gateway", [])), None)
                
                if exc_detail:
                    context["data"]["exception_details"] = exc_detail.model_dump()
                    # Try to fetch AI investigation purely as context
                    ai_res = investigate_exception(exc_detail.model_dump())
                    context["data"]["ai_recommendation"] = ai_res.model_dump()
                else:
                    context["data"]["error"] = f"Exception {target_id} not found in the current run."
            else:
                context["data"]["error"] = "Please provide a specific exception ID to investigate."
                
        # 2. Cash Position
        elif re.search(r'\b(cash|balance|position|pending|risk|bank|revenue|captured|reconciled)\b', q_lower) and not re.search(r'\b(forecast|next|expect|tomorrow|future)\b', q_lower):
            context["intent"] = "cash_position"
            context["source"] = ["Cash Position"]
            pos = calculate_cash_position(latest_run_data)
            context["data"]["cash_metrics"] = pos.model_dump()
            
            # We also get some exception counts for context if they ask about biggest problems
            if "exception" in q_lower or "problem" in q_lower:
                exceptions_res = reconciliation_service.get_exceptions()
                context["data"]["exception_counts"] = {
                    "total": exceptions_res.total_exceptions,
                    "types": {t.type: t.count for t in exceptions_res.by_type}
                }
                
        # 3. Forecast
        elif re.search(r'\b(forecast|next|expect|tomorrow|future|upcoming|inflow)\b', q_lower):
            context["intent"] = "forecast"
            context["source"] = ["Deterministic Forecast"]
            fore = calculate_cash_forecast(latest_run_data)
            context["data"]["forecast_7_day"] = [d.model_dump() for d in fore.forecast_7_day]
            
        # 4. Reconciliation metrics
        elif re.search(r'\b(reconciled|rate|summary|metrics|how many)\b', q_lower):
            context["intent"] = "reconciliation_summary"
            context["source"] = ["Reconciliation Summary"]
            fin_summary = reconciliation_service.get_financial_summary()
            context["data"]["financial_summary"] = fin_summary.model_dump()
            
            # Add simple counts
            raw = latest_run_data.get("raw_results", [])
            resolved = sum(1 for r in raw if r.status.value == "RESOLVED")
            unresolved = len(raw) - resolved
            context["data"]["counts"] = {
                "total": len(raw),
                "resolved": resolved,
                "unresolved": unresolved
            }
            
        # 5. Policy Queries
        elif re.search(r'\b(policy|rules|sop|guideline)\b', q_lower):
            context["intent"] = "policy"
            context["source"] = ["Policy Documents"]
            from backend.app.ai.rag.vector_store import knowledge_base
            docs = knowledge_base.search_policies(question, k=3)
            context["data"]["policies"] = [d.page_content for d in docs]
            
        # 6. Historical Cases
        elif re.search(r'\b(history|historical|past cases|similar cases|before)\b', q_lower):
            context["intent"] = "historical"
            context["source"] = ["Historical Cases"]
            from backend.app.ai.rag.vector_store import knowledge_base
            docs = knowledge_base.search_historical_cases("UNKNOWN", question, k=3)
            context["data"]["historical_cases"] = [d.page_content for d in docs]

        else:
            # Fallback - provide a minimal summary of everything so the LLM can try to answer general queries
            context["intent"] = "general_summary"
            context["source"] = ["Reconciliation Summary", "Cash Position"]
            pos = calculate_cash_position(latest_run_data)
            fin_summary = reconciliation_service.get_financial_summary()
            context["data"]["cash_metrics"] = pos.model_dump()
            context["data"]["financial_summary"] = fin_summary.model_dump()

        return context
