from typing import Optional, List, Dict, Any, Tuple
"""
    DocMindX AI - Dynamic Clinical Care & Recommendations Engine
Powered by Gemini AI, Groq API, OpenFDA, DailyMed, WHO-ICD & BioPortal.
Generates dynamic, patient-tailored medicine counts, food timings, recovery duration,
supportive yoga & physio with YouTube tutorial links, and ice/hot compress guidance.
Provides graceful local clinical dataset fallback with clear warning metadata if APIs are unreachable.

ANTI-FABRICATION RULES:
- AI is instructed to recommend medicines ONLY for reported symptoms / assessed condition.
- AI must not invent symptoms or add medicines for conditions not present.
- Medicine count is dynamic (no fixed padding).
- All medicine entries are verified against OpenFDA / DailyMed.
- Recovery time uses qualified language (not guaranteed).
"""
import logging
import sys
import os
import re
import json
import urllib.parse
import requests

_logger = logging.getLogger("DocMindX.TriageEngine.CareRecommendations")

# Valid model chains
_GEMINI_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]
_GROQ_MODELS = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import GEMINI_API_KEY, GROQ_API_KEY, OPENFDA_API_KEY, gemini_pool
from ai.utils.image_resolver import resolve_image
from ai.utils.seasonal_context import get_seasonal_health_context, INDIAN_STATES

try:
    from api.openfda import search_drug_openfda
except Exception:
    def search_drug_openfda(*args, **kwargs):
        return None

try:
    from api.dailymed import search_dailymed_drugnames
except Exception:
    def search_dailymed_drugnames(*args, **kwargs):
        return []

try:
    from api.yoga_api import search_yoga_pose
except Exception:
    def search_yoga_pose(*args, **kwargs):
        return None


def _clean_json_response(raw_text: str) -> dict | None:
    """
    Extracts valid JSON dictionary from LLM markdown response.
    """
    if not raw_text:
        return None
    cleaned = raw_text.strip()
    if "</think>" in cleaned:
        cleaned = cleaned.split("</think>")[-1].strip()
    else:
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

    # Strip markdown code blocks
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        # Try to find JSON substring
        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(cleaned[first_brace:last_brace + 1])
            except Exception:
                pass
    return None


def _first_candidate_name(medicine_name: str, brand_examples: str = "") -> str:
    """
    Picks a clean drug name to query against live medicine APIs.
    """
    candidate = ""
    if brand_examples:
        candidate = brand_examples.split(",")[0].strip()
    if not candidate and medicine_name:
        candidate = medicine_name.split("OR ")[0]
        candidate = candidate.split("(")[0]
        candidate = candidate.split("+")[0]
        candidate = candidate.split("/")[0]
    return candidate.strip()



def _extract_clinical_presentation_attributes(
    symptoms: list = None,
    top_condition: str = "",
    condition_category: str = "",
    user_context: dict = None
) -> dict:
    """
    Extracts standardized generalized clinical attributes from patient presentation.
    Evaluates anatomical regions, physiological systems, and symptom concepts.
    Completely disease-name agnostic.
    """
    symptoms_list = symptoms or []
    text = f"{top_condition} {condition_category} " + " ".join([str(s) for s in symptoms_list])
    text_lower = text.lower()

    # 1. Neurological / Radicular / Neural compression involvement
    has_radicular_symptoms = any(k in text_lower for k in [
        "radiating", "radiates", "shooting pain", "nerve pain", "numbness",
        "tingling", "paresthesia", "radiculopathy", "radicular", "loss of sensation",
        "burning pain down", "pain radiating", "nerve compression", "shooting leg pain",
        "lumbosacral radiculopathy", "sciatic nerve root irritation", "sciatic nerve", "dermatomal radiation",
        "disc herniation", "herniated disc", "slipped disc", "disc prolapse",
        "पैर में जा रहा", "रेडिएटिंग", "कमर से पैर", "પગમાં જાય", "ઝણઝણાટી", "झुनझुनी", "मुंगिया"
    ])

    # 2. Musculoskeletal / Joint / Spinal involvement
    has_musculoskeletal_symptoms = any(k in text_lower for k in [
        "back pain", "backache", "lumbar", "cervical", "neck pain", "joint", "knee",
        "shoulder", "stiffness", "sprain", "strain", "muscle spasm", "tendon",
        "ligament", "arthritis", "myalgia", "swelling in joint", "spondyl", "synov"
    ])

    # 3. Respiratory / Airway involvement
    has_respiratory_symptoms = any(k in text_lower for k in [
        "cough", "wheeze", "sputum", "shortness of breath", "breathless",
        "dyspnea", "chest congestion", "bronch", "stridor", "airway"
    ])

    # 4. Gastrointestinal / Digestive involvement
    has_gastrointestinal_symptoms = any(k in text_lower for k in [
        "nausea", "vomiting", "acidity", "heartburn", "indigestion", "diarrhea",
        "abdominal pain", "cramps", "bloating", "constipation", "reflux", "gastric", "colic"
    ])

    # 5. Systemic / Febrile / Multi-system presentation
    has_systemic_fatigue_or_fever = any(k in text_lower for k in [
        "fever", "pyrexia", "high temperature", "chills", "rigors",
        "malaise", "body ache", "fatigue", "exhaustion", "weakness"
    ])

    # 6. Acute Emergency / Critical Red Flag
    has_emergency_red_flags = any(k in text_lower for k in [
        "severe chest pain", "chest pressure", "retrosternal", "cardiac arrest", "myocardial",
        "coronary", "stroke", "facial droop", "slurred speech", "loss of consciousness", "unconscious",
        "syncope", "acute shock", "uncontrolled bleeding", "anaphylaxis", "severe dyspnea", "cyanosis",
        "respiratory failure"
    ])

    # 7. Localized superficial presentation (cutaneous, musculoskeletal, topical-amenable)
    is_localized_superficial = has_musculoskeletal_symptoms or any(k in text_lower for k in [
        "skin", "rash", "dermatitis", "eczema", "burn", "cutaneous", "lesion",
        "wound", "contusion", "sprain", "local swelling", "erythema", "pruritus", "itch"
    ])

    # 8. Purely systemic or visceral presentation
    is_systemic_presentation = has_systemic_fatigue_or_fever or any(k in text_lower for k in [
        "internal", "visceral", "sepsis", "viremia", "bacteremia", "infection", "systemic"
    ])

    # 9. Oncological / Neoplastic indications
    has_oncological_indications = any(k in text_lower for k in [
        "neoplasm", "malignan", "carcinoma", "lymphoma", "sarcoma", "tumor", "cancer", "oncolog", "metastasis"
    ])

    # 10. Renal clearance / End-stage renal involvement
    has_renal_failure_indications = any(k in text_lower for k in [
        "renal failure", "kidney failure", "uremia", "dialysis", "end stage renal", "anuria", "severe azotemia", "ckd"
    ])

    # 11. Reactive bronchospasm
    has_bronchospasm_indications = has_respiratory_symptoms and any(k in text_lower for k in [
        "bronchospasm", "wheezing", "stridor", "airway constriction", "asthma attack", "reactive airway"
    ])

    # 12. Physiological presentation for compress/fomentation
    is_febrile_hyperpyrexia = has_systemic_fatigue_or_fever and any(k in text_lower for k in [
        "fever", "pyrexia", "high temperature", "chills", "ताप", "તાવ"
    ])
    is_acute_inflammatory_edema = any(k in text_lower for k in [
        "acute sprain", "acute strain", "recent contusion", "swelling", "edema", "hematoma", "मोच", "सूजन", "સોજો"
    ])
    is_chronic_musculoskeletal_stiffness = has_musculoskeletal_symptoms and not is_acute_inflammatory_edema

    return {
        "has_radicular_symptoms": has_radicular_symptoms,
        "has_musculoskeletal_symptoms": has_musculoskeletal_symptoms,
        "has_respiratory_symptoms": has_respiratory_symptoms,
        "has_gastrointestinal_symptoms": has_gastrointestinal_symptoms,
        "has_systemic_fatigue_or_fever": has_systemic_fatigue_or_fever,
        "has_emergency_red_flags": has_emergency_red_flags,
        "is_localized_superficial": is_localized_superficial,
        "is_systemic_presentation": is_systemic_presentation,
        "has_oncological_indications": has_oncological_indications,
        "has_renal_failure_indications": has_renal_failure_indications,
        "has_bronchospasm_indications": has_bronchospasm_indications,
        "is_acute_inflammatory_edema": is_acute_inflammatory_edema,
        "is_chronic_musculoskeletal_stiffness": is_chronic_musculoskeletal_stiffness,
    }


def condition_supports_topical(top_condition: str = "", symptoms: list = None) -> bool:
    """
    Returns True if localized topical formulations (gels, creams, sprays, ointments)
    are clinically appropriate for the patient's presentation.
    Evaluates clinical presentation attributes: localized superficial tissue involvement
    vs. purely systemic, visceral, or emergency presentations.
    Completely disease-name agnostic.
    """
    attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition=top_condition)

    # Emergency cardiac or acute internal presentations -> Topical inappropriate
    if attrs["has_emergency_red_flags"]:
        return False

    # Open bite wounds / deep punctures / bleeding cuts -> routine analgesic topical gel contraindicated
    text_lower = f"{top_condition} " + " ".join([str(s) for s in (symptoms or [])]).lower()
    if any(w in text_lower for w in ["bite", "dog bite", "animal bite", "deep cut", "puncture wound", "bleeding wound"]):
        return False

    # If the presentation is purely systemic/febrile with no localized musculoskeletal
    # or cutaneous involvement, topical formulations have zero clinical indication
    if attrs["is_systemic_presentation"] and not attrs["is_localized_superficial"]:
        return False

    # Permitted if patient has localized superficial (musculoskeletal or dermatological) indications
    return attrs["is_localized_superficial"]



KNOWN_ACTIVE_COMPOUNDS = {
    "paracetamol", "acetaminophen", "ibuprofen", "aspirin", "amoxicillin",
    "azithromycin", "ciprofloxacin", "cetirizine", "levocetirizine", "clotrimazole",
    "terbinafine", "ketoconazole", "fluconazole", "diclofenac", "aceclofenac",
    "tramadol", "metformin", "atorvastatin", "pantoprazole", "omeprazole",
    "rabeprazole", "ranitidine", "losartan", "amlodipine", "salbutamol",
    "montelukast", "dextromethorphan", "chlorpheniramine", "mupirocin"
}


def _extract_active_compound(name: str) -> str:
    """Extracts simplified active compound name for deduplication."""
    name_lower = (name or "").lower()
    for known in KNOWN_ACTIVE_COMPOUNDS:
        if known in name_lower:
            return known

    clean = re.sub(r'\(.*?\)', '', name_lower)
    clean = re.sub(r'[0-9]+(\.[0-9]+)?\s*(mg|mcg|g|%|ml)', '', clean)
    clean = re.sub(r'\b(inj|tablet|capsule|syrup|gel|cream|ointment|spray|drops|infusion|solution|oral)\b', '', clean)
    words = [w.strip() for w in clean.split() if len(w.strip()) > 2]
    return words[0] if words else name_lower[:8]


