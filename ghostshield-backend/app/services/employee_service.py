"""
Employee Service
Handles employee registration and management.

Service Layer Pattern:
- Validates input
- Calls AI modules
- Updates database
- Returns serialized responses

Why separate from routes?
- Easier to test
- Reusable across multiple route handlers
- Clear separation of concerns
"""

import uuid
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Employee, FaceEncoding, AttendanceRecord
from app.schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeListResponse
from app.ai.face_verification import FaceVerifier, base64_to_bytes
from datetime import datetime

logger = logging.getLogger(__name__)


class EmployeeService:
    """Manages employee operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.face_verifier = FaceVerifier()
    
    def create_employee(
        self,
        employee_data: EmployeeCreate,
        face_image_base64: Optional[str] = None
    ) -> Employee:
        """
        Register a new employee with optional face encoding.
        
        Args:
            employee_data: EmployeeCreate schema
            face_image_base64: Base64 encoded face image
            
        Returns:
            Employee model instance
            
        Flow:
        1. Create employee record
        2. Extract and store face encoding (if provided)
        3. Return to user
        """
        # Check for duplicates
        existing = self.db.query(Employee).filter(
            Employee.email == employee_data.email
        ).first()
        
        if existing:
            raise ValueError(f"Employee with email {employee_data.email} already exists")
        
        # Create employee
        employee = Employee(
            id=uuid.uuid4(),
            name=employee_data.name,
            department=employee_data.department,
            email=employee_data.email,
            salary=employee_data.salary,
            is_active=True
        )
        
        self.db.add(employee)
        self.db.flush()  # Get ID without committing
        
        # Process face image if provided
        if face_image_base64:
            try:
                image_bytes = base64_to_bytes(face_image_base64)
                encoding = self.face_verifier.encode_face(image_bytes)
                
                # Store encoding
                face_enc = FaceEncoding(
                    id=uuid.uuid4(),
                    employee_id=employee.id,
                    encoding=encoding.tobytes(),  # Convert numpy array to bytes
                    is_primary=True
                )
                self.db.add(face_enc)
                logger.info(f"Face encoding stored for {employee.name}")
            
            except Exception as e:
                logger.warning(f"Face encoding failed for {employee.name}: {str(e)}")
                # Don't fail registration if face encoding fails
                # Employee can upload face later
        
        self.db.commit()
        logger.info(f"Employee registered: {employee.name} ({employee.id})")
        
        return employee
    
    def get_employee(self, employee_id: uuid.UUID) -> Optional[Employee]:
        """Get employee by ID."""
        return self.db.query(Employee).filter(
            Employee.id == employee_id
        ).first()
    
    def list_employees(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> Tuple[int, List[Employee]]:
        """
        List employees with pagination.
        
        Returns:
            (total_count, employee_list)
        """
        query = self.db.query(Employee)
        
        if active_only:
            query = query.filter(Employee.is_active == True)
        
        total = query.count()
        employees = query.offset(skip).limit(limit).all()
        
        return total, employees
    
    def update_employee(
        self,
        employee_id: uuid.UUID,
        employee_data: EmployeeUpdate
    ) -> Optional[Employee]:
        """Update employee information."""
        employee = self.get_employee(employee_id)
        
        if not employee:
            return None
        
        # Update fields if provided
        update_data = employee_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)
        
        employee.updated_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Employee updated: {employee_id}")
        
        return employee
    
    def get_employee_attendance_stats(self, employee_id: uuid.UUID) -> Dict:
        """
        Get attendance statistics for an employee.
        
        Returns stats useful for risk scoring.
        """
        employee = self.get_employee(employee_id)
        if not employee:
            return {}
        
        # Get attendance records
        records = self.db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id
        ).all()
        
        if not records:
            return {
                "total_checkins": 0,
                "days_since_last_checkin": 999,
                "average_weekly_checkins": 0,
                "last_checkin": None
            }
        
        # Calculate stats
        last_checkin = records[-1].check_in_time if records else None
        days_since = (datetime.utcnow() - last_checkin).days if last_checkin else 999
        
        # Get date range
        first_checkin = records[0].check_in_time
        date_range_days = (last_checkin - first_checkin).days
        
        avg_weekly = 0
        if date_range_days > 0:
            avg_weekly = (len(records) / date_range_days) * 7
        
        return {
            "total_checkins": len(records),
            "days_since_last_checkin": days_since,
            "average_weekly_checkins": avg_weekly,
            "last_checkin": last_checkin
        }
    
    def deactivate_employee(self, employee_id: uuid.UUID) -> bool:
        """Soft delete: mark employee as inactive."""
        employee = self.get_employee(employee_id)
        if not employee:
            return False
        
        employee.is_active = False
        employee.updated_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Employee deactivated: {employee_id}")
        
        return True
