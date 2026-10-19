"""
Module: document.py
Responsibility: FastAPI router for document uploads, parsing, and management.
"""

from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.document import PolicyDocument, PolicyChunk
from app.schemas.document import DocumentOut, DocumentListResponse
from app.services.document_parser import chunk_markdown_document, extract_text_from_file_bytes
from app.services.vector_store import (                                                                                            
    add_chunks_to_vector_store,                                                                                                    
    delete_document_chunks_from_vector_store,                                                                                      
)

router = APIRouter(prefix="/documents", tags=["Policy Documents"])


@router.post(
    "/upload",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and chunk a policy document into MySQL",
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(..., description="Document display title"),
    entity: Literal["India", "UK", "Global"] = Form(..., description="Operating entity"),
    version: str = Form(..., description="Policy version e.g. v2025.1"),
    effective_date: str = Form(..., description="Effective date YYYY-MM-DD"),
    db: Session = Depends(get_db),
) -> DocumentOut:
    """
    Accepts a .md or .txt document, extracts text, breaks into clauses,
    and commits both document record and chunks to MySQL atomically.
    """
    # 1. Validate file extension
    filename = file.filename or "unknown.md"
    ext = filename.split(".")[-1].lower() if "." in filename else "md"
    if ext not in ["md", "txt", "markdown", "pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Only .md and .txt files are supported.",
        )

    # 2. Read file contents into text
    content_bytes = await file.read()
    try:
        raw_text = extract_text_from_file_bytes(content_bytes, ext)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from {filename}: {e}",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 3. Parse into semantic chunks
    parsed_chunks = chunk_markdown_document(raw_text)

    # 4. Create parent PolicyDocument record
    policy_doc = PolicyDocument(
        title=title,
        filename=filename,
        file_type=ext,
        version=version,
        effective_date=effective_date,
        entity=entity,
        raw_content=raw_text,
        is_active=True,
    )

    # 5. Attach children PolicyChunk records
    for c in parsed_chunks:
        chunk_obj = PolicyChunk(
            chunk_index=c["chunk_index"],
            clause_id=c["clause_id"],
            content=c["content"],
            token_count=c["token_count"],
        )
        policy_doc.chunks.append(chunk_obj)

    # 6. Commit to MySQL
    db.add(policy_doc)
    db.commit()
    db.refresh(policy_doc)

    # 7. Index in ChromaDB for Semantic Search                                                                                     
    add_chunks_to_vector_store(                                                                                                    
        document_id=policy_doc.id,                                                                                                 
        title=policy_doc.title,                                                                                                    
        entity=policy_doc.entity,                                                                                                  
        version=policy_doc.version,                                                                                                
        effective_date=policy_doc.effective_date,                                                                                  
        chunks=parsed_chunks,                                                                                                      
    )

    return DocumentOut(
        id=policy_doc.id,
        title=policy_doc.title,
        filename=policy_doc.filename,
        file_type=policy_doc.file_type,
        version=policy_doc.version,
        effective_date=policy_doc.effective_date,
        entity=policy_doc.entity,  # type: ignore
        is_active=policy_doc.is_active,
        uploaded_at=policy_doc.uploaded_at,
        total_chunks=len(policy_doc.chunks),
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded policy documents",
)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    """Returns all active policy documents with their chunk counts."""
    docs = db.query(PolicyDocument).filter(PolicyDocument.is_active == True).all()
    results = [
        DocumentOut(
            id=d.id,
            title=d.title,
            filename=d.filename,
            file_type=d.file_type,
            version=d.version,
            effective_date=d.effective_date,
            entity=d.entity,  # type: ignore
            is_active=d.is_active,
            uploaded_at=d.uploaded_at,
            total_chunks=len(d.chunks),
        )
        for d in docs
    ]
    return DocumentListResponse(documents=results, total_count=len(results))


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a policy document and its chunks",
)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Deletes a document and its cascading chunks from MySQL."""
    doc = db.query(PolicyDocument).filter(PolicyDocument.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )
    db.delete(doc)
    delete_document_chunks_from_vector_store(document_id)
    db.commit()
    return None