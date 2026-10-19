"""
Module: document_parser.py
Responsibility: Semantic Markdown clause parser and chunker for HR policy documents.
"""
import io
import re
from typing import TypedDict
import pypdf
import docx
from app.services.token_cost_calculator import count_tokens


class ParsedChunk(TypedDict):
    chunk_index: int
    clause_id: str
    content: str
    token_count: int


def chunk_markdown_document(raw_text: str) -> list[ParsedChunk]:
    if not raw_text or not raw_text.strip():
        return []

    # Regex to split on Markdown headings (e.g., "# Title", "## Clause 1: Eligibility")
    heading_pattern = re.compile(r"(?m)^(#{1,4}\s+.+)$")
    splits = heading_pattern.split(raw_text)

    chunks: list[ParsedChunk] = []
    chunk_idx = 0

    # If document has content before the first heading (intro/preamble)
    if splits and splits[0].strip():
        intro_text = splits[0].strip()
        chunks.append({
            "chunk_index": chunk_idx,
            "clause_id": "Preamble",
            "content": intro_text,
            "token_count": count_tokens(intro_text),
        })
        chunk_idx += 1

    # Pairs of (heading, body)
    for i in range(1, len(splits), 2):
        heading = splits[i].strip()
        body = splits[i + 1].strip() if i + 1 < len(splits) else ""

        full_content = f"{heading}\n\n{body}".strip()
        if not full_content:
            continue

        # Extract a clean clause_id from the heading (remove leading hashes #)
        clean_title = re.sub(r"^#+\s*", "", heading).strip()

        chunks.append({
            "chunk_index": chunk_idx,
            "clause_id": clean_title,
            "content": full_content,
            "token_count": count_tokens(full_content),
        })
        chunk_idx += 1

    return chunks

def extract_text_from_file_bytes(content_bytes: bytes, file_ext: str) -> str:
    """                                                                                                                               
    Extracts raw text from PDF, DOCX, Markdown, or plain text bytes in memory.                                                        
    """ 
    ext = file_ext.lower().lstrip(".")
    if ext == 'pdf':
        reader = pypdf.PdfReader(io.BytesIO(content_bytes))                                                                           
        pages_text = []                                                                                                               
        for i, page in enumerate(reader.pages):                                                                                       
            text = page.extract_text()                                                                                                
            if text and text.strip():                                                                                                 
                pages_text.append(f"## Page {i + 1}\n\n{text.strip()}")                                                               
        return "\n\n".join(pages_text)                                                                                                
                                                                                                                                        
    elif ext in ["docx", "doc"]:                                                                                                      
        doc = docx.Document(io.BytesIO(content_bytes))                                                                                
        paragraphs = []                                                                                                               
        for p in doc.paragraphs:                                                                                                      
            if p.text.strip():                                                                                                        
                # If paragraph style is a Heading, format it as markdown heading                                                      
                if p.style and p.style.name.startswith("Heading"):                                                                    
                    paragraphs.append(f"## {p.text.strip()}")                                                                         
                else:                                                                                                                 
                    paragraphs.append(p.text.strip())                                                                                 
        return "\n\n".join(paragraphs)                                                                                                
                                                                                                                                        
    elif ext in ["md", "markdown", "txt"]:                                                                                            
        return content_bytes.decode("utf-8")

    else:                                                                                                                             
        raise ValueError(f"Unsupported file format: .{ext}")