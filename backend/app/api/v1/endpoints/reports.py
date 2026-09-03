import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

from app.schemas.report import ReportSummaryResponse
from app.services.report_service import report_service

logger = logging.getLogger(__name__)

router = APIRouter()


class TextReportRequest(BaseModel):
    text: str
    language: Optional[str] = "en"


@router.post(
    "/summarize",
    response_model=ReportSummaryResponse,
    summary="Upload and summarize diagnostic lab report with Gemini AI",
    description="Accepts a PDF, PNG, JPG medical report file or raw text, and generates a patient-friendly plain language summary.",
)
async def summarize_report(
    file: Optional[UploadFile] = File(None),
    raw_text: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
):
    file_bytes = None
    mime_type = None

    if file:
        file_bytes = await file.read()
        mime_type = file.content_type or "application/octet-stream"
        logger.info(f"Received report file '{file.filename}' ({len(file_bytes)} bytes, {mime_type})")

    if not file_bytes and not raw_text:
        # If neither provided, return default clinical sample summary
        return report_service._get_fallback_summary()

    try:
        summary = await report_service.summarize_report(
            file_bytes=file_bytes,
            mime_type=mime_type,
            raw_text=raw_text,
            language=language or "en",
        )
        return summary
    except Exception as e:
        logger.error(f"Failed to summarize report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report summarization failed: {str(e)}",
        )


@router.post(
    "/summarize-text",
    response_model=ReportSummaryResponse,
    summary="Summarize raw report text",
)
async def summarize_report_text(payload: TextReportRequest):
    return await report_service.summarize_report(
        raw_text=payload.text,
        language=payload.language or "en",
    )
