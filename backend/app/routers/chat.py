from fastapi import FastAPI, APIRouter, HTTPException, status
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
)
from app.services.chat_service import execute_chat_query
from app.services.multi_agents.supervisor import run_supervisor_orchestrator
from app.services.tracing import record_trace_from_response

router = APIRouter(prefix="/chat", tags=["Chat"])
@router.post(
    "",
    response_model=ChatQueryResponse,
    summary="Ask policy question with automated tool execution",
)
def chat_endpoint(payload: ChatQueryRequest) -> ChatQueryResponse:
    if payload.agent_mode == "multi":                                                                                                 
        res = run_supervisor_orchestrator(                                                                                            
            message=payload.message,                                                                                                  
            employee_id=payload.employee_id,                                                                                          
        )                                                                                                                             
    else:                                                                                                                             
        res = execute_chat_query(                                                                                                     
            message=payload.message,                                                                                                  
            employee_id=payload.employee_id,                                                                                          
        )                                                                                                                             
                                                                                                                                        
    # Record trace for local dashboard and Langfuse Cloud                                                                             
    record_trace_from_response(                                                                                                       
        query=payload.message,                                                                                                        
        response=res,                                                                                                                 
        employee_id=payload.employee_id,                                                                                              
        agent_mode=payload.agent_mode,                                                                                                
    )                                                                                                                                 
    return res