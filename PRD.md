# Product Requirements Document (PRD)

## Document Details
- **Project Name:** MediDecode
- **Product Phase:** Hackathon MVP (v1.0)
- **Status:** Approved / In Development
- **Target Audience:** Elderly patients, chronic illness patients, non-English speaking patients, caregivers, and community health workers.

---

## 1. Executive Summary & Problem Statement

### 1.1 The Problem
Medical prescriptions, post-operative discharge summaries, and dosage regimens are notoriously difficult for laypeople to interpret. Illegible physician handwriting, complex Latin dosage abbreviations (e.g., *BD, TDS, PRN, AC, PC*), and high-register clinical terminology create significant barriers to patient comprehension. 

Furthermore, patients routinely take prescribed medicines alongside incompatible everyday foods (e.g., consuming dairy products with tetracyclines or grapefruit with statins), leading to adverse reactions or negated therapeutic efficacy.

### 1.2 The Solution: MediDecode
**MediDecode** is an AI-powered healthcare assistant that bridges the gap between doctor handwriting and patient comprehension. By combining multimodal vision models with domain-validated drug safety layers, MediDecode:
1. Digits messy handwritten prescriptions into clean, structured digital tables.
2. Translates medical jargon into plain, 6th-grade-level instructions.
3. Translates care instructions into the patient’s preferred regional language.
4. Identifies potential food–drug and drink interactions using an automated clinical safety layer.
5. Surfaces interactive medication schedules and automated dose reminders.

---

## 2. Product Goals & Success Metrics (KPIs)

### 2.1 Strategic Goals
- Eliminate medication errors caused by misreading physician handwriting and medical jargon.
- Mitigate preventable food–drug interactions before consumption.
- Democratize healthcare literacy across linguistically diverse patient demographics.

### 2.2 Hackathon MVP Success Metrics (KPIs)
| Metric Category | Target KPI | Method of Measurement |
| :--- | :--- | :--- |
| **Extraction Accuracy** | $\ge 90\%$ entity accuracy | Benchmarked on a standardized test set of sample doctor slips |
| **Processing Latency** | $< 5.0$ seconds total turnaround | Image upload to rendered structured dashboard |
| **Safety Flag Precision** | $100\%$ flag rate for severe tier | Tested against curated interactions (e.g., Statin + Grapefruit) |
| **Vernacular Readability** | Flesch-Kincaid Grade 6 or lower | Text readability analysis of generated simplified instructions |

---

## 3. User Personas & User Journeys

### 3.1 Personas
1. **Ramesh (68, Hypertensive Patient):** Struggles to read small cursive handwriting on doctor slips. Needs a clear, visual morning/night dosage schedule and instructions in his native language (Hindi).
2. **Priya (32, Caregiver):** Manages multiple medications for her post-surgery mother. Needs a quick way to scan hospital discharge notes, check whether medications conflict with her mother's diet, and receive reminder alerts.

### 3.2 Key User Journey
```
[Capture / Upload Prescription] 
       │
       ▼
[Image Preprocessing & VLM Parsing] 
       │
       ▼
[Safety & Interaction Validation] 
       │
       ▼
[Language Simplification & Localization] 
       │
       ▼
[Interactive Dashboard View] 
       │
       ├── Adjust Reminders
       ├── Switch Language Toggle
       └── Export/Share PDF Schedule
```

---

## 4. System Scope & Feature Requirements

### 4.1 Feature 1: Prescription & Document Ingestion
- **Input Types:** Camera photo capture (`.jpg`, `.png`) and document upload (`.pdf`).
- **File Constraints:** Max upload size 10MB. Automatic client-side compression before API transfer.
- **Preprocessing:** Contrast auto-adjustment and cropping aids to maximize OCR quality.

### 4.2 Feature 2: Multimodal Entity Extraction
- **Entities Captured:**
  - `Brand Name` and `Generic Active Ingredient`
  - `Strength/Dosage` (e.g., 500mg, 5ml)
  - `Form Factor` (Tablet, Syrup, Inhaler, Capsule, Injection)
  - `Frequency` parsed from Latin clinical terms:
    - *OD* $\rightarrow$ Once Daily
    - *BD/BID* $
ightarrow$ Twice Daily (Every 12 hours)
    - *TDS/TID* $
ightarrow$ Three Times Daily (Every 8 hours)
    - *QDS/QID* $
ightarrow$ Four Times Daily (Every 6 hours)
    - *SOS / PRN* $
