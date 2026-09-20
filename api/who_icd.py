"""
DocMindX AI — WHO ICD-11 API Client (World Health Organization)
Official Disease Classification & Diagnosis Taxonomy Validation Client.
Features:
- Strict provider status contract: SUCCESS, NO_RELEVANT_RESULT, TIMEOUT, RATE_LIMIT, AUTH_ERROR, NETWORK_ERROR, INVALID_RESPONSE
- Code validation and title validation directly against WHO ICD-11 live endpoint
- Never mislabels ICD-10 codes as ICD-11
- Truthful verification tracking: unvalidated codes are explicitly marked UNVERIFIED
"""
import logging
import requests
import time
import re
import os
import sys
from typing import Optional, Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import WHO_ICD_CLIENT_ID, WHO_ICD_CLIENT_SECRET

TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
API_BASE_URL = "https://id.who.int/icd"

# In-memory Token & Rate/Circuit Breaker State
_cached_token = None
_token_expiry_timestamp = 0
_last_auth_failure_timestamp = 0
_circuit_open_until = 0

STATUS_SUCCESS = "SUCCESS"
STATUS_NO_RELEVANT_RESULT = "NO_RELEVANT_RESULT"
STATUS_RATE_LIMIT = "RATE_LIMIT"
STATUS_AUTH_ERROR = "AUTH_ERROR"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_NETWORK_ERROR = "NETWORK_ERROR"
STATUS_INVALID_RESPONSE = "INVALID_RESPONSE"
STATUS_CIRCUIT_OPEN = "CIRCUIT_OPEN"

_logger = logging.getLogger("DocMindX.TriageEngine.WHO_ICD")


def is_probable_icd10_code(code: str) -> bool:
    """
    Checks if a code adheres to the legacy WHO ICD-10 syntax (e.g. A00, G44.2, J11.1).
    ICD-10 codes must NEVER be labelled as system = 'ICD-11'.
    """
    if not code:
        return False
    c = str(code).strip().upper()
    return bool(re.match(r"^[A-Z][0-9]{2}(?:\.[0-9A-Z]+)?$", c))


def get_who_access_token() -> Optional[str]:
    """
    Obtains or reuses an active OAuth2 Bearer token from WHO Identity Management.
    Returns None when credentials are absent or request fails.
    Caches auth failure for 60 seconds to avoid repeating failed network requests.
    """
    global _cached_token, _token_expiry_timestamp, _last_auth_failure_timestamp

    if _cached_token and time.time() < (_token_expiry_timestamp - 60):
        return _cached_token

    if (time.time() - _last_auth_failure_timestamp) < 60:
        return None

    if not WHO_ICD_CLIENT_ID or not WHO_ICD_CLIENT_SECRET:
        _logger.info("[WHO ICD-11] Credentials not configured (WHO_ICD_CLIENT_ID / WHO_ICD_CLIENT_SECRET)")
        return None

    try:
        payload = {
            "client_id": WHO_ICD_CLIENT_ID,
            "client_secret": WHO_ICD_CLIENT_SECRET,
            "scope": "icdapi_access",
            "grant_type": "client_credentials"
        }
        res = requests.post(TOKEN_URL, data=payload, timeout=3)
        if res.status_code == 200:
            data = res.json()
            _cached_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            _token_expiry_timestamp = time.time() + expires_in
            _logger.info("[WHO ICD-11] Token obtained successfully (expires in %ds)", expires_in)
            return _cached_token
        else:
            _logger.warning("[WHO ICD-11] Token request failed: HTTP %s", res.status_code)
            _last_auth_failure_timestamp = time.time()
    except requests.exceptions.Timeout:
        _logger.warning("[WHO ICD-11] Token request TIMEOUT")
        _last_auth_failure_timestamp = time.time()
    except requests.exceptions.ConnectionError:
        _logger.warning("[WHO ICD-11] Token request CONNECTION ERROR")
        _last_auth_failure_timestamp = time.time()
    except Exception as exc:
        _logger.error("[WHO ICD-11] Token request error: %s", exc)
        _last_auth_failure_timestamp = time.time()

    return None


