"""
Risk Scoring Engine
Combines multiple risk signals into a single risk score.

Why separate?
- Easy to adjust weights for different use cases
- Transparent scoring algorithm
- Can run A/B tests on different models
"""

from typing import Dict, List, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk classification levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskScorer:
    """Computes risk scores from multiple signals."""
    
    def __init__(self):
        """
        Initialize risk scorer with weights.
        
        These weights are tunable based on business requirements.
        MVP: Conservative weights (lean towards flagging).
        Production: Calibrate with historical fraud data.
        """
        self.weights = {
            "face_verification": 0.25,      # Identity mismatch is critical
            "attendance": 0.25,             # Inactive workers are primary target
            "payroll": 0.25,                # Abnormal salary patterns
            "anomaly_detection": 0.25       # ML-detected outliers
        }
        
        # Thresholds
        self.risk_level_thresholds = {
            RiskLevel.LOW: 30,
            RiskLevel.MEDIUM: 60,
            RiskLevel.HIGH: 85,
            RiskLevel.CRITICAL: 100
        }
    
    def compute_risk_score(
        self,
        face_risk: float,           # 0-100: Higher = mismatch
        attendance_risk: float,     # 0-100: Higher = inactive
        payroll_risk: float,        # 0-100: Higher = suspicious
        anomaly_risk: float,        # 0-100: Higher = outlier
    ) -> Tuple[float, RiskLevel]:
        """
        Compute weighted risk score.
        
        Args:
            face_risk: Risk from face verification mismatch
            attendance_risk: Risk from inactivity
            payroll_risk: Risk from payroll patterns
            anomaly_risk: Risk from Isolation Forest
            
        Returns:
            (risk_score: 0-100, risk_level: Enum)
            
        Example:
            score, level = scorer.compute_risk_score(
                face_risk=10,           # Low: good match
                attendance_risk=80,     # High: inactive
                payroll_risk=50,        # Medium
                anomaly_risk=70         # High: outlier
            )
            # Returns: (52.5, RiskLevel.MEDIUM)
        """
        # Ensure all values are 0-100
        face_risk = max(0, min(100, face_risk))
        attendance_risk = max(0, min(100, attendance_risk))
        payroll_risk = max(0, min(100, payroll_risk))
        anomaly_risk = max(0, min(100, anomaly_risk))
        
        # Weighted sum
        risk_score = (
            self.weights["face_verification"] * face_risk +
            self.weights["attendance"] * attendance_risk +
            self.weights["payroll"] * payroll_risk +
            self.weights["anomaly_detection"] * anomaly_risk
        )
        
        # Classify into risk level
        risk_level = self._classify_risk_level(risk_score)
        
        logger.info(
            f"Risk score computed: {risk_score:.1f} ({risk_level.value}) | "
            f"face={face_risk:.0f}, attendance={attendance_risk:.0f}, "
            f"payroll={payroll_risk:.0f}, anomaly={anomaly_risk:.0f}"
        )
        
        return risk_score, risk_level
    
    def _classify_risk_level(self, risk_score: float) -> RiskLevel:
        """Classify score into risk level."""
        if risk_score >= self.risk_level_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_level_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif risk_score >= self.risk_level_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


class RiskSignalGenerator:
    """Generates individual risk signals from raw data."""
    
    @staticmethod
    def face_verification_risk(
        face_match_score: float,
        threshold: float = 0.6
    ) -> float:
        """
        Generate face risk from match score.
        
        Args:
            face_match_score: 0-1 cosine similarity
            threshold: Minimum acceptable score
            
        Returns:
            0-100 risk score
        """
        if face_match_score is None:
            return 100.0  # Unknown = high risk
        
        if face_match_score >= threshold:
            return 0.0  # Perfect match = no risk
        else:
            # Scale: 0.6 threshold → 0 risk, 0.0 → 100 risk
            risk = (1 - face_match_score / threshold) * 100
            return min(100, risk)
    
    @staticmethod
    def attendance_risk(
        days_since_last_checkin: int,
        expected_checkins_per_week: int = 5
    ) -> float:
        """
        Generate attendance risk from inactivity.
        
        Args:
            days_since_last_checkin: Days since last attendance
            expected_checkins_per_week: Expected working days per week
            
        Returns:
            0-100 risk score
        """
        # Expected gap between check-ins (in days)
        expected_gap_days = 7 / expected_checkins_per_week
        
        # Risk increases with inactivity
        # 0 days → 0 risk
        # 30+ days → 100 risk
        if days_since_last_checkin <= 0:
            return 0.0
        elif days_since_last_checkin >= 30:
            return 100.0
        else:
            risk = (days_since_last_checkin / 30) * 100
            return risk
    
    @staticmethod
    def payroll_risk(
        salary_amount: float,
        employee_salary: float,
        time_since_last_payment_days: int
    ) -> float:
        """
        Generate payroll risk from suspicious patterns.
        
        Args:
            salary_amount: Amount being processed
            employee_salary: Employee's normal salary
            time_since_last_payment_days: Days since last payment
            
        Returns:
            0-100 risk score
        """
        risk = 0.0
        
        # Flag unusual amounts (>20% deviation from normal)
        if employee_salary > 0:
            deviation = abs(salary_amount - employee_salary) / employee_salary
            if deviation > 0.2:
                risk += 40
        
        # Flag infrequent payments (should be regular)
        if time_since_last_payment_days > 45:
            risk += 30
        
        # Flag very small amounts
        if salary_amount < 100:
            risk += 20
        
        return min(100, risk)
    
    @staticmethod
    def anomaly_risk(anomaly_score: float, threshold: float = 0.7) -> float:
        """
        Generate risk from anomaly detection score.
        
        Args:
            anomaly_score: 0-1 from Isolation Forest
            threshold: Score above which to flag
            
        Returns:
            0-100 risk score
        """
        if anomaly_score < threshold:
            return 0.0
        else:
            # Scale above threshold: threshold → 0, 1.0 → 100
            risk = ((anomaly_score - threshold) / (1 - threshold)) * 100
            return min(100, risk)
