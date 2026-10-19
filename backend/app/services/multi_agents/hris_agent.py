"""                                                                                                                                   
Module: hris_agent.py                                                                                                                 
Responsibility: Dedicated Worker Agent specialized in querying HRIS employee records and leave balances.                              
"""                                                                                                                                   
                                                                                                                                        
import json                                                                                                                           
from typing import Any                                                                                                                
from app.services.llm_client import call_llm                                                                                          
from app.tools.employee_tool import check_leave_balance, lookup_employee_record                                                       
                                                                                                                                        
HRIS_TOOLS = [                                                                                                                        
    {                                                                                                                                 
        "type": "function",                                                                                                           
        "function": {                                                                                                                 
            "name": "lookup_employee_record",                                                                                         
            "description": "Look up employee grade band, legal entity, and tenure by employee ID.",                                   
            "parameters": {                                                                                                           
                "type": "object",                                                                                                     
                "properties": {                                                                                                       
                    "employee_id": {"type": "string", "description": "The employee ID (e.g. EMP-101)"}                                
                },                                                                                                                    
                "required": ["employee_id"],                                                                                          
            },                                                                                                                        
        },                                                                                                                            
    },                                                                                                                                
    {                                                                                                                                 
        "type": "function",                                                                                                           
        "function": {                                                                                                                 
            "name": "check_leave_balance",                                                                                            
            "description": "Check accrued leave balance and operating legal entity by employee ID.",                                  
            "parameters": {                                                                                                           
                "type": "object",                                                                                                     
                "properties": {                                                                                                       
                    "employee_id": {"type": "string", "description": "The employee ID (e.g. EMP-101)"}                                
                },                                                                                                                    
                "required": ["employee_id"],                                                                                          
            },                                                                                                                        
        },                                                                                                                            
    },                                                                                                                                
]                                                                                                                                     
                                                                                                                                        
                                                                                                                                        
def run_hris_agent(task_description: str) -> dict[str, Any]:                                                                          
    """                                                                                                                               
    Executes an isolated HRIS specialist task and returns structured employee data.                                                   
    """                                                                                                                               
    messages = [                                                                                                                      
        {                                                                                                                             
            "role": "system",                                                                                                         
            "content": (                                                                                                              
                "You are the HRIS Database Specialist. Your sole responsibility is looking up "                                       
                "employee records and leave balances using controlled tools. "                                                        
                "Never guess any data. Extract the exact facts and return them clearly."                                              
            ),                                                                                                                        
        },                                                                                                                            
        {"role": "user", "content": task_description},                                                                                
    ]                                                                                                                                 
                                                                                                                                        
    resp = call_llm(messages=messages, tools=HRIS_TOOLS)                                                                              
    tool_calls = resp.get("tool_calls")                                                                                               
    executed_tools = []                                                                                                               
                                                                                                                                        
    if tool_calls:                                                                                                                    
        for call in tool_calls:                                                                                                       
            args = json.loads(call.function.arguments)                                                                                
            tool_output = None                                                                                                        
            if call.function.name == "lookup_employee_record":                                                                        
                tool_output = lookup_employee_record(**args).model_dump()                                                             
            elif call.function.name == "check_leave_balance":                                                                         
                tool_output = check_leave_balance(**args).model_dump()                                                                
                                                                                                                                        
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
        "summary": resp.get("content") or "No HRIS records found.",                                                                   
        "data": [],                                                                                                                   
        "cost_usd": resp["cost_usd"],                                                                                                 
        "tokens": resp["prompt_tokens"],                                                                                              
    }