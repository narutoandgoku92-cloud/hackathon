"""
Risk Assessment Routes
Handles risk scoring and fraud detection.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.services.risk_service import RiskService
from app.schemas import (
    RiskAssessmentResponse, RiskAnalysisRequest, RiskReportResponse,
    RiskLevel
)

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.post("/analyze", response_model=RiskAssessmentResponse)
async def analyze_employee_risk(
    data: RiskAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Perform risk assessment for an employee.
    
    Request:
    ```json
    {
        "employee_id": "550e8400-e29b-41d4-a716-446655440000",
        "recalculate": false
    }
    ```
    
    Response:
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "employee_id": "550e8400-e29b-41d4-a716-446655440000",
        "employee_name": "John Doe",
        "assessment_date": "2024-01-15T10:30:00",
        "risk_score": 52.5,
        "risk_level": "medium",
        "breakdown": {
            "face_risk": 10.0,
            "attendance_risk": 80.0,
            "payroll_risk": 50.0,
            "anomaly_risk": 70.0
        },
        "last_attendance_days_ago": 3,
        "attendance_frequency_per_week": 4.5,
        "is_isolation_forest_outlier": true,
        "anomaly_reasons": [
            "Attendance frequency below normal",
            "Pattern matches historical anomalies"
        ]
    }
    ```
    
    Risk Levels:
    - low: 0-30 (safe to process)
    - medium: 31-60 (review recommended)
    - high: 61-85 (likely fraud)
    - critical: 86-100 (block immediately)
    
    Signals:
    1. Face Risk: Identity verification mismatches
    2. Attendance Risk: Inactivity (no check-ins for N days)
    3. Payroll Risk: Unusual salary patterns
    4. Anomaly Risk: ML model detects outlier behavior
    """
    try:
        service = RiskService(db)
        assessment = service.assess_employee_risk(
            employee_id=data.employee_id,
            save_to_db=True
        )
        
        import json
        return RiskAssessmentResponse(
            id=assessment.id,
            employee_id=assessment.employee_id,
            employee_name=assessment.employee.name,
            assessment_date=assessment.assessment_date,
            risk_score=assessment.risk_score,
            risk_level=RiskLevel(assessment.risk_level.value),
            breakdown={
                "face_risk": assessment.face_risk,
                "attendance_risk": assessment.attendance_risk,
                "payroll_risk": assessment.payroll_risk,
                "anomaly_risk": assessment.anomaly_risk
            },
            last_attendance_days_ago=assessment.last_attendance_days_ago,
            attendance_frequency_per_week=assessment.attendance_frequency_per_week,
            is_isolation_forest_outlier=assessment.is_isolation_forest_outlier,
            anomaly_reasons=json.loads(assessment.anomaly_reasons or "[]")
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/batch")
async def batch_risk_assessment(
    employee_ids: Optional[List[UUID]] = None,
    skip_recent: bool = True,
    db: Session = Depends(get_db)
):
    """
    Run risk assessment on multiple employees.
    
    Optional Parameters:
    - employee_ids: List of specific employee IDs (None = all active)
    - skip_recent: Skip employees assessed in last 24 hours
    
    Returns:
    ```json
    {
        "total_assessed": 150,
        "critical_risk": [
            {
                "employee_id": "...",
                "name": "Jane Smith",
                "score": 92.5
            }
        ],
        "high_risk": [],
        "medium_risk": [],
        "low_risk": [],
        "errors": []
    }
    ```
    """
    try:
        service = RiskService(db)
        results = service.batch_risk_assessment(employee_ids, skip_recent)
        return results
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/high-risk", response_model=RiskReportResponse)
async def get_high_risk_report(
    threshold: int = 70,
    db: Session = Depends(get_db)
):
    """
    Get report of all high-risk employees.
    
    Query Parameters:
    - threshold: Risk score threshold (default: 70)
    
    Returns all employees flagged as high-risk for review and action.
    """
    try:
        service = RiskService(db)
        high_risk_list = service.get_high_risk_employees(threshold)
        
        # Count by risk level
        critical_count = sum(1 for e in high_risk_list if e["risk_level"] == "critical")
        high_count = sum(1 for e in high_risk_list if e["risk_level"] == "high")
        medium_count = sum(1 for e in high_risk_list if e["risk_level"] == "medium")
        low_count = sum(1 for e in high_risk_list if e["risk_level"] == "low")
        
        # Convert to response format
        assessments = []
        for emp in high_risk_list:
            assessments.append(RiskAssessmentResponse(
                id=UUID(int=0),  # Placeholder
                employee_id=UUID(emp["employee_id"]),
                employee_name=emp["name"],
                assessment_date=datetime.utcnow(),
                risk_score=emp["risk_score"],
                risk_level=RiskLevel(emp["risk_level"]),
                breakdown={},  # Simplified
                last_attendance_days_ago=None,
                attendance_frequency_per_week=None,
                is_isolation_forest_outlier=False,
                anomaly_reasons=emp["reasons"]
            ))
        
        return RiskReportResponse(
            total_employees=len(high_risk_list),
            critical_risk_count=critical_count,
            high_risk_count=high_count,
            medium_risk_count=medium_count,
            low_risk_count=low_count,
            employees_at_risk=assessments,
            report_generated_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
