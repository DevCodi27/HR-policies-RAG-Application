"""
Module: document.py
Responsibility: Pydantic schemas for document ingestion and retrieval.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class DocumentChunkOut(BaseModel):
    id: int
    chunk_index: int
    clause_id: Optional[str]
    content: str
    token_count: int

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    version: str
    effective_date: str
    entity: Literal["India", "UK", "Global"]
    is_active: bool
    uploaded_at: datetime
    total_chunks: int = 0

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    documents: list[DocumentOut]
    total_count: int