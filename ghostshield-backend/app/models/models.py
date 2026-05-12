# Models package initialization
# Import all models here for Alembic
from app.models import Employee, FaceEncoding, AttendanceRecord, RiskAssessment, PayrollRecord

__all__ = [
    "Employee",
    "FaceEncoding",
    "AttendanceRecord",
    "RiskAssessment",
    "PayrollRecord"
]
