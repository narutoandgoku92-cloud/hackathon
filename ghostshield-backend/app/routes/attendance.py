"""
Attendance Routes
Handles employee check-ins and face verification.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.services.attendance_service import AttendanceService
from app.schemas import (
    AttendanceCheckInRequest, AttendanceCheckInResponse,
    AttendanceRecordResponse, AttendanceListResponse
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post("/check-in", response_model=AttendanceCheckInResponse)
async def check_in_employee(
    data: AttendanceCheckInRequest,
    db: Session = Depends(get_db)
):
    """
    Process employee check-in with face verification.
    
    Request:
    ```json
    {
        "employee_id": "550e8400-e29b-41d4-a716-446655440000",
        "face_image_base64": "<base64_encoded_face_image>",
        "location": "Office Building A, Floor 3",
        "device_id": "device-001"
    }
    ```
    
    Response (Success):
    ```json
    {
        "success": true,
        "attendance_id": "550e8400-e29b-41d4-a716-446655440001",
        "face_match_score": 0.95,
        "verification_status": "verified",
        "message": "Check-in successful",
        "employee_name": "John Doe"
    }
    ```
    
    Response (Failed):
    ```json
    {
        "success": false,
        "attendance_id": "550e8400-e29b-41d4-a716-446655440002",
        "face_match_score": 0.35,
        "verification_status": "suspicious",
        "message": "Face does not match stored encoding",
        "employee_name": "John Doe"
    }
    ```
    
    Flow:
    1. Receive face image (base64)
    2. Extract face embedding using DeepFace
    3. Compare to stored encoding
    4. Record attendance with confidence score
    5. Return verification status
    
    Risk Detection:
    - Score < 0.6 = Suspicious (possible identity fraud)
    - Logs for risk assessment
    """
    try:
        service = AttendanceService(db)
        success, record, metadata = service.check_in_employee(
            employee_id=data.employee_id,
            face_image_base64=data.face_image_base64,
            location=data.location,
            device_id=data.device_id
        )
        
        return AttendanceCheckInResponse(
            success=success,
            attendance_id=record.id,
            face_match_score=record.face_match_score,
            verification_status=record.verification_status.value,
            message="Check-in verified" if success else "Check-in failed - face mismatch",
            employee_name=metadata["employee_name"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/records/{employee_id}", response_model=AttendanceListResponse)
async def get_employee_attendance(
    employee_id: UUID,
    skip: int = 0,
    limit: int = 100,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get attendance records for an employee.
    
    Query Parameters:
    - skip: Pagination offset
    - limit: Max records to return
    - days_back: Only show records from last N days
    """
    service = AttendanceService(db)
    total, records = service.get_attendance_records(
        employee_id=employee_id,
        skip=skip,
        limit=limit,
        days_back=days_back
    )
    
    return AttendanceListResponse(
        total=total,
        records=records,
        employee_id=employee_id,
        date_from=(datetime.utcnow().timestamp() - days_back * 86400),
        date_to=datetime.utcnow().timestamp()
    )


@router.get("/records", response_model=AttendanceListResponse)
async def list_all_attendance(
    skip: int = 0,
    limit: int = 100,
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """Get all attendance records across all employees."""
    service = AttendanceService(db)
    total, records = service.get_attendance_records(
        skip=skip,
        limit=limit,
        days_back=days_back
    )
    
    return AttendanceListResponse(
        total=total,
        records=records,
        date_from=(datetime.utcnow().timestamp() - days_back * 86400),
        date_to=datetime.utcnow().timestamp()
    )
