"""
    NLM Clinical Tables API Client (National Library of Medicine / NIH)
Provides fast, zero-auth disease, symptom, and condition autocomplete & search.
"""
import logging
import requests

BASE_URL = "https://clinicaltables.nlm.nih.gov/api"
_logger = logging.getLogger("DocMindX.TriageEngine.NLM")


def search_nlm_conditions(query, max_list=10):
    """
    Search NIH NLM conditions database for fast autocomplete suggestions.
    No API key required.
    Returns: List of condition name strings, or [] on failure.
    """
    if not query or not query.strip() or len(query.strip()) < 2:
        return []

    failure_type = None
    try:
        url = f"{BASE_URL}/conditions/v3/search"
        params = {
            "terms": query.strip(),
            "maxList": max_list
        }
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            # NLM conditions returns [total_count, code_list, extra_data, display_list]
            if len(data) >= 4 and data[3]:
                results = [item[0] if isinstance(item, list) else item for item in data[3]]
                _logger.info("[NLM] CONDITIONS search SUCCESS for '%s': %d results", query, len(results))
                return results
            elif len(data) >= 1 and isinstance(data[0], int) and len(data) >= 2 and data[1]:
                _logger.info("[NLM] CONDITIONS search SUCCESS (alt format) for '%s'", query)
                return data[1]
            else:
                failure_type = "empty_response"
                _logger.warning("[NLM] CONDITIONS search returned empty for '%s'", query)
        else:
            failure_type = f"HTTP_{res.status_code}"
            _logger.warning("[NLM] CONDITIONS HTTP %s for '%s'", res.status_code, query)

    except requests.exceptions.Timeout:
        failure_type = "timeout"
        _logger.warning("[NLM] CONDITIONS TIMEOUT for '%s' → LOCAL FALLBACK", query)
    except requests.exceptions.ConnectionError:
        failure_type = "connection_error"
        _logger.warning("[NLM] CONDITIONS CONNECTION ERROR for '%s' → LOCAL FALLBACK", query)
    except Exception as exc:
        failure_type = "unknown_error"
        _logger.error("[NLM] CONDITIONS unexpected error for '%s': %s", query, exc)

    return []


def search_nlm_icd11_codes(query, max_list=10):
    """
    Search ICD-11 codes from NLM Clinical Tables.
    Returns list of dicts with code and title, or [] on failure.
    """
    if not query or not query.strip() or len(query.strip()) < 2:
        return []

    failure_type = None
    try:
        url = f"{BASE_URL}/icd11_codes/v3/search"
        params = {
            "terms": query.strip(),
            "maxList": max_list,
            "df": "code,title"
        }
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if len(data) >= 4 and data[3]:
                results = []
                for item in data[3]:
                    if isinstance(item, list) and len(item) >= 2:
                        results.append({"code": item[0], "title": item[1]})
                    elif isinstance(item, list) and len(item) == 1:
                        results.append({"code": "", "title": item[0]})
                _logger.info("[NLM] ICD-11 search SUCCESS for '%s': %d codes found", query, len(results))
                return results
            else:
                failure_type = "empty_response"
                _logger.warning("[NLM] ICD-11 search returned empty for '%s'", query)
        else:
            failure_type = f"HTTP_{res.status_code}"
            _logger.warning("[NLM] ICD-11 HTTP %s for '%s'", res.status_code, query)

    except requests.exceptions.Timeout:
        failure_type = "timeout"
        _logger.warning("[NLM] ICD-11 TIMEOUT for '%s'", query)
    except requests.exceptions.ConnectionError:
        failure_type = "connection_error"
        _logger.warning("[NLM] ICD-11 CONNECTION ERROR for '%s'", query)
    except Exception as exc:
        failure_type = "unknown_error"
        _logger.error("[NLM] ICD-11 unexpected error for '%s': %s", query, exc)

    return []
