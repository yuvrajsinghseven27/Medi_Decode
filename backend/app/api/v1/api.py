from fastapi import APIRouter
from app.api.v1.endpoints import prescriptions

api_router = APIRouter()
api_router.include_router(prescriptions.router, prefix="/prescriptions", tags=["Prescriptions"])
