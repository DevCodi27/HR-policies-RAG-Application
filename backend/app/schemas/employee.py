"""
Module: employee.py
Responsibility: Define strict Pydantic schemas for employee records and tool inputs.
Dependencies: pydantic
"""

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class EmployeeRecord(BaseModel):
    """
    Represents a verified employee record from the HRIS database.
    
    Business Rules enforced:
    - Grade band MUST be an integer between 1 and 7.
    - Entity MUST be either 'India' or 'UK'.
    - Tenure must be non-negative.
    """
    model_config = ConfigDict(frozen=True)  # Read-only / immutable record

    employee_id: str = Field(
        ...,
        pattern=r"^EMP-\d{3,4}$",
        description="Unique employee identifier (e.g. EMP-101)",
        examples=["EMP-101"]
    )
    name: str = Field(..., min_length=2, description="Full name of employee")
    grade_band: int = Field(
        ...,
        ge=1,
        le=7,
        description="Grade band from 1 (entry level) to 7 (executive)"
    )
    entity: Literal["India", "UK"] = Field(
        ...,
        description="Operating legal entity (India or UK)"
    )
    department: str = Field(..., description="Department or business unit")
    tenure_years: float = Field(
        default=0.0,
        ge=0.0,
        description="Completed years of service at the company"
    )
    accrued_leave_days: float = Field(
        default=0.0,
        ge=0.0,
        description="Current approved accrued leave balance"
    )


class EmployeeLookupRequest(BaseModel):
    """Schema for employee lookup tool arguments."""
    employee_id: str = Field(
        ...,
        description="The employee ID to look up (e.g. EMP-101)",
        examples=["EMP-101"]
    )

class LeaveBalanceResponse(BaseModel):
    employee_id: str = Field(
        ...,
        description="The employee ID to look up (e.g. EMP-101)",
        examples=["EMP-101"]
    )
    entity: Literal["India","UK"] = Field(
        ...,
        description="Operating legal entity (India or UK)"
    )
    accrued_days: float = Field(
        default=0,
        ge=0.0,
        description="Current approved accrued balance"
    )
    pending_request: int = Field(
        default=0,
        ge=0,
        description="Balance pending request"
    )

class EscalationRequest(BaseModel):
    """Schema for escalating a query to a human HR Business Partner."""
    employee_id: str = Field(
        ...,
        description="The employee ID requesting escalation (e.g. EMP-101)",
        examples=["EMP-101"]
    )
    policy_topic: str = Field(
        ...,
        description="The topic requiring human review (e.g. Compassionate Leave, Policy Exception, Grievance)"
    )
    reason: str = Field(
        ...,
        min_length=10,
        description="Detailed explanation of why human HR discretion is needed"
    )
    urgency: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Urgency level of the escalation"
    )
                                                                                                                                       
                                                                                                                                       
class EscalationResponse(BaseModel):                                                                                               
    """Verified response returned when a human HRBP ticket is created."""                                                          
    ticket_id: str                                                                                                                 
    employee_id: str                                                                                                               
    entity: Literal["India", "UK"]                                                                                                 
    assigned_hrbp: str                                                                                                             
    status: Literal["escalated", "pending_review"]                                                                                 
    summary: str 