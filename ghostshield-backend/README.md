# GhostShield AI - Backend MVP

An AI-powered government workforce integrity and payroll fraud detection platform.

## Quick Start (5 minutes)

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Git

### Local Development Setup

```bash
# 1. Clone and navigate
git clone <repo>
cd ghostshield-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# 5. Initialize database
alembic upgrade head
# Or for quick MVP: let SQLAlchemy create tables on startup

# 6. Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs` (Swagger UI)
- ReDoc: `http://localhost:8000/redoc`

---

## Architecture Overview

```
FastAPI Routes
    ↓
Service Layer (business logic)
    ↓
AI Modules (face-recognition, Isolation Forest, Risk Scoring)
    ↓
Models (SQLAlchemy ORM)
    ↓
PostgreSQL Database
```

### Key Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **Routes** | HTTP endpoints | FastAPI |
| **Services** | Business logic | Python classes |
| **AI Modules** | Face verification, anomaly detection | face-recognition, scikit-learn |
| **Models** | Data layer | SQLAlchemy ORM |
| **Schemas** | Validation & serialization | Pydantic |
| **Integrations** | External APIs | Squad API client |

---

## API Endpoints

### Employees
- `POST /api/employees/register` - Register new employee
- `GET /api/employees` - List employees
- `GET /api/employees/{id}` - Get employee
- `PUT /api/employees/{id}` - Update employee
- `DELETE /api/employees/{id}` - Deactivate employee

### Attendance
- `POST /api/attendance/check-in` - Check-in with face verification
- `GET /api/attendance/records` - List attendance records
- `GET /api/attendance/records/{employee_id}` - Get employee attendance

### Risk Assessment
- `POST /api/risk/analyze` - Analyze single employee risk
- `POST /api/risk/batch` - Batch risk assessment
- `GET /api/risk/high-risk` - Get high-risk employees report

### Payroll
- `POST /api/payroll/process` - Process payroll with AI approval
- `POST /api/payroll/process-dry-run` - Test payroll (no payments)
- `GET /api/payroll/summary/{month}` - Payroll summary
- `POST /api/payroll/reject/{id}` - Manually reject payment

### Health
- `GET /health` - Health check

---

## Core Workflows

### 1. Employee Registration

```
POST /api/employees/register
{
    "name": "John Doe",
    "email": "john@agency.gov.ng",
    "department": "Finance",
    "salary": 50000.00,
    "face_image": "<base64>"
}
↓
- Create employee record
- Extract & store face embedding (DeepFace)
- Return employee ID
```

### 2. Employee Check-In (Identity Verification)

```
POST /api/attendance/check-in
{
    "employee_id": "...",
    "face_image_base64": "<base64>",
    "location": "Office A"
}
↓
- Get stored face encoding
- Verify submitted face vs stored (DeepFace)
- Create attendance record
- Return verification status & confidence score
↓
Response:
{
    "success": true,
    "verification_status": "verified",
    "face_match_score": 0.95
}
```

### 3. Risk Assessment (AI Fraud Detection)

```
POST /api/risk/analyze
{
    "employee_id": "..."
}
↓
Calculate 4 risk signals:
  1. Face Risk (identity mismatches)
  2. Attendance Risk (days since last check-in)
  3. Payroll Risk (unusual salary patterns)
  4. Anomaly Risk (Isolation Forest ML model)
↓
Combine with weights:
risk_score = (0.25 × face_risk) +
             (0.25 × attendance_risk) +
             (0.25 × payroll_risk) +
             (0.25 × anomaly_risk)
↓
Classify:
  0-30: LOW
  31-60: MEDIUM
  61-85: HIGH
  86-100: CRITICAL
↓
Response:
{
    "risk_score": 52.5,
    "risk_level": "medium",
    "breakdown": {
        "face_risk": 0,
        "attendance_risk": 80,
        "payroll_risk": 50,
        "anomaly_risk": 70
    }
}
```

### 4. Payroll Processing (AI Approval + Squad Payment)

