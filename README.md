# 🩺 MediDecode — AI-Powered Prescription & Food-Safety Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![AI-Powered](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/dhyeydadhaniya02-del/medicine)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/dhyeydadhaniya02-del/medicine)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/dhyeydadhaniya02-del/medicine)

> **MediDecode** transforms illegible handwritten prescriptions and complex medical discharge documents into crystal-clear, structured daily schedules, provides plain-language explanations in regional languages, and alerts patients to dangerous food–drug interactions.

---

## 🚀 Key Features

- 📸 **Multimodal Prescription OCR & Extraction:** Ingests camera snapshots and PDFs to accurately identify drug names, dosages, frequencies (OD, BD, TDS, PRN), and duration.
- 🥗 **Food–Drug Interaction Safety Layer:** Cross-references active pharmaceutical ingredients against common foods (dairy, grapefruit, alcohol, leafy greens) with severity grading (🔴 Severe, 🟡 Moderate, 🟢 Safe).
- 🗣️ **Plain-Language Summarizer:** Translates clinical jargon from hospital discharge summaries into simple, 6th-grade-level explanations.
- 🌐 **Multilingual Regional Localization:** Translates dosage schedules and instructions into regional languages (Hindi, Bengali, Tamil, Telugu, Spanish, etc.) while preserving brand names for reference.
- ⏰ **Interactive Schedule & Reminders:** Provides a time-segmented visual planner (Morning, Afternoon, Evening, Bedtime) with push notification simulation.
- 🛡️ **Medical Disclaimer & Confidence Guardrails:** Highlights ambiguous extractions (<85% confidence) and maintains compliance standards.

---

## 🏗️ Architecture & Tech Stack

```
[ Patient Client (Next.js / Tailwind CSS) ]
                     │
               REST APIs / JSON
                     ▼
       [ Backend Gateway (FastAPI) ]
         │                       │
         ▼                       ▼
 [ Vision-LLM Pipeline ]     [ Safety Interaction Engine ]
 (Gemini 1.5 Pro / GPT-4o)   (RxNorm / OpenFDA Rules DB)
         │                       │
         └───────────┬───────────┘
                     ▼
     [ Database & Cache (PostgreSQL / Supabase) ]
```

- **Frontend:** Next.js 14 (App Router), React, Tailwind CSS, Lucide Icons
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Uvicorn
- **AI / Vision:** Google Gemini 1.5 Pro (via Google Generative AI SDK) / OpenAI GPT-4o
- **Database & Auth:** Supabase / PostgreSQL
- **Notifications (Optional):** Twilio API (SMS/WhatsApp) / Web Push API

---

## 📂 Project Structure

```text
medidecode/
├── PRD.md                  # Comprehensive Product Requirements Document
├── README.md               # Project setup and documentation
├── backend/
│   ├── app/
│   │   ├── api/            # API route controllers (/parse, /interactions, /translate)
│   │   ├── core/           # Config and security settings
│   │   ├── services/       # Vision extraction, LLM parsing, safety checks
│   │   ├── models/         # Pydantic schemas & DB models
│   │   └── data/           # Food-drug interaction rule sets
│   ├── main.py             # FastAPI entrypoint
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
└── frontend/
    ├── public/             # Static assets and demo samples
    ├── src/
    │   ├── app/            # Next.js pages & dashboard
    │   ├── components/     # UI components (Upload, ScheduleCard, AlertBanner)
    │   └── lib/            # API clients and utilities
    ├── package.json
    └── tailwind.config.js
```

---

## ⚡ Quickstart Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Gemini API Key ([Google AI Studio](https://aistudio.google.com/)) or OpenAI API Key

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/medidecode.git
cd medidecode
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and insert your GEMINI_API_KEY
```

Run the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger docs will be live at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🔑 Environment Variables

Create a `.env` file in the `/backend` directory:

```env
# AI Model Credentials
GEMINI_API_KEY="your_google_gemini_api_key_here"

# Server Configuration
PORT=8000
HOST="0.0.0.0"
CORS_ORIGINS="http://localhost:3000"

# Optional: Database / Notification Services
DATABASE_URL="postgresql://user:password@localhost:5432/medidecode"
TWILIO_ACCOUNT_SID=""
TWILIO_AUTH_TOKEN=""
```

---

## 🚀 One-Click Deployment Links

You can deploy MediDecode directly to the cloud for free using any of these deployable links:

### 1. Render Blueprint (Full Stack Backend + DB + Frontend)
👉 **[Click to Deploy on Render](https://render.com/deploy?repo=https://github.com/dhyeydadhaniya02-del/medicine)**  
Automatically deploys the PostgreSQL database, FastAPI unified backend with Docker, and static frontend with zero manual configuration.

### 2. Vercel (Frontend Static SPA)
👉 **[Click to Deploy on Vercel](https://vercel.com/new/clone?repository-url=https://github.com/dhyeydadhaniya02-del/medicine)**  
Instantly builds and deploys the frontend dashboard with global CDN hosting.

### 3. Railway (Full Stack Template)
👉 **[Click to Deploy on Railway](https://railway.app/new/template?template=https://github.com/dhyeydadhaniya02-del/medicine)**  
One-click cloud provisioning with automatic health checks and database provisioning.

---

## 🧪 Sample API Response

`POST /api/v1/prescriptions/parse`

```json
{
  "status": "success",
  "data": {
    "prescription_id": "rx_98234",
    "medications": [
      {
        "brand_name": "Augmentin",
        "generic_name": "Amoxicillin and Clavulanate",
        "dosage": "625mg",
        "frequency": "BD",
        "timing": "after_food",
        "duration_days": 5,
        "daily_schedule": ["09:00 AM", "09:00 PM"]
      }
    ],
    "food_interactions": [
      {
        "drug": "Augmentin",
        "trigger": "Dairy Products",
        "severity": "moderate",
        "advice": "Take at the start of a meal; avoid heavy calcium supplements within 2 hours."
      }
    ],
    "simplified_summary": "Take this antibiotic twice a day right after breakfast and dinner for 5 days. Complete the entire course.",
    "confidence_score": 0.96
  }
}
```

---

## ⚖️ Medical & Ethical Disclaimer

> **IMPORTANT:** MediDecode is an assistive, educational software prototype designed for hackathon demonstration. It does **not** provide certified clinical diagnosis, treatment recommendations, or pharmacovigilance sign-offs. Always verify prescriptions and dosage instructions with a licensed healthcare practitioner or registered pharmacist.

---

## 👥 Team & Acknowledgments

Built with passion for accessible healthcare at **[Your Hackathon Name]**.
