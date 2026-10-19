"""
Module: seed_policies.py
Responsibility: Seed the benchmark HR policy documents into MySQL and ChromaDB Vector Store.
Run:
    python app/db/seed_policies.py
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.database import SessionLocal, engine, Base
from app.db.document import PolicyDocument, PolicyChunk
from app.services.document_parser import chunk_markdown_document
from app.services.vector_store import add_chunks_to_vector_store

POLICIES_TO_SEED = [
    {
        "filename": "india_leave_policy_2025.md",
        "title": "India Annual & Statutory Leave Policy 2025",
        "entity": "India",
        "version": "v2025.1",
        "effective_date": "2025-01-01",
        "is_active": True,
    },
    {
        "filename": "uk_leave_policy_2025.md",
        "title": "UK Annual Leave & Sickness Absence Policy 2025",
        "entity": "UK",
        "version": "v2025.1",
        "effective_date": "2025-01-01",
        "is_active": True,
    },
    {
        "filename": "india_leave_policy_2024.md",
        "title": "India Annual Leave Policy 2024 (SUPERSEDED)",
        "entity": "India",
        "version": "v2024.1",
        "effective_date": "2024-01-01",
        "is_active": False,  # Superseded policy
    },
    {
        "filename": "grade_band_matrix.md",
        "title": "Global Grade Band Entitlement Matrix 2025",
        "entity": "Global",
        "version": "v2025.1",
        "effective_date": "2025-01-01",
        "is_active": True,
    },
]


def seed_database():
    print("[INFO] Starting HR Policy Ingestion into MySQL and ChromaDB...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    policies_dir = os.path.join(base_dir, "data", "sample_policies")

    total_chunks_indexed = 0

    try:
        for p in POLICIES_TO_SEED:
            filepath = os.path.join(policies_dir, p["filename"])
            if not os.path.exists(filepath):
                print(f"[WARNING] File not found: {filepath}")
                continue

            with open(filepath, "r", encoding="utf-8") as f:
                raw_text = f.read()

            # Check if already seeded
            existing = db.query(PolicyDocument).filter(PolicyDocument.title == p["title"]).first()
            if existing:
                print(f"[INFO] Document already exists: '{p['title']}' (ID: {existing.id}). Skipping.")
                continue

            # 1. Parse into semantic chunks
            parsed_chunks = chunk_markdown_document(raw_text)

            # 2. Insert into MySQL
            doc = PolicyDocument(
                title=p["title"],
                filename=p["filename"],
                file_type="md",
                version=p["version"],
                effective_date=p["effective_date"],
                entity=p["entity"],
                raw_content=raw_text,
                is_active=p["is_active"],
            )

            for c in parsed_chunks:
                chunk_record = PolicyChunk(
                    chunk_index=c["chunk_index"],
                    clause_id=c["clause_id"],
                    content=c["content"],
                    token_count=c["token_count"],
                )
                doc.chunks.append(chunk_record)

            db.add(doc)
            db.commit()
            db.refresh(doc)

            # 3. Index into ChromaDB Vector Store
            add_chunks_to_vector_store(
                document_id=doc.id,
                title=doc.title,
                entity=doc.entity,
                version=doc.version,
                effective_date=doc.effective_date,
                chunks=parsed_chunks,
            )

            print(f"[SUCCESS] Ingested: '{doc.title}' -> MySQL ID {doc.id} with {len(parsed_chunks)} clause chunks indexed in ChromaDB.")
            total_chunks_indexed += len(parsed_chunks)

        print(f"\n[COMPLETE] Seeding Finished! Total clause chunks indexed: {total_chunks_indexed}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
