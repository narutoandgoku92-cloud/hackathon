"""
Employee Routes
Handles employee registration and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.services.employee_service import EmployeeService
from app.schemas import (
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeListResponse
)

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.post("/register", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def register_employee(
    data: EmployeeCreate,
    face_image: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Register a new employee with optional face image.
    
    Request:
    ```json
    {
        "name": "John Doe",
        "email": "john@agency.gov.ng",
        "department": "Finance",
        "salary": 50000.00,
        "face_image": "<base64_encoded_image>"
    }
    ```
    
    Response:
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John Doe",
        "email": "john@agency.gov.ng",
        "department": "Finance",
        "salary": 50000.00,
        "is_active": true,
        "created_at": "2024-01-15T10:30:00"
    }
    ```
    """
    try:
        service = EmployeeService(db)
        employee = service.create_employee(data, face_image)
        return employee
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    """Get employee by ID."""
    service = EmployeeService(db)
    employee = service.get_employee(employee_id)
    
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    
    return employee


@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of employees."""
    service = EmployeeService(db)
    total, employees = service.list_employees(skip, limit, active_only)
    
    return EmployeeListResponse(
        total=total,
        employees=employees
    )


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: UUID,
    data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """Update employee information."""
    service = EmployeeService(db)
    employee = service.update_employee(employee_id, data)
    
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    
    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_employee(
    employee_id: UUID,
    db: Session = Depends(get_db)
):
    """Deactivate (soft delete) an employee."""
    service = EmployeeService(db)
    success = service.deactivate_employee(employee_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
