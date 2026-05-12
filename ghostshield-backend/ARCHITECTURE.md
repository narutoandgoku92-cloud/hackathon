# GhostShield AI - Backend MVP Architecture

## Overview
GhostShield AI is a government workforce integrity platform that uses AI to detect fraud, ghost workers, and suspicious payroll activity. This is a **production-grade MVP** designed for rapid deployment on Render.

---

## 1. Folder Structure Philosophy

```
ghostshield-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Environment & settings
│   │   ├── database.py         # SQLAlchemy setup
│   │   └── security.py         # Auth helpers
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── employee.py
│   │   ├── attendance.py
│   │   ├── risk_assessment.py
│   │   └── payroll.py
│   ├── schemas/                # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── employee.py
│   │   ├── attendance.py
│   │   ├── risk.py
│   │   └── payroll.py
│   ├── routes/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── employees.py
│   │   ├── attendance.py
│   │   ├── risk.py
│   │   └── payroll.py
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── employee_service.py
│   │   ├── attendance_service.py
│   │   ├── risk_service.py
│   │   └── payroll_service.py
│   ├── ai/                     # AI/ML modules
│   │   ├── __init__.py
│   │   ├── face_verification.py
│   │   ├── anomaly_detector.py
│   │   └── risk_scorer.py
│   └── integrations/           # External services
│       ├── __init__.py
│       └── squad_api.py
├── migrations/                 # Alembic DB migrations
├── requirements.txt
├── .env.example
├── run_locally.sh
├── Procfile                    # Render deployment
└── README.md
```

### Why This Structure?

| Folder | Purpose | Why It Matters |
|--------|---------|----------------|
| `core/` | Centralized config, DB setup | Single source of truth for app initialization |
| `models/` | SQLAlchemy ORM models | Maps Python objects to DB tables |
| `schemas/` | Pydantic validators | Validates API requests/responses cleanly |
| `routes/` | API endpoints | Clear request handling |
| `services/` | Business logic | Separates routing from complex logic |
| `ai/` | AI/ML algorithms | Isolated, testable ML code |
| `integrations/` | External APIs | Easy to swap Squad for competitors |

---

## 2. Database Schema Design

### ER Diagram (Conceptual)

```
Employees ─┬─ Attendance
           ├─ FaceEncodings
           ├─ RiskAssessments
           └─ PayrollRecords
```

### Tables

**employees**
- `id` (UUID, PK)
- `name` (String, NOT NULL)
- `department` (String)
- `email` (String, UNIQUE)
- `salary` (Decimal, NOT NULL)
- `is_active` (Boolean, default=True)
- `created_at` (DateTime)
- `updated_at` (DateTime)

**face_encodings**
- `id` (UUID, PK)
- `employee_id` (UUID, FK → employees)
- `encoding` (BYTEA, stored face embedding)
- `image_path` (String, S3 path)
- `created_at` (DateTime)

**attendance_records**
- `id` (UUID, PK)
- `employee_id` (UUID, FK → employees)
- `check_in_time` (DateTime, NOT NULL)
- `check_out_time` (DateTime, nullable)
- `face_match_score` (Float, 0-1)
- `verification_status` (Enum: 'verified', 'failed', 'suspicious')
- `location` (String, nullable)

**risk_assessments**
- `id` (UUID, PK)
- `employee_id` (UUID, FK → employees)
- `assessment_date` (DateTime, NOT NULL)
- `risk_score` (Float, 0-100)
- `risk_level` (Enum: 'low', 'medium', 'high', 'critical')
- `anomalies_detected` (Array of strings)
- `last_attendance_days_ago` (Int)
- `payroll_processed_count` (Int)

**payroll_records**
- `id` (UUID, PK)
- `employee_id` (UUID, FK → employees)
- `amount` (Decimal, NOT NULL)
- `processing_date` (DateTime)
- `risk_score_at_time` (Float)
- `approved_by_ai` (Boolean)
- `squad_transaction_id` (String)
- `status` (Enum: 'pending', 'approved', 'rejected', 'processed')

---

## 3. Core Architecture Patterns

### API Request Flow
```
Request
  ↓
Route Handler (validates with Pydantic)
  ↓
Service Layer (business logic + AI calls)
  ↓
Models Layer (database queries)
  ↓
Response (serialized with Pydantic)
```

### Risk Detection Pipeline
```
Employee Check-In
  ↓ (Upload face image)
Face Verification (DeepFace)
  ↓ (Compare with stored encoding)
Anomaly Detection (Isolation Forest)
  ↓ (Check attendance/payroll patterns)
Risk Scoring (Weighted algorithm)
  ↓ (Return risk_score + risk_level)
Decision Engine
  ↓ (Auto-approve or flag for review)
```

