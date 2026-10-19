from datetime import datetime                                                                                                      
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey                                                
from sqlalchemy.orm import relationship                                                                                            
from app.db.database import Base 


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), default="md")
    version = Column(String(50), nullable=False)              # e.g., "v2025.1"
    effective_date = Column(String(50), nullable=False)       # e.g., "2025-01-01"
    entity = Column(String(50), nullable=False)               # "India", "UK", "Global"
    raw_content = Column(Text(length=4294967295), nullable=False) # LongText for full text
    is_active = Column(Boolean, default=True)                 # Soft deprecation flag
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # 1-to-many relationship with chunks 
    chunks = relationship("PolicyChunk", back_populates="document", cascade="all, delete-orphan")


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("policy_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)             # 0, 1, 2, ...
    clause_id = Column(String(100), nullable=True)            # e.g., "Clause 4.2"
    content = Column(Text, nullable=False)                    # Chunk text
    token_count = Column(Integer, default=0)

    # Relationship back to parent document
    document = relationship("PolicyDocument", back_populates="chunks")