import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class BotChatRequest(BaseModel):
    message: str = Field(..., description="User question to MediBot")
    history: Optional[List[ChatMessage]] = Field(default_factory=list)
    medications: Optional[List[Dict[str, Any]]] = None
    language: Optional[str] = "en"


class BotChatResponse(BaseModel):
    reply: str
    model_used: str
    suggested_followups: List[str] = Field(default_factory=list)


MEDIBOT_SYSTEM_PROMPT = """
You are MediBot, an empathetic, highly knowledgeable AI Clinical Assistant and Patient Safety Guardian developed for MediDecode.
Your purpose is to answer patient questions about their prescriptions, active medicines, dosages, food interactions, dangerous combinations, and medical lab reports in simple, crystal-clear, reassuring language.

Rules for your answers:
1. Be medically accurate, empathetic, and speak in plain everyday language (avoid medical jargon without explaining it).
2. When answering about active medications, emphasize correct timing (AC = before food, PC = after food) and critical food interactions (e.g. alcohol + metformin = lactic acidosis; grapefruit + atorvastatin = toxic muscle breakdown; morning chai/milk + thyronorm = reduced absorption).
3. If a patient asks about symptoms that could indicate an emergency (chest pain, severe breathlessness, fainting), instruct them calmly to seek immediate emergency care.
4. Keep answers structured, conversational, and helpful with bullet points when listing items.
5. Answer in the patient's requested language.
"""


@router.post(
    "/chat",
    response_model=BotChatResponse,
    summary="Chat with MediBot AI Assistant",
    description="Conversational endpoint powered by Google Gemini 2.5 Flash for answering questions about medications, food safety, and reports.",
)
async def chat_with_medibot(payload: BotChatRequest):
    active_key = ocr_service.current_api_key
    user_msg = payload.message.strip()

    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Contextual medications prompt
    meds_context = ""
    if payload.medications:
        items = []
        for m in payload.medications:
            name = m.get("name") or m.get("brand_name") or "Medicine"
            dosage = m.get("dosage") or m.get("strength") or ""
            timing = m.get("meal") or m.get("timing_relation") or ""
            items.append(f"- {name} {dosage} ({timing})")
        meds_context = "Current Active Medications in Regimen:\n" + "\n".join(items)
    else:
        meds_context = (
            "Current Active Medications in Regimen:\n"
            "- Thyronorm 50mcg (Morning empty stomach)\n"
            "- Metformin 500mg (With breakfast & dinner)\n"
            "- Atorvastatin 10mg (Bedtime with water)\n"
            "- Augmentin 625mg (Twice daily after meals x 5 days)\n"
            "- Crocin 500mg (Twice daily after food SOS)"
        )

    model_used = "gemini-2.5-flash"
    reply_text = ""

    if active_key:
        try:
            from google import genai
            from google.genai import types

            client = ocr_service.client

            # Build conversational prompt
            conv_lines = [MEDIBOT_SYSTEM_PROMPT, f"\n{meds_context}\n", f"Target Language: {payload.language or 'en'}\n"]
            if payload.history:
                conv_lines.append("Recent Conversation History:")
                for h in payload.history[-6:]:
                    prefix = "Patient: " if h.role == "user" else "MediBot: "
                    conv_lines.append(f"{prefix}{h.content}")

            conv_lines.append(f"\nPatient: {user_msg}\nMediBot:")
            full_prompt = "\n".join(conv_lines)

            for model_candidate in ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-2.5-flash"]:
                try:
                    resp = client.models.generate_content(
                        model=model_candidate,
                        contents=[full_prompt],
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                        ),
                    )
                    if resp and resp.text:
                        reply_text = resp.text.strip()
                        model_used = model_candidate
                        break
                except Exception as ex:
                    logger.warning(f"MediBot inference with {model_candidate} failed: {ex}")

        except Exception as e:
            logger.error(f"MediBot chat failed: {e}", exc_info=True)

    if not reply_text:
        # High quality clinical fallback response
        model_used = "clinical-pharmacology-rules (offline engine)"
        reply_text = get_clinical_fallback_response(user_msg)

    # Generate helpful smart follow-ups
    followups = [
        "What foods should I avoid with my medicines?",
        "Can I drink tea with Thyronorm in the morning?",
        "Explain my lab test results in simple words",
        "What should I do if I miss a scheduled dose?"
    ]

    return BotChatResponse(
        reply=reply_text,
        model_used=model_used,
        suggested_followups=followups,
    )


def get_clinical_fallback_response(query: str) -> str:
    q = query.lower()
    if "tea" in q or "chai" in q or "thyronorm" in q:
        return (
            "☕ **Morning Chai with Thyronorm:**\n"
            "You should **NEVER** drink milk tea, black tea, or coffee at the same time as taking Thyronorm (Levothyroxine). "
            "Tannins and calcium in tea chelate with the hormone, reducing drug absorption by up to 40%.\n\n"
            "💡 **Safe Rule:** Take your Thyronorm tablet with **1 glass of plain lukewarm water** first thing in the morning, "
            "then wait at least **45 to 60 minutes** before drinking your morning chai or having breakfast!"
        )
    elif "alcohol" in q:
        return (
            "🍷 **Alcohol Interaction Warning:**\n"
            "Alcohol is strictly dangerous with your current medications:\n"
            "1. **With Metformin:** Massively spikes the risk of life-threatening **Lactic Acidosis** (muscle pain, dizziness, severe weakness).\n"
            "2. **With Paracetamol (Crocin):** Triggers toxic metabolite NAPQI build-up, causing acute liver damage.\n\n"
            "💡 **Safe Swap:** Enjoy fresh coconut water, spiced buttermilk (chaas), or fresh lime soda instead."
        )
    elif "food" in q or "avoid" in q or "eat" in q:
        return (
            "🚫 **Foods to Avoid with Your Regimen:**\n"
            "1. **Grapefruit & Pomelo:** Avoid with **Atorvastatin** (stops liver breakdown, risking severe muscle breakdown / rhabdomyolysis).\n"
            "2. **Alcohol:** Strictly avoid with **Metformin** (lactic acidosis risk) and **Crocin** (liver toxicity).\n"
            "3. **Chai & Milk (within 1 hr):** Do not take with **Thyronorm** (blocks hormone uptake).\n"
            "4. **Raw Milk at the exact same minute:** Separate from **Augmentin** by 2 hours; eat fresh dahi/curd 2 hours later to restore healthy gut bacteria."
        )
    elif "miss" in q or "dose" in q:
        return (
            "⏰ **What to Do If You Miss a Dose:**\n"
            "• If you remember within 2–3 hours, take it as soon as you remember.\n"
            "• If it is almost time for your next scheduled dose, **skip the missed dose** and resume your normal schedule.\n"
            "• **Never double up or take 2 pills together** to make up for a forgotten dose!"
        )
    else:
        return (
            "Hello! I am **MediBot**, your MediDecode Clinical AI Assistant powered by Google Gemini.\n\n"
            "I monitor your active prescriptions (Thyronorm, Metformin, Atorvastatin, Augmentin, and Crocin) "
            "and your diagnostic lab reports to keep you safe.\n\n"
            "Feel free to ask me anything like:\n"
            "• *'Can I drink tea with my morning pills?'*\n"
            "• *'Why was I prescribed Metformin?'*\n"
            "• *'What foods must I avoid today?'*\n"
            "• *'Explain my latest blood test results'*."
        )
