import os
import json
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from backend.app.ai.resolver import embedding_provider

class KnowledgeBase:
    """Manages vector store and in-memory knowledge for synthetic policies and historical cases."""
    
    def __init__(self):
        self.persist_directory = os.path.join(os.getcwd(), "chroma_db")
        
        # Determine paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.policies_dir = os.path.join(base_dir, "knowledge", "policies")
        self.historical_path = os.path.join(base_dir, "knowledge", "historical_cases.json")
        
        self.policy_docs: List[Document] = []
        self.historical_docs: List[Document] = []
        self._load_raw_knowledge()
        
        self.embeddings = embedding_provider.get_embeddings()
        self.vector_store = None
        
        # Optional ChromaDB indexing with safety
        try:
            from langchain_chroma import Chroma
            self.vector_store = Chroma(
                collection_name="recon_knowledge",
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            if self.vector_store._collection.count() == 0:
                all_docs = self.policy_docs + self.historical_docs
                if all_docs:
                    self.vector_store.add_documents(all_docs)
        except BaseException as e:
            # Gracefully continue with in-memory knowledge store
            self.vector_store = None
            
    def _load_raw_knowledge(self):
        """Loads markdown policies and JSON historical cases directly into memory."""
        # Load policies
        if os.path.exists(self.policies_dir):
            for filename in sorted(os.listdir(self.policies_dir)):
                if filename.endswith(".md"):
                    filepath = os.path.join(self.policies_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        self.policy_docs.append(Document(
                            page_content=content,
                            metadata={"type": "policy", "source": filename}
                        ))
        
        # Load historical cases
        if os.path.exists(self.historical_path):
            with open(self.historical_path, "r", encoding="utf-8") as f:
                cases = json.load(f)
                for case in cases:
                    content = (
                        f"Exception Type: {case.get('exception_type')}\n"
                        f"Pattern: {case.get('transaction_pattern')}\n"
                        f"Resolution: {case.get('human_resolution')}\n"
                        f"Reasoning: {case.get('reasoning')}\n"
                        f"Evidence: {json.dumps(case.get('evidence', {}))}"
                    )
                    self.historical_docs.append(Document(
                        page_content=content,
                        metadata={
                            "type": "historical_case", 
                            "case_id": case.get("case_id"),
                            "exception_type": case.get("exception_type")
                        }
                    ))
            
    def get_query_embedding(self, query: str) -> Optional[List[float]]:
        if not self.embeddings:
            return None
        try:
            return self.embeddings.embed_query(query)
        except Exception:
            return None

    def search_policies(self, query: str, k: int = 2, query_vector: Optional[List[float]] = None) -> List[Document]:
        # 1. Try vector store first if available
        if self.vector_store:
            try:
                if query_vector is not None:
                    docs = self.vector_store.similarity_search_by_vector(query_vector, k=k, filter={"type": "policy"})
                else:
                    docs = self.vector_store.similarity_search(query, k=k, filter={"type": "policy"})
                if docs:
                    return docs
            except Exception:
                pass
                
        # 2. Rock-solid in-memory fallback
        q_lower = query.lower()
        scored_docs = []
        for doc in self.policy_docs:
            score = 0
            src = doc.metadata.get("source", "").lower()
            content = doc.page_content.lower()
            
            if "sop" in src or "reconciliation_sop" in src:
                score += 5  # Always prioritize SOP
            if "duplicate" in q_lower and "duplicate" in src:
                score += 10
            elif "batch" in q_lower and "settlement" in src:
                score += 10
            elif "missing_erp" in q_lower and "missing_erp" in src:
                score += 10
            elif "fee" in q_lower and "fee" in src:
                score += 10
            
            for word in q_lower.split():
                if len(word) > 3 and word in content:
                    score += 1
                    
            scored_docs.append((score, doc))
            
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:k]]
            
    def search_historical_cases(self, exception_type: str, query: str, k: int = 2, query_vector: Optional[List[float]] = None) -> List[Document]:
        # 1. Try vector store first if available
        if self.vector_store:
            filter_dict = {
                "$and": [
                    {"type": "historical_case"},
                    {"exception_type": exception_type}
                ]
            }
            try:
                if query_vector is not None:
                    docs = self.vector_store.similarity_search_by_vector(query_vector, k=k, filter=filter_dict)
                else:
                    docs = self.vector_store.similarity_search(query, k=k, filter=filter_dict)
                if docs:
                    return docs
            except Exception:
                pass
                
        # 2. Rock-solid in-memory fallback by exception_type
        matching = [
            doc for doc in self.historical_docs
            if doc.metadata.get("exception_type") == exception_type
        ]
        if not matching:
            matching = self.historical_docs
        return matching[:k]

knowledge_base = KnowledgeBase()
