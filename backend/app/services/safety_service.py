import re
import logging
from typing import List, Dict, Optional, Tuple, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import (
    User,
    Prescription,
    MedicationItem,
    SafetyAlert,
    PrescriptionStatus,
    MedicationFrequency,
    TimingRelation,
    SafetyAlertType,
    AlertSeverity,
)
from app.schemas.safety import (
    CumulativeToxicityAlert,
    FastingAdjustment,
    ReconciliationResponse,
    SafetyAlertRead,
)

logger = logging.getLogger(__name__)

# Catalog mapping commercial brand names to canonical generic molecules
BRAND_TO_GENERIC: Dict[str, str] = {
    # Paracetamol / Acetaminophen
    "crocin": "Paracetamol",
    "dolo": "Paracetamol",
    "calpol": "Paracetamol",
    "tylenol": "Paracetamol",
    "panadol": "Paracetamol",
    "p-650": "Paracetamol",
    "pacimol": "Paracetamol",
    "paracetamol": "Paracetamol",
    "acetaminophen": "Paracetamol",
    # NSAIDs
    "combiflam": "Ibuprofen + Paracetamol",
    "brufen": "Ibuprofen",
    "ibuprofen": "Ibuprofen",
    "voveran": "Diclofenac",
    "dynapar": "Diclofenac",
    "diclofenac": "Diclofenac",
    "zerodol": "Aceclofenac",
    "aceclofenac": "Aceclofenac",
    "naprosyn": "Naproxen",
    "naproxen": "Naproxen",
    # Antidiabetics
    "glycomet": "Metformin",
    "glucophage": "Metformin",
    "obimet": "Metformin",
    "cetapin": "Metformin",
    "metformin": "Metformin",
    # Statins
    "lipitor": "Atorvastatin",
    "atorva": "Atorvastatin",
    "storvas": "Atorvastatin",
    "atorvastatin": "Atorvastatin",
    "rosuvas": "Rosuvastatin",
    "crestor": "Rosuvastatin",
    "rosuvastatin": "Rosuvastatin",
    # Thyroid
    "eltroxin": "Levothyroxine",
    "thyronorm": "Levothyroxine",
    "synthroid": "Levothyroxine",
    "levothyroxine": "Levothyroxine",
    # Antibiotics
    "ciplox": "Ciprofloxacin",
    "cifran": "Ciprofloxacin",
    "ciprofloxacin": "Ciprofloxacin",
    "doxy-1": "Doxycycline",
    "doxicip": "Doxycycline",
    "doxycycline": "Doxycycline",
    "minoz": "Minocycline",
    "minocycline": "Minocycline",
    "augmentin": "Amoxicillin-Clavulanate",
    "mox": "Amoxicillin",
    # Antihypertensives
    "envas": "Enalapril",
    "enalapril": "Enalapril",
    "cardace": "Ramipril",
    "ramipril": "Ramipril",
    "telma": "Telmisartan",
    "telmisartan": "Telmisartan",
    "losar": "Losartan",
    "losartan": "Losartan",
    "amlong": "Amlodipine",
    "amlodipine": "Amlodipine",
}

# Maximum daily safe doses in mg
SAFE_DAILY_CEILINGS_MG: Dict[str, float] = {
    "Paracetamol": 4000.0,      # >4000mg risks acute hepatic necrosis
    "Metformin": 2550.0,        # >2550mg increases lactic acidosis risk
    "Ibuprofen": 2400.0,        # >2400mg severe gastrointestinal/renal risk
    "Diclofenac": 150.0,        # >150mg cardiovascular/renal risk
    "Aceclofenac": 200.0,       # >200mg ulcer/renal risk
    "Atorvastatin": 80.0,       # >80mg rhabdomyolysis risk
    "Rosuvastatin": 40.0,       # >40mg myopathy risk
}

NSAID_MOLECULES = {"Ibuprofen", "Diclofenac", "Aceclofenac", "Naproxen"}

FREQUENCY_MULTIPLIERS = {
    MedicationFrequency.OD: 1,
    MedicationFrequency.BD: 2,
    MedicationFrequency.TID: 3,
    MedicationFrequency.QID: 4,
    MedicationFrequency.SOS: 1,
}

