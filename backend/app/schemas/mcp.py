from typing import Any, Optional
from pydantic import BaseModel, Field

class JsonRpcRequest(BaseModel):                                                                                                      
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")                                                               
    id: Optional[Any] = Field(default=None, description="Request identifier")                                                         
    method: str = Field(..., description="Method name: 'tools/list' or 'tools/call'")                                                 
    params: Optional[dict[str, Any]] = Field(default=None, description="Method parameters")                                           
                                                                                                                                        
                                                                                                                                        
class JsonRpcResponse(BaseModel):                                                                                                     
    jsonrpc: str = "2.0"                                                                                                              
    id: Optional[Any] = None                                                                                                          
    result: Optional[dict[str, Any]] = None                                                                                           
    error: Optional[dict[str, Any]] = None