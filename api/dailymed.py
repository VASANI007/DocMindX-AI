"""
    DailyMed REST API v2 Client (National Library of Medicine / NIH)
Provides official Structured Product Labels (SPL), drug names, packaging, and NDC metadata.
No API key required (Public GET REST Service).
"""
import requests
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.create_tables import cache_medicine, get_cached_medicine

BASE_URL = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def search_dailymed_drugnames(drug_name, page_size=10):
    """
    Search DailyMed for matching brand and generic drug names.
    """
    if not drug_name or not drug_name.strip():
        return []

    try:
        url = f"{BASE_URL}/drugnames.json"
        params = {
            "drug_name": drug_name.strip(),
            "pagesize": page_size
        }
        res = requests.get(url, params=params, timeout=6)
        if res.status_code == 200:
            data = res.json()
            items = data.get("data", [])
            return [item.get("drug_name") for item in items if item.get("drug_name")]
    except Exception as e:
        print(f"DailyMed drugnames note: {e}")

    return []

def search_dailymed_spls(drug_name, page_size=5):
    """
    Search official Structured Product Labels (SPL) for a given drug name.
    Returns: List of dicts containing title, setid, and published_date.
    """
    if not drug_name or not drug_name.strip():
        return []

    try:
        url = f"{BASE_URL}/spls.json"
        params = {
            "drug_name": drug_name.strip(),
            "pagesize": page_size
        }
        res = requests.get(url, params=params, timeout=6)
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
            return results
    except Exception as e:
        print(f"DailyMed SPLs note: {e}")

    return []

def get_dailymed_spl_ndcs(setid):
    """
    Fetch National Drug Codes (NDCs) associated with an SPL setid.
    """
    if not setid:
        return []

    try:
        url = f"{BASE_URL}/spls/{setid}/ndcs.json"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            ndc_items = data.get("data", {}).get("ndcs", [])
            return ndc_items[:5]
    except Exception as e:
        print(f"DailyMed NDCs note: {e}")

    return []

def get_dailymed_spl_media(setid):
    """
    Fetch image and media URLs associated with an SPL setid.
    """
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
        print(f"DailyMed Media note: {e}")

    return []

def get_dailymed_medicine_summary(drug_name):
    """
    Combines DailyMed drug names, SPL label records, and media URLs into a structured summary.
    """
    if not drug_name or not drug_name.strip():
        return None

    clean_name = drug_name.strip()
    
    # 1. Check local cache
    cached = get_cached_medicine(clean_name)
    if cached and cached.get("source") == "DailyMed / OpenFDA":
        return cached

    # 2. Search DailyMed SPLs
    spl_list = search_dailymed_spls(clean_name, page_size=2)
    if spl_list:
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
            "source": "DailyMed v2 (NIH / NLM)"
        }
        return summary

    return None
