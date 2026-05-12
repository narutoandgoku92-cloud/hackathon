"""
Attendance Service
Handles employee check-ins and face verification.
"""

import uuid
import logging
from typing import Tuple, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Employee, AttendanceRecord, FaceEncoding
from app.ai.face_verification import FaceVerifier, base64_to_bytes, FaceVerificationError
import numpy as np

logger = logging.getLogger(__name__)


class AttendanceService:
    """Manages attendance check-ins and verification."""
    
    def __init__(self, db: Session):
        self.db = db
        self.face_verifier = FaceVerifier()
    
    def check_in_employee(
        self,
        employee_id: uuid.UUID,
        face_image_base64: str,
        location: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Tuple[bool, AttendanceRecord, Dict]:
        """
        Process employee check-in with face verification.
        
        Args:
            employee_id: UUID of employee
            face_image_base64: Base64 encoded face image
            location: Optional location string
            device_id: Optional device identifier
            
        Returns:
            (success: bool, attendance_record, metadata: dict)
            
        Flow:
        1. Get employee and stored face encoding
        2. Verify submitted face against stored encoding
        3. Create attendance record
        4. Return result
        
        Raises:
            ValueError: If employee not found
            FaceVerificationError: If face detection fails
        """
        # Get employee
        employee = self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
        
        if not employee:
            raise ValueError(f"Employee {employee_id} not found")
        
        # Get primary face encoding
        face_encoding = self.db.query(FaceEncoding).filter(
            FaceEncoding.employee_id == employee_id,
            FaceEncoding.is_primary == True
        ).first()
        
        if not face_encoding:
            raise ValueError(f"No face encoding found for employee {employee_id}")
        
        # Decode face image
        try:
            image_bytes = base64_to_bytes(face_image_base64)
        except Exception as e:
            raise ValueError(f"Invalid face image format: {str(e)}")
        
        # Verify face
        stored_embedding = np.frombuffer(face_encoding.encoding, dtype=np.float32)
        is_match, confidence = self.face_verifier.verify_face(stored_embedding, image_bytes)
        
        # Determine verification status
        if is_match:
            verification_status = AttendanceRecord.VerificationStatus.VERIFIED
            success = True
        else:
            verification_status = AttendanceRecord.VerificationStatus.SUSPICIOUS
            success = False
        
        # Create attendance record
        record = AttendanceRecord(
            id=uuid.uuid4(),
            employee_id=employee_id,
            check_in_time=datetime.utcnow(),
            face_match_score=confidence,
            verification_status=verification_status,
            location=location,
            device_id=device_id
        )
        
        self.db.add(record)
        self.db.commit()
        
        metadata = {
            "is_match": is_match,
            "confidence": float(confidence),
            "verification_status": verification_status.value,
            "employee_name": employee.name
        }
        
        logger.info(
            f"Check-in: {employee.name}, "
            f"match={is_match}, confidence={confidence:.3f}"
        )
        
        return success, record, metadata
    
    def get_employee_today_checkins(self, employee_id: uuid.UUID) -> int:
        """Get number of check-ins today."""
        from datetime import date
        
        today = date.today()
        count = self.db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.check_in_time >= datetime(today.year, today.month, today.day)
        ).count()
        
        return count
    
    def get_attendance_records(
        self,
        employee_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 100,
        days_back: int = 30
    ) -> Tuple[int, list]:
        """
        Get attendance records with optional filtering.
        
        Returns:
            (total_count, records)
        """
        from datetime import timedelta
        
        query = self.db.query(AttendanceRecord)
        
        if employee_id:
            query = query.filter(AttendanceRecord.employee_id == employee_id)
        
        # Filter by date range
        start_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(AttendanceRecord.check_in_time >= start_date)
        
        total = query.count()
        records = query.order_by(AttendanceRecord.check_in_time.desc()).offset(skip).limit(limit).all()
        
        return total, records
    
    def get_attendance_statistics(self, employee_id: uuid.UUID) -> Dict:
        """
        Get attendance statistics for risk assessment.
        
        Returns dict with keys:
        - total_records: Total attendance records
        - days_since_last: Days since last check-in
        - weekly_average: Average check-ins per week
        - monthly_average: Average check-ins per month
        - current_streak: Current consecutive working days
        """
        records = self.db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.verification_status == AttendanceRecord.VerificationStatus.VERIFIED
        ).order_by(AttendanceRecord.check_in_time.desc()).all()
        
        if not records:
            return {
                "total_records": 0,
                "days_since_last": 999,
                "weekly_average": 0.0,
                "monthly_average": 0.0,
                "current_streak": 0
            }
        
        # Last check-in
        last_checkin = records[0].check_in_time
        days_since_last = (datetime.utcnow() - last_checkin).days
        
        # Time range
        first_checkin = records[-1].check_in_time
        total_days = (last_checkin - first_checkin).days
        
        weekly_avg = 0.0
        monthly_avg = 0.0
        if total_days >= 7:
            weekly_avg = (len(records) / total_days) * 7
        if total_days >= 30:
            monthly_avg = (len(records) / total_days) * 30
        
        return {
            "total_records": len(records),
            "days_since_last": days_since_last,
            "weekly_average": weekly_avg,
            "monthly_average": monthly_avg,
            "current_streak": 1  # Simplified for MVP
        }
