"""
Phase 3 Automated Test Suite:
Validates policy document parsing, semantic chunking, metadata attachment,
vector store indexing, disk persistence, and domain query retrieval.
"""

from pathlib import Path
import pytest

from rag.ingestion import ingest_all_policies, parse_markdown_sections
from rag.vector_store import PolicyVectorStore
from rag.retriever import PolicyRetriever, search_policy, retrieve_fee_rule, retrieve_escalation_rule

BASE_DIR = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
TEMP_STORE_DIR = BASE_DIR / "rag" / "test_store"


def test_tc_p3_01_ingestion_and_vector_index_creation():
    """TC-P3-01: Ingestion creates chunks from all markdown files and stores them to disk."""
    chunks = ingest_all_policies(KNOWLEDGE_DIR)
    assert len(chunks) >= 15, f"Expected at least 15 chunks from policy docs, got {len(chunks)}"

    # Verify each chunk has non-empty fields
    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.source_file.endswith(".md")
        assert chunk.policy_type in ["fee", "settlement", "refund", "dispute", "escalation"]
        assert len(chunk.content.strip()) > 20

    # Build and persist store
    store = PolicyVectorStore(TEMP_STORE_DIR)
    store.fit_and_index(chunks)
    store.save_to_disk()

    assert (TEMP_STORE_DIR / "index_meta.json").exists()
    assert (TEMP_STORE_DIR / "doc_vectors.npy").exists()

    # Load from disk
    loaded_store = PolicyVectorStore.load_from_disk(TEMP_STORE_DIR)
    assert len(loaded_store.chunks) == len(chunks)
    assert len(loaded_store.vocabulary) > 50


def test_tc_p3_02_fee_policy_retrieval_accuracy():
    """TC-P3-02: Query for gateway fee cap returns fee_schedule.md chunk."""
    retriever = PolicyRetriever.initialize_or_load(KNOWLEDGE_DIR, TEMP_STORE_DIR)
    results = retriever.search(query="maximum allowable gateway fee cap 300", top_k=3)

    assert len(results) > 0, "No results returned for fee cap query"
    top_result = results[0]
    assert "fee_schedule.md" in [r.source_file for r in results]
    assert any("300" in r.content for r in results)


def test_tc_p3_03_escalation_policy_retrieval():
    """TC-P3-03: Query for human escalation threshold retrieves the ₹500 mandatory condition."""
    retriever = PolicyRetriever.initialize_or_load(KNOWLEDGE_DIR, TEMP_STORE_DIR)
    results = retriever.search(
        query="Mandatory Human Escalation Thresholds unexplained difference",
        policy_type="escalation",
        top_k=2
    )

    assert len(results) > 0
    assert results[0].source_file == "escalation_policy.md"
    assert "500" in results[0].content


def test_tc_p3_04_grounding_metadata_integrity():
    """TC-P3-04: Standalone tool helper returns structured dicts with complete citations."""
    results = search_policy("refund limit eligible amount", policy_type="refund", top_k=1)
    assert len(results) == 1
    res = results[0]

    assert "chunk_id" in res
    assert "source_file" in res and res["source_file"] == "refund_policy.md"
    assert "header" in res
    assert "content" in res
    assert "relevance_score" in res
    assert res["relevance_score"] > 0.0
