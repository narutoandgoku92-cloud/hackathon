"""
Payroll Routes
Handles salary processing with AI approval workflow.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional, Dict
from datetime import datetime
from app.core.database import get_db
from app.services.payroll_service import PayrollService
from app.schemas import (
    PayrollProcessRequest, PayrollRecordResponse, PayrollBatchResponse,
    PayrollRejectRequest, PaymentStatus
)

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


@router.post("/process", response_model=PayrollBatchResponse)
async def process_payroll(
    data: PayrollProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Process payroll for employees with AI approval.
    
    Request:
    ```json
    {
        "employee_ids": [
            "550e8400-e29b-41d4-a716-446655440000",
            "550e8400-e29b-41d4-a716-446655440001"
        ],
        "month": "2024-01",
        "skip_risk_check": false
    }
    ```
    
    Response:
    ```json
    {
        "total": 2,
        "approved": 1,
        "rejected": 1,
        "batch_id": "batch-001",
        "records": [
            {
                "payroll_id": "550e8400-e29b-41d4-a716-446655440002",
                "employee_name": "John Doe",
                "amount": 50000.00,
                "status": "processed",
                "approved_by_ai": true,
                "risk_score": 35.0
            },
            {
                "payroll_id": "550e8400-e29b-41d4-a716-446655440003",
                "employee_name": "Jane Smith",
                "amount": 45000.00,
                "status": "rejected",
                "approved_by_ai": false,
                "risk_score": 85.0
            }
        ]
    }
    ```
    
    Workflow:
    1. For each employee:
       - Run risk assessment (unless skip_risk_check=true)
       - If risk_score < 70: APPROVED
       - If risk_score >= 70: REJECTED (needs manual review)
    2. For approved employees:
       - Create payroll record
       - Send payment via Squad API
       - Update status to PROCESSED
    3. Return summary
    
    AI Decision Logic:
    - Risk score combines:
      * Face verification mismatches
      * Attendance inactivity
      * Unusual payroll patterns
      * ML anomaly detection (Isolation Forest)
    
    - Automatic Approval Threshold: 70
      * score < 70 = Safe, auto-approved
      * score >= 70 = Flagged, requires review
    
    Squad Integration:
    - Uses employee bank details (assumed to exist)
    - Creates transfer via Squad API
    - Tracks transaction ID for reconciliation
    """
    try:
        service = PayrollService(db)
        results = service.process_payroll(
            employee_ids=data.employee_ids,
            amount_per_employee=None,  # Use default salary
            skip_risk_check=data.skip_risk_check,
            send_payment=True
        )
        
        return PayrollBatchResponse(
            total=results["processed"],
            approved=results["approved"],
            rejected=results["rejected"],
            records=[PayrollRecordResponse(**r) for r in results["records"]],
            batch_id=results["batch_id"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/process-dry-run")
async def process_payroll_dry_run(
    data: PayrollProcessRequest,
    db: Session = Depends(get_db)
):
    """
    Dry-run payroll processing (no actual payments).
    
    Useful for:
    - Testing approval workflow
    - Previewing decisions before execution
    - Audit purposes
    """
    try:
        service = PayrollService(db)
        results = service.process_payroll(
            employee_ids=data.employee_ids,
            skip_risk_check=data.skip_risk_check,
            send_payment=False  # Don't actually send
        )
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/records/{payroll_id}", response_model=PayrollRecordResponse)
async def get_payroll_record(
    payroll_id: UUID,
    db: Session = Depends(get_db)
):
    """Get specific payroll record by ID."""
    from app.models import PayrollRecord
    
    record = db.query(PayrollRecord).filter(
        PayrollRecord.id == payroll_id
    ).first()
    
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll record not found")
    
    return record


@router.get("/employee/{employee_id}")
async def get_employee_payroll(
    employee_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all payroll records for an employee."""
    service = PayrollService(db)
    total, records = service.get_payroll_records(
        employee_id=employee_id,
        skip=skip,
        limit=limit
    )
    
    from app.models import Employee
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    return {
        "total": total,
        "employee_id": str(employee_id),
        "employee_name": employee.name if employee else "Unknown",
        "records": [
            {
                "payroll_id": str(r.id),
                "amount": r.amount,
                "status": r.status.value,
                "processing_date": r.processing_date,
                "risk_score": r.risk_score_at_time
            }
            for r in records
        ]
    }


@router.post("/reject/{payroll_id}")
async def reject_payroll(
    payroll_id: UUID,
    data: PayrollRejectRequest,
    db: Session = Depends(get_db)
):
    """Manually reject a payroll record (admin override)."""
    service = PayrollService(db)
    success = service.reject_payroll(payroll_id, data.reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reject payroll (already processed or not found)"
        )
    
    return {"success": True, "payroll_id": str(payroll_id), "reason": data.reason}


@router.get("/summary/{month}")
async def get_payroll_summary(
    month: str,  # Format: YYYY-MM
    db: Session = Depends(get_db)
):
    """
    Get payroll summary for a month.
    
    Example: GET /api/payroll/summary/2024-01
    
    Returns:
    ```json
    {
        "month": "2024-01",
        "total_records": 150,
        "total_amount": 7500000.00,
        "approved_count": 148,
        "rejected_count": 2,
        "pending_count": 0,
        "average_risk_score": 38.5,
        "by_status": {
            "processed": 148,
            "rejected": 2,
            "pending": 0
        }
    }
    ```
    """
    try:
        service = PayrollService(db)
        summary = service.get_payroll_summary(month)
        return summary
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
