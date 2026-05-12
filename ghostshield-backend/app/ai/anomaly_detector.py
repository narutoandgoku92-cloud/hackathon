"""
Anomaly Detection Module
Uses Isolation Forest to detect abnormal employee patterns.

Why Isolation Forest?
- Unsupervised (no labeled training data needed)
- Efficient with high-dimensional data
- Works well for fraud detection
- Easy to interpret scores

MVP: Basic features. Production: Add temporal patterns, seasonality.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnomalyDetectionError(Exception):
    """Custom exception for anomaly detection failures."""
    pass


class AnomalyDetector:
    """Detects abnormal employee behavior using Isolation Forest."""
    
    def __init__(self):
        # Isolation Forest hyperparameters
        # contamination: expected % of outliers (0.05 = 5%)
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        self.feature_names = [
            "days_since_last_attendance",
            "attendance_frequency_per_week",
            "total_salary_processed",
            "payroll_frequency_per_month"
        ]
        
    def extract_features(self, attendance_records: List[Dict]) -> Optional[np.ndarray]:
        """
        Extract features from employee attendance/payroll data.
        
        Args:
            attendance_records: List of attendance records with timestamps
            
        Returns:
            1D numpy array of features, or None if insufficient data
        """
        try:
            if not attendance_records:
                return None
            
            # Sort by date
            records = sorted(attendance_records, key=lambda x: x.get("check_in_time", datetime.min))
            
            # Feature 1: Days since last attendance
            now = datetime.utcnow()
            last_checkin = records[-1].get("check_in_time", datetime.min)
            days_since_last = (now - last_checkin).days if last_checkin else 999
            
            # Feature 2: Attendance frequency (check-ins per week)
            if len(records) > 1:
                date_range_days = (records[-1].get("check_in_time", datetime.min) - 
                                 records[0].get("check_in_time", datetime.min)).days
                if date_range_days > 0:
                    attendance_frequency = (len(records) / date_range_days) * 7
                else:
                    attendance_frequency = len(records)
            else:
                attendance_frequency = len(records)
            
            # Feature 3 & 4: Payroll data (placeholder for now)
            # In production: query payroll records from database
            total_salary_processed = 0.0  # Would come from PayrollRecord model
            payroll_frequency = 0.0
            
            features = np.array([
                days_since_last,
                attendance_frequency,
                total_salary_processed,
                payroll_frequency
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            raise AnomalyDetectionError(f"Feature extraction failed: {str(e)}")
    
    def detect_anomaly(
        self,
        features: np.ndarray,
        batch_features: Optional[np.ndarray] = None
    ) -> Tuple[bool, float]:
        """
        Detect if employee is anomalous.
        
        Args:
            features: 1D array of employee features
            batch_features: 2D array of all employee features for context (optional)
            
        Returns:
            (is_anomaly: bool, anomaly_score: float)
            
        MVP: Uses pre-trained model. Production: Retrain weekly.
        """
        try:
            # Reshape to 2D for sklearn
            features_2d = features.reshape(1, -1)
            
            # Predict: -1 = anomaly, 1 = normal
            prediction = self.model.predict(features_2d)[0]
            
            # Get anomaly score (lower = more anomalous, typically -5 to 0.5)
            # Normalize to 0-1 range
            anomaly_score_raw = self.model.score_samples(features_2d)[0]
            anomaly_score = self._normalize_anomaly_score(anomaly_score_raw)
            
            is_anomaly = prediction == -1
            
            logger.info(f"Anomaly detection: score={anomaly_score:.3f}, is_anomaly={is_anomaly}")
            
            return is_anomaly, anomaly_score
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            raise AnomalyDetectionError(f"Anomaly detection failed: {str(e)}")
    
    @staticmethod
    def _normalize_anomaly_score(raw_score: float) -> float:
        """
        Normalize Isolation Forest score to 0-1 range.
        
        Raw scores typically: [-5, 0.5]
        Normalized: [0, 1] where 1 = most anomalous
        """
        # Simple linear mapping
        # -5 → 0, 0.5 → 1
        normalized = max(0.0, min(1.0, (raw_score + 5) / 5.5))
        return normalized


class AnomalyExplainer:
    """Provides human-readable explanations for anomalies."""
    
    @staticmethod
    def explain_anomaly(
        features: Dict[str, float],
        feature_names: List[str],
        threshold: float = 0.7
    ) -> List[str]:
        """
        Generate explanations for why an employee is flagged.
        
        Args:
            features: Dict of feature values
            feature_names: List of feature names
            threshold: Threshold for flagging individual features
            
        Returns:
            List of human-readable reasons
        """
        reasons = []
        
        days_since = features.get("days_since_last_attendance", 0)
        if days_since > 30:
            reasons.append(f"No attendance in {int(days_since)} days")
        
        freq = features.get("attendance_frequency_per_week", 0)
        if freq < 1:
            reasons.append(f"Low attendance frequency: {freq:.1f} days/week")
        
        salary = features.get("total_salary_processed", 0)
        if salary == 0:
            reasons.append("No salary processed recently")
        
        return reasons if reasons else ["Pattern matches historical anomalies"]
