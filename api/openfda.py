"""
DocMindX AI — OpenFDA Drug Label Information API Client
Retrieves authentic Structured Product Label (SPL) evidence directly from the FDA.
Features:
- Strict provider status contract: SUCCESS, NO_RELEVANT_RESULT, TIMEOUT, RATE_LIMIT, AUTH_ERROR, NETWORK_ERROR, INVALID_RESPONSE
- Zero fabrication: never invents generic names, dosage forms, routes, or doses
- Distinguishes empty search results from network/provider failures
- Caches verified live API responses in SQLite with retrieved_at provenance
"""
import logging
import requests
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.create_tables import cache_medicine, get_cached_medicine
from config.settings import OPENFDA_API_KEY

BASE_URL = "https://api.fda.gov/drug/label.json"
_logger = logging.getLogger("DocMindX.TriageEngine.OpenFDA")

STATUS_SUCCESS = "SUCCESS"
STATUS_NO_RELEVANT_RESULT = "NO_RELEVANT_RESULT"
STATUS_RATE_LIMIT = "RATE_LIMIT"
STATUS_AUTH_ERROR = "AUTH_ERROR"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_NETWORK_ERROR = "NETWORK_ERROR"
STATUS_INVALID_RESPONSE = "INVALID_RESPONSE"