def get_medicine_gallery(
    medicine_entries: list,
    max_items: Optional[int] = None,
    top_condition: str = "",
    symptoms: list = None,
    duration: str = "1-3 Days"
) -> list:
    """
    Enriches each medicine entry with live OpenFDA / DailyMed verification, route/form gating,
    active compound deduplication, explicit dosage provenance, and resolved images.
    Returns dynamic count (0, 1, 2, 3, etc.) - never pads or truncates to an artificial quota.
    """
    gallery = []
    seen_dedup_keys = set()
    symptoms = symptoms or []

    entries = (medicine_entries or [])[:max_items] if max_items is not None else (medicine_entries or [])

    for entry in entries:
        if isinstance(entry, dict):
            med_name = entry.get("medicine_name") or entry.get("name", "")
            brand_examples = entry.get("brand_examples", "")
            indication = entry.get("indication", "")
            dosage = entry.get("dosage", "")
            course_duration = entry.get("course_duration") or entry.get("duration") or duration or "3 – 5 Days"
            food_timing = entry.get("food_timing", "After Food (खाने के बाद)")
            time_of_day = entry.get("time_of_day", "Twice Daily")
            warnings = entry.get("warnings", "Consult physician before use.")
            med_type = entry.get("type", "OTC")
            source_tag = entry.get("source", "Live Clinical AI")
            spec_form = entry.get("form") or entry.get("dosage_form", "")
            spec_route = entry.get("route", "")
        else:
            med_name = str(entry)
            brand_examples = ""
            indication = "Symptomatic relief"
            dosage = "As directed by physician"
            course_duration = "3 – 5 Days"
            food_timing = "After Food"
            time_of_day = "Twice Daily"
            warnings = "Consult doctor"
            med_type = "OTC"
            source_tag = "Clinical AI"
            spec_form = ""
            spec_route = ""

        candidate = _first_candidate_name(med_name, brand_examples)
        display_name = med_name if med_name else candidate

        # Topical clinical appropriateness gate
        name_lower = (display_name + " " + spec_form + " " + spec_route).lower()
        is_topical = any(t in name_lower for t in ["gel", "cream", "ointment", "spray", "lotion", "topical", "liniment"])
        if is_topical and not condition_supports_topical(top_condition, symptoms):
            continue

        # Active compound & route deduplication
        compound = _extract_active_compound(f"{display_name} {candidate}")
        route_lower = (spec_route or "").lower()
        if any(r in route_lower or r in name_lower for r in ["inject", "intravenous", "iv", "im", "subcutaneous", "infusion"]):
            route_key = "injectable"
            # Route gating: block routine injections for common mild short-duration illnesses, but permit Day 1 emergency prophylaxis
            emergency_terms = [
                "rabies", "arv", "rig", "antirabies", "anti-rabies", "tetanus",
                "toxoid", "snake", "antivenom", "asv", "epinephrine", "adrenaline",
                "resuscitation", "saline", "ringer", "dextrose", "insulin", "atropine",
                "bite", "wound", "anaphylaxis", "shock"
            ]
            combined_context = (display_name + " " + top_condition + " " + " ".join([str(s) for s in symptoms])).lower()
            is_emergency_prophylaxis = any(term in combined_context for term in emergency_terms)

            is_short_duration = any(d in (str(course_duration) + " " + str(duration)).lower() for d in ["1-3", "1 day", "2 days", "3 days", "day 1", "day 0", "hours", "started today"])
            is_common_mild = any(c in top_condition.lower() for c in ["common cold", "viral fever", "mild", "tension headache", "acute viral", "unspecified fever"])
            if not is_emergency_prophylaxis and is_common_mild and is_short_duration:
                _logger.info("[CareRecommendations] Blocked routine injectable '%s' for acute mild condition '%s'", display_name, top_condition)
                continue
        elif is_topical or any(r in route_lower for r in ["topical", "transdermal", "cutaneous"]):
            route_key = "topical"
        elif any(r in route_lower for r in ["inhal", "nasal"]):
            route_key = "inhalation"
        elif any(r in route_lower for r in ["eye", "opht"]):
            route_key = "ophthalmic"
        elif any(r in route_lower for r in ["ear", "otic"]):
            route_key = "otic"
        elif any(r in route_lower for r in ["rectal", "suppos"]):
            route_key = "rectal"
        else:
            route_key = "oral"

        dedup_key = (compound, route_key)
        if dedup_key in seen_dedup_keys:
            continue
        seen_dedup_keys.add(dedup_key)

        api_source = source_tag
        api_info = None
        fda_live = False
        dailymed_live = False
        dailymed_name_match = False
        dailymed_info = []

        if candidate:
            try:
                from api.openfda import search_drug_openfda, is_openfda_verified
                api_info = search_drug_openfda(candidate)
                if is_openfda_verified(api_info):
                    fda_live = True
            except Exception as exc:
                _logger.warning("[CareRecommendations] OpenFDA verification notice for '%s': %s", candidate, exc)

            try:
                from api.dailymed import get_dailymed_medicine_summary, is_dailymed_verified, search_dailymed_drugnames
                spl_summary = get_dailymed_medicine_summary(candidate)
                if is_dailymed_verified(spl_summary):
                    dailymed_live = True
                    dailymed_info = spl_summary.get("ndcs", [])
                else:
                    # Check drugnames for existence only (Name match, NOT SPL label verification)
                    name_matches = search_dailymed_drugnames(candidate)
                    if name_matches and len(name_matches) > 0:
                        dailymed_name_match = True
                        dailymed_info = name_matches
            except Exception as exc:
                _logger.warning("[CareRecommendations] DailyMed verification notice for '%s': %s", candidate, exc)

        is_clinically_verified = bool(fda_live or dailymed_live)
        if fda_live and dailymed_live:
            verification_status = "OPENFDA_AND_DAILYMED_VERIFIED"
            provider = "OpenFDA + DailyMed"
            api_source = f"{source_tag} [OpenFDA + DailyMed Verified]"
        elif fda_live:
            verification_status = "OPENFDA_VERIFIED"
            provider = "OpenFDA"
            api_source = f"{source_tag} [OpenFDA Verified]"
        elif dailymed_live:
            verification_status = "DAILYMED_VERIFIED"
            provider = "DailyMed"
            api_source = f"{source_tag} [DailyMed Verified]"
        elif dailymed_name_match:
            verification_status = "DAILYMED_NAME_MATCH"
            provider = "DailyMed (Name Match Only)"
            api_source = f"{source_tag} [DailyMed Name Match]"
        else:
            verification_status = "CLINICAL_REFERENCE"
            provider = "DocMindX Clinical Reference"
            api_source = f"{source_tag} [Clinical Reference]"

        candidate_dosage = dosage
        verified_label_dosage = None
        verified_strength = None
        verified_route = None
        verified_form = None

        if fda_live and api_info and isinstance(api_info, dict):
            verified_label_dosage = api_info.get("verified_label_dosage") or api_info.get("dosage_instructions") or None
            raw_strengths = api_info.get("strengths") or api_info.get("verified_strength")
            verified_strength = raw_strengths[0] if isinstance(raw_strengths, list) and raw_strengths else (raw_strengths or None)
            raw_routes = api_info.get("routes") or api_info.get("verified_route")
            verified_route = raw_routes[0] if isinstance(raw_routes, list) and raw_routes else (raw_routes or None)
            raw_forms = api_info.get("dosage_forms") or api_info.get("verified_form")
            verified_form = raw_forms[0] if isinstance(raw_forms, list) and raw_forms else (raw_forms or None)

        # Clean dosage form - never permit "Tube" (tube is packaging, not a dosage form)
        clean_spec_form = spec_form
        if str(clean_spec_form).strip().lower() in ["tube", "bottle", "strip"]:
            clean_spec_form = "Cream" if is_topical else "Tablet"
        if str(verified_form).strip().lower() in ["tube", "bottle", "strip"]:
            verified_form = "Cream" if is_topical else "Tablet"

        resolved_form = verified_form or clean_spec_form or ("Cream" if is_topical else "Tablet" if route_key == "oral" else route_key.capitalize())
        resolved_route = verified_route or spec_route or route_key.capitalize()

        # Truthful dosage instruction display
        dosage_display = candidate_dosage or "Consult healthcare practitioner for official clinical dosage."

        is_inj = (route_key == "injectable")
        is_hospital_protocol = is_inj
        admin_setting = "Hospital / Clinic Administration by Healthcare Professional Only" if is_inj else ("External Application / Topical" if is_topical else "Self-administration / Oral as directed")

        search_query = f"{display_name} {candidate}".strip()
        image_path, is_fallback = resolve_image("medicine", search_query)

        gallery.append({
            "name": display_name,
            "medicine_name": display_name,
            "candidate_medication": display_name,
            "candidate_name": candidate,
            "candidate_dosage": candidate_dosage,
            "dosage": dosage_display,
            "verified_label_dosage": verified_label_dosage,
            "verified_strength": verified_strength,
            "verified_route": verified_route,
            "verified_form": verified_form,
            "provider": provider,
            "verification_status": verification_status,
            "is_live": bool(fda_live or dailymed_live or dailymed_name_match),
            "is_fallback": bool(not is_clinically_verified),
            "is_verified": bool(is_clinically_verified),
            "source": api_source,
            "indication": indication,
            "course_duration": course_duration,
            "food_timing": food_timing,
            "time_of_day": time_of_day,
            "warnings": warnings,
            "type": med_type,
            "openfda": api_info,
            "dailymed": dailymed_info[:2] if isinstance(dailymed_info, list) else [],
            "route": resolved_route,
            "dosage_form": resolved_form,
            "is_hospital_protocol": is_hospital_protocol,
            "administration_setting": admin_setting,
            "image": image_path,
        })
    return gallery

def get_youtube_search_url(query: str) -> str:
    """
    Constructs a clean, direct YouTube search tutorial link.
    """
    clean_q = f"how to do {query} yoga tutorial"
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_q)}"


