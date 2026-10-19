"""                                                                                                                                   
Module: hybrid_search.py                                                                                                              
Responsibility: Hybrid Search combining Dense Vector Search (ChromaDB)                                                                
and Sparse Lexical Search (BM25) with Reciprocal Rank Fusion (RRF) and Reranking.                                                     
"""

from typing import Any
from rank_bm25 import BM25Okapi
from app.services.vector_store import collection, search_policy_clauses

def bm25_search(query: str, entity: str, top_k: int = 10) -> list[dict[str, Any]]:
    """                                                                                                                               
    Performs Okapi BM25 keyword search across all indexed chunks for an entity.                                                       
    """
    where_filter = {
        "$or": [
            {"entity": entity},
            {"entity": "Global"}
        ]
    }
    
    res = collection.get(where=where_filter, include=["documents", "metadatas"])                                                      
    docs = res.get("documents") or []                                                                                                 
    metas = res.get("metadatas") or []

    if not docs:
        return []

    tokenized_corpus = [doc.lower().split() for doc in docs]                                                                          
    bm25 = BM25Okapi(tokenized_corpus)

    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)

    scored_candidates = []                                                                                                            
    for doc, meta, score in zip(docs, metas, scores):                                                                                 
        if score > 0:  # Only keep documents with at least one matching token                                                         
            scored_candidates.append({                                                                                                
                "clause_id": str(meta.get("clause_id", "Unknown")),                                                                   
                "document_title": str(meta.get("title", "Policy Document")),                                                          
                "version": str(meta.get("version", "v1.0")),                                                                          
                "effective_date": str(meta.get("effective_date", "")),                                                                
                "entity": str(meta.get("entity", entity)),                                                                            
                "content": doc,                                                                                                       
                "bm25_score": round(float(score), 4),                                                                                 
            })

    scored_candidates.sort(key=lambda x: x["bm25_score"], reverse=True)                                                               
    return scored_candidates[:top_k]

def hybrid_search_policy_clauses(                                                                                                     
    query: str,                                                                                                                       
    entity: str,                                                                                                                      
    top_k: int = 3,                                                                                                                   
    active_only: bool = True,                                                                                                         
) -> list[dict[str, Any]]:                                                                                                            
    """                                                                                                                               
    Executes Hybrid Search (ChromaDB Dense + BM25 Sparse),                                                                            
    merges using Reciprocal Rank Fusion (RRF), and applies temporal reranking.                                                        
    """                                                                                                                               
    # 1. Retrieve top 5 Dense (Semantic) candidates                                                                                   
    dense_results = search_policy_clauses(query=query, entity=entity, top_k=5)                                                        
                                                                                                                                        
    # 2. Retrieve top 5 Sparse (BM25 Keyword) candidates                                                                              
    sparse_results = bm25_search(query=query, entity=entity, top_k=5)                                                                 
                                                                                                                                        
    # 3. Reciprocal Rank Fusion (RRF)                                                                                                 
    # RRF formula: score = 1 / (60 + rank)                                                                                            
    rrf_scores: dict[str, float] = {}                                                                                                 
    doc_map: dict[str, dict[str, Any]] = {}                                                                                           
    k_constant = 60                                                                                                                   
                                                                                                                                        
    # Process Dense ranks                                                                                                             
    for rank, doc in enumerate(dense_results, start=1):                                                                               
        key = doc["content"]                                                                                                          
        rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (k_constant + rank))                                                      
        doc_map[key] = doc                                                                                                            
                                                                                                                                        
    # Process Sparse ranks                                                                                                            
    for rank, doc in enumerate(sparse_results, start=1):                                                                              
        key = doc["content"]                                                                                                          
        rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (k_constant + rank))                                                      
        if key not in doc_map:                                                                                                        
            doc["similarity_score"] = 0.5  # default if not found in dense                                                            
            doc_map[key] = doc                                                                                                        
                                                                                                                                        
    # 4. Reranking & Temporal Filtering                                                                                               
    ranked_docs = []
    asking_for_past = any(w in query.lower() for w in ["2024", "past", "history", "historical", "superseded", "previous"])

    for key, rrf_score in rrf_scores.items():                                                                                         
        doc_info = doc_map[key]                                                                                                       
        doc_info["rrf_score"] = round(rrf_score, 5)

        is_superseded = "SUPERSEDED" in doc_info.get("document_title", "").upper()                                                    
        # If user is asking for current rules, filter out obsolete policies                                                           
        if active_only and is_superseded and not asking_for_past:                                                                     
            continue                                                                               
                                                                                                                                        
        # Temporal bonus: boost 2025/active policies                                                                                  
        effective_date = doc_info.get("effective_date", "")                                                                           
        if "2025" in effective_date:                                                                                                  
            doc_info["rrf_score"] += 0.01  # Temporal precedence bonus                                                                
                                                                                                                                        
        ranked_docs.append(doc_info)                                                                                                  
                                                                                                                                        
    # Sort descending by final fused RRF score                                                                                        
    ranked_docs.sort(key=lambda x: x["rrf_score"], reverse=True)                                                                      
    return ranked_docs[:top_k]