from typing import Dict, Any, List
from backend.app.ai.rag.vector_store import knowledge_base

class HybridRetriever:
    """Retrieves structured evidence from the system and semantic context from RAG."""
    
    def retrieve_context(self, exception_dict: dict) -> Dict[str, Any]:
        """
        Builds the complete evidence packet for the AI orchestrator.
        """
        structured_evidence = exception_dict
        exception_type = exception_dict.get("type", "UNKNOWN")
        diff = exception_dict.get("difference", 0)
        query = f"Exception type {exception_type} with variance {diff}. How to resolve this?"
        
        # 1. Retrieve Policies
        policy_docs = knowledge_base.search_policies(query, k=2)
        policies = [doc.page_content for doc in policy_docs]
            
        # 2. Retrieve Historical Cases
        case_docs = knowledge_base.search_historical_cases(exception_type, query, k=2)
        historical_cases = [doc.page_content for doc in case_docs]
            
        return {
            "structured_evidence": structured_evidence,
            "policies": policies,
            "historical_cases": historical_cases,
            "metrics": {
                "retrieved_policies": len(policies),
                "retrieved_historical_cases": len(historical_cases),
                "retrieval_error": False
            }
        }

retriever = HybridRetriever()
