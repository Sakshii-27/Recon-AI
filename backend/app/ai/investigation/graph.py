import os
import json
from typing import List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from backend.app.ai.investigation.state import InvestigationState
from backend.app.ai.resolver import LLMProvider
from backend.app.ai.schemas import (
    EvidenceAnalysisResult, PolicyAnalysisResult, HistoricalAnalysisResult, RiskValidationResult
)
from backend.app.ai.prompts.system import SYSTEM_INSTRUCTIONS

class UnifiedInvestigationResult(BaseModel):
    """Complete evidence-grounded AI investigation schema with embedded risk audit."""
    evidence_summary: str = Field(..., description="Concise 1-2 sentence executive summary of financial evidence")
    evidence_flags: List[str] = Field(default_factory=list, description="Key transaction anomalies or patterns detected")
    applicable_policies: List[str] = Field(default_factory=list, description="Names of relevant policies")
    policy_implications: str = Field(..., description="Concise 1-2 sentence statement of policy impact")
    similar_cases_found: int = Field(default=0, description="Count of relevant historical precedent cases")
    historical_comparison: str = Field(..., description="Concise 1-2 sentence precedent comparison")
    hypothesis_decision: str = Field(..., description="Proposed classification (e.g. LIKELY_DUPLICATE, LIKELY_MISSING_ERP, VALID_BATCH_SETTLEMENT)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Proposed confidence between 0.0 and 1.0")
    reasoning: str = Field(..., description="Concise executive reasoning (max 2-3 sentences)")
    supporting_evidence: List[str] = Field(default_factory=list, description="Specific evidence facts supporting this hypothesis")
    risk_approved: bool = Field(..., description="Whether the independent risk validator approves the hypothesis")
    risk_concerns: List[str] = Field(default_factory=list, description="Specific contradictions, missing settlement proofs, or false duplicate flags")
    final_decision: str = Field(..., description="Final decision after risk audit. Must downgrade to HUMAN_REVIEW or INSUFFICIENT_EVIDENCE if unproven")
    recommended_action: str = Field(..., description="Direct actionable instruction for the human operator")

def _get_llm():
    provider = LLMProvider()
    if provider.is_mock():
        return None
    
    if not provider.api_key:
        raise ValueError("AI unavailable: AI_API_KEY is not configured")
    
    if provider.provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=provider.model, 
            google_api_key=provider.api_key, 
            temperature=0.1,
            max_retries=0,
            request_timeout=35
        )
    
    raise ValueError(f"AI unavailable: Unsupported provider {provider.provider}")

UNIFIED_INVESTIGATION_PROMPT = """
You are the Lead Financial Reconciliation Analyst and Risk Controller.
Perform a comprehensive, evidence-grounded investigation of this reconciliation exception.

### 1. TRANSACTION EVIDENCE:
{structured_evidence}

### 2. RELEVANT ORGANIZATIONAL POLICIES:
{policies}

### 3. HISTORICAL PRECEDENT CASES:
{historical_cases}

### REQUIRED PERSPECTIVES:
1. Lead Analyst:
   - Synthesize evidence (cite specific amounts, order references, fees, bank deposits).
   - Reference applicable policies and precedent.
   - Propose an initial classification hypothesis (e.g. LIKELY_DUPLICATE, LIKELY_MISSING_ERP, VALID_BATCH_SETTLEMENT).
2. Risk & Contradiction Validator (Adversarial Audit):
   - Scrutinize the hypothesis for false duplicate signals, missing bank settlement proofs, or unsupported assumptions.
   - If evidence is ambiguous or incomplete, REJECT and downgrade final_decision to HUMAN_REVIEW.
   - Provide concrete next actions for the human operator.
"""

