"""
RAG package initialization for FinRecon.
Exposes ingestion, vector store, and search policy tools.
"""

from rag.ingestion import PolicyChunk, parse_markdown_sections, ingest_all_policies
from rag.vector_store import PolicyVectorStore, SearchResult
from rag.retriever import (
    PolicyRetriever,
    get_policy_retriever,
    search_policy,
    retrieve_fee_rule,
    retrieve_escalation_rule
)

__all__ = [
    "PolicyChunk",
    "parse_markdown_sections",
    "ingest_all_policies",
    "PolicyVectorStore",
    "SearchResult",
    "PolicyRetriever",
    "get_policy_retriever",
    "search_policy",
    "retrieve_fee_rule",
    "retrieve_escalation_rule"
]
