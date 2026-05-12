from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.core.config import settings

# Create database engine
# MVP Note: In production, add:
# - Connection pooling (NullPool for serverless)
# - Echo only in dev
# - Timeouts
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Verify connections are alive
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Session:
    """
    Dependency injection for database session.
    
    Usage in routes:
    @router.post("/employees")
    async def create_employee(schema: EmployeeCreate, db: Session = Depends(get_db)):
        ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions in services.
    
    Usage in services:
    with get_db_context() as db:
        employee = db.query(Employee).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    
    Call this once on app startup or use Alembic migrations.
    """
    from app.models import Base
    Base.metadata.create_all(bind=engine)


# Base class for all models
from sqlalchemy.orm import declarative_base

Base = declarative_base()
