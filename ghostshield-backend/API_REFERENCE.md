# GhostShield AI - API Reference

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://<your-service>.onrender.com`

## Authentication

MVP: No authentication required.
Production: Add JWT bearer tokens to all endpoints.

---

## Endpoints

### Health & Status

#### GET /health
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "environment": "development",
    "timestamp": "2024-01-15T10:30:00",
    "database_connected": true,
    "ai_models_loaded": true
}
```

---

### Employees

#### POST /api/employees/register
Register new employee.

**Request:**
```json
{
    "name": "John Doe",
    "email": "john@agency.gov.ng",
    "department": "Finance",
    "salary": 50000.00
}
```

**Optional:**
- `face_image`: Base64-encoded face image for enrollment

**Response (201):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "john@agency.gov.ng",
    "department": "Finance",
    "salary": 50000.00,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
}
```

---

#### GET /api/employees
List all employees.

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Max records (default: 100)
- `active_only`: Filter by active status (default: true)

**Response:**
```json
{
    "total": 150,
    "employees": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "John Doe",
            ...
        }
    ]
}
```

---

#### GET /api/employees/{employee_id}
Get single employee.

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    ...
}
```

---

#### PUT /api/employees/{employee_id}
Update employee.

**Request:**
```json
{
    "name": "Jane Doe",
    "salary": 55000.00
}
```

**Response:** Updated employee object

---

#### DELETE /api/employees/{employee_id}
Deactivate employee (soft delete).

**Response:** 204 No Content

---

### Attendance

#### POST /api/attendance/check-in
Check-in with face verification.

**Request:**
```json
{
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "face_image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "location": "Office Building A, Floor 3",
    "device_id": "device-001"
}
```

**Response:**
```json
{
    "success": true,
    "attendance_id": "550e8400-e29b-41d4-a716-446655440001",
    "face_match_score": 0.95,
    "verification_status": "verified",
    "message": "Check-in verified",
    "employee_name": "John Doe"
}
```

**Verification Status:**
- `verified` (0-1): Face matched, confidence score
- `suspicious` (0-1): Face did not match (possible fraud)
- `failed`: Face detection failed

---

#### GET /api/attendance/records
List all attendance records.

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Max records (default: 100)
- `days_back`: Only show last N days (default: 30)

**Response:**
```json
{
    "total": 1500,
    "records": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "employee_id": "550e8400-e29b-41d4-a716-446655440000",
            "employee_name": "John Doe",
            "check_in_time": "2024-01-15T09:00:00",
            "face_match_score": 0.95,
            "verification_status": "verified",
            "location": "Office A",
            "created_at": "2024-01-15T09:00:01"
        }
    ]
}
```

---

#### GET /api/attendance/records/{employee_id}
Get attendance for specific employee.

**Response:** Same as above, filtered by employee

---

### Risk Assessment

#### POST /api/risk/analyze
Analyze risk for single employee.

**Request:**
```json
{
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "recalculate": false
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "employee_name": "John Doe",
    "assessment_date": "2024-01-15T10:30:00",
    "risk_score": 52.5,
    "risk_level": "medium",
    "breakdown": {
        "face_risk": 10.0,
        "attendance_risk": 80.0,
        "payroll_risk": 50.0,
        "anomaly_risk": 70.0
    },
    "last_attendance_days_ago": 3,
    "attendance_frequency_per_week": 4.5,
    "is_isolation_forest_outlier": true,
    "anomaly_reasons": [
        "No attendance in 30 days",
        "Anomalous pattern detected by AI model"
    ]
}
```

**Risk Levels:**
- `low`: 0-30 (Safe)
- `medium`: 31-60 (Review recommended)
- `high`: 61-85 (Likely fraud)
- `critical`: 86-100 (Block immediately)

---

#### POST /api/risk/batch
Batch risk assessment on multiple employees.

**Query Parameters:**
- `employee_ids`: List of UUIDs (optional, defaults to all active)
- `skip_recent`: Skip employees assessed in last 24h (default: true)

**Response:**
```json
{
    "total_assessed": 150,
    "critical_risk": [
        {
            "employee_id": "550e8400-e29b-41d4-a716-446655440003",
            "name": "Jane Smith",
            "score": 92.5
        }
    ],
    "high_risk": [],
    "medium_risk": [],
    "low_risk": [],
    "errors": []
}
```

---

#### GET /api/risk/high-risk
Get all high-risk employees.

**Query Parameters:**
- `threshold`: Risk score threshold (default: 70)

**Response:**
```json
{
    "total_employees": 5,
    "critical_risk_count": 1,
    "high_risk_count": 3,
    "medium_risk_count": 1,
    "low_risk_count": 0,
    "employees_at_risk": [
        {
            "employee_id": "550e8400-e29b-41d4-a716-446655440003",
            "employee_name": "Jane Smith",
            "risk_score": 92.5,
            "risk_level": "critical",
            "reasons": ["No attendance in 60 days"]
        }
    ],
    "report_generated_at": "2024-01-15T10:30:00"
}
```

---

### Payroll

#### POST /api/payroll/process
Process payroll with AI approval.

**Request:**
```json
{
    "employee_ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "month": "2024-01",
    "skip_risk_check": false
}
```

**Response:**
```json
{
    "total": 2,
    "approved": 1,
    "rejected": 1,
    "batch_id": "batch-001",
    "records": [
        {
            "payroll_id": "550e8400-e29b-41d4-a716-446655440004",
            "employee_name": "John Doe",
            "amount": 50000.00,
            "status": "processed",
            "approved_by_ai": true,
            "risk_score": 35.0
        },
        {
            "payroll_id": "550e8400-e29b-41d4-a716-446655440005",
            "employee_name": "Jane Smith",
            "amount": 45000.00,
            "status": "rejected",
            "approved_by_ai": false,
            "risk_score": 85.0
        }
    ]
}
```

**Auto-Approval Logic:**
- risk_score < 70 → APPROVED
- risk_score >= 70 → REJECTED (requires manual review)

---

#### POST /api/payroll/process-dry-run
Test payroll processing (no payments sent).

**Request:** Same as `/process`

**Response:** Same as `/process`, but no Squad transfers created

---

#### GET /api/payroll/records/{payroll_id}
Get specific payroll record.

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "employee_name": "John Doe",
    "amount": 50000.00,
    "processing_date": "2024-01-15T10:30:00",
    "status": "processed",
    "approved_by_ai": true,
    "risk_score_at_time": 35.0,
    "squad_transaction_id": "TXN-123456",
    "squad_status": "success",
    "created_at": "2024-01-15T10:30:00"
}
```

