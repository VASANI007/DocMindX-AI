"""
DocMindX AI — DailyMed REST API v2 Client (National Library of Medicine / NIH)
Provides official Structured Product Labels (SPL), drug names, packaging, and NDC metadata.
Features:
- Strict provider status contract: SUCCESS, NO_RELEVANT_RESULT, TIMEOUT, RATE_LIMIT, AUTH_ERROR, NETWORK_ERROR, INVALID_RESPONSE
- Official NIH/NLM SPL label records with images and packaging
- Accurate provenance tracking: never claims verification on timeout or empty result
"""
import logging
import requests
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.create_tables import cache_medicine, get_cached_medicine

BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
_logger = logging.getLogger("DocMindX.DailyMed")

STATUS_SUCCESS = "SUCCESS"
STATUS_NO_RELEVANT_RESULT = "NO_RELEVANT_RESULT"
STATUS_RATE_LIMIT = "RATE_LIMIT"
STATUS_AUTH_ERROR = "AUTH_ERROR"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_NETWORK_ERROR = "NETWORK_ERROR"
STATUS_INVALID_RESPONSE = "INVALID_RESPONSE"


def search_dailymed_drugnames(drug_name: str, page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Search DailyMed for matching brand and generic drug names.
    Returns: List of matching drug name strings or dicts with status.
    """
    if not drug_name or not str(drug_name).strip():
        return []

    try:
        url = f"{BASE_URL}/drugnames.json"
        params = {"drug_name": str(drug_name).strip(), "pagesize": page_size}
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", [])
            names = [item.get("drug_name") for item in items if item.get("drug_name")]
            _logger.info("[DailyMed] Drugnames SUCCESS for '%s': %d names", drug_name, len(names))
            return names
        elif res.status_code == 429:
            _logger.warning("[DailyMed] Drugnames RATE_LIMIT (429) for '%s'", drug_name)
        else:
            _logger.warning("[DailyMed] Drugnames HTTP %s for '%s'", res.status_code, drug_name)
    except requests.exceptions.Timeout:
        _logger.warning("[DailyMed] Drugnames TIMEOUT for '%s'", drug_name)
    except requests.exceptions.ConnectionError:
        _logger.warning("[DailyMed] Drugnames NETWORK_ERROR for '%s'", drug_name)
    except Exception as e:
        _logger.error("[DailyMed] Drugnames error for '%s': %s", drug_name, e)

    return []


def search_dailymed_spls(drug_name: str, page_size: int = 5) -> Dict[str, Any]:
    """
    Search official Structured Product Labels (SPL) for a given drug name.
    Returns: Structured dict with results list and status.
    """
    if not drug_name or not str(drug_name).strip():
        return {"status": "NO_RELEVANT_RESULT", "results": [], "is_live": False}

    clean_name = str(drug_name).strip()
    try:
        url = f"{BASE_URL}/spls.json"
        params = {"drug_name": clean_name, "pagesize": page_size}
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", [])
            results = []
            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "setid": item.get("setid", ""),
                    "published_date": item.get("published_date", "")
                })
            if results:
                return {
                    "status": "SUCCESS",
                    "results": results,
                    "is_live": True,
                    "fallback_used": False,
                    "fallback_reason": ""
                }
            else:
                return {
                    "status": "NO_RELEVANT_RESULT",
                    "results": [],
                    "is_live": True,
                    "fallback_used": False,
                    "fallback_reason": "No Structured Product Label found in DailyMed"
                }
        elif res.status_code == 429:
            return {"status": "RATE_LIMIT", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": "DailyMed HTTP 429 Rate Limit"}
        else:
            return {"status": "INVALID_RESPONSE", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": f"DailyMed HTTP {res.status_code}"}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": "DailyMed request timed out"}
    except requests.exceptions.ConnectionError:
        return {"status": "NETWORK_ERROR", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": "DailyMed network connection error"}
    except Exception as e:
        return {"status": "INVALID_RESPONSE", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": str(e)}


def get_dailymed_spl_ndcs(setid: str) -> List[str]:
    """Fetch National Drug Codes (NDCs) associated with an SPL setid."""
    if not setid:
        return []
    try:
        url = f"{BASE_URL}/spls/{setid}/ndcs.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            ndc_items = data.get("data", {}).get("ndcs", [])
            return ndc_items[:5]
    except Exception as e:
        _logger.debug("DailyMed NDCs note: %s", e)
    return []


def get_dailymed_spl_media(setid: str) -> List[str]:
    """Fetch image and media URLs associated with an SPL setid."""
    if not setid:
        return []
    try:
        url = f"{BASE_URL}/spls/{setid}/media.json"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            media_items = data.get("data", {}).get("media", [])
            media_urls = []
            for m in media_items:
                if isinstance(m, dict) and m.get("url"):
                    media_urls.append(m.get("url"))
            return media_urls
    except Exception as e:
        _logger.debug("DailyMed Media note: %s", e)
    return []


def get_dailymed_medicine_summary(drug_name: str) -> Optional[Dict[str, Any]]:
    """
    Combines DailyMed drug names, SPL label records, and media URLs into a structured summary.
    Enforces strict status contract and truthful verification tracking.
    """
    if not drug_name or not str(drug_name).strip():
        return None

    clean_name = str(drug_name).strip()
    now_iso = datetime.now().isoformat()

    # 1. Check local cache
    cached = get_cached_medicine(clean_name)
    if cached and cached.get("source") in ["DailyMed v2 (NIH / NLM)", "DailyMed / OpenFDA"]:
        return cached

    # 2. Search DailyMed SPLs
    spl_resp = search_dailymed_spls(clean_name, page_size=2)
    status = spl_resp.get("status", "NO_RELEVANT_RESULT")
    spl_list = spl_resp.get("results", [])

    if status == "SUCCESS" and spl_list:
        top_spl = spl_list[0]
        setid = top_spl.get("setid", "")
        ndcs = get_dailymed_spl_ndcs(setid) if setid else []
        media = get_dailymed_spl_media(setid) if setid else []

        summary = {
            "medicine_name": clean_name.capitalize(),
            "generic_name": top_spl.get("title", clean_name),
            "spl_setid": setid,
            "published_date": top_spl.get("published_date", "Current"),
            "ndcs": ndcs,
            "media_urls": media,
            "source": "DailyMed v2 (NIH / NLM)",
            "provider": "DailyMed",
            "status": "SUCCESS",
            "verification_status": "DAILYMED_VERIFIED",
            "is_live": True,
            "fallback_used": False,
            "fallback_reason": "",
            "retrieved_at": now_iso
        }
        return summary
    elif status == "NO_RELEVANT_RESULT":
        return {
            "medicine_name": clean_name.capitalize(),
            "generic_name": clean_name.capitalize(),
            "spl_setid": "",
            "published_date": "",
            "ndcs": [],
            "media_urls": [],
            "source": "DailyMed v2 (NIH / NLM)",
            "provider": "DailyMed",
            "status": "NO_RELEVANT_RESULT",
            "verification_status": "NOT_FOUND",
            "is_live": True,
            "fallback_used": False,
            "fallback_reason": "No Structured Product Label found in DailyMed",
            "retrieved_at": now_iso
        }
    else:
        # TIMEOUT, RATE_LIMIT, NETWORK_ERROR, INVALID_RESPONSE
        return {
            "medicine_name": clean_name.capitalize(),
            "generic_name": clean_name.capitalize(),
            "spl_setid": "",
            "published_date": "",
            "ndcs": [],
            "media_urls": [],
            "source": "DailyMed Unavailable (Local Reference)",
            "provider": "DailyMed",
            "status": status,
            "verification_status": "UNVERIFIED",
            "is_live": False,
            "fallback_used": True,
            "fallback_reason": spl_resp.get("fallback_reason", f"DailyMed status: {status}"),
            "retrieved_at": now_iso
        }


def is_dailymed_verified(record: Optional[Dict[str, Any]]) -> bool:
    """
    Evaluates whether a DailyMed drug record represents a genuinely verified DailyMed SPL label.
    Rules:
    - Must not be None
    - status == "SUCCESS"
    - verification_status == "DAILYMED_VERIFIED"
    - spl_setid is non-empty string
    - fallback_used is not True
    """
    if not record or not isinstance(record, dict):
        return False
    return (
        record.get("status") == "SUCCESS" and
        record.get("verification_status") == "DAILYMED_VERIFIED" and
        bool(record.get("spl_setid") and str(record.get("spl_setid")).strip()) and
        record.get("fallback_used") is not True
    )

