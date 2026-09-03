import os
import uuid
import logging
from typing import Optional
from uuid import UUID
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import (
    User,
    Prescription,
    MedicationItem,
    PrescriptionStatus,
)
from app.schemas.ocr import PrescriptionUploadResponse, PrescriptionExtractionResult
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
}

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def get_or_create_default_user(session: AsyncSession) -> User:
    """Ensures at least one default patient profile exists for uploads without explicit user_id."""
    stmt = select(User).limit(1)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user

    default_user = User(
        full_name="Primary Patient",
        phone="+919800000000",
        preferred_language="en",
        cultural_dietary_profile={
            "fasting_routines": [],
            "tea_dairy_intake": "Moderate",
            "dietary_type": "Omnivore",
        },
    )
    session.add(default_user)
    await session.flush()
    return default_user


@router.post(
    "/upload",
    response_model=PrescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse medical prescription",
    description="Accepts an image (JPEG, PNG, WEBP) or PDF scan of a prescription, runs multimodal Gemini vision parsing, and returns structured clinical data.",
)
async def upload_prescription(
    file: UploadFile = File(..., description="Prescription image or PDF document"),
    user_id: Optional[UUID] = Form(None, description="Optional target patient User UUID"),
    session: AsyncSession = Depends(get_db),
):
    # 1. Validate MIME format
    content_type = file.content_type or ""
    if content_type.lower() not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported media type '{content_type}'. "
                f"Allowed formats: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            ),
        )

    # 2. Read file buffer
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    # 3. Store file locally
    file_ext = Path(file.filename or "rx.jpg").suffix or ".jpg"
    saved_filename = f"rx_{uuid.uuid4().hex}{file_ext}"
    saved_path = UPLOAD_DIR / saved_filename
    try:
        with open(saved_path, "wb") as f:
            f.write(file_bytes)
        raw_image_url = f"/uploads/{saved_filename}"
    except Exception as e:
        logger.error(f"Error persisting file upload: {e}")
        raw_image_url = f"/uploads/{saved_filename}"

    # 4. Multimodal Vision OCR extraction
    try:
        extraction_result: PrescriptionExtractionResult = (
            await ocr_service.parse_prescription_document(
                file_bytes=file_bytes,
                mime_type=content_type,
            )
        )
    except Exception as e:
        logger.error(f"Vision OCR pipeline execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Clinical OCR processing failed: {str(e)}",
        )

    # 5. Determine Patient User
    if user_id:
        stmt = select(User).where(User.id == user_id)
        user_result = await session.execute(stmt)
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found.",
            )
    else:
        user = await get_or_create_default_user(session)

    # 6. Persist Prescription and MedicationItem rows
    prescription = Prescription(
        user_id=user.id,
        raw_image_url=raw_image_url,
        doctor_name=extraction_result.doctor_name,
        doctor_specialty=extraction_result.doctor_specialty,
        status=PrescriptionStatus.PARSED,
    )
    session.add(prescription)
    await session.flush()

    for med in extraction_result.medications:
        raw_line = f"{med.brand_name or ''} {med.strength} {med.frequency.value} {med.timing_relation.value}".strip()
        med_item = MedicationItem(
            prescription_id=prescription.id,
            raw_text=raw_line or med.brand_name or "Prescribed Item",
            brand_name=med.brand_name,
            generic_molecule=med.generic_molecule,
            form=med.dosage_form,
            strength=med.strength,
            frequency=med.frequency,
            timing_relation=med.timing_relation,
            duration_days=med.duration_days,
            is_active=True,
        )
        session.add(med_item)

    await session.commit()
    await session.refresh(prescription)

    return PrescriptionUploadResponse(
        prescription_id=prescription.id,
        user_id=user.id,
        status=prescription.status,
        raw_image_url=raw_image_url,
        extraction=extraction_result,
    )
