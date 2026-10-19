"""                                                                                                                                   
Module: escalation_agent.py                                                                                                           
Responsibility: Dedicated Worker Agent specialized in HRBP escalations, grievance ticketing, and exception handling.                  
"""                                                                                                                                   
                                                                                                                                        
import json                                                                                                                           
from typing import Any                                                                                                                
from app.services.llm_client import call_llm                                                                                          
from app.tools.employee_tool import escalate_to_hrbp                                                                                  
                                                                                                                                        
ESCALATION_TOOLS = [                                                                                                                  
    {                                                                                                                                 
        "type": "function",                                                                                                           
        "function": {                                                                                                                 
            "name": "escalate_to_hrbp",                                                                                               
            "description": "Escalate a policy question, grievance, or exception to a human HR Business Partner (India or UK).",       
            "parameters": {                                                                                                           
                "type": "object",                                                                                                     
                "properties": {                                                                                                       
                    "employee_id": {                                                                                                  
                        "type": "string",                                                                                             
                        "description": "The employee ID (e.g. EMP-101)",                                                              
                    },                                                                                                                
                    "policy_topic": {                                                                                                 
                        "type": "string",                                                                                             
                        "description": "The policy topic requiring human review (e.g. Compassionate Leave, Grievance, Exception)",    
                    },                                                                                                                
                    "reason": {                                                                                                       
                        "type": "string",                                                                                             
                        "description": "Detailed explanation of why human HR discretion is needed (at least 10 characters)",          
                    },                                                                                                                
                    "urgency": {                                                                                                      
                        "type": "string",                                                                                             
                        "enum": ["low", "medium", "high"],                                                                            
                        "description": "Urgency level of the ticket",                                                                 
                    },                                                                                                                
                },                                                                                                                    
                "required": ["employee_id", "policy_topic", "reason"],                                                                
            },                                                                                                                        
        },                                                                                                                            
    }                                                                                                                                 
]                                                                                                                                     
                                                                                                                                        
                                                                                                                                        
def run_escalation_agent(task_description: str, employee_id: str | None = None) -> dict[str, Any]:                                    
    """                                                                                                                               
    Executes an isolated Escalation specialist task to create a formal HRBP ticket.                                                   
    """                                                                                                                               
    context = f"Employee ID: {employee_id}\n" if employee_id else ""                                                                  
    messages = [                                                                                                                      
        {                                                                                                                             
            "role": "system",                                                                                                         
            "content": (                                                                                                              
                "You are the HR Escalations & Grievance Specialist. "                                                                 
                "Your responsibility is assessing escalation requests, exceptions, or disputes, "                                     
                "and creating formal HRBP tickets using the 'escalate_to_hrbp' tool. "                                                
                "Always require a clear employee ID and specific reason for human review."                                            
            ),                                                                                                                        
        },                                                                                                                            
        {                                                                                                                             
            "role": "user",                                                                                                           
            "content": f"{context}Escalation Request: {task_description}",                                                            
        },                                                                                                                            
    ]                                                                                                                                 
                                                                                                                                        
    resp = call_llm(messages=messages, tools=ESCALATION_TOOLS)                                                                        
    tool_calls = resp.get("tool_calls")                                                                                               
    executed_tools = []                                                                                                               
                                                                                                                                        
    if tool_calls:                                                                                                                    
        for call in tool_calls:                                                                                                       
            args = json.loads(call.function.arguments)                                                                                
            tool_output = None                                                                                                        
            if call.function.name == "escalate_to_hrbp":                                                                              
                # Ensure employee_id fallback if missing in tool arguments                                                            
                if "employee_id" not in args and employee_id:                                                                         
                    args["employee_id"] = employee_id                                                                                 
                tool_output = escalate_to_hrbp(**args).model_dump()                                                                   
                                                                                                                                        
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
        "summary": resp.get("content") or "No escalation ticket was created.",                                                        
        "data": [],                                                                                                                   
        "cost_usd": resp["cost_usd"],                                                                                                 
    }