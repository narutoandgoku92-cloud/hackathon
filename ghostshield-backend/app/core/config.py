import os
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    MVP Note: Keep this simple. Production apps add:
    - Separate dev/staging/prod configs
    - Secrets manager integration
    - Dynamic feature flags
    """
    
    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/ghostshield_db"
    
    # API
    API_TITLE: str = "GhostShield AI API"
    API_VERSION: str = "1.0.0"
    
    # Security
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    
    # AI/ML
    FACE_MATCH_THRESHOLD: float = 0.6  # Cosine similarity threshold
    ANOMALY_THRESHOLD: float = 0.7  # Isolation Forest outlier score
    RISK_SCORE_APPROVAL_THRESHOLD: int = 70  # Auto-approve if below this
    
    # Squad API Integration
    SQUAD_API_KEY: str = "your-squad-api-key"
    SQUAD_PUBLIC_KEY: str = "your-squad-public-key"
    SQUAD_API_BASE_URL: str = "https://api.squadco.com"
    SQUAD_WEBHOOK_SECRET: str = "your-squad-webhook-secret"
    
    # File Storage (MVP: Local filesystem, production: S3)
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Feature Flags
    ENABLE_FACE_VERIFICATION: bool = True
    ENABLE_ANOMALY_DETECTION: bool = True
    ENABLE_SQUAD_INTEGRATION: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Single instance used across app
settings = Settings()


def get_settings() -> Settings:
    """Dependency injection for settings."""
    return settings