```
POST /api/payroll/process
{
    "employee_ids": ["...", "..."],
    "month": "2024-01",
    "skip_risk_check": false
}
↓
For each employee:
  1. Run risk assessment
  2. Decision:
     - if risk_score < 70: APPROVED
     - if risk_score >= 70: REJECTED
  3. If approved:
     - Create PayrollRecord
     - Send payment via Squad API
     - Update status to PROCESSED
↓
Response:
{
    "total": 2,
    "approved": 1,
    "rejected": 1,
    "records": [...]
}
```

---

## AI Integration Guide

### Face Verification (face-recognition)

**Library**: Uses dlib-based face recognition (no TensorFlow dependency)

**Enrollment (Registration)**
```python
from app.ai.face_verification import FaceVerifier

verifier = FaceVerifier()
face_bytes = ...  # From uploaded image

# Extract encoding (128-dimensional)
encoding = verifier.encode_face(face_bytes)
# Store in FaceEncoding model
```

**Verification (Check-In)**
```python
# Compare stored vs new
stored_embedding = ...  # From database
new_image_bytes = ...  # From check-in

is_match, similarity = verifier.verify_face(stored_embedding, new_image_bytes)
# similarity: 0-1 (higher = better match)
# Threshold: 0.6 (configurable)
```

### Anomaly Detection (Isolation Forest)

```python
from app.ai.anomaly_detector import AnomalyDetector

detector = AnomalyDetector()

# Extract features
features = detector.extract_features(attendance_records)
# Features: [days_since_last, frequency_per_week, salary_total, payment_frequency]

# Detect anomaly
is_anomaly, anomaly_score = detector.detect_anomaly(features)
# anomaly_score: 0-1 (higher = more anomalous)
```

### Risk Scoring

```python
from app.ai.risk_scorer import RiskScorer, RiskSignalGenerator

scorer = RiskScorer()
signal_gen = RiskSignalGenerator()

# Generate individual risk signals
face_risk = signal_gen.face_verification_risk(match_score=0.95)
attendance_risk = signal_gen.attendance_risk(days_since=5)
payroll_risk = signal_gen.payroll_risk(amount, salary, days_since_payment)
anomaly_risk = signal_gen.anomaly_risk(anomaly_score=0.8)

# Combine into score
score, level = scorer.compute_risk_score(face_risk, attendance_risk, payroll_risk, anomaly_risk)
# score: 0-100
# level: 'low', 'medium', 'high', 'critical'
```

---

## Squad API Integration

### Setup

