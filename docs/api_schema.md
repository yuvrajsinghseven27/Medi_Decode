# MediDecode API Specification

This document details the REST API specifications and contracts for the MediDecode platform.

---

## 1. General Conventions

- **Base URL**: `http://localhost:8000` (Dev) / `https://api.medidecode.health` (Prod)
- **API Prefix**: `/api/v1`
- **Content Type**: `application/json` (unless handling multipart/form-data for file uploads)
- **Character Encoding**: UTF-8

---

## 2. Endpoints

### 2.1 System Health
#### `GET /healthz`
Returns system health, app version, and telemetry.

- **Response `200 OK`**:
```json
{
  "status": "ok",
  "app": "MediDecode API",
  "version": "0.1.0",
  "environment": "development"
}
```

---

### 2.2 Prescription Intake & Extraction
#### `POST /api/v1/prescriptions/upload`
Uploads a scanned prescription image (PNG, JPG, WebP) or document (PDF) for AI parsing.

- **Request**: `multipart/form-data`
  - `file`: Binary file upload
  - `patient_id`: string (optional)
- **Response `202 Accepted`**:
```json
{
  "job_id": "job_01h9x3p87v9",
  "status": "processing",
  "filename": "prescription_scan.jpg",
  "uploaded_at": "2026-09-03T05:30:00Z"
}
```

#### `GET /api/v1/prescriptions/{id}`
Fetches parsed and clinically normalized prescription details.

- **Response `200 OK`**:
```json
{
  "id": "rx_890123",
  "doctor_name": "Dr. Sarah Mitchell, MD",
  "clinic": "Metro Health Cardiology",
  "prescribed_date": "2026-08-28",
  "confidence_score": 0.98,
  "medications": [
    {
      "id": "med_1",
      "name": "Atorvastatin Calcium",
      "brand_name": "Lipitor",
      "dosage": "20mg",
      "form": "Tablet",
      "frequency": "Once daily at bedtime",
      "instructions": "Take with water before sleep. Avoid grapefruit juice.",
      "duration_days": 30,
      "refills_remaining": 3,
      "warnings": [
        "Avoid high-grapefruit intake",
        "Report unexpected muscle pain immediately"
      ]
    }
  ]
}
```

---

### 2.3 Safety & Interactions
#### `POST /api/v1/safety/check-interactions`
Analyzes a set of active medications against newly prescribed drugs or patient conditions.

- **Request `application/json`**:
```json
{
  "active_medication_ids": ["med_1"],
  "candidate_drug_name": "Clarithromycin 500mg"
}
```
- **Response `200 OK`**:
```json
{
  "severity": "high",
  "has_conflict": true,
  "interaction_details": [
    {
      "drug_a": "Atorvastatin",
      "drug_b": "Clarithromycin",
      "severity_level": "major",
      "mechanism": "Clarithromycin significantly increases atorvastatin plasma concentration by inhibiting CYP3A4.",
      "recommendation": "Hold atorvastatin during macrolide therapy or consider azithromycin as an alternative."
    }
  ]
}
```

---

### 2.4 Patient Schedules
#### `GET /api/v1/schedules/daily`
Returns aggregated daily schedule categorized by time-of-day slots.

- **Response `200 OK`**:
```json
{
  "date": "2026-09-03",
  "slots": {
    "morning": [
      {
        "medication_id": "med_2",
        "name": "Metformin HCl",
        "dosage": "500mg",
        "time": "08:00 AM",
        "taken": true
      }
    ],
    "bedtime": [
      {
        "medication_id": "med_1",
        "name": "Atorvastatin",
        "dosage": "20mg",
        "time": "10:00 PM",
        "taken": false
      }
    ]
  }
}
```
