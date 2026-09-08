"""
    DocMindX AI Configuration & Environment Settings
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys & Credentials (Loaded securely from .env)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
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

# DB Path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "DocMindX.db")
