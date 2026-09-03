from fastapi import APIRouter
from app.api.v1.endpoints import prescriptions, safety, schedule

api_router = APIRouter()
api_router.include_router(prescriptions.router, prefix="/prescriptions", tags=["Prescriptions"])
api_router.include_router(safety.router, prefix="/safety", tags=["Safety & Dietary"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["Schedule & Depletion"])