### AI Decision Points
- **Check-In**: Face must match stored encoding (>0.6 confidence)
- **Payroll**: Risk score must be <70 to auto-approve
- **Detection**: Isolation Forest identifies outliers

---

## 4. Key Design Decisions

| Decision | Why | Tradeoff |
|----------|-----|----------|
| FastAPI (async) | Handles concurrent requests efficiently | Python only (not Go/Rust) |
| PostgreSQL | ACID guarantees for payroll data | Overkill for MVP, but production-ready |
| SQLAlchemy ORM | Type-safe queries | Slightly slower than raw SQL |
| Pydantic schemas | Automatic validation + OpenAPI docs | Some duplication with models |
| Isolation Forest | Unsupervised anomaly detection | No labeled data needed |
| DeepFace | Pre-trained face verification | Dependency on external model |
| Squad API | Real payment infrastructure | Requires merchant account |

---

## 5. AI Module Strategy

### Face Verification (DeepFace)
- Enrollment: Extract face embedding at registration
- Verification: Compare live check-in embedding to stored encoding
- Threshold: 0.6 cosine similarity (tunable)

### Anomaly Detection (Isolation Forest)
Features used:
- Days since last attendance
- Attendance frequency (check-ins per week)
- Total salary processed
- Payroll frequency anomalies

Output: Anomaly score (0-1), flagged as outlier if score > 0.7

### Risk Scoring
```
risk_score = (
    (face_mismatch_weight × face_risk) +
    (attendance_weight × attendance_risk) +
    (payroll_weight × payroll_risk) +
    (anomaly_weight × anomaly_score)
) / 4

risk_level = {
    0-30: 'low',
    31-60: 'medium',
    61-85: 'high',
    86-100: 'critical'
}
```

---

## 6. MVP Development Priority (1-Week Timeline)

**Day 1-2:** Database + Models + Schemas
- ✅ Set up PostgreSQL locally
- ✅ Create SQLAlchemy models
- ✅ Define Pydantic schemas

**Day 2-3:** Core Routes + Services
- ✅ Employee registration endpoint
- ✅ Employee service layer
- ✅ Attendance endpoint
- ✅ Basic face upload (file storage)

**Day 3-4:** AI Integration
- ✅ DeepFace face verification
- ✅ Basic risk scoring
- ✅ Anomaly detection (Isolation Forest)

**Day 4-5:** Payroll + Squad API
- ✅ Squad API integration
- ✅ Payroll processing endpoint
- ✅ Risk-based approval engine

**Day 5-6:** Testing + Refinement
- ✅ Unit tests for services
- ✅ Integration tests for endpoints
- ✅ End-to-end workflow testing

**Day 6-7:** Deployment + Polish
- ✅ Render deployment setup
- ✅ Environment configuration
- ✅ Documentation + API cleanup

---

## 7. Deployment on Render

### Environment Variables Required
```
DATABASE_URL=postgresql://user:pass@host/ghostshield_db
JWT_SECRET=your-secret-key
SQUAD_API_KEY=your-squad-api-key
SQUAD_PUBLIC_KEY=your-squad-public-key
ENVIRONMENT=production
```

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Render.yaml Setup
```yaml
services:
  - type: web
    name: ghostshield-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        scope: shared
```

---

## 8. Security Considerations

- [ ] All face images stored encrypted (use AWS S3 with server-side encryption)
- [ ] Payroll data logged (audit trail for compliance)
- [ ] Rate limiting on face verification (prevent brute force)
- [ ] JWT tokens with 24-hour expiry
- [ ] CORS restricted to frontend domain
- [ ] API keys never logged in production

---

## 9. MVP Success Metrics

- ✅ Register employee with face encoding
- ✅ Check-in with face verification
- ✅ Detect anomalies in attendance
- ✅ Flag high-risk employees before payroll
- ✅ Process payment via Squad API
- ✅ Return risk reports with reasons

---

## 10. Post-MVP Roadmap

1. **Face Recognition Accuracy**: Add liveness detection (prevent spoofing)
2. **Dashboard**: Real-time risk monitoring UI
3. **Webhooks**: Notify when employees flagged
4. **ML Improvements**: Collect data, retrain Isolation Forest
5. **Multi-location**: GPS verification for check-ins
6. **Biometric**: Fingerprint + face (redundancy)
7. **Report Generation**: Compliance-ready PDF exports

---

## Next Steps

1. Review the folder structure (already created)
2. Set up PostgreSQL locally
3. Install dependencies from `requirements.txt`
4. Create `.env` file from `.env.example`
5. Run `alembic upgrade head` to create tables
6. Start with employee registration endpoint
7. Test with curl/Postman
8. Integrate DeepFace for face verification
9. Deploy to Render

**Let's build production-grade code at hackathon speed.**
