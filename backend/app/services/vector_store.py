import os
import chromadb

# Resolves the path to 'data/chroma_db' in the project root                                                                        
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))                                              
CHROMA_DIR = os.path.join(BASE_DIR, "data", "chroma_db")                                                                           
os.makedirs(CHROMA_DIR, exist_ok=True)

client = chromadb.PersistentClient(path=CHROMA_DIR)

collection = client.get_or_create_collection(
    name="policy_clauses",
    metadata={"hnsw:space": "cosine"}
)

def add_chunks_to_vector_store(
    document_id: int,
    title: str,                                                                                                                    
    entity: str,                                                                                                                   
    version: str,                                                                                                                  
    effective_date: str,                                                                                                           
    chunks: list[dict],
) -> None:
    if not chunks:
        return

    ids: list[str]=[]
    documents: list[str] = []                                                                                                      
    metadatas: list[dict] = []

    for c in chunks:
        chunk_idx = c["chunk_index"]
        clause_id = c.get("clause_id",f"Clause-{chunk_idx}")
        content = c["content"]                                                                                                     
                                                                                                                                       
        ids.append(f"doc_{document_id}_chunk_{chunk_idx}")                                                                         
        documents.append(content)                                                                                                  
        metadatas.append({                                                                                                         
            "document_id": document_id,                                                                                            
            "title": title,                                                                                                        
            "entity": entity,                                                                                                      
            "version": version,                                                                                                    
            "effective_date": effective_date,                                                                                      
            "clause_id": clause_id,                                                                                                
        })                                                                                                                         
                                                                                                                                    
    collection.upsert(                                                                                                             
        ids=ids,                                                                                                                   
        documents=documents,                                                                                                       
        metadatas=metadatas,                                                                                                       
    )

def search_policy_clauses(                                                                                                         
    query: str,                                                                                                                    
    entity: str,                                                                                                                   
    top_k: int = 3                                                                                                                 
) -> list[dict]:                                                                                                                   
    """                                                                                                                            
    Performs entity-scoped semantic search.                                                                                        
    Guarantees an India employee only retrieves India or Global policies.                                                          
    """                                                                                                                            
    where_filter = {                                                                                                               
        "$or": [                                                                                                                   
            {"entity": entity},                                                                                                    
            {"entity": "Global"},                                                                                                  
        ]                                                                                                                          
    }                                                                                                                              
                                                                                                                                    
    results = collection.query(                                                                                                    
        query_texts=[query],                                                                                                       
        n_results=top_k,                                                                                                           
        where=where_filter,                                                                                                        
    )                                                                                                                              
                                                                                                                                    
    retrieved: list[dict] = []                                                                                                     
    if not results or not results["documents"] or not results["documents"][0]:                                                     
        return retrieved                                                                                                           
                                                                                                                                    
    docs = results["documents"][0]                                                                                                 
    metas = results["metadatas"][0] if results["metadatas"] else []                                                                
    distances = results["distances"][0] if results["distances"] else []                                                            
                                                                                                                                    
    for doc, meta, dist in zip(docs, metas, distances):                                                                            
        # Cosine similarity score between 0.0 and 1.0                                                                              
        sim_score = round(1.0 - (dist / 2.0), 4) if dist is not None else 1.0                                                      
                                                                                                                                    
        retrieved.append({                                                                                                         
            "clause_id": str(meta.get("clause_id", "Unknown")),                                                                    
            "document_title": str(meta.get("title", "Policy Document")),                                                           
            "version": str(meta.get("version", "v1.0")),                                                                           
            "effective_date": str(meta.get("effective_date", "")),                                                                 
            "entity": str(meta.get("entity", entity)),                                                                             
            "content": doc,                                                                                                        
            "similarity_score": sim_score,                                                                                         
        })                                                                                                                         
                                                                                                                                    
    return retrieved                                                                                                               
                                                                                                                                       
                                                                                                                                    
def delete_document_chunks_from_vector_store(document_id: int) -> None:                                                            
    """Removes all indexed chunks for a document ID from ChromaDB."""                                                              
    collection.delete(                                                                                                             
        where={"document_id": document_id}                                                                                         
    )