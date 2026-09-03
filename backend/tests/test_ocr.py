import io
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import async_session_maker
from app.models import Prescription, MedicationItem, PrescriptionStatus
from app.schemas.ocr import (
    PrescriptionExtractionResult,
    ExtractedMedication,
    MedicationFrequency,
    TimingRelation,
)
from app.services.ocr_service import ocr_service


@pytest.mark.asyncio
async def test_ocr_successful_ingestion():
    """Verify prescription upload with high confidence returns 201 and persists to DB."""
    mock_result = PrescriptionExtractionResult(
        doctor_name="Dr. Sarah Mitchell",
        doctor_specialty="Cardiology",
        medications=[
            ExtractedMedication(
                brand_name="Lipitor",
                generic_molecule="Atorvastatin",
                dosage_form="Tablet",
                strength="20mg",
                frequency=MedicationFrequency.OD,
                timing_relation=TimingRelation.PC,
                duration_days=30,
                confidence_score=0.98,
            ),
            ExtractedMedication(
                brand_name="Glucophage",
                generic_molecule="Metformin",
                dosage_form="Tablet",
                strength="500mg",
                frequency=MedicationFrequency.BD,
                timing_relation=TimingRelation.PC,
                duration_days=60,
                confidence_score=0.95,
            ),
        ],
        unreadable_notes=None,
        requires_verification=False,
    )

    fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"

    with patch.object(
        ocr_service,
        "parse_prescription_document",
        new=AsyncMock(return_value=mock_result),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            files = {
                "file": ("prescription_scan.jpg", fake_image_bytes, "image/jpeg")
            }
            response = await client.post("/api/v1/prescriptions/upload", files=files)

            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "PARSED"
            assert data["extraction"]["doctor_name"] == "Dr. Sarah Mitchell"
            assert len(data["extraction"]["medications"]) == 2
            assert data["extraction"]["requires_verification"] is False

            # Verify in database
            import uuid as _uuid
            prescription_uuid = _uuid.UUID(data["prescription_id"])
            async with async_session_maker() as session:
                rx_stmt = select(Prescription).where(Prescription.id == prescription_uuid)
                rx_res = await session.execute(rx_stmt)
                rx = rx_res.scalar_one()
                assert rx.doctor_name == "Dr. Sarah Mitchell"
                assert rx.status == PrescriptionStatus.PARSED

                meds_stmt = select(MedicationItem).where(
                    MedicationItem.prescription_id == prescription_uuid
                )
                meds_res = await session.execute(meds_stmt)
                meds = meds_res.scalars().all()
                assert len(meds) == 2
                assert any(m.brand_name == "Lipitor" for m in meds)
                assert any(m.brand_name == "Glucophage" for m in meds)


@pytest.mark.asyncio
async def test_ocr_low_confidence_triggers_verification():
    """Verify that any medication item with confidence < 0.85 forces requires_verification = True."""
    mock_result = PrescriptionExtractionResult(
        doctor_name="Dr. Unknown",
        medications=[
            ExtractedMedication(
                brand_name="ScribbledMed",
                dosage_form="Tablet",
                strength="10mg",
                frequency=MedicationFrequency.OD,
                timing_relation=TimingRelation.PC,
                confidence_score=0.65,  # Low confidence
            )
        ],
        unreadable_notes="Unclear dosage instructions in margin",
    )
    # The Pydantic validator should have flagged requires_verification
    assert mock_result.requires_verification is True

    fake_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"

    with patch.object(
        ocr_service,
        "parse_prescription_document",
        new=AsyncMock(return_value=mock_result),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            files = {"file": ("rx_blurry.png", fake_png_bytes, "image/png")}
            response = await client.post("/api/v1/prescriptions/upload", files=files)

            assert response.status_code == 201
            data = response.json()
            assert data["extraction"]["requires_verification"] is True
            assert data["extraction"]["medications"][0]["confidence_score"] == 0.65


@pytest.mark.asyncio
async def test_ocr_unsupported_media_type():
    """Verify rejection of non-image/non-PDF files with HTTP 415."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("notes.txt", b"plain text notes", "text/plain")}
        response = await client.post("/api/v1/prescriptions/upload", files=files)
        assert response.status_code == 415
        assert "Unsupported media type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ocr_empty_file_rejected():
    """Verify rejection of 0-byte file with HTTP 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        response = await client.post("/api/v1/prescriptions/upload", files=files)
        assert response.status_code == 400
        assert "empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_ocr_service_parse_prescription_document_unit():
    """Unit test for OCRService verifying google-genai client call and JSON parsing."""
    sample_json = """{
        "doctor_name": "Dr. Emily Watson",
        "doctor_specialty": "Neurology",
        "medications": [
            {
                "brand_name": "Topamax",
                "generic_molecule": "Topiramate",
                "dosage_form": "Tablet",
                "strength": "25mg",
                "frequency": "BD",
                "timing_relation": "PC",
                "duration_days": 14,
                "confidence_score": 0.96
            }
        ],
        "unreadable_notes": null,
        "requires_verification": false
    }"""

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = sample_json
    mock_client.models.generate_content.return_value = mock_response

    service = ocr_service
    with patch.object(service, "_client", mock_client):
        result = await service.parse_prescription_document(
            file_bytes=b"sample_bytes",
            mime_type="image/jpeg",
        )

        assert isinstance(result, PrescriptionExtractionResult)
        assert result.doctor_name == "Dr. Emily Watson"
        assert len(result.medications) == 1
        assert result.medications[0].brand_name == "Topamax"
        assert result.medications[0].frequency == MedicationFrequency.BD
        assert result.requires_verification is False
        mock_client.models.generate_content.assert_called_once()