# Pre-compiled high-quality regional clinical templates
REGIONAL_FALLBACK_TEMPLATES: Dict[str, Dict[str, str]] = {
    "hi": {
        "DUPLICATE_PARACETAMOL": "चेतावनी: आपके डॉक्टर के पर्चों में पेरासिटामोल दो अलग-अलग नामों से मौजूद है। दोनों को एक साथ लेने से लीवर को गंभीर नुकसान पहुँच सकता है।",
        "TOXIC_PARACETAMOL": "अत्यधिक खुराक चेतावनी: कुल पेरासिटामोल दैनिक सुरक्षित सीमा 4000mg से अधिक है। कृपया तुरंत अपने डॉक्टर से परामर्श करें।",
        "CHAI_IRON": "चाय में मौजूद टैनिन इस दवा के अवशोषण को रोकते हैं। दवा लेने के 2 घंटे पहले और बाद तक दूध वाली चाय या कॉफी न पिएं।",
        "DAIRY_ANTIBIOTIC": "दूध, दही या पनीर में मौजूद कैल्शियम एंटीबायोटिक के असर को कम कर देता है। दवा और डेयरी उत्पादों के बीच 2 घंटे का अंतर रखें।",
        "HIGH_SODIUM": "अचार, पापड़ और नमकीन में अधिक नमक इस दवा के रक्तचाप नियंत्रण को कमजोर करता है।",
        "RAMADAN_FASTING": "रमजान उपवास के दौरान खाली पेट ली जाने वाली दवा सुबह सेहरी से पहले (~04:30 AM) और शाम की दवा इफ्तार के बाद (~07:15 PM) लें।",
    },
    "ta": {
        "DUPLICATE_PARACETAMOL": "எச்சரிக்கை: பாராசிட்டமால் இரண்டு வெவ்வேறு பெயர்களில் பரிந்துரைக்கப்பட்டுள்ளது. இரண்டையும் ஒன்றாக உட்கொள்வது கல்லீரலை பாதிக்கும்.",
        "TOXIC_PARACETAMOL": "அதிக அளவு எச்சரிக்கை: பாராசிட்டமால் மொத்த அளவு பாதுகாப்பான வரம்பை (4000mg) தாண்டியுள்ளது.",
        "CHAI_IRON": "தேநீரில் உள்ள டானின் சத்து இந்த மருந்தின் சத்து உறிஞ்சுதலைத் தடுக்கிறது. மருந்து உட்கொள்வதற்கு 2 மணி நேரத்திற்குள் தேநீர் அருந்த வேண்டாம்.",
        "DAIRY_ANTIBIOTIC": "பால் அல்லது தயிரில் உள்ள கால்சியம் இந்த ஆண்டிபயாடிக் மருந்தின் வீரியத்தை குறைக்கும்.",
        "HIGH_SODIUM": "ஊறுகாய் மற்றும் அப்பளத்தில் உள்ள அதிக உப்பு இரத்த அழுத்தக் கட்டுப்பாட்டை பலவீனப்படுத்தும்.",
        "RAMADAN_FASTING": "ரமலான் நோன்பின் போது வெறும் வயிற்றில் உட்கொள்ளும் மருந்துகளை சஹர் நேரத்திலும், மாலை மருந்துகளை இப்தாருக்குப் பிறகும் எடுத்துக் கொள்ளுங்கள்.",
    },
    "te": {
        "DUPLICATE_PARACETAMOL": "హెచ్చరిక: పారాసిటమాల్ రెండు వేర్వేరు బ్రాండ్ పేర్లతో ఇవ్వబడింది. రెండింటినీ కలిపి తీసుకుంటే కాలేయానికి ప్రమాదం.",
        "TOXIC_PARACETAMOL": "మోతాదు మించిన హెచ్చరిక: పారాసిటమాల్ మొత్తం రోజువారీ పరిమితి 4000mg దాటింది.",
        "CHAI_IRON": "టీలోని టానిన్లు ఈ ఔషధ శోషణను అడ్డుకుంటాయి. మందు తీసుకునే 2 గంటల ముందు మరియు తరువాత టీ తాగవద్దు.",
        "DAIRY_ANTIBIOTIC": "పాలు, పెరుగులోని కాల్షియం ఈ యాంటీబయాటిక్ ప్రభావాన్ని తగ్గిస్తుంది.",
        "HIGH_SODIUM": "ఊరగాయలు మరియు అప్పడాలలోని అధిక ఉప్పు రక్తపోటు నియంత్రణను తగ్గిస్తుంది.",
        "RAMADAN_FASTING": "రంజాన్ ఉపవాస సమయంలో ఖాళీ కడుపుతో తీసుకునే మందులను సెహ్రీ ముందు, సాయంత్రం మందులను ఇఫ్తార్ తర్వాత తీసుకోండి.",
    },
    "bn": {
        "DUPLICATE_PARACETAMOL": "সতর্কতা: প্যারাসিটামল দুটি ভিন্ন নামে প্রেসক্রিপশনে রয়েছে। দুটি একসাথে খেলে লিভারের ক্ষতি হতে পারে।",
        "TOXIC_PARACETAMOL": "বিষাক্ততার সতর্কতা: প্যারাসিটামল দৈনিক নিরাপদ মাত্রা 4000 মিলিগ্রাম অতিক্রম করেছে।",
        "CHAI_IRON": "দুধ চায়ে থাকা ট্যানিন এই ওষুধের শোষণ ব্যাহত করে। ওষুধ খাওয়ার ২ ঘণ্টার মধ্যে চা খাবেন না।",
        "DAIRY_ANTIBIOTIC": "দুধ বা দইয়ের ক্যালসিয়াম এই অ্যান্টিবায়োটিকের কার্যকারিতা কমিয়ে দেয়।",
        "HIGH_SODIUM": "আচার ও পাঁপড়ের অতিরিক্ত লবণ রক্তচাপ নিয়ন্ত্রণে বাধা দেয়।",
        "RAMADAN_FASTING": "রমজানের উপবাসে খালি পেটের ওষুধ সাহরির আগে এবং সন্ধ্যার ওষুধ ইফতারের পরে গ্রহণ করুন।",
    },
}


