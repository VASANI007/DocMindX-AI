"""
    DocMindX AI Configuration & Environment Settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys & Credentials (Loaded securely from .env)
from api.gemini_manager import (
    get_gemini_api_keys,
    get_active_gemini_key,
    call_gemini_with_failover,
    gemini_pool
)

# Multi-Key Pool for Google Gemini (Auto-Failover on 429 Quota Exceeded)
GEMINI_API_KEYS = get_gemini_api_keys()
GEMINI_API_KEY = get_active_gemini_key()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Centralized AI Model Chains (Fastest verified working models first)
DEFAULT_GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]
GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "allam-2-7b",
]

OPENFDA_API_KEY = os.getenv("OPENFDA_API_KEY", "")
BIOPORTAL_API_KEY = os.getenv("BIOPORTAL_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
WHO_ICD_CLIENT_ID = os.getenv("WHO_ICD_CLIENT_ID", "")
WHO_ICD_CLIENT_SECRET = os.getenv("WHO_ICD_CLIENT_SECRET", "")
DATA_GOV_IN_API_KEY = os.getenv("DATA_GOV_IN_API_KEY", "")
WHO_OUTBREAK_API_URL = os.getenv("WHO_OUTBREAK_API_URL", "https://www.who.int/api/news/diseaseoutbreaknews")
GOOGLE_CLOUD_SPEECH_API_KEY = os.getenv("GOOGLE_CLOUD_SPEECH_API_KEY", "")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "command_center")

# App Info
APP_NAME = "DocMindX AI"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Intelligent Multilingual AI Healthcare System"

# Supported Languages (All-India Multi-Lingual Architecture)
SUPPORTED_LANGUAGES = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "ગુજરાતી (Gujarati)": "gu",
    "मराठी (Marathi)": "mr",
    "বাংলা (Bengali)": "bn",
    "தமிழ் (Tamil)": "ta",
    "తెలుగు (Telugu)": "te",
    "ಕನ್ನಡ (Kannada)": "kn",
    "മലയാളം (Malayalam)": "ml",
    "ਪੰਜਾਬੀ (Punjabi)": "pa",
    "ଓଡ଼ିଆ (Odia)": "or",
    "اردو (Urdu)": "ur"
}

# Database Configuration (Supabase PostgreSQL Only)
from config.database import get_database_engine_name
DATABASE_ENGINE = get_database_engine_name()
