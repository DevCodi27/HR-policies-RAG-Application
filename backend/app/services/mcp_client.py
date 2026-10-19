"""                                                                                                                                   
Module: mcp_client.py                                                                                                                 
Responsibility: MCP Client adapter that connects to external MCP servers,                                                             
discovers remote tools via JSON-RPC 2.0, and converts them into Groq/OpenAI function schemas.                                         
"""                                                                                                                                   
                                                                                                                                        
import json                                                                                                                           
from typing import Any, Optional                                                                                                      
import httpx                                                                                                                          
                                                                                                                                        
                                                                                                                                        
class ExternalMCPClient:                                                                                                              
    """                                                                                                                               
    Client for connecting to external Model Context Protocol (MCP) servers.                                                           
    """                                                                                                                               
                                                                                                                                        
    def __init__(self, server_url: str, timeout_sec: float = 5.0):                                                                    
        self.server_url = server_url                                                                                                  
        self.timeout_sec = timeout_sec                                                                                                
                                                                                                                                        
    def fetch_remote_tools(self) -> list[dict[str, Any]]:                                                                             
        """                                                                                                                           
        Discovers tools available on the external MCP server via JSON-RPC 'tools/list'.                                               
        """                                                                                                                           
        payload = {                                                                                                                   
            "jsonrpc": "2.0",                                                                                                         
            "id": 1,                                                                                                                  
            "method": "tools/list",                                                                                                   
        }                                                                                                                             
        try:                                                                                                                          
            with httpx.Client(timeout=self.timeout_sec) as client:                                                                    
                resp = client.post(self.server_url, json=payload)                                                                     
                resp.raise_for_status()                                                                                               
                data = resp.json()                                                                                                    
                return data.get("result", {}).get("tools", [])                                                                        
        except Exception as e:                                                                                                        
            print(f"[WARNING] Failed to fetch tools from external MCP server ({self.server_url}): {e}")                               
            return []                                                                                                                 
                                                                                                                                        
    @staticmethod                                                                                                                     
    def convert_mcp_to_openai_tool(mcp_tool: dict[str, Any]) -> dict[str, Any]:                                                       
        """                                                                                                                           
        Converts standard MCP inputSchema format into Groq/OpenAI function calling schema.                                            
        """                                                                                                                           
        return {                                                                                                                      
            "type": "function",                                                                                                       
            "function": {                                                                                                             
                "name": mcp_tool.get("name", "unknown_tool"),                                                                         
                "description": mcp_tool.get("description", ""),                                                                       
                "parameters": mcp_tool.get("inputSchema", {"type": "object", "properties": {}}),                                      
            },                                                                                                                        
        }                                                                                                                             
                                                                                                                                        
    def execute_remote_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:                                                  
        """                                                                                                                           
        Executes a remote tool on the external MCP server via JSON-RPC 'tools/call'.                                                  
        """                                                                                                                           
        payload = {                                                                                                                   
            "jsonrpc": "2.0",                                                                                                         
            "id": 2,                                                                                                                  
            "method": "tools/call",                                                                                                   
            "params": {                                                                                                               
                "name": tool_name,                                                                                                    
                "arguments": arguments,                                                                                               
            },                                                                                                                        
        }                                                                                                                             
        try:                                                                                                                          
            with httpx.Client(timeout=self.timeout_sec) as client:                                                                    
                resp = client.post(self.server_url, json=payload)                                                                     
                resp.raise_for_status()                                                                                               
                result = resp.json().get("result", {})                                                                                
                                                                                                                                        
                # Check for standard MCP content payload                                                                              
                content_items = result.get("content", [])                                                                             
                if content_items and content_items[0].get("type") == "text":                                                          
                    raw_text = content_items[0]["text"]                                                                               
                    try:                                                                                                              
                        return json.loads(raw_text)                                                                                   
                    except json.JSONDecodeError:                                                                                      
                        return raw_text                                                                                               
                return result                                                                                                         
        except Exception as e:                                                                                                        
            return {"error": f"External MCP call to '{tool_name}' failed: {str(e)}"}