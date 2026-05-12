from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import enum


# ==================== Employee Schemas ====================

class EmployeeCreate(BaseModel):
    """Request body for employee registration."""
    name: str = Field(..., min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    salary: float = Field(..., gt=0)


class EmployeeUpdate(BaseModel):
    """Request body for updating employee."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = None
    salary: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    """Response body for employee."""
    id: UUID
    name: str
    department: Optional[str]
    email: str
    salary: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeListResponse(BaseModel):
    """Response body for employee list."""
    total: int
    employees: List[EmployeeResponse]


# ==================== Attendance Schemas ====================

class AttendanceCheckInRequest(BaseModel):
    """Request body for employee check-in."""
    employee_id: UUID
    face_image_base64: str = Field(..., description="Base64 encoded face image")
    location: Optional[str] = None
    device_id: Optional[str] = None


class AttendanceCheckInResponse(BaseModel):
    """Response body for check-in."""
    success: bool
    attendance_id: UUID
    face_match_score: Optional[float]
    verification_status: str  # "verified", "failed", "suspicious"
    message: str
    employee_name: str


class AttendanceRecordResponse(BaseModel):
    """Response body for attendance record."""
    id: UUID
    employee_id: UUID
    employee_name: str
    check_in_time: datetime
    check_out_time: Optional[datetime]
    face_match_score: Optional[float]
    verification_status: str
    location: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AttendanceListResponse(BaseModel):
    """Response body for attendance list."""
    total: int
    records: List[AttendanceRecordResponse]
    employee_id: Optional[UUID] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


# ==================== Risk Assessment Schemas ====================

class RiskLevel(str, enum.Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskScoreBreakdown(BaseModel):
    """Breakdown of risk score components."""
    face_risk: float
    attendance_risk: float
    payroll_risk: float
    anomaly_risk: float


class RiskAssessmentResponse(BaseModel):
    """Response body for risk assessment."""
    id: UUID
    employee_id: UUID
    employee_name: str
    assessment_date: datetime
    risk_score: float
    risk_level: RiskLevel
    breakdown: RiskScoreBreakdown
    last_attendance_days_ago: Optional[int]
    attendance_frequency_per_week: Optional[float]
    is_isolation_forest_outlier: bool
    anomaly_reasons: Optional[List[str]]
    
    class Config:
        from_attributes = True


class RiskAnalysisRequest(BaseModel):
    """Request body for manual risk analysis."""
    employee_id: UUID
    recalculate: bool = False


class RiskReportResponse(BaseModel):
    """Response body for risk report."""
    total_employees: int
    critical_risk_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    employees_at_risk: List[RiskAssessmentResponse]
    report_generated_at: datetime


# ==================== Payroll Schemas ====================

class PaymentStatus(str, enum.Enum):
    """Payment statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSED = "processed"
    FAILED = "failed"


class PayrollProcessRequest(BaseModel):
    """Request body for processing payroll."""
    employee_ids: List[UUID]
    month: str = Field(..., description="YYYY-MM format")
    skip_risk_check: bool = False  # For admin override


class PayrollRecordResponse(BaseModel):
    """Response body for payroll record."""
    id: UUID
    employee_id: UUID
    employee_name: str
    amount: float
    processing_date: datetime
    status: PaymentStatus
    approved_by_ai: bool
    risk_score_at_time: Optional[float]
    squad_transaction_id: Optional[str]
    squad_status: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PayrollBatchResponse(BaseModel):
    """Response body for payroll batch processing."""
    total: int
    approved: int
    rejected: int
    records: List[PayrollRecordResponse]
    batch_id: str


class PayrollRejectRequest(BaseModel):
    """Request body for rejecting payroll."""
    payroll_id: UUID
    reason: str


# ==================== Health Check Schemas ====================

class HealthCheckResponse(BaseModel):
    """Response body for health check."""
    status: str
    environment: str
    timestamp: datetime
    database_connected: bool
    ai_models_loaded: bool


# ==================== Error Schemas ====================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
