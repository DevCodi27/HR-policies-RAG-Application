import sys
import os
import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.employee import (
    EmployeeRecord,
    LeaveBalanceResponse,
    EscalationRequest,
    EscalationResponse,
)
from app.tools.employee_tool import (
    lookup_employee_record,
    check_leave_balance,
    escalate_to_hrbp,
    EmployeeNotFoundError,
)

def test_lookup_valid_employee_india():
    emp = lookup_employee_record("EMP-101")
    assert isinstance(emp, EmployeeRecord)
    assert emp.employee_id == "EMP-101"
    assert emp.name == "Aarav Sharma"
    assert emp.grade_band == 3
    assert emp.entity == "India"
    assert emp.tenure_years == 2.5
    assert emp.accrued_leave_days == 14.5

def test_lookup_case_insensitivity():
    emp = lookup_employee_record("  emp-102  ")
    assert emp.employee_id == "EMP-102"
    assert emp.entity == "UK"
    assert emp.grade_band == 6

def test_lookup_nonexistent_employee():
    with pytest.raises(EmployeeNotFoundError) as exc_info:
        lookup_employee_record("EMP-999")
    assert "not found in HRIS records" in str(exc_info.value)

def test_check_leave_balance_success():
    balance = check_leave_balance("EMP-101")
    assert isinstance(balance, LeaveBalanceResponse)
    assert balance.employee_id == "EMP-101"
    assert balance.entity == "India"
    assert balance.accrued_days == 14.5
    assert balance.pending_request == 0

def test_check_leave_balance_nonexistent():
    with pytest.raises(EmployeeNotFoundError):
        check_leave_balance("EMP-999")

def test_pydantic_validation_invalid_grade():
    # Grade band must be between 1 and 7
    with pytest.raises(ValidationError) as exc_info:
        EmployeeRecord(
            employee_id="EMP-999",
            name="Invalid Grade Employee",
            grade_band=8,  # Invalid: > 7
            entity="India",
            department="QA",
            tenure_years=1.0,
            accrued_leave_days=5.0
        )
    assert "Input should be less than or equal to 7" in str(exc_info.value)

def test_pydantic_validation_invalid_entity():
    # Entity must be India or UK
    with pytest.raises(ValidationError) as exc_info:
        EmployeeRecord(
            employee_id="EMP-999",
            name="Invalid Entity Employee",
            grade_band=3,
            entity="Germany",  # Invalid: not India or UK
            department="QA",
            tenure_years=1.0,
            accrued_leave_days=5.0
        )
    assert "Input should be 'India' or 'UK'" in str(exc_info.value)
 
 
def test_escalate_to_hrbp_india():
    res = escalate_to_hrbp(
        employee_id="EMP-101",
        policy_topic="Compassionate Leave Exception",
        reason="Family emergency requiring additional days beyond statutory limit",
        urgency="high"
    )
    assert isinstance(res, EscalationResponse)
    assert res.ticket_id == "TICK-INDIA-101-2026"
    assert res.employee_id == "EMP-101"
    assert res.entity == "India"
    assert "Pooja Sharma" in res.assigned_hrbp
    assert res.status == "escalated"
    assert "Compassionate Leave Exception" in res.summary
    assert "HIGH" in res.summary


def test_escalate_to_hrbp_uk():
    res = escalate_to_hrbp(
        employee_id="EMP-102",
        policy_topic="Parental Leave Policy Clarification",
        reason="Requesting advice on shared parental leave eligibility",
        urgency="medium"
    )
    assert isinstance(res, EscalationResponse)
    assert res.ticket_id == "TICK-UK-102-2026"
    assert res.employee_id == "EMP-102"
    assert res.entity == "UK"
    assert "James Davies" in res.assigned_hrbp
    assert res.status == "escalated"


def test_escalate_to_hrbp_nonexistent():
    with pytest.raises(EmployeeNotFoundError):
        escalate_to_hrbp(
            employee_id="EMP-999",
            policy_topic="Compensation Query",
            reason="Querying salary band discrepancy",
            urgency="low"
        )


def test_escalation_request_validation():
    # Reason must be at least 10 chars
    with pytest.raises(ValidationError) as exc_info:
        EscalationRequest(
            employee_id="EMP-101",
            policy_topic="Leave",
            reason="short",  # < 10 chars
            urgency="low"
        )
    assert "String should have at least 10 characters" in str(exc_info.value)