def get_dynamic_clinical_recommendations(
    symptoms: list,
    user_context: dict,
    top_condition: str = "",
    lang_code: str = "en"
) -> dict:
    """
    Main API-First Dynamic Clinical Engine.
    Queries Gemini / Groq with patient's complete demographics, symptoms, severity, duration, and medical history.
    Dynamically generates the required number of medicines, food timing, recovery duration, supportive yoga with YouTube links,
    and ice/hot compress advice. Falls back to local dataset if APIs fail.
    """
    symptoms = symptoms or []
    user_context = user_context or {}
    age = user_context.get("age", "-- Select Age Group --")
    gender = user_context.get("gender", "-- Select Gender --")
    state = user_context.get("state") or user_context.get("location", "Gujarat")
    if "--" in state or "select" in state.lower():
        state = "Gujarat"
    location = state
    blood_group = user_context.get("blood_group", "None")
    severity = user_context.get("severity", "Moderate")
    duration = user_context.get("duration", "1 - 3 Days")
    conditions = user_context.get("conditions", ["None"])
    conditions_str = ", ".join(conditions) if isinstance(conditions, list) else str(conditions)
    medications = user_context.get("medications", "None")
    allergies = user_context.get("allergies", "None")
    family_history = user_context.get("surgeries", "") or user_context.get("family_history", "None")
    details = user_context.get("details", "")
    cond_lower = (top_condition or "").lower()
    sym_lower = " ".join([str(s) for s in symptoms]).lower()

    # Extract standardized clinical presentation attributes and emergency gate
    attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition=top_condition, user_context=user_context)
    is_emergency = bool(attrs.get("has_emergency_red_flags") or user_context.get("is_emergency", False))

    # Retrieve live seasonal health intelligence for the selected Indian State
    seasonal_data = get_seasonal_health_context(state, lang_code=lang_code)

    lang_instruction = "English" if lang_code == "en" else "Hindi (हिंदी)" if lang_code == "hi" else "Gujarati (ગુજરાતી)"

    supports_topical = condition_supports_topical(top_condition, symptoms)
    if supports_topical:
        topical_prompt_directive = """
   - DERMATOLOGICAL / TOPICAL FORMULATION MANDATE:
     This patient presents with a localized cutaneous or dermatological condition.
     First-line therapy MUST include an appropriate TOPICAL formulation (Cream, Ointment, or Gel — e.g. Clotrimazole 1% Cream, Terbinafine 1% Cream, Ketoconazole 2% Cream).
     Second-line therapy MAY include an oral formulation if clinically indicated (e.g. Fluconazole tablet or Levocetirizine for severe pruritus).
     Do NOT prescribe oral-only therapy for superficial fungal/skin infections.
     Set "form": "Cream" / "Ointment" / "Gel" / "Tablet" (NEVER set form to "Tube").
     Set "route": "Topical" / "Oral".
"""
    else:
        topical_prompt_directive = """
   - Prescribe appropriate oral or inhalation formulations.
     Set "form": "Tablet" / "Capsule" / "Syrup" / "Sachet".
     Set "route": "Oral".
"""

    prompt = f"""
    You are DocMindX AI — an advanced clinical healthcare & triage AI.
Perform an in-depth clinical analysis and prescribe a comprehensive, personalized care recommendation package for this patient across all relevant clinical care modalities.

PATIENT PROFILE:
- Demographics: Age Group: {age}, Gender: {gender}, State: {state}, Blood Group: {blood_group}
- Active Indian Season & Climate: {seasonal_data['season_name']} ({seasonal_data['alert_title']})
- Prevalent Regional Outbreak Risks in {state}: {', '.join(seasonal_data['key_surging_diseases'])}
- Clinical Symptoms: {', '.join(symptoms) if symptoms else 'General Illness'}
- Symptom Severity: {severity}
- Symptom Duration: {duration}
- Pre-existing Medical Conditions: {conditions_str}
- Current Ongoing Medications: {medications}
- Known Drug/Food Allergies: {allergies}
- Relevant Family Medical History & Prior Surgeries: {family_history}
- Additional Notes: {details}
- Primary Assessed Condition: {top_condition or 'Acute Illness'}

ANTI-FABRICATION RULES (MANDATORY):
0. ONLY recommend medicines that are DIRECTLY indicated for the reported symptoms and assessed condition.
   DO NOT add medicines for symptoms the patient did NOT report.
   DO NOT invent conditions or symptoms not present in the patient profile above.
   Use qualified clinical language: "Pattern compatible with..." NOT "Patient is diagnosed with..."
   Medicine count must be EXACTLY what is clinically required — do NOT pad with extra medicines.

CRITICAL CLINICAL INSTRUCTIONS:
1. LANGUAGE CONSISTENCY:
   - All text, indications, instructions, dietary advice, red flags, and food timing MUST be strictly in {lang_instruction}.
   - If English is requested, use pure English: "After Food", "Before Food (Empty Stomach)", "Take with Water".
   - If Hindi is requested, use pure Hindi: "भोजन के बाद", "भोजन से पहले (खाली पेट)".
   - If Gujarati is requested, use pure Gujarati: "જમ્યા પછી", "જમ્યા પહેલા (ખાલી પેટે)".

2. ILLNESS-SPECIFIC CLINICAL SUMMARY & TIMELINE:
   - "summary": A personalized 2-3 sentence clinical summary strictly tailored to {top_condition}, current season ({seasonal_data['season_name']}), and reported symptoms in {lang_instruction}. Use "Pattern compatible with..." language.
   - "recovery_duration": Realistic recovery timeline — use qualified language ("Recovery typically ranges from X to Y days depending on...") in {lang_instruction}.

3. TIER 1: DYNAMIC MEDICINES:
{topical_prompt_directive}
   - Prescribe ONLY the clinically indicated medications directly supported by evidence for this patient's exact symptoms, severity, and duration (return dynamic count: 0, 1, 2, 3, etc. - do NOT artificially target any fixed count).
   - For EACH medicine provide:
     - "name": Generic name with popular Indian brand in parentheses (e.g., "Paracetamol 650mg (Dolo 650 / Calpol)", "Pantoprazole 40mg (Pan 40)", "Oral Rehydration Salts (Electral / ORS)", "Azithromycin 500mg (Azee 500)", "Levocetirizine 5mg (Levocet)").
     - "indication": Specific symptom it treats in {lang_instruction}.
     - "dosage": Exact clinical dosage (e.g., "1 Tablet thrice daily after meals", "Apply thin layer twice daily").
     - "course_duration": Explicit course length in {lang_instruction} (e.g. "3 to 5 Days", "5 Days Full Course", "3 થી 5 દિવસ").
     - "food_timing": Explicit timing strictly in {lang_instruction} ("After Food", "Before Food (Empty Stomach)", "External Application").
     - "time_of_day": E.g. "Morning & Night (BD)", "Morning Empty Stomach", "SOS (When needed)", "Thrice Daily (TDS)".
     - "type": "OTC" or "Prescription".
     - "form": "Cream" / "Ointment" / "Gel" / "Tablet" / "Capsule" / "Syrup" (never "Tube").
     - "route": "Topical" / "Oral" / "Inhalation".
     - "warnings": Crucial safety precautions in {lang_instruction}.

4. TIER 2: CLINICAL INJECTIONS & IV FLUIDS (CONDITIONAL & STRICT DURATION-GATED):
   - Analyze whether injectable medication, IV infusion, or vaccine is MEDICALLY INDICATED for this patient.
   - STRICT DURATION RULE FOR ORDINARY / COMMON ILLNESSES:
     For common illnesses (e.g. viral fever, flu, cold, headache, throat infection, cough, mild infection, gastroenteritis):
     * If duration is short ("Started Today" or "1 - 3 Days"): NEVER prescribe or indicate injections or IV fluids. Set "is_indicated": false. First-line care is strictly oral medications.
     * Only consider injections / IV fluids for common illnesses if duration has persisted for "4 - 7 Days", "1 - 2 Weeks", or "More than 2 Weeks" AND severity is Severe / Refractory.
   - EXEMPTION FOR ACUTE EMERGENCIES: Animal/dog bites (Rabies post-exposure vaccine), deep/contaminated wounds or rusty metal cuts (Tetanus Toxoid), or acute shock/severe continuous vomiting unable to retain liquids are medically exempt and require immediate injection/IV from Day 1.
   - If indicated, provide "clinical_rationale" in {lang_instruction} and list of "items":
     - "name": Generic and brand name of injection / IV fluid.
     - "route": "Intravenous (IV)" or "Intramuscular (IM)" or "Subcutaneous (SC)".
     - "administration_setting": "Hospital / Clinic by Nurse or Physician" in {lang_instruction}.
     - "purpose": Plain-language purpose in {lang_instruction}.
     - "precautions": Crucial clinical safety note in {lang_instruction}.
   - If not indicated, set "is_indicated": false and "items": [].

5. TIER 3: COMPRESS GUIDANCE (ICE vs HOT vs COLD SPONGING - CONDITIONAL):
   - Analyze whether Cold / Ice Compress ("ice"), Warm / Hot Fomentation ("hot"), or Tepid Sponging ("cold_sponging") is beneficial for {top_condition}.
   - For high fever: use "cold_sponging" (माथे व शरीर पर ठंडी पट्टी).
   - For acute sprain/swelling/acute injury: use "ice" (बर्फ की सिकाई).
   - For muscle spasm/back pain/stiff joints/cervical: use "hot" (गर्म पानी की सिकाई).
   - If neither is clinically beneficial, set "is_indicated": false and "mode": "none".
   - If indicated, set "is_indicated": true, "mode": "ice" / "hot" / "cold_sponging", "title", "instructions", "duration_and_frequency", and "precautions" in {lang_instruction}.

6. TIER 4: PHYSIOTHERAPY & REHABILITATION EXERCISES (CONDITIONAL):
   - Analyze whether physical therapy, spinal mobility, joint rehabilitation exercises, or postural therapy are indicated for {top_condition}.
   - Set "is_indicated" to true ONLY when localized musculoskeletal, spinal, joint, or peripheral motor rehabilitation is clinically indicated.
   - Set "is_indicated" to false for purely systemic illnesses, uncomplicated headaches, or non-musculoskeletal presentations.
   - If indicated, provide "condition_target" in {lang_instruction} and 2 to 4 "exercises":
     - "name": Name of stretch/exercise (e.g. "Cat-Cow Spinal Stretch", "Straight Leg Raise", "Wall Ladder Climbing").
     - "target_area": Targeted joint or muscle group in {lang_instruction}.
     - "instructions": Step-by-step guidance in {lang_instruction}.
     - "caution": Warning when to stop (e.g. "Stop if sharp shooting pain occurs") in {lang_instruction}.

7. TIER 5: SPECIALIZED HOSPITAL CLINICAL THERAPIES (CONDITIONAL):
   - Analyze whether specialized tertiary clinical hospital procedures or therapies are required for this condition (e.g. Malignancy -> Chemotherapy/Targeted biologics; Renal Failure -> Hemodialysis; Severe Airway Obstruction -> Nebulization Therapy, Oxygen Support; Cardiac ischemia -> Invasive Cardiology / Revascularization).
   - Set "is_indicated" to true ONLY for serious, chronic, or oncological conditions. Set "is_indicated": false for common or self-limiting conditions.
   - If true, provide "therapy_name", "specialist_consult", "overview", and "patient_guidance" in {lang_instruction}.

8. SUPPORTIVE YOGA:
   - Provide restorative yoga postures tailored to this clinical presentation. CRITICAL EXERCISE SAFETY RULE: For any patient presenting with radicular nerve symptoms, radiating limb pain, acute disc herniation risk, or neuroforaminal compression, NEVER prescribe spinal hyperextension postures (such as Cobra Pose / Bhujangasana or deep backward bends) or high-load axial compression. Recommend only gentle decompression, neutral spinal alignment, and restorative postures.

9. DIETARY, HYDRATION, DO'S, DON'TS & RED FLAGS:
   - "foods_to_eat", "foods_to_avoid", "hydration_advice", "dos", "donts", "red_flags" in {lang_instruction}.

OUTPUT FORMAT:
Return strictly a valid JSON object with NO preamble matching this exact schema:
{{
  "summary": "2-3 sentence clinical summary in {lang_instruction}",
  "recovery_duration": "Expected recovery time text in {lang_instruction}",
  "seasonal_alert": {{
    "is_active": true,
    "title": "{seasonal_data['alert_title']}",
    "message": "{seasonal_data['alert_description']}"
  }},
  "medicines": [
    {{
      "name": "Medicine Name (Brand Example)",
      "indication": "...",
      "dosage": "...",
      "course_duration": "3 to 5 Days",
      "food_timing": "After Food / Before Food (Empty Stomach)",
      "time_of_day": "...",
      "type": "OTC / Prescription",
      "warnings": "..."
    }}
  ],
  "injections_and_iv": {{
    "is_indicated": false,
    "clinical_rationale": "...",
    "items": [
      {{
        "name": "Inj. Name",
        "route": "IV / IM / SC",
        "administration_setting": "Hospital / Clinic",
        "purpose": "...",
        "precautions": "..."
      }}
    ]
  }},
  "compress_guidance": {{
    "is_indicated": false,
    "mode": "ice / hot / cold_sponging / none",
    "title": "...",
    "instructions": "...",
    "duration_and_frequency": "...",
    "precautions": "..."
  }},
  "physiotherapy_guidance": {{
    "is_indicated": false,
    "condition_target": "...",
    "exercises": [
      {{
        "name": "...",
        "target_area": "...",
        "instructions": "...",
        "caution": "..."
      }}
    ]
  }},
  "specialized_therapies": {{
    "is_indicated": false,
    "therapy_name": "...",
    "specialist_consult": "...",
    "overview": "...",
    "patient_guidance": "..."
  }},
  "yoga_physio": [
    {{
      "name": "Pose Name",
      "sanskrit_name": "Sanskrit Name",
      "benefits": "...",
      "instructions": "..."
    }}
  ],
  "foods_to_eat": ["..."],
  "foods_to_avoid": ["..."],
  "hydration_advice": "...",
  "dos": ["..."],
  "donts": ["..."],
  "red_flags": ["..."]
}}"""
    ai_data = None
    api_source_name = "DocMindX AI Verified Care"
    ai_is_live = False
    ai_provider_used = None
    fallback_warning = ""

    # 1. Try Gemini API (Primary — Multi-Key Failover Pool)
    if gemini_pool.get_active_keys():
        gemini_payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.15, "maxOutputTokens": 2500, "responseMimeType": "application/json"}
        }
        res_data, gemini_model, key_used = gemini_pool.execute_with_failover(
            payload=gemini_payload,
            models=_GEMINI_MODELS,
            timeout=12
        )
        if res_data:
            candidates = res_data.get("candidates", [])
            if candidates:
                text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                parsed = _clean_json_response(text_out)
                if parsed and parsed.get("medicines"):
                    ai_data = parsed
                    api_source_name = f"DocMindX Clinical AI"
                    ai_is_live = True
                    ai_provider_used = f"Gemini ({gemini_model})"
                    _logger.info("[CareRecommendations] Gemini %s SUCCESS with key pool", gemini_model)

    # 2. Try Groq API (Secondary — valid model chain)
    if not ai_data and GROQ_API_KEY:
        for groq_model in _GROQ_MODELS:
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                body = {
                    "model": groq_model,
                    "messages": [
                        {"role": "system", "content": f"You are DocMindX AI. Return strict JSON only in {lang_instruction}. Do not include emojis."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.15,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"}
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=10)
                if res.status_code == 200:
                    text_out = res.json()["choices"][0]["message"]["content"]
                    parsed = _clean_json_response(text_out)
                    if parsed and parsed.get("medicines"):
                        ai_data = parsed
                        api_source_name = f"DocMindX Clinical AI"
                        ai_is_live = True
                        ai_provider_used = f"Groq ({groq_model})"
                        _logger.info("[CareRecommendations] Groq %s SUCCESS", groq_model)
                        break
                else:
                    _logger.warning("[CareRecommendations] Groq %s HTTP %s", groq_model, res.status_code)
            except requests.exceptions.Timeout:
                _logger.warning("[CareRecommendations] Groq %s TIMEOUT", groq_model)
            except requests.exceptions.ConnectionError:
                _logger.warning("[CareRecommendations] Groq %s CONNECTION ERROR", groq_model)
            except Exception as exc:
                _logger.error("[CareRecommendations] Groq %s error: %s", groq_model, exc)

    # Process AI Data if successfully fetched from Live APIs
    if ai_data and ai_data.get("medicines"):
        # Format medicines with OpenFDA + DailyMed verification + image resolver
        raw_meds = ai_data.get("medicines", [])
        for m in raw_meds:
            m["source"] = "Clinical AI Candidate (Gemini/Groq)"
        med_gallery = get_medicine_gallery(raw_meds, max_items=12, top_condition=top_condition, symptoms=symptoms)

        # Format Yoga / Physio with YouTube search URLs and images
        yoga_list = []
        text_presentation = f"{top_condition} " + " ".join([str(s) for s in symptoms]).lower()
        is_derm_condition = any(k in text_presentation for k in [
            "fungal", "fungus", "tinea", "ringworm", "dhadhar", "dadar", "khujli", "pruritus", "skin rash", "itching",
            "candidiasis", "athlete's foot", "jock itch"
        ])
        has_physical_indication = bool(
            attrs.get("has_radicular_symptoms") or
            attrs.get("has_musculoskeletal_symptoms") or
            attrs.get("has_respiratory_symptoms") or
            attrs.get("has_gastrointestinal_symptoms")
        )

        if is_emergency or (is_derm_condition and not has_physical_indication):
            # EMERGENCY / DERMATOLOGICAL GATE: Routine yoga is not indicated for superficial fungal/skin infections
            yoga_list = []
        else:
            raw_yoga = ai_data.get("yoga_physio") or ai_data.get("yoga_recommendations") or ai_data.get("yoga") or []
            for y in raw_yoga:
                y_name = y.get("name", "Restorative Posture")
                y_sansk = y.get("sanskrit_name", "")
                # Prevent hyperextension postures for radicular symptoms
                if attrs.get("has_radicular_symptoms") and any(k in f"{y_name} {y_sansk}".lower() for k in ["cobra", "bhujanga", "backward bend", "backbend"]):
                    continue
                y_ben = y.get("benefits", "Restorative stretching and recovery.")
                y_inst = y.get("instructions", "")
                
                image_path, is_fallback_img = resolve_image("yoga", f"{y_name} {y_sansk}")
                youtube_url = get_youtube_search_url(f"{y_name} {y_sansk}")

                yoga_list.append({
                    "name": y_name,
                    "sanskrit_name": y_sansk,
                    "benefits": y_ben,
                    "instructions": y_inst,
                    "image": image_path,
                    "is_fallback": is_fallback_img,
                    "youtube_url": youtube_url
                })

            # If LLM returned empty yoga list, populate safely from clinical attribute registry
            if not yoga_list and not is_derm_condition:
                yoga_list = _get_condition_fallback_yoga(top_condition, symptoms, lang_code)

        foods_to_eat = ai_data.get("foods_to_eat") or []
        if isinstance(foods_to_eat, str):
            foods_to_eat = [x.strip() for x in foods_to_eat.split("\n") if x.strip()]
        
        foods_to_avoid = ai_data.get("foods_to_avoid") or []
        if isinstance(foods_to_avoid, str):
            foods_to_avoid = [x.strip() for x in foods_to_avoid.split("\n") if x.strip()]
        
        hyd_advice = ai_data.get("hydration_advice") or "Drink 2.5 - 3 liters of water / fluids daily."
        
        clinical_dos = ai_data.get("dos") or ai_data.get("clinical_dos") or []
        if isinstance(clinical_dos, str):
            clinical_dos = [x.strip() for x in clinical_dos.split("\n") if x.strip()]
        
        clinical_donts = ai_data.get("donts") or ai_data.get("clinical_donts") or []
        if isinstance(clinical_donts, str):
            clinical_donts = [x.strip() for x in clinical_donts.split("\n") if x.strip()]

        diet_tips = (
            ai_data.get("dietary_guidelines") 
            or ai_data.get("dietary_advice") 
            or ai_data.get("diet") 
            or ai_data.get("diet_tips") 
            or []
        )
        if isinstance(diet_tips, str):
            diet_tips = [t.strip() for t in diet_tips.split("\n") if t.strip()]

        red_flag_tips = (
            ai_data.get("red_flags") 
            or ai_data.get("emergency_red_flags") 
            or ai_data.get("warning_signs") 
            or ai_data.get("red_flag_symptoms") 
            or []
        )
        if isinstance(red_flag_tips, str):
            red_flag_tips = [t.strip() for t in red_flag_tips.split("\n") if t.strip()]

        # If empty, extract condition-specific tips from CSV
        if not diet_tips or not red_flag_tips or not foods_to_eat:
            try:
                guidance_csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "diet", "condition_guidance.csv")
                if os.path.exists(guidance_csv_path):
                    import pandas as pd
                    df_g = pd.read_csv(guidance_csv_path)
                    cond_words = [w for w in re.findall(r'\b\w{4,}\b', (top_condition or "").lower()) if w not in ["disease", "syndrome", "acute", "chronic", "pain"]]
                    matched_g = df_g[df_g["condition_name"].str.lower().apply(lambda x: any(w in str(x).lower() for w in cond_words))] if cond_words else df_g.head(0)
                    if not matched_g.empty:
                        row = matched_g.iloc[0]
                        if not foods_to_eat:
                            diet_rec = str(row.get("diet_recommendation", "")).strip()
                            if diet_rec:
                                foods_to_eat.append(diet_rec)
                        if not foods_to_avoid:
                            avoid_food = str(row.get("food_to_limit", "") or row.get("what_to_avoid", "")).strip()
                            if avoid_food:
                                foods_to_avoid.append(avoid_food)
                        if not diet_tips:
                            if foods_to_eat:
                                diet_tips.extend([f"Recommended: {x}" for x in foods_to_eat])
                            if foods_to_avoid:
                                diet_tips.extend([f"Avoid: {x}" for x in foods_to_avoid])
                        if not red_flag_tips:
                            mon_adv = str(row.get("monitoring_advice", "")).strip()
                            if mon_adv:
                                red_flag_tips.append(f"Clinical Alert: {mon_adv}")
            except Exception as exc:
                _logger.error("[CareRecommendations] Condition guidance lookup error: %s", exc)

        # Default dos & donts if empty
        if not clinical_dos:
            clinical_dos = [
                "Take all medications strictly at the advised dosage and timing." if lang_code == "en" else ("दवाएं सही समय और सही खुराक पर लें।" if lang_code == "hi" else "દવાઓ યોગ્ય સમયે અને નિયમિત માત્રામાં લો."),
                "Maintain optimal rest and hydration to facilitate bodily recovery." if lang_code == "en" else ("शरीर को पूरा आराम दें और खूब पानी/तरल पदार्थ पिएं।" if lang_code == "hi" else "શરીરને પૂરતો આરામ આપો અને પ્રવાહીનું સેવન કરો."),
                "Monitor temperature and key symptoms daily." if lang_code == "en" else ("तापमान और लक्षणों पर नियमित नजर रखें।" if lang_code == "hi" else "શરીરનું તાપમાન અને લક્ષણો પર નિયમિત ધ્યાન રાખો.")
            ]
        if not clinical_donts:
            clinical_donts = [
                "Do NOT self-medicate or stop prescribed antibiotics/dosages prematurely." if lang_code == "en" else ("बिना डॉक्टर की सलाह के दवाएं बंद या बदलें नहीं।" if lang_code == "hi" else "ડૉક્ટરની સલાહ વિના દવા બંધ કે બદલવી નહીં."),
                "Avoid heavy physical exertion, smoking, and alcohol during recovery." if lang_code == "en" else ("भारी शारीरिक मेहनत और शराब/धूम्रपान से बचें।" if lang_code == "hi" else "વધુ પડતો શ્રમ અને બિનઆરોગ્યપ્રદ ટેવો ટાળો."),
                "Do NOT ignore sudden severe chest pain, breathlessness, or high fever." if lang_code == "en" else ("तेज बुखार, सांस में तकलीफ या छाती में दर्द को नजरअंदाज न करें।" if lang_code == "hi" else "તીવ્ર તાવ કે શ્વાસની તકલીફને અવગણશો નહીં.")
            ]

        # 1. Parse Injections / IV Fluids guidance
        injections_data = ai_data.get("injections_and_iv") or ai_data.get("injections") or {}
        if not isinstance(injections_data, dict):
            injections_data = {"is_indicated": False, "items": [], "injections": []}
        else:
            is_ind = bool(injections_data.get("is_indicated", False))
            raw_inj_items = injections_data.get("items") or injections_data.get("injections") or []
            if not isinstance(raw_inj_items, list):
                raw_inj_items = []
            clean_inj_items = []
            for inj in raw_inj_items:
                if isinstance(inj, dict):
                    clean_inj_items.append({
                        "name": inj.get("name", "Clinical Injection"),
                        "dose": inj.get("dose") or inj.get("dosage", "As directed by physician"),
                        "type": inj.get("type") or inj.get("route", "Intramuscular (IM) / Intravenous (IV)"),
                        "route": inj.get("route", "Intramuscular (IM) / Intravenous (IV)"),
                        "administration_setting": inj.get("administration_setting") or ("Hospital / Clinic by Healthcare Professional" if lang_code == "en" else ("अस्पताल या क्लिनिक में मेडिकल स्टाफ द्वारा" if lang_code == "hi" else "હોસ્પિટલ અથવા ક્લિનિકમાં નર્સ/ડૉક્ટર દ્વારા")),
                        "purpose": inj.get("purpose", ""),
                        "precautions": inj.get("precautions", "Administer under strict medical supervision.")
                    })
            injections_data = {
                "is_indicated": is_ind and len(clean_inj_items) > 0,
                "clinical_rationale": injections_data.get("clinical_rationale") or injections_data.get("reason", ""),
                "admin_setting": injections_data.get("admin_setting") or ("Hospital / Clinic Administration Only" if lang_code == "en" else ("केवल अस्पताल / क्लिनिक में चिकित्सकीय देखरेख में" if lang_code == "hi" else "માત્ર હોસ્પિટલ / ક્લિનિકમાં ડૉક્ટરની દેખરેખ હેઠળ")),
                "items": clean_inj_items,
                "injections": clean_inj_items
            }

            # Enforce Duration-Gated Injection Rule for Ordinary / Common Illnesses
            # Injections for common illnesses (fever, cold, viral, flu) are strictly blocked in 1-3 days
            dur_raw = str(duration).lower().strip()
            is_short_duration = any(d in dur_raw for d in ["today", "1 - 3", "1-3", "1 to 3", "आज", "આજે"])
            is_emergency_acute = any(k in cond_lower or k in sym_lower for k in [
                "dog bite", "animal bite", "rabies", "tetanus", "wound", "cut", "trauma", "puncture",
                "anaphylaxis", "severe dehydration", "shock", "रेबीज", "टिटनेस", "काटना"
            ])
            if is_short_duration and not is_emergency_acute:
                injections_data = {
                    "is_indicated": False,
                    "clinical_rationale": "",
                    "admin_setting": "Hospital / Clinic Administration Only",
                    "items": [],
                    "injections": []
                }

        # 2. Parse Compress Guidance (Ice vs Hot vs Cold Sponging)
        compress_data = ai_data.get("compress_guidance") or {}
        if not isinstance(compress_data, dict):
            compress_data = {"is_indicated": False, "mode": "none"}
        else:
            mode = str(compress_data.get("mode", "none")).lower().strip()
            is_comp_ind = bool(compress_data.get("is_indicated", mode in ["ice", "hot", "cold_sponging"]))
            compress_data = {
                "is_indicated": is_comp_ind and mode in ["ice", "hot", "cold_sponging"],
                "mode": mode if mode in ["ice", "hot", "cold_sponging"] else "none",
                "title": compress_data.get("title") or ("Cold / Ice Compress" if mode == "ice" else ("Warm / Hot Fomentation" if mode == "hot" else "Cold Sponging")),
                "instructions": compress_data.get("instructions") or compress_data.get("text", ""),
                "duration": compress_data.get("duration") or compress_data.get("duration_and_frequency", "10-15 minutes, 2 to 3 times daily."),
                "duration_and_frequency": compress_data.get("duration_and_frequency", "10-15 minutes, 2 to 3 times daily."),
                "cautions": compress_data.get("cautions") or compress_data.get("precautions", "Do not apply directly to damaged skin."),
                "precautions": compress_data.get("precautions", "Do not apply directly to damaged skin.")
            }

        # 3. Parse Physiotherapy & Rehabilitation guidance
        physio_data = ai_data.get("physiotherapy_guidance") or ai_data.get("physiotherapy") or {}
        if not isinstance(physio_data, dict):
            physio_data = {"is_indicated": False, "exercises": []}
        else:
            is_phys_ind = bool(physio_data.get("is_indicated", False))
            p_exercises = physio_data.get("exercises") or []
            if not isinstance(p_exercises, list):
                p_exercises = []
            enriched_exercises = []
            for ex in p_exercises:
                if isinstance(ex, dict):
                    ex_name = ex.get("name", "Rehabilitation Exercise")
                    ex_target = ex.get("target_area") or ex.get("target_muscle", "Target Joint")
                    ex_inst = ex.get("instructions") or ex.get("description", "")
                    ex_caution = ex.get("caution") or ex.get("precautions", "Stop immediately if sharp radiating pain occurs.")
                    enriched_exercises.append({
                        "name": ex_name,
                        "focus": ex_target,
                        "target_area": ex_target,
                        "reps": ex.get("reps", "10 reps / 2 sets"),
                        "description": ex_inst,
                        "instructions": ex_inst,
                        "caution": ex_caution,
                        "youtube_search_url": get_youtube_search_url(f"{ex_name} physiotherapy exercise tutorial"),
                        "youtube_url": get_youtube_search_url(f"{ex_name} physiotherapy exercise tutorial")
                    })
            physio_data = {
                "is_indicated": is_phys_ind and len(enriched_exercises) > 0,
                "clinical_rationale": physio_data.get("clinical_rationale") or physio_data.get("condition_target", "Mobility & Joint Function"),
                "condition_target": physio_data.get("condition_target", "Mobility & Joint Function"),
                "cautions": physio_data.get("cautions", "Stop immediately if sharp radiating pain occurs."),
                "exercises": enriched_exercises
            }

        # Emergency Gate: Suppress routine physiotherapy exercises
        if is_emergency:
            physio_data = {
                "is_indicated": False,
                "clinical_rationale": "Emergency Gate Activated",
                "condition_target": "Emergency Medical Evaluation Required",
                "cautions": "Routine physical exercises are strictly contraindicated during an acute emergency.",
                "exercises": []
            }

        # Dermatological Presentation Gate: Compresses and Physiotherapy are NOT indicated for fungal/superficial skin infections
        if is_derm_condition and not attrs.get("has_musculoskeletal_symptoms"):
            compress_data = {
                "is_indicated": False,
                "mode": "none",
                "title": "Compress Not Indicated",
                "instructions": "Warm fomentation or cold moisture is contraindicated for active cutaneous fungal lesions as heat/moisture promotes fungal growth.",
                "duration": "",
                "duration_and_frequency": "",
                "cautions": "Keep the affected skin clean and completely dry.",
                "precautions": "Keep the affected skin clean and completely dry."
            }
            physio_data = {
                "is_indicated": False,
                "clinical_rationale": "Non-musculoskeletal dermatological presentation",
                "condition_target": "Dermatological Presentation",
                "cautions": "Physical therapy exercises are not indicated for superficial cutaneous infections.",
                "exercises": []
            }

        # 4. Parse Specialized Clinical Therapies (Chemotherapy, Dialysis, Nebulization, etc.)
        specialized_data = ai_data.get("specialized_therapies") or ai_data.get("specialized_therapy") or {}
        if not isinstance(specialized_data, dict):
            specialized_data = {"is_indicated": False, "therapies": []}
        else:
            is_spec_ind = bool(specialized_data.get("is_indicated", False))
            th_name = specialized_data.get("therapy_name", "")
            raw_th_list = specialized_data.get("therapies", [])
            if not raw_th_list and th_name:
                raw_th_list = [{
                    "name": th_name,
                    "category": "Tertiary Hospital Treatment",
                    "setting": "Specialized Hospital / Medical Center",
                    "description": specialized_data.get("overview", "")
                }]
            specialized_data = {
                "is_indicated": is_spec_ind and (bool(th_name) or len(raw_th_list) > 0),
                "therapy_name": th_name,
                "specialist_type": specialized_data.get("specialist_consult") or specialized_data.get("specialist_type", "Specialist Physician"),
                "specialist_consult": specialized_data.get("specialist_consult") or specialized_data.get("specialist_type", "Specialist Physician"),
                "overview": specialized_data.get("overview") or specialized_data.get("clinical_guidance", ""),
                "patient_guidance": specialized_data.get("patient_guidance", "Undergo planned evaluation at an accredited medical centre."),
                "therapies": raw_th_list
            }

        # 5. Seasonal Alert metadata
        seasonal_alert_data = ai_data.get("seasonal_alert") or {}
        if not isinstance(seasonal_alert_data, dict):
            seasonal_alert_data = {
                "is_active": True,
                "title": seasonal_data["alert_title"],
                "message": seasonal_data["alert_description"]
            }
        else:
            seasonal_alert_data = {
                "is_active": bool(seasonal_alert_data.get("is_active", True)),
                "title": seasonal_alert_data.get("title") or seasonal_data["alert_title"],
                "message": seasonal_alert_data.get("message") or seasonal_data["alert_description"]
            }

        summary_val = ai_data.get("summary", "")
        if is_emergency and "EMERGENCY" not in summary_val.upper():
            summary_val = "CRITICAL EMERGENCY ALERT: Clinical findings indicate a possible medical emergency requiring urgent in-person medical evaluation. Routine exercise and home management are suspended. " + summary_val
        if is_emergency:
            red_flag_tips = ["URGENT EMERGENCY EVALUATION REQUIRED: Report immediately to an Emergency Department."] + [r for r in red_flag_tips if "EMERGENCY EVALUATION" not in r]

        return {
            "is_fallback": False,
            "is_live": True,
            "fallback_used": False,
            "fallback_warning": "",
            "api_source": api_source_name,
            "ai_provider_used": ai_provider_used or "Unknown AI",
            "top_condition": top_condition,
            "lang_code": lang_code,
            "state": state,
            "is_emergency": is_emergency,
            "summary": summary_val,
            "recovery_duration": ai_data.get("recovery_duration", "Recovery timeline varies by individual response to treatment and symptom severity."),
            "seasonal_context": seasonal_data,
            "seasonal_alert": seasonal_alert_data,
            "medicine_gallery": med_gallery,
            "total_medicines_recommended": len(med_gallery),
            "injections_and_iv": injections_data,
            "compress_guidance": compress_data,
            "cold_warm_compress_mode": compress_data.get("mode", "none"),
            "cold_warm_compress_indicated": compress_data.get("is_indicated", False),
            "physiotherapy_guidance": physio_data,
            "specialized_therapies": specialized_data,
            "yoga_recommendations": yoga_list,
            "dietary_guidelines": diet_tips,
            "foods_to_eat": foods_to_eat,
            "foods_to_avoid": foods_to_avoid,
            "hydration_advice": hyd_advice,
            "clinical_dos": clinical_dos,
            "clinical_donts": clinical_donts,
            "red_flags": red_flag_tips
        }

    # 3. Resilient Local Dataset Fallback (When APIs are unreachable)
    _logger.warning("[CareRecommendations] All AI providers failed — using LOCAL dataset fallback for: '%s'", top_condition)
    return _build_local_dataset_fallback(symptoms, user_context, top_condition, lang_code)



def _get_condition_fallback_medicines(top_condition: str, symptoms: list, lang_code: str = "en") -> list:
    """
    Dynamically loads condition-specific medicines from india_major_diseases.csv.
    Returns dynamic count (1 to 4, or 0 if acute emergency) - never forces exactly 4.
    """
    cond_lower = (top_condition or "").lower().strip()
    sym_lower = " ".join([str(s) for s in (symptoms or [])]).lower()

    # If no symptoms reported or input is unresolvable ("something feels strange in my body"), return 0 medicines
    if not symptoms or all(str(s).strip().lower() in ["something feels strange in my body", "unspecified", "unknown", "none", "insufficient_information", ""] for s in symptoms):
        return []

    # Emergency check: acute life-threatening presentations require hospital emergency care
    if any(k in cond_lower or k in sym_lower for k in ["heart attack", "myocardial", "stroke", "severe chest pain", "crushing chest pain", "acute shock", "unconscious", "cyanosis"]):
        return []

    ft_after = "After Food" if lang_code == "en" else "भोजन के बाद" if lang_code == "hi" else "જમ્યા પછી"
    ft_before = "Before Food (Empty Stomach)" if lang_code == "en" else "भोजन से पहले (खाली पेट)" if lang_code == "hi" else "જમ્યા પહેલા (ખાલી પેટે)"

    # 1. Dermatological / Cutaneous Fungal Presentation (First-line topical antifungal + optional antipruritic)
    is_derm_condition = any(k in cond_lower or k in sym_lower for k in [
        "fungal", "tinea", "ringworm", "dhadhar", "dadar", "khujli", "pruritus", "skin rash", "itching", "dermatitis", "eczema", "athlete's foot", "jock itch"
    ])
    if is_derm_condition and condition_supports_topical(top_condition, symptoms):
        parsed = []
        parsed.append({
            "name": "Clotrimazole 1% Cream (Candid / Canesten)",
            "brand_examples": "Candid, Canesten",
            "indication": "Topical antifungal treatment for superficial tinea, ringworm, and cutaneous fungal lesions." if lang_code == "en" else "दाद, खाज और त्वचा के फंगल संक्रमण के लिए सामयिक एंटीफंगल क्रीम।" if lang_code == "hi" else "દાદર અને ફંગલ ઇન્ફેક્શન માટે એન્ટિફંગલ ક્રીમ.",
            "dosage": "Apply a thin layer twice daily to clean, dry affected skin for 2 to 4 weeks.",
            "course_duration": "2 to 4 Weeks" if lang_code == "en" else "2 से 4 सप्ताह",
            "food_timing": "External Application (बाहरी प्रयोग)",
            "time_of_day": "Twice Daily (Morning & Evening)",
            "type": "OTC",
            "form": "Cream",
            "route": "Topical",
            "warnings": "For external application only. Continue use for 1-2 weeks after lesion clears to prevent relapse. Avoid contact with eyes or mucous membranes." if lang_code == "en" else "केवल बाहरी उपयोग के लिए। आंखों के संपर्क से बचें।",
            "source": "Clinical Reference Guidelines (IDSA / IADVL)"
        })
        if any(w in sym_lower or w in cond_lower for w in ["itch", "khujli", "prurit", "rash", "allergy", "ખંજવાળ"]):
            parsed.append({
                "name": "Levocetirizine 5mg (Levocet / 1-AL)",
                "brand_examples": "Levocet, 1-AL",
                "indication": "Relieves intense itching, erythema, and allergic cutaneous flare." if lang_code == "en" else "तीव्र खुजली, लालिमा और त्वचा की जलन से राहत देता है।" if lang_code == "hi" else "તીવ્ર ખંજવાળ અને લાલાશમાં રાહત આપે છે.",
                "dosage": "1 Tablet once daily at night / bedtime.",
                "course_duration": "5 to 7 Days" if lang_code == "en" else "5 से 7 दिन",
                "food_timing": ft_after,
                "time_of_day": "Night / Bedtime",
                "type": "OTC",
                "form": "Tablet",
                "route": "Oral",
                "warnings": "May cause mild drowsiness. Avoid driving or operating machinery after consumption." if lang_code == "en" else "हल्की नींद आ सकती है। सावधानी बरतें।",
                "source": "Clinical Reference Guidelines"
            })
        return parsed

    # 2. Look up in india_major_diseases.csv with robust non-generic keyword matching
    try:
        import pandas as pd
        csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "disease", "india_major_diseases.csv")
        if not os.path.exists(csv_path):
            csv_path = "datasets/disease/india_major_diseases.csv"
        if os.path.exists(csv_path):
            df_major = pd.read_csv(csv_path)
            generic_stopwords = {"disease", "syndrome", "acute", "chronic", "pain", "infection", "disorder", "condition", "fever", "major", "india", "type", "stage"}
            cond_words = [w for w in re.findall(r'\b\w{4,}\b', cond_lower) if w not in generic_stopwords]
            matched = df_major.head(0)
            if cond_words:
                exact_match = df_major[df_major["disease_name"].str.lower().apply(lambda x: cond_lower in str(x).lower() or str(x).lower() in cond_lower)]
                if not exact_match.empty:
                    matched = exact_match
                else:
                    def _overlap(row_name):
                        r_clean = str(row_name).lower()
                        hits = [w for w in cond_words if w in r_clean]
                        return len(hits) >= min(len(cond_words), 2) and len(hits) > 0
                    matched = df_major[df_major["disease_name"].apply(_overlap)]

            if not matched.empty:
                row = matched.iloc[0]
                meds_raw = str(row.get("medicines", "[]"))
                import ast
                try:
                    med_list = ast.literal_eval(meds_raw) if meds_raw.startswith("[") else [m.strip() for m in meds_raw.split(",") if m.strip()]
                except Exception:
                    med_list = [m.strip() for m in meds_raw.split(",") if m.strip()]
                
                parsed = []
                for m_str in med_list:
                    m_clean = str(m_str).strip(" '\"[]")
                    if not m_clean:
                        continue
                    is_ppi = any(p in m_clean.lower() for p in ["prazole", "antacid"])
                    parsed.append({
                        "name": m_clean,
                        "indication": f"Standard clinical therapy for {row.get('disease_name', top_condition)}.",
                        "dosage": "As directed by physician (1 tablet daily / twice daily).",
                        "course_duration": "5 to 7 Days" if lang_code == "en" else "5 से 7 दिन",
                        "food_timing": ft_before if is_ppi else ft_after,
                        "time_of_day": "Morning Empty Stomach" if is_ppi else "After meals",
                        "type": "Prescription",
                        "warnings": "Take strictly under clinical supervision." if lang_code == "en" else "चिकित्सक के परामर्श अनुसार लें।",
                        "source": "India MoHFW Master Guidelines"
                    })
                if parsed:
                    return parsed
    except Exception as e:
        pass

    # 3. Symptom-driven dynamic fallback
    parsed = []

    if any(f in sym_lower for f in ["fever", "pyrexia", "temperature", "बुखार", "તાવ"]):
        parsed.append({
            "name": "Paracetamol 650mg (Dolo 650 / Calpol)",
            "indication": "Reduces elevated body temperature and body aches." if lang_code == "en" else "बुखार और बदन दर्द में राहत देता है।",
            "dosage": "1 Tablet every 6 to 8 hours as needed.",
            "course_duration": "3 to 5 Days",
            "food_timing": ft_after,
            "time_of_day": "After meals",
            "type": "OTC",
            "warnings": "Do not exceed 3000mg per 24 hours.",
            "source": "DocMindX Clinical Master"
        })
        parsed.append({
            "name": "Oral Rehydration Salts (Electral / ORS)",
            "indication": "Restores hydration and vital electrolyte balance.",
            "dosage": "1 Sachet dissolved in 1 Litre clean water.",
            "course_duration": "2 to 3 Days",
            "food_timing": "With Water",
            "time_of_day": "Throughout the day",
            "type": "OTC",
            "warnings": "Reconstitute in exact quantity of clean water.",
            "source": "DocMindX Clinical Master"
        })
    elif any(p in sym_lower for p in ["back", "joint", "muscle", "sprain", "strain", "stiff", "tendon", "ligament", "ache", "pain", "કમર", "કમરનો દુખાવો", "પીઠ", "દર્દ"]):
        parsed.append({
            "name": "Ibuprofen 400mg (Brufen / Ibugesic)",
            "indication": "Relieves musculoskeletal inflammation and pain.",
            "dosage": "1 Tablet twice daily after food.",
            "course_duration": "3 to 5 Days",
            "food_timing": ft_after,
            "time_of_day": "Morning & Night",
            "type": "Prescription",
            "warnings": "Always take after a meal to protect the stomach.",
            "source": "DocMindX Clinical Master"
        })
        if condition_supports_topical(top_condition, symptoms):
            parsed.append({
                "name": "Diclofenac Diethylamine 1.16% Gel (Volini / Voveran)",
                "indication": "Localized topical pain relief for muscular stiffness.",
                "dosage": "Apply gently 2 to 3 times daily on affected area.",
                "course_duration": "3 to 5 Days",
                "food_timing": "External Use Only",
                "time_of_day": "As needed",
                "type": "OTC",
                "warnings": "For external application only. Do not apply on broken skin.",
                "source": "DocMindX Clinical Master"
            })
    else:
        # Only add paracetamol if pain was explicitly reported
        if any(w in sym_lower for w in ["pain", "discomfort", "sore", "hurt", "दर्द", "દુખાવો"]):
            parsed.append({
                "name": "Paracetamol 650mg (Dolo 650 / Calpol)",
                "indication": "Symptomatic pain and mild discomfort relief.",
                "dosage": "1 Tablet SOS when needed.",
                "course_duration": "3 Days",
                "food_timing": ft_after,
                "time_of_day": "As needed",
                "type": "OTC",
                "warnings": "Consult a registered doctor if symptoms persist.",
                "source": "DocMindX Clinical Master"
            })
    return parsed