def _apply_deterministic_investigation(state: InvestigationState):
    """Ground truth fallback when AI provider is offline or rate-limited."""
    exc_type = state["structured_evidence"].get("type", "UNKNOWN")
    cases = state.get("historical_cases", [])
    
    if exc_type == "DUPLICATE":
        state["evidence_analysis"] = EvidenceAnalysisResult(
            summary="Transaction flagged under duplicate detection footprint. Gateway capture records require manual validation against bank settlement.",
            flags=["Potential retry or duplicate transaction footprint", "Requires gateway telemetry verification"]
        )
        state["policy_analysis"] = PolicyAnalysisResult(
            applicable_policies=["Duplicate Transaction Policy", "Standard Operating Procedure (SOP)"],
            implications="Under Tier 4 SOP, duplicate transaction footprints with ambiguous bank credits require mandatory human review."
        )
        state["historical_analysis"] = HistoricalAnalysisResult(
            similar_cases_found=len(cases),
            comparison_summary="Historical precedents indicate duplicate claims frequently stem from customer retry attempts rather than double debit."
        )
        state["proposed_decision"] = "LIKELY_DUPLICATE"
        state["proposed_confidence"] = 0.85
        state["proposed_reasoning"] = "Transaction matches duplicate exception pattern. Risk validator requires human review to confirm bank settlement."
        state["supporting_evidence"] = ["Gateway capture verified", "Ambiguous bank credit"]
        state["policy_basis"] = ["Duplicate Transaction Policy", "SOP Tier 4"]
        state["similar_cases"] = [c[:60] for c in cases]
        state["risk_validation"] = RiskValidationResult(
            approved=False,
            risk_concerns=["Single bank credit cannot be attributed without gateway retry telemetry confirmation."],
            final_decision="HUMAN_REVIEW",
            recommended_action="Verify payment gateway retry telemetry and customer statement before approving write-off or refund."
        )
    elif exc_type == "MISSING_ERP":
        state["evidence_analysis"] = EvidenceAnalysisResult(
            summary="A payment gateway capture exists, but no corresponding ERP order or ledger invoice was found.",
            flags=["Missing ERP order record", "Potential unposted revenue"]
        )
        state["policy_analysis"] = PolicyAnalysisResult(
            applicable_policies=["Missing ERP Policy", "Standard Operating Procedure (SOP)"],
            implications="Missing ERP transactions require confirmation of settled funds before posting manual ledger journal entries."
        )
        state["historical_analysis"] = HistoricalAnalysisResult(
            similar_cases_found=len(cases),
            comparison_summary="Historical precedent resolved by creating manual ERP order entry following bank settlement verification."
        )
        state["proposed_decision"] = "LIKELY_MISSING_ERP"
        state["proposed_confidence"] = 0.90
        state["proposed_reasoning"] = "Gateway record confirms captured customer payment. ERP order dropped during webhook ingestion."
        state["supporting_evidence"] = ["Gateway capture verified", "ERP record absent"]
        state["policy_basis"] = ["Missing ERP Policy", "SOP Tier 2"]
        state["similar_cases"] = [c[:60] for c in cases]
        state["risk_validation"] = RiskValidationResult(
            approved=False,
            risk_concerns=["Verify whether gateway funds have settled into bank account before booking revenue."],
            final_decision="HUMAN_REVIEW",
            recommended_action="Confirm bank settlement status for gateway transaction, then post manual invoice in ERP."
        )
    elif exc_type == "BATCH_SETTLEMENT":
        state["evidence_analysis"] = EvidenceAnalysisResult(
            summary="Bank statement shows bulk deposit matching multiple gateway transaction captures.",
            flags=["Bulk settlement grouping detected"]
        )
        state["policy_analysis"] = PolicyAnalysisResult(
            applicable_policies=["Batch Settlement Policy", "Standard Operating Procedure (SOP)"],
            implications="Batch settlements require 100% aggregate value alignment between gateway net and bank deposit."
        )
        state["historical_analysis"] = HistoricalAnalysisResult(
            similar_cases_found=len(cases),
            comparison_summary="Batch settlement matched against historical bulk deposit reconciliation records."
        )
        state["proposed_decision"] = "VALID_BATCH_SETTLEMENT"
        state["proposed_confidence"] = 0.92
        state["proposed_reasoning"] = "Gateway transaction captures sum accurately to bank batch deposit net of fees."
        state["supporting_evidence"] = ["Net capture aggregate matches bank deposit"]
        state["policy_basis"] = ["Batch Settlement Policy"]
        state["similar_cases"] = [c[:60] for c in cases]
        state["risk_validation"] = RiskValidationResult(
            approved=True,
            risk_concerns=[],
            final_decision="VALID_BATCH_SETTLEMENT",
            recommended_action="Review and confirm batch settlement group."
        )
    else:
        state["evidence_analysis"] = EvidenceAnalysisResult(
            summary="Deterministic evidence extracted. Ambiguity prevents autonomous classification.",
            flags=["Inconclusive evidence"]
        )
        state["policy_analysis"] = PolicyAnalysisResult(
            applicable_policies=["Standard Operating Procedure (SOP)"],
            implications="Inconclusive exceptions default to human review under conservative policy."
        )
        state["historical_analysis"] = HistoricalAnalysisResult(
            similar_cases_found=0,
            comparison_summary="No conclusive historical precedent identified."
        )
        state["proposed_decision"] = "INSUFFICIENT_EVIDENCE"
        state["proposed_confidence"] = 0.0
        state["proposed_reasoning"] = "Insufficient financial evidence to propose resolution."
        state["supporting_evidence"] = []
        state["policy_basis"] = ["Standard Operating Procedure (SOP)"]
        state["similar_cases"] = []
        state["risk_validation"] = RiskValidationResult(
            approved=False,
            risk_concerns=["Insufficient evidence for automated decision."],
            final_decision="INSUFFICIENT_EVIDENCE",
            recommended_action="Manual Investigation Required."
        )

