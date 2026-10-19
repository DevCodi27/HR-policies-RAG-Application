"""
Module: employee_tool.py
Responsibility: Controlled read-only employee record lookup tool.
Enforces:
- Strict grade band (1-7) and entity resolution before policy retrieval.
- Never allows modification of records (read-only).
- Raises controlled exceptions when an employee is not found.
"""

from typing import Optional
from app.schemas.employee import (
    EmployeeRecord,
    EmployeeLookupRequest,
    LeaveBalanceResponse,
    EscalationResponse
)

# Synthetic database of employees representing India and UK entities across grades 1-7
SYNTHETIC_EMPLOYEES: dict[str, dict] = {
    "EMP-101": {
        "employee_id": "EMP-101",
        "name": "Aarav Sharma",
        "grade_band": 3,
        "entity": "India",
        "department": "Engineering",
        "tenure_years": 2.5,
        "accrued_leave_days": 14.5,
    },
    "EMP-102": {
        "employee_id": "EMP-102",
        "name": "Eleanor Vance",
        "grade_band": 6,
        "entity": "UK",
        "department": "Product Management",
        "tenure_years": 5.0,
        "accrued_leave_days": 22.0,
    },
    "EMP-103": {
        "employee_id": "EMP-103",
        "name": "Priya Nair",
        "grade_band": 1,
        "entity": "India",
        "department": "Operations",
        "tenure_years": 0.8,
        "accrued_leave_days": 8.0,
    },
    "EMP-104": {
        "employee_id": "EMP-104",
        "name": "Arthur Pendelton",
        "grade_band": 5,
        "entity": "UK",
        "department": "Finance",
        "tenure_years": 3.2,
        "accrued_leave_days": 18.0,
    },
    "EMP-105": {
        "employee_id": "EMP-105",
        "name": "Rohan Deshmukh",
        "grade_band": 4,
        "entity": "India",
        "department": "Human Resources",
        "tenure_years": 1.5,
        "accrued_leave_days": 12.0,
    },
}


class EmployeeNotFoundError(Exception):
    """Raised when an employee identifier is not found in the HRIS database."""
    pass


def lookup_employee_record(employee_id: str) -> EmployeeRecord:
    """
    Looks up an employee record by ID and returns a validated EmployeeRecord.

    Args:
        employee_id: The ID string to query (e.g. 'EMP-101').

    Returns:
        A validated, immutable EmployeeRecord instance.

    Raises:
        EmployeeNotFoundError: If the ID does not match any record.
        pydantic.ValidationError: If the record fails schema validation.
    """
    clean_id = employee_id.strip().upper()
    raw_data = SYNTHETIC_EMPLOYEES.get(clean_id)
    if not raw_data:
        raise EmployeeNotFoundError(f"Employee with ID '{clean_id}' was not found in HRIS records.")

    # Parse and validate through Pydantic model
    return EmployeeRecord(**raw_data)

def check_leave_balance(employee_id: str) -> LeaveBalanceResponse:
    """
    Retrieves accrued leave balance and entity for a verified employee.

    Args:
        employee_id: Unique employee identifier (e.g. 'EMP-101').

    Returns:
        Validated LeaveBalanceResponse.

    Raises:
        EmployeeNotFoundError: If the employee ID does not exist.
    """
    employee_record = lookup_employee_record(employee_id)
    return LeaveBalanceResponse(
        employee_id=employee_record.employee_id,
        entity=employee_record.entity,
        accrued_days=employee_record.accrued_leave_days,
        pending_request=0,
    )

def escalate_to_hrbp(
    employee_id: str,
    policy_topic: str,
    reason: str,
    urgency: str = "medium"
) -> EscalationResponse:
    """
    Controlled tool: Creates an escalation ticket to a human HR Business Partner.
    Enforces entity routing (assigning India HRBP vs UK HRBP).
    """
    # 1. Resolve the employee record to verify entity and identity
    employee = lookup_employee_record(employee_id)

    # 2. Entity-based HRBP Assignment
    if employee.entity == "India":
        hrbp_name = "Pooja Sharma (Lead HRBP - India)"
    else:
        hrbp_name = "James Davies (Senior HRBP - UK)"

    # 3. Generate a deterministic synthetic ticket reference
    clean_id = employee.employee_id.replace("EMP-", "")
    ticket_id = f"TICK-{employee.entity.upper()}-{clean_id}-2026"

    # 4. Return the validated Pydantic EscalationResponse
    return EscalationResponse(
        ticket_id=ticket_id,
        employee_id=employee.employee_id,
        entity=employee.entity,
        assigned_hrbp=hrbp_name,
        status="escalated",
        summary=f"Query regarding '{policy_topic}' escalated to {hrbp_name} [Urgency: {urgency.upper()}]. Reason: {reason}"
    )

