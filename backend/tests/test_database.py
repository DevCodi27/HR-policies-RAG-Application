import sys
import os
import pytest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import SessionLocal, engine, Base
from app.db.document import PolicyDocument, PolicyChunk


@pytest.fixture
def db_session():
    """Provides a transactional database session for testing."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_database_connection(db_session):
    """Verifies that the engine connects to MySQL and creates tables."""
    assert db_session is not None


def test_create_and_query_policy_document(db_session):
    """Verifies inserting a PolicyDocument and cascading PolicyChunk records."""
    # 1. Create a test policy document with 2 chunks
    test_doc = PolicyDocument(
        title="Test Leave Policy 2025",
        filename="test_leave_policy_2025.md",
        file_type="md",
        version="v2025.1",
        effective_date="2025-01-01",
        entity="India",
        raw_content="# Leave Policy\nClause 1: Annual Leave...",
        is_active=True,
    )

    chunk1 = PolicyChunk(
        chunk_index=0,
        clause_id="Cl. 1.1",
        content="Annual leave entitlement is 20 days.",
        token_count=8,
    )
    chunk2 = PolicyChunk(
        chunk_index=1,
        clause_id="Cl. 1.2",
        content="Sick leave entitlement is 10 days.",
        token_count=7,
    )

    test_doc.chunks.append(chunk1)
    test_doc.chunks.append(chunk2)

    # 2. Persist to MySQL
    db_session.add(test_doc)
    db_session.commit()
    db_session.refresh(test_doc)

    assert test_doc.id is not None
    assert len(test_doc.chunks) == 2

    # 3. Query back by title and entity
    retrieved = (
        db_session.query(PolicyDocument)
        .filter(PolicyDocument.title == "Test Leave Policy 2025")
        .first()
    )
    assert retrieved is not None
    assert retrieved.entity == "India"
    assert retrieved.chunks[0].clause_id == "Cl. 1.1"

    # 4. Cleanup test data
    db_session.delete(retrieved)
    db_session.commit()

    # Verify cascading delete removed the chunks as well
    orphaned_chunks = (
        db_session.query(PolicyChunk)
        .filter(PolicyChunk.document_id == retrieved.id)
        .all()
    )
    assert len(orphaned_chunks) == 0
