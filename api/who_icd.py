"""
    WHO ICD-11 API Client (World Health Organization)
Official Disease Classification & Diagnosis Taxonomy API with OAuth2 Token Caching.
"""
import requests
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import WHO_ICD_CLIENT_ID, WHO_ICD_CLIENT_SECRET

TOKEN_URL = "https://icdaccessmanagement.who.int/connect/token"
API_BASE_URL = "https://id.who.int/icd"

# In-memory Token Cache
_cached_token = None
_token_expiry_timestamp = 0

def get_who_access_token():
    """
    Obtains or reuses an active OAuth2 Bearer token from WHO Identity Management.
    """
    global _cached_token, _token_expiry_timestamp

    # If token exists and is valid for at least 60 more seconds, reuse it
    if _cached_token and time.time() < (_token_expiry_timestamp - 60):
        return _cached_token

    if not WHO_ICD_CLIENT_ID or not WHO_ICD_CLIENT_SECRET:
        return None

    try:
        payload = {
            "client_id": WHO_ICD_CLIENT_ID,
            "client_secret": WHO_ICD_CLIENT_SECRET,
            "scope": "icdapi_access",
            "grant_type": "client_credentials"
        }
        res = requests.post(TOKEN_URL, data=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            _cached_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            _token_expiry_timestamp = time.time() + expires_in
            return _cached_token
    except Exception as e:
        print(f"WHO ICD-11 Token note: {e}")

    return None

def search_who_icd11(query):
    """
    Searches official WHO ICD-11 entity registry for standard disease diagnosis definitions.
    Returns: List of formatted diagnostic entities with ICD title and chapter.
    """
    if not query or not query.strip():
        return []

    token = get_who_access_token()
    if not token:
        return []

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Accept-Language": "en",
            "API-Version": "v2"
        }
        search_url = f"{API_BASE_URL}/entity/search"
        params = {"q": query.strip()}

        res = requests.get(search_url, headers=headers, params=params, timeout=8)
        if res.status_code == 200:
            data = res.json()
            entities = data.get("destinationEntities", [])
            results = []

            for ent in entities[:6]:
                # Clean html tags like <em class='found'> from title
                raw_title = ent.get("title", "")
                clean_title = raw_title.replace("<em class='found'>", "").replace("</em>", "")
                
                results.append({
                    "id": ent.get("id"),
                    "title": clean_title,
                    "chapter": ent.get("chapter", ""),
                    "the_code": ent.get("theCode", "ICD-11 Entity"),
                    "score": ent.get("score", 1.0)
                })
            return results
    except Exception as e:
        print(f"WHO ICD-11 Search note: {e}")

    return []
