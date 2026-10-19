# Lesson 4: Your First FastAPI Application
# Run with: uvicorn practice_fastapi:app --reload


import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from fastapi import FastAPI, APIRouter, HTTPException, status
from app.schemas.employee import EmployeeLookupRequest, EmployeeRecord
from app.tools.employee_tool import lookup_employee_record, EmployeeNotFoundError

# 1. Initialize the FastAPI application instance
app = FastAPI(title="Policy Answer Desk - Practice API")

api_v1_router = APIRouter(prefix="/api/v1")

# === YOUR CODE GOES HERE ===

# Task 1: Create a GET endpoint at "/health"
# Hint:
# @app.get("/health")
# def health():
#     return {"status": "healthy"}


# Task 2: Create a POST endpoint at "/api/v1/tools/employee-record"
# Hint:
# @app.post("/api/v1/tools/employee-record")
# def get_employee(payload: EmployeeLookupRequest) -> EmployeeRecord:
#     try:
#         ...
#     except EmployeeNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e))
@app.get("/health", tags=["Health"])
def health_check() -> dict[str,str]:
    return{"status": "healthy", "service": "policy-answer-desk-backend"}

tool_router = APIRouter(prefix="/tools", tags=["HRIS Tools"])

@tool_router.post("/employee-record")
def get_employee(payload: EmployeeLookupRequest) -> EmployeeRecord:
    try:
        return lookup_employee_record(payload.employee_id)
    except EmployeeNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


api_v1_router.include_router(tool_router)

app.include_router(api_v1_router)
