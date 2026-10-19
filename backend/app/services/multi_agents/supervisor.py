"""                                                                                                                                   
Module: supervisor.py                                                                                                                 
Responsibility: Central Supervisor Orchestrator managing specialized worker agents (HRIS, Policy, Escalation).                        
"""                                                                                                                                   
                                                                                                                                        
import time                                                                                                                           
import json                                                                                                                           
from typing import Optional, Any                                                                                                      
from app.schemas.chat import ChatQueryResponse                                                                                        
from app.services.llm_client import call_llm                                                                                          
from app.services.security import detect_prompt_injection                                                                             
from app.services.multi_agents.hris_agent import run_hris_agent                                                                       
from app.services.multi_agents.policy_agent import run_policy_agent                                                                   
from app.services.multi_agents.escalation_agent import run_escalation_agent                                                           
                                                                                                                                        
SUPERVISOR_TOOLS = [                                                                                                                  
    {                                                                                                                                 
        "type": "function",                                                                                                           
        "function": {                                                                                                                 
            "name": "delegate_to_hris_specialist",                                                                                    
            "description": "Delegate to the HRIS Specialist to look up employee profile, operating legal entity (India or UK), tenure, and leave balances.",                                                                                                                   
            "parameters": {                                                                                                           
                "type": "object",                                                                                                     
                "properties": {                                                                                                       
                    "task_description": {                                                                                             
                        "type": "string",                                                                                             
                        "description": "Specific query or instruction for the HRIS worker, including employee ID (e.g. 'Look up EMP-101 profile and leave balance')",                                                                                                       
                    }                                                                                                                 
                },                                                                                                                    
                "required": ["task_description"],                                                                                     
            },                                                                                                                        
        },                                                                                                                            
    },                                                                                                                                
    {                                                                                                                                 
        "type": "function",                                                                                                           
        "function": {                                                                                                                 
            "name": "delegate_to_policy_specialist",                                                                                  
            "description": "Delegate to the Legal & Policy Specialist to search HR policy clauses, carryover rules, probation limits, and statutory allowances for India or UK.",                                                                                             
            "parameters": {                                                                                                           
                "type": "object",                                                                                                     
                "properties": {                                                                                                       
                    "task_description": {                                                                                             
                        "type": "string",                                                                                             
                        "description": "Specific policy question to research (e.g. 'annual leave carryover limit')",                  
                    },                                                                                                                
                    "entity": {                                                                                                       
                        "type": "string",                                                                                             
                        "enum": ["India", "UK"],                                                                                      
                        "description": "The legal operating entity of the employee ('India' or 'UK')",                                
                    },                                                                                                                
                },                                                                                                                    
                "required": ["task_description", "entity"],                                                                           
            },                                                                                                                        
        },                                                                                                                            
    },                                                                                                                                
    {                                                                                                                                 
        "type": "function",                                                                                                           
        "function": {                                                                                                                 
            "name": "delegate_to_escalation_specialist",                                                                              
            "description": "Delegate to the HRBP Escalations Specialist to create a formal ticket for policy exceptions, grievances, or human discretion.",                                                                                                                  
            "parameters": {                                                                                                           
                "type": "object",                                                                                                     
                "properties": {                                                                                                       
                    "task_description": {                                                                                             
                        "type": "string",                                                                                             
                        "description": "Explanation of the exception, grievance, or reason for HRBP review",                          
                    },                                                                                                                
                    "employee_id": {                                                                                                  
                        "type": "string",                                                                                             
                        "description": "The employee ID (e.g. EMP-101)",                                                              
                    },                                                                                                                
                },                                                                                                                    
                "required": ["task_description", "employee_id"],                                                                      
            },                                                                                                                        
        },                                                                                                                            
    },                                                                                                                                
]                                                                                                                                     
                                                                                                                                        