# ==============================================================================
# GENERALIZED EXERCISE & YOGA CLINICAL METADATA REGISTRY
# ==============================================================================
YOGA_POSTURE_REGISTRY = [
    {
        "name": "Knees-to-Chest Pose",
        "sanskrit_name": "Apanasana",
        "target_body_region": "lumbar_spine",
        "movement_type": "flexion",
        "spinal_extension": "none",
        "loading_level": "none",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": ["acute_abdominal_surgery", "third_trimester_pregnancy"],
        "suitable_for_attributes": ["lumbar_musculoskeletal", "radicular_symptoms", "digestive_distress"],
        "benefits": "Gently decompresses lumbar spine without nerve-root pinching.",
        "instructions": "Lie on your back, gently draw one knee then both toward chest."
    },
    {
        "name": "Reclining Hamstring Stretch",
        "sanskrit_name": "Supta Padangusthasana",
        "target_body_region": "lower_extremity",
        "movement_type": "restorative",
        "spinal_extension": "none",
        "loading_level": "none",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": ["acute_hamstring_tear"],
        "suitable_for_attributes": ["lumbar_musculoskeletal", "radicular_symptoms"],
        "benefits": "Safely releases posterior myofascial tension along lower extremity nerve pathways.",
        "instructions": "Lie flat, loop towel around ball of foot and gently extend leg upward without forcing."
    },
    {
        "name": "Pelvic Tilts",
        "sanskrit_name": "Supta Pelvic Tilt",
        "target_body_region": "lumbar_spine",
        "movement_type": "neutral_stabilization",
        "spinal_extension": "none",
        "loading_level": "low",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": [],
        "suitable_for_attributes": ["lumbar_musculoskeletal", "radicular_symptoms"],
        "benefits": "Strengthens deep core stabilisers to support lumbar vertebrae in neutral alignment.",
        "instructions": "Lie on back with knees bent, gently flatten lower back into mat."
    },
    {
        "name": "Child's Pose",
        "sanskrit_name": "Balasana",
        "target_body_region": "spine_and_systemic",
        "movement_type": "gentle_flexion",
        "spinal_extension": "none",
        "loading_level": "none",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": ["acute_knee_injury"],
        "suitable_for_attributes": ["lumbar_musculoskeletal", "radicular_symptoms", "respiratory_support", "general_fatigue"],
        "benefits": "Gently elongates the dorsal spine and calms the autonomic nervous system.",
        "instructions": "Kneel, sit back on heels, gently fold forward extending arms."
    },
    {
        "name": "Cobra Pose",
        "sanskrit_name": "Bhujangasana",
        "target_body_region": "lumbar_spine",
        "movement_type": "extension",
        "spinal_extension": "hyperextension",
        "loading_level": "moderate",
        "impact_level": "low",
        "neurological_symptom_risk": "high",
        "contraindications": ["radicular_symptoms", "acute_lumbar_herniation", "spinal_stenosis", "nerve_compression"],
        "suitable_for_attributes": ["mild_non_radicular_back_stiffness"],
        "benefits": "Strengthens upper spinal extensor musculature.",
        "instructions": "Lie prone, gently press hands under shoulders to lift chest while keeping hips grounded."
    },
    {
        "name": "Alternate Nostril Breathing",
        "sanskrit_name": "Anulom Vilom",
        "target_body_region": "respiratory",
        "movement_type": "pranayama",
        "spinal_extension": "none",
        "loading_level": "none",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": [],
        "suitable_for_attributes": ["respiratory_support", "general_fatigue", "stress_reduction"],
        "benefits": "Enhances respiratory vital capacity, lowers sympathetic tone, and calms the nervous system.",
        "instructions": "Sit tall, inhale through left nostril, exhale through right nostril gently."
    },
    {
        "name": "Deep Yogic Breathing",
        "sanskrit_name": "Bhastrika",
        "target_body_region": "respiratory",
        "movement_type": "pranayama",
        "spinal_extension": "none",
        "loading_level": "none",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": ["uncontrolled_hypertension", "active_vertigo"],
        "suitable_for_attributes": ["respiratory_support"],
        "benefits": "Clears bronchopulmonary congestion and increases oxygenation.",
        "instructions": "Sit comfortably with upright spine, breathe deeply and rhythmically."
    },
    {
        "name": "Diamond Pose",
        "sanskrit_name": "Vajrasana",
        "target_body_region": "pelvic_digestive",
        "movement_type": "restorative",
        "spinal_extension": "none",
        "loading_level": "low",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": ["acute_knee_injury"],
        "suitable_for_attributes": ["digestive_distress"],
        "benefits": "Promotes gastric circulation and aids post-prandial digestion.",
        "instructions": "Sit on heels with spine straight for 5 to 10 minutes after light meals."
    },
    {
        "name": "Wind-Relieving Pose",
        "sanskrit_name": "Pawanmuktasana",
        "target_body_region": "abdominal_digestive",
        "movement_type": "flexion",
        "spinal_extension": "none",
        "loading_level": "none",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": ["recent_abdominal_surgery"],
        "suitable_for_attributes": ["digestive_distress", "lumbar_musculoskeletal"],
        "benefits": "Assists gentle peristalsis and abdominal gas release.",
        "instructions": "Lie on back, hug knees to chest gently."
    },
    {
        "name": "Corpse Pose",
        "sanskrit_name": "Shavasana",
        "target_body_region": "systemic_rest",
        "movement_type": "restorative",
        "spinal_extension": "none",
        "loading_level": "none",
        "impact_level": "none",
        "neurological_symptom_risk": "none",
        "contraindications": [],
        "suitable_for_attributes": ["general_fatigue", "digestive_distress", "respiratory_support", "stress_reduction"],
        "benefits": "Facilitates deep cellular rest and somatic recovery.",
        "instructions": "Lie flat on back and relax all abdominal muscles."
    }
]


