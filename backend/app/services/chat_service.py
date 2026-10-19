import time
import json
from typing import Optional, Any
from app.schemas.chat import ChatQueryResponse
from app.services.llm_client import call_llm
from app.tools.employee_tool import check_leave_balance, lookup_employee_record, escalate_to_hrbp, EmployeeNotFoundError
from app.services.hybrid_search import hybrid_search_policy_clauses as search_policy_clauses
from app.services.security import detect_prompt_injection

POLICY_DESK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_leave_balance",
            "description": "Check accrued leave balance and operating legal entity by employee ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The employee ID (e.g. EMP-101)"
                    }
                },
                "required": ["employee_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_employee_record",
            "description": "Look up employee grade band, legal entity, and tenure by employee ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "The employee ID (e.g. EMP-101)"
                    }
                },
                "required": ["employee_id"]
            }
        }
    },
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
                        "description": "The employee ID (e.g. EMP-101)"                                                            
                    },                                                                                                             
                    "policy_topic": {                                                                                              
                        "type": "string",                                                                                          
                        "description": "The policy topic requiring human review (e.g. Compassionate Leave, Grievance, Exception)"  
                    },                                                                                                             
                    "reason": {                                                                                                    
                        "type": "string",                                                                                          
                        "description": "Detailed explanation of why human HR discretion is needed (at least 10 characters)"        
                    },                                                                                                             
                    "urgency": {                                                                                                   
                        "type": "string",                                                                                          
                        "enum": ["low", "medium", "high"],                                                                         
                        "description": "Urgency level of the ticket"                                                               
                    }                                                                                                              
                },                                                                                                                 
                "required": ["employee_id", "policy_topic", "reason"]                                                              
            }                                                                                                                      
        }                                                                                                                          
    },
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
                        "description": "Semantic search query keywords (e.g. 'annual leave carryover limit', 'compassionate leave')"  
                    },                                                                                                                
                    "entity": {                                                                                                       
                        "type": "string",                                                                                             
                        "enum": ["India", "UK"],                                                                                      
                        "description": "The legal operating entity of the employee ('India' or 'UK')"                                 
                    }                                                                                                                 
                },                                                                                                                    
                "required": ["query", "entity"]                                                                                       
            }                                                                                                                         
        }                                                                                                                             
    }                                                                                                                            
         
]

MAX_STEPS = 4                                                                                                                         
MAX_LATENCY_SEC = 5.0                                                                                                                 
MAX_TOKENS = 4000                                                                                                                     
MAX_COST_USD = 0.0100

def execute_chat_query(message: str, employee_id: Optional[str] = None) -> ChatQueryResponse:
    start_time = time.time()

    # Inbound Security Guardrail                                                                                                      
    security_check = detect_prompt_injection(message)                                                                                 
    if not security_check.is_safe:                                                                                                    
        return ChatQueryResponse(                                                                                                     
            reply="I cannot fulfill this request. Security violation detected: System directives and policies cannot be overridden.", 
            model="security-guardrail",                                                                                               
            latency_sec=0.001,                                                                                                        
            prompt_tokens=0,                                                                                                          
            completion_tokens=0,                                                                                                      
            cost_usd=0.0,                                                                                                             
            tool_calls_executed=[]                                                                                                    
        )                                                                                                        
                                                                                                                                          
    cumulative_prompt_tokens = 0                                                                                                      
    cumulative_completion_tokens = 0                                                                                                  
    cumulative_cost_usd = 0.0                                                                                                         
    executed_tools: list[dict[str, Any]] = []
    system_prompt = (                                                                                                                 
        "You are the Enterprise HR Policy Assistant for Policy Answer Desk. "                                                         
        "Always use controlled tools to look up employee records, leave balances, or policy clauses before answering. "               
        "Never guess an employee's grade band, entity, or leave balance. "                                                            
        "When an employee asks a question with an employee ID, look up their record first to determine their legal entity ('India' or 'UK'). "                                                                                                                                
        "Then call 'search_policy_clauses' with that entity to retrieve relevant policy rules. "                                      
        "Always ground your answer with strict citations: [Document Title, Clause ID]. "                                              
        "If policies are silent or ambiguous, state that clearly and offer to escalate to HRBP."                                      
    )
    messages = [
        {                                                                                                                             
            "role": "system",                                                                                                         
            "content": system_prompt                                                                                                                         
        },
        {"role": "user", "content": message}
    ]

    last_model = "qwen/qwen3.8-27b"
    final_reply: Optional[str] = None
    for step in range(1, MAX_STEPS + 1):

        elapsed_sec = time.time() - start_time                                                                                        
        total_tokens = cumulative_prompt_tokens + cumulative_completion_tokens                                                        
                                                                                                                                        
        if elapsed_sec > MAX_LATENCY_SEC:                                                                                             
            final_reply = f"Latency budget exceeded ({round(elapsed_sec, 2)}s > {MAX_LATENCY_SEC}s). Request terminated safely."      
            break                                                                                                                     
                                                                                                                                        
        if total_tokens > MAX_TOKENS:                                                                                                 
            final_reply = f"Token budget exceeded ({total_tokens} > {MAX_TOKENS}). Request terminated safely."                        
            break                                                                                                                     
                                                                                                                                        
        if cumulative_cost_usd > MAX_COST_USD:                                                                                        
            final_reply = f"Cost budget exceeded (${round(cumulative_cost_usd, 4)} > ${MAX_COST_USD}). Request terminated safely."    
            break

        llm_resp = call_llm(messages=messages, tools=POLICY_DESK_TOOLS)

        cumulative_prompt_tokens += llm_resp.get("prompt_tokens", 0)                                                                  
        cumulative_completion_tokens += llm_resp.get("completion_tokens", 0)                                                          
        cumulative_cost_usd = round(cumulative_cost_usd + llm_resp.get("cost_usd", 0.0), 6)                                           
        last_model = llm_resp.get("model", last_model)

        tool_calls = llm_resp.get("tool_calls")

        if not tool_calls:                                                                                                            
            final_reply = llm_resp.get("content") or "No reply generated."                                                            
            break


        for call in tool_calls:
            tool_name = call.function.name
            args = json.loads(call.function.arguments)
            tool_output: Any = None
            try:
                if tool_name == "check_leave_balance":
                    tool_output = check_leave_balance(**args).model_dump()
                elif tool_name == "lookup_employee_record":
                    tool_output = lookup_employee_record(**args).model_dump()
                elif tool_name == "escalate_to_hrbp":
                    tool_output = escalate_to_hrbp(**args).model_dump()
                elif tool_name == "search_policy_clauses":
                    tool_output = search_policy_clauses(**args)
            except EmployeeNotFoundError as e:                                                                                        
                tool_output = {"error": str(e)}                                                                                       
            except Exception as e:                                                                                                    
                tool_output = {"error": f"Tool execution failed: {str(e)}"}


            executed_tools.append({
                "step": step,
                "tool_name": tool_name,
                "arguments": args,
                "output": tool_output,
            })

            messages.append({"role": "assistant", "content": "", "tool_calls": [call]})
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": tool_name,
                "content": json.dumps(tool_output)
            })

    total_latency = round(time.time() - start_time, 4)
    return ChatQueryResponse(
        reply=final_reply or "Agent step limit reached without complete resolution.",                                                 
        model=last_model,                                                                                                             
        latency_sec=total_latency,                                                                                                    
        prompt_tokens=cumulative_prompt_tokens,                                                                                       
        completion_tokens=cumulative_completion_tokens,                                                                               
        cost_usd=cumulative_cost_usd,                                                                                                 
        tool_calls_executed=executed_tools,
    )
