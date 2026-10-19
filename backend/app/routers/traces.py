"""                                                                                                                                   
Module: traces.py                                                                                                                     
Responsibility: FastAPI endpoints serving traces and telemetry metrics to the Observability Dashboard.                                
"""                                                                                                                                   
                                                                                                                                        
from typing import Any                                                                                                                
from fastapi import APIRouter, HTTPException, status                                                                                  
from app.services.tracing import (                                                                                                    
    get_all_traces,                                                                                                                   
    get_trace_by_id,                                                                                                                  
    get_trace_metrics,                                                                                                                
)                                                                                                                                     
                                                                                                                                        
router = APIRouter(prefix="/traces", tags=["Observability & Tracing"])                                                                
                                                                                                                                        
                                                                                                                                        
@router.get("", summary="Get all recorded traces and aggregate telemetry metrics")                                                    
def list_traces_endpoint() -> dict[str, Any]:                                                                                         
    """Returns dashboard summary metrics and all recorded traces."""                                                                  
    return {                                                                                                                          
        "metrics": get_trace_metrics(),                                                                                               
        "traces": get_all_traces(),                                                                                                   
    }                                                                                                                                 
                                                                                                                                        
                                                                                                                                        
@router.get("/{trace_id}", summary="Get detailed trace waterfall tree by trace ID")                                                   
def get_trace_detail_endpoint(trace_id: str) -> dict[str, Any]:                                                                       
    """Returns deep span tree, tool inputs/outputs, and latency breakdown for a trace."""                                             
    trace = get_trace_by_id(trace_id)                                                                                                 
    if not trace:                                                                                                                     
        raise HTTPException(                                                                                                          
            status_code=status.HTTP_404_NOT_FOUND,                                                                                    
            detail=f"Trace with ID '{trace_id}' was not found.",                                                                      
        )                                                                                                                             
    return trace                                                                                                                      
