import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.vector_store import (
    search_policy_clauses,
    delete_document_chunks_from_vector_store,
)
# Support both naming variations if user wrote add_chunks_to_vector_store or add_chunk_to_vector_stores
try:
    from app.services.vector_store import add_chunks_to_vector_store
except ImportError:
    from app.services.vector_store import add_chunk_to_vector_stores as add_chunks_to_vector_store


def test_vector_store_indexing_and_search():
    """
    Verifies that:
    1. Chunks are embedded and indexed into ChromaDB.
    2. Semantic search returns relevant clauses with similarity scores.
    3. Jurisdictional scoping prevents an India query from seeing UK policies.
    """
    doc_id = 9999
    chunks = [
        {
            "chunk_index": 0,
            "clause_id": "Clause 4: Annual Leave Carryover",
            "content": "India employees may carry forward up to 8 unused annual leave days into the next calendar year.",
        },
        {
            "chunk_index": 1,
            "clause_id": "Clause 5: Compassionate Leave",
            "content": "India employees are entitled to 3 days of paid compassionate leave for immediate family.",
        }
    ]

    # 1. Index test chunks
    add_chunks_to_vector_store(
        document_id=doc_id,
        title="India Test Leave Policy 2025",
        entity="India",
        version="v2025.1",
        effective_date="2025-01-01",
        chunks=chunks,
    )

    # 2. Semantic query: "Can I transfer unused vacation to next year?"
    # Notice: The word 'vacation' is NOT in the text! Semantic search must map 'vacation' -> 'annual leave'.
    results = search_policy_clauses(
        query="Can I transfer unused vacation to next year?",
        entity="India",
        top_k=2
    )

    assert len(results) > 0
    top_match = results[0]
    assert "Clause 4" in top_match["clause_id"]
    assert top_match["entity"] == "India"
    assert top_match["similarity_score"] > 0.4
    assert "8 unused annual leave days" in top_match["content"]

    # 3. Jurisdictional Isolation Test:
    # A UK employee searching for vacation carryover should NOT match this India policy
    uk_results = search_policy_clauses(
        query="Can I transfer unused vacation to next year?",
        entity="UK",
        top_k=2
    )
    for r in uk_results:
        assert r["entity"] != "India"

    # 4. Cleanup: Delete test chunks
    delete_document_chunks_from_vector_store(doc_id)
