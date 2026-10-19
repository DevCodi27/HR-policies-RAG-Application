import sys
import os
import io
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)

SAMPLE_MARKDOWN = """# India Annual & Sick Leave Policy 2025

## Clause 1: Scope & Eligibility
This policy applies to all full-time employees in the India legal entity across grades 1 through 7.

## Clause 2: Annual Leave Accrual
Employees accrue 1.75 days per completed calendar month of service, totaling 21 days annually.

## Clause 3: Sick & Casual Leave
Employees are entitled to 12 days of paid sick and casual leave per calendar year.
"""


def test_upload_markdown_document_success():
    """Verifies uploading, parsing, chunking, and MySQL persistence."""
    file_bytes = io.BytesIO(SAMPLE_MARKDOWN.encode("utf-8"))
    
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("india_leave_policy_2025.md", file_bytes, "text/markdown")},
        data={
            "title": "India Leave Policy 2025",
            "entity": "India",
            "version": "v2025.1",
            "effective_date": "2025-01-01",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "India Leave Policy 2025"
    assert data["entity"] == "India"
    assert data["version"] == "v2025.1"
    assert data["total_chunks"] == 4  # Title header + Clause 1, 2, 3

    doc_id = data["id"]

    # Verify listing includes the newly uploaded document
    list_resp = client.get("/api/v1/documents")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert any(d["id"] == doc_id for d in list_data["documents"])

    # Cleanup: delete the document
    del_resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_resp.status_code == 204


def test_upload_invalid_extension():
    """Verifies that non-markdown/txt files are rejected with 400."""
    fake_file = io.BytesIO(b"binary content")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malicious.exe", fake_file, "application/octet-stream")},
        data={
            "title": "Bad File",
            "entity": "UK",
            "version": "v1.0",
            "effective_date": "2025-01-01",
        },
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_upload_empty_file():
    """Verifies that empty files are rejected with 400."""
    empty_file = io.BytesIO(b"   ")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.md", empty_file, "text/markdown")},
        data={
            "title": "Empty File",
            "entity": "Global",
            "version": "v1.0",
            "effective_date": "2025-01-01",
        },
    )
    assert response.status_code == 400
    assert "Uploaded file is empty" in response.json()["detail"]


def test_delete_nonexistent_document():
    """Verifies 404 for deleting a non-existent document ID."""
    response = client.delete("/api/v1/documents/999999")
    assert response.status_code == 404
