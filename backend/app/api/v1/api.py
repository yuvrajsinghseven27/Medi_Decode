from fastapi import APIRouter
from app.api.v1.endpoints import prescriptions, safety, schedule, auth, settings, reports, bot, users

api_router = APIRouter()
api_router.include_router(settings.router, prefix="/settings", tags=["System Settings & Gemini AI"])
api_router.include_router(bot.router, prefix="/bot", tags=["MediBot Conversational AI"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Profiles"])
api_router.include_router(users.router, prefix="/users", tags=["Patients & Users"])
api_router.include_router(reports.router, prefix="/reports", tags=["Lab Reports & Summarization"])
api_router.include_router(prescriptions.router, prefix="/prescriptions", tags=["Prescriptions"])
api_router.include_router(safety.router, prefix="/safety", tags=["Safety & Dietary"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["Schedule & Depletion"])
