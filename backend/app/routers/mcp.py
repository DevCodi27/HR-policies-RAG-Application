"""                                                                                                                                   
Module: mcp.py                                                                                                                        
Responsibility: Model Context Protocol (MCP) JSON-RPC 2.0 endpoint                                                                    
for exposing HRIS tools to external AI clients (Claude, Cursor, Antigravity).                                                         
"""

import json                                                                                                     
from fastapi import APIRouter, HTTPException, status

from app.tools.employee_tool import check_leave_balance, lookup_employee_record, escalate_to_hrbp                                     
from app.services.hybrid_search import hybrid_search_policy_clauses

from app.schemas.mcp import JsonRpcRequest, JsonRpcResponse

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])

 # 1. MCP Standard Tool Catalog (inputSchema format)                                                                                   
MCP_TOOLS = [                                                                                                                         
    {                                                                                                                                 
        "name": "lookup_employee_record",                                                                                             
        "description": "Look up an employee's legal entity, grade band, and tenure by employee ID.",                                  
        "inputSchema": {                                                                                                              
            "type": "object",                                                                                                         
            "properties": {                                                                                                           
                "employee_id": {"type": "string", "description": "Employee ID (e.g. EMP-101)"}                                        
            },                                                                                                                        
            "required": ["employee_id"],                                                                                              
        },                                                                                                                            
    },                                                                                                                                
    {                                                                                                                                 
        "name": "check_leave_balance",                                                                                                
        "description": "Check accrued leave balance and operating legal entity by employee ID.",                                      
        "inputSchema": {                                                                                                              
            "type": "object",                                                                                                         
            "properties": {                                                                                                           
                "employee_id": {"type": "string", "description": "Employee ID (e.g. EMP-101)"}                                        
            },                                                                                                                        
            "required": ["employee_id"],                                                                                              
        },                                                                                                                            
    },                                                                                                                                
    {                                                                                                                                 
        "name": "escalate_to_hrbp",                                                                                                   
        "description": "Escalate a policy question, grievance, or exception to a human HRBP.",                                        
        "inputSchema": {                                                                                                              
            "type": "object",                                                                                                         
            "properties": {                                                                                                           
                "employee_id": {"type": "string", "description": "Employee ID (e.g. EMP-101)"},                                       
                "policy_topic": {"type": "string", "description": "Topic e.g. Compassionate Leave"},                                  
                "reason": {"type": "string", "description": "Detailed explanation for escalation"},                                   
                "urgency": {"type": "string", "enum": ["low", "medium", "high"], "description": "Urgency level"},                     
            },                                                                                                                        
            "required": ["employee_id", "policy_topic", "reason"],                                                                    
        },                                                                                                                            
    },                                                                                                                                
    {                                                                                                                                 
        "name": "search_policy_clauses",                                                                                              
        "description": "Hybrid search (BM25 + Dense) for HR policy clauses across India and UK.",                                     
        "inputSchema": {                                                                                                              
            "type": "object",                                                                                                         
            "properties": {                                                                                                           
                "query": {"type": "string", "description": "Search query keywords"},                                                  
                "entity": {"type": "string", "enum": ["India", "UK"], "description": "Legal entity ('India' or 'UK')"},               
                "top_k": {"type": "integer", "description": "Number of clauses to return", "default": 3},                             
            },                                                                                                                        
            "required": ["query", "entity"],                                                                                          
        },                                                                                                                            
    },                                                                                                                                
]

 # 3. JSON-RPC 2.0 MCP Endpoint                                                                                                        
@router.post("", response_model=JsonRpcResponse, summary="MCP JSON-RPC 2.0 Gateway")                                                  
async def mcp_gateway(req: JsonRpcRequest) -> JsonRpcResponse:                                                                        
    if req.jsonrpc != "2.0":                                                                                                          
        return JsonRpcResponse(                                                                                                       
            id=req.id,                                                                                                                
            error={"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0'"},                                              
        )                                                                                                                             
                                                                                                                                        
    # Handler: tools/list                                                                                                             
    if req.method == "tools/list":                                                                                                    
        return JsonRpcResponse(                                                                                                       
            id=req.id,                                                                                                                
            result={"tools": MCP_TOOLS},                                                                                              
        )                                                                                                                             
                                                                                                                                        
    # Handler: tools/call                                                                                                             
    elif req.method == "tools/call":                                                                                                  
        params = req.params or {}                                                                                                     
        tool_name = params.get("name")                                                                                                
        args = params.get("arguments", {})                                                                                            
                                                                                                                                        
        if not tool_name:                                                                                                             
            return JsonRpcResponse(                                                                                                   
                id=req.id,                                                                                                            
                error={"code": -32602, "message": "Invalid params: 'name' is required for tools/call"},                               
            )                                                                                                                         
                                                                                                                                        
        try:                                                                                                                          
            output: Any = None                                                                                                        
            if tool_name == "lookup_employee_record":                                                                                 
                output = lookup_employee_record(**args).model_dump()                                                                  
            elif tool_name == "check_leave_balance":                                                                                  
                output = check_leave_balance(**args).model_dump()                                                                     
            elif tool_name == "escalate_to_hrbp":                                                                                     
                output = escalate_to_hrbp(**args).model_dump()                                                                        
            elif tool_name == "search_policy_clauses":                                                                                
                output = hybrid_search_policy_clauses(**args)                                                                         
            else:                                                                                                                     
                return JsonRpcResponse(                                                                                               
                    id=req.id,                                                                                                        
                    error={"code": -32601, "message": f"Method/Tool '{tool_name}' not found"},                                        
                )                                                                                                                     
                                                                                                                                        
            # Standard MCP tool response format: content array of text items                                                          
            return JsonRpcResponse(                                                                                                   
                id=req.id,                                                                                                            
                result={                                                                                                              
                    "content": [                                                                                                      
                        {"type": "text", "text": json.dumps(output, default=str)}                                                     
                    ],                                                                                                                
                    "isError": False,                                                                                                 
                },                                                                                                                    
            )                                                                                                                         
        except Exception as e:                                                                                                        
            return JsonRpcResponse(                                                                                                   
                id=req.id,                                                                                                            
                result={                                                                                                              
                    "content": [{"type": "text", "text": str(e)}],                                                                    
                    "isError": True,                                                                                                  
                },                                                                                                                    
            )                                                                                                                         
                                                                                                                                        
    return JsonRpcResponse(                                                                                                           
        id=req.id,                                                                                                                    
        error={"code": -32601, "message": f"Method '{req.method}' not found"},                                                        
    )

