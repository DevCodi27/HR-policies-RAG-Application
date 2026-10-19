import sys
import os
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.llm_client import call_llm
from app.tools.employee_tool import check_leave_balance

def test_live_qwen_completion():
    messages = [
        {"role": "system", "content": "You are a concise HR assistant."},
        {"role": "user", "content": "Reply with only the exact words: Policy Desk Active"}
    ]
    response = call_llm(messages=messages, model_name="qwen/qwen3.8-27b", max_tokens=20)
    
    assert response["content"] is not None
    assert "Policy Desk Active" in response["content"]
    assert response["latency_sec"] > 0
    assert response["prompt_tokens"] > 0
    assert response["completion_tokens"] > 0
    assert response["model"] == "qwen/qwen3.8-27b"
    print(f"\n[Verified Live Qwen Output]: {response['content']}")
    print(f"[Speed]: {response['latency_sec']}s | Tokens: {response['prompt_tokens']} in, {response['completion_tokens']} out")

def test_live_qwen_tool_calling():
    """
    Tests that Qwen correctly decides to invoke the check_leave_balance tool
    when an employee asks about their leave balance.
    """
    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_leave_balance",
                "description": "Retrieve the accrued leave balance and legal entity for an employee by their employee ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_id": {
                            "type": "string",
                            "description": "The employee ID to query (e.g. EMP-101)"
                        }
                    },
                    "required": ["employee_id"]
                }
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": "You are an HR policy assistant. When an employee asks for their leave balance, use the check_leave_balance tool."
        },
        {
            "role": "user",
            "content": "Hi, I am employee EMP-101. How many leave days do I currently have accrued?"
        }
    ]

    response = call_llm(messages=messages, tools=tools, model_name="qwen/qwen3.8-27b")

    tool_calls = response["tool_calls"]
    assert tool_calls is not None, "Model should have generated a tool call"
    assert len(tool_calls) == 1, "Expected exactly one tool call"
    
    call = tool_calls[0]
    assert call.function.name == "check_leave_balance"
    
    args = json.loads(call.function.arguments)
    assert args.get("employee_id") == "EMP-101"
    print(f"\n[Tool Called]: {call.function.name} with args: {args}")

    # Now execute the actual Python tool with the model's arguments!
    tool_result = check_leave_balance(**args)
    print(f"[Tool Execution Result]: {tool_result}")
    assert tool_result.employee_id == "EMP-101"
    assert tool_result.accrued_days == 14.5
    assert tool_result.entity == "India"
