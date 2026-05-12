# GhostShield AI - Quick Start (5 Min)

## 1. Install & Setup

```bash
# Virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with PostgreSQL credentials

# Create database
createdb ghostshield_db  # or use PostgreSQL GUI
```

## 2. Start Server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit: `http://localhost:8000/docs` (API docs)

## 3. Register Employee

```bash
curl -X POST http://localhost:8000/api/employees/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@gov.ng",
    "salary": 50000
  }'
```

**Response:** Employee ID returned

## 4. Employee Check-In (Face Verification)

```bash
# Convert image to base64
base64 -i face.jpg | tr -d '\n' > face_b64.txt

# Check-in with face
curl -X POST http://localhost:8000/api/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "<employee-id-from-step-3>",
    "face_image_base64": "<paste-base64-from-face_b64.txt>",
    "location": "Office A"
  }'
```

**Response:** Check-in verified or failed

## 5. Risk Assessment (AI)

```bash
curl -X POST http://localhost:8000/api/risk/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "<employee-id>"
  }'
```

**Response:** Risk score (0-100) + breakdown

## 6. Process Payroll (Dry-Run)

```bash
curl -X POST http://localhost:8000/api/payroll/process-dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "employee_ids": ["<employee-id>"],
    "month": "2024-01"
  }'
```

**Response:** Approved/rejected list

## 7. Deploy to Render

1. Push to GitHub
2. Login to Render.com
3. Create PostgreSQL → copy URL to `.env`
4. Create Web Service → connect GitHub
5. Add environment variables
6. Deploy!

---

## Architecture (High Level)

```
Request → FastAPI Route
        ↓
    Service Layer (business logic)
        ↓
    AI Modules (DeepFace, Isolation Forest, Risk Scoring)
        ↓
    SQLAlchemy Models
        ↓
    PostgreSQL
```

## Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI entry point |
| `app/routes/*.py` | API endpoints |
| `app/services/*.py` | Business logic |
| `app/ai/*.py` | Face verification, anomaly detection, risk scoring |
| `app/models/__init__.py` | Database tables |
| `app/integrations/squad_api.py` | Payment processing |

## What It Does

| Feature | How |
|---------|-----|
| **Employee Registration** | Stores employee + extracts face embedding |
| **Face Verification** | Compares live face to stored encoding (DeepFace) |
| **Risk Scoring** | 4 signals (face, attendance, payroll, anomaly) → 0-100 score |
| **Anomaly Detection** | Isolation Forest ML model detects outliers |
| **Payroll** | Auto-approves if risk < 70, sends payment via Squad |

## Core Endpoints

```
POST   /api/employees/register        # Register
POST   /api/attendance/check-in       # Face verification
POST   /api/risk/analyze              # Risk score
POST   /api/payroll/process           # Payroll + payment
GET    /api/risk/high-risk            # Report
GET    /health                        # Health check
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| Face detection fails | Check image quality (face >= 30% of image) |
| DeepFace import error | `pip install deepface --no-cache-dir` |
| Database connection error | Verify PostgreSQL is running + DATABASE_URL correct |
| Port 8000 in use | `lsof -i :8000 && kill -9 <PID>` |

## Next Steps

1. Register 5+ employees with real face images
2. Run check-ins to test face verification
3. Create test payroll & process
4. Deploy to Render
5. Load test & monitor performance

---

## Production Checklist

- [ ] JWT authentication
- [ ] Rate limiting
- [ ] CORS restrictions
- [ ] Error logging
- [ ] Health monitoring
- [ ] Database backups
- [ ] S3 for face images (not local)
- [ ] Secrets manager (not .env)

---

**You're ready! Start with Step 1 and build incrementally.**