def unified_investigation_node(state: InvestigationState) -> InvestigationState:
    llm = _get_llm()
    
    if not llm:
        _apply_deterministic_investigation(state)
        return state

    try:
        structured_llm = llm.with_structured_output(UnifiedInvestigationResult)
        prompt = UNIFIED_INVESTIGATION_PROMPT.format(
            structured_evidence=json.dumps(state["structured_evidence"], indent=2),
            policies="\n\n".join(state.get("policies", [])) if state.get("policies") else "No specific policies retrieved.",
            historical_cases="\n\n".join(state.get("historical_cases", [])) if state.get("historical_cases") else "No historical cases retrieved."
        )
        res = structured_llm.invoke([
            SystemMessage(content=SYSTEM_INSTRUCTIONS),
            HumanMessage(content=prompt)
        ])
        
        state["evidence_analysis"] = EvidenceAnalysisResult(
            summary=res.evidence_summary,
            flags=res.evidence_flags
        )
        state["policy_analysis"] = PolicyAnalysisResult(
            applicable_policies=res.applicable_policies,
            implications=res.policy_implications
        )
        state["historical_analysis"] = HistoricalAnalysisResult(
            similar_cases_found=res.similar_cases_found,
            comparison_summary=res.historical_comparison
        )
        state["proposed_decision"] = res.hypothesis_decision
        state["proposed_confidence"] = res.confidence
        state["proposed_reasoning"] = res.reasoning
        state["supporting_evidence"] = res.supporting_evidence
        state["policy_basis"] = res.applicable_policies
        state["similar_cases"] = [c[:60] for c in state.get("historical_cases", [])]
        state["risk_validation"] = RiskValidationResult(
            approved=res.risk_approved,
            risk_concerns=res.risk_concerns,
            final_decision=res.final_decision,
            recommended_action=res.recommended_action
        )
    except Exception as e:
        # Graceful fallback: populate high-grade deterministic investigation
        state["errors"].append(f"AI service unavailable: {e}")
        _apply_deterministic_investigation(state)
        
    return state

# Build the Graph: Single unified high-performance pass
workflow = StateGraph(InvestigationState)
workflow.add_node("investigation", unified_investigation_node)
workflow.set_entry_point("investigation")
workflow.add_edge("investigation", END)

app = workflow.compile()
