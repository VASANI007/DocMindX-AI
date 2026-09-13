"""
    DocMindX AI Multilingual Translation & Dynamic Localization Helper
    True Hybrid Architecture: Instant offline static dictionaries + live Gemini AI fallback with disk caching.
    Supports all 12 major Indian languages with zero latency and 100% dictionary parity.
"""
import json
import os
import re
import requests
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations")
DYNAMIC_CACHE_FILE = os.path.join(TRANSLATIONS_DIR, ".dynamic_cache.json")

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

# In-memory caches for high-speed sub-millisecond lookups
_LOADED_TRANSLATIONS = {}
_DYNAMIC_CACHE = {}

def _init_dynamic_cache():
    """Initializes the dynamic translation cache from disk."""
    global _DYNAMIC_CACHE
    if os.path.exists(DYNAMIC_CACHE_FILE):
        try:
            with open(DYNAMIC_CACHE_FILE, "r", encoding="utf-8") as f:
                _DYNAMIC_CACHE = json.load(f)
        except Exception:
            _DYNAMIC_CACHE = {}
    else:
        _DYNAMIC_CACHE = {}

_init_dynamic_cache()

def _save_dynamic_cache():
    """Persists dynamic cache to disk."""
    try:
        with open(DYNAMIC_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_DYNAMIC_CACHE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def clean_json_str(s: str) -> str:
    """Strips markdown code blocks and trailing commas from JSON string."""
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

def _translate_batch_with_gemini(missing_dict: dict, lang_code: str, lang_name: str) -> dict:
    """Translates a batch of key-value pairs into target language via Gemini API."""
    if not GEMINI_API_KEY or not missing_dict:
        return {}
    
    prompt = f"""You are an expert medical localization AI for the Government of India.
Translate this JSON dictionary from English into {lang_name} ({lang_code}).

CRITICAL RULES:
1. Retain ALL original JSON keys exactly as they are without renaming, modifying, or skipping any keys.
2. Translate all string values into natural, accurate, culturally appropriate {lang_name} medical and healthcare phrasing.
3. Keep technical acronyms like AI, OCR, NLEM, IPHS, ICU, OPD, GPS, API, PDF, ID recognized if standard.
4. Output MUST be strictly valid JSON.

JSON:
{json.dumps(missing_dict, ensure_ascii=False, indent=2)}
"""
    # Try lightweight fast models
    models_to_try = ["gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-1.5-flash"]
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
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
                if isinstance(data, dict):
                    return data
        except Exception:
            continue
            
    return {}

def load_translations(lang_code="en", force_reload=False):
    """
    Loads translations for the given language code with hybrid architecture:
    1. Loads target language JSON from disk.
    2. Compares against english.json baseline.
    3. If missing keys exist and online, dynamically translates & caches to disk.
    4. If offline, falls back seamlessly to English values for missing keys without crashing.
    """
    global _LOADED_TRANSLATIONS
    if not force_reload and lang_code in _LOADED_TRANSLATIONS:
        return _LOADED_TRANSLATIONS[lang_code]
    
    en_path = os.path.join(TRANSLATIONS_DIR, "english.json")
    en_dict = {}
    if os.path.exists(en_path):
        try:
            with open(en_path, "r", encoding="utf-8") as f:
                en_dict = json.load(f)
        except Exception:
            en_dict = {}

    if lang_code == "en":
        _LOADED_TRANSLATIONS["en"] = en_dict
        return en_dict

    file_name = LANGUAGE_FILE_MAP.get(lang_code, f"{lang_code}.json")
    file_path = os.path.join(TRANSLATIONS_DIR, file_name)
    target_dict = {}

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                target_dict = json.load(f)
        except Exception:
            target_dict = {}

    # Detect missing keys against English baseline
    missing_keys = {k: en_dict[k] for k in en_dict if k not in target_dict}

    if missing_keys:
        lang_name = LANGUAGE_NAME_MAP.get(lang_code, lang_code.title())
        # Attempt online dynamic batch translation
        translated_batch = _translate_batch_with_gemini(missing_keys, lang_code, lang_name)
        if translated_batch:
            target_dict.update(translated_batch)
            # Persist updated complete dictionary to disk
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(target_dict, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        
        # Safe offline fallback for any key still missing
        for k, v in missing_keys.items():
            if k not in target_dict:
                target_dict[k] = v

    _LOADED_TRANSLATIONS[lang_code] = target_dict
    return target_dict

def translate_dynamic_text(text: str, target_lang_code: str = "en") -> str:
    """
    Translates free-form dynamic text into target language using Gemini AI.
    Caches in memory and persists to disk for zero-latency repeats.
    Falls back gracefully to original text if offline.
    """
    if not text or target_lang_code == "en":
        return text
    
    # Check in-memory & disk cache
    lang_cache = _DYNAMIC_CACHE.setdefault(target_lang_code, {})
    if text in lang_cache:
        return lang_cache[text]

    if not GEMINI_API_KEY:
        return text

    lang_name = LANGUAGE_NAME_MAP.get(target_lang_code, target_lang_code.title())
    prompt = f"""You are an expert clinical localization assistant.
Translate the following healthcare text into {lang_name} ({target_lang_code}).
Rules:
- Provide ONLY the natural {lang_name} translation without explanation or surrounding quotes.
- Maintain clinical terms, numbers, bullet points, and formatting accurately.

Text:
{text}
"""
    models_to_try = ["gemini-flash-lite-latest", "gemini-2.5-flash"]
    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1}
                },
                timeout=12
            )
            if res.status_code == 200:
                out = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if out:
                    lang_cache[text] = out
                    _save_dynamic_cache()
                    return out
        except Exception:
            continue

    return text

def get_text(translations, key, default="", lang_code="en"):
    """
    Returns the translated string for the given key, falling back to default or key name.
    If translations dictionary has the key, returns it immediately.
    """
    if not isinstance(translations, dict):
        return default or key
    val = translations.get(key)
    if val:
        return val
    return default or key
