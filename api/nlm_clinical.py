"""
    NLM Clinical Tables API Client (National Library of Medicine / NIH)
Provides fast, zero-auth disease, symptom, and condition autocomplete & search.
"""
import requests

BASE_URL = "https://clinicaltables.nlm.nih.gov/api"

def search_nlm_conditions(query, max_list=10):
    """
    Search NIH NLM conditions database for fast autocomplete suggestions.
    No API key required.
    Returns: List of condition name strings.
    """
    if not query or not query.strip() or len(query.strip()) < 2:
        return []

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
                return [item[0] if isinstance(item, list) else item for item in data[3]]
            elif len(data) >= 1 and isinstance(data[0], int) and len(data) >= 2 and data[1]:
                return data[1]
    except Exception as e:
        print(f"NLM Clinical Tables note: {e}")

    return []

def search_nlm_icd11_codes(query, max_list=10):
    """
    Search ICD-11 codes from NLM Clinical Tables.
    Returns list of dicts with code and title.
    """
    if not query or not query.strip() or len(query.strip()) < 2:
        return []

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
                return results
    except Exception as e:
        print(f"NLM ICD-11 search note: {e}")

    return []
