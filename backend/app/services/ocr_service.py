import logging
from typing import Optional
from google import genai
from google.genai import types
from app.core.config import settings
from app.schemas.ocr import PrescriptionExtractionResult

logger = logging.getLogger(__name__)

CLINICAL_OCR_SYSTEM_PROMPT = """You are an expert clinical pharmacologist and prescription handwriting recognition specialist.
Analyze the provided medical prescription document (handwritten or printed doctor's note, hospital discharge summary, or pharmacy slip).

Extract the clinical information with 100% precision:
1. doctor_name: The prescribing physician's name, if present.
2. doctor_specialty: The clinician's medical specialty (e.g. Cardiology, Endocrinology, General Medicine).
3. medications: For each individual medication line:
   - brand_name: Commercial trade name (e.g. 'Lipitor', 'Augmentin', 'Eltroxin', 'Glycomet').
   - generic_molecule: Active pharmaceutical molecule (e.g. 'Atorvastatin', 'Amoxicillin-Clavulanate', 'Levothyroxine', 'Metformin').
   - dosage_form: Tablet, Capsule, Syrup, Inhaler, Injection, Drops, Ointment.
   - strength: Dosage amount with unit (e.g. '500mg', '20mg', '50mcg', '10ml').
   - frequency: Standard medical abbreviation:
       - OD: Once daily
       - BD: Twice daily
       - TID: Thrice daily
       - QID: Four times daily
       - SOS: As needed / Emergency
   - timing_relation:
       - AC: Ante Cibum (Before Food / empty stomach)
       - PC: Post Cibum (After Food)
       - WITH_FOOD: Concurrently with meals
   - duration_days: Prescribed course duration in days (integer).
   - confidence_score: Your certainty score from 0.0 to 1.0 reflecting handwriting clarity. If any letters are ambiguous or smudged, score below 0.85.
4. unreadable_notes: Flag any cursive writing, illegible shorthand, or warnings that cannot be reliably deciphered.
5. requires_verification: Set to true if any medication confidence is below 0.85, or if ambiguous notes exist.
"""


class OCRService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = "gemini-flash-latest"
        self._client: Optional[genai.Client] = None

    @property
    def current_api_key(self) -> str:
        return self.api_key or settings.GEMINI_API_KEY

    @property
    def client(self) -> genai.Client:
        if self._client is not None:
            return self._client
        key = self.current_api_key
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in backend/.env or via the web portal."
            )
        self._client = genai.Client(api_key=key)
        self._active_key = key
        return self._client

    async def parse_prescription_document(
        self,
        file_bytes: bytes,
        mime_type: str,
    ) -> PrescriptionExtractionResult:
        """Parses a scanned prescription image or PDF using Gemini Flash multimodal vision.

        Args:
            file_bytes: Binary buffer of the uploaded file.
            mime_type: MIME type of the document (e.g. 'image/jpeg', 'image/png', 'application/pdf').

        Returns:
            PrescriptionExtractionResult: Strictly typed Pydantic extraction model.
        """
        logger.info(
            f"Initiating clinical vision extraction with model '{self.model_name}' on {len(file_bytes)} bytes ({mime_type})"
        )

        # Enforce deterministic JSON output matching PrescriptionExtractionResult schema
        config = types.GenerateContentConfig(
            system_instruction=CLINICAL_OCR_SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature to prioritize factual transcription
            response_mime_type="application/json",
            response_schema=PrescriptionExtractionResult,
        )

        # Wrap file bytes as a multimodal Part
        file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        prompt_text = (
            "Analyze this medical prescription image or document. Extract all medications, dosage parameters, "
            "frequencies, food timing relations, and doctor details into the requested clinical JSON schema."
        )

        models_to_try = [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        seen_models = set()
        last_err = None

        for model in models_to_try:
            if model in seen_models:
                continue
            seen_models.add(model)
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[file_part, prompt_text],
                    config=config,
                )

                raw_json = response.text
                if not raw_json:
                    raise ValueError(f"Received empty response from Gemini vision model {model}.")

                result = PrescriptionExtractionResult.model_validate_json(raw_json)
                logger.info(
                    f"Successfully parsed prescription via {model}: {len(result.medications)} medications found, "
                    f"requires_verification={result.requires_verification}"
                )
                return result

            except Exception as e:
                last_err = e
                logger.warning(f"Inference with {model} failed: {e}. Trying fallback model...")

        logger.error(f"All Gemini prescription parsing models failed: {last_err}", exc_info=True)
        raise last_err or RuntimeError("All Gemini OCR models failed.")


# Global singleton instance
ocr_service = OCRService()
