"""                                                                                                                                   
Module: policy_agent.py                                                                                                               
Responsibility: Dedicated Worker Agent specialized in legal policy retrieval, clause citation, and compliance analysis.               
"""                                                                                                                                   
                                                                                                                                        
import json                                                                                                                           
from typing import Any                                                                                                                
from app.services.llm_client import call_llm                                                                                          
from app.services.hybrid_search import hybrid_search_policy_clauses as search_policy_clauses                                          
                                                                                                                                        
POLICY_TOOLS = [                                                                                                                      
    {                                                                                                                                 
        "type": "function",                                                                                                           
        "function": {                                                                                                                 
            "name": "search_policy_clauses",                                                                                          
            "description": "Search HR policy documents (India and UK) for leave entitlements, carryover limits, probation rules, and allowances.",                                                                                                                           
            "parameters": {                                                                                                           
                "type": "object",                                                                                                     
                "properties": {                                                                                                       
                    "query": {                                                                                                        
                        "type": "string",                                                                                             
                        "description": "Semantic search query keywords (e.g. 'annual leave carryover limit', 'compassionate leave')", 
                    },                                                                                                                
                    "entity": {                                                                                                       
                        "type": "string",                                                                                             
                        "enum": ["India", "UK"],                                                                                      
                        "description": "The legal operating entity of the employee ('India' or 'UK')",                                
                    },                                                                                                                
                },                                                                                                                    
                "required": ["query", "entity"],                                                                                      
            },                                                                                                                        
        },                                                                                                                            
    }                                                                                                                                 
]                                                                                                                                     
                                                                                                                                        
                                                                                                                                        
def run_policy_agent(task_description: str, entity: str = "India") -> dict[str, Any]:                                                 
    """                                                                                                                               
    Executes an isolated Policy specialist task and returns grounded legal analysis with citations.                                   
    """                                                                                                                               
    messages = [                                                                                                                      
        {                                                                                                                             
            "role": "system",                                                                                                         
            "content": (                                                                                                              
                "You are the Senior HR Legal & Policy Compliance Specialist. "                                                        
                "Your sole responsibility is retrieving and interpreting HR policy clauses "                                          
                "for India and UK jurisdictions using the 'search_policy_clauses' tool. "                                             
                "Always ground your answer strictly in retrieved clauses. "                                                           
                "Always cite: [Document Title, Clause ID]. "                                                                          
                "If no matching policy clause is found, state that clearly without guessing."                                         
            ),                                                                                                                        
        },                                                                                                                            
        {                                                                                                                             
            "role": "user",                                                                                                           
            "content": f"Jurisdiction Entity: {entity}\nTask: {task_description}",                                                    
        },                                                                                                                            
    ]                                                                                                                                 
                                                                                                                                        
    resp = call_llm(messages=messages, tools=POLICY_TOOLS)                                                                            
    tool_calls = resp.get("tool_calls")                                                                                               
    executed_tools = []                                                                                                               
                                                                                                                                        
    if tool_calls:                                                                                                                    
        for call in tool_calls:                                                                                                       
            args = json.loads(call.function.arguments)                                                                                
            tool_output = None                                                                                                        
            if call.function.name == "search_policy_clauses":                                                                         
                # Fallback to function argument entity if not in tool call args                                                       
                if "entity" not in args:                                                                                              
                    args["entity"] = entity                                                                                           
                tool_output = search_policy_clauses(**args)                                                                           
                                                                                                                                        
            executed_tools.append({"tool": call.function.name, "output": tool_output})                                                
            messages.append({"role": "assistant", "content": "", "tool_calls": [call]})                                               
            messages.append({                                                                                                         
                "role": "tool",                                                                                                       
                "tool_call_id": call.id,                                                                                              
                "name": call.function.name,                                                                                           
                "content": json.dumps(tool_output),                                                                                   
            })                                                                                                                        
                                                                                                                                        
        final_resp = call_llm(messages=messages)                                                                                      
        return {                                                                                                                      
            "summary": final_resp["content"],                                                                                         
            "data": executed_tools,                                                                                                   
            "cost_usd": resp["cost_usd"] + final_resp["cost_usd"],                                                                    
            "tokens": resp["prompt_tokens"] + final_resp["completion_tokens"],                                                        
        }                                                                                                                             
                                                                                                                                        
    return {                                                                                                                          
        "summary": resp.get("content") or "No matching policy clauses retrieved.",                                                    
        "data": [],                                                                                                                   
        "cost_usd": resp["cost_usd"],                                                                                                 
        "tokens": resp["prompt_tokens"],                                                                                              
    }