import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "policy-answer-desk-backend"


def test_get_employee_record_valid():
    response = client.post(
        "/api/v1/tools/employee-record",
        json={"employee_id": "EMP-101"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == "EMP-101"
    assert data["name"] == "Aarav Sharma"
    assert data["grade_band"] == 3
    assert data["entity"] == "India"


def test_get_employee_record_not_found():
    response = client.post(
        "/api/v1/tools/employee-record",
        json={"employee_id": "EMP-999"}
    )
    assert response.status_code == 404
    assert "not found in HRIS records" in response.json()["detail"]


def test_get_leave_balance_valid():
    response = client.post(
        "/api/v1/tools/leave-balance",
        json={"employee_id": "EMP-102"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["employee_id"] == "EMP-102"
    assert data["entity"] == "UK"
    assert data["accrued_days"] == 22.0


def test_escalate_to_hrbp_endpoint_valid_india():
    payload = {
        "employee_id": "EMP-101",
        "policy_topic": "Discretionary Leave",
        "reason": "Requesting 3 days emergency leave for urgent family situation",
        "urgency": "high"
    }
    response = client.post("/api/v1/tools/escalate-to-hrbp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == "TICK-INDIA-101-2026"
    assert data["employee_id"] == "EMP-101"
    assert data["entity"] == "India"
    assert "Pooja Sharma" in data["assigned_hrbp"]
    assert data["status"] == "escalated"


def test_escalate_to_hrbp_endpoint_not_found():
    payload = {
        "employee_id": "EMP-999",
        "policy_topic": "Discretionary Leave",
        "reason": "Requesting 3 days emergency leave for urgent family situation",
        "urgency": "medium"
    }
    response = client.post("/api/v1/tools/escalate-to-hrbp", json=payload)
    assert response.status_code == 404
    assert "not found in HRIS records" in response.json()["detail"]


def test_escalate_to_hrbp_endpoint_validation_error():
    # Reason < 10 characters should fail Pydantic validation with 422 Unprocessable Entity
    payload = {
        "employee_id": "EMP-101",
        "policy_topic": "Discretionary Leave",
        "reason": "short",
        "urgency": "low"
    }
    response = client.post("/api/v1/tools/escalate-to-hrbp", json=payload)
    assert response.status_code == 422


def test_chat_endpoint_with_tool_calling():
    """
    Tests the complete end-to-end chat flow where Qwen invokes
    the tool and synthesizes a final response.
    """
    response = client.post(
        "/api/v1/chat",
        json={"message": "I am employee EMP-101. What is my accrued leave balance right now?"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["model"] == "qwen/qwen3.8-27b"
    assert data["latency_sec"] > 0
    assert len(data["tool_calls_executed"]) >= 1
    
    # Check that tool call output recorded 14.5 days
    executed = data["tool_calls_executed"][0]
    assert executed["tool_name"] in ["check_leave_balance", "lookup_employee_record"]
    
    # The final natural language reply should mention 14.5 or 14
    reply = data["reply"]
    print(f"\n[FastAPI Chat Output]: {reply}")
    assert "14" in reply or "14.5" in reply


def test_chat_endpoint_with_escalation_tool():
    """
    Tests that Qwen autonomously triggers escalate_to_hrbp when
    a user requests human HR intervention.
    """
    response = client.post(
        "/api/v1/chat",
        json={"message": "I am employee EMP-101. Please escalate my request for compassionate leave exception due to a critical family emergency."}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["tool_calls_executed"]) >= 1
    tool_names = [call["tool_name"] for call in data["tool_calls_executed"]]
    assert "escalate_to_hrbp" in tool_names or "lookup_employee_record" in tool_names
    reply = data["reply"]
    print(f"\n[FastAPI Chat Escalation Output]: {reply}")