def search_who_icd11_structured(query: str) -> Dict[str, Any]:
    """
    Searches official WHO ICD-11 entity registry for standard disease diagnosis definitions.
    Returns: Structured dictionary with status, results list, and live provenance.
    """
    global _last_auth_failure_timestamp, _circuit_open_until, _cached_token, _token_expiry_timestamp

    if not query or not str(query).strip():
        return {"status": "NO_RELEVANT_RESULT", "results": [], "is_live": False}

    if time.time() < _circuit_open_until:
        return {
            "status": "CIRCUIT_OPEN",
            "results": [],
            "is_live": False,
            "fallback_used": True,
            "fallback_reason": "WHO circuit open due to recent failures"
        }

    token = get_who_access_token()
    if not token:
        return {
            "status": "AUTH_ERROR",
            "results": [],
            "is_live": False,
            "fallback_used": True,
            "fallback_reason": "WHO ICD-11 credentials missing or auth failure"
        }

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Accept-Language": "en",
            "API-Version": "v2"
        }
        search_url = f"{API_BASE_URL}/entity/search"
        params = {"q": str(query).strip()}

        res = requests.get(search_url, headers=headers, params=params, timeout=2.5)
        if res.status_code == 200:
            data = res.json()
            entities = data.get("destinationEntities", [])
            results = []
            for ent in entities[:6]:
                raw_title = ent.get("title", "")
                clean_title = raw_title.replace("<em class='found'>", "").replace("</em>", "")
                raw_code = ent.get("theCode", "")
                
                # Check for legacy ICD-10 pollution
                system_label = "ICD-10" if is_probable_icd10_code(raw_code) else "ICD-11"

                results.append({
                    "id": ent.get("id"),
                    "title": clean_title,
                    "chapter": ent.get("chapter", ""),
                    "code": raw_code,
                    "the_code": raw_code,
                    "system": system_label,
                    "score": ent.get("score", 1.0),
                    "is_live": True,
                    "fallback_used": False,
                    "fallback_reason": ""
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
                    "is_live": False,
                    "fallback_used": True,
                    "fallback_reason": "No matching ICD-11 entity found"
                }

        elif res.status_code == 401:
            _logger.warning("[WHO ICD-11] Authentication failed (401) for query: '%s'", query)
            _cached_token = None
            _token_expiry_timestamp = 0
            _last_auth_failure_timestamp = time.time()
            return {"status": "AUTH_ERROR", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": "WHO 401 Unauthorized"}
        elif res.status_code == 429:
            _circuit_open_until = time.time() + 60
            return {"status": "RATE_LIMIT", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": "WHO 429 Rate Limit"}
        else:
            return {"status": "INVALID_RESPONSE", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": f"WHO HTTP {res.status_code}"}

    except requests.exceptions.Timeout:
        _circuit_open_until = time.time() + 30
        return {"status": "TIMEOUT", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": "WHO request timed out"}
    except requests.exceptions.ConnectionError:
        _circuit_open_until = time.time() + 30
        return {"status": "NETWORK_ERROR", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": "WHO network connection error"}
    except Exception as exc:
        return {"status": "INVALID_RESPONSE", "results": [], "is_live": False, "fallback_used": True, "fallback_reason": str(exc)}


def search_who_icd11(query: str) -> List[Dict[str, Any]]:
    """Legacy compatibility wrapper returning list of entity dicts."""
    resp = search_who_icd11_structured(query)
    return resp.get("results", [])


_validation_cache: Dict[str, Dict[str, Any]] = {}


def validate_icd11_condition(condition_name: str) -> Dict[str, Any]:
    """
    Validates a clinical condition name against WHO ICD-11.
    
    Returns structured dict conforming to Section 22:
    {
        "code": str,
        "system": "ICD-11",
        "title": str,
        "source": "WHO",
        "verification_status": "VERIFIED" | "UNVERIFIED",
        "validated": bool,
        "provider_status": str,
        "is_live": bool,
        "fallback_used": bool,
        "fallback_reason": str
    }
    """
    if not condition_name or not str(condition_name).strip():
        return {
            "code": "",
            "icd_code": "",
            "system": "ICD-11",
            "title": "",
            "source": "WHO",
            "verification_status": "UNVERIFIED",
            "validated": False,
            "provider_status": "NO_RELEVANT_RESULT",
            "is_live": False,
            "fallback_used": True,
            "fallback_reason": "Empty condition name"
        }

    clean_name = str(condition_name).strip()
    cache_key = clean_name.lower()
    if cache_key in _validation_cache:
        return dict(_validation_cache[cache_key])

    # Try sanitized query (strip parentheticals, slashes) first
    sanitized_query = clean_name
    if "(" in sanitized_query:
        sanitized_query = re.sub(r'\(.*?\)', '', sanitized_query).strip()
    if "/" in sanitized_query:
        sanitized_query = sanitized_query.split("/")[0].strip()
    sanitized_query = sanitized_query or clean_name

    resp = search_who_icd11_structured(sanitized_query)
    status = resp.get("status", "NO_RELEVANT_RESULT")
    results = resp.get("results", [])

    if (not results or status != "SUCCESS") and sanitized_query.lower() != clean_name.lower():
        fallback_resp = search_who_icd11_structured(clean_name)
        if fallback_resp.get("status") == "SUCCESS" and fallback_resp.get("results"):
            resp = fallback_resp
            status = resp.get("status")
            results = resp.get("results", [])

    if status == "SUCCESS" and results:
        best = results[0]
        code = best.get("the_code") or best.get("code") or ""
        system = "ICD-10" if is_probable_icd10_code(code) else "ICD-11"
        is_verified = (system == "ICD-11") and bool(code)

        res = {
            "code": code,
            "icd_code": code,
            "system": system,
            "title": best.get("title", clean_name),
            "source": "WHO",
            "verification_status": "VERIFIED" if is_verified else "UNVERIFIED",
            "validated": is_verified,
            "provider_status": "SUCCESS",
            "is_live": True,
            "fallback_used": False,
            "fallback_reason": ""
        }
        _validation_cache[cache_key] = res
        return res
    else:
        # Unverified outcome (WHO API failed, not configured, or returned 0 matches)
        res = {
            "code": "",
            "icd_code": "",
            "system": "ICD-11",
            "title": clean_name,
            "source": "WHO",
            "verification_status": "UNVERIFIED",
            "validated": False,
            "provider_status": status,
            "is_live": False,
            "fallback_used": True,
            "fallback_reason": resp.get("fallback_reason", "No verified WHO ICD-11 entity found")
        }
        _validation_cache[cache_key] = res
        return res
