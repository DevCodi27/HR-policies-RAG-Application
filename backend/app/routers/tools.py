from fastapi import FastAPI, APIRouter, HTTPException, status
from app.schemas.employee import (
    EmployeeRecord,
    EmployeeLookupRequest,
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
router = APIRouter(prefix="/tools", tags=["HRIS Tools"])
@router.post(
    "/employee-record",
    response_model=EmployeeRecord,
    tags=["HRIS Tools"],
    summary="Look up employee grade band and entity",
)
def get_employee_record(payload: EmployeeLookupRequest) -> EmployeeRecord:
    """
    Controlled tool: Resolves employee grade band and entity from HRIS database.
    Enforces pre-execution scoping before answering entitlement questions.
    """
    try:
        return lookup_employee_record(payload.employee_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/leave-balance",
    response_model=LeaveBalanceResponse,
    tags=["HRIS Tools"],
    summary="Check accrued leave balance",
)
def get_leave_balance(payload: EmployeeLookupRequest) -> LeaveBalanceResponse:
    """
    Controlled tool: Retrieves approved accrued leave balance for an employee.
    """
    try:
        return check_leave_balance(payload.employee_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

@router.post(
    "/escalate-to-hrbp",
    response_model=EscalationResponse,
    tags=["HRIS Tools"],
    summary="Escalate policy query to human HRBP",
)
def create_escalation_ticket(payload: EscalationRequest) -> EscalationResponse:
    """
    Controlled tool: Dispatches an escalation ticket to an India or UK HRBP
    when discretionary human judgment is required.
    """
    try:
        return escalate_to_hrbp(
            employee_id=payload.employee_id,
            policy_topic=payload.policy_topic,
            reason=payload.reason,
            urgency=payload.urgency,
        )
    except EmployeeNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
