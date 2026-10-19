"""                                                                                                                                   
Module: test_mcp_client.py                                                                                                            
Responsibility: Tests for ExternalMCPClient connecting to an MCP gateway.                                                             
"""                                                                                                                                   
                                                                                                                                        
import sys                                                                                                                            
import os                                                                                                                             
import pytest                                                                                                                         
from unittest.mock import patch, MagicMock                                                                                            
                                                                                                                                        
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))                                                    
from app.services.mcp_client import ExternalMCPClient                                                                                 
                                                                                                                                        
                                                                                                                                        
def test_convert_mcp_to_openai_tool():                                                                                                
    """Verifies format conversion from MCP inputSchema to OpenAI tool schema."""                                                      
    mcp_tool = {                                                                                                                      
        "name": "workday_payroll_lookup",                                                                                             
        "description": "Fetch payroll history from Workday",                                                                          
        "inputSchema": {                                                                                                              
            "type": "object",                                                                                                         
            "properties": {                                                                                                           
                "employee_id": {"type": "string"}                                                                                     
            },                                                                                                                        
            "required": ["employee_id"]                                                                                               
        }                                                                                                                             
    }                                                                                                                                 
    openai_tool = ExternalMCPClient.convert_mcp_to_openai_tool(mcp_tool)                                                              
    assert openai_tool["type"] == "function"                                                                                          
    assert openai_tool["function"]["name"] == "workday_payroll_lookup"                                                                
    assert "parameters" in openai_tool["function"]                                                                                    
    assert openai_tool["function"]["parameters"]["required"] == ["employee_id"]                                                       
                                                                                                                                        
                                                                                                                                        
def test_fetch_remote_tools_mocked():                                                                                                 
    """Verifies fetching remote tools over JSON-RPC."""                                                                               
    client = ExternalMCPClient("http://mock-mcp-server:8000/mcp")                                                                     
                                                                                                                                        
    mock_response = MagicMock()                                                                                                       
    mock_response.json.return_value = {                                                                                               
        "jsonrpc": "2.0",                                                                                                             
        "id": 1,                                                                                                                      
        "result": {                                                                                                                   
            "tools": [{"name": "servicenow_ticket", "description": "Create ticket", "inputSchema": {}}]                               
        }                                                                                                                             
    }                                                                                                                                 
    mock_response.raise_for_status = MagicMock()                                                                                      
                                                                                                                                        
    with patch("httpx.Client.post", return_value=mock_response):                                                                      
        tools = client.fetch_remote_tools()                                                                                           
        assert len(tools) == 1                                                                                                        
        assert tools[0]["name"] == "servicenow_ticket"                                                                                
                                                                                                                                        
                                                                                                                                        
def test_execute_remote_tool_mocked():                                                                                                
    """Verifies executing a tool over JSON-RPC tools/call."""                                                                         
    client = ExternalMCPClient("http://mock-mcp-server:8000/mcp")                                                                     
                                                                                                                                        
    mock_response = MagicMock()                                                                                                       
    mock_response.json.return_value = {                                                                                               
        "jsonrpc": "2.0",                                                                                                             
        "id": 2,                                                                                                                      
        "result": {                                                                                                                   
            "content": [{"type": "text", "text": "{\"ticket_id\": \"INC-9999\"}"}],                                                   
            "isError": False                                                                                                          
        }                                                                                                                             
    }                                                                                                                                 
    mock_response.raise_for_status = MagicMock()                                                                                      
                                                                                                                                        
    with patch("httpx.Client.post", return_value=mock_response):                                                                      
        result = client.execute_remote_tool("servicenow_ticket", {"priority": "high"})                                                
        assert result["ticket_id"] == "INC-9999"