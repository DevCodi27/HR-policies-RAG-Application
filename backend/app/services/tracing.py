"""                                                                                                                                   
Module: tracing.py                                                                                                                    
Responsibility: Distributed tracing engine and local observability repository.                                                        
Supports optional export to Langfuse Cloud while feeding the live Angular Trace Dashboard.                                            
"""                                                                                                                                   
                                                                                                                                        
import os                                                                                                                             
import uuid
from dotenv import load_dotenv                                                                                                                   
from datetime import datetime, timezone                                                                                               
from typing import Any, Optional                                                                                                      
from app.schemas.chat import ChatQueryResponse  

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env")))
                                                                                                                                        
# Try importing Langfuse client safely                                                                                                
try:                                                                                                                                  
    from langfuse import Langfuse                                                                                                     
except ImportError:                                                                                                                   
    Langfuse = None

def _clean_env(key: str) -> Optional[str]:                                                                                            
    val = os.getenv(key)                                                                                                              
    if val:                                                                                                                           
        return val.strip("\"' ")                                                                                                      
    return None                                                                                                                   
                                                                                                                                        
# Detect Langfuse credentials from environment                                                                                        
LANGFUSE_PUBLIC_KEY = _clean_env("LANGFUSE_PUBLIC_KEY")                                                                               
LANGFUSE_SECRET_KEY = _clean_env("LANGFUSE_SECRET_KEY")                                                                               
LANGFUSE_HOST = _clean_env("LANGFUSE_HOST") or _clean_env("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"                                                              
                                                                                                                                        
langfuse_client: Optional[Any] = None                                                                                                 
if Langfuse and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:                                                                          
    try:                                                                                                                              
        langfuse_client = Langfuse(                                                                                                   
            public_key=LANGFUSE_PUBLIC_KEY,                                                                                           
            secret_key=LANGFUSE_SECRET_KEY,                                                                                           
            host=LANGFUSE_HOST,                                                                                                       
        )                                                                                                                             
    except Exception:                                                                                                                 
        langfuse_client = None                                                                                                        
                                                                                                                                        
# Structured In-Memory & Historical Trace Repository                                                                                  
_TRACE_HISTORY: list[dict[str, Any]] = []                                                                                             
                                                                                                                                        
                                                                                                                                        
def record_trace_from_response(                                                                                                       
    query: str,                                                                                                                       
    response: ChatQueryResponse,                                                                                                      
    employee_id: Optional[str] = None,                                                                                                
    agent_mode: str = "single",                                                                                                       
) -> dict[str, Any]:                                                                                                                  
    """                                                                                                                               
    Constructs a structured OpenTelemetry-compatible trace tree from an agent response,                                               
    caches it for the live dashboard, and forwards to Langfuse Cloud if active.                                                       
    """                                                                                                                               
    trace_id = str(uuid.uuid4())                                                                                                      
    timestamp = datetime.now(timezone.utc).isoformat()                                                                                
    total_tokens = response.prompt_tokens + response.completion_tokens                                                                
                                                                                                                                        
    # Determine status                                                                                                                
    if response.model == "security-guardrail":                                                                                        
        status = "SECURITY_BLOCKED"                                                                                                   
    elif "budget exceeded" in response.reply.lower():                                                                                 
        status = "BUDGET_EXCEEDED"                                                                                                    
    else:                                                                                                                             
        status = "SUCCESS"                                                                                                            
                                                                                                                                        
    # Build hierarchical spans from executed tools                                                                                    
    spans: list[dict[str, Any]] = []                                                                                                  
                                                                                                                                        
    # 1. Root Inbound Guardrail Span                                                                                                  
    spans.append({                                                                                                                    
        "span_id": str(uuid.uuid4()),                                                                                                 
        "name": "inbound_prompt_guardrail",                                                                                           
        "type": "guardrail",                                                                                                          
        "status": "PASS" if status != "SECURITY_BLOCKED" else "BLOCKED",                                                              
        "latency_sec": 0.001,                                                                                                         
        "input": {"query": query},                                                                                                    
        "output": {"is_safe": status != "SECURITY_BLOCKED"},                                                                          
    })                                                                                                                                
                                                                                                                                        
    # 2. Tool / Worker Delegation Spans                                                                                               
    for idx, tool in enumerate(response.tool_calls_executed, start=1):                                                                
        tool_name = tool.get("tool_name", "unknown_tool")                                                                             
        is_worker = "delegate_to_" in tool_name                                                                                       
        spans.append({                                                                                                                
            "span_id": str(uuid.uuid4()),                                                                                             
            "step": tool.get("step", idx),                                                                                            
            "name": tool_name,                                                                                                        
            "type": "worker_agent" if is_worker else "database_tool",                                                                 
            "latency_sec": round(response.latency_sec / max(len(response.tool_calls_executed), 1), 3),                                
            "input": tool.get("arguments", {}),                                                                                       
            "output": tool.get("output", {}),                                                                                         
        })                                                                                                                            
                                                                                                                                        
    # 3. Final Synthesis Span                                                                                                         
    spans.append({                                                                                                                    
        "span_id": str(uuid.uuid4()),                                                                                                 
        "name": "synthesis_and_grounding",                                                                                            
        "type": "llm_synthesis",                                                                                                      
        "model": response.model,                                                                                                      
        "tokens": response.completion_tokens,                                                                                         
        "cost_usd": response.cost_usd,                                                                                                
        "output": {"reply_preview": response.reply[:200] + ("..." if len(response.reply) > 200 else "")},                             
    })                                                                                                                                
                                                                                                                                        
    trace_record = {                                                                                                                  
        "trace_id": trace_id,                                                                                                         
        "timestamp": timestamp,                                                                                                       
        "employee_id": employee_id or "ANONYMOUS",                                                                                    
        "agent_mode": response.agent_mode or agent_mode,                                                                              
        "query": query,                                                                                                               
        "reply": response.reply,                                                                                                      
        "model": response.model,                                                                                                      
        "latency_sec": response.latency_sec,                                                                                          
        "prompt_tokens": response.prompt_tokens,                                                                                      
        "completion_tokens": response.completion_tokens,                                                                              
        "total_tokens": total_tokens,                                                                                                 
        "cost_usd": response.cost_usd,                                                                                                
        "status": status,                                                                                                             
        "tool_count": len(response.tool_calls_executed),                                                                              
        "spans": spans,                                                                                                               
        "langfuse_synced": langfuse_client is not None,                                                                               
    }                                                                                                                                 
                                                                                                                                        
    # Prepend to history so newest traces appear first                                                                                
    _TRACE_HISTORY.insert(0, trace_record)                                                                                            
                                                                                                                                        
    # Forward to Langfuse Cloud if configured                                                                                         
if langfuse_client:                                                                                                               
    try:                                                                                                                          
        # Modern Langfuse v5 API (start_observation)                                                                              
        if hasattr(langfuse_client, "start_observation"):                                                                         
            root_obs = langfuse_client.start_observation(                                                                         
                name=f"hr_desk_{trace_record['agent_mode']}",                                                                     
                input={"query": query},                                                                                           
                output={"reply": response.reply},                                                                                 
                as_type="chain",                                                                                                  
                metadata={                                                                                                        
                    "agent_mode": trace_record["agent_mode"],                                                                     
                    "status": status,                                                                                             
                    "employee_id": employee_id or "ANONYMOUS",                                                                    
                },                                                                                                                
            )                                                                                                                     
            for span in spans:                                                                                                    
                span_type = "guardrail" if "guardrail" in span["name"] else ("tool" if "tool" in span.get("type", "") else "span")
                child_obs = root_obs.start_observation(                                                                           
                    name=span["name"],                                                                                            
                    input=span.get("input"),                                                                                      
                    output=span.get("output"),                                                                                    
                    as_type=span_type,                                                                                            
                )                                                                                                                 
                child_obs.end()                                                                                                   
            root_obs.end()                                                                                                        
            langfuse_client.flush()                                                                                               
        # Legacy fallback for v2 SDKs                                                                                             
        elif hasattr(langfuse_client, "trace"):                                                                                   
            lf_trace = langfuse_client.trace(                                                                                     
                name=f"hr_desk_{trace_record['agent_mode']}",                                                                     
                session_id=employee_id or "anonymous",                                                                            
                metadata={"agent_mode": trace_record["agent_mode"], "status": status},                                            
                input={"query": query},                                                                                           
                output={"reply": response.reply},                                                                                 
            )                                                                                                                     
            for span in spans:                                                                                                    
                lf_trace.span(                                                                                                    
                    name=span["name"],                                                                                            
                    input=span.get("input"),                                                                                      
                    output=span.get("output"),                                                                                    
                )                                                                                                                 
            langfuse_client.flush()                                                                                               
    except Exception as e:                                                                                                        
        print(f"[LANGFUSE WARNING] Cloud sync failed: {e}")                                                                                                                      
                                                                                                                                        
    return trace_record                                                                                                               
                                                                                                                                        
                                                                                                                                        
def get_all_traces() -> list[dict[str, Any]]:                                                                                         
    """Returns all recorded traces, newest first."""                                                                                  
    return _TRACE_HISTORY                                                                                                             
                                                                                                                                        
                                                                                                                                        
def get_trace_by_id(trace_id: str) -> Optional[dict[str, Any]]:                                                                       
    """Returns a specific trace by UUID."""                                                                                           
    for t in _TRACE_HISTORY:                                                                                                          
        if t["trace_id"] == trace_id:                                                                                                 
            return t                                                                                                                  
    return None                                                                                                                       
                                                                                                                                        
                                                                                                                                        
def get_trace_metrics() -> dict[str, Any]:                                                                                            
    """Calculates aggregate metrics across all recorded traces for dashboard header."""                                               
    total_traces = len(_TRACE_HISTORY)                                                                                                
    if total_traces == 0:                                                                                                             
        return {                                                                                                                      
            "total_traces": 0,                                                                                                        
            "total_tokens": 0,                                                                                                        
            "total_cost_usd": 0.0,                                                                                                    
            "avg_latency_sec": 0.0,                                                                                                   
            "single_agent_traces": 0,                                                                                                 
            "multi_agent_traces": 0,                                                                                                  
            "langfuse_connected": langfuse_client is not None,                                                                        
        }                                                                                                                             
                                                                                                                                        
    total_tokens = sum(t["total_tokens"] for t in _TRACE_HISTORY)                                                                     
    total_cost = sum(t["cost_usd"] for t in _TRACE_HISTORY)                                                                           
    avg_latency = sum(t["latency_sec"] for t in _TRACE_HISTORY) / total_traces                                                        
    single_count = sum(1 for t in _TRACE_HISTORY if t["agent_mode"] == "single")                                                      
    multi_count = sum(1 for t in _TRACE_HISTORY if t["agent_mode"] == "multi")                                                        
                                                                                                                                        
    return {                                                                                                                          
        "total_traces": total_traces,                                                                                                 
        "total_tokens": total_tokens,                                                                                                 
        "total_cost_usd": round(total_cost, 6),                                                                                       
        "avg_latency_sec": round(avg_latency, 3),                                                                                     
        "single_agent_traces": single_count,                                                                                          
        "multi_agent_traces": multi_count,                                                                                            
        "langfuse_connected": langfuse_client is not None,                                                                            
    }