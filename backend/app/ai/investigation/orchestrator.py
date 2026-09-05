import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from backend.app.ai.rag.retriever import retriever
from backend.app.ai.investigation.graph import app as investigation_graph, _apply_deterministic_investigation
from backend.app.ai.investigation.state import InvestigationState
from backend.app.ai.schemas import AIInvestigationResponse, EvidenceAnalysisResult, PolicyAnalysisResult, HistoricalAnalysisResult, RiskValidationResult

# Setup structured logger
logger = logging.getLogger("ReconPulse.AILogger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def run_investigation(structured_evidence: dict) -> AIInvestigationResponse:
    start_time = time.time()
    exc_id = structured_evidence.get("id", "UNKNOWN")
    exc_type = structured_evidence.get("type", "UNKNOWN")
    
    # 1. Retrieve Context
    retrieval_start = time.time()
    context = retriever.retrieve_context(structured_evidence)
    retrieval_latency = time.time() - retrieval_start
    
    # 2. Initialize State
    initial_state = {
        "structured_evidence": structured_evidence,
        "policies": context.get("policies", []),
        "historical_cases": context.get("historical_cases", []),
        "errors": []
    }
    
    # 3. Run Graph with timeout protection (max 25s)
    graph_start = time.time()
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(investigation_graph.invoke, initial_state)
            final_state = future.result(timeout=35.0)
    except FutureTimeoutError:
        logger.warning(f"Graph execution timed out after 35s for {exc_id}")
        final_state = initial_state
        final_state["errors"].append("AI service timed out after 35s")
        _apply_deterministic_investigation(final_state)
    except Exception as e:
        logger.error(f"Graph execution failed for {exc_id}: {e}")
        final_state = initial_state
        final_state["errors"].append(str(e))
        _apply_deterministic_investigation(final_state)
        
    graph_latency = time.time() - graph_start
    total_latency = time.time() - start_time
    
    is_fallback = len(final_state.get("errors", [])) > 0 or context.get("metrics", {}).get("retrieval_error", False)
    
    # Extract components
    ea = final_state.get("evidence_analysis") or EvidenceAnalysisResult(
        summary="Deterministic evidence analyzed.", flags=[]
    )
    pa = final_state.get("policy_analysis") or PolicyAnalysisResult(
        applicable_policies=["Standard Operating Procedure (SOP)"], 
        implications="Governed by organizational financial reconciliation guidelines."
    )
    ha = final_state.get("historical_analysis") or HistoricalAnalysisResult(
        similar_cases_found=0, comparison_summary="Evaluated against system precedent."
    )
    rv = final_state.get("risk_validation") or RiskValidationResult(
        approved=False, 
        risk_concerns=["Manual review required."], 
        final_decision="HUMAN_REVIEW", 
        recommended_action="Manual Review Required"
    )
    
    if is_fallback:
        final_decision = "INSUFFICIENT_EVIDENCE"
        prop_conf = 0.0
        prop_reas = "AI unavailable — deterministic evidence only."
        rv = RiskValidationResult(
            approved=False, 
            risk_concerns=["AI offline or unavailable — deterministic evidence only."], 
            final_decision="INSUFFICIENT_EVIDENCE", 
            recommended_action="Manual Review Required (AI unavailable — deterministic evidence only.)"
        )
    else:
        final_decision = rv.final_decision
        prop_conf = final_state.get("proposed_confidence", 0.85)
        prop_reas = final_state.get("proposed_reasoning", "Evidence analyzed under financial policies.")
    
    response = AIInvestigationResponse(
        exception_id=exc_id,
        decision=final_decision,
        confidence=prop_conf,
        reasoning=prop_reas,
        evidence_analysis=ea,
        policy_analysis=pa,
        historical_analysis=ha,
        risk_validation=rv,
        supporting_evidence=final_state.get("supporting_evidence", []),
        policy_basis=final_state.get("policy_basis", []),
        similar_cases=final_state.get("similar_cases", []),
        risk_flags=rv.risk_concerns,
        recommended_action=rv.recommended_action,
        human_review_required=True,
        source_types={
            "structured_evidence": "deterministic",
            "policies": "policy_rag",
            "historical_cases": "historical_rag",
            "decision": "ai_inference"
        },
        is_fallback=is_fallback
    )
    
    # 4. Observability Logging
    from backend.app.ai.resolver import LLMProvider
    _prov = LLMProvider()
    logger.info(
        f"AI_INVESTIGATION | ID:{exc_id} | Type:{exc_type} | Provider:{_prov.provider} | Model:{_prov.model} | "
        f"Policies:{context['metrics']['retrieved_policies']} | History:{context['metrics']['retrieved_historical_cases']} | "
        f"Decision:{final_decision} | Conf:{prop_conf:.2f} | RiskApproved:{rv.approved} | "
        f"HumanReview:True | Latency:{total_latency*1000:.1f}ms | Fallback:{is_fallback}"
    )
    
    return response