def normalize_molecule(brand_name: Optional[str], generic_molecule: Optional[str]) -> str:
    """Standardizes brand names and molecule spellings into canonical active pharmaceutical ingredient."""
    if generic_molecule and generic_molecule.strip():
        gen_clean = generic_molecule.strip().lower()
        if gen_clean in BRAND_TO_GENERIC:
            return BRAND_TO_GENERIC[gen_clean]
        # Check title casing
        return generic_molecule.strip().capitalize()

    if brand_name and brand_name.strip():
        first_token = re.split(r"[\s\-_/]+", brand_name.strip().lower())[0]
        if first_token in BRAND_TO_GENERIC:
            return BRAND_TO_GENERIC[first_token]
        return brand_name.strip().capitalize()

    return "Unknown Molecule"


def extract_strength_in_mg(strength_str: str) -> float:
    """Extracts numeric milligram dose from strength string, e.g. '650mg' -> 650.0, '1g' -> 1000.0, '50mcg' -> 0.05."""
    if not strength_str:
        return 0.0

    s = strength_str.strip().lower()
    
    # Grams
    g_match = re.search(r"(\d+(?:\.\d+)?)\s*g(?:ram)?\b", s)
    if g_match:
        return float(g_match.group(1)) * 1000.0

    # Micrograms (mcg / ug)
    mcg_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mcg|ug)\b", s)
    if mcg_match:
        return float(mcg_match.group(1)) / 1000.0

    # Milligrams (mg)
    mg_match = re.search(r"(\d+(?:\.\d+)?)\s*mg\b", s)
    if mg_match:
        return float(mg_match.group(1))

    # Raw digits without units
    num_match = re.search(r"(\d+(?:\.\d+)?)", s)
    if num_match:
        return float(num_match.group(1))

    return 0.0