MAX_STEPS = 4                                                                                                                         
MAX_LATENCY_SEC = 35.0                                                                                                                
MAX_TOKENS = 12000                                                                                                                    
MAX_COST_USD = 0.0300                                                                                                                 
                                                                                                                                        
                                                                                                                                        
def run_supervisor_orchestrator(                                                                                                      
    message: str, employee_id: Optional[str] = None                                                                                   
) -> ChatQueryResponse:                                                                                                               
    """                                                                                                                               
    Supervisor-Worker multi-agent orchestrator. Analyzes intent, delegates tasks                                                      
    to domain specialist agents, aggregates findings, and synthesizes final response.                                                 
    """                                                                                                                               
    start_time = time.time()                                                                                                          
                                                                                                                                        
    # 1. Security Guardrail: Inbound Prompt Injection Defense                                                                         
    security_check = detect_prompt_injection(message)                                                                                 
    if not security_check.is_safe:                                                                                                    
        return ChatQueryResponse(                                                                                                     
            reply="I cannot fulfill this request. Security violation detected: System directives and policies cannot be overridden.", 
            model="security-guardrail",                                                                                               
            latency_sec=0.001,                                                                                                        
            prompt_tokens=0,                                                                                                          
            completion_tokens=0,                                                                                                      
            cost_usd=0.0,                                                                                                             
            tool_calls_executed=[],                                                                                                   
            agent_mode="multi",                                                                                                       
        )                                                                                                                             
                                                                                                                                        
    cumulative_prompt_tokens = 0                                                                                                      
    cumulative_completion_tokens = 0                                                                                                  
    cumulative_cost_usd = 0.0                                                                                                         
    executed_tools: list[dict[str, Any]] = []                                                                                         
                                                                                                                                        
    system_prompt = (                                                                                                                 
        "You are the Chief HR Orchestrator for the Enterprise Policy Answer Desk. "                                                   
        "You lead a team of specialized sub-agents:\n"                                                                                
        "1. HRIS Specialist ('delegate_to_hris_specialist'): For looking up employee profiles, legal entity ('India' or 'UK'), and accrued leave balances.\n"                                                                                                              
        "2. Policy Specialist ('delegate_to_policy_specialist'): For searching authoritative policy clauses and citations for India or UK.\n"                                                                                                                                  
        "3. Escalation Specialist ('delegate_to_escalation_specialist'): For creating official HRBP tickets when exceptions or grievances arise.\n\n"                                                                                                                  
        "Standard Operational Protocol:\n"                                                                                            
        "- If an employee ID is mentioned or provided, FIRST delegate to the HRIS Specialist to discover their operating entity and balances.\n"                                                                                                                            
        "- Next, delegate to the Policy Specialist with that entity to retrieve relevant policy rules and citations.\n"               
        "- If an exception or grievance is requested, delegate to the Escalation Specialist.\n"                                       
        "- Synthesize all worker findings into a clear, unified answer citing [Document Title, Clause ID]."                           
    )                                                                                                                                 
                                                                                                                                        
    context = f"Authenticated Employee ID: {employee_id}\n" if employee_id else ""                                                    
    messages = [                                                                                                                      
        {"role": "system", "content": system_prompt},                                                                                 
        {"role": "user", "content": f"{context}Employee Query: {message}"},                                                           
    ]                                                                                                                                 
                                                                                                                                        
    last_model = "qwen/qwen3.8-27b"                                                                                                   
    final_reply: Optional[str] = None                                                                                                 
                                                                                                                                        
    for step in range(1, MAX_STEPS + 1):                                                                                              
        elapsed_sec = time.time() - start_time                                                                                        
        total_tokens = cumulative_prompt_tokens + cumulative_completion_tokens                                                        
                                                                                                                                        
        # Governor Safety Checks                                                                                                      
        if elapsed_sec > MAX_LATENCY_SEC:                                                                                             
            final_reply = f"Latency budget exceeded ({round(elapsed_sec, 2)}s > {MAX_LATENCY_SEC}s). Supervisor terminated safely."   
            break                                                                                                                     
        if total_tokens > MAX_TOKENS:                                                                                                 
            final_reply = f"Token budget exceeded ({total_tokens} > {MAX_TOKENS}). Supervisor terminated safely."                     
            break                                                                                                                     
        if cumulative_cost_usd > MAX_COST_USD:                                                                                        
            final_reply = f"Cost budget exceeded (${round(cumulative_cost_usd, 4)} > ${MAX_COST_USD}). Supervisor terminated safely." 
            break                                                                                                                     
                                                                                                                                        
        llm_resp = call_llm(messages=messages, tools=SUPERVISOR_TOOLS)                                                                
                                                                                                                                        
        cumulative_prompt_tokens += llm_resp.get("prompt_tokens", 0)                                                                  
        cumulative_completion_tokens += llm_resp.get("completion_tokens", 0)                                                          
        cumulative_cost_usd = round(cumulative_cost_usd + llm_resp.get("cost_usd", 0.0), 6)                                           
        last_model = llm_resp.get("model", last_model)                                                                                
                                                                                                                                        
        tool_calls = llm_resp.get("tool_calls")                                                                                       
        if not tool_calls:                                                                                                            
            final_reply = llm_resp.get("content") or "Supervisor completed without message."                                          
            break                                                                                                                     
                                                                                                                                        
        for call in tool_calls:                                                                                                       
            tool_name = call.function.name                                                                                            
            args = json.loads(call.function.arguments)                                                                                
            worker_output: Any = None                                                                                                 
                                                                                                                                        
            if tool_name == "delegate_to_hris_specialist":                                                                            
                res = run_hris_agent(**args)                                                                                          
                worker_output = res["summary"]                                                                                        
                cumulative_prompt_tokens += res.get("tokens", 0)                                                                      
                cumulative_cost_usd = round(cumulative_cost_usd + res.get("cost_usd", 0.0), 6)                                        
            elif tool_name == "delegate_to_policy_specialist":                                                                        
                res = run_policy_agent(**args)                                                                                        
                worker_output = res["summary"]                                                                                        
                cumulative_prompt_tokens += res.get("tokens", 0)                                                                      
                cumulative_cost_usd = round(cumulative_cost_usd + res.get("cost_usd", 0.0), 6)                                        
            elif tool_name == "delegate_to_escalation_specialist":                                                                    
                res = run_escalation_agent(**args)                                                                                    
                worker_output = res["summary"]                                                                                        
                cumulative_prompt_tokens += res.get("tokens", 0)                                                                      
                cumulative_cost_usd = round(cumulative_cost_usd + res.get("cost_usd", 0.0), 6)                                        
                                                                                                                                        
            executed_tools.append({                                                                                                   
                "step": step,                                                                                                         
                "tool_name": tool_name,                                                                                               
                "arguments": args,                                                                                                    
                "output": worker_output,                                                                                              
            })                                                                                                                        
                                                                                                                                        
            messages.append({"role": "assistant", "content": "", "tool_calls": [call]})                                               
            messages.append({                                                                                                         
                "role": "tool",                                                                                                       
                "tool_call_id": call.id,                                                                                              
                "name": tool_name,                                                                                                    
                "content": str(worker_output),                                                                                        
            })                                                                                                                        
                                                                                                                                        
    total_latency = round(time.time() - start_time, 4)                                                                                
    return ChatQueryResponse(                                                                                                         
        reply=final_reply or "Supervisor step limit reached without complete resolution.",                                            
        model=last_model,                                                                                                             
        latency_sec=total_latency,                                                                                                    
        prompt_tokens=cumulative_prompt_tokens,                                                                                       
        completion_tokens=cumulative_completion_tokens,                                                                               
        cost_usd=cumulative_cost_usd,                                                                                                 
        tool_calls_executed=executed_tools,                                                                                           
        agent_mode="multi",                                                                                                           
    )