---

#### GET /api/payroll/employee/{employee_id}
Get all payroll records for employee.

**Response:**
```json
{
    "total": 12,
    "employee_id": "550e8400-e29b-41d4-a716-446655440000",
    "employee_name": "John Doe",
    "records": [
        {
            "payroll_id": "...",
            "amount": 50000.00,
            "status": "processed",
            "processing_date": "2024-01-15T10:30:00",
            "risk_score": 35.0
        }
    ]
}
```

---

#### POST /api/payroll/reject/{payroll_id}
Manually reject payroll (admin override).

**Request:**
```json
{
    "reason": "Requires additional verification"
}
```

**Response:**
```json
{
    "success": true,
    "payroll_id": "550e8400-e29b-41d4-a716-446655440004",
    "reason": "Requires additional verification"
}
```

---

#### GET /api/payroll/summary/{month}
Get monthly payroll summary.

**Example:** `GET /api/payroll/summary/2024-01`

**Response:**
```json
{
    "month": "2024-01",
    "total_records": 150,
    "total_amount": 7500000.00,
    "approved_count": 148,
    "rejected_count": 2,
    "pending_count": 0,
    "average_risk_score": 38.5,
    "by_status": {
        "processed": 148,
        "rejected": 2,
        "pending": 0,
        "failed": 0
    }
}
```

---

## Error Responses

All errors follow standard HTTP status codes:

- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
    "error": "Employee not found",
    "detail": "No employee with ID 550e8400...",
    "timestamp": "2024-01-15T10:30:00"
}
```

---

## Rate Limiting (MVP: None)

Production should add rate limiting:
- 100 requests/minute per IP
- 1000 requests/minute per API key
- 10 check-ins per second per employee

---

## Pagination

All list endpoints support:
- `skip`: Start position (default: 0)
- `limit`: Max results (default: 100, max: 1000)

**Example:**
```
GET /api/employees?skip=50&limit=25
```

---

## Timestamps

All timestamps in ISO 8601 format (UTC):
```
2024-01-15T10:30:00.123456
```

---

## Data Types

| Type | Format | Example |
|------|--------|---------|
| UUID | String | `550e8400-e29b-41d4-a716-446655440000` |
| Timestamp | ISO 8601 | `2024-01-15T10:30:00` |
| Float | Number | `50000.00` |
| Enum | String | `"verified"`, `"medium"`, `"processed"` |
| Base64 | String | `iVBORw0KGgo...` |

---

## Testing

### Swagger UI
```
http://localhost:8000/docs
```

### ReDoc
```
http://localhost:8000/redoc
```

### OpenAPI JSON
```
http://localhost:8000/openapi.json
```

### Curl Examples

Register employee:
```bash
curl -X POST http://localhost:8000/api/employees/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@test.com","salary":50000}'
```

Check-in:
```bash
curl -X POST http://localhost:8000/api/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"...","face_image_base64":"..."}'
```

Analyze risk:
```bash
curl -X POST http://localhost:8000/api/risk/analyze \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"..."}'
```

Process payroll:
```bash
curl -X POST http://localhost:8000/api/payroll/process \
  -H "Content-Type: application/json" \
  -d '{"employee_ids":["..."],"month":"2024-01"}'
```

---

## Webhooks (Future)

Squad webhook for payment updates:
```
POST /api/webhooks/squad
X-Squad-Signature: <signature>

{
    "event": "transfer.completed",
    "transaction_id": "TXN-123456",
    "status": "success"
}
```

---

**Built for the GhostShield AI hackathon**