def _get_condition_fallback_yoga(top_condition: str, symptoms: list, lang_code: str = "en") -> list:
    """
    Generalized attribute-based supportive yoga & exercise safety engine.
    Reasons from clinical attributes (movement properties, spinal extension, neurological risk,
    and patient clinical presentation attributes). Completely disease-name agnostic.
    """
    attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition=top_condition)

    # Absolute contraindication: acute emergency red flags
    if attrs["has_emergency_red_flags"]:
        return []

    # Dermatological / Superficial Skin Presentation Gate: Physical postures do not treat cutaneous / fungal infections
    text_lower = f"{top_condition} " + " ".join([str(s) for s in (symptoms or [])]).lower()
    is_dermatological = any(k in text_lower for k in [
        "fungal", "fungus", "tinea", "ringworm", "dhadhar", "dadar", "khujli", "pruritus", "itching",
        "rash", "skin", "eczema", "dermatitis", "psoriasis", "acne", "impetigo", "scabies", "urticaria",
        "candidiasis", "athlete's foot", "jock itch"
    ])
    has_physical_indication = (
        attrs["has_radicular_symptoms"] or
        attrs["has_musculoskeletal_symptoms"] or
        attrs["has_respiratory_symptoms"] or
        attrs["has_gastrointestinal_symptoms"]
    )
    if is_dermatological and not has_physical_indication:
        return []

    poses = []
    for posture in YOGA_POSTURE_REGISTRY:
        # GENERALIZED SAFETY RULE: Postures with significant spinal hyperextension
        # are strictly excluded for any patient presenting with radicular neurological symptoms
        if posture.get("spinal_extension") == "hyperextension" and attrs["has_radicular_symptoms"]:
            continue

        # Exclude postures with high neurological symptom risk when radicular symptoms exist
        if posture.get("neurological_symptom_risk") == "high" and attrs["has_radicular_symptoms"]:
            continue

        # Contraindication attribute matching
        contra = posture.get("contraindications", [])
        if attrs["has_radicular_symptoms"] and "radicular_symptoms" in contra:
            continue
        if attrs["has_emergency_red_flags"] and "severe_cardiac_emergency" in contra:
            continue

        # Suitability attribute matching
        suit = posture.get("suitable_for_attributes", [])
        matched = False
        if attrs["has_radicular_symptoms"] and "radicular_symptoms" in suit:
            matched = True
        elif attrs["has_musculoskeletal_symptoms"] and "lumbar_musculoskeletal" in suit:
            matched = True
        elif attrs["has_respiratory_symptoms"] and "respiratory_support" in suit:
            matched = True
        elif attrs["has_gastrointestinal_symptoms"] and "digestive_distress" in suit:
            matched = True
        elif attrs["has_systemic_fatigue_or_fever"] and "general_fatigue" in suit and not is_dermatological:
            matched = True

        if matched:
            poses.append(posture)

    # Restorative postures only indicated if patient has systemic fatigue/fever and not dermatological
    if not poses and attrs["has_systemic_fatigue_or_fever"] and not is_dermatological:
        poses = [p for p in YOGA_POSTURE_REGISTRY if p["sanskrit_name"] in ["Balasana", "Shavasana", "Anulom Vilom"]]

    yoga_list = []
    for p in poses:
        image_path, is_fallback_img = resolve_image("yoga", p["sanskrit_name"])
        youtube_url = get_youtube_search_url(f"{p['name']} {p['sanskrit_name']}")
        yoga_list.append({
            "name": p["name"],
            "sanskrit_name": p["sanskrit_name"],
            "benefits": p["benefits"],
            "instructions": p["instructions"],
            "image": image_path,
            "is_fallback": is_fallback_img,
            "youtube_url": youtube_url
        })
    return yoga_list