ightarrow$ As needed / In emergency
  - `Timing Relation to Meals` (*AC* = Before food, *PC* = After food).
  - `Duration` (e.g., "for 5 days", "ongoing").

### 4.3 Feature 3: Plain-Language Simplifier
- Summarizes complex diagnosis lines and discharge summaries into direct, clear sentences.
- Avoids medical jargon (e.g., replaces "Analgesic for cephalalgia" with "Pain reliever for headache").
- Emphasizes course completion (e.g., explicit warnings to finish antibiotic courses even if symptoms stop).

### 4.4 Feature 4: Regional Language Translation
- Dynamic toggle on the user dashboard.
- Supported initial languages: **English, Hindi, Bengali, Tamil, Telugu, Spanish**.
- Localizes drug instructions, warnings, and dosage times while preserving the original brand name in Latin script for pharmacy reference.

### 4.5 Feature 5: Food & Dietary Interaction Layer
- Cross-references extracted active ingredients against a dietary contraindication ruleset:
  - **High Calcium / Dairy:** Flags fluoroquinolones/tetracyclines.
  - **Grapefruit / Citrus:** Flags CYP3A4 inhibitors like statins and certain calcium channel blockers.
  - **Tyramine Foods (Aged cheese, cured meats):** Flags MAOIs.
  - **Alcohol:** Flags metronidazole, sedatives, and paracetamol overdose risks.
- Color-coded severity tiers:
  - 🔴 **Severe / Contraindicated:** Do not consume together under any circumstances.
  - 🟡 **Moderate / Warning:** Space out consumption by at least 2 hours.
  - 🟢 **Information / Best Practice:** Best taken with water on an empty stomach.

### 4.6 Feature 6: Medication Dashboard & Reminders
- Visual timetable segmented into: **Morning (8:00 AM), Afternoon (1:00 PM), Evening (8:00 PM), Bedtime (10:00 PM)**.
- Single-click action to set browser push notifications or trigger a simulated WhatsApp/SMS reminder payload.

---

## 5. Non-Functional & Regulatory Requirements

### 5.1 Safety & Medical Disclaimers (Strictly Required)
- **Persistent Global Disclaimer:**
  > *"MediDecode is an assistive educational tool powered by AI and does not provide clinical diagnosis or certified medical prescriptions. Always verify drug instructions with your prescribing physician or a licensed pharmacist."*
- **Low Confidence Guardrail:** If the AI model’s extraction confidence for any medication name or dosage falls below **85%**, the item must be flagged with a warning banner:
  > *"⚠️ Low confidence reading: Please verify this medication dosage directly from the original paper."*

### 5.2 Data Privacy & PHI Redaction
- Uploaded prescription images must not be used for public model training.
- Images are stored in volatile, encrypted storage and purged within 24 hours of session completion.
- Direct Patient Identifiers (Name, Phone number, Hospital Registration ID) are masked during processing.

### 5.3 Performance & Reliability
- 99.5% uptime during hackathon judging windows.
- Graceful degradation: If regional language translation fails, the UI falls back immediately to English with an inline notification.

---

## 6. Target Technical Architecture

```
[ Frontend: Next.js + Tailwind CSS ]
               │
          REST / JSON
               ▼
[ Backend API: FastAPI (Python 3.11) ]
       │                │
       ▼                ▼
[ Vision-LLM API ]   [ Safety Rule Engine ]
(Gemini 1.5 Pro)     (RxNorm / OpenFDA / Rules DB)
       │                │
       └───────┬────────┘
               ▼
   [ PostgreSQL / Supabase ]
   (Cached Prescriptions & Alert Logs)
```

---

## 7. Out of Scope for MVP (Future Roadmap)
1. Direct integration with electronic health record (EHR) systems via HL7/FHIR protocols.
2. In-app automated e-pharmacy ordering and prescription fulfillment.
3. Automated voice-agent telephone calls for dose reminders (planned for v2.0).
4. Multi-page clinical laboratory blood test interpretation.

---

## 8. Hackathon Submission & Demo Checklist
- [ ] Working image capture and upload on mobile and desktop web.
- [ ] Live demonstration of extracting 1 handwritten prescription with >= 2 medications.
- [ ] Real-time language toggle showing instant schedule translation.
- [ ] Triggering of at least one clear food-interaction alert (e.g., Atorvastatin + Grapefruit).
- [ ] Visible medical disclaimer across all application views.
