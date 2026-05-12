"""
Risk Service
Orchestrates risk assessment using AI modules.
"""

import uuid
import logging
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Employee, RiskAssessment, AttendanceRecord, PayrollRecord
from app.ai.risk_scorer import RiskScorer, RiskSignalGenerator, RiskLevel
from app.ai.anomaly_detector import AnomalyDetector, AnomalyExplainer
from app.services.attendance_service import AttendanceService
import json

logger = logging.getLogger(__name__)


class RiskService:
    """Orchestrates risk assessment and scoring."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scorer = RiskScorer()
        self.signal_generator = RiskSignalGenerator()
        self.anomaly_detector = AnomalyDetector()
        self.attendance_service = AttendanceService(db)
    
    def assess_employee_risk(
        self,
        employee_id: uuid.UUID,
        save_to_db: bool = True
    ) -> RiskAssessment:
        """
        Perform complete risk assessment for an employee.
        
        Args:
            employee_id: UUID of employee
            save_to_db: Whether to save assessment to database
            
        Returns:
            RiskAssessment model instance
            
        Assessment Process:
        1. Calculate face risk (0 if encoding exists)
        2. Calculate attendance risk (days since last check-in)
        3. Calculate payroll risk (unusual salary patterns)
        4. Calculate anomaly risk (Isolation Forest)
        5. Combine into risk score
        6. Save to database
        """
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        # Signal 1: Face Risk (binary: exists or not)
        from app.models import FaceEncoding
        face_encoding = self.db.query(FaceEncoding).filter(
            FaceEncoding.employee_id == employee_id
        ).first()
        face_risk = 0.0 if face_encoding else 50.0  # 50 if no face encoding
        
        # Signal 2: Attendance Risk
        attendance_stats = self.attendance_service.get_attendance_statistics(employee_id)
        days_since = attendance_stats.get("days_since_last", 999)
        attendance_risk = self.signal_generator.attendance_risk(days_since)
        
        # Signal 3: Payroll Risk
        last_payroll = self.db.query(PayrollRecord).filter(
            PayrollRecord.employee_id == employee_id
        ).order_by(PayrollRecord.processing_date.desc()).first()
        
        if last_payroll:
            days_since_payment = (datetime.utcnow() - last_payroll.processing_date).days
            payroll_risk = self.signal_generator.payroll_risk(
                salary_amount=last_payroll.amount,
                employee_salary=employee.salary,
                time_since_last_payment_days=days_since_payment
            )
        else:
            payroll_risk = 30.0  # Never been paid = medium risk
        
        # Signal 4: Anomaly Risk (Isolation Forest)
        attendance_records = self.db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id
        ).all()
        
        features = self.anomaly_detector.extract_features([{
            "check_in_time": r.check_in_time
        } for r in attendance_records])
        
        anomaly_risk = 0.0
        is_outlier = False
        if features is not None:
            is_outlier, anomaly_score = self.anomaly_detector.detect_anomaly(features)
            anomaly_risk = self.signal_generator.anomaly_risk(anomaly_score)
        
        # Combine signals
        risk_score, risk_level = self.scorer.compute_risk_score(
            face_risk=face_risk,
            attendance_risk=attendance_risk,
            payroll_risk=payroll_risk,
            anomaly_risk=anomaly_risk
        )
        
        # Generate human-readable reasons
        reasons = []
        if days_since > 30:
            reasons.append(f"No attendance in {days_since} days")
        if attendance_stats.get("weekly_average", 0) < 1:
            reasons.append("Very low attendance frequency")
        if is_outlier:
            reasons.append("Anomalous pattern detected by AI model")
        if not face_encoding:
            reasons.append("No face encoding on file")
        
        # Create assessment record
        assessment = RiskAssessment(
            id=uuid.uuid4(),
            employee_id=employee_id,
            assessment_date=datetime.utcnow(),
            risk_score=risk_score,
            risk_level=risk_level,
            face_risk=face_risk,
            attendance_risk=attendance_risk,
            payroll_risk=payroll_risk,
            anomaly_risk=anomaly_risk,
            last_attendance_days_ago=days_since,
            attendance_frequency_per_week=attendance_stats.get("weekly_average", 0),
            total_salary_processed=last_payroll.amount if last_payroll else 0,
            is_isolation_forest_outlier=is_outlier,
            anomaly_reasons=json.dumps(reasons)
        )
        
        if save_to_db:
            self.db.add(assessment)
            self.db.commit()
            logger.info(
                f"Risk assessment saved: {employee.name}, "
                f"risk_score={risk_score:.1f}, risk_level={risk_level.value}"
            )
        
        return assessment
    
    def batch_risk_assessment(
        self,
        employee_ids: Optional[List[uuid.UUID]] = None,
        skip_recent: bool = True
    ) -> Dict:
        """
        Run risk assessment on multiple employees.
        
        Args:
            employee_ids: List of employee IDs (None = all active employees)
            skip_recent: Skip employees assessed in last 24 hours
            
        Returns:
            Dict with summary stats
        """
        # Get employees
        query = self.db.query(Employee).filter(Employee.is_active == True)
        if employee_ids:
            query = query.filter(Employee.id.in_(employee_ids))
        
        employees = query.all()
        
        results = {
            "total_assessed": 0,
            "critical_risk": [],
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "errors": []
        }
        
        for employee in employees:
            try:
                # Skip if recently assessed
                if skip_recent:
                    recent = self.db.query(RiskAssessment).filter(
                        RiskAssessment.employee_id == employee.id,
                        RiskAssessment.assessment_date >= datetime.utcnow() - timedelta(hours=24)
                    ).first()
                    if recent:
                        continue
                
                assessment = self.assess_employee_risk(employee.id, save_to_db=True)
                results["total_assessed"] += 1
                
                # Categorize
                if assessment.risk_level == RiskLevel.CRITICAL:
                    results["critical_risk"].append({
                        "employee_id": str(employee.id),
                        "name": employee.name,
                        "score": assessment.risk_score
                    })
                elif assessment.risk_level == RiskLevel.HIGH:
                    results["high_risk"].append({
                        "employee_id": str(employee.id),
                        "name": employee.name,
                        "score": assessment.risk_score
                    })
                elif assessment.risk_level == RiskLevel.MEDIUM:
                    results["medium_risk"].append({
                        "employee_id": str(employee.id),
                        "name": employee.name,
                        "score": assessment.risk_score
                    })
                else:
                    results["low_risk"].append({
                        "employee_id": str(employee.id),
                        "name": employee.name,
                        "score": assessment.risk_score
                    })
            
            except Exception as e:
                logger.error(f"Risk assessment failed for {employee.id}: {str(e)}")
                results["errors"].append({
                    "employee_id": str(employee.id),
                    "name": employee.name,
                    "error": str(e)
                })
        
        logger.info(
            f"Batch assessment complete: {results['total_assessed']} processed, "
            f"critical={len(results['critical_risk'])}, "
            f"high={len(results['high_risk'])}"
        )
        
        return results
    
    def get_high_risk_employees(self, threshold: int = 70) -> List[Dict]:
        """Get employees with risk score above threshold."""
        # Get most recent assessment for each employee
        from sqlalchemy import func
        
        latest_assessments = self.db.query(
            RiskAssessment.employee_id,
            func.max(RiskAssessment.assessment_date).label('max_date')
        ).group_by(RiskAssessment.employee_id).subquery()
        
        high_risk = self.db.query(RiskAssessment).join(
            latest_assessments,
            (RiskAssessment.employee_id == latest_assessments.c.employee_id) &
            (RiskAssessment.assessment_date == latest_assessments.c.max_date)
        ).filter(
            RiskAssessment.risk_score >= threshold
        ).all()
        
        result = []
        for assessment in high_risk:
            employee = self.db.query(Employee).filter(
                Employee.id == assessment.employee_id
            ).first()
            
            result.append({
                "employee_id": str(assessment.employee_id),
                "name": employee.name,
                "department": employee.department,
                "risk_score": assessment.risk_score,
                "risk_level": assessment.risk_level.value,
                "reasons": json.loads(assessment.anomaly_reasons or "[]")
            })
        
        return result
