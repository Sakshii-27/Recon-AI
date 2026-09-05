import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
load_dotenv()

from backend.app.ai.schemas import AIResolutionResponse
from backend.app.ai.prompts import SYSTEM_INSTRUCTIONS, build_investigation_prompt

class LLMProvider:
    def __init__(self):
        self.api_key = os.environ.get("AI_API_KEY")
        self.provider = os.environ.get("AI_PROVIDER", "mock")
        self.model = os.environ.get("AI_MODEL", "gemini-2.5-flash")

    def is_mock(self) -> bool:
        return self.provider == "mock"

    def generate_structured_response(self, exception_data: dict) -> AIResolutionResponse:
        exc_id = exception_data.get("id", "UNKNOWN")

        # Explicit mock mode
        if self.is_mock():
            return self._mock_resolve(exception_data)
        
        # Missing API Key fallback: DO NOT fabricate mock output
        if not self.api_key:
            return AIResolutionResponse(
                exception_id=exc_id,
                decision="UNRESOLVED",
                confidence=0.0,
                reasoning="AI unavailable — deterministic evidence only.",
                supporting_evidence=[],
                recommended_action="Manual investigation required (AI unavailable).",
                human_review_required=True
            )
        
        if self.provider == "gemini":
            try:
                from google import genai
                from pydantic import BaseModel
                
                class GeminiResponse(BaseModel):
                    exception_id: str
                    decision: str
                    confidence: float
                    reasoning: str
                    supporting_evidence: list[str]
                    recommended_action: str
                    human_review_required: bool
                    
                client = genai.Client(api_key=self.api_key)
                prompt = build_investigation_prompt(exception_data)
                
                response = client.models.generate_content(
                    model=self.model,
                    contents=[
                        {"role": "user", "parts": [{"text": SYSTEM_INSTRUCTIONS}]},
                        {"role": "user", "parts": [{"text": prompt}]}
                    ],
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": GeminiResponse,
                        "temperature": 0.1,
                    },
                )
                
                result = json.loads(response.text)
                return AIResolutionResponse(**result)
            except Exception as e:
                # Catch error without logging secrets; fallback safely without mock fabrication
                print(f"AI Provider Error: {type(e).__name__}")
                return AIResolutionResponse(
                    exception_id=exc_id,
                    decision="UNRESOLVED",
                    confidence=0.0,
                    reasoning="AI unavailable — deterministic evidence only.",
                    supporting_evidence=[],
                    recommended_action="Manual investigation required (AI unavailable).",
                    human_review_required=True
                )
        
        # Unsupported provider fallback
        return AIResolutionResponse(
            exception_id=exc_id,
            decision="UNRESOLVED",
            confidence=0.0,
            reasoning="AI unavailable — deterministic evidence only.",
            supporting_evidence=[],
            recommended_action="Manual investigation required (AI unavailable).",
            human_review_required=True
        )

    def _mock_resolve(self, exception_data: dict) -> AIResolutionResponse:
        """Deterministic mock mode for benchmarking and development (explicitly labeled)."""
        exc_id = exception_data.get("id", "UNKNOWN")
        exc_type = exception_data.get("type", "UNKNOWN")

        decision = "UNRESOLVED"
        reasoning = "Insufficient evidence to resolve automatically."
        evidence_list = []

        if exc_type == "DUPLICATE":
            decision = "UNRESOLVED"
            reasoning = "Ambiguous duplicate transaction footprint. Risk validator downgraded decision to safe abstention."
            evidence_list = ["Gateway timestamps", "Potential retry footprint"]
        elif exc_type == "BATCH_SETTLEMENT":
            decision = "LIKELY_BATCH_SETTLEMENT"
            reasoning = "Gateway transactions sum exactly to the batch settlement amount found in the bank transaction."
            evidence_list = ["Gateway sum equals bank settlement", "Matching dates"]
        elif exc_type == "MISSING_ERP":
            decision = "LIKELY_MISSING_ERP"
            reasoning = "Gateway and Bank evidence cleanly align, strongly suggesting the ERP order was dropped or failed to post."
            evidence_list = ["Gateway capture successful", "Bank settlement complete", "No ERP record"]

        return AIResolutionResponse(
            exception_id=exc_id,
            decision=decision,
            confidence=0.85 if decision != "UNRESOLVED" else 0.0,
            reasoning=f"[MOCK/DEMO] {reasoning}",
            supporting_evidence=evidence_list,
            recommended_action="[MOCK/DEMO] Review and verify evidence.",
            human_review_required=True
        )

