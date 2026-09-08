"""
    DocMindX AI Multilingual Translation & Dynamic Localization Helper
    Supports all 12 major Indian languages with zero-latency caching & live AI fallback.
"""
import json
import os
import re
import requests
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations")

LANGUAGE_FILE_MAP = {
    "en": "english.json",
    "hi": "hindi.json",
    "gu": "gujarati.json",
    "mr": "marathi.json",
    "bn": "bengali.json",
    "ta": "tamil.json",
    "te": "telugu.json",
    "kn": "kannada.json",
    "ml": "malayalam.json",
    "pa": "punjabi.json",
    "or": "odia.json",
    "ur": "urdu.json"
}

LANGUAGE_NAME_MAP = {
    "en": "English",
    "hi": "Hindi",
    "gu": "Gujarati",
    "mr": "Marathi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu"
}

def clean_json_str(s: str) -> str:
    s = s.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    s = s.strip()
    s = re.sub(r",\s*([\]}])", r"\1", s)
    return s

def _fetch_dynamic_translation(lang_code: str, lang_name: str) -> dict:
    """Dynamically translates the English dictionary into target language via Gemini API and caches it."""
    en_path = os.path.join(TRANSLATIONS_DIR, "english.json")
    if not os.path.exists(en_path):
        return {}
    
    with open(en_path, "r", encoding="utf-8") as f:
        en_dict = json.load(f)
    
    prompt = f"""You are an expert medical localization AI for the Government of India.
Translate this complete JSON UI dictionary from English into {lang_name} ({lang_code}).

CRITICAL RULES:
1. Retain ALL original JSON keys exactly as they are without renaming, skipping, or adding any keys.
2. Translate all string values into natural, accurate, culturally appropriate {lang_name} medical and healthcare phrasing.
3. Keep technical acronyms like AI, OCR, NLEM, IPHS, ICU, OPD, GPS, API, PDF, ID recognized if standard.
4. Output MUST be strictly valid JSON.

English JSON:
{json.dumps(en_dict, ensure_ascii=False, indent=2)}
"""

    if GEMINI_API_KEY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                },
                timeout=25
            )
            if res.status_code == 200:
                raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                cleaned = clean_json_str(raw_text)
                data = json.loads(cleaned)
                # Cache to disk for instant future loads
                file_name = LANGUAGE_FILE_MAP.get(lang_code, f"{lang_code}.json")
                out_path = os.path.join(TRANSLATIONS_DIR, file_name)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return data
        except Exception:
            pass
            
    return en_dict

def load_translations(lang_code="en"):
    """Loads translations for the given language code with fast caching & dynamic fallback."""
    file_name = LANGUAGE_FILE_MAP.get(lang_code, f"{lang_code}.json")
    file_path = os.path.join(TRANSLATIONS_DIR, file_name)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    # If not on disk, dynamically generate and cache
    lang_name = LANGUAGE_NAME_MAP.get(lang_code, lang_code.title())
    return _fetch_dynamic_translation(lang_code, lang_name)

def get_text(translations, key, default=""):
    """Returns the translated string for the given key, falling back to default or key name."""
    if not isinstance(translations, dict):
        return default or key
    return translations.get(key, default or key)