def _build_local_dataset_fallback(
    symptoms: list,
    user_context: dict,
    top_condition: str = "",
    lang_code: str = "en"
) -> dict:
    """
    Builds a standardized clinical dataset fallback response with condition-specific guidance from CSV dataset.
    """
    sym_lower = " ".join(symptoms).lower()
    cond_lower = (top_condition or "").lower().strip()
    
    ft_after = "After Food" if lang_code == "en" else "भोजन के बाद" if lang_code == "hi" else "જમ્યા પછી"
    ft_before = "Before Food (Empty Stomach)" if lang_code == "en" else "भोजन से पहले (खाली पेट)" if lang_code == "hi" else "જમ્યા પહેલા (ખાલી પેટે)"
    ft_water = "With Water (Sip Throughout Day)" if lang_code == "en" else "पानी के साथ (दिन भर घूंट लें)" if lang_code == "hi" else "પાણી સાથે (દિવસ દરમિયાન)"

    attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition=top_condition, user_context=user_context)
    is_emergency = bool(attrs.get("has_emergency_red_flags") or user_context.get("is_emergency", False))

    fallback_meds = _get_condition_fallback_medicines(top_condition, symptoms, lang_code)
    med_gallery = get_medicine_gallery(fallback_meds, max_items=None, top_condition=top_condition, symptoms=symptoms)
    yoga_list = [] if is_emergency else _get_condition_fallback_yoga(top_condition, symptoms, lang_code)

    # Try condition-specific lookups from condition_guidance.csv
    csv_diet_tips = []
    csv_red_flags = []
    try:
        guidance_csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "datasets", "diet", "condition_guidance.csv")
        if os.path.exists(guidance_csv_path):
            import pandas as pd
            df_g = pd.read_csv(guidance_csv_path)
            cond_words = [w for w in re.findall(r'\b\w{4,}\b', cond_lower) if w not in ["disease", "syndrome", "acute", "chronic", "pain"]]
            matched_g = df_g[df_g["condition_name"].str.lower().apply(lambda x: any(w in str(x).lower() for w in cond_words))] if cond_words else df_g.head(0)
            if not matched_g.empty:
                row = matched_g.iloc[0]
                diet_rec = str(row.get("diet_recommendation", "")).strip()
                avoid_food = str(row.get("food_to_limit", "") or row.get("what_to_avoid", "")).strip()
                home_c = str(row.get("home_care", "") or row.get("what_to_do", "")).strip()
                mon_adv = str(row.get("monitoring_advice", "")).strip()
                
                if diet_rec:
                    csv_diet_tips.append(f"Recommended Nutrition: {diet_rec}")
                if avoid_food:
                    csv_diet_tips.append(f"Foods & Items to Avoid: {avoid_food}")
                if home_c:
                    csv_diet_tips.append(f"Home Management: {home_c}")
                if mon_adv:
                    csv_red_flags.append(f"Clinical Alert: {mon_adv}")
    except Exception as e:
        print(f"Condition guidance lookup notice: {e}")

    state = user_context.get("state") or user_context.get("location", "Gujarat")
    if "--" in state or "select" in state.lower():
        state = "Gujarat"
    seasonal_data = get_seasonal_health_context(state, lang_code=lang_code)

    attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition=top_condition, user_context=user_context)

    # 1. Fallback Injections / IV Fluids (Clinically gated)
    fb_injections = {"is_indicated": False, "items": [], "injections": []}
    dur_raw = str(user_context.get("duration", "")).lower().strip()
    is_short_duration = any(d in dur_raw for d in ["today", "1 - 3", "1-3", "1 to 3", "आज", "આજે"])

    has_animal_bite_exposure = any(k in cond_lower or k in sym_lower for k in [
        "animal bite", "dog bite", "monkey bite", "rabies", "animal saliva", "bite wound"
    ])
    has_contaminated_wound_exposure = any(k in cond_lower or k in sym_lower for k in [
        "tetanus", "deep cut", "puncture wound", "soil contamination", "rusty", "dirty wound", "contaminated laceration"
    ])
    has_severe_dehydration_shock = any(k in cond_lower or k in sym_lower for k in [
        "severe dehydration", "hypovolemia", "intractable vomiting", "persistent vomiting", "inability to retain fluids", "electrolyte collapse"
    ])
    has_refractory_severe_hyperpyrexia = (
        attrs["has_systemic_fatigue_or_fever"]
        and not is_short_duration
        and str(user_context.get("severity", "")).lower() == "severe"
    )

    if has_animal_bite_exposure:
        inj_items = [{
            "name": "Anti-Rabies Vaccine (Rabipur / Vaxirab N)",
            "dose": "1 Dose (0.5ml / 1.0ml)",
            "type": "Vaccine / Intramuscular",
            "route": "Intramuscular (IM - Deltoid)",
            "administration_setting": "Administer at Primary Health Centre / Hospital (Day 0, 3, 7, 14, 28)",
            "purpose": "Rabies post-exposure prophylaxis",
            "precautions": "Wash wound thoroughly with soap and water for 15 minutes before injection."
        }]
        fb_injections = {
            "is_indicated": True,
            "clinical_rationale": "Immediate post-exposure rabies prophylaxis is vital." if lang_code == "en" else "रेबीज से बचाव के लिए तत्काल एंटी-रेबीज इंजेक्शन आवश्यक है।" if lang_code == "hi" else "હડકવા સામે રક્ષણ માટે તાત્કાલિક એન્ટિ-રેબીઝ ઈન્જેક્શન જરૂરી છે.",
            "admin_setting": "Hospital / Clinic Administration Only",
            "items": inj_items,
            "injections": inj_items
        }
    elif has_contaminated_wound_exposure:
        inj_items = [{
            "name": "Tetanus Toxoid (TT 0.5ml) / Td Vaccine",
            "dose": "0.5ml Single Dose",
            "type": "Toxoid / Intramuscular",
            "route": "Intramuscular (IM)",
            "administration_setting": "Administered by healthcare worker within 24 hours of injury",
            "purpose": "Active immunization against tetanus",
            "precautions": "Verify booster history; use sterile disposable syringe."
        }]
        fb_injections = {
            "is_indicated": True,
            "clinical_rationale": "Prevents anaerobic Clostridium tetani infection." if lang_code == "en" else "टिटनेस के गंभीर संक्रमण से बचाव हेतु इंजेक्शन आवश्यक है।" if lang_code == "hi" else "ધનુર સામે રક્ષણ માટે ઇન્જેક્શન જરૂરી છે.",
            "admin_setting": "Hospital / Clinic Administration Only",
            "items": inj_items,
            "injections": inj_items
        }
    elif has_severe_dehydration_shock:
        inj_items = [
            {
                "name": "IV Normal Saline 0.9% (NS 500ml)",
                "dose": "500ml IV Infusion",
                "type": "Intravenous Infusion",
                "route": "Intravenous (IV Drip)",
                "administration_setting": "Administer at Hospital / Day Care Centre",
                "purpose": "Rapid volume resuscitation and rehydration",
                "precautions": "Monitor infusion rate and urine output."
            },
            {
                "name": "Inj. Ondansetron 4mg/2ml (Emeset)",
                "dose": "4mg IV Slow",
                "type": "Antiemetic Injectable",
                "route": "Intravenous (IV Slow)",
                "administration_setting": "Hospital / Clinic",
                "purpose": "Controls persistent nausea and vomiting",
                "precautions": "Administer over 2 to 5 minutes."
            }
        ]
        fb_injections = {
            "is_indicated": True,
            "clinical_rationale": "Immediate fluid and electrolyte restoration." if lang_code == "en" else "गंभीर निर्जलीकरण रोकने हेतु IV ड्रिप आवश्यक है।" if lang_code == "hi" else "તીવ્ર ડિહાઇડ્રેશન રોકવા માટે IV ફ્લૂઇડ જરૂરી છે.",
            "admin_setting": "Hospital / Clinic Administration Only",
            "items": inj_items,
            "injections": inj_items
        }
    elif has_refractory_severe_hyperpyrexia:
        inj_items = [{
            "name": "Inj. Paracetamol IV Infusion (100ml / 1000mg)",
            "dose": "1000mg IV Infusion slowly over 15 minutes",
            "type": "Antipyretic IV Infusion",
            "route": "Intravenous (IV)",
            "administration_setting": "Hospital / Day Care Unit",
            "purpose": "Rapid antipyresis for refractory prolonged high fever",
            "precautions": "Administer under physician supervision; monitor liver function."
        }]
        fb_injections = {
            "is_indicated": True,
            "clinical_rationale": "Indicated for prolonged severe fever unresponsive to oral antipyretics." if lang_code == "en" else "मौखिक दवाओं से न उतरने वाले लंबे समय के गंभीर बुखार के लिए अस्पताल में आई.वी. इन्फ्यूजन।" if lang_code == "hi" else "ઓરલ દવાઓથી કાબૂમાં ન આવતા લાંબા તાવ માટે હોસ્પિટલમાં IV ઇન્ફ્યુઝન.",
            "admin_setting": "Hospital / Clinic Administration Only",
            "items": inj_items,
            "injections": inj_items
        }

    # 2. Fallback Compress Guidance (Physiologically Gated by Clinical Attributes)
    if attrs.get("is_febrile_hyperpyrexia"):
        compress_info = {
            "is_indicated": True,
            "mode": "cold_sponging",
            "title": "माथे व शरीर पर ठंडे पानी की पट्टी (Tepid / Cold Sponging) करें" if lang_code == "hi" else ("માથા પર સામાન્ય ઠંડા પાણીની પટ્ટી (Cold Sponging) મૂકો" if lang_code == "gu" else "Tepid / Cold Sponge Compress Recommended"),
            "instructions": "सामान्य नल के पानी में सूती कपड़ा भिगोकर निचोड़ें और माथे, गर्दन व बगलों पर रखें। यह बुखार को सुरक्षित रूप से कम करता है।" if lang_code == "hi" else ("સામાન્ય ઠંડા પાણીમાં સુતરાઉ કપડું પલાળીને માથા અને ગળા પર મૂકો. તેનાથી તાવ ઝડપથી નિયંત્રિત થાય છે." if lang_code == "gu" else "Dip a clean cotton towel in cool tap water, wring gently, and place across forehead, neck, and axillae to dissipate body heat."),
            "duration": "10–15 minutes every 2–3 hours as needed.",
            "duration_and_frequency": "10–15 minutes every 2–3 hours as needed.",
            "cautions": "Do NOT apply freezing ice directly to the skin. Avoid warm fomentation during active fever.",
            "precautions": "Do NOT apply freezing ice directly to the skin. Avoid warm fomentation during active fever."
        }
    elif attrs.get("is_acute_inflammatory_edema"):
        compress_info = {
            "is_indicated": True,
            "mode": "ice",
            "title": "बर्फ की सिकाई (Cold / Ice Pack Compress)" if lang_code == "hi" else ("બરફનો શેક (Ice Compress)" if lang_code == "gu" else "Cold / Ice Pack Compress Recommended"),
            "instructions": "बर्फ को कपड़े में लपेटकर प्रभावित जोड़ या सूजन वाली जगह पर 10-15 मिनट लगाएं।" if lang_code == "hi" else ("બરફને કપડામાં વીંટાળીને સોજાવાળા ભાગ પર 10-15 મિનિટ રાખો." if lang_code == "gu" else "Apply an ice pack wrapped in a clean cloth to the injured area to constrict blood vessels and reduce inflammatory edema."),
            "duration": "15 minutes, 3 to 4 times daily for the first 48 hours.",
            "duration_and_frequency": "15 minutes, 3 to 4 times daily for the first 48 hours.",
            "cautions": "Never apply bare ice directly to skin to avoid cold injury.",
            "precautions": "Never apply bare ice directly to skin to avoid cold injury."
        }
    elif attrs.get("is_chronic_musculoskeletal_stiffness"):
        compress_info = {
            "is_indicated": True,
            "mode": "hot",
            "title": "गर्म पानी की सिकाई (Warm / Hot Fomentation)" if lang_code == "hi" else ("ગરમ પાણીનો શેક (Hot Fomentation)" if lang_code == "gu" else "Warm / Hot Fomentation Recommended"),
            "instructions": "गर्म पानी की थैली (Hot water bag) या हीटिंग पैड से मांसपेशियों की सिकाई करें।" if lang_code == "hi" else ("ગરમ પાણીની કોથળી અથવા હીટિંગ પેડથી સ્નાયુઓનો હળવો શેક કરો." if lang_code == "gu" else "Apply a warm water bottle or heating pad to tight muscle groups to increase local vascular circulation and relieve stiffness."),
            "duration": "15–20 minutes, 2 times daily.",
            "duration_and_frequency": "15–20 minutes, 2 times daily.",
            "cautions": "Ensure temperature is comfortable to avoid skin burns.",
            "precautions": "Ensure temperature is comfortable to avoid skin burns."
        }
    else:
        compress_info = {"is_indicated": False, "mode": "none"}

    # 3. Fallback Physiotherapy & Rehabilitation (Physiologically Gated)
    fb_physio = {"is_indicated": False, "exercises": []}
    if attrs["has_musculoskeletal_symptoms"] and not attrs["has_emergency_red_flags"] and not is_emergency:
        fb_physio = {
            "is_indicated": True,
            "condition_target": "Spine & Joint Mobility & Core Stabilization",
            "clinical_rationale": "Spinal mobility and core strengthening relieve nerve compression and muscular spasm.",
            "cautions": "Stop immediately if sharp radiating pain occurs.",
            "exercises": [
                {
                    "name": "Cat-Cow Gentle Spinal Flexion & Extension",
                    "focus": "Lumbar & Thoracic Spine",
                    "target_area": "Lumbar & Thoracic Spine",
                    "reps": "10 slow cycles",
                    "description": "On all fours, gently round your back towards ceiling on exhale, then gently arch on inhale.",
                    "instructions": "On all fours, gently round your back towards ceiling on exhale, then gently arch on inhale.",
                    "caution": "Stop immediately if sharp shooting pain radiates down legs.",
                    "youtube_search_url": get_youtube_search_url("Cat Cow stretch physiotherapy tutorial"),
                    "youtube_url": get_youtube_search_url("Cat Cow stretch physiotherapy tutorial")
                },
                {
                    "name": "Pelvic Tilts & Bridge Exercise",
                    "focus": "Core & Gluteal Muscle Groups",
                    "target_area": "Core & Gluteal Muscle Groups",
                    "reps": "8 to 10 repetitions",
                    "description": "Lie on back with knees bent, tighten abdominal core, and gently lift pelvis.",
                    "instructions": "Lie on back with knees bent, tighten abdominal core, and gently lift pelvis.",
                    "caution": "Avoid hyper-extending the lower back.",
                    "youtube_search_url": get_youtube_search_url("Pelvic tilt physiotherapy tutorial"),
                    "youtube_url": get_youtube_search_url("Pelvic tilt physiotherapy tutorial")
                }
            ]
        }

    # 4. Fallback Specialized Clinical Therapies (Clinically Gated by Attributes)
    fb_specialized = {"is_indicated": False, "therapies": []}
    has_oncological_indications = attrs.get("has_oncological_indications", False)
    has_renal_failure_indications = attrs.get("has_renal_failure_indications", False)
    has_severe_bronchospasm_indications = attrs.get("has_bronchospasm_indications", False)

    if has_oncological_indications:
        ov_text = "Malignant diseases require histological grading, staging (PET-CT), and individualized systemic chemotherapy or targeted biologics under tertiary oncology centre protocol." if lang_code == "en" else "कैंसर की स्थिति में ऑन्कोलॉजिस्ट की देखरेख में कीमोथेरेपी, रेडियोथेरेपी या इम्यूनोथेरेपी का विशेष अस्पताल आधारित प्रोटोकॉल दिया जाता है।" if lang_code == "hi" else "કેન્સરના કિસ્સામાં કેન્સર નિષ્ણાત (ઓન્કોલોજિસ્ટ) ની દેખરેખ હેઠળ કીમોથેરાપી અને વિશિષ્ટ હોસ્પિટલ સારવાર આપવામાં આવે છે."
        fb_specialized = {
            "is_indicated": True,
            "therapy_name": "Chemotherapy & Medical Oncology Regimen (कीमोथेरेपी)",
            "specialist_type": "Medical Oncologist & Comprehensive Cancer Care Team",
            "specialist_consult": "Medical Oncologist & Comprehensive Cancer Care Team",
            "overview": ov_text,
            "patient_guidance": "Strict neutropenic dietary hygiene, high protein intake, infection avoidance, and prompt hospital reporting for any fever >100.4°F.",
            "therapies": [{
                "name": "Chemotherapy & Medical Oncology Regimen",
                "category": "Tertiary Oncology Care",
                "setting": "Comprehensive Cancer Centre / Day Care Chemotherapy Ward",
                "description": ov_text
            }]
        }
    elif has_renal_failure_indications:
        ov_text = "Renal replacement therapy (Hemodialysis) filters metabolic waste and excess fluid when renal clearance falls below critical clinical levels."
        fb_specialized = {
            "is_indicated": True,
            "therapy_name": "Hemodialysis & Nephrological Management (डायलिसिस)",
            "specialist_type": "Consultant Nephrologist",
            "specialist_consult": "Consultant Nephrologist",
            "overview": ov_text,
            "patient_guidance": "Strict daily fluid and sodium restriction, low potassium diet, and regular AV fistula monitoring.",
            "therapies": [{
                "name": "Maintenance Hemodialysis (HD)",
                "category": "Renal Replacement Therapy",
                "setting": "Hospital Dialysis Unit / Nephrology Ward",
                "description": ov_text
            }]
        }
    elif has_severe_bronchospasm_indications:
        ov_text = "Aerosolized bronchodilator nebulization relieves acute bronchospasm and restores airflow in reactive airway diseases."
        fb_specialized = {
            "is_indicated": True,
            "therapy_name": "Nebulization & Inhalation Bronchodilator Therapy (नेबुलाइज़र)",
            "specialist_type": "Pulmonologist / Chest Physician",
            "specialist_consult": "Pulmonologist / Chest Physician",
            "overview": ov_text,
            "patient_guidance": "Rinse mouth after inhalation therapy; maintain peak flow tracking.",
            "therapies": [{
                "name": "Emergency Bronchodilator Nebulization (Levosalbutamol + Ipratropium)",
                "category": "Respiratory Therapy",
                "setting": "Emergency Ward / Outpatient Clinic",
                "description": ov_text
            }]
        }

    # Fallback Warning Message, Dietary & Clinical Care
    if lang_code == "hi":
        warning_msg = " [ऑफलाइन क्लिनिकल डेटासेट मोड]: लाइव AI API से संपर्क नहीं हो सका। मानकीकृत स्थानीय डेटासेट से डेटा दिखाया जा रहा है।"
        recovery_txt = f"5 – 7 दिन ({top_condition or 'लक्षणों'} के लिए उचित दवा, पर्याप्त आराम और तरल पदार्थों के सेवन के साथ)।"
        summary_txt = f"क्लिनिकल विश्लेषण के अनुसार लक्षण {top_condition or 'संक्रमण'} की ओर संकेत करते हैं। पर्याप्त विश्राम और समय पर दवा लेने की सलाह दी जाती है।"
        foods_to_eat = [
            f"{top_condition or 'बीमारी'} में सुपाच्य और पौष्टिक भोजन जैसे मूंग दाल की खिचड़ी, दलिया या सूप लें।",
            "ताजे फल, उबली सब्जियां और पर्याप्त प्रोटीन युक्त आहार लें।",
            "नारियल पानी, ओआरएस और गुनगुने तरल पदार्थों का सेवन करें।"
        ]
        foods_to_avoid = [
            "तेल-मसालेदार, तले हुए और भारी गरिष्ठ भोजन से बचें।",
            "अत्यधिक कैफीन, जंक फूड और पैकेट बंद मीठे पेय पदार्थों से परहेज करें।"
        ]
        hyd_advice = "प्रतिदिन 2.5 से 3 लीटर साफ गुनगुना पानी या ओआरएस घोल पिएं।"
        clinical_dos = [
            "सभी दवाएं डॉक्टर या फार्मासिस्ट के निर्देशानुसार सही समय पर लें।",
            "शरीर को 7-8 घंटे का पर्याप्त विश्राम दें और तनाव से बचें।",
            "प्रतिदिन शारीरिक तापमान और लक्षणों में बदलाव पर नजर रखें।"
        ]
        clinical_donts = [
            "बिना डॉक्टर की सलाह के दवाओं की खुराक खुद से न बदलें।",
            "संक्रमण के दौरान अत्यधिक शारीरिक श्रम या बाहर जाने से बचें।",
            "लगातार तेज़ बुखार या सांस की तकलीफ को बिल्कुल नजरअंदाज न करें।"
        ]
        red_flags = csv_red_flags if csv_red_flags else [
            "लगातार 3 दिन से अधिक 103°F से तेज़ बुखार रहना या लक्षणों का बिगड़ना।",
            "सांस लेने में कठिनाई, सीने में दर्द या अत्यधिक कमजोरी।",
            "तरल पदार्थ न पचना या डिहाइड्रेशन के गंभीर लक्षण दिखना।"
        ]
    elif lang_code == "gu":
        warning_msg = " [ઓફલાઇન ક્લિનિકલ ડેટાસેટ મોડ]: લાઈવ AI API કનેક્ટ થઈ શક્યું નથી. સ્થાનિક પ્રમાણિત ડેટાસેટ દર્શાવવામાં આવી રહ્યું છે."
        recovery_txt = f"5 – 7 દિવસ ({top_condition or 'લક્ષણો'} માટે સાચી દવા, પૂરતો આરામ અને પ્રવાહીના સેવન સાથે)."
        summary_txt = f"ક્લિનિકલ વિશ્લેષણ મુજબ લક્ષણો {top_condition or 'ચેપ / સંક્રમણ'} સૂચવે છે. પૂરતો આરામ અને સમયસર દવા લેવાની ભલામણ કરવામાં આવે છે."
        foods_to_eat = [
            f"{top_condition or 'રિકવરી'} દરમિયાન સરળતાથી પચી જાય તેવો હળવો ખોરાક જેમ કે મગની દાળની ખીચડી, રાબ અને સૂપ લો.",
            "તાજા મોસમી ફળો અને પ્રોટીનયુક્ત આહારનું સેવન કરો.",
            "નાળિયેર પાણી, ઓઆરએસ અને ગરમ પ્રવાહીથી હાઇડ્રેશન જાળવી રાખો."
        ]
        foods_to_avoid = [
            "તળેલો, વધુ મસાલેદાર, ભારે અને બહારનો બિનઆરોગ્યપ્રદ ખોરાક ટાળો.",
            "વધુ પડતી ખાંડવાળા પીણાં અને ઠંડી વસ્તુઓથી દૂર રહો."
        ]
        hyd_advice = "દરરોજ 2.5 થી 3 લિટર ચોખ્ખું નવશેકું પાણી અથવા પ્રવાહીનું સેવન કરો."
        clinical_dos = [
            "દવાઓ નિયમિતપણે અને યોગ્ય માત્રામાં જમ્યા પછી/પહેલાં લો.",
            "શરીરને પૂરતો આરામ આપો અને તણાવ મુક્ત રહો.",
            "દરરોજ શરીરનું તાપમાન અને લક્ષણોમાં સુધારો નોંધો."
        ]
        clinical_donts = [
            "ડૉક્ટરની સલાહ વિના જાતે દવાઓ બંધ કે બદલશો નહીં.",
            "બીમારી દરમિયાન વધુ પડતો શારીરિક શ્રમ કરવાનું ટાળો.",
            "તીવ્ર તાવ, શ્વાસની તકલીફ કે છાતીમાં દુખાવાને અવગણશો નહીં."
        ]
        red_flags = csv_red_flags if csv_red_flags else [
            "સતત 3 દિવસથી વધુ સમય માટે 103°F થી વધુ તાવ રહેવો અથવા લક્ષણો વધવા.",
            "શ્વાસ લેવામાં તકલીફ, છાતીમાં દુખાવો અથવા અતિશય નબળાઈ.",
            "પ્રવાહી પચી ન શકવું અથવા ડિહાઇડ્રેશનના ગંભીર લક્ષણો જણાવા."
        ]
    else:
        warning_msg = " [Offline Clinical Dataset Fallback Active]: Live AI APIs could not be reached. Displaying standardized local clinical dataset."
        recovery_txt = f"Expected recovery is 5 – 7 days for {top_condition or 'acute condition'} with adequate rest, hydration, and proper therapy."
        summary_txt = f"Clinical triage shows symptoms aligning with {top_condition or 'acute illness'}. Prompt hydration and symptomatic management indicated."
        foods_to_eat = [
            f"Eat freshly prepared, nutrient-dense, easily digestible meals (khichdi, oats, clear vegetable soups) for {top_condition or 'recovery'}.",
            "Include fresh Vitamin C-rich fruits and lean protein to support cellular healing.",
            "Drink oral rehydration solutions, coconut water, or warm broths."
        ]
        foods_to_avoid = [
            "Avoid deep-fried, heavily spiced, greasy, and ultra-processed foods.",
            "Avoid unpasteurized dairy, raw undercooked meats, and excessive refined sugars."
        ]
        hyd_advice = "Drink 2.5 – 3.0 Liters of clean water or warm fluids daily."
        clinical_dos = [
            "Take all prescribed medications strictly as directed with proper food timings.",
            "Ensure 7 – 9 hours of restful sleep to optimize immune recovery.",
            "Track daily body temperature and symptom progression."
        ]
        clinical_donts = [
            "Do NOT alter or stop prescribed medication courses prematurely without consulting your doctor.",
            "Avoid strenuous physical exertion and crowded places during recovery.",
            "Do NOT ignore worsening chest pain, acute shortness of breath, or persistent high fever."
        ]
        red_flags = csv_red_flags if csv_red_flags else [
            f"Worsening of {top_condition or 'symptoms'} or persistent high fever exceeding 103°F.",
            "Shortness of breath, chest pain, or sudden confusion/dizziness.",
            "Inability to retain liquids or severe signs of dehydration."
        ]

    if is_emergency:
        emergency_notice = "CRITICAL EMERGENCY ALERT: Clinical findings indicate a possible medical emergency requiring urgent in-person medical evaluation. Routine exercise and home management are suspended. "
        summary_txt = emergency_notice + summary_txt
        red_flags = ["URGENT EMERGENCY EVALUATION REQUIRED: Report immediately to an Emergency Department."] + [r for r in red_flags if "EMERGENCY EVALUATION" not in r]

    return {
        "is_fallback": True,
        "is_live": False,
        "fallback_used": True,
        "api_source": "Local Clinical Dataset (Offline Fallback)",
        "ai_provider_used": None,
        "fallback_warning": warning_msg,
        "top_condition": top_condition,
        "lang_code": lang_code,
        "state": state,
        "is_emergency": is_emergency,
        "summary": summary_txt,
        "recovery_duration": recovery_txt,
        "seasonal_context": seasonal_data,
        "seasonal_alert": {
            "is_active": True,
            "title": seasonal_data["alert_title"],
            "message": seasonal_data["alert_description"]
        },
        "medicine_gallery": med_gallery,
        "total_medicines_recommended": len(med_gallery),
        "injections_and_iv": fb_injections,
        "compress_guidance": compress_info,
        "cold_warm_compress_mode": compress_info.get("mode", "none"),
        "cold_warm_compress_indicated": compress_info.get("is_indicated", False),
        "physiotherapy_guidance": fb_physio,
        "specialized_therapies": fb_specialized,
        "yoga_recommendations": yoga_list,
        "dietary_guidelines": foods_to_eat,
        "foods_to_eat": foods_to_eat,
        "foods_to_avoid": foods_to_avoid,
        "hydration_advice": hyd_advice,
        "clinical_dos": clinical_dos,
        "clinical_donts": clinical_donts,
        "red_flags": red_flags
    }


