"""                                                                                                                                   
Module: eval_harness.py                                                                                                               
Responsibility: Comprehensive RAG Evaluation Harness measuring:                                                                       
1. Retrieval IR Metrics: Hit Rate @ 3, Mean Reciprocal Rank (MRR), Recall @ 3                                                         
2. Generation Metrics: Citation Accuracy, Factual Grounding, Latency & Cost SLAs                                                      
"""                                                                                                                                   
                                                                                                                                        
import os                                                                                                                             
import sys                                                                                                                            
import json                                                                                                                           
import time                                                                                                                           
                                                                                                                                        
if hasattr(sys.stdout, "reconfigure"):                                                                                                
    sys.stdout.reconfigure(encoding="utf-8")                                                                                          
                                                                                                                                        
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))                                                    
from app.services.hybrid_search import hybrid_search_policy_clauses                                                                   
from app.services.chat_service import execute_chat_query                                                                              
                                                                                                                                        
                                                                                                                                        
def run_evaluation():                                                                                                                 
    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.json")                                                     
    with open(dataset_path, "r", encoding="utf-8") as f:                                                                              
        test_cases = json.load(f)                                                                                                     
                                                                                                                                        
    print("\n===================================================================")                                                    
    print("      ENTERPRISE HR POLICY DESK - FULL RAG & IR EVALUATION        ")                                                       
    print("===================================================================\n")                                                    
                                                                                                                                        
    # --- PART 1: RETRIEVAL ENGINE IR METRICS (Hit Rate, MRR, Recall) ---                                                             
    print("--- [STAGE 1: RETRIEVAL EVALUATION (Hit Rate, MRR, Recall @ 3)] ---")                                                      
    retrieval_cases = [tc for tc in test_cases if tc.get("relevant_clause_keywords")]                                                 
                                                                                                                                        
    hits = 0                                                                                                                          
    reciprocal_ranks = []                                                                                                             
    recalls = []                                                                                                                      
                                                                                                                                        
    for tc in retrieval_cases:                                                                                                        
        query = tc["query"]                                                                                                           
        entity = tc["entity"]                                                                                                         
        expected_kws = tc["relevant_clause_keywords"]                                                                                 
                                                                                                                                        
        retrieved_chunks = hybrid_search_policy_clauses(query=query, entity=entity, top_k=3)                                          
                                                                                                                                        
        # Check rank of first matching chunk                                                                                          
        rank_found = 0                                                                                                                
        for idx, chunk in enumerate(retrieved_chunks, start=1):                                                                       
            text_to_check = (chunk["clause_id"] + " " + chunk["content"]).lower()                                                     
            if any(kw.lower() in text_to_check for kw in expected_kws):                                                               
                rank_found = idx                                                                                                      
                break                                                                                                                 
                                                                                                                                        
        if rank_found > 0:                                                                                                            
            hits += 1                                                                                                                 
            reciprocal_rank = 1.0 / rank_found                                                                                        
            reciprocal_ranks.append(reciprocal_rank)                                                                                  
            recalls.append(1.0)                                                                                                       
            print(f"  [{tc['id']}] Hit at Rank #{rank_found} (RR={round(reciprocal_rank, 2)})")                                       
        else:                                                                                                                         
            reciprocal_ranks.append(0.0)                                                                                              
            recalls.append(0.0)                                                                                                       
            print(f"  [{tc['id']}] Missed (RR=0.0)")                                                                                  
                                                                                                                                        
    hit_rate = round((hits / len(retrieval_cases)) * 100, 1)                                                                          
    mrr = round(sum(reciprocal_ranks) / len(retrieval_cases), 3)                                                                      
    avg_recall = round((sum(recalls) / len(retrieval_cases)) * 100, 1)                                                                
                                                                                                                                        
    print(f"\n>> IR Retrieval Metrics (N={len(retrieval_cases)}):")                                                                   
    print(f"   * Hit Rate @ 3 : {hit_rate}%")                                                                                         
    print(f"   * MRR @ 3      : {mrr}")                                                                                               
    print(f"   * Recall @ 3   : {avg_recall}%\n")                                                                                     
                                                                                                                                        
    # --- PART 2: END-TO-END AGENT EVALUATION (Grounding & Citations) ---                                                             
    print("--- [STAGE 2: END-TO-END GENERATION & CITATION EVALUATION] ---")                                                           
    gen_passed = 0                                                                                                                    
    total_latency = 0.0                                                                                                               
    total_cost = 0.0                                                                                                                  
                                                                                                                                        
    for tc in test_cases:                                                                                                             
        tc_id = tc["id"]                                                                                                              
        tc_name = tc["name"]                                                                                                          
        query = tc["query"]                                                                                                           
        expected_keywords = tc["expected_keywords"]                                                                                   
        expected_citation = tc["expected_citation"]                                                                                   
                                                                                                                                        
        t0 = time.time()                                                                                                              
        resp = execute_chat_query(query)                                                                                              
        duration = round(time.time() - t0, 3)                                                                                         
        total_latency += duration                                                                                                     
        total_cost += resp.cost_usd                                                                                                   
                                                                                                                                        
        reply = resp.reply.lower()                                                                                                    
                                                                                                                                        
        # Keyword Grounding                                                                                                           
        kw_pass = len([kw for kw in expected_keywords if kw.lower() in reply]) > 0                                                    
                                                                                                                                        
        # Citation Grounding                                                                                                          
        cit_pass = True                                                                                                               
        if expected_citation:                                                                                                         
            cit_pass = expected_citation.lower() in reply                                                                             
                                                                                                                                        
        if kw_pass and cit_pass:                                                                                                      
            gen_passed += 1                                                                                                           
            print(f"  [{tc_id}] [PASS] ({duration}s | ${resp.cost_usd})")                                                             
        else:                                                                                                                         
            print(f"  [{tc_id}] [FAIL]")                                                                                              
            if not kw_pass:                                                                                                           
                print(f"       Missing keywords: {expected_keywords}")                                                                
            if not cit_pass:                                                                                                          
                print(f"       Missing citation: {expected_citation}")                                                                
                                                                                                                                        
    gen_accuracy = round((gen_passed / len(test_cases)) * 100, 1)                                                                     
    avg_latency = round(total_latency / len(test_cases), 3)                                                                           
                                                                                                                                        
    print("\n===================================================================")                                                    
    print("                       FINAL SCORECARD                            ")                                                       
    print("===================================================================")                                                      
    print(f"  Retrieval Hit Rate @ 3 : {hit_rate}%")                                                                                  
    print(f"  Retrieval MRR @ 3      : {mrr}")                                                                                        
    print(f"  Retrieval Recall @ 3   : {avg_recall}%")                                                                                
    print(f"  Generation Accuracy    : {gen_accuracy}% ({gen_passed}/{len(test_cases)} Passed)")                                      
    print(f"  Average Latency        : {avg_latency}s")                                                                               
    print(f"  Cumulative Cost        : ${round(total_cost, 6)}")                                                                      
    print("===================================================================\n")                                                    
                                                                                                                                        
                                                                                                                                        
if __name__ == "__main__":                                                                                                            
    run_evaluation()