import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, ForeignKey, LargeBinary, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class Employee(Base):
    """
    Core employee record.
    
    Why separate models?
    - Employee: Static data
    - FaceEncoding: AI embeddings (large binary)
    - Attendance: Time series (grows over time)
    - RiskAssessment: ML outputs
    - PayrollRecord: Financial data (audit trail)
    """
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    department = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    salary = Column(Float, nullable=False)  # In cents to avoid float precision issues
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    face_encodings = relationship("FaceEncoding", back_populates="employee", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", back_populates="employee", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="employee", cascade="all, delete-orphan")
    payroll_records = relationship("PayrollRecord", back_populates="employee", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Employee {self.name} ({self.id})>"


class FaceEncoding(Base):
    """
    Stores face embeddings for identity verification.
    
    Why separate?
    - Large binary data (not queried often)
    - Multiple encodings per employee (backup/update)
    - Supports model versioning
    """
    __tablename__ = "face_encodings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    encoding = Column(LargeBinary, nullable=False)  # 128-dim vector from DeepFace
    image_path = Column(String(512), nullable=True)  # Path to original image
    model_version = Column(String(50), default="deepface-vggface2")
    is_primary = Column(Boolean, default=True)  # Which encoding to use for verification
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    employee = relationship("Employee", back_populates="face_encodings")


class AttendanceRecord(Base):
    """
    Tracks employee check-ins and check-outs.
    
    MVP: Start with simple check-in. Add check-out later.
    """
    __tablename__ = "attendance_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=False, index=True)
    check_out_time = Column(DateTime, nullable=True)
    face_match_score = Column(Float, nullable=True)  # 0-1, cosine similarity
    
    # Enum for verification status
    class VerificationStatus(str, enum.Enum):
        VERIFIED = "verified"
        FAILED = "failed"
        SUSPICIOUS = "suspicious"
    
    verification_status = Column(
        SQLEnum(VerificationStatus),
        default=VerificationStatus.VERIFIED,
        nullable=False
    )
    
    location = Column(String(255), nullable=True)
    device_id = Column(String(255), nullable=True)
    notes = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    employee = relationship("Employee", back_populates="attendance_records")


class RiskAssessment(Base):
    """
    Stores AI risk scores for each employee.
    
    Run this:
    - Daily batch job
    - Before payroll processing
    - On manual request
    """
    __tablename__ = "risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    assessment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Risk scoring (0-100)
    risk_score = Column(Float, nullable=False)
    
    # Risk levels
    class RiskLevel(str, enum.Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    
    # Breakdown scores (for transparency)
    face_risk = Column(Float, default=0.0)
    attendance_risk = Column(Float, default=0.0)
    payroll_risk = Column(Float, default=0.0)
    anomaly_risk = Column(Float, default=0.0)
    
    # Anomaly details
    last_attendance_days_ago = Column(Integer, nullable=True)
    attendance_frequency_per_week = Column(Float, nullable=True)
    total_salary_processed = Column(Float, nullable=True)
    is_isolation_forest_outlier = Column(Boolean, default=False)
    
    # Human-readable reason
    anomaly_reasons = Column(String(1024), nullable=True)  # JSON list of strings
    
    # Relationship
    employee = relationship("Employee", back_populates="risk_assessments")


class PayrollRecord(Base):
    """
    Tracks salary payments and Squad API integration.
    
    Why separate model?
    - Financial audit trail (immutable)
    - Squad transaction tracking
    - Risk snapshot at time of payment
    """
    __tablename__ = "payroll_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # In cents
    processing_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Risk snapshot
    risk_score_at_time = Column(Float, nullable=True)
    
    # Payment status
    class PaymentStatus(str, enum.Enum):
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"
        PROCESSED = "processed"
        FAILED = "failed"
    
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    approved_by_ai = Column(Boolean, default=False)
    
    # Squad API tracking
    squad_transaction_id = Column(String(255), unique=True, nullable=True, index=True)
    squad_reference = Column(String(255), nullable=True)
    squad_status = Column(String(50), nullable=True)  # From Squad API
    
    # Metadata
    notes = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    employee = relationship("Employee", back_populates="payroll_records")