def get_yoga_recommendation(disease_name: str = "", symptoms: list = None) -> dict | None:
    """
    Helper for legacy standalone yoga recommendation lookup.
    """
    from api.yoga_api import search_yoga_pose
    pose_name = "Child's Pose"
    sans_name = "Balasana"
    benefits = "Gently relaxes spine and calms the autonomic nervous system."
    img, is_fb = resolve_image("yoga", pose_name)
    return {
        "name": pose_name,
        "sanskrit_name": sans_name,
        "benefits": benefits,
        "image": img,
        "is_fallback": is_fb,
        "youtube_url": get_youtube_search_url(f"{pose_name} {sans_name}")
    }


def get_compress_guidance(disease_name: str = "", symptoms: list = None, lang_code: str = "en") -> dict | None:
    """
    Helper for legacy standalone compress guidance lookup.
    """
    return {
        "mode": "ice",
        "title": "Cold / Tepid Sponge Compress",
        "text": "Apply a damp, cool cloth to the forehead and neck to safely bring down elevated body temperature."
    }


def localize_care_recommendations(care_res: dict, target_lang_code: str) -> dict:
    """
    Translates textual clinical fields of an existing care recommendation into the target language
    while strictly locking and preserving the exact same medicines (gallery items), dosages, and yoga routines.
    """
    if not care_res or not isinstance(care_res, dict):
        return care_res

    current_lang = care_res.get("lang_code", "en")
    if current_lang == target_lang_code:
        return care_res

    _LANG_NAME_MAP = {
        "en": "English",
        "hi": "Hindi (हिंदी)",
        "gu": "Gujarati (ગુજરાતી)",
        "mr": "Marathi (मराठी)",
        "bn": "Bengali (বাংলা)",
        "ta": "Tamil (தமிழ்)",
        "te": "Telugu (తెలుగు)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "ml": "Malayalam (മലയാളം)",
        "pa": "Punjabi (ਪੰਜਾਬੀ)",
        "or": "Odia (ଓଡ଼ିଆ)",
        "ur": "Urdu (اردو)",
    }
    lang_name = _LANG_NAME_MAP.get(target_lang_code, target_lang_code.title())

    # Update seasonal context
    st_val = care_res.get("state") or "Gujarat"
    seasonal_data = get_seasonal_health_context(st_val, lang_code=target_lang_code)
    care_res["seasonal_context"] = seasonal_data
    care_res["seasonal_alert"] = {
        "is_active": True,
        "title": seasonal_data["alert_title"],
        "message": seasonal_data["alert_description"]
    }

    # Food timing translation — all 12 supported languages
    ft_map = {
        "en": {"after": "After Food", "before": "Before Food (Empty Stomach)", "water": "With Water (Sip Throughout Day)"},
        "hi": {"after": "भोजन के बाद", "before": "भोजन से पहले (खाली पेट)", "water": "पानी के साथ (दिन भर घूंट लें)"},
        "gu": {"after": "જમ્યા પછી", "before": "જમ્યા પહેલા (ખાલી પેટે)", "water": "પાણી સાથે (દિવસ દરમ્યાન)"},
        "mr": {"after": "जेवणानंतर", "before": "जेवणापूर्वी (रिकाम्या पोटी)", "water": "पाण्यासोबत (दिवसभर)"},
        "bn": {"after": "খাওয়ার পরে", "before": "খাওয়ার আগে (খালি পেটে)", "water": "জলের সাথে (সারাদিন)"},
        "ta": {"after": "சாப்பிட்ட பிறகு", "before": "சாப்பிடுவதற்கு முன்பு (வெறும் வயிற்றில்)", "water": "தண்ணீருடன் (நாள் முழுவதும்)"},
        "te": {"after": "భోజనం తర్వాత", "before": "భోజనానికి ముందు (ఖాళీ కడుపుతో)", "water": "నీటితో (రోజంతా)"},
        "kn": {"after": "ಊಟದ ನಂತರ", "before": "ಊಟಕ್ಕೂ ಮುನ್ನ (ಖಾಲಿ ಹೊಟ್ಟೆಯಲ್ಲಿ)", "water": "ನೀರಿನೊಂದಿಗೆ (ದಿನವಿಡೀ)"},
        "ml": {"after": "ഭക്ഷണത്തിനു ശേഷം", "before": "ഭക്ഷണത്തിനു മുമ്പ് (ശൂന്യ ഉദരത്തിൽ)", "water": "വെള്ളത്തോടൊപ്പം (ദിവസം മുഴുവൻ)"},
        "pa": {"after": "ਖਾਣੇ ਤੋਂ ਬਾਅਦ", "before": "ਖਾਣੇ ਤੋਂ ਪਹਿਲਾਂ (ਖਾਲੀ ਪੇਟ)", "water": "ਪਾਣੀ ਨਾਲ (ਪੂਰਾ ਦਿਨ)"},
        "or": {"after": "ଖାଇବା ପରେ", "before": "ଖାଇବା ପୂର୍ବରୁ (ଖାଲି ପେଟ)", "water": "ପାଣି ସହ (ଦିନ ସାରା)"},
        "ur": {"after": "کھانے کے بعد", "before": "کھانے سے پہلے (خالی پیٹ)", "water": "پانی کے ساتھ (دن بھر)"},
    }
    target_ft = ft_map.get(target_lang_code, ft_map["en"])
    for med in care_res.get("medicine_gallery", []):
        old_ft = str(med.get("food_timing", "")).lower()
        if "before" in old_ft or "खाली" in old_ft or "પહેલા" in old_ft or "pehle" in old_ft:
            med["food_timing"] = target_ft["before"]
        elif "water" in old_ft or "पानी" in old_ft or "પાણી" in old_ft:
            med["food_timing"] = target_ft["water"]
        else:
            med["food_timing"] = target_ft["after"]

    # Bundle text items to translate
    items_to_translate = {
        "summary": care_res.get("summary", ""),
        "recovery_duration": care_res.get("recovery_duration", ""),
        "hydration_advice": care_res.get("hydration_advice", ""),
        "foods_to_eat": care_res.get("foods_to_eat", []),
        "foods_to_avoid": care_res.get("foods_to_avoid", []),
        "clinical_dos": care_res.get("clinical_dos", []),
        "clinical_donts": care_res.get("clinical_donts", []),
        "red_flags": care_res.get("red_flags", []),
        "med_indications": [m.get("indication", "") for m in care_res.get("medicine_gallery", [])],
        "yoga_benefits": [y.get("benefits", "") for y in care_res.get("yoga_recommendations", [])]
    }

    trans_prompt = f"""You are DocMindX Medical Localization AI.
Translate this clinical care JSON dictionary from {current_lang} into 100% pure {lang_name} ({target_lang_code}).
CRITICAL RULES:
1. All text MUST be strictly in {lang_name} script without mixing other languages.
2. Return STRICT JSON with identical keys.

Bundle to translate:
{json.dumps(items_to_translate, ensure_ascii=False)}
"""
    translated_bundle = None
    if gemini_pool.get_active_keys():
        try:
            trans_payload = {
                "contents": [{"parts": [{"text": trans_prompt}]}],
                "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
            }
            res_data, _, _ = gemini_pool.execute_with_failover(
                payload=trans_payload,
                models=["gemini-3.6-flash", "gemini-3.5-flash-lite"],
                timeout=10
            )
            if res_data:
                candidates = res_data.get("candidates", [])
                if candidates:
                    raw_t = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    translated_bundle = _clean_json_response(raw_t)
        except Exception as e:
            print(f"Gemini localization notice: {e}")

    if not translated_bundle and GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            body = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Translate all medical text into 100% pure {lang_name}. Output strict JSON only."},
                    {"role": "user", "content": trans_prompt}
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8)
            if res.status_code == 200:
                raw_t = res.json()["choices"][0]["message"]["content"]
                translated_bundle = _clean_json_response(raw_t)
        except Exception as e:
            print(f"Groq localization notice: {e}")

    if translated_bundle and isinstance(translated_bundle, dict):
        if translated_bundle.get("summary"):
            care_res["summary"] = translated_bundle["summary"]
        if translated_bundle.get("recovery_duration"):
            care_res["recovery_duration"] = translated_bundle["recovery_duration"]
        if translated_bundle.get("hydration_advice"):
            care_res["hydration_advice"] = translated_bundle["hydration_advice"]
        if translated_bundle.get("foods_to_eat"):
            care_res["foods_to_eat"] = translated_bundle["foods_to_eat"]
        if translated_bundle.get("foods_to_avoid"):
            care_res["foods_to_avoid"] = translated_bundle["foods_to_avoid"]
        if translated_bundle.get("clinical_dos"):
            care_res["clinical_dos"] = translated_bundle["clinical_dos"]
        if translated_bundle.get("clinical_donts"):
            care_res["clinical_donts"] = translated_bundle["clinical_donts"]
        if translated_bundle.get("red_flags"):
            care_res["red_flags"] = translated_bundle["red_flags"]

        med_inds = translated_bundle.get("med_indications", [])
        if isinstance(med_inds, list):
            for idx, med in enumerate(care_res.get("medicine_gallery", [])):
                if idx < len(med_inds) and med_inds[idx]:
                    med["indication"] = med_inds[idx]

        yoga_bens = translated_bundle.get("yoga_benefits", [])
        if isinstance(yoga_bens, list):
            for idx, y in enumerate(care_res.get("yoga_recommendations", [])):
                if idx < len(yoga_bens) and yoga_bens[idx]:
                    y["benefits"] = yoga_bens[idx]

    care_res["lang_code"] = target_lang_code
    return care_res