1. Get credentials from [Squad Dashboard](https://dashboard.squadco.com)
2. Add to `.env`:
   ```
   SQUAD_API_KEY=your-key
   SQUAD_PUBLIC_KEY=your-public-key
   ```

### Payment Processing

```python
from app.integrations.squad_api import SquadPaymentProcessor

processor = SquadPaymentProcessor()

result = processor.create_transfer(
    recipient_bank_code="001",  # CBN
    recipient_account_number="1234567890",
    amount_in_cents=5000000,  # 50,000 NGN
    employee_name="John Doe",
    employee_id="emp-123"
)

# Returns:
# {
#     "success": True,
#     "transaction_id": "TXN-123456",
#     "status": "pending"
# }
```

### Transaction Verification

```python
status = processor.verify_transfer("TXN-123456")
# {
#     "transaction_id": "TXN-123456",
#     "status": "success",
#     "amount": 50000
# }
```

---

## Database Schema

### Core Tables

**employees**
- id, name, email, department, salary, is_active

**face_encodings**
- id, employee_id, encoding (128-dim vector), is_primary

**attendance_records**
- id, employee_id, check_in_time, face_match_score, verification_status

**risk_assessments**
- id, employee_id, assessment_date, risk_score, risk_level, anomaly_reasons

**payroll_records**
- id, employee_id, amount, status, approved_by_ai, squad_transaction_id

---

## Deployment to Render

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Create free account

### 2. Create PostgreSQL Database
- Dashboard → New → PostgreSQL
- Copy `DATABASE_URL`

### 3. Create Web Service
- Dashboard → New → Web Service
- Connect GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 4. Set Environment Variables
```
DATABASE_URL=<from PostgreSQL service>
SQUAD_API_KEY=<your-key>
SQUAD_PUBLIC_KEY=<your-public-key>
JWT_SECRET=<generate-random>
ENVIRONMENT=production
```

### 5. Deploy
- Push to GitHub
- Render auto-deploys

API will be at `https://<your-service>.onrender.com`

---

## Testing

### Manual Testing with curl

```bash
# Register employee
curl -X POST http://localhost:8000/api/employees/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@test.gov.ng",
    "salary": 50000
  }'

# Check-in (mock base64 image)
curl -X POST http://localhost:8000/api/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "face_image_base64": "iVBORw0KGgo..."
  }'

# Analyze risk
curl -X POST http://localhost:8000/api/risk/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "550e8400-e29b-41d4-a716-446655440000"
  }'

# Get high-risk report
curl http://localhost:8000/api/risk/high-risk
```

### Test with Postman
- Import API docs: `http://localhost:8000/openapi.json`
- Use Swagger UI: `http://localhost:8000/docs`

---

## MVP Development Timeline (1-2 Weeks)

**Phase 1: Setup (Day 1)**
- [ ] Database setup
- [ ] Models & migrations
- [ ] Environment configuration

**Phase 2: Core Features (Days 2-3)**
- [ ] Employee registration
- [ ] Face enrollment (DeepFace)
- [ ] Attendance check-in with face verification

**Phase 3: AI (Days 3-4)**
- [ ] Risk scoring engine
- [ ] Anomaly detection (Isolation Forest)
- [ ] High-risk employee reports

**Phase 4: Payroll (Days 4-5)**
- [ ] Payroll processing logic
- [ ] Risk-based approval workflow
- [ ] Squad API integration

**Phase 5: Polish (Days 5-6)**
- [ ] Testing
- [ ] Documentation
- [ ] Performance optimization

**Phase 6: Deployment (Day 6-7)**
- [ ] Deploy to Render
- [ ] Load testing
- [ ] Monitoring setup

---

## Security Notes

### MVP (Development)
- All CORS origins allowed
- Basic JWT implementation
- No rate limiting

### Production Checklist
- [ ] Restrict CORS to frontend domain
- [ ] Enable HTTPS only
- [ ] Add rate limiting (FastAPI-Limiter)
- [ ] Hash passwords (for future auth)
- [ ] Implement refresh tokens
- [ ] Add request signing (Squad webhooks)
- [ ] Encrypt face encodings at rest
- [ ] Audit logging for all payments
- [ ] VPC isolation (Render Private Services)
- [ ] Secrets rotation (Squad keys, JWT secret)

---

## Performance Optimization

### MVP
- Single-threaded, single-server
- In-memory Isolation Forest model
- No caching

### Production Improvements
- [ ] Redis caching for risk assessments
- [ ] Async face verification (queue jobs)
- [ ] Batch operations for ML predictions
- [ ] Database indexing on frequently queried fields
- [ ] Connection pooling (SQLAlchemy)
- [ ] Horizontal scaling (multiple Render services)
- [ ] CDN for face images (S3 + CloudFront)

---

## Troubleshooting

### face-recognition Installation Issues
```bash
# On Windows, you may need cmake and Visual C++ build tools
pip install cmake
# On macOS/Linux, install system dependencies first
# macOS: brew install dlib
# Ubuntu: sudo apt-get install build-essential cmake

# Then install face-recognition
pip install face-recognition
```

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U user -d ghostshield_db
```

### Port Already in Use
```bash
# Kill process using port 8000
lsof -i :8000
kill -9 <PID>
```

---

## Next Steps

1. **Setup local environment** - Follow Quick Start
2. **Create test employee** - Register via API
3. **Integrate facial data** - Upload test images
4. **Run risk assessment** - Test AI pipeline
5. **Process test payroll** - Verify Squad integration
6. **Deploy to Render** - Go live

---

## Support & Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [face-recognition GitHub](https://github.com/ageitgey/face_recognition)
- [Squad API Docs](https://documenter.getpostman.com/view/6278867/TVnqdgQ9)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)

---

## License

MIT License - see LICENSE file

---

**Built for the GhostShield AI hackathon**
*Production-grade architecture, hackathon speed.*