class SafetyService:
    """Core intelligence engine for multi-script reconciliation and cultural safety."""

    async def get_regional_translations(
        self,
        key: str,
        english_text: str,
        preferred_lang: str,
    ) -> Dict[str, str]:
        """Returns multilingual localized advisories, using Gemini when available with verified clinical fallbacks."""
        localized: Dict[str, str] = {
            "en": english_text,
        }

        # Check precompiled templates first
        for lang in ["hi", "ta", "te", "bn"]:
            if lang in REGIONAL_FALLBACK_TEMPLATES and key in REGIONAL_FALLBACK_TEMPLATES[lang]:
                localized[lang] = REGIONAL_FALLBACK_TEMPLATES[lang][key]

        # If user preferred language is requested and not in localized dict, attempt Gemini translation
        if preferred_lang != "en" and preferred_lang not in localized and settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = (
                    f"Translate the following medical patient advisory into plain, colloquial, empathetic "
                    f"language for a patient speaking '{preferred_lang}':\n\"{english_text}\"\n"
                    f"Return only the translated sentence without extra commentary."
                )
                resp = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[prompt],
                )
                if resp.text and resp.text.strip():
                    localized[preferred_lang] = resp.text.strip()
            except Exception as e:
                logger.warning(f"Regional translation via Gemini failed: {e}")

        return localized

    async def reconcile_prescription(
        self,
        prescription_id: UUID,
        session: AsyncSession,
    ) -> ReconciliationResponse:
        """Audits a new prescription against all previously active patient prescriptions."""
        # 1. Load current prescription with medications and user
        stmt = (
            select(Prescription)
            .where(Prescription.id == prescription_id)
            .options(
                selectinload(Prescription.medication_items),
                selectinload(Prescription.user),
            )
        )
        res = await session.execute(stmt)
        target_rx = res.scalar_one_or_none()
        if not target_rx:
            raise ValueError(f"Prescription with ID '{prescription_id}' not found.")

        user = target_rx.user
        new_meds = target_rx.medication_items

        # 2. Fetch all previous active prescriptions for this user
        prev_stmt = (
            select(Prescription)
            .where(
                Prescription.user_id == user.id,
                Prescription.id != prescription_id,
            )
            .options(selectinload(Prescription.medication_items))
        )
        prev_res = await session.execute(prev_stmt)
        prev_rxs = prev_res.scalars().all()

        all_active_meds_map: Dict[UUID, Tuple[MedicationItem, Prescription]] = {}
        for rx in prev_rxs:
            for med in rx.medication_items:
                if med.is_active:
                    all_active_meds_map[med.id] = (med, rx)

        # Map current target prescription meds
        for med in new_meds:
            all_active_meds_map[med.id] = (med, target_rx)

        # 3. Cross-Doctor De-Duplication & Toxicity Detection
        alerts: List[SafetyAlert] = []
        cumulative_toxicities: List[CumulativeToxicityAlert] = []

        # Group by canonical generic molecule
        molecule_groups: Dict[str, List[Tuple[MedicationItem, Prescription]]] = {}
        for med, rx in all_active_meds_map.values():
            canonical = normalize_molecule(med.brand_name, med.generic_molecule)
            molecule_groups.setdefault(canonical, []).append((med, rx))

        # Check for duplicates & cumulative dosages
        nsaid_count = 0
        nsaid_items: List[Tuple[MedicationItem, Prescription]] = []

        for molecule, items in molecule_groups.items():
            if molecule in NSAID_MOLECULES:
                nsaid_count += len(items)
                nsaid_items.extend(items)

            # Cumulative daily dose calculation
            total_daily_mg = 0.0
            brands_seen = set()
            doctors_seen = set()

            for med, rx in items:
                dose_mg = extract_strength_in_mg(med.strength)
                mult = FREQUENCY_MULTIPLIERS.get(med.frequency, 1)
                total_daily_mg += dose_mg * mult
                if med.brand_name:
                    brands_seen.add(med.brand_name)
                if rx.doctor_name:
                    doctors_seen.add(rx.doctor_name)

            # A. Duplicate Molecule Detection
            if len(items) > 1 and len(brands_seen) > 1:
                brands_str = ", ".join(sorted(brands_seen))
                doctors_str = ", ".join(sorted(doctors_seen)) if doctors_seen else "Multiple clinicians"
                adv_text = (
                    f"Duplicate molecule detected: '{molecule}' is actively prescribed under multiple brand names "
                    f"({brands_str}) by {doctors_str}. Taking both can lead to inadvertent overdose."
                )
                localized = await self.get_regional_translations(
                    key="DUPLICATE_PARACETAMOL" if molecule == "Paracetamol" else "DUPLICATE_GENERIC",
                    english_text=adv_text,
                    preferred_lang=user.preferred_language,
                )
                alert = SafetyAlert(
                    user_id=user.id,
                    medication_id=items[-1][0].id,
                    alert_type=SafetyAlertType.DUPLICATE_MOLECULE,
                    severity=AlertSeverity.CRITICAL,
                    advisory_text=adv_text,
                    localized_advisory=localized,
                )
                alerts.append(alert)
                session.add(alert)

            # B. Cumulative Toxicity Detection
            ceiling_mg = SAFE_DAILY_CEILINGS_MG.get(molecule)
            if ceiling_mg and total_daily_mg > ceiling_mg:
                is_toxic = True
                clinical_risk = (
                    f"Acute hepatotoxicity / liver failure risk (dose {total_daily_mg:.0f}mg/day exceeds safe ceiling {ceiling_mg:.0f}mg/day)"
                    if molecule == "Paracetamol"
                    else f"Severe toxicity risk: daily dose ({total_daily_mg:.0f}mg) exceeds maximum safe ceiling ({ceiling_mg:.0f}mg)"
                )
                cum_alert = CumulativeToxicityAlert(
                    generic_molecule=molecule,
                    cumulative_daily_dose_mg=total_daily_mg,
                    max_safe_daily_dose_mg=ceiling_mg,
                    is_toxic=is_toxic,
                    contributing_brands=list(brands_seen),
                    prescribing_doctors=list(doctors_seen),
                    clinical_risk=clinical_risk,
                )
                cumulative_toxicities.append(cum_alert)

                adv_text = (
                    f"CRITICAL TOXICITY WARNING: Cumulative daily intake of {molecule} is {total_daily_mg:.0f}mg/day, "
                    f"which exceeds the maximum clinical ceiling of {ceiling_mg:.0f}mg/day. "
                    f"Contributing brands: {', '.join(sorted(brands_seen))}."
                )
                localized = await self.get_regional_translations(
                    key="TOXIC_PARACETAMOL" if molecule == "Paracetamol" else "TOXIC_GENERIC",
                    english_text=adv_text,
                    preferred_lang=user.preferred_language,
                )
                alert = SafetyAlert(
                    user_id=user.id,
                    medication_id=items[-1][0].id,
                    alert_type=SafetyAlertType.CUMULATIVE_TOXICITY,
                    severity=AlertSeverity.CRITICAL,
                    advisory_text=adv_text,
                    localized_advisory=localized,
                )
                alerts.append(alert)
                session.add(alert)

        # C. Multiple NSAID Overlap
        if len({normalize_molecule(m.brand_name, m.generic_molecule) for m, _ in nsaid_items}) > 1:
            nsaid_brands = ", ".join(sorted({m.brand_name for m, _ in nsaid_items if m.brand_name}))
            adv_text = (
                f"Combined NSAID Alert: Multiple non-steroidal anti-inflammatory drugs ({nsaid_brands}) "
                f"are concurrently active. Concomitant NSAIDs compound gastric ulceration, bleeding, and renal injury risk."
            )
            localized = await self.get_regional_translations(
                key="DUPLICATE_NSAID",
                english_text=adv_text,
                preferred_lang=user.preferred_language,
            )
            alert = SafetyAlert(
                user_id=user.id,
                medication_id=nsaid_items[-1][0].id,
                alert_type=SafetyAlertType.DUPLICATE_MOLECULE,
                severity=AlertSeverity.CRITICAL,
                advisory_text=adv_text,
                localized_advisory=localized,
            )
            alerts.append(alert)
            session.add(alert)

        # 4. Cultural Dietary & Fasting Rules Engine
        diet_profile = user.cultural_dietary_profile or {}
        tea_intake = str(diet_profile.get("tea_dairy_intake", "")).lower()
        fasting_routines = [str(f).upper() for f in diet_profile.get("fasting_routines", [])]
        fasting_adjustments: List[FastingAdjustment] = []

        for med in new_meds:
            molecule = normalize_molecule(med.brand_name, med.generic_molecule)

            # Rule 1: Chai / Milk Tea blunting Iron / Calcium / Levothyroxine
            if molecule in {"Levothyroxine", "Iron", "Ferrous", "Calcium"}:
                if any(k in tea_intake for k in ["high", "tea", "chai", "cup"]):
                    adv_text = (
                        f"Cultural Dietary Conflict: Tannins and casein in daily milk tea (chai) severely blunt the intestinal "
                        f"absorption of {med.brand_name or molecule}. Maintain a strict separation of at least 2 hours."
                    )
                    localized = await self.get_regional_translations(
                        key="CHAI_IRON",
                        english_text=adv_text,
                        preferred_lang=user.preferred_language,
                    )
                    alert = SafetyAlert(
                        user_id=user.id,
                        medication_id=med.id,
                        alert_type=SafetyAlertType.FOOD_INTERACTION,
                        severity=AlertSeverity.MODERATE,
                        advisory_text=adv_text,
                        localized_advisory=localized,
                    )
                    alerts.append(alert)
                    session.add(alert)

            # Rule 2: Dairy Chelation with Tetracyclines & Fluoroquinolones
            if molecule in {"Ciprofloxacin", "Levofloxacin", "Doxycycline", "Minocycline"}:
                if any(k in tea_intake for k in ["dairy", "milk", "high", "paneer"]):
                    adv_text = (
                        f"Dairy Chelation Risk: Polyvalent calcium cations in milk, yogurt (dahi), and paneer bind with {molecule}, "
                        f"forming insoluble chelates that render the antibiotic ineffective. Do not consume dairy within 2 hours of dosing."
                    )
                    localized = await self.get_regional_translations(
                        key="DAIRY_ANTIBIOTIC",
                        english_text=adv_text,
                        preferred_lang=user.preferred_language,
                    )
                    alert = SafetyAlert(
                        user_id=user.id,
                        medication_id=med.id,
                        alert_type=SafetyAlertType.FOOD_INTERACTION,
                        severity=AlertSeverity.MODERATE,
                        advisory_text=adv_text,
                        localized_advisory=localized,
                    )
                    alerts.append(alert)
                    session.add(alert)

            # Rule 3: High-Sodium traditional diet with ACE inhibitors / ARBs
            if molecule in {"Enalapril", "Ramipril", "Telmisartan", "Losartan"}:
                adv_text = (
                    f"Sodium Counteraction Notice: Traditional high-sodium pickles (achaar), papad, and savory namkeen counteract "
                    f"the therapeutic blood pressure lowering efficacy of {med.brand_name or molecule}."
                )
                localized = await self.get_regional_translations(
                    key="HIGH_SODIUM",
                    english_text=adv_text,
                    preferred_lang=user.preferred_language,
                )
                alert = SafetyAlert(
                    user_id=user.id,
                    medication_id=med.id,
                    alert_type=SafetyAlertType.FOOD_INTERACTION,
                    severity=AlertSeverity.INFO,
                    advisory_text=adv_text,
                    localized_advisory=localized,
                )
                alerts.append(alert)
                session.add(alert)

            # Rule 4: Fasting Mode Adjustments (Ramadan, Navratri)
            if "RAMADAN" in fasting_routines:
                if med.timing_relation == TimingRelation.AC:
                    # Empty stomach -> pre-dawn Suhoor
                    fasting_adjustments.append(
                        FastingAdjustment(
                            routine_name="RAMADAN",
                            original_timing=f"{med.brand_name or molecule} (AC - Morning)",
                            adapted_timing="Pre-dawn Suhoor (~04:30 AM) with water 30 mins before morning meal",
                            rationale="Oral fasting commences at dawn (Fajr); empty stomach dosing must occur prior to daylight.",
                        )
                    )
                elif med.timing_relation in {TimingRelation.PC, TimingRelation.WITH_FOOD}:
                    # Evening dose -> post-sunset Iftar
                    fasting_adjustments.append(
                        FastingAdjustment(
                            routine_name="RAMADAN",
                            original_timing=f"{med.brand_name or molecule} (PC/With Food)",
                            adapted_timing="Post-sunset Iftar (~07:15 PM) or after night meal",
                            rationale="Consuming food-dependent medications during daylight breaks fast; synchronize with evening feast.",
                        )
                    )

                adv_text = (
                    f"Ramadan Fasting Synchronization: Dosing for {med.brand_name or molecule} is adapted for dawn-to-dusk fasting. "
                    f"Take pre-dawn doses at Suhoor and evening doses after sunset at Iftar. Stay hydrated."
                )
                localized = await self.get_regional_translations(
                    key="RAMADAN_FASTING",
                    english_text=adv_text,
                    preferred_lang=user.preferred_language,
                )
                alert = SafetyAlert(
                    user_id=user.id,
                    medication_id=med.id,
                    alert_type=SafetyAlertType.FASTING_CONFLICT,
                    severity=AlertSeverity.MODERATE,
                    advisory_text=adv_text,
                    localized_advisory=localized,
                )
                alerts.append(alert)
                session.add(alert)

        # 5. Generate Doctor Query Summary Sheet (Markdown)
        doctor_query_summary = self._generate_doctor_query_summary(
            user=user,
            target_rx=target_rx,
            cumulative_toxicities=cumulative_toxicities,
            alerts=alerts,
        )

        # 6. Update Prescription Status
        target_rx.status = PrescriptionStatus.RECONCILED
        await session.commit()

        # Build response
        alert_reads = [
            SafetyAlertRead(
                id=a.id,
                user_id=a.user_id,
                medication_id=a.medication_id,
                alert_type=a.alert_type,
                severity=a.severity,
                advisory_text=a.advisory_text,
                localized_advisory=a.localized_advisory,
                created_at=a.created_at or datetime.now(timezone.utc),
            )
            for a in alerts
        ]

        return ReconciliationResponse(
            prescription_id=target_rx.id,
            user_id=user.id,
            status=target_rx.status,
            alerts=alert_reads,
            cumulative_toxicities=cumulative_toxicities,
            fasting_adjustments=fasting_adjustments,
            doctor_query_summary=doctor_query_summary,
        )

    def _generate_doctor_query_summary(
        self,
        user: User,
        target_rx: Prescription,
        cumulative_toxicities: List[CumulativeToxicityAlert],
        alerts: List[SafetyAlert],
    ) -> Optional[str]:
        """Compiles a clinical markdown sheet for patient-to-physician reconciliation inquiries."""
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        if not critical_alerts and not cumulative_toxicities:
            return None

        lines = [
            "# MediDecode Clinical Safety & Multi-Script Reconciliation Report",
            f"**Patient Name**: {user.full_name}  ",
            f"**Patient ID**: #{str(user.id)[:8].upper()}  ",
            f"**Date Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"**Target Prescription**: {target_rx.doctor_name or 'Prescribing Doctor'} ({target_rx.doctor_specialty or 'Clinician'})  ",
            "\n---\n",
            "## ⚠️ Clinical Attention Required Prior to Dispensation",
            "\nThis patient is concurrently taking active medications prescribed across multiple clinicians. "
            "The following potential duplicate molecules and cumulative toxicities have been flagged by MediDecode:\n",
        ]

        if cumulative_toxicities:
            lines.append("### 1. Cumulative Toxicity Overages")
            lines.append("| Generic Molecule | Calculated Daily Dose | Safe Ceiling | Contributing Brands | Prescribing Clinicians |")
            lines.append("|---|---|---|---|---|")
            for tox in cumulative_toxicities:
                brands = ", ".join(tox.contributing_brands)
                docs = ", ".join(tox.prescribing_doctors) if tox.prescribing_doctors else "Multiple"
                lines.append(
                    f"| **{tox.generic_molecule}** | <span style='color:red;'>**{tox.cumulative_daily_dose_mg:.0f} mg/day**</span> | {tox.max_safe_daily_dose_mg:.0f} mg/day | {brands} | {docs} |"
                )
            lines.append("")

        if critical_alerts:
            lines.append("### 2. High-Risk Interaction & Duplicate Details")
            for idx, a in enumerate(critical_alerts, 1):
                lines.append(f"{idx}. **[{a.alert_type.value}]**: {a.advisory_text}")
            lines.append("")

        lines.extend([
            "### 3. Clinician Query Prompt",
            "> *\"Doctor, the patient is currently on multiple prescriptions containing overlapping molecules. "
            "Please confirm if the previous regimen should be discontinued or if dosage adjustments are required.\"*",
            "\n---\n",
            "*Generated by MediDecode Clinical Safety Guard*",
        ])

        return "\n".join(lines)


# Singleton safety engine instance
safety_service = SafetyService()
