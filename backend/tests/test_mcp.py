"""                                                                                                                                   
Module: test_mcp.py                                                                                                                   
Responsibility: Integration tests for Model Context Protocol (MCP) JSON-RPC 2.0 gateway.                                              
"""                                                                                                                                   
                                                                                                                                        
import sys                                                                                                                            
import os                                                                                                                             
import pytest                                                                                                                         
from fastapi.testclient import TestClient                                                                                             
                                                                                                                                        
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))                                                    
from app.main import app                                                                                                              
                                                                                                                                        
client = TestClient(app)                                                                                                              
                                                                                                                                        
                                                                                                                                        
def test_mcp_tools_list():                                                                                                            
    """Verifies that tools/list returns all 4 registered HRIS tools with schemas."""                                                  
    response = client.post("/api/v1/mcp", json={                                                                                      
        "jsonrpc": "2.0",                                                                                                             
        "id": 1,                                                                                                                      
        "method": "tools/list",                                                                                                       
    })                                                                                                                                
    assert response.status_code == 200                                                                                                
    data = response.json()                                                                                                            
    assert data["jsonrpc"] == "2.0"                                                                                                   
    assert data["id"] == 1                                                                                                            
                                                                                                                                        
    tools = data["result"]["tools"]                                                                                                   
    tool_names = [t["name"] for t in tools]                                                                                           
    assert "lookup_employee_record" in tool_names                                                                                     
    assert "check_leave_balance" in tool_names                                                                                        
    assert "escalate_to_hrbp" in tool_names                                                                                           
    assert "search_policy_clauses" in tool_names                                                                                      
                                                                                                                                        
                                                                                                                                        
def test_mcp_tools_call_lookup():                                                                                                     
    """Verifies tools/call for lookup_employee_record."""                                                                             
    response = client.post("/api/v1/mcp", json={                                                                                      
        "jsonrpc": "2.0",                                                                                                             
        "id": 2,                                                                                                                      
        "method": "tools/call",                                                                                                       
        "params": {                                                                                                                   
            "name": "lookup_employee_record",                                                                                         
            "arguments": {"employee_id": "EMP-101"}                                                                                   
        }                                                                                                                             
    })                                                                                                                                
    assert response.status_code == 200                                                                                                
    data = response.json()                                                                                                            
    assert data["result"]["isError"] is False                                                                                         
    content_text = data["result"]["content"][0]["text"]                                                                               
    assert "EMP-101" in content_text                                                                                                  
    assert "India" in content_text                                                                                                    
                                                                                                                                        
                                                                                                                                        
def test_mcp_tools_call_unknown_tool():                                                                                               
    """Verifies that calling an unknown tool returns standard JSON-RPC -32601 error."""                                               
    response = client.post("/api/v1/mcp", json={                                                                                      
        "jsonrpc": "2.0",                                                                                                             
        "id": 3,                                                                                                                      
        "method": "tools/call",                                                                                                       
        "params": {"name": "hack_salary_database"}                                                                                    
    })                                                                                                                                
    assert response.status_code == 200                                                                                                
    data = response.json()                                                                                                            
    assert data["error"]["code"] == -32601                                                                                            
    assert "not found" in data["error"]["message"]                                                                                    
                                                                                                                                        
                                                                                                                                        
def test_mcp_invalid_jsonrpc_version():                                                                                               
    """Verifies that non-2.0 JSON-RPC requests return -32600 error."""                                                                
    response = client.post("/api/v1/mcp", json={                                                                                      
        "jsonrpc": "1.0",                                                                                                             
        "id": 4,                                                                                                                      
        "method": "tools/list",                                                                                                       
    })                                                                                                                                
    assert response.status_code == 200                                                                                                
    data = response.json()                                                                                                            
    assert data["error"]["code"] == -32600