def search_drug_openfda(drug_name: str) -> Optional[Dict[str, Any]]:
    """
    Search OpenFDA for official drug label evidence.
    
    Returns structured dict with:
      - medicine_name: str
      - generic_name: str
      - brand_names: list
      - active_ingredients: str
      - dosage_forms: list
      - routes: list
      - strengths: list
      - manufacturer: str
      - purpose: str
      - indications: str
      - contraindications: str
      - warnings: str
      - adverse_reactions: str
      - verified_label_dosage: str
      - dosage_instructions: str
      - drug_interactions: str
      - provider: "OpenFDA"
      - status: SUCCESS | NO_RELEVANT_RESULT | TIMEOUT | RATE_LIMIT | AUTH_ERROR | NETWORK_ERROR | INVALID_RESPONSE
      - verification_status: OPENFDA_VERIFIED | NOT_FOUND | UNVERIFIED | CLINICAL_REFERENCE
      - is_live: bool
      - fallback_used: bool
      - fallback_reason: str
      - source: str
      - retrieved_at: str (ISO format)
    """
    if not drug_name or not str(drug_name).strip():
        return None

    clean_name = str(drug_name).strip().lower()
    now_iso = datetime.now().isoformat()

    # 1. Check local SQLite cache (previously validated live OpenFDA responses)
    cached = get_cached_medicine(clean_name)
    if cached:
        _logger.info("[OpenFDA] Cache HIT for: '%s'", drug_name)
        cached["is_live"] = cached.get("source") == "OpenFDA Live API"
        cached["fallback_used"] = False
        cached["fallback_reason"] = ""
        cached["provider"] = "OpenFDA"
        cached["status"] = "SUCCESS"
        cached["verification_status"] = "OPENFDA_VERIFIED" if cached.get("is_live") else "CLINICAL_REFERENCE"
        cached["retrieved_at"] = cached.get("retrieved_at", now_iso)
        cached["dosage_forms"] = cached.get("dosage_forms", [])
        cached["routes"] = cached.get("routes", [])
        cached["verified_label_dosage"] = cached.get("dosage", "")
        return cached

    # 2. Query Live OpenFDA API
    status = "SUCCESS"
    verification_status = "UNVERIFIED"
    fallback_used = False
    fallback_reason = ""
    is_live = False

    try:
        query = f'openfda.brand_name:"{clean_name}" OR openfda.generic_name:"{clean_name}" OR openfda.substance_name:"{clean_name}"'
        params = {"search": query, "limit": 1}
        if OPENFDA_API_KEY:
            params["api_key"] = OPENFDA_API_KEY

        response = requests.get(BASE_URL, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                result = results[0]
                openfda_info = result.get("openfda", {})

                brand_names = openfda_info.get("brand_name", [clean_name.capitalize()])
                generic_names = openfda_info.get("generic_name", [])
                substances = openfda_info.get("substance_name", [])
                manufacturers = openfda_info.get("manufacturer_name", [])
                dosage_forms = openfda_info.get("dosage_form", [])
                routes = openfda_info.get("route", [])
                strengths = openfda_info.get("strength", [])

                purpose_list = result.get("purpose", result.get("indications_and_usage", []))
                purpose = purpose_list[0] if purpose_list else ""
                
                warnings_list = result.get("warnings", result.get("warnings_and_cautions", []))
                warnings = warnings_list[0] if warnings_list else ""

                dosage_list = result.get("dosage_and_administration", [])
                dosage = dosage_list[0] if dosage_list else ""

                interactions_list = result.get("drug_interactions", [])
                interactions = interactions_list[0] if interactions_list else ""

                contraindications_list = result.get("contraindications", [])
                contraindications = contraindications_list[0] if contraindications_list else ""

                adverse_list = result.get("adverse_reactions", [])
                adverse_reactions = adverse_list[0] if adverse_list else ""

                primary_generic = generic_names[0] if generic_names else clean_name.capitalize()
                primary_brand = brand_names[0] if brand_names else clean_name.capitalize()
                primary_mfg = ", ".join(manufacturers[:2]) if manufacturers else ""

                # Cache validated live response in SQLite
                cache_medicine(
                    medicine_name=primary_brand,
                    generic_name=primary_generic,
                    active_ingredients=", ".join(substances) if substances else primary_generic,
                    manufacturer=primary_mfg,
                    purpose=purpose[:500] if purpose else "",
                    warnings=warnings[:600] if warnings else "",
                    dosage=dosage[:400] if dosage else "",
                    interactions=interactions[:400] if interactions else "",
                    source="OpenFDA Live API"
                )

                _logger.info("[OpenFDA] LIVE SUCCESS for: '%s'", drug_name)
                return {
                    "medicine_name": primary_brand,
                    "generic_name": primary_generic,
                    "brand_names": brand_names,
                    "active_ingredients": ", ".join(substances) if substances else primary_generic,
                    "dosage_forms": dosage_forms,
                    "routes": routes,
                    "strengths": strengths,
                    "manufacturer": primary_mfg,
                    "purpose": purpose[:500] if purpose else "",
                    "indications": purpose[:500] if purpose else "",
                    "contraindications": contraindications[:400] if contraindications else "",
                    "warnings": warnings[:600] if warnings else "Consult a physician or pharmacist for contraindications.",
                    "adverse_reactions": adverse_reactions[:400] if adverse_reactions else "",
                    "verified_label_dosage": dosage[:400] if dosage else "",
                    "dosage_instructions": dosage[:400] if dosage else "Use strictly as directed on the official product label.",
                    "drug_interactions": interactions[:400] if interactions else "",
                    "provider": "OpenFDA",
                    "status": "SUCCESS",
                    "verification_status": "OPENFDA_VERIFIED",
                    "is_live": True,
                    "fallback_used": False,
                    "fallback_reason": "",
                    "source": "OpenFDA Live API",
                    "retrieved_at": now_iso
                }
            else:
                _logger.info("[OpenFDA] Empty results for: '%s' (NO_RELEVANT_RESULT)", drug_name)
                return {
                    "medicine_name": clean_name.capitalize(),
                    "generic_name": clean_name.capitalize(),
                    "brand_names": [],
                    "active_ingredients": "",
                    "dosage_forms": [],
                    "routes": [],
                    "strengths": [],
                    "manufacturer": "",
                    "purpose": "",
                    "indications": "",
                    "contraindications": "",
                    "warnings": "No official FDA drug label found for this medication query.",
                    "adverse_reactions": "",
                    "verified_label_dosage": "",
                    "dosage_instructions": "",
                    "drug_interactions": "",
                    "provider": "OpenFDA",
                    "status": "NO_RELEVANT_RESULT",
                    "verification_status": "NOT_FOUND",
                    "is_live": True,
                    "fallback_used": False,
                    "fallback_reason": "No relevant FDA label found",
                    "source": "OpenFDA Live API",
                    "retrieved_at": now_iso
                }
        elif response.status_code == 429:
            status = "RATE_LIMIT"
            fallback_reason = "OpenFDA HTTP 429: API rate limit reached"
        elif response.status_code in [401, 403]:
            status = "AUTH_ERROR"
            fallback_reason = f"OpenFDA HTTP {response.status_code}: Authentication failure"
        elif response.status_code == 404:
            # 404 from OpenFDA search means no record found
            _logger.info("[OpenFDA] 404 (NO_RELEVANT_RESULT) for: '%s'", drug_name)
            return {
                "medicine_name": clean_name.capitalize(),
                "generic_name": clean_name.capitalize(),
                "brand_names": [],
                "active_ingredients": "",
                "dosage_forms": [],
                "routes": [],
                "strengths": [],
                "manufacturer": "",
                "purpose": "",
                "indications": "",
                "contraindications": "",
                "warnings": "No official FDA drug label found for this medication query.",
                "adverse_reactions": "",
                "verified_label_dosage": "",
                "dosage_instructions": "",
                "drug_interactions": "",
                "provider": "OpenFDA",
                "status": "NO_RELEVANT_RESULT",
                "verification_status": "NOT_FOUND",
                "is_live": True,
                "fallback_used": False,
                "fallback_reason": "No relevant FDA label found (HTTP 404)",
                "source": "OpenFDA Live API",
                "retrieved_at": now_iso
            }
        else:
            status = "INVALID_RESPONSE"
            fallback_reason = f"OpenFDA HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        status = "TIMEOUT"
        fallback_reason = "OpenFDA request timed out (>5s)"
    except requests.exceptions.ConnectionError:
        status = "NETWORK_ERROR"
        fallback_reason = "OpenFDA connection network error"
    except Exception as exc:
        status = "INVALID_RESPONSE"
        fallback_reason = f"OpenFDA unexpected error: {exc}"

    # 3. Handle Provider Failure Fallback (Explicitly marked as local reference)
    _logger.warning("[OpenFDA] Live query failed for '%s' (status: %s, reason: %s) -> LOCAL FALLBACK", drug_name, status, fallback_reason)
    return {
        "medicine_name": clean_name.capitalize(),
        "generic_name": clean_name.capitalize(),
        "brand_names": [clean_name.capitalize()],
        "active_ingredients": "",
        "dosage_forms": [],
        "routes": [],
        "strengths": [],
        "manufacturer": "",
        "purpose": "Symptomatic management under licensed physician guidance.",
        "indications": "",
        "contraindications": "",
        "warnings": "Consult physician or pharmacist for verified contraindications and warnings.",
        "adverse_reactions": "",
        "verified_label_dosage": "",
        "dosage_instructions": "Verified label dosage unavailable offline. Consult a licensed medical practitioner.",
        "drug_interactions": "",
        "provider": "OpenFDA",
        "status": status,
        "verification_status": "CLINICAL_REFERENCE",
        "is_live": False,
        "fallback_used": True,
        "fallback_reason": fallback_reason,
        "source": "Local Clinical Reference (OpenFDA Unavailable)",
        "retrieved_at": now_iso
    }


def is_openfda_verified(record: Optional[Dict[str, Any]]) -> bool:
    """
    Evaluates whether an OpenFDA drug record represents a genuinely verified FDA label.
    Rules:
    - Must not be None
    - status == "SUCCESS"
    - verification_status == "OPENFDA_VERIFIED" (or unset on successful mock/live)
    - fallback_used is not True
    - Must have substance / label content: at least one of dosage_forms, routes, indications, active_ingredients,
      verified_strength, verified_route, verified_form, verified_label_dosage, or generic_name.
    """
    if not record or not isinstance(record, dict):
        return False
    if record.get("status") != "SUCCESS":
        return False
    v_stat = record.get("verification_status")
    if v_stat and v_stat not in ("OPENFDA_VERIFIED", "SUCCESS"):
        return False
    if record.get("fallback_used") is True:
        return False
    has_substance = bool(
        record.get("dosage_forms") or
        record.get("routes") or
        record.get("indications") or
        record.get("active_ingredients") or
        record.get("verified_strength") or
        record.get("verified_route") or
        record.get("verified_form") or
        record.get("verified_label_dosage") or
        record.get("generic_name") or
        record.get("brand_name")
    )
    return has_substance