ai_provider = LLMProvider()

def investigate_exception(exception_dict: dict) -> AIResolutionResponse:
    # Restrict to eligible types
    eligible_types = {"DUPLICATE", "BATCH_SETTLEMENT", "MISSING_ERP"}
    if exception_dict.get("type") not in eligible_types:
        return AIResolutionResponse(
            exception_id=exception_dict.get("id", ""),
            decision="UNRESOLVED",
            confidence=1.0,
            reasoning="Exception type is not eligible for AI investigation.",
            supporting_evidence=[],
            recommended_action="Manual investigation required.",
            human_review_required=True
        )
    
    # Strip unnecessary keys to bounded payload
    bounded_payload = {
        "id": exception_dict.get("id"),
        "type": exception_dict.get("type"),
        "amount": exception_dict.get("amount"),
        "difference": exception_dict.get("difference"),
        "evidence": exception_dict.get("evidence", {})
    }
    
    return ai_provider.generate_structured_response(bounded_payload)

class EmbeddingProvider:
    def __init__(self):
        self.api_key = os.environ.get("AI_API_KEY")
        self.provider = os.environ.get("AI_PROVIDER", "mock")
        self.model = os.environ.get("AI_EMBEDDING_MODEL", "models/gemini-embedding-001")

    def get_embeddings(self):
        """Returns a LangChain embeddings object based on configuration."""
        if self.provider == "mock" or not self.api_key:
            from langchain_core.embeddings import FakeEmbeddings
            return FakeEmbeddings(size=768)
            
        if self.provider == "gemini":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(model=self.model, google_api_key=self.api_key)
            
        # Fallback
        from langchain_core.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=768)

embedding_provider = EmbeddingProvider()

def investigate_exception_v2(exception_dict: dict):
    """
    V2 AI investigation using LangGraph, RAG, and a multi-stage reasoning chain.
    """
    # Restrict to eligible types
    eligible_types = {"DUPLICATE", "BATCH_SETTLEMENT", "MISSING_ERP"}
    if exception_dict.get("type") not in eligible_types:
        from backend.app.ai.schemas import AIInvestigationResponse, EvidenceAnalysisResult, PolicyAnalysisResult, HistoricalAnalysisResult, RiskValidationResult
        return AIInvestigationResponse(
            exception_id=exception_dict.get("id", ""),
            decision="UNRESOLVED",
            confidence=1.0,
            reasoning="Exception type is not eligible for AI investigation.",
            evidence_analysis=EvidenceAnalysisResult(summary="N/A", flags=[]),
            policy_analysis=PolicyAnalysisResult(applicable_policies=[], implications="N/A"),
            historical_analysis=HistoricalAnalysisResult(similar_cases_found=0, comparison_summary="N/A"),
            risk_validation=RiskValidationResult(approved=False, risk_concerns=["Not eligible for AI resolution"]),
            supporting_evidence=[],
            policy_basis=[],
            similar_cases=[],
            risk_flags=["Ineligible Type"],
            recommended_action="Manual investigation required.",
            human_review_required=True,
            source_types={},
            is_fallback=True
        )
    
    # Strip unnecessary keys
    bounded_payload = {
        "id": exception_dict.get("id"),
        "type": exception_dict.get("type"),
        "amount": exception_dict.get("amount"),
        "difference": exception_dict.get("difference"),
        "evidence": exception_dict.get("evidence", {})
    }
    
    # Delegate to the orchestrator to prevent circular imports and keep resolver clean
    from backend.app.ai.investigation.orchestrator import run_investigation
    return run_investigation(bounded_payload)
