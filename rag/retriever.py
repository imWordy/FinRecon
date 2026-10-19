"""
Retriever and query interface for FinRecon Policy RAG.
Provides high-level retrieval functions for agents and workflows.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from rag.ingestion import ingest_all_policies
from rag.vector_store import PolicyVectorStore, SearchResult
from config import KNOWLEDGE_DIR, VECTOR_STORE_DIR


class PolicyRetriever:
    """Singleton/Cached retriever for financial policies."""

    def __init__(self, vector_store: PolicyVectorStore):
        self.store = vector_store

    @classmethod
    def initialize_or_load(
        cls,
        knowledge_dir: Path = KNOWLEDGE_DIR,
        store_dir: Path = VECTOR_STORE_DIR,
        force_reindex: bool = False
    ) -> "PolicyRetriever":
        """Loads index from disk or indexes policies if missing."""
        if not force_reindex and (store_dir / "index_meta.json").exists():
            store = PolicyVectorStore.load_from_disk(store_dir)
        else:
            chunks = ingest_all_policies(knowledge_dir)
            store = PolicyVectorStore(store_dir)
            store.fit_and_index(chunks)
            store.save_to_disk()
        return cls(store)

    def search(
        self,
        query: str,
        policy_type: Optional[str] = None,
        top_k: int = 3
    ) -> List[SearchResult]:
        """Performs semantic search with optional policy domain filter."""
        return self.store.search(query=query, policy_type=policy_type, top_k=top_k)


# Standalone tool functions for agents
_cached_retriever: Optional[PolicyRetriever] = None

def get_policy_retriever() -> PolicyRetriever:
    global _cached_retriever
    if _cached_retriever is None:
        _cached_retriever = PolicyRetriever.initialize_or_load()
    return _cached_retriever


def search_policy(query: str, policy_type: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search tool callable by Agents and LangGraph workflows.
    Returns list of dicts with citations and content.
    """
    retriever = get_policy_retriever()
    results = retriever.search(query=query, policy_type=policy_type, top_k=top_k)
    return [
        {
            "chunk_id": r.chunk_id,
            "source_file": r.source_file,
            "policy_type": r.policy_type,
            "header": r.header,
            "content": r.content,
            "relevance_score": round(r.score, 4)
        }
        for r in results
    ]


def retrieve_fee_rule(channel: str = "CREDIT_CARD") -> Dict[str, Any]:
    """Retrieves specific fee rules from fee_schedule policy."""
    results = search_policy(f"processing fee rate schedule {channel}", policy_type="fee", top_k=1)
    return results[0] if results else {}


def retrieve_escalation_rule(issue: str = "unexplained difference") -> Dict[str, Any]:
    """Retrieves escalation policy rule for human-in-the-loop triggers."""
    results = search_policy(f"mandatory human review escalation threshold {issue}", policy_type="escalation", top_k=1)
    return results[0] if results else {}
