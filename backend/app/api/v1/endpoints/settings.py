import re
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from google import genai

from app.core.config import settings
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter()


class GeminiKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=10, description="Google AI Studio Gemini API Key")


class GeminiStatusResponse(BaseModel):
    configured: bool
    preview: str
    model: str
    active_cascade: list[str]


@router.get("/gemini", response_model=GeminiStatusResponse, summary="Check Gemini API status")
async def get_gemini_status():
    """Returns whether a Gemini API key is configured and provides a masked preview."""
    active_key = ocr_service.current_api_key
    configured = bool(active_key and len(active_key) >= 15)
    preview = ""
    if configured:
        preview = f"{active_key[:6]}...{active_key[-4:]}"
    return GeminiStatusResponse(
        configured=configured,
        preview=preview,
        model=ocr_service.model_name,
        active_cascade=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"],
    )


@router.post("/gemini", summary="Validate and update Gemini API key")
async def save_gemini_key(payload: GeminiKeyRequest):
    """Validates the key against Google Gemini API and updates runtime settings and .env."""
    new_key = payload.api_key.strip()
    if not new_key:
        raise HTTPException(status_code=400, detail="API Key cannot be empty.")

    # 1. Test key connectivity with Google GenAI SDK
    test_client = genai.Client(api_key=new_key)
    success = False
    validation_error = None

    for test_model in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]:
        try:
            resp = test_client.models.generate_content(
                model=test_model,
                contents="Reply with: OK",
            )
            if resp and resp.text:
                success = True
                logger.info(f"Gemini API key validated successfully with model '{test_model}'.")
                break
        except Exception as e:
            validation_error = e

    if not success:
        logger.error(f"Gemini API key verification failed: {validation_error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate key with Gemini API: {str(validation_error)}",
        )

    # 2. Update memory & OCR service
    settings.GEMINI_API_KEY = new_key
    ocr_service.api_key = new_key
    ocr_service._client = None

    # 3. Persist to backend/.env
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        if "GEMINI_API_KEY=" in content:
            new_content = re.sub(r'GEMINI_API_KEY=.*', f'GEMINI_API_KEY="{new_key}"', content)
        else:
            new_content = content + f'\nGEMINI_API_KEY="{new_key}"\n'
        env_path.write_text(new_content, encoding="utf-8")
    else:
        env_path.write_text(f'GEMINI_API_KEY="{new_key}"\n', encoding="utf-8")

    return {
        "status": "success",
        "message": "Gemini API key validated and saved successfully!",
        "preview": f"{new_key[:6]}...{new_key[-4:]}",
    }
