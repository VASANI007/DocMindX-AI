"""DocMindX AI — Clinical-Grade Multilingual AI Healthcare System
Version: 2.0 (Enterprise Clinical Red Edition)
Features:
1. Panel 1: AI Health & Symptom Analyzer (Trilingual Triage, Red Flags, Diet, Lifestyle, Yoga & Physio)
2. Panel 2: Clinical Report & Prescription Analyzer (Lab Reference Ranges, OCR, Layman Explanations)
3. Panel 3: Regional Healthcare & Emergency Finder (OpenStreetMap, Overpass API, Live Facilities)
4. Panel 4: Health Records & Clinical History (SQLite Historical Vault & Analytics)
5. Panel 5: About DocMindX AI (System Architecture, Datasets, AI Engines & Credits)
"""
import os
import sys

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)


import markdown

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import base64
import re
import uuid
from datetime import datetime
import services.email_service as email_service
from config.settings import APP_NAME, APP_VERSION, SUPPORTED_LANGUAGES
from config.language import load_translations, get_text
from config.theme import apply_theme
from components.theme_toggle import theme_toggle_switch
import database.auth_db as auth_db
import components.auth_ui as auth_ui
import components.family_ui as family_ui
import components.admin_ui as admin_ui
import services.auth_service as auth_svc
from database.insert_data import (
    log_triage_session,
    log_report_analysis,
    get_recent_triage_history,
    get_recent_report_history,
    seed_sample_records_if_empty
)
from ai.disease_prediction.predict import SymptomTriageEngine
from ai.disease_prediction.multilingual_symptom_extractor import symptom_extractor
from ai.report_ai.blood_report import LabReportAnalyzer
from ai.report_ai.prescription import PrescriptionAnalyzer
from ai.report_ai.radiology import RadiologyReportAnalyzer
from ai.ocr.text_extractor import extract_text_from_file
from ai.chatbot.rag import generate_health_summary_ai
from ai.chatbot.chatbot import ask_DocMindX_ai, generate_dynamic_patient_questions, detect_redirect_action
from ai.utils.report_generator import generate_pdf_report, generate_scan_record_pdf
from ai.utils.care_recommendations import (
    get_dynamic_clinical_recommendations,
    localize_care_recommendations,
    get_medicine_gallery,
    get_youtube_search_url
)
from ai.utils.seasonal_context import INDIAN_STATES, get_seasonal_health_context
from ai.medicine_ai.medicine_details import get_medicine_details
from api.openfda import search_drug_openfda
from ai.chatbot.deep_explainer import (
    generate_deep_explanation,
    answer_assessment_question,
    generate_medical_report_comprehensive_breakdown
)
from api.dailymed import search_dailymed_spls, search_dailymed_drugnames
from api.bioportal import search_bioportal_concept, annotate_clinical_text
from api.nlm_clinical import search_nlm_conditions
from api.who_icd import search_who_icd11
from api.nominatim import geocode_city_district
from api.geolocation import detect_auto_location, get_client_ip
from api.overpass import query_nearby_healthcare
from services.geocoding_service import geocode_address, reverse_geocode
from services.places_service import search_nearby_healthcare, search_nearby_hospitals
from services.routes_service import get_route
from components.google_map import generate_google_map_html
from components.command_center_view import render_command_center_dashboard
from components.diagnostic_results_view import render_diagnostic_evaluation_view
from ai.voice.speech_to_text import transcribe_audio
from ai.voice.text_to_speech import synthesize_speech

# Seed sample records if database table is initially empty
seed_sample_records_if_empty()

def get_base64_image(image_path: str) -> str:
    try:
        if os.path.exists(image_path):
            ext = "jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "png"
            with open(image_path, "rb") as img_file:
                return f"data:image/{ext};base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
    except Exception:
        pass
    return ""

def safe_markdown(content: str, **kwargs):
    """Safely renders HTML via st.markdown by stripping leading whitespace from all lines.
    This strictly prevents CommonMark from accidentally parsing indented HTML tags as markdown code blocks.
    """
    if not isinstance(content, str):
        content = str(content)
    cleaned = "\n".join(line.strip() for line in content.strip().splitlines())
    return st.markdown(cleaned, unsafe_allow_html=True, **kwargs)

LOGO_DARK_B64 = get_base64_image(os.path.join(os.path.dirname(__file__), "assets", "logo", "logo_dark.png"))
LOGO_LIGHT_B64 = get_base64_image(os.path.join(os.path.dirname(__file__), "assets", "logo", "logo_light.png"))
ROBOT_MASCOT_B64 = get_base64_image(os.path.join(os.path.dirname(__file__), "assets", "images", "assistant_bot.jpg"))
FAVICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "logo", "favicon.png")

# Page configuration
st.set_page_config(
    page_title=f"{APP_NAME} — Enterprise Clinical Healthcare Portal",
    page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# Read query parameters to sync dark mode state if requested
qp_theme = st.query_params.get("theme", None)
if qp_theme is not None:
    st.session_state["dark_mode"] = (qp_theme.lower() == "dark")

# Session State Setup
auth_ui.init_auth_session_state()
if "session_scans" not in st.session_state:
    st.session_state["session_scans"] = []
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False
if "active_panel" not in st.session_state:
    st.session_state["active_panel"] = "Health Assessment"
if "assessment_step" not in st.session_state:
    st.session_state["assessment_step"] = 1
if "language" not in st.session_state:
    st.session_state["language"] = "en"
if "app_language" not in st.session_state:
    st.session_state["app_language"] = "English"
if "floating_chat_open" not in st.session_state:
    st.session_state["floating_chat_open"] = False
if "floating_chat_history" not in st.session_state:
    st.session_state["floating_chat_history"] = []

# Apply Clinical Red Enterprise Styling
apply_theme(st.session_state.get("dark_mode", False))

# Cache Engine Instances
@st.cache_resource
def get_triage_engine():
    return SymptomTriageEngine()

@st.cache_resource
def get_lab_analyzer():
    return LabReportAnalyzer()

@st.cache_resource
def get_prescription_analyzer():
    return PrescriptionAnalyzer()

@st.cache_resource
def get_radiology_analyzer():
    return RadiologyReportAnalyzer()

triage_engine = get_triage_engine()
lab_analyzer = get_lab_analyzer()
prescription_analyzer = get_prescription_analyzer()
radiology_analyzer = get_radiology_analyzer()


@st.dialog("Deep Clinical AI Consultation & Q&A", width="large")
def show_deep_ai_report_dialog(report_text: str, report_type: str, lang_code: str):
    lang_name = "English" if lang_code == "en" else ("हिन्दी (Hindi)" if lang_code == "hi" else "ગુજરાતી (Gujarati)")
    
    st.markdown("""
    <style>
    div[data-testid="stDialog"] [data-testid="stChatInput"],
    div[data-testid="stDialog"] [data-testid="stChatInputContainer"],
    div[data-testid="stDialog"] [data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stDialog"] [data-testid="stChatInput"] [data-baseweb="base-input"],
    div[data-testid="stDialog"] [data-testid="stChatInput"] [data-baseweb="input"],
    div[data-testid="stDialog"] [data-testid="stChatInput"] div[data-baseweb="base-input"] {
        background-color: #0F172A !important;
        background: #0F172A !important;
        border: 1.5px solid #1E2E4E !important;
        border-radius: 24px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
    }
    div[data-testid="stDialog"] [data-testid="stChatInput"] textarea {
        background: transparent !important;
        background-color: transparent !important;
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
        border: none !important;
        font-size: 0.90rem !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-testid="stDialog"] [data-testid="stChatInput"] textarea::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
    }
    div[data-testid="stDialog"] [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #2563EB, #06B6D4) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 50% !important;
    }
    div[data-testid="stDialog"] [data-testid="stChatInput"] button svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: rgba(37, 99, 235, 0.08); border-left: 4px solid #2563EB; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <b style="font-size: 0.95rem; color: var(--mm-text-primary);">Clinical Report AI Specialist — {report_type}</b>
            <span class="mm-badge mm-badge-brand">{lang_name}</span>
        </div>
        <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 4px 0 0 0;">
            Ask any question about your medical parameters, out-of-range values, medications, precautions, or health insights in your preferred language.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "p2_deep_ai_chat"not in st.session_state or not st.session_state["p2_deep_ai_chat"]:
        if lang_code == "hi":
            initial_msg = (
                f"नमस्ते! मैंने आपकी **{report_type}** का विस्तृत अध्ययन पूरा कर लिया है।\n\n"f"आप इस रिपोर्ट के बारे में कोई भी प्रश्न पूछ सकते हैं (जैसे: *'मेरा ब्लड ग्रुप क्या है?'*, *'कौन सा टेस्ट नॉर्मल रेंज से बाहर है?'*, *'मुझे क्या सावधानियां रखनी चाहिए?'*)।"
            )
        elif lang_code == "gu":
            initial_msg = (
                f"નમસ્તે! મેં તમારા **{report_type}** નું વિગતવાર વિશ્લેષણ પૂર્ણ કર્યું છે.\n\n"f"તમે આ રિપોર્ટ વિશે કોઈપણ પ્રશ્ન પૂછી શકો છો (જેમ કે: *'મારો બ્લડ ગ્રૂપ કયો છે?'*, *'કઈ વેલ્યુ નોર્મલ નથી?'*, *'મારે કઈ સાવચેતી રાખવી જોઈએ?'*)।"
            )
        else:
            initial_msg = (
                f"Hello! I have analyzed your **{report_type}**.\n\n"f"Feel free to ask me any question regarding your report (e.g. *'What is my blood group?'*, *'Which parameters are out of range?'*, *'What diet or lifestyle changes should I follow?'*)."
            )
        st.session_state["p2_deep_ai_chat"] = [{"role": "assistant", "content": initial_msg}]

    # Render previous conversation
    chat_container = st.container(height=320)
    with chat_container:
        for msg in st.session_state["p2_deep_ai_chat"]:
            avatar = "https://cdn-icons-png.flaticon.com/512/6873/6873405.png" if msg["role"] == "assistant" else "https://cdn-icons-png.flaticon.com/512/11103/11103363.png"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    # Quick Question Chips
    quick_q_map = {
        "en": ["Is anything critical in this report?", "Explain all abnormal values in simple words", "What precautions or diet should I follow?"],
        "hi": ["क्या इस रिपोर्ट में कुछ गंभीर है?", "सभी एब्नॉर्मल वैल्यू को सरल भाषा में समझाएं", "मुझे क्या डाइट या सावधानियां रखनी चाहिए?"],
        "gu": ["શું આ રિપોર્ટમાં કંઈ ગંભીર છે?", "અસામાન્ય વેલ્યુ સરળ ભાષામાં સમજાવો", "મારે કયો ખોરાક અથવા સાવચેતી રાખવી જોઈએ?"]
    }
    quick_questions = quick_q_map.get(lang_code, quick_q_map["en"])

    st.markdown("<div style='font-size: 0.76rem; color: var(--mm-text-secondary); font-weight: 600; margin: 8px 0 4px 0;'>Suggested Questions:</div>", unsafe_allow_html=True)
    q_cols = st.columns(len(quick_questions))
    selected_quick_q = None
    for q_idx, q_text in enumerate(quick_questions):
        with q_cols[q_idx]:
            if st.button(q_text, key=f"p2_quick_q_{q_idx}", use_container_width=True):
                selected_quick_q = q_text

    # User Input
    user_q = st.chat_input("Ask any question about your report...") or selected_quick_q

    if user_q and user_q.strip():
        st.session_state["p2_deep_ai_chat"].append({"role": "user", "content": user_q.strip()})
        with st.spinner("Analyzing report and generating answer..."):
            clinical_ctx = {
                "report_text": report_text,
                "report_type": report_type,
                "age": st.session_state.get("p2_age", "Adult"),
                "gender": st.session_state.get("p2_gender", "Unspecified")
            }
            ai_reply = ask_DocMindX_ai(user_q.strip(), st.session_state["p2_deep_ai_chat"], clinical_ctx, lang_code)
        st.session_state["p2_deep_ai_chat"].append({"role": "assistant", "content": ai_reply})
        st.rerun()


if "triage_result"not in st.session_state:
    st.session_state["triage_result"] = None
if "selected_symptoms_list"not in st.session_state:
    st.session_state["selected_symptoms_list"] = []
if "user_location_cache"not in st.session_state:
    st.session_state["user_location_cache"] = {"lat": 23.0225, "lon": 72.5714, "name": "Ahmedabad, Gujarat"}
if "user_context"not in st.session_state:
    st.session_state["user_context"] = {
        "age": "",
        "age_key": "select",
        "gender": "",
        "gender_key": "select",
        "state": "-- Select State --",
        "location": "-- Select State --",
        "height": "None",
        "weight": "None",
        "blood_group": "None",
        "severity": "Moderate",
        "duration": "1 - 3 Days",
        "conditions": ["None"],
        "medications": "",
        "allergies": "None"
    }

# Canonical Dropdown Key Mappings for Lossless Language Switching
AGE_KEYS = [
    "select", "10_15", "16_20", "21_25", "26_30", "31_35", "36_40",
    "41_45", "46_50", "51_55", "56_60", "61_65", "66_70", "71_75", "76_80", "80_plus"
]
AGE_LABEL_MAP = {
    "select": "select_age_prompt",
    "10_15": "age_10_15",
    "16_20": "age_16_20",
    "21_25": "age_21_25",
    "26_30": "age_26_30",
    "31_35": "age_31_35",
    "36_40": "age_36_40",
    "41_45": "age_41_45",
    "46_50": "age_46_50",
    "51_55": "age_51_55",
    "56_60": "age_56_60",
    "61_65": "age_61_65",
    "66_70": "age_66_70",
    "71_75": "age_71_75",
    "76_80": "age_76_80",
    "80_plus": "age_80_plus",
}

GENDER_KEYS = ["select", "male", "female", "other"]
GENDER_LABEL_MAP = {
    "select": "select_gender_prompt",
    "male": "gender_male",
    "female": "gender_female",
    "other": "gender_other",
}

BLOOD_KEYS = ["select", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "unknown"]

SEVERITY_KEYS = ["mild", "moderate", "severe"]
SEVERITY_LABEL_MAP = {
    "mild": "severity_mild",
    "moderate": "severity_moderate",
    "severe": "severity_severe",
}

DURATION_KEYS = ["today", "1_3", "4_7", "1_2w", "more_2w"]
DURATION_LABEL_MAP = {
    "today": "dur_today",
    "1_3": "dur_1_3",
    "4_7": "dur_4_7",
    "1_2w": "dur_1_2w",
    "more_2w": "dur_more_2w",
}


# Language Options Constants (All-India Multi-Lingual Architecture)
LANG_OPTIONS = [
    "English",
    "Hindi (हिंदी)",
    "Gujarati (ગુજરાતી)",
    "Marathi (मराठी)",
    "Bengali (বাংলা)",
    "Tamil (தமிழ்)",
    "Telugu (తెలుగు)",
    "Kannada (ಕನ್ನಡ)",
    "Malayalam (മലയാളം)",
    "Punjabi (ਪੰਜਾਬੀ)",
    "Odia (ଓଡ଼ିଆ)",
    "Urdu (اردو)"
]
lang_code_map = {
    "English": "en",
    "Hindi (हिंदी)": "hi",
    "Gujarati (ગુજરાતી)": "gu",
    "Marathi (मराठी)": "mr",
    "Bengali (বাংলা)": "bn",
    "Tamil (தமிழ்)": "ta",
    "Telugu (తెలుగు)": "te",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Malayalam (മലയാളം)": "ml",
    "Punjabi (ਪੰਜਾਬੀ)": "pa",
    "Odia (ଓଡ଼ିଆ)": "or",
    "Urdu (اردو)": "ur"
}

# Initialize language keys in session state to prevent default index conflicts
if "app_language" not in st.session_state:
    st.session_state["app_language"] = "English"

for k in ["hdr_lang_p1", "hdr_lang_p2", "hdr_lang_p3", "hdr_lang_p4", "hdr_lang_p5"]:
    if k not in st.session_state:
        st.session_state[k] = st.session_state["app_language"]

def sync_language(source_key):
    new_val = st.session_state.get(source_key)
    if new_val in LANG_OPTIONS:
        st.session_state["app_language"] = new_val
        st.session_state["language"] = lang_code_map.get(new_val, "en")
        for k in ["hdr_lang_p1", "hdr_lang_p2", "hdr_lang_p3", "hdr_lang_p4", "hdr_lang_p5"]:
            if k != source_key:
                st.session_state[k] = new_val

def sync_theme_mode(source_key):
    new_mode = st.session_state.get(source_key, False)
    st.session_state["dark_mode"] = new_mode
    for k in ["hdr_theme_p1", "hdr_theme_p2", "hdr_theme_p3", "hdr_theme_p4", "hdr_theme_p5"]:
        st.session_state[k] = new_mode

def toggle_floating_chat():
    st.session_state["floating_chat_open"] = not st.session_state.get("floating_chat_open", False)

def clear_floating_chat():
    st.session_state["floating_chat_history"] = []

def handle_floating_chat_submit():
    raw_q = st.session_state.get("floating_chat_user_input", "").strip()
    if raw_q:
        st.session_state["floating_chat_history"].append({"role": "user", "content": raw_q})
        st.session_state["pending_chat_query"] = raw_q
    st.session_state["floating_chat_user_input"] = ""

def sync_medical_conditions():
    selected = list(st.session_state.get("selected_conditions_widget", []))
    prev = list(st.session_state.get("prev_selected_conditions", ["None"]))
    if "None" in selected and len(selected) > 1:
        if "None" not in prev:
            selected = ["None"]
        else:
            selected = [c for c in selected if c != "None"]
    elif not selected:
        selected = ["None"]
    st.session_state["selected_conditions_widget"] = selected
    st.session_state["prev_selected_conditions"] = list(selected)
    if "user_context" in st.session_state:
        st.session_state["user_context"]["conditions"] = selected

lang_choice = st.session_state.get("app_language", "English")
lang_code = lang_code_map.get(lang_choice, "en")
st.session_state["language"] = lang_code
T = load_translations(lang_code)

def get_localized_user_val(val_key, raw_val, T, lang_code):
    if not raw_val or str(raw_val).strip().lower() in ["none", "null", "none_selected", "unknown", "કંઈ નથી", "कोई नहीं"]:
        return T.get("val_none", "None")
    
    raw_str = str(raw_val).strip()
    raw_lower = raw_str.lower()
    
    if val_key == "gender":
        if "male" in raw_lower and "female" not in raw_lower:
            return T.get("gender_male", "Male")
        elif "female" in raw_lower:
            return T.get("gender_female", "Female")
        elif "other" in raw_lower:
            return T.get("gender_other", "Other")
            
    elif val_key == "severity":
        if "mild" in raw_lower or "हल्का" in raw_lower or "હળવું" in raw_lower:
            return T.get("severity_mild", "Mild").split("(")[0].strip()
        elif "mod" in raw_lower or "मध्यम" in raw_lower or "મધ્યમ" in raw_lower:
            return T.get("severity_moderate", "Moderate").split("(")[0].strip()
        elif "sev" in raw_lower or "गंभीर" in raw_lower or "ગંભીર" in raw_lower:
            return T.get("severity_severe", "Severe").split("(")[0].strip()
            
    elif val_key == "duration":
        if "today" in raw_lower or "आज" in raw_lower or "આજ" in raw_lower:
            return T.get("dur_today", "Started Today")
        elif "1" in raw_lower and "3" in raw_lower:
            return T.get("dur_1_3", "1 - 3 Days")
        elif "4" in raw_lower and "7" in raw_lower:
            return T.get("dur_4_7", "4 - 7 Days")
        elif "1" in raw_lower and "2" in raw_lower and "week" in raw_lower:
            return T.get("dur_1_2w", "1 - 2 Weeks")
        elif "more" in raw_lower or "વધુ" in raw_lower or "अधिक" in raw_lower:
            return T.get("dur_more_2w", "More than 2 Weeks")
            
    elif val_key == "age":
        if lang_code == "gu":
            return raw_str.replace("Years", "વર્ષ").replace("years", "વર્ષ")
        elif lang_code == "hi":
            return raw_str.replace("Years", "वर्ष").replace("years", "वर्ष")
            
    return raw_str


def render_dynamic_browser_translator(target_lang_code: str):
    """
    DocMindX Translation Engine.

    Uses Python-side static JSON translations (T dict) exclusively.
    Google Translate Widget is intentionally disabled — it caused mixed-language
    output by re-translating already-localized text (treating Gujarati/Hindi as English).

    All 12 Indian languages are fully supported via translations/*.json files.
    The T dict is loaded once per page render based on lang_code, ensuring
    100% consistent, script-correct translations without any mixing.
    """
    # No Google Translate widget injection.
    # Static T dict (loaded above) is the single source of truth.
    pass

# Execute Dynamic Browser Translator Engine (no-op; T dict is active)
render_dynamic_browser_translator(lang_code)

# ── One-time cleanup: remove any stale Google Translate cookies from previous sessions ──
# GT cookies cause the GT banner/toolbar to re-activate on page load, interfering
# with our static T dict translations. This script clears them exactly once per session.
if not st.session_state.get("_gt_cookies_cleared"):
    import streamlit.components.v1 as _st_comps
    _st_comps.html("""
    <script>
    (function() {
        try {
            var doc = window.parent.document;
            doc.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            doc.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" + window.location.hostname;
            var banner = doc.querySelector('iframe.goog-te-banner-frame');
            if (banner) banner.style.display = 'none';
            var body = doc.querySelector('body');
            if (body) body.style.top = '0px';
        } catch(e) {}
    })();
    </script>
    """, height=0, width=0)
    st.session_state["_gt_cookies_cleared"] = True



def render_footer_trust_bar(t_dict=None):
    return """
    <div class="mm-footer-trust-bar" style="border-top: 1.5px solid rgba(148, 163, 184, 0.25); background: transparent; padding: 18px 24px; margin-top: 28px; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; width: 100%;">
            <!-- Brand Info -->
            <div style="display: flex; flex-direction: column;">
                <span style="font-weight: 800; font-size: 0.95rem; color: #1E3A8A; line-height: 1.2;">DocMindX AI &copy; 2026</span>
                <span style="font-size: 0.75rem; color: #64748B; margin-top: 2px;">Enterprise Multilingual Healthcare Suite</span>
            </div>
            <div style="width: 1px; height: 30px; background: #CBD5E1;"></div>
            <!-- Badge 1: Secure & Encrypted -->
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <polyline points="9 12 11 14 15 10"/>
                </svg>
                <span style="font-size: 0.84rem; font-weight: 600; color: #1E293B;">Secure &amp; Encrypted</span>
            </div>
            <div style="width: 1px; height: 30px; background: #CBD5E1;"></div>
            <!-- Badge 2: HIPAA & WHO Compliant -->
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
                <span style="font-size: 0.84rem; font-weight: 600; color: #1E293B;">HIPAA &amp; WHO Compliant</span>
            </div>
            <div style="width: 1px; height: 30px; background: #CBD5E1;"></div>
            <!-- Badge 3: Trusted Healthcare -->
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="#2563EB" stroke="none">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <span style="font-size: 0.84rem; font-weight: 600; color: #1E293B;">Trusted Healthcare</span>
            </div>
            <div style="width: 1px; height: 30px; background: #CBD5E1;"></div>
            <!-- Slogan: Better Health Brighter Tomorrow -->
            <div style="display: flex; align-items: center; gap: 10px;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="#10B981" stroke="none">
                    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12" stroke="#10B981" stroke-width="1.8" stroke-linecap="round"/>
                </svg>
                <span style="font-family: 'Segoe Script', 'Brush Script MT', 'Caveat', cursive; font-size: 1.25rem; color: #2563EB; font-weight: 700; line-height: 1.05; font-style: italic; letter-spacing: -0.2px;">
                    Better Health<br/><span style="font-size: 1.10rem; padding-left: 4px;">Brighter Tomorrow</span>
                </span>
            </div>
        </div>
    </div>
    """

is_dark = st.session_state.get("dark_mode", False)
dark_mode_js = f"""
<script>
(function() {{
    var isDark = {'true' if is_dark else 'false'};
    function applyTheme(dark) {{
        var targets = [document.documentElement, document.body];
        var stApp = document.querySelector('.stApp');
        if (stApp) targets.push(stApp);
        targets.forEach(function(el) {{
            if (el) {{
                el.setAttribute('data-theme', dark ? 'dark' : 'light');
                el.setAttribute('data-dark-mode', dark ? 'true' : 'false');
            }}
        }});
    }}
    applyTheme(isDark);

    // KPI Count-Up Animation Engine
    function runCountUp() {{
        var metricEls = document.querySelectorAll('[data-testid="stMetricValue"], .mm-count-up');
        metricEls.forEach(function(el) {{
            var rawText = (el.innerText || '').trim();
            if (!rawText) return;
            if (el.getAttribute('data-mm-counted') === rawText) return;

            var match = rawText.match(/^([^0-9\\-+]*)([-+]?[0-9,]+(?:\\.[0-9]+)?)(.*)$/);
            if (!match) return;
            var prefix = match[1] || '';
            var numStr = match[2].replace(/,/g, '');
            var suffix = match[3] || '';
            var targetVal = parseFloat(numStr);
            if (isNaN(targetVal)) return;

            var hasDecimals = numStr.indexOf('.') !== -1;
            var decimalPlaces = hasDecimals ? numStr.split('.')[1].length : 0;
            var hasCommas = match[2].indexOf(',') !== -1;

            el.setAttribute('data-mm-counted', rawText);
            var duration = 750;
            var startTime = null;

            function animate(timestamp) {{
                if (!startTime) startTime = timestamp;
                var progress = Math.min((timestamp - startTime) / duration, 1);
                var ease = 1 - Math.pow(1 - progress, 3);
                var currentVal = targetVal * ease;

                var formattedNum = hasDecimals ? currentVal.toFixed(decimalPlaces) : Math.round(currentVal).toString();
                if (hasCommas) {{
                    var parts = formattedNum.split('.');
                    parts[0] = parts[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
                    formattedNum = parts.join('.');
                }}
                el.innerText = prefix + formattedNum + suffix;

                if (progress < 1) {{
                    window.requestAnimationFrame(animate);
                }} else {{
                    el.innerText = rawText;
                }}
            }}
            window.requestAnimationFrame(animate);
        }});
    }}

    // Ripple effect on button clicks
    if (!window._mm_ripple_attached) {{
        window._mm_ripple_attached = true;
        document.addEventListener('click', function(e) {{
            var btn = e.target.closest('.stButton > button, .mm-btn');
            if (!btn) return;
            var rect = btn.getBoundingClientRect();
            var circle = document.createElement('span');
            var diameter = Math.max(btn.clientWidth, btn.clientHeight);
            var radius = diameter / 2;
            circle.style.width = circle.style.height = diameter + 'px';
            circle.style.left = (e.clientX - rect.left - radius) + 'px';
            circle.style.top = (e.clientY - rect.top - radius) + 'px';
            circle.className = 'mm-ripple';
            var existing = btn.querySelector('.mm-ripple');
            if (existing) existing.remove();
            btn.appendChild(circle);
            setTimeout(function() {{ circle.remove(); }}, 600);
        }});
    }}

    var obs = new MutationObserver(function() {{
        applyTheme(isDark);
        runCountUp();
    }});
    obs.observe(document.body, {{ childList: true, subtree: true }});
    setTimeout(function() {{ applyTheme(isDark); runCountUp(); }}, 100);
    setTimeout(function() {{ applyTheme(isDark); runCountUp(); }}, 400);
    setTimeout(function() {{ applyTheme(isDark); runCountUp(); }}, 900);

    // Listen for theme toggle messages from iframe component
    window.addEventListener("message", function(e) {{
        if (e.data && e.data.type === "DocMindX_theme_toggle") {{
            var newDark = e.data.dark;
            applyTheme(newDark);
            try {{
                var url = new URL(window.location.href);
                url.searchParams.set("theme", newDark ? "dark" : "light");
                if (window.history && window.history.replaceState) {{
                    window.history.replaceState(null, "", url.toString());
                }}
            }} catch(err) {{}}
        }}
    }});
}})();
</script>
"""
st.markdown(dark_mode_js, unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    # Sidebar Brand
    if LOGO_DARK_B64:
        st.markdown(f"""
        <div class="mm-sidebar-brand" style="text-align: center; padding: 14px 10px 14px 10px; margin-bottom: 14px; background: linear-gradient(180deg, rgba(37, 99, 235, 0.16) 0%, rgba(15, 23, 42, 0.5) 100%); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 14px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);">
            <img src="{LOGO_DARK_B64}" style="width: 135px; height: auto; border-radius: 10px; margin: 0 auto 6px auto; display: block; filter: drop-shadow(0 4px 12px rgba(37, 99, 235, 0.35));" alt="DocMindX AI Logo"/>
            <div style="font-size: 0.76rem; color: #94A3B8; font-weight: 500; margin-bottom: 8px;">{T.get("app_subtitle", "Intelligent Healthcare Powered by AI")}</div>
            <span class="mm-badge" style="background: rgba(37, 99, 235, 0.20); color: #93C5FD; border: 1px solid rgba(59, 130, 246, 0.45); font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 20px;">{T.get("enterprise_suite", "V2.0 ENTERPRISE SUITE")}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="mm-sidebar-brand" style="padding: 14px 10px 14px 10px; margin-bottom: 14px; background: linear-gradient(180deg, rgba(37, 99, 235, 0.16) 0%, rgba(15, 23, 42, 0.5) 100%); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 14px;">
            <h2 style="color: #FFFFFF; margin: 0; font-size: 1.25rem; font-weight: 800; letter-spacing: -0.01em;">{T.get("app_brand", "DocMindX AI")}</h2>
            <p style="color: #94A3B8; margin: 4px 0 8px 0; font-size: 0.8rem;">{T.get("app_subtitle", "Intelligent Healthcare Powered by AI")}</p>
            <span class="mm-badge" style="background: rgba(37, 99, 235, 0.20); color: #93C5FD; border: 1px solid rgba(59, 130, 246, 0.45); font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 20px;">{T.get("enterprise_suite", "V2.0 ENTERPRISE SUITE")}</span>
        </div>
        """, unsafe_allow_html=True)

    # Clinical Navigation (Clean Equal-Width Rows, Zero Emojis)
    st.markdown(f"""
    <style>
    /* Nav group container — must NOT overflow sidebar */
    [data-testid="stSidebar"] [data-testid="stRadio"],
    [data-testid="stSidebar"] .stRadio,
    [data-testid="stSidebar"] div[role="radiogroup"] {{
        width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: stretch !important;
        gap: 6px !important;
        overflow: hidden !important;
        box-sizing: border-box !important;
    }}
    /* Each nav item row */
    [data-testid="stSidebar"] div[role="radiogroup"] > label,
    [data-testid="stSidebar"] label[data-baseweb="radio"],
    [data-testid="stSidebar"] div[data-baseweb="radio"] {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
        display: flex !important;
        box-sizing: border-box !important;
        align-items: center !important;
        justify-content: flex-start !important;
        padding: 10px 12px !important;
        border-radius: 10px !important;
        overflow: hidden !important;
        background-color: #131E32 !important;
        border: 1px solid #1E2E4E !important;
        cursor: pointer !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
        background-color: #1A2845 !important;
        border-color: #38BDF8 !important;
        transform: translateX(2px) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {{
        background: linear-gradient(90deg, rgba(37, 99, 235, 0.35) 0%, rgba(6, 182, 212, 0.18) 100%) !important;
        border: 1.2px solid #3B82F6 !important;
        border-left: 4px solid #3B82F6 !important;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.25) !important;
    }}
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child:not([data-testid="stMarkdownContainer"]) {{
        display: none !important;
    }}
    /* Label text — must not wrap or overflow */
    [data-testid="stSidebar"] div[role="radiogroup"] > label [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] div[role="radiogroup"] > label p,
    [data-testid="stSidebar"] div[role="radiogroup"] > label span {{
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        font-size: 0.87rem !important;
        font-weight: 600 !important;
        color: #F8FAFC !important;
        line-height: 1.2 !important;
        flex: 1 1 0% !important;
    }}
    </style>
    <div style='font-size: 0.71rem; font-weight: 700; color: #94A3B8; letter-spacing: 0.06em; text-transform: uppercase; margin: 4px 0 6px 0;'>{T.get('clinical_navigation', 'CLINICAL MODULE NAVIGATION')}</div>
    """, unsafe_allow_html=True)
    
    panel_map = {
        "Health Assessment": T.get("nav_health_assessment", "Health Assessment"),
        "Medical Report": T.get("nav_medical_report", "Medical Report"),
        "Nearby Healthcare": T.get("nav_nearby_healthcare", "Nearby Healthcare"),
        "Health Records": T.get("nav_health_records", "Health Records"),
        "National Command Center": T.get("nav_command_center", "National Command Center"),
        "About DocMindX AI": T.get("nav_about", "About DocMindX AI")
        }
    panel_keys = list(panel_map.keys())

    def _on_clinical_nav_change():
        chosen = st.session_state.get("clinical_module_nav_radio")
        if chosen in panel_keys:
            st.session_state["active_panel"] = chosen

    active_p = st.session_state.get("active_panel", "Health Assessment")

    if "clinical_module_nav_radio" not in st.session_state:
        st.session_state["clinical_module_nav_radio"] = active_p if active_p in panel_keys else None
    elif active_p in panel_keys:
        st.session_state["clinical_module_nav_radio"] = active_p
    else:
        st.session_state["clinical_module_nav_radio"] = None

    st.radio(
        "Clinical Module Navigation",
        options=panel_keys,
        format_func=lambda k: panel_map[k],
        key="clinical_module_nav_radio",
        on_change=_on_clinical_nav_change,
        label_visibility="collapsed"
    )

    # Clinical Identity & Profile Card in Sidebar
    curr_sb_user = auth_ui.get_current_user()
    if curr_sb_user and auth_ui.is_authenticated():
        is_sb_admin = auth_svc.is_admin_session(curr_sb_user)
        badge_text = "ADMINISTRATOR" if is_sb_admin else "PATIENT"
        badge_bg = "rgba(239, 68, 68, 0.18)" if is_sb_admin else "rgba(37, 99, 235, 0.15)"
        badge_color = "#F87171" if is_sb_admin else "#60A5FA"
        avatar_bg = "#DC2626" if is_sb_admin else "#2563EB"
        st.markdown(f"""
        <div class="mm-sidebar-user" style="background: #111B2E; border: 1px solid #1E2E4E; border-radius: 12px; padding: 12px; margin-top: 14px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 34px; height: 34px; border-radius: 10px; background: {avatar_bg}; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0;">
                    {curr_sb_user.get('full_name', 'U')[:1].upper()}
                </div>
                <div style="min-width: 0; flex: 1;">
                    <div style="font-weight: 700; font-size: 0.82rem; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{curr_sb_user.get('full_name', 'Patient')}</div>
                    <div style="font-size: 0.70rem; color: #94A3B8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{curr_sb_user.get('email', '')}</div>
                </div>
            </div>
            <div style="margin-top: 6px; display: inline-block; padding: 2px 8px; border-radius: 5px; background: {badge_bg}; color: {badge_color}; font-size: 0.64rem; font-weight: 800; letter-spacing: 0.05em;">
                {badge_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if is_sb_admin:
            sb_c1, sb_c2 = st.columns([1, 1])
            with sb_c1:
                if st.button("Admin", key="sb_btn_admin", use_container_width=True):
                    st.session_state["active_panel"] = "Admin Panel"
                    st.rerun()
            with sb_c2:
                if st.button("Logout", key="sb_btn_signout", use_container_width=True):
                    auth_ui.logout_user()
                    st.rerun()
        else:
            # Normal user ke liye sirf Logout / Sign Out button
            if st.button("Sign Out", key="sb_btn_signout", use_container_width=True):
                auth_ui.logout_user()
                st.rerun()
    else:
        st.markdown(f"""
        <div class="mm-sidebar-guest" style="background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 12px; padding: 12px; margin-top: 14px;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #93C5FD; margin-bottom: 3px;">CLINICAL IDENTITY</div>
            <div style="font-size: 0.71rem; color: #94A3B8; line-height: 1.35; margin-bottom: 8px;">Sign in to access your permanent health vault & family profiles.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sign In / Register", key="sb_btn_signin", type="primary", use_container_width=True):
            st.session_state["active_panel"] = "Account / Authentication"
            st.rerun()

    # 5. Safety & Privacy Card (Unified 12px Radius, Dark Mode Parity, No Emojis)
    st.markdown(f"""
    <div class="mm-sidebar-trust"style="background: #111B2E; border: 1px solid #1E2E4E; border-radius: 12px; padding: 14px; margin-top: 14px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
            <b style="color: #F8FAFC; font-size: 0.82rem; letter-spacing: 0.04em;">{T.get("safety_privacy_title", "SAFETY & PRIVACY")}</b>
        </div>
        <p style="margin: 0; font-size: 0.74rem; color: #94A3B8; line-height: 1.45;">{T.get("safety_privacy_desc", "Your data is encrypted and protected following HIPAA & WHO guidelines.")}</p>
    </div>
    <div class="mm-sidebar-warning"style="background: rgba(234, 88, 12, 0.09); border: 1px solid rgba(234, 88, 12, 0.35); border-left: 4px solid #EA580C; border-radius: 10px; padding: 12px 14px; margin-top: 10px;">
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
            <span style="font-size: 0.85rem;"></span>
            <b style="color: #FB923C; font-size: 0.78rem; letter-spacing: 0.03em; text-transform: uppercase;">{T.get("sidebar_warning_title", "CLINICAL ADVISORY")}</b>
        </div>
        <p style="margin: 0; font-size: 0.72rem; color: #E2E8F0; line-height: 1.45;">{T.get("sidebar_warning_desc", "DocMindX AI can make mistakes. Do not rely solely on AI suggestions — always consult a certified doctor or licensed physician for clinical decisions.")}</p>
    </div>
    """, unsafe_allow_html=True)

    # 6. System Status Indicator
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: #10B981; margin-top: 16px; padding-left: 2px;">
        <span class="ai-badge-dot"style="background: #10B981; width: 7px; height: 7px;"></span>
        <span>{T.get("all_systems_operational", "All Systems Operational")}</span>
    </div>
    """, unsafe_allow_html=True)


# ----------------- MAIN CONTENT AREA -----------------

# ==============================================================================
# MODULE 1: AI HEALTH ASSESSMENT
# ==============================================================================
if st.session_state["active_panel"] == "Health Assessment":
    current_step = st.session_state.get("assessment_step", 1)

    # 1. Top Header Bar (Identical and consistent with Modules 2, 3, 4)
    assessment_icon_html = '<div style="width: 52px; height: 52px; border-radius: 14px; background: rgba(37, 99, 235, 0.08); border: 1.5px solid #2563EB; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); flex-shrink: 0;"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 3v5a5.5 5.5 0 0 0 11 0V3"></path><path d="M10 13.5v3.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-1.5"></path><circle cx="17" cy="15.5" r="2.5"></circle></svg></div>'
    with st.container(key="mm_top_header_card_1"):
        hdr_c1, hdr_c2, hdr_c3, hdr_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr_c1:
            title_p1 = T.get("p1_header_title", "AI Health & Symptom Assessment")
            sub_p1 = T.get("p1_header_subtitle", "Provide your symptoms and demographic details. Our clinical intelligence engine analyzes potential conditions and triages severity.")
            safe_markdown(
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{assessment_icon_html}'
                f'<div style="min-width: 0; flex: 1;">'
                f'<div style="margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">{title_p1}</div>'
                f'<div style="margin-top: 4px; font-size: 0.85rem; color: var(--mm-text-secondary); line-height: 1.35;">{sub_p1}</div>'
                f'</div>'
                f'</div>'
            )
        with hdr_c2:
            safe_markdown(
                f'<div style="display: flex; justify-content: center; align-items: center; height: 38px;">'
                f'<span style="height: 36px; padding: 0 16px; border-radius: 20px; background: rgba(16, 185, 129, 0.10); border: 1px solid rgba(16, 185, 129, 0.3); color: #059669; font-weight: 700; font-size: 0.80rem; display: inline-flex; align-items: center; gap: 8px;">'
                f'<span style="width: 8px; height: 8px; border-radius: 50%; background: #10B981; display: inline-block;"></span>'
                f'{T.get("ai_online", "AI System Online")}'
                f'</span>'
                f'</div>'
            )
        with hdr_c3:
            header_lang_1 = st.selectbox(
                "Header Lang Selector",
                options=LANG_OPTIONS,
                key="hdr_lang_p1",
                label_visibility="collapsed",
                on_change=sync_language,
                args=("hdr_lang_p1",)
            )
        with hdr_c4:
            new_theme_p1 = theme_toggle_switch(is_dark=st.session_state.get("dark_mode", False), key="hdr_sun_moon_p1")
            if new_theme_p1 != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = new_theme_p1
                st.rerun()

    # 2. Stepping Progress Bar with Horizontal Connecting Lines (Matching Image 2)
    s1_active = "active" if current_step == 1 else ("done" if current_step > 1 else "")
    s2_active = "active" if current_step == 2 else ("done" if current_step > 2 else "")
    s3_active = "active" if current_step == 3 else ("done" if current_step > 3 else "")
    s4_active = "active" if current_step == 4 else ""
    st.markdown(f"""
    <div class="mm-stepper">
        <div class="mm-step-item">
            <div class="mm-step-num {s1_active}">1</div>
            <div>
                <div class="mm-step-text-title {'active' if current_step == 1 else ''}">{T.get("step1_title", "About You")}</div>
                <div class="mm-step-text-sub">{T.get("step1_sub", "Demographic Info")}</div>
            </div>
        </div>
        <div class="mm-step-connector"><span class="mm-step-arrow">→</span></div>
        <div class="mm-step-item">
            <div class="mm-step-num {s2_active}">2</div>
            <div>
                <div class="mm-step-text-title {'active' if current_step == 2 else ''}">{T.get("step2_title", "Symptoms")}</div>
                <div class="mm-step-text-sub">{T.get("step2_sub", "Clinical Presentation")}</div>
            </div>
        </div>
        <div class="mm-step-connector"><span class="mm-step-arrow">→</span></div>
        <div class="mm-step-item">
            <div class="mm-step-num {s3_active}">3</div>
            <div>
                <div class="mm-step-text-title {'active' if current_step == 3 else ''}">{T.get("step3_title", "Medical History")}</div>
                <div class="mm-step-text-sub">{T.get("step3_sub", "Prior Conditions")}</div>
            </div>
        </div>
        <div class="mm-step-connector"><span class="mm-step-arrow">→</span></div>
        <div class="mm-step-item">
            <div class="mm-step-num {s4_active}">4</div>
            <div>
                <div class="mm-step-text-title {'active' if current_step == 4 else ''}">{T.get("step4_title", "Analysis & Triage")}</div>
                <div class="mm-step-text-sub">{T.get("step4_sub", "Clinical Insights")}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Patient Profile / Family Member Selection for Authenticated Sessions
    curr_auth_user = auth_ui.get_current_user()
    if curr_auth_user and auth_ui.is_authenticated():
        p1_patient_ctx = family_ui.render_scan_patient_selector(curr_auth_user, key_prefix="p1_scan_selector")
        st.session_state["p1_patient_context"] = p1_patient_ctx
        if p1_patient_ctx.get("mode") in ["PROFILE", "FAMILY_MEMBER"] and p1_patient_ctx.get("context"):
            ctx_data = p1_patient_ctx["context"]
            if ctx_data.get("existing_conditions"):
                st.session_state["user_context"]["conditions"] = list(set(st.session_state["user_context"].get("conditions", []) + ctx_data["existing_conditions"]))
            if ctx_data.get("current_medicines"):
                st.session_state["user_context"]["medications"] = list(set(st.session_state["user_context"].get("medications", []) + ctx_data["current_medicines"]))
    else:
        st.session_state["p1_patient_context"] = {"mode": "GENERAL", "member_id": None, "name": "General Patient"}

    # ----------------- STEP 1: ABOUT YOU -----------------
    if current_step == 1:
        with st.container(key="assessment_step_card", border=True):
            safe_markdown(f"""
            <div class="mm-step-card-header" style="background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(59,130,246,0.02) 100%); border-bottom: 1.5px solid #BFDBFE; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; border-radius: 16px 16px 0 0; margin: -16px -16px 16px -16px;">
                <div class="mm-step-header-left" style="display: flex; align-items: center; gap: 14px;">
                    <div class="mm-step-header-icon" style="width: 44px; height: 44px; border-radius: 12px; background: #EFF6FF; border: 1.2px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title" style="font-size: 1.25rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1.25; margin: 0;">{T.get("card_about_you", "Patient Demographics")}</div>
                        <div class="mm-step-header-sub" style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 3px; line-height: 1.35;">{T.get("about_you_note", "Your demographic data helps our clinical AI calculate precise body mass and physiological risk factors.")}</div>
                    </div>
                </div>
                <div class="mm-step-progress-indicator" style="display: flex; align-items: center; gap: 10px; background: var(--mm-card-bg, #FFFFFF); border: 1px solid #BFDBFE; border-radius: 10px; padding: 6px 14px; box-shadow: 0 1px 3px rgba(37,99,235,0.06);">
                    <div class="mm-step-progress-bar" style="width: 3.5px; height: 28px; background: #2563EB; border-radius: 2px;"></div>
                    <div class="mm-step-progress-text" style="display: flex; flex-direction: column; line-height: 1.15;">
                        <span class="mm-step-progress-step" style="font-size: 0.74rem; font-weight: 800; color: #2563EB; letter-spacing: 0.5px;">STEP 1 OF 4</span>
                        <span class="mm-step-progress-sub" style="font-size: 0.68rem; font-weight: 700; color: var(--mm-text-secondary, #64748B); letter-spacing: 0.5px;">BASIC INFORMATION</span>
                    </div>
                </div>
            </div>
            """)

            r1_c1, r1_c2, r1_c3 = st.columns(3)
            with r1_c1:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-weight: 700; font-size: 0.84rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                    </div>
                    <span>{T.get('label_age_group', 'Age Group')} <span style="color: #EF4444;">*</span></span>
                </div>
                """)
                cur_age_key = st.session_state["user_context"].get("age_key", "select")
                if cur_age_key not in AGE_KEYS:
                    cur_age_key = "select"
                age_idx = AGE_KEYS.index(cur_age_key)
                sel_age_key = st.selectbox(
                    "Age Group",
                    options=AGE_KEYS,
                    index=age_idx,
                    format_func=lambda k: T.get(AGE_LABEL_MAP.get(k, "select_age_prompt"), k),
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["age_key"] = sel_age_key
                st.session_state["user_context"]["age"] = "" if sel_age_key == "select" else T.get(AGE_LABEL_MAP.get(sel_age_key, "select_age_prompt"), sel_age_key)

            with r1_c2:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-weight: 700; font-size: 0.84rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="5"></circle>
                            <path d="M11 16v5M8 18.5h6M14.5 7.5L19 3M19 6.5V3h-3.5"></path>
                        </svg>
                    </div>
                    <span>{T.get('label_gender', 'Biological Gender')} <span style="color: #EF4444;">*</span></span>
                </div>
                """)
                cur_gen_key = st.session_state["user_context"].get("gender_key", "select")
                if cur_gen_key not in GENDER_KEYS:
                    cur_gen_key = "select"
                gen_idx = GENDER_KEYS.index(cur_gen_key)
                sel_gen_key = st.selectbox(
                    "Biological Gender",
                    options=GENDER_KEYS,
                    index=gen_idx,
                    format_func=lambda k: T.get(GENDER_LABEL_MAP.get(k, "select_gender_prompt"), k),
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["gender_key"] = sel_gen_key
                st.session_state["user_context"]["gender"] = "" if sel_gen_key == "select" else T.get(GENDER_LABEL_MAP.get(sel_gen_key, "select_gender_prompt"), sel_gen_key)

            with r1_c3:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-weight: 700; font-size: 0.84rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                            <circle cx="12" cy="10" r="3"></circle>
                        </svg>
                    </div>
                    <span>{T.get('label_state', 'State / Location')} <span style="color: #EF4444;">*</span></span>
                </div>
                """)
                cur_st = st.session_state["user_context"].get("state", "-- Select State --")
                if cur_st not in INDIAN_STATES:
                    cur_st = "-- Select State --"
                st_idx = INDIAN_STATES.index(cur_st)
                sel_state = st.selectbox(
                    "State / Location",
                    options=INDIAN_STATES,
                    index=st_idx,
                    format_func=lambda s: T.get("select_state_prompt", "-- Select State --") if s == "-- Select State --" else s,
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["state"] = "" if sel_state == "-- Select State --" else sel_state
                st.session_state["user_context"]["location"] = st.session_state["user_context"]["state"]

            r2_c1, r2_c2, r2_c3 = st.columns(3)
            with r2_c1:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; margin-top: 10px; font-weight: 700; font-size: 0.84rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="7" y="2" width="10" height="20" rx="2"></rect>
                            <line x1="7" y1="6" x2="11" y2="6"></line>
                            <line x1="7" y1="10" x2="13" y2="10"></line>
                            <line x1="7" y1="14" x2="11" y2="14"></line>
                            <line x1="7" y1="18" x2="13" y2="18"></line>
                        </svg>
                    </div>
                    <span>{T.get('label_height', 'Height (cm)')} ({T.get('optional', 'Optional')})</span>
                </div>
                """)
                cur_h = st.session_state["user_context"].get("height", "None")
                h_val_display = "" if cur_h in ["None", ""] else cur_h
                height_val = st.text_input(
                    "Height (cm)",
                    value=h_val_display,
                    placeholder=T.get("placeholder_height", "Optional (e.g. 175 cm)"),
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["height"] = height_val.strip() if height_val.strip() else "None"

            with r2_c2:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; margin-top: 10px; font-weight: 700; font-size: 0.84rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="3" width="18" height="18" rx="4"></rect>
                            <path d="M9 7h6a1 1 0 0 1 1 1v1a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1Z"></path>
                        </svg>
                    </div>
                    <span>{T.get('label_weight', 'Weight (kg)')} ({T.get('optional', 'Optional')})</span>
                </div>
                """)
                cur_w = st.session_state["user_context"].get("weight", "None")
                w_val_display = "" if cur_w in ["None", ""] else cur_w
                weight_val = st.text_input(
                    "Weight (kg)",
                    value=w_val_display,
                    placeholder=T.get("placeholder_weight", "Optional (e.g. 65 kg)"),
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["weight"] = weight_val.strip() if weight_val.strip() else "None"

            with r2_c3:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; margin-top: 10px; font-weight: 700; font-size: 0.84rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"></path>
                        </svg>
                    </div>
                    <span>{T.get('label_blood_group', 'Blood Group')} ({T.get('optional', 'Optional')})</span>
                </div>
                """)
                none_label = T.get("opt_none", "None")
                blood_opts = [none_label, "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", T.get("bg_unknown", "Unknown")]
                cur_bg = st.session_state["user_context"].get("blood_group", "None")
                bg_idx = blood_opts.index(cur_bg) if cur_bg in blood_opts else 0
                blood_group = st.selectbox(
                    "Blood Group",
                    blood_opts,
                    index=bg_idx,
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["blood_group"] = blood_group

        # Symptoms Search & Clinical Triage Card
        with st.container(key="symptoms_search_card", border=True):
            safe_markdown(f"""
            <div class="mm-symptoms-card-header">
                <div class="mm-symptoms-header-left">
                    <div class="mm-symptoms-header-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#2563EB"/>
                            <path d="M14 2V8H20" fill="#93C5FD"/>
                            <path d="M8 12H16M8 15H16M8 18H13" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-symptoms-header-title">{T.get("card_symptoms_title", "Clinical Symptoms")} <span style="color: #EF4444;">*</span></div>
                        <div class="mm-symptoms-header-sub">{T.get("symptom_search_placeholder", "Search and add symptoms (e.g. fever, headache, cough)...")}</div>
                    </div>
                </div>
            </div>
            """)

            symptoms_df = triage_engine.df_symptoms
            sym_map_gu = {}
            sym_map_hi = {}
            if not symptoms_df.empty:
                for _, row in symptoms_df.iterrows():
                    eng_sym = str(row.get("symptom_name", "")).strip()
                    if "symptom_name_gu" in row and pd.notna(row["symptom_name_gu"]):
                        sym_map_gu[eng_sym] = str(row["symptom_name_gu"]).strip()
                    if "symptom_name_hi" in row and pd.notna(row["symptom_name_hi"]):
                        sym_map_hi[eng_sym] = str(row["symptom_name_hi"]).strip()

            major_diseases_df = getattr(triage_engine, "df_major_diseases", pd.DataFrame())
            dis_map_hi = {}
            dis_map_gu = {}
            if not major_diseases_df.empty:
                for _, d_row in major_diseases_df.iterrows():
                    d_eng = str(d_row.get("disease_name", "")).strip()
                    if "disease_name_hi" in d_row and pd.notna(d_row["disease_name_hi"]):
                        dis_map_hi[d_eng] = str(d_row["disease_name_hi"]).strip()
                    if "disease_name_gu" in d_row and pd.notna(d_row["disease_name_gu"]):
                        dis_map_gu[d_eng] = str(d_row["disease_name_gu"]).strip()

            def format_symptom_display(s_name):
                if lang_code == "gu":
                    if s_name in dis_map_gu:
                        return f"{dis_map_gu[s_name]} ({s_name})"
                    gu_val = sym_map_gu.get(s_name)
                    return f"{gu_val} ({s_name})" if gu_val and gu_val != s_name else s_name
                elif lang_code == "hi":
                    if s_name in dis_map_hi:
                        return f"{dis_map_hi[s_name]} ({s_name})"
                    hi_val = sym_map_hi.get(s_name)
                    return f"{hi_val} ({s_name})" if hi_val and hi_val != s_name else s_name
                elif not major_diseases_df.empty and s_name in major_diseases_df["disease_name"].values:
                    return f"{s_name} (Major Condition)"
                return s_name

            # Build search options combining symptoms and 100+ major Indian diseases
            all_symptom_names = []
            if not symptoms_df.empty:
                all_symptom_names = symptoms_df["symptom_name"].tolist()
            
            major_disease_names = []
            if not major_diseases_df.empty:
                major_disease_names = major_diseases_df["disease_name"].tolist()

            combined_search_options = major_disease_names + all_symptom_names

            s_col1, s_col2 = st.columns([2.8, 1.2], vertical_alignment="center")
            with s_col1:
                search_sym = st.multiselect(
                    "Search symptoms or major diseases...",
                    options=combined_search_options,
                    default=[s for s in st.session_state["selected_symptoms_list"] if s in combined_search_options],
                    format_func=format_symptom_display,
                    label_visibility="collapsed",
                    placeholder=T.get("symptom_search_placeholder", "Search and add symptoms (e.g. fever, headache, cough)...")
                )
                for s in search_sym:
                    if s not in st.session_state["selected_symptoms_list"]:
                        st.session_state["selected_symptoms_list"].append(s)
                    if not major_diseases_df.empty and s in major_diseases_df["disease_name"].values:
                        clean_dname = s.strip()
                        d_match = major_diseases_df[major_diseases_df["disease_name"] == clean_dname]
                        if not d_match.empty:
                            raw_syms = d_match.iloc[0].get("symptoms", [])
                            if isinstance(raw_syms, str):
                                try:
                                    d_syms = eval(raw_syms) if raw_syms.startswith("[") else [x.strip() for x in raw_syms.split(",")]
                                except Exception:
                                    d_syms = [x.strip() for x in raw_syms.split(",")]
                            else:
                                d_syms = list(raw_syms) if isinstance(raw_syms, (list, tuple)) else []
                            for ds in d_syms:
                                if ds not in st.session_state["selected_symptoms_list"]:
                                    st.session_state["selected_symptoms_list"].append(ds)
                            st.session_state["detected_chief_condition"] = d_match.iloc[0].to_dict()
                st.session_state["user_context"]["symptoms"] = list(st.session_state["selected_symptoms_list"])

            with s_col2:
                describe_words = st.button(T.get("btn_describe_words", "Describe in Your Own Words"), key="btn_describe_words", use_container_width=True)

            if describe_words or st.session_state.get("show_free_text_nlp"):
                st.session_state["show_free_text_nlp"] = True
                st.markdown("""
                <div class="mm-extractor-box" style="background: rgba(37, 99, 235, 0.04); border: 1.2px solid rgba(37, 99, 235, 0.22); border-radius: 12px; padding: 12px 16px; margin: 8px 0 12px 0;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 3px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="2" y1="12" x2="22" y2="12"></line>
                            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                        </svg>
                        <b style="font-size: 0.86rem; color: #DC2626;">DocMindX AI Multilingual Clinical Extractor (English / हिन्दी / ગુજરાતી)</b>
                    </div>
                    <p style="font-size: 0.78rem; color: var(--mm-text-secondary); margin: 2px 0 4px 26px;">
                        Type any condition, disease (e.g. <i>"blood cancer"</i>, <i>"हार्ट अटैक"</i>, <i>"ડાયાબિટીસ"</i>), or symptoms in your own words.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form("p1_free_text_form", clear_on_submit=False, border=False):
                    ft_c1, ft_c2 = st.columns([3, 1.2])
                    with ft_c1:
                        free_sym_input = st.text_input(
                            "Describe in Your Own Words",
                            placeholder='e.g. "blood cancer", "Severe chest pain and sweating", "મને 3 દિવસથી ખૂબ તાવ અને ઉધરસ છે"...',
                            key="p1_free_text_input",
                            label_visibility="collapsed"
                        )
                    with ft_c2:
                        extract_nlp_btn = st.form_submit_button("Extract with DocMindX AI", type="primary", use_container_width=True)

                if extract_nlp_btn and free_sym_input and free_sym_input.strip():
                    query_text = free_sym_input.strip()
                    with st.spinner("DocMindX AI analyzing keywords and extracting clinical symptoms..."):
                        extracted_nlp = symptom_extractor.extract_symptoms_and_medicines(query_text, user_lang=lang_code)
                        new_added = 0
                        for sname in extracted_nlp.get("symptom_labels", []):
                            if sname not in st.session_state["selected_symptoms_list"]:
                                st.session_state["selected_symptoms_list"].append(sname)
                                new_added += 1
                        
                        if extracted_nlp.get("detected_disease"):
                            st.session_state["detected_chief_condition"] = extracted_nlp["detected_disease"]
                        
                        st.session_state["nlp_medicines"] = extracted_nlp.get("recommended_medicines", [])
                        
                        if extracted_nlp.get("detected_disease"):
                            d_info = extracted_nlp["detected_disease"]
                            d_disp_name = d_info.get("name_hi") if lang_code == "hi" else (d_info.get("name_gu") if lang_code == "gu" else d_info.get("name"))
                            st.session_state["p1_nlp_msg"] = f"DocMindX AI Detected: **{d_disp_name}** ({d_info.get('category')}) — {len(extracted_nlp.get('symptom_labels', []))} clinical symptoms mapped!"
                        elif new_added > 0:
                            st.session_state["p1_nlp_msg"] = f"DocMindX AI Extracted {new_added} clinical symptoms from your description!"
                        else:
                            st.session_state["p1_nlp_msg"] = "DocMindX AI: No matching symptoms found. Try describing symptoms like fever, headache, etc."
                        st.rerun()

                st.markdown(f"""
                <div style='display: flex; align-items: center; gap: 8px; font-size: 0.82rem; font-weight: 700; color: var(--mm-text-primary); margin: 12px 0 6px 0;'>
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                        <line x1="12" y1="19" x2="12" y2="23"/>
                        <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                    <span>{T.get('voice_input_prompt', 'Or Speak Your Symptoms (Google Cloud Speech-to-Text):')}</span>
                </div>
                """, unsafe_allow_html=True)
                voice_symptom_audio = st.audio_input("Speak Symptoms", key="p1_voice_symptom_mic", label_visibility="collapsed")
                if voice_symptom_audio:
                    import hashlib
                    audio_bytes = voice_symptom_audio.getvalue() if hasattr(voice_symptom_audio, "getvalue") else b""
                    audio_hash = hashlib.md5(audio_bytes).hexdigest() if audio_bytes else ""
                    if audio_hash and st.session_state.get("last_processed_audio_hash") != audio_hash:
                        st.session_state["last_processed_audio_hash"] = audio_hash
                        with st.spinner("Transcribing speech with DocMindX AI Speech-to-Text..."):
                            transcribed_text = transcribe_audio(voice_symptom_audio, language_code=lang_code)
                        if transcribed_text:
                            with st.spinner("Extracting clinical symptoms from voice input..."):
                                extracted_voice = symptom_extractor.extract_symptoms_and_medicines(transcribed_text, user_lang=lang_code)
                                v_added = 0
                                for sname in extracted_voice.get("symptom_labels", []):
                                    if sname not in st.session_state["selected_symptoms_list"]:
                                        st.session_state["selected_symptoms_list"].append(sname)
                                        v_added += 1
                                if extracted_voice.get("detected_disease"):
                                    st.session_state["detected_chief_condition"] = extracted_voice["detected_disease"]
                                st.session_state["p1_nlp_msg"] = f"Voice Transcribed: \"{transcribed_text}\" — Mapped {v_added} clinical symptoms!"
                                conf_speech = synthesize_speech(f"Recorded symptoms: {transcribed_text}", lang=lang_code)
                                if conf_speech:
                                    st.session_state["p1_voice_conf_audio"] = conf_speech
                            st.rerun()

                if st.session_state.get("p1_voice_conf_audio"):
                    st.audio(st.session_state["p1_voice_conf_audio"])

                if st.session_state.get("p1_nlp_msg"):
                    st.success(st.session_state["p1_nlp_msg"])

            st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 8px; font-size: 0.84rem; font-weight: 800; color: var(--mm-text-primary); margin: 14px 0 8px 0;'>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="#2563EB">
                    <rect x="3" y="3" width="4" height="4" rx="1"/>
                    <rect x="10" y="3" width="4" height="4" rx="1"/>
                    <rect x="17" y="3" width="4" height="4" rx="1"/>
                    <rect x="3" y="10" width="4" height="4" rx="1"/>
                    <rect x="10" y="10" width="4" height="4" rx="1"/>
                    <rect x="17" y="10" width="4" height="4" rx="1"/>
                    <rect x="3" y="17" width="4" height="4" rx="1"/>
                    <rect x="10" y="17" width="4" height="4" rx="1"/>
                    <rect x="17" y="17" width="4" height="4" rx="1"/>
                </svg>
                <span>{T.get('popular_symptoms', 'Common Symptoms:')}</span>
            </div>
            """, unsafe_allow_html=True)
            pop_symptoms_data = [
                {"key": "Fever", "en": "Fever", "hi": "बुखार", "gu": "તાવ"},
                {"key": "Headache", "en": "Headache", "hi": "सिरदर्द", "gu": "માથાનો દુખાવો"},
                {"key": "Cough", "en": "Cough", "hi": "खांसी", "gu": "ખાંસી"},
                {"key": "Nausea", "en": "Nausea", "hi": "जी मिचलाना", "gu": "ઉબકા"},
                {"key": "Fatigue", "en": "Fatigue", "hi": "थकान", "gu": "થાક"},
                {"key": "Sore Throat", "en": "Sore Throat", "hi": "गले में खराश", "gu": "ગળામાં દુખાવો"},
                {"key": "Body Pain", "en": "Body Pain", "hi": "बदन दर्द", "gu": "શરીરનો દુખાવો"}
            ]
            pop_cols = st.columns(len(pop_symptoms_data))
            for p_idx, p_item in enumerate(pop_symptoms_data):
                p_key = p_item["key"]
                p_label = p_item.get(lang_code, p_item["en"])
                with pop_cols[p_idx]:
                    if st.button(p_label, key=f"pop_sym_chip_{p_idx}", type="primary", use_container_width=True):
                        if p_key not in st.session_state["selected_symptoms_list"]:
                            st.session_state["selected_symptoms_list"].append(p_key)
                        else:
                            st.session_state["selected_symptoms_list"].remove(p_key)
                        st.rerun()

            st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 8px; font-size: 0.84rem; font-weight: 800; color: var(--mm-text-primary); margin: 14px 0 6px 0;'>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="8" y1="6" x2="21" y2="6"/>
                    <line x1="8" y1="12" x2="21" y2="12"/>
                    <line x1="8" y1="18" x2="21" y2="18"/>
                    <circle cx="4" cy="6" r="1.5" fill="#2563EB"/>
                    <circle cx="4" cy="12" r="1.5" fill="#2563EB"/>
                    <circle cx="4" cy="18" r="1.5" fill="#2563EB"/>
                </svg>
                <span>{T.get('selected_symptoms', 'Selected Symptoms:')}</span>
            </div>
            """, unsafe_allow_html=True)
            if st.session_state["selected_symptoms_list"]:
                sel_chips_html = "".join([f'<span style="background: rgba(37, 99, 235, 0.10); color: #2563EB; border: 1.2px solid rgba(37, 99, 235, 0.3); border-radius: 8px; padding: 5px 10px; font-size: 0.80rem; font-weight: 700; margin-right: 6px; margin-bottom: 6px; display: inline-flex; align-items: center; gap: 4px;">{format_symptom_display(s)}</span>' for s in st.session_state["selected_symptoms_list"]])
                sel_col1, sel_col2 = st.columns([4, 1])
                with sel_col1:
                    st.markdown(f'<div style="display: flex; align-items: center; flex-wrap: wrap;">{sel_chips_html}</div>', unsafe_allow_html=True)
                with sel_col2:
                    if st.button(T.get("clear_all", "Clear All"), key="clear_all_sym_btn", use_container_width=True):
                        st.session_state["selected_symptoms_list"] = []
                        st.session_state["detected_chief_condition"] = None
                        st.session_state["p1_nlp_msg"] = None
                        st.rerun()
            else:
                st.markdown(f"<div style='font-size: 0.82rem; color: var(--mm-text-secondary); margin-top: 4px; margin-bottom: 14px;'>{T.get('no_symptoms_selected', 'No symptoms selected yet. Type to search or select common symptoms above.')}</div>", unsafe_allow_html=True)

            if st.button(f"{T.get('btn_next_symptoms', 'Next: Select Symptoms')} →", key="btn_goto_step2", type="primary", use_container_width=True):
                missing_fields = []
                if not sel_state or sel_state == "-- Select State --":
                    missing_fields.append(T.get("label_state", "State / Location"))
                if not sel_age_key or sel_age_key == "select":
                    missing_fields.append(T.get("label_age_group", "Age Group"))
                if not sel_gen_key or sel_gen_key == "select":
                    missing_fields.append(T.get("label_gender", "Biological Gender"))
                if not st.session_state["selected_symptoms_list"]:
                    missing_fields.append(T.get("card_symptoms_title", "Clinical Symptoms"))
                
                if missing_fields:
                    fields_str = ", ".join(missing_fields)
                    st.error(f"{T.get('err_required_prefix', 'Please provide required details to proceed:')} **{fields_str}**")
                else:
                    st.session_state["user_context"]["symptoms"] = list(st.session_state.get("selected_symptoms_list") or [])
                    st.session_state["assessment_step"] = 2
                    st.rerun()

    # ----------------- STEP 2: SYMPTOMS & SEVERITY -----------------
    elif current_step == 2:
        with st.container(key="assessment_step_card", border=True):
            safe_markdown(f"""
            <div class="mm-step-card-header" style="background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(59,130,246,0.02) 100%); border-bottom: 1.5px solid #BFDBFE; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; border-radius: 16px 16px 0 0; margin: -16px -16px 16px -16px;">
                <div class="mm-step-header-left" style="display: flex; align-items: center; gap: 14px;">
                    <div class="mm-step-header-icon" style="width: 44px; height: 44px; border-radius: 12px; background: #E0F2FE; border: 1.2px solid #BAE6FD; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4.5 3v5a5.5 5.5 0 0 0 11 0V3"></path>
                            <path d="M10 13.5v3.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-1.5"></path>
                            <circle cx="17" cy="15.5" r="2.5"></circle>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title" style="font-size: 1.25rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1.25; margin: 0;">{T.get("card_symptoms_title", "Clinical Symptoms")}</div>
                        <div class="mm-step-header-sub" style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 3px; line-height: 1.35;">{T.get("card_symptoms_sub", "Tell us about your current symptoms so our AI can analyze them more accurately.")}</div>
                    </div>
                </div>
                <div class="mm-step-progress-indicator" style="display: flex; align-items: center; gap: 10px; background: var(--mm-card-bg, #FFFFFF); border: 1px solid #BFDBFE; border-radius: 10px; padding: 6px 14px; box-shadow: 0 1px 3px rgba(37,99,235,0.06);">
                    <div class="mm-step-progress-bar" style="width: 3.5px; height: 28px; background: #2563EB; border-radius: 2px;"></div>
                    <div class="mm-step-progress-text" style="display: flex; flex-direction: column; line-height: 1.15;">
                        <span class="mm-step-progress-step" style="font-size: 0.74rem; font-weight: 800; color: #2563EB; letter-spacing: 0.5px;">STEP 2 OF 4</span>
                        <span class="mm-step-progress-sub" style="font-size: 0.68rem; font-weight: 700; color: var(--mm-text-secondary, #64748B); letter-spacing: 0.5px;">CLINICAL SYMPTOMS</span>
                    </div>
                </div>
            </div>
            """)

            safe_markdown(f"""
            <div style="margin-top: 14px; margin-bottom: 6px;">
                <b style="font-size: 0.88rem; font-weight: 700; color: var(--mm-text-primary);">{T.get('selected_symptoms', 'Selected Symptoms:')}</b>
            </div>
            """)
            step2_syms = [s for s in (st.session_state.get("selected_symptoms_list") or st.session_state.get("user_context", {}).get("symptoms") or []) if s and str(s).strip()]
            if not step2_syms and st.session_state.get("detected_chief_condition"):
                c_d = st.session_state["detected_chief_condition"]
                c_nm = c_d.get("name") or c_d.get("disease_name") or c_d.get("name_hi") or c_d.get("name_gu")
                if c_nm:
                    step2_syms = [c_nm]
            if not step2_syms:
                step2_syms = ["Headache"]
            active_s_html = "".join([f'<span class="mm-symptom-tag" style="background: #EFF6FF; border: 1px solid #BFDBFE; color: #2563EB; font-weight: 700; font-size: 0.76rem; padding: 4px 10px; border-radius: 9999px; display: inline-flex; align-items: center; gap: 6px;">{str(s).upper()} <span style="font-size: 0.70rem; opacity: 0.75;">✕</span></span>' for s in step2_syms])
            safe_markdown(f"<div style='margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 6px;'>{active_s_html}</div>")

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                safe_markdown(f"<div class='mm-field-label-wrap' style='font-size: 0.85rem; font-weight: 700; color: var(--mm-text-primary); margin-bottom: 6px;'><span>{T.get('symptom_severity', 'Symptom Severity Level')}</span></div>")
                cur_sev_key = st.session_state["user_context"].get("severity_key", "moderate")
                if cur_sev_key not in SEVERITY_KEYS:
                    cur_sev_key = "moderate"
                sev_idx = SEVERITY_KEYS.index(cur_sev_key)
                sel_sev_key = st.radio(
                    "Severity",
                    options=SEVERITY_KEYS,
                    index=sev_idx,
                    format_func=lambda k: T.get(SEVERITY_LABEL_MAP.get(k, "severity_moderate"), k),
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["severity_key"] = sel_sev_key
                st.session_state["user_context"]["severity"] = sel_sev_key.capitalize()
            with col_s2:
                safe_markdown(f"<div class='mm-field-label-wrap' style='font-size: 0.85rem; font-weight: 700; color: var(--mm-text-primary); margin-bottom: 6px;'><span>{T.get('symptom_duration', 'Symptom Duration')}</span></div>")
                cur_dur_key = st.session_state["user_context"].get("duration_key", "1_3")
                if cur_dur_key not in DURATION_KEYS:
                    cur_dur_key = "1_3"
                dur_idx = DURATION_KEYS.index(cur_dur_key)
                sel_dur_key = st.selectbox(
                    "Duration",
                    options=DURATION_KEYS,
                    index=dur_idx,
                    format_func=lambda k: T.get(DURATION_LABEL_MAP.get(k, "dur_1_3"), k),
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["duration_key"] = sel_dur_key
                st.session_state["user_context"]["duration"] = T.get(DURATION_LABEL_MAP.get(sel_dur_key, "dur_1_3"), sel_dur_key)

            safe_markdown(f"<div class='mm-field-label-wrap' style='margin-top: 14px; margin-bottom: 6px; font-size: 0.85rem; font-weight: 700; color: var(--mm-text-primary);'><span>{T.get('label_additional_notes', 'Additional Clinical Notes & Triggers (Optional)')}</span></div>")
            additional_desc = st.text_area(
                "Additional Details",
                value=st.session_state.get("user_context", {}).get("details", ""),
                placeholder='e.g. Symptoms worsen at night...',
                label_visibility="collapsed"
            )
            st.session_state["user_context"]["details"] = additional_desc

            nav_c1, nav_c2 = st.columns([1, 1.8])
            with nav_c1:
                if st.button(f"← {T.get('btn_prev', 'Previous Step')}", key="p2_prev_btn", use_container_width=True):
                    st.session_state["assessment_step"] = 1
                    st.rerun()
            with nav_c2:
                if st.button(f"{T.get('btn_next_history', 'Next: Medical History')} →", key="btn_goto_step3", type="primary", use_container_width=True):
                    st.session_state["user_context"]["symptoms"] = list(st.session_state.get("selected_symptoms_list") or [])
                    st.session_state["assessment_step"] = 3
                    st.rerun()

    # ----------------- STEP 3: MEDICAL HISTORY -----------------
    elif current_step == 3:
        with st.container(key="assessment_step_card", border=True):
            safe_markdown(f"""
            <div class="mm-step-card-header" style="background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(59,130,246,0.02) 100%); border-bottom: 1.5px solid #BFDBFE; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; border-radius: 16px 16px 0 0; margin: -16px -16px 16px -16px;">
                <div class="mm-step-header-left" style="display: flex; align-items: center; gap: 14px;">
                    <div class="mm-step-header-icon" style="width: 44px; height: 44px; border-radius: 12px; background: #EFF6FF; border: 1.2px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round"/>
                            <rect x="8" y="2" width="8" height="4" rx="1.5" fill="#2563EB"/>
                            <path d="M12 11v6M9 14h6" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title" style="font-size: 1.25rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1.25; margin: 0;">{T.get("card_history_title", "Medical History")}</div>
                        <div class="mm-step-header-sub" style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 3px; line-height: 1.35;">{T.get("card_history_sub", "Tell us about your existing health background to get more accurate insights.")}</div>
                    </div>
                </div>
                <div class="mm-step-progress-indicator" style="display: flex; align-items: center; gap: 10px; background: var(--mm-card-bg, #FFFFFF); border: 1px solid #BFDBFE; border-radius: 10px; padding: 6px 14px; box-shadow: 0 1px 3px rgba(37,99,235,0.06);">
                    <div class="mm-step-progress-bar" style="width: 3.5px; height: 28px; background: #2563EB; border-radius: 2px;"></div>
                    <div class="mm-step-progress-text" style="display: flex; flex-direction: column; line-height: 1.15;">
                        <span class="mm-step-progress-step" style="font-size: 0.74rem; font-weight: 800; color: #2563EB; letter-spacing: 0.5px;">STEP 3 OF 4</span>
                        <span class="mm-step-progress-sub" style="font-size: 0.68rem; font-weight: 700; color: var(--mm-text-secondary, #64748B); letter-spacing: 0.5px;">MEDICAL HISTORY</span>
                    </div>
                </div>
            </div>
            """)

            safe_markdown(f"""
            <div class="mm-step-info-pill" style="display: flex; align-items: center; gap: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 10px 16px; font-size: 0.78rem; color: #1D4ED8; font-weight: 600; line-height: 1.35; margin-top: 4px; margin-bottom: 14px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <span>This information helps our AI provide more personalized and safe recommendations.</span>
            </div>
            """)

            safe_markdown(f"""
            <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-weight: 700; font-size: 0.85rem; color: var(--mm-text-primary, #0F172A);">
                <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4.5 3v5a5.5 5.5 0 0 0 11 0V3"></path>
                        <path d="M10 13.5v3.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-1.5"></path>
                        <circle cx="17" cy="15.5" r="2.5"></circle>
                    </svg>
                </div>
                <span>{T.get('label_conditions', 'Pre-existing Medical Conditions')}</span>
            </div>
            """)
            cond_label_map = {
                "None": {"en": "None", "hi": "कोई नहीं (None)", "gu": "કોઈ નહીં (None)"},
                "Diabetes (Type 1 or 2)": {"en": "Diabetes (Type 1 or 2)", "hi": "डायबिटीज / मधुमेह (Diabetes)", "gu": "ડાયાબિટીસ (Diabetes)"},
                "Hypertension (High BP)": {"en": "Hypertension (High BP)", "hi": "हाई ब्लड प्रेशर (Hypertension)", "gu": "હાઈ બ્લડ પ્રેશર (Hypertension)"},
                "Asthma / Respiratory": {"en": "Asthma / Respiratory", "hi": "अस्थमा / श्वास रोग (Asthma)", "gu": "અસ્થમા / શ્વાસની તકલીફ (Asthma)"},
                "Heart Disease": {"en": "Heart Disease", "hi": "हृदय रोग (Heart Disease)", "gu": "હૃદય રોગ (Heart Disease)"},
                "Thyroid Disorder": {"en": "Thyroid Disorder", "hi": "थायरॉइड विकार (Thyroid)", "gu": "થાઇરોઇડ (Thyroid)"},
                "Kidney Disease": {"en": "Kidney Disease", "hi": "किडनी की बीमारी (Kidney Disease)", "gu": "કિડનીની બીમારી (Kidney Disease)"},
                "Acidity / GERD": {"en": "Acidity / GERD", "hi": "एसिडिटी / गैस (Acidity / GERD)", "gu": "એસિડિટી / ગેસ (Acidity / GERD)"}
            }
            if "selected_conditions_widget" not in st.session_state:
                st.session_state["selected_conditions_widget"] = st.session_state.get("user_context", {}).get("conditions", ["None"])
            if "prev_selected_conditions" not in st.session_state:
                st.session_state["prev_selected_conditions"] = list(st.session_state["selected_conditions_widget"])

            cond_choices = st.multiselect(
                "Existing Conditions",
                options=["None", "Diabetes (Type 1 or 2)", "Hypertension (High BP)", "Asthma / Respiratory", "Heart Disease", "Thyroid Disorder", "Kidney Disease", "Acidity / GERD"],
                key="selected_conditions_widget",
                on_change=sync_medical_conditions,
                format_func=lambda k: cond_label_map.get(k, {}).get(lang_code, k),
                label_visibility="collapsed"
            )
            st.session_state["user_context"]["conditions"] = cond_choices

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-weight: 700; font-size: 0.85rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path>
                            <path d="m8.5 8.5 7 7"></path>
                        </svg>
                    </div>
                    <span>{T.get('label_medications', 'Current Ongoing Medications')}</span>
                </div>
                """)
                curr_meds = st.text_input(
                    "Current Medications",
                    value=st.session_state.get("user_context", {}).get("medications", ""),
                    placeholder="e.g. Metformin 500mg, Telmisartan 40mg",
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["medications"] = curr_meds
            with col_m2:
                safe_markdown(f"""
                <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; font-weight: 700; font-size: 0.85rem; color: var(--mm-text-primary, #0F172A);">
                    <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="4"></circle>
                            <path d="M12 2v2"></path>
                            <path d="M12 20v2"></path>
                            <path d="m4.93 4.93 1.41 1.41"></path>
                            <path d="m17.66 17.66 1.41 1.41"></path>
                            <path d="M2 12h2"></path>
                            <path d="M20 12h2"></path>
                            <path d="m6.34 17.66-1.41 1.41"></path>
                            <path d="m19.07 4.93-1.41 1.41"></path>
                        </svg>
                    </div>
                    <span>{T.get('label_allergies', 'Known Food or Drug Allergies')}</span>
                </div>
                """)
                allergies_val = st.text_input(
                    "Allergies",
                    value=st.session_state.get("user_context", {}).get("allergies", ""),
                    placeholder="e.g. Penicillin, Sulfa, Peanuts",
                    label_visibility="collapsed"
                )
                st.session_state["user_context"]["allergies"] = allergies_val

            safe_markdown(f"""
            <div class="mm-field-label-wrap" style="display: flex; align-items: center; gap: 8px; margin-top: 14px; margin-bottom: 6px; font-weight: 700; font-size: 0.85rem; color: var(--mm-text-primary, #0F172A);">
                <div class="mm-field-icon-badge" style="width: 28px; height: 28px; border-radius: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                </div>
                <span>{T.get('label_family_history', 'Relevant Family Medical History (Optional)')}</span>
            </div>
            """)
            surgeries_val = st.text_area(
                "Surgeries",
                value=st.session_state.get("user_context", {}).get("surgeries", ""),
                placeholder="e.g. Prior surgeries, family history of cardiac illness...",
                label_visibility="collapsed"
            )
            st.session_state["user_context"]["surgeries"] = surgeries_val

            nav_c1, nav_c2 = st.columns([1, 1.8])
            with nav_c1:
                if st.button(f"← {T.get('btn_prev', 'Previous Step')}", key="p3_prev_btn", use_container_width=True):
                    st.session_state["assessment_step"] = 2
                    st.rerun()
            with nav_c2:
                if st.button(f"{T.get('btn_next_review', 'Next: Review & Run AI Analysis')} →", key="btn_goto_step4", type="primary", use_container_width=True):
                    st.session_state["user_context"]["symptoms"] = list(st.session_state.get("selected_symptoms_list") or [])
                    st.session_state["assessment_step"] = 4
                    st.rerun()

    # ----------------- STEP 4: REVIEW & ANALYZE -----------------
    elif current_step == 4:
        with st.container(key="assessment_step_card", border=True):
            safe_markdown(f"""
            <div class="mm-step-card-header" style="background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(59,130,246,0.02) 100%); border-bottom: 1.5px solid #BFDBFE; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; border-radius: 16px 16px 0 0; margin: -16px -16px 16px -16px;">
                <div class="mm-step-header-left" style="display: flex; align-items: center; gap: 14px;">
                    <div class="mm-step-header-icon" style="width: 44px; height: 44px; border-radius: 12px; background: #EFF6FF; border: 1.2px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #2563EB;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title" style="font-size: 1.25rem; font-weight: 800; color: var(--mm-text-primary, #0F172A); line-height: 1.25; margin: 0;">{T.get("card_review_title", "Review Clinical Details & Run Analysis")}</div>
                        <div class="mm-step-header-sub" style="font-size: 0.82rem; color: var(--mm-text-secondary, #64748B); margin-top: 3px; line-height: 1.35;">{T.get("card_review_sub", "Verify your submitted details before running the knowledge graph triage engine.")}</div>
                    </div>
                </div>
                <div class="mm-step-progress-indicator" style="display: flex; align-items: center; gap: 10px; background: var(--mm-card-bg, #FFFFFF); border: 1px solid #BFDBFE; border-radius: 10px; padding: 6px 14px; box-shadow: 0 1px 3px rgba(37,99,235,0.06);">
                    <div class="mm-step-progress-bar" style="width: 3.5px; height: 28px; background: #2563EB; border-radius: 2px;"></div>
                    <div class="mm-step-progress-text" style="display: flex; flex-direction: column; line-height: 1.15;">
                        <span class="mm-step-progress-step" style="font-size: 0.74rem; font-weight: 800; color: #2563EB; letter-spacing: 0.5px;">STEP 4 OF 4</span>
                        <span class="mm-step-progress-sub" style="font-size: 0.68rem; font-weight: 700; color: var(--mm-text-secondary, #64748B); letter-spacing: 0.5px;">ANALYSIS &amp; TRIAGE</span>
                    </div>
                </div>
            </div>
            """)

            safe_markdown(f"""
            <div class="mm-step-info-pill" style="display: flex; align-items: center; gap: 8px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 10px 16px; font-size: 0.78rem; color: #1D4ED8; font-weight: 600; line-height: 1.35; margin-top: 4px; margin-bottom: 14px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                <span>Verify all clinical parameters before generating triage diagnosis.</span>
            </div>
            """)

            u_ctx = st.session_state.get("user_context", {})

            c_sum1, c_sum2, c_sum3 = st.columns(3)
            with c_sum1:
                h_disp = u_ctx.get('height') or 'None'
                w_disp = u_ctx.get('weight') or 'None'
                safe_markdown(f"""
                <div class="mm-review-card-blue">
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 3px 10px rgba(37, 99, 235, 0.28);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                        </div>
                        <div>
                            <b class="mm-text-blue" style="font-size: 1.15rem; font-weight: 800; color: #1D4ED8; display: block; line-height: 1.2;">
                                {T.get("card_about_you", "Patient Demographics")}
                            </b>
                            <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">
                                {T.get("card_about_you_sub", "Basic information about the patient")}
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="mm-review-row-blue">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_age_group", "Age Group")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{get_localized_user_val('age', u_ctx.get('age', '21-30'), T, lang_code)}</span>
                        </div>
                        <div class="mm-review-row-blue">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="10" cy="14" r="5"/><line x1="19" y1="5" x2="13.5" y2="10.5"/><polyline points="15 5 19 5 19 9"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_gender", "Biological Gender")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{get_localized_user_val('gender', u_ctx.get('gender', 'Male'), T, lang_code)}</span>
                        </div>
                        <div class="mm-review-row-blue">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_location", "Current City / Location")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('state') or u_ctx.get('location') or 'None'}</span>
                        </div>
                        <div class="mm-review-row-blue">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M21 3v18"/><path d="M3 3v18"/><path d="M3 12h18"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_height", "Height (cm)")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{h_disp}</span>
                        </div>
                        <div class="mm-review-row-blue">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><rect x="4" y="6" width="16" height="14" rx="2"/><circle cx="12" cy="10" r="2"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_weight", "Weight (kg)")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{w_disp}</span>
                        </div>
                        <div class="mm-review-row-blue" style="margin-bottom: 0;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_blood_group", "Blood Group")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{get_localized_user_val('other', u_ctx.get('blood_group'), T, lang_code)}</span>
                        </div>
                    </div>
                </div>
                """)

            with c_sum2:
                s_list_raw = [str(s).strip() for s in (st.session_state.get("selected_symptoms_list") or u_ctx.get("symptoms") or []) if s and str(s).strip()]
                if not s_list_raw and st.session_state.get("detected_chief_condition"):
                    c_data = st.session_state["detected_chief_condition"]
                    c_name = c_data.get("disease_name") or c_data.get("name") or c_data.get("name_hi") or c_data.get("name_gu")
                    if c_name:
                        s_list_raw = [str(c_name).strip()]
                if not s_list_raw:
                    s_list_raw = ["Fever", "Headache"]
                
                s_list_str = ", ".join(s_list_raw)
                sym_lbl = T.get("selected_symptoms", "Selected Symptoms").rstrip(":")
                sev_lbl = T.get("symptom_severity", "Symptom Severity Level").rstrip(":")
                dur_lbl = T.get("symptom_duration", "Symptom Duration").rstrip(":")
                safe_markdown(f"""
                <div class="mm-review-card-purple">
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: #7C3AED; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 3px 10px rgba(124, 58, 237, 0.28);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                        </div>
                        <div>
                            <b class="mm-text-purple" style="font-size: 1.15rem; font-weight: 800; color: #7C3AED; display: block; line-height: 1.2;">
                                {T.get("card_symptoms_title", "Clinical Symptoms")}
                            </b>
                            <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">
                                {T.get("card_symptoms_sub", "Current symptoms and severity")}
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="mm-review-row-purple">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{sym_lbl}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{s_list_str}</span>
                        </div>
                        <div class="mm-review-row-purple">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{sev_lbl}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{get_localized_user_val('severity', u_ctx.get('severity', 'Moderate'), T, lang_code)}</span>
                        </div>
                        <div class="mm-review-row-purple" style="margin-bottom: 0;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{dur_lbl}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{get_localized_user_val('duration', u_ctx.get('duration', '1 - 3 Days'), T, lang_code)}</span>
                        </div>
                    </div>
                </div>
                """)

            with c_sum3:
                cond_str = ", ".join(u_ctx.get("conditions", ["None"]))
                fam_val = u_ctx.get("surgeries", "") or "None"
                safe_markdown(f"""
                <div class="mm-review-card-green">
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: #059669; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 3px 10px rgba(5, 150, 105, 0.28);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                        </div>
                        <div>
                            <b class="mm-text-green" style="font-size: 1.15rem; font-weight: 800; color: #059669; display: block; line-height: 1.2;">
                                {T.get("step3_title", "Medical History")}
                            </b>
                            <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">
                                {T.get("card_history_sub", "Past medical conditions and relevant history")}
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="mm-review-row-green">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_conditions", "Pre-existing Medical Conditions")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{cond_str}</span>
                        </div>
                        <div class="mm-review-row-green">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><line x1="4.5" y1="19.5" x2="19.5" y2="4.5"/><path d="M10.5 4.5a4.24 4.24 0 0 0-6 6l9 9a4.24 4.24 0 0 0 6-6l-9-9z"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_medications", "Current Ongoing Medications")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('medications') or 'None'}</span>
                        </div>
                        <div class="mm-review-row-green">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_allergies", "Known Food or Drug Allergies")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('allergies') or 'None'}</span>
                        </div>
                        <div class="mm-review-row-green" style="margin-bottom: 0;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_family_history", "Relevant Family Medical History (Optional)")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{fam_val}</span>
                        </div>
                    </div>
                </div>
                """)

            nav_c1, nav_c2 = st.columns([1, 2])
            with nav_c1:
                if st.button(f"← {T.get('btn_prev', 'Previous Step')}", key="p4_prev_btn", use_container_width=True):
                    st.session_state["assessment_step"] = 3
                    st.rerun()
            with nav_c2:
                analyze_p1_btn = st.button(f"{T.get('btn_analyze', 'Run AI Health Analysis')} →", key="btn_run_analysis_final", type="primary", use_container_width=True)

        if analyze_p1_btn:
            user_st = st.session_state["user_context"].get("state", "").strip()
            if not user_st or user_st in ["-- Select State --", "select"]:
                st.error(f"{T.get('err_state_required', 'Please select your State to proceed with the analysis.')}")
                st.stop()
            if not st.session_state["user_context"].get("gender") or st.session_state["user_context"].get("gender_key") == "select":
                st.error("Please select your Gender before proceeding (कृपया अपना लिंग चुनें).")
                st.stop()
            if not st.session_state["user_context"].get("age") or st.session_state["user_context"].get("age_key") == "select":
                st.error("Please select your Age Group before proceeding (कृपया अपना आयु वर्ग चुनें).")
                st.stop()
            if not st.session_state.get("selected_symptoms_list") and not st.session_state.get("detected_chief_condition"):
                st.error("Please select at least one clinical symptom to evaluate (कृपया कम से कम एक लक्षण चुनें).")
                st.stop()

            with st.status("DocMindX Clinical AI Engine Running...", expanded=True) as status:
                st.write("Processing reported symptoms and ontology...")
                st.write("Cross-referencing ICD-11 knowledge graph and history...")
                st.markdown('<div style="font-size: 0.88rem; display: flex; align-items: center; gap: 6px; padding: 2px 0;"><img src="https://cdn-icons-png.flaticon.com/512/190/190256.png" style="width: 14px; height: 14px; object-fit: contain;"/> Generating personalized health summary, dietary guidance & triage alerts...</div>', unsafe_allow_html=True)
                
                selected_ids = []
                symptom_ontology_map = {
                    "fever": ["S000001"],
                    "high fever": ["S000002"],
                    "high fever (above 103°f/39.4°c)": ["S000002"],
                    "headache": ["S000061"],
                    "cough": ["S000023"],
                    "dry cough": ["S000023"],
                    "sore throat": ["S000030"],
                    "fatigue": ["S000005"],
                    "severe fatigue": ["S000006"],
                    "severe fatigue and weakness": ["S000006"],
                    "body pain": ["S000011"],
                    "body ache": ["S000011"],
                    "nausea": ["S000086"],
                    "vomiting": ["S000087"],
                    "cold": ["S000035"],
                    "chills": ["S000003"],
                    "diarrhea": ["S000089"],
                    "stomach pain": ["S000091"],
                    "chest pain": ["S000046"],
                    "shortness of breath": ["S000026"],
                    "easy bruising": ["S000127"],
                    "easy bruising or bleeding": ["S000127"],
                    "easy bruising and bleeding (petechiae / purpura)": ["S000127"],
                    "petechiae": ["S000127"],
                    "frequent infections": ["S000001"],
                    "bone and joint pain": ["S000011"],
                    "night sweats": ["S000003"],
                    "drenching night sweats": ["S000003"],
                    "unintended weight loss": ["S000017"],
                    "unintentional weight loss and night sweats": ["S000017"],
                }
                
                for s_name in st.session_state.get("selected_symptoms_list", []):
                    s_lower = s_name.strip().lower()
                    if s_lower in symptom_ontology_map:
                        selected_ids.extend(symptom_ontology_map[s_lower])
                
                if not selected_ids:
                    selected_ids = ["S000001", "S000061"]

                # Pass all selected symptom names & detected chief condition
                s_list_names = st.session_state.get("selected_symptoms_list", [])
                chief_d = st.session_state.get("detected_chief_condition", {})
                chief_name = chief_d.get("name") if isinstance(chief_d, dict) else None

                # Run Comprehensive Knowledge-Graph Triage Engine
                if hasattr(triage_engine, "evaluate_triage"):
                    triage_res = triage_engine.evaluate_triage(
                        reported_symptom_ids=selected_ids,
                        patient_history={
                            "age_group": u_ctx.get("age", "21-30"),
                            "gender": u_ctx.get("gender", "Male"),
                            "duration": u_ctx.get("duration", "1-3 Days"),
                            "severity": u_ctx.get("severity", "Moderate"),
                            "conditions": u_ctx.get("conditions", []),
                            "location": u_ctx.get("location", "Ahmedabad, Gujarat"),
                            "symptom_names": s_list_names,
                            "chief_condition": chief_name
                        },
                        symptom_names=s_list_names,
                        chief_condition=chief_name
                    )
                else:
                    triage_res = triage_engine.evaluate_symptoms(
                        selected_symptom_ids=selected_ids,
                        age_group=u_ctx.get("age", "21-30"),
                        gender=u_ctx.get("gender", "Male"),
                        duration=u_ctx.get("duration", "1-3 Days"),
                        existing_conditions=u_ctx.get("conditions", {}),
                        symptom_names=s_list_names,
                        chief_condition=chief_name
                    )
                
                st.session_state["p1_triage_results"] = triage_res
                st.session_state["care_recommendations"] = None
                st.session_state["assessment_completed"] = True
                status.update(label="Clinical Assessment & Triage Complete", state="complete", expanded=False)
                st.rerun()

    # Results Section (Visible after Assessment)
    if st.session_state.get("assessment_completed") and st.session_state.get("p1_triage_results"):
        t_res = st.session_state["p1_triage_results"]
        u_ctx = st.session_state.get("user_context", {})
        
        ranked_conds = t_res.get("ranked_conditions", [])
        top_disease_name = ranked_conds[0].get("name", "Acute Infection") if ranked_conds else "Acute Illness"

        # Fetch / compute dynamic care recommendations (Cached for session to keep medicines & yoga consistent across language changes)
        current_sym_key = str(sorted(st.session_state.get("selected_symptoms_list", [])))
        care_res = st.session_state.get("care_recommendations")
        if (
            not care_res
            or care_res.get("top_condition") != top_disease_name
            or care_res.get("symptoms_key") != current_sym_key
        ):
            care_res = get_dynamic_clinical_recommendations(
                symptoms=st.session_state.get("selected_symptoms_list", []),
                user_context=u_ctx,
                top_condition=top_disease_name,
                lang_code=lang_code
            )
            if care_res and isinstance(care_res, dict):
                care_res["top_condition"] = top_disease_name
                care_res["symptoms_key"] = current_sym_key
            st.session_state["care_recommendations"] = care_res
        elif care_res.get("lang_code") != lang_code:
            # Language changed on existing assessment: localize text while locking medicines & yoga
            care_res = localize_care_recommendations(care_res, lang_code)
            if care_res and isinstance(care_res, dict):
                care_res["top_condition"] = top_disease_name
                care_res["symptoms_key"] = current_sym_key
            st.session_state["care_recommendations"] = care_res

        # Auto-persist complete clinical assessment record
        curr_auth_user = auth_ui.get_current_user()
        p1_ctx = st.session_state.get("p1_patient_context") or {}
        p_mode = p1_ctx.get("mode", "GENERAL") if curr_auth_user else "GENERAL"
        p_mem_id = p1_ctx.get("member_id") if p_mode == "FAMILY_MEMBER" else None
        p_name = p1_ctx.get("name") or (curr_auth_user.get("full_name") if curr_auth_user else "General Patient")

        triage_save_key = f"triage_saved_{t_res.get('session_id', id(t_res))}_{p_mode}_{p_mem_id}"
        if triage_save_key not in st.session_state:
            full_scan_record = {
                "scan_type": "Health Assessment",
                "scan_mode": p_mode,
                "result_reference": top_disease_name,
                "summary": f"{top_disease_name} ({t_res.get('urgency_level', 'NORMAL')} Urgency)",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "patient_name": p_name,
                "family_member_name": p_name if p_mode == "FAMILY_MEMBER" else None,
                "patient_context": p1_ctx,
                "user_inputs": {
                    "age": u_ctx.get("age", "Adult"),
                    "gender": u_ctx.get("gender", "Unspecified"),
                    "duration": u_ctx.get("duration", "1-3 Days"),
                    "severity": u_ctx.get("severity", "Moderate"),
                    "location": u_ctx.get("location") or u_ctx.get("state", "India"),
                    "blood_group": u_ctx.get("blood_group", "None"),
                    "height": u_ctx.get("height", "None"),
                    "weight": u_ctx.get("weight", "None"),
                    "existing_conditions": u_ctx.get("conditions", []),
                    "current_medicines": u_ctx.get("medications", []),
                    "allergies": u_ctx.get("allergies", "None"),
                    "symptoms": st.session_state.get("selected_symptoms_list", [])
                },
                "triage_result": t_res,
                "care_recommendations": care_res,
                "ranked_conditions": ranked_conds,
                "urgency_level": t_res.get("urgency_level", "NORMAL"),
                "is_emergency": bool(t_res.get("is_emergency") or t_res.get("red_flag_alert")),
                "red_flags": t_res.get("red_flags", []),
                "medicines": care_res.get("medicine_gallery", []),
                "yoga_recommendations": care_res.get("yoga_recommendations", []),
                "diet_guidance": care_res.get("diet_guidance", {}),
                "lifestyle_guidance": care_res.get("lifestyle_guidance", []),
                "precautions": care_res.get("precautions", [])
            }
            if curr_auth_user:
                try:
                    auth_db.save_medical_scan(
                        user_id=curr_auth_user["id"],
                        family_member_id=p_mem_id,
                        scan_type="Health Assessment",
                        scan_mode=p_mode,
                        result_reference=top_disease_name,
                        summary=f"{top_disease_name} — {t_res.get('urgency_level', 'NORMAL')} Urgency",
                        details=full_scan_record
                    )
                except Exception as save_err:
                    print(f"Notice auto-saving assessment: {save_err}")
            st.session_state["current_session_scan"] = full_scan_record
            if "session_scans" not in st.session_state:
                st.session_state["session_scans"] = []
            st.session_state["session_scans"].insert(0, full_scan_record)
            st.session_state[triage_save_key] = True


        # Dialog definition for Medicine Compounds and Packaging Image
        if hasattr(st, "dialog"):
            def dialog_dec(title):
                return st.dialog(title, width="large")
        elif hasattr(st, "experimental_dialog"):
            def dialog_dec(title):
                return st.experimental_dialog(title, width="large")
        else:
            def dialog_dec(title):
                def wrapper(fn):
                    return fn
                return wrapper

        @dialog_dec("Medication Clinical Profile & Active Compounds")
        def show_medicine_modal(med):
            med_detail = get_medicine_details(med['name'])
            modal_key_id = re.sub(r'[^a-zA-Z0-9]', '_', med['name'])[:15]

            img_url = med.get("image", "")
            med_type_str = (med.get('type') or 'Prescription').upper()
            generic_val = med_detail.get('generic_name') or med['name']
            course_val = med.get('course_duration') or '3 - 5 Days'
            dosage_val = med.get('dosage') or 'As prescribed by physician'
            timing_val = med.get('food_timing') or 'After Food'
            brand_list = med_detail.get('brand_names', [])
            brands_str = ', '.join(brand_list) if brand_list else (med.get('name') or 'Available across licensed pharmacies')
            ind_text = med.get('indication') or ', '.join(med_detail.get('primary_indications', [])) or "Forms a targeted therapeutic effect to stabilize symptoms and promote recovery."
            warn_text = med.get('warnings') or ', '.join(med_detail.get('contraindications', [])) or 'Consult a certified physician before initiating or modifying dosage.'

            compounds = med_detail.get("active_compounds", [])
            compounds_items = []
            if compounds:
                for cmpd in compounds:
                    c_name = cmpd.get('compound_name', '')
                    c_formula = cmpd.get('molecular_formula', '')
                    formula_str = f"({c_formula})" if c_formula else ""
                    c_strength = cmpd.get('strength', 'Standard Clinical Strength')
                    c_role = cmpd.get('role', 'Active Therapeutic Agent')
                    compounds_items.append(
                        f'<div class="mmp-compound-item">'
                        f'<span class="mmp-bullet">&bull;</span> '
                        f'<span class="mmp-cmpd-name">{c_name}</span> '
                        f'<span class="mmp-cmpd-formula">{formula_str}</span>: '
                        f'<span class="mmp-strength-pill">{c_strength}</span> '
                        f'<span class="mmp-cmpd-role">&mdash; {c_role}</span>'
                        f'</div>'
                    )
            else:
                compounds_items.append(
                    f'<div class="mmp-compound-item">'
                    f'<span class="mmp-bullet">&bull;</span> '
                    f'<span class="mmp-cmpd-name">{med["name"]}</span>: '
                    f'<span class="mmp-strength-pill">Standard Clinical Strength</span> '
                    f'<span class="mmp-cmpd-role">&mdash; Active Therapeutic Formulation</span>'
                    f'</div>'
                )
            compounds_html = "".join(compounds_items)

            if img_url:
                img_block = (
                    f'<a href="{img_url}" target="_blank" style="text-decoration:none;display:block;width:100%;text-align:center;">'
                    f'<img src="{img_url}" class="mmp-img" alt="{med["name"]}" />'
                    f'</a>'
                    f'<div class="mmp-img-link">'
                    f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">'
                    f'<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>'
                    f'</svg>'
                    f'<a href="{img_url}" target="_blank" style="color:#2563EB;text-decoration:none;font-weight:600;">Click image to open in new tab &nearr;</a>'
                    f'</div>'
                    f'<div class="mmp-img-disclaimer">* Representative / Similar Image (&#2360;&#2366;&#2306;&#2325;&#2375;&#2340;&#2367;&#2325; / &#2360;&#2350;&#2352;&#2370;&#2346; &#2330;&#2367;&#2340;&#2381;&#2352;)</div>'
                )
            else:
                img_block = (
                    f'<div style="font-size:0.95rem;font-weight:700;color:var(--mm-text-primary,#0F172A);text-align:center;padding:70px 10px;">{med["name"]}</div>'
                    f'<div class="mmp-img-disclaimer">* Representative / Similar Image (&#2360;&#2366;&#2306;&#2325;&#2375;&#2340;&#2367;&#2325; / &#2360;&#2350;&#2352;&#2370;&#2346; &#2330;&#2367;&#2340;&#2381;&#2352;)</div>'
                )

            raw_html_lines = [
                '<style>',
                'div[data-testid="stDialog"],',
                'div[data-modal-container="true"],',
                'div[data-baseweb="modal"],',
                'div[data-baseweb="backdrop"] {',
                '    background: rgba(15, 23, 42, 0.18) !important;',
                '    backdrop-filter: blur(4px) !important;',
                '    -webkit-backdrop-filter: blur(4px) !important;',
                '}',
                'div[data-testid="stDialog"] > div {',
                '    background: transparent !important;',
                '    border: none !important;',
                '    box-shadow: none !important;',
                '    padding: 0 !important;',
                '    margin: 0 !important;',
                '}',
                'div[data-testid="stDialog"] div[role="dialog"],',
                'div[role="dialog"],',
                'section[role="dialog"] {',
                '    max-width: 1060px !important;',
                '    width: min(1060px, 94vw) !important;',
                '    min-width: min(840px, 90vw) !important;',
                '    border-radius: 20px !important;',
                '    padding: 22px 24px !important;',
                '    box-sizing: border-box !important;',
                '    background: var(--mm-bg-surface, #FFFFFF) !important;',
                '    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22), 0 0 0 1px rgba(0,0,0,0.06) !important;',
                '}',
                '.mmp-layout {',
                '    display: flex;',
                '    flex-direction: row;',
                '    gap: 26px;',
                '    width: 100%;',
                '    align-items: flex-start;',
                '    box-sizing: border-box;',
                '    margin-top: 4px;',
                '}',
                '.mmp-col-img {',
                '    flex: 0 0 380px;',
                '    max-width: 380px;',
                '    min-width: 0;',
                '    display: flex;',
                '    flex-direction: column;',
                '}',
                '.mmp-img-box {',
                '    background: var(--mm-bg-surface, #FFFFFF);',
                '    border: 1.5px solid var(--mm-border-color, #E2E8F0);',
                '    border-radius: 16px;',
                '    padding: 16px;',
                '    display: flex;',
                '    flex-direction: column;',
                '    align-items: center;',
                '    justify-content: flex-start;',
                '    box-sizing: border-box;',
                '    min-height: 330px;',
                '    box-shadow: 0 2px 10px rgba(0,0,0,0.03);',
                '}',
                '.mmp-img {',
                '    width: 100%;',
                '    max-height: 250px;',
                '    object-fit: contain;',
                '    border-radius: 10px;',
                '    display: block;',
                '}',
                '.mmp-img-link {',
                '    display: flex;',
                '    align-items: center;',
                '    gap: 6px;',
                '    margin-top: 14px;',
                '    font-size: 0.82rem;',
                '    font-weight: 600;',
                '    color: #2563EB;',
                '    justify-content: center;',
                '}',
                '.mmp-img-disclaimer {',
                '    margin-top: 6px;',
                '    font-size: 0.72rem;',
                '    color: var(--mm-text-secondary, #64748B);',
                '    text-align: center;',
                '    font-weight: 500;',
                '}',
                '.mmp-badges-row {',
                '    margin-top: 14px;',
                '    display: flex;',
                '    flex-direction: row;',
                '    gap: 10px;',
                '    width: 100%;',
                '}',
                '.mmp-badge {',
                '    flex: 1;',
                '    display: inline-flex;',
                '    align-items: center;',
                '    justify-content: center;',
                '    gap: 7px;',
                '    padding: 9px 10px;',
                '    font-size: 0.74rem;',
                '    font-weight: 800;',
                '    letter-spacing: 0.03em;',
                '    text-transform: uppercase;',
                '    border-radius: 9999px;',
                '    white-space: nowrap;',
                '    box-sizing: border-box;',
                '}',
                '.mmp-badge-rx {',
                '    background: #E0F2FE;',
                '    border: 1.2px solid #BAE6FD;',
                '    color: #0284C7;',
                '}',
                '.mmp-badge-ok {',
                '    background: #DCFCE7;',
                '    border: 1.2px solid #BBF7D0;',
                '    color: #16A34A;',
                '}',
                '.mmp-col-info {',
                '    flex: 1 1 0;',
                '    min-width: 0;',
                '    display: flex;',
                '    flex-direction: column;',
                '}',
                '.mmp-title {',
                '    font-size: 1.45rem;',
                '    font-weight: 800;',
                '    color: var(--mm-text-primary, #0F172A);',
                '    margin: 0 0 14px 0;',
                '    line-height: 1.25;',
                '    letter-spacing: -0.01em;',
                '}',
                '.mmp-grid-card {',
                '    background: var(--mm-bg-surface, #FFFFFF);',
                '    border: 1.2px solid var(--mm-border-color, #E2E8F0);',
                '    border-radius: 14px;',
                '    padding: 16px 18px;',
                '    margin-bottom: 14px;',
                '    box-shadow: 0 2px 10px rgba(0,0,0,0.03);',
                '}',
                '.mmp-grid-2x2 {',
                '    display: grid;',
                '    grid-template-columns: 1fr 1fr;',
                '    gap: 14px 20px;',
                '}',
                '.mmp-cell {',
                '    display: flex;',
                '    align-items: flex-start;',
                '    gap: 10px;',
                '}',
                '.mmp-icon-circle {',
                '    width: 40px;',
                '    height: 40px;',
                '    min-width: 40px;',
                '    border-radius: 50%;',
                '    display: flex;',
                '    align-items: center;',
                '    justify-content: center;',
                '    flex-shrink: 0;',
                '}',
                '.mmp-ic-blue   { background:#EFF6FF; border:1px solid #DBEAFE; }',
                '.mmp-ic-teal   { background:#ECFEFF; border:1px solid #CFFAFE; }',
                '.mmp-ic-red    { background:#FFF1F2; border:1px solid #FFE4E6; }',
                '.mmp-ic-orange { background:#FEF2F2; border:1px solid #FEE2E2; }',
                '.mmp-ic-tag    { background:#EFF6FF; border:1px solid #DBEAFE; border-radius:10px; }',
                '.mmp-cell-label {',
                '    font-size: 0.74rem;',
                '    font-weight: 600;',
                '    color: var(--mm-text-secondary, #64748B);',
                '    line-height: 1.2;',
                '}',
                '.mmp-val-generic { font-size:0.87rem; font-weight:700; color:#2563EB; margin-top:2px; line-height:1.3; }',
                '.mmp-val-course  { font-size:0.89rem; font-weight:800; color:#16A34A; margin-top:2px; line-height:1.3; }',
                '.mmp-val-dosage  { font-size:0.87rem; font-weight:700; color:var(--mm-text-primary,#0F172A); margin-top:2px; line-height:1.3; }',
                '.mmp-val-timing  { font-size:0.87rem; font-weight:800; color:#EA580C; margin-top:2px; line-height:1.3; }',
                '.mmp-brands-row {',
                '    margin-top: 12px;',
                '    padding-top: 12px;',
                '    border-top: 1px solid var(--mm-border-color, #F1F5F9);',
                '    display: flex;',
                '    align-items: center;',
                '    gap: 10px;',
                '}',
                '.mmp-brands-text {',
                '    font-size: 0.83rem;',
                '    color: var(--mm-text-primary, #1E293B);',
                '    line-height: 1.45;',
                '}',
                '.mmp-section-hdr {',
                '    display: flex;',
                '    align-items: center;',
                '    gap: 8px;',
                '    margin-top: 14px;',
                '    margin-bottom: 6px;',
                '}',
                '.mmp-section-hdr-title {',
                '    font-size: 0.92rem;',
                '    font-weight: 800;',
                '    color: var(--mm-text-primary, #0F172A);',
                '}',
                '.mmp-compound-item {',
                '    font-size: 0.82rem;',
                '    color: var(--mm-text-secondary, #64748B);',
                '    margin: 4px 0 4px 12px;',
                '    line-height: 1.5;',
                '}',
                '.mmp-bullet { margin-right: 4px; font-weight: bold; }',
                '.mmp-cmpd-name { color: var(--mm-text-primary, #1E293B); font-weight: 700; }',
                '.mmp-cmpd-formula { color: var(--mm-text-secondary, #64748B); }',
                '.mmp-strength-pill {',
                '    background: rgba(37,99,235,0.08);',
                '    color: #2563EB;',
                '    border: 1px solid rgba(37,99,235,0.25);',
                '    border-radius: 6px;',
                '    padding: 2px 7px;',
                '    font-family: monospace;',
                '    font-size: 0.75rem;',
                '    font-weight: 700;',
                '    margin: 0 4px;',
                '}',
                '.mmp-cmpd-role { font-style: italic; color: var(--mm-text-secondary, #64748B); }',
                '.mmp-purpose-text {',
                '    font-size: 0.84rem;',
                '    color: var(--mm-text-secondary, #475569);',
                '    margin: 3px 0 0 26px;',
                '    line-height: 1.5;',
                '}',
                '.mmp-alert-box {',
                '    background: rgba(254,243,199,0.35);',
                '    border: 1px solid rgba(249,115,22,0.35);',
                '    border-left: 4.5px solid #F97316;',
                '    border-radius: 10px;',
                '    padding: 11px 15px;',
                '    margin-top: 14px;',
                '    display: flex;',
                '    align-items: flex-start;',
                '    gap: 10px;',
                '}',
                '.mmp-alert-content {',
                '    font-size: 0.83rem;',
                '    line-height: 1.45;',
                '    color: var(--mm-text-primary, #1E293B);',
                '}',
                '.mmp-alert-title { color:#EA580C; font-weight:800; margin-right:4px; }',
                '.mmp-alert-text { color: var(--mm-text-secondary, #475569); }',
                '[data-theme="dark"] .mmp-img-box {',
                '    background: rgba(255,255,255,0.03) !important;',
                '    border-color: rgba(255,255,255,0.1) !important;',
                '}',
                '[data-theme="dark"] .mmp-badge-rx {',
                '    background: rgba(14,165,233,0.15) !important;',
                '    border-color: rgba(14,165,233,0.35) !important;',
                '    color: #38BDF8 !important;',
                '}',
                '[data-theme="dark"] .mmp-badge-ok {',
                '    background: rgba(34,197,94,0.15) !important;',
                '    border-color: rgba(34,197,94,0.35) !important;',
                '    color: #4ADE80 !important;',
                '}',
                '[data-theme="dark"] .mmp-grid-card {',
                '    background: rgba(255,255,255,0.025) !important;',
                '    border-color: rgba(255,255,255,0.08) !important;',
                '}',
                '[data-theme="dark"] .mmp-ic-blue   { background:rgba(37,99,235,0.18)!important; border-color:rgba(37,99,235,0.35)!important; }',
                '[data-theme="dark"] .mmp-ic-teal   { background:rgba(6,182,212,0.18)!important; border-color:rgba(6,182,212,0.35)!important; }',
                '[data-theme="dark"] .mmp-ic-red    { background:rgba(225,29,72,0.18)!important; border-color:rgba(225,29,72,0.35)!important; }',
                '[data-theme="dark"] .mmp-ic-orange { background:rgba(234,88,12,0.18)!important; border-color:rgba(234,88,12,0.35)!important; }',
                '[data-theme="dark"] .mmp-ic-tag    { background:rgba(37,99,235,0.18)!important; border-color:rgba(37,99,235,0.35)!important; }',
                '[data-theme="dark"] .mmp-val-dosage { color:#F8FAFC !important; }',
                '[data-theme="dark"] .mmp-cmpd-name  { color:#F8FAFC !important; }',
                '[data-theme="dark"] .mmp-strength-pill {',
                '    background:rgba(37,99,235,0.20)!important;',
                '    border-color:rgba(37,99,235,0.45)!important;',
                '    color:#60A5FA !important;',
                '}',
                '[data-theme="dark"] .mmp-alert-box {',
                '    background:rgba(234,88,12,0.10)!important;',
                '    border-color:rgba(234,88,12,0.35)!important;',
                '}',
                '[data-theme="dark"] .mmp-alert-text    { color:#CBD5E1 !important; }',
                '[data-theme="dark"] .mmp-purpose-text  { color:#CBD5E1 !important; }',
                '[data-theme="dark"] .mmp-brands-row    { border-top-color:rgba(255,255,255,0.08)!important; }',
                '[data-theme="dark"] .mmp-section-hdr-title { color:#F8FAFC !important; }',
                '@media (max-width: 720px) {',
                '    .mmp-layout { flex-direction: column !important; gap: 16px !important; }',
                '    .mmp-col-img { flex: unset !important; max-width: 100% !important; width: 100% !important; }',
                '    .mmp-title { font-size: 1.20rem !important; }',
                '    .mmp-grid-2x2 { grid-template-columns: 1fr 1fr !important; }',
                '}',
                '@media (max-width: 480px) {',
                '    .mmp-grid-2x2 { grid-template-columns: 1fr !important; }',
                '}',
                f'.st-key-btn_deep_chat_{modal_key_id} button {{',
                '    height: 46px !important;',
                '    min-height: 46px !important;',
                '    font-size: 0.90rem !important;',
                '    font-weight: 700 !important;',
                '    background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;',
                '    border: none !important;',
                '    border-radius: 12px !important;',
                '    color: #FFFFFF !important;',
                '    box-shadow: 0 4px 14px rgba(37,99,235,0.35) !important;',
                '    transition: all 0.18s ease !important;',
                '}',
                f'.st-key-btn_deep_chat_{modal_key_id} button:hover {{',
                '    box-shadow: 0 6px 20px rgba(37,99,235,0.50) !important;',
                '    transform: translateY(-1px) !important;',
                '}',
                '</style>',
                '<div class="mmp-layout">',
                '    <div class="mmp-col-img">',
                '        <div class="mmp-img-box">',
                f'            {img_block}',
                '        </div>',
                '        <div class="mmp-badges-row">',
                '            <div class="mmp-badge mmp-badge-rx">',
                '                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                    <rect x="4" y="2" width="16" height="20" rx="3"/>',
                '                    <line x1="9" y1="7" x2="15" y2="7"/>',
                '                    <line x1="9" y1="12" x2="15" y2="12"/>',
                '                    <line x1="9" y1="17" x2="13" y2="17"/>',
                '                </svg>',
                f'                {med_type_str}',
                '            </div>',
                '            <div class="mmp-badge mmp-badge-ok">',
                '                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">',
                '                    <circle cx="12" cy="12" r="11" fill="#16A34A"/>',
                '                    <polyline points="7.5 12 10.5 15 16.5 9" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>',
                '                </svg>',
                '                DOCMINDX VERIFIED',
                '            </div>',
                '        </div>',
                '    </div>',
                '    <div class="mmp-col-info">',
                f'        <h2 class="mmp-title">{med["name"]}</h2>',
                '        <div class="mmp-grid-card">',
                '            <div class="mmp-grid-2x2">',
                '                <div class="mmp-cell">',
                '                    <div class="mmp-icon-circle mmp-ic-blue">',
                '                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                            <line x1="16.5" y1="7.5" x2="7.5" y2="16.5"/>',
                '                            <path d="M14 5l3 3a4.24 4.24 0 0 1 0 6l-5 5a4.24 4.24 0 0 1-6 0l-1-1a4.24 4.24 0 0 1 0-6l5-5a4.24 4.24 0 0 1 6 0z"/>',
                '                        </svg>',
                '                    </div>',
                '                    <div>',
                '                        <div class="mmp-cell-label">Generic:</div>',
                f'                        <div class="mmp-val-generic">{generic_val}</div>',
                '                    </div>',
                '                </div>',
                '                <div class="mmp-cell">',
                '                    <div class="mmp-icon-circle mmp-ic-teal">',
                '                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0891B2" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>',
                '                            <path d="M6 12v5c3 3 9 3 12 0v-5"/>',
                '                        </svg>',
                '                    </div>',
                '                    <div>',
                '                        <div class="mmp-cell-label">Course:</div>',
                f'                        <div class="mmp-val-course">{course_val}</div>',
                '                    </div>',
                '                </div>',
                '                <div class="mmp-cell">',
                '                    <div class="mmp-icon-circle mmp-ic-red">',
                '                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                            <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/>',
                '                            <path d="m8.5 8.5 7 7"/>',
                '                        </svg>',
                '                    </div>',
                '                    <div>',
                '                        <div class="mmp-cell-label">Dosage:</div>',
                f'                        <div class="mmp-val-dosage">{dosage_val}</div>',
                '                    </div>',
                '                </div>',
                '                <div class="mmp-cell">',
                '                    <div class="mmp-icon-circle mmp-ic-orange">',
                '                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                            <circle cx="12" cy="12" r="10"/>',
                '                            <polyline points="12 6 12 12 16 14"/>',
                '                        </svg>',
                '                    </div>',
                '                    <div>',
                '                        <div class="mmp-cell-label">Timing:</div>',
                f'                        <div class="mmp-val-timing">{timing_val}</div>',
                '                    </div>',
                '                </div>',
                '            </div>',
                '            <div class="mmp-brands-row">',
                '                <div class="mmp-icon-circle mmp-ic-tag" style="width:36px;height:36px;min-width:36px;">',
                '                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                        <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>',
                '                        <line x1="7" y1="7" x2="7.01" y2="7"/>',
                '                    </svg>',
                '                </div>',
                '                <div class="mmp-brands-text">',
                f'                    <b style="color:var(--mm-text-secondary,#64748B);">Popular Brands:</b> <span style="font-weight:600;">{brands_str}</span>',
                '                </div>',
                '            </div>',
                '        </div>',
                '        <div class="mmp-section-hdr">',
                '            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                <path d="M10 2v7.31"/><path d="M14 2v7.31"/>',
                '                <path d="M8.5 2h7"/>',
                '                <path d="M14 9.3 18.8 17A3 3 0 0 1 16.2 21H7.8a3 3 0 0 1-2.6-4L10 9.3"/>',
                '                <path d="M7 16h10"/>',
                '            </svg>',
                '            <span class="mmp-section-hdr-title">Active Chemical Compounds &amp; Formula:</span>',
                '        </div>',
                f'        {compounds_html}',
                '        <div class="mmp-section-hdr">',
                '            <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">',
                '                <circle cx="12" cy="12" r="10"/>',
                '                <circle cx="12" cy="12" r="6"/>',
                '                <circle cx="12" cy="12" r="2"/>',
                '            </svg>',
                '            <span class="mmp-section-hdr-title">Purpose &amp; Why Take This Medicine:</span>',
                '        </div>',
                f'        <div class="mmp-purpose-text">{ind_text}</div>',
                '        <div class="mmp-alert-box">',
                '            <div style="flex-shrink:0;margin-top:1px;">',
                '                <svg width="22" height="22" viewBox="0 0 24 24" fill="none">',
                '                    <circle cx="12" cy="12" r="11" fill="#EA580C"/>',
                '                    <line x1="12" y1="7" x2="12" y2="13" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round"/>',
                '                    <circle cx="12" cy="17" r="1.3" fill="#FFFFFF"/>',
                '                </svg>',
                '            </div>',
                '            <div class="mmp-alert-content">',
                '                <span class="mmp-alert-title">Safety &amp; Precautions:</span>',
                f'                <span class="mmp-alert-text">{warn_text}</span>',
                '            </div>',
                '        </div>',
                '    </div>',
                '</div>'
            ]
            clean_html = "\n".join([line.strip() for line in raw_html_lines if line.strip()])
            st.markdown(clean_html, unsafe_allow_html=True)

            # Bottom CTA Button
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            chat_btn_label = {
                "en": "\u2726  Deep Clinical Analysis & More Info in AI Chat",
                "hi": "\u2726  AI Chat me \u0926\u0935\u093e\u0908 \u0915\u093e \u0938\u0902\u092a\u0942\u0930\u094d\u0923 \u0935\u093f\u0935\u0932\u0947\u0937\u0923 \u0914\u0930 \u0935\u093f\u0936\u094d\u0932\u0947\u0937\u0923",
                "gu": "\u2726  AI Chat \u0aae\u0abe\u0a82 \u0aa6\u0ab5\u0abe\u0aa8\u0ac1\u0a82 \u0ab8\u0a82\u0aaa\u0ac2\u0ab0\u0acd\u0aa3 \u0ab5\u0abf\u0ab6\u0acd\u0ab2\u0ac7\u0ab7\u0aa3 \u0a85\u0aa8\u0ac7 \u0aae\u0abe\u0ab9\u0abf\u0aa4\u0ac0"
            }.get(lang_code, "\u2726  Deep Clinical Analysis & More Info in AI Chat")

            if st.button(chat_btn_label, key=f"btn_deep_chat_{modal_key_id}", type="primary", use_container_width=True):
                st.session_state["floating_chat_open"] = True
                user_disp_q = f"Deep analyze and clinical breakdown for {med['name']}"
                prompt_lang_name = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}.get(lang_code, "English")
                system_exec_q = (
                    f"Please provide a comprehensive clinical, pharmacological, and therapeutic deep-dive for the medication '{med['name']}' in {prompt_lang_name}.\n"
                    f"Include:\n"
                    f"1. Active chemical compounds, molecular structure, and pharmacokinetics\n"
                    f"2. Exact clinical indications (why this medicine is prescribed and how it works)\n"
                    f"3. Optimal dosage, timing (food interactions), and duration rules\n"
                    f"4. Contraindications, side effects to watch for, and safety precautions\n"
                    f"5. Common commercial brand names available in pharmacies"
                )
                if "floating_chat_history" not in st.session_state:
                    st.session_state["floating_chat_history"] = []
                st.session_state["floating_chat_history"].append({"role": "user", "content": user_disp_q})
                st.session_state["pending_chat_query"] = system_exec_q
                st.rerun()

        
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="mm-triage-header-card">
            <div class="mm-triage-header-left">
                <div class="mm-triage-icon-wrap">
                    <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                </div>
                <div>
                    <div class="mm-triage-eyebrow">
                        <span class="mm-triage-pulse-dot"></span>
                        {T.get("clinical_report_tag", "CLINICAL EVALUATION REPORT")}
                    </div>
                    <div class="mm-triage-header-title">
                        {T.get("triage_results_title", "Clinical Assessment & Triage Findings")}
                    </div>
                    <div class="mm-triage-header-sub">
                        {T.get("clinical_assessment_subtitle", "AI-assisted evaluation based on provided symptoms, history, and clinical guidelines.")}
                    </div>
                </div>
            </div>
            <div>
                <div class="mm-triage-header-badge">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="#2563EB" stroke="#2563EB" stroke-width="1.2" style="flex-shrink: 0;">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <polyline points="9 12 11 14 15 9" fill="none" stroke="#FFFFFF" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <div class="mm-triage-header-badge-sep"></div>
                    <span class="mm-triage-header-badge-text">
                        {care_res.get('api_source', 'DocMindX AI Verified Care').upper()}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Seasonal Epidemiological Advisory (if active)
        seasonal_data = t_res.get("seasonal_alert")
        if seasonal_data and isinstance(seasonal_data, dict):
            s_title = seasonal_data.get("headline") or seasonal_data.get("title", "Seasonal Health Advisory")
            s_risk = str(seasonal_data.get("risk_level", "MODERATE")).upper()
            s_desc = seasonal_data.get("message") or seasonal_data.get("advisory", "")
            st.markdown(f"""
            <div style="background: rgba(234, 88, 12, 0.08); border: 1.2px solid #F97316; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="#EA580C"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
                        <b style="color: #EA580C; font-size: 0.88rem; text-transform: uppercase;">SEASONAL EPIDEMIOLOGICAL ADVISORY: {s_title}</b>
                    </div>
                    <span style="background: rgba(234, 88, 12, 0.15); color: #EA580C; border: 1px solid rgba(234, 88, 12, 0.4); border-radius: 999px; padding: 2px 10px; font-size: 0.72rem; font-weight: 800;">RISK LEVEL: {s_risk}</span>
                </div>
                <div style="font-size: 0.82rem; color: var(--mm-text-primary); line-height: 1.45; padding-left: 26px;">
                    {s_desc}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Emergency Red Flag (if active)
        red_flags_list = t_res.get("emergency_red_flags") or t_res.get("red_flags") or []
        if red_flags_list:
            rf_items_html = "<br/>".join([f"• {x}" for x in red_flags_list if str(x).strip()])
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.08); border: 1.2px solid #EF4444; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="#DC2626"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                    <b style="color: #DC2626; font-size: 0.88rem; text-transform: uppercase;">EMERGENCY RED FLAG DETECTED — IMMEDIATE MEDICAL EVALUATION REQUIRED</b>
                </div>
                <div style="font-size: 0.82rem; color: #DC2626; line-height: 1.45; padding-left: 26px; font-weight: 500;">
                    {rf_items_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 1. Fallback Warning Badge (If offline dataset was used)
        if care_res.get("is_fallback"):
            st.markdown(f"""
            <div style="background: rgba(234, 88, 12, 0.12); border: 1.5px solid #F97316; border-radius: 12px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
                <div>
                    <b style="color: #EA580C; font-size: 0.90rem;">{T.get("offline_fallback_badge", "Offline Clinical Dataset Fallback Active")}</b>
                    <p style="color: var(--mm-text-primary); font-size: 0.82rem; margin: 2px 0 0 0;">{care_res.get("fallback_warning", T.get("offline_fallback_warning", "Live API could not be reached. Showing standardized local dataset."))}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 2. Clinical Summary
        summary_text = care_res.get("summary") or generate_health_summary_ai(st.session_state.get("selected_symptoms_list", []), top_disease_name, u_ctx, lang=lang_code)
        st.markdown(f"""
        <div class="mm-summary-card">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <div style="width: 36px; height: 36px; min-width: 36px; border-radius: 50%; background: #3B82F6; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                </div>
                <b class="mm-text-blue" style="color: #1D4ED8; font-size: 1.05rem; font-weight: 800;">
                    {T.get("clinical_summary_title", "Clinical Summary").rstrip(":")}
                </b>
            </div>
            <p style="color: var(--mm-text-primary); font-size: 0.88rem; line-height: 1.6; margin: 0; padding-left: 2px;">
                {summary_text}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 3. Expected Clinical Recovery Timeline
        rec_duration = care_res.get("recovery_duration", "5 – 7 Days with rest and proper medication.")
        st.markdown(f"""
        <div class="mm-recovery-card">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 36px; height: 36px; min-width: 36px; border-radius: 50%; background: #10B981; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    </div>
                    <b class="mm-text-green" style="color: #047857; font-size: 1.05rem; font-weight: 800;">
                        {T.get("expected_recovery_title", "Expected Clinical Recovery Timeline")}
                    </b>
                </div>
                <span class="mm-badge" style="background: rgba(16, 185, 129, 0.15); color: #059669; border: 1.2px solid rgba(16, 185, 129, 0.35); border-radius: 999px; padding: 5px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase;">
                    RECOVERY ESTIMATE
                </span>
            </div>
            <p style="color: var(--mm-text-primary); font-size: 0.88rem; line-height: 1.55; margin: 0; padding-left: 2px;">
                {rec_duration}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 4. Verified Dynamic Medication Gallery (All medicines with food timing, photo, dosage)
        medicine_gallery = care_res.get("medicine_gallery", [])
        if medicine_gallery:
            with st.container(border=True):
                st.markdown(f"""
                <div class="mm-section-header-card">
                    <div style="display: flex; align-items: center; gap: 16px; flex: 1; min-width: 280px;">
                        <div class="mm-section-header-avatar">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 20.5l10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 1.18rem; font-weight: 850; color: var(--mm-text-primary); line-height: 1.25; letter-spacing: -0.3px;">
                                {T.get('verified_med_title', 'Verified Medical & Pharmaceutical Guidance')}
                            </div>
                            <div style="font-size: 0.84rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 450;">
                                {T.get('verified_med_sub', 'Personalized medication suggestions with verified dosages and food timing instructions.')} ({len(medicine_gallery)} items)
                            </div>
                        </div>
                    </div>
                    <div>
                        <span class="mm-badge" style="background: #EFF6FF; color: #2563EB; border: 1.2px solid #BFDBFE; border-radius: 999px; padding: 6px 16px; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase;">
                            {len(medicine_gallery)} {T.get('medicines_badge', 'MEDICINES')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                num_meds = len(medicine_gallery)
                for chunk_start in range(0, num_meds, 3):
                    med_chunk = medicine_gallery[chunk_start:chunk_start+3]
                    med_cols = st.columns(3)
                    for m_idx, med in enumerate(med_chunk):
                        with med_cols[m_idx]:
                            is_dark = st.session_state.get("dark_mode", False)
                            ft = med.get('food_timing', 'After Food')
                        
                            # Timing color logic
                            if "before" in ft.lower() or "empty" in ft.lower() or "pehle" in ft.lower() or "khali" in ft.lower():
                                ft_color = "#FB923C" if is_dark else "#EA580C"
                            else:
                                ft_color = "#4ADE80" if is_dark else "#16A34A"
                        
                            # Split timing into main label and subtext if parentheses exist
                            if "(" in ft:
                                ft_parts = ft.split("(", 1)
                                timing_main = ft_parts[0].strip()
                                timing_sub = f"({ft_parts[1].strip()}"
                            else:
                                timing_main = ft.strip()
                                timing_sub = ""

                            # Resolve medicine packaging / product image
                            med_img = med.get('image')
                            if not med_img or not isinstance(med_img, str) or not med_img.strip():
                                from ai.utils.image_resolver import resolve_image
                                med_img, _ = resolve_image("medicine", med.get('name', ''))
                                med['image'] = med_img
                        
                            fallback_img = "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&q=80"

                            # Title & Brand formatting: e.g. "Pantoprazole 40mg (Pan 40 / Pantocid)"
                            med_name_raw = med.get('name', 'Medicine').strip()
                            med_brand_raw = med.get('candidate_name', '').strip()
                            if '(' in med_name_raw:
                                med_title_full = med_name_raw
                            elif med_brand_raw and med_brand_raw.lower() not in med_name_raw.lower():
                                med_title_full = f"{med_name_raw} ({med_brand_raw})"
                            else:
                                med_title_full = med_name_raw

                            # Clinical indication / description
                            med_ind = med.get('indication', 'Reduces gastric acid production and promotes healing of peptic ulcers.')

                            # Type badge
                            med_type = med.get('type', 'Prescription').strip()
                            badge_type_text = med_type.upper() if med_type else "PRESCRIPTION"

                            # Values
                            dosage_val = med.get('dosage', '1 Tablet once daily')
                            duration_val = med.get('course_duration', '7 to 14 Days')

                            # Dynamic Theme Colors
                            card_bg = "#111827" if is_dark else "#FFFFFF"
                            card_border = "#1F2937" if is_dark else "#E2E8F0"
                            title_color = "#F8FAFC" if is_dark else "#0F172A"
                            desc_color = "#94A3B8" if is_dark else "#64748B"
                            box_bg = "#0B1220" if is_dark else "#F8FAFC"
                            box_border = "#1F2937" if is_dark else "#E2E8F0"
                            label_color = "#94A3B8" if is_dark else "#64748B"
                            val_color = "#F8FAFC" if is_dark else "#0F172A"
                            divider_color = "#1F2937" if is_dark else "#E2E8F0"

                            pill_icon_bg = "rgba(14, 165, 233, 0.2)" if is_dark else "#E0F2FE"
                            pill_icon_color = "#38BDF8" if is_dark else "#0284C7"

                            food_icon_bg = "rgba(234, 88, 12, 0.2)" if is_dark else "#FFEDD5"
                            food_icon_color = "#FB923C" if is_dark else "#EA580C"

                            cal_icon_bg = "rgba(124, 58, 237, 0.2)" if is_dark else "#EDE9FE"
                            cal_icon_color = "#A78BFA" if is_dark else "#7C3AED"
                            cal_val_color = "#60A5FA" if is_dark else "#2563EB"

                            rx_bg = "rgba(14, 165, 233, 0.15)" if is_dark else "#E0F2FE"
                            rx_color = "#38BDF8" if is_dark else "#0284C7"
                            rx_border = "rgba(14, 165, 233, 0.35)" if is_dark else "#BAE6FD"

                            ver_bg = "rgba(34, 197, 94, 0.15)" if is_dark else "#DCFCE7"
                            ver_color = "#4ADE80" if is_dark else "#16A34A"
                            ver_border = "rgba(34, 197, 94, 0.35)" if is_dark else "#BBF7D0"

                            with st.container(border=True, key=f"med_card_box_{chunk_start}_{m_idx}"):
                                card_html = f"""<div class="mm-med-card-content" style="width: 100%; box-sizing: border-box; display: flex; flex-direction: column; height: 100%;">
    <div style="width: 100%; height: 185px; min-height: 185px; max-height: 185px; border-radius: 14px; overflow: hidden; background: {box_bg}; margin-bottom: 12px; position: relative; display: flex; align-items: center; justify-content: center;">
    <img src="{med_img}" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='{fallback_img}';" style="max-width: 100%; max-height: 100%; width: 100%; height: 100%; object-fit: contain; border-radius: 14px; display: block;" alt="{med_name_raw}" />
    <div style="position: absolute; bottom: 8px; right: 8px; background: rgba(15, 23, 42, 0.78); backdrop-filter: blur(4px); color: #F8FAFC; font-size: 0.60rem; font-weight: 700; padding: 2px 7px; border-radius: 6px; letter-spacing: 0.02em; display: inline-flex; align-items: center; gap: 3px; box-shadow: 0 2px 6px rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.15); pointer-events: none;">
    <span style="color: #F87171; font-weight: 900;">*</span> Similar Image
    </div>
    </div>
    <div class="mm-med-title-top" style="font-size: 1.12rem; font-weight: 800; color: {title_color}; line-height: 1.25; margin-bottom: 4px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;" title="{med_title_full}">{med_title_full}</div>
    <div class="mm-med-desc" style="font-size: 0.82rem; color: {desc_color}; line-height: 1.4; margin-bottom: 12px; height: 38px; min-height: 38px; max-height: 38px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{med_ind}</div>
    <div class="mm-med-info-box-grid" style="background: {box_bg}; border: 1.2px solid {box_border}; border-radius: 14px; padding: 8px 6px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 4px; box-sizing: border-box; min-height: 68px;">
    <div class="mm-med-stat-col" style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {pill_icon_bg}; display: flex; align-items: center; justify-content: center; color: {pill_icon_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M4.22 11.29l5.07-5.07a5 5 0 0 1 7.07 0l2.35 2.35a5 5 0 0 1 0 7.07l-5.07 5.07a5 5 0 0 1-7.07 0l-2.35-2.35a5 5 0 0 1 0-7.07zm1.41 1.41a3 3 0 0 0 0 4.24l2.35 2.35a3 3 0 0 0 4.24 0l1.41-1.41-6.59-6.59-1.41 1.41z"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div class="mm-med-stat-label" style="font-size: 0.60rem; color: {label_color}; font-weight: 600; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">Dosage & Freq</div>
    <div class="mm-med-stat-val" style="font-size: 0.64rem; font-weight: 700; color: {val_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{dosage_val}">{dosage_val}</div>
    </div>
    </div>
    <div class="mm-med-stat-divider" style="width: 1px; height: 32px; background: {divider_color}; flex-shrink: 0;"></div>
    <div class="mm-med-stat-col" style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {food_icon_bg}; display: flex; align-items: center; justify-content: center; color: {food_icon_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-3v8h2.5v8H21V2c-2.76 0-5 2.24-5 4z"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div class="mm-med-stat-label" style="font-size: 0.60rem; color: {label_color}; font-weight: 600; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">Timing</div>
    <div class="mm-med-stat-val" style="font-size: 0.64rem; font-weight: 700; color: {ft_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{timing_main} {timing_sub}">{timing_main} {timing_sub}</div>
    </div>
    </div>
    <div class="mm-med-stat-divider" style="width: 1px; height: 32px; background: {divider_color}; flex-shrink: 0;"></div>
    <div class="mm-med-stat-col" style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {cal_icon_bg}; display: flex; align-items: center; justify-content: center; color: {cal_icon_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10z"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div class="mm-med-stat-label" style="font-size: 0.60rem; color: {label_color}; font-weight: 600; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">Course Duration</div>
    <div class="mm-med-stat-val" style="font-size: 0.64rem; font-weight: 700; color: {cal_val_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{duration_val}">{duration_val}</div>
    </div>
    </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px;">
    <span class="mm-med-badge-rx" style="background: {rx_bg}; color: {rx_color}; border: 1.2px solid {rx_border}; border-radius: 999px; padding: 4px 14px; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; display: inline-flex; align-items: center; gap: 6px;">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58.55 0 1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.55-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"/></svg>
    <span>{badge_type_text}</span>
    </span>
    <span class="mm-med-badge-verified" style="background: {ver_bg}; color: {ver_color}; border: 1.2px solid {ver_border}; border-radius: 999px; padding: 4px 14px; font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; display: inline-flex; align-items: center; gap: 6px;">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
    <span>DOCMINDX VERIFIED</span>
    </span>
    </div>
    </div>"""
                                st.markdown(card_html, unsafe_allow_html=True)

                                btn_label = f"{T.get('view_compounds_btn', 'View Active Compounds & Info')} →"
                                if st.button(btn_label, key=f"btn_med_modal_{chunk_start}_{m_idx}", type="primary", use_container_width=True):
                                    show_medicine_modal(med)
            
                st.markdown(f"<div style='font-size: 0.72rem; color: var(--mm-text-muted); margin: 6px 0 18px 0; font-style: italic;'>{T.get('medicine_gallery_disclaimer', 'Always confirm dosage with a physician or pharmacist.')}</div>", unsafe_allow_html=True)

        # 4.5. Clinical Injections & IV Infusions (Strictly Conditional)
        inj_data = care_res.get("injections_and_iv", {})
        if inj_data and inj_data.get("is_indicated") and inj_data.get("injections"):
            injections_list = inj_data.get("injections", [])
            admin_setting = inj_data.get("admin_setting", "Hospital / Clinic Administration Only")
            inj_rationale = inj_data.get("clinical_rationale", "")
            
            st.markdown(f"""
            <div class="mm-card" style="border-top: 3.5px solid #EF4444; margin-top: 14px; margin-bottom: 18px; padding: 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <h4 style="margin: 0; font-size: 1.05rem; color: var(--mm-text-primary); display: flex; align-items: center; gap: 8px;">
                            {T.get('injections_title', 'Clinical Injections & IV Infusions Guidance')}
                        </h4>
                        <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">
                            {T.get('injections_sub', 'Medically indicated injectable therapies to be administered under clinical supervision.')}
                        </div>
                    </div>
                    <span class="mm-badge mm-badge-critical" style="font-size: 0.72rem; padding: 4px 10px;">{admin_setting}</span>
                </div>
                {f'<p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.5; margin: 4px 0 12px 0;"><b>Clinical Indication & Rationale:</b> {inj_rationale}</p>' if inj_rationale else ''}
            """, unsafe_allow_html=True)
            
            inj_cols = st.columns(3)
            for i_idx, inj in enumerate(injections_list):
                with inj_cols[i_idx % 3]:
                    i_type = inj.get("type", "Injectable")
                    st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.06); border: 1.2px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 12px; margin-bottom: 10px; height: 185px; min-height: 185px; max-height: 185px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                                <b style="font-size: 0.90rem; color: var(--mm-text-primary); display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;">{inj.get('name', 'Injection')}</b>
                                <span class="mm-badge" style="background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); font-size: 0.62rem;">{i_type}</span>
                            </div>
                            <div style="font-size: 0.76rem; color: var(--mm-text-secondary); margin-bottom: 4px;">Dose: <b>{inj.get('dose', 'As prescribed')}</b></div>
                            <p style="font-size: 0.76rem; color: var(--mm-text-secondary); line-height: 1.35; margin: 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;"><b>Purpose:</b> {inj.get('purpose', '')}</p>
                        </div>
                        <div style="font-size: 0.70rem; color: #EF4444; font-weight: 600; line-height: 1.25; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                            * {inj.get('precautions', 'Hospital/Clinic administration only.')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 5. Supportive Restorative Yoga (Clinically safe postures)
        yoga_recs = care_res.get("yoga_recommendations", [])
        if yoga_recs:
            with st.container(border=True):
                st.markdown(f"""
                <div class="mm-section-header-card">
                    <div style="display: flex; align-items: center; gap: 16px; flex: 1; min-width: 280px;">
                        <div class="mm-section-header-avatar">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="2"/><path d="M12 7v4"/><path d="M7 14l5-3 5 3"/><path d="M9 18l3-3 3 3"/><path d="M5 21l7-3 7 3"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 1.18rem; font-weight: 850; color: var(--mm-text-primary); line-height: 1.25; letter-spacing: -0.3px;">
                                {T.get('supportive_yoga_title', 'Supportive Restorative Yoga & Physiotherapy')}
                            </div>
                            <div style="font-size: 0.84rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 450;">
                                {T.get('supportive_yoga_sub', 'Clinically safe postures and mobility routines to facilitate physical recovery.')} ({len(yoga_recs)} routines)
                            </div>
                        </div>
                    </div>
                    <div>
                        <span class="mm-badge" style="background: #ECFDF5; color: #059669; border: 1.2px solid #A7F3D0; border-radius: 999px; padding: 6px 16px; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase;">
                            {len(yoga_recs)} {T.get('routines_badge', 'ROUTINES')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                num_yoga = len(yoga_recs)
                for chunk_start in range(0, num_yoga, 3):
                    y_chunk = yoga_recs[chunk_start:chunk_start+3]
                    y_cols = st.columns(3)
                    for y_idx, y_item in enumerate(y_chunk):
                        with y_cols[y_idx]:
                            is_dark = st.session_state.get("dark_mode", False)
                        
                            # Title and Sanskrit / English Alternative formatting
                            name_raw = y_item.get('name', 'Yoga Pose').strip()
                            sans_raw = y_item.get('sanskrit_name', '').strip()
                            if '(' in name_raw:
                                main_name = name_raw.split('(')[0].strip()
                                sub_text = f"({name_raw.split('(')[1].strip()}"
                                if not sub_text.endswith(')'):
                                    sub_text += ')'
                            elif sans_raw:
                                main_name = name_raw
                                sub_text = f"({sans_raw})"
                            else:
                                main_name = name_raw
                                sub_text = f"({name_raw})"
                        
                            yt_link = y_item.get('youtube_url', f"https://www.youtube.com/results?search_query=how+to+do+{main_name}+yoga+tutorial")
                            y_img = y_item.get('image')
                            if not y_img or not isinstance(y_img, str) or not y_img.strip():
                                from ai.utils.image_resolver import resolve_image
                                y_img, _ = resolve_image("yoga", f"{main_name} {sans_raw}")
                                y_item['image'] = y_img
                            fallback_yoga_img = "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=600&q=80"

                            y_ben = y_item.get('benefits', 'Restorative stretching and clinical recovery posture.').strip()
                            ben_text = (y_ben + ' ' + y_item.get('instructions', '') + ' ' + name_raw).lower()

                            # Dynamic 3 Benefits extraction
                            # 1. Improves
                            if any(k in ben_text for k in ["digest", "stomach", "pet", "gastric", "acidity", "kabz", "ulcer", "paachan"]):
                                imp_val = T.get("yoga_imp_digestion", "Digestion")
                            elif any(k in ben_text for k in ["breath", "lung", "oxygen", "pranayama", "shwas", "respirat", "asthma"]):
                                imp_val = T.get("yoga_imp_resp", "Respiratory Vitality")
                            elif any(k in ben_text for k in ["circulat", "blood", "heart", "rakt"]):
                                imp_val = T.get("yoga_imp_circ", "Blood Circulation")
                            elif any(k in ben_text for k in ["postur", "align", "balance", "santulan"]):
                                imp_val = T.get("yoga_imp_posture", "Body Posture")
                            elif any(k in ben_text for k in ["flexib", "stretch", "lacheelapan"]):
                                imp_val = T.get("yoga_imp_flex", "Flexibility")
                            else:
                                imp_val = T.get("yoga_imp_vitality", "Vitality & Recovery")

                            # 2. Strengthens
                            if any(k in ben_text for k in ["abdomin", "belly", "core", "abs"]):
                                str_val = T.get("yoga_str_abs", "Abdominal Muscles")
                            elif any(k in ben_text for k in ["spine", "back", "reedh", "peeth"]):
                                str_val = T.get("yoga_str_spine", "Spine & Back")
                            elif any(k in ben_text for k in ["chest", "shoulder", "chaati", "kandha"]):
                                str_val = T.get("yoga_str_chest", "Chest & Shoulders")
                            elif any(k in ben_text for k in ["leg", "hamstring", "knee", "taang", "ghutna", "joint"]):
                                str_val = T.get("yoga_str_legs", "Legs & Joints")
                            elif any(k in ben_text for k in ["neck", "gardan", "cervical"]):
                                str_val = T.get("yoga_str_neck", "Neck & Shoulders")
                            else:
                                str_val = T.get("yoga_str_core", "Core & Spine")

                            # 3. Relieves
                            if any(k in ben_text for k in ["stress", "fatigue", "tension", "calm", "thaan", "tanaav", "mental"]):
                                rel_val = T.get("yoga_rel_stress", "Stress & Fatigue")
                            elif any(k in ben_text for k in ["pain", "ache", "dard"]):
                                rel_val = T.get("yoga_rel_pain", "Body & Joint Pain")
                            elif any(k in ben_text for k in ["stiff", "tight"]):
                                rel_val = T.get("yoga_rel_stiff", "Muscle Stiffness")
                            elif any(k in ben_text for k in ["anxiety", "nervous", "chinta", "headache", "sir dard"]):
                                rel_val = T.get("yoga_rel_anxiety", "Mental Tension")
                            else:
                                rel_val = T.get("yoga_rel_stress", "Stress & Fatigue")

                            # Dynamic Theme Colors
                            card_bg = "#111827" if is_dark else "#FFFFFF"
                            card_border = "#1F2937" if is_dark else "#E2E8F0"
                            title_color = "#F8FAFC" if is_dark else "#0F172A"
                            desc_color = "#94A3B8" if is_dark else "#64748B"
                            box_bg = "#0B1220" if is_dark else "#F8FAFC"
                            box_border = "#1F2937" if is_dark else "#E2E8F0"
                            label_color = "#94A3B8" if is_dark else "#64748B"
                            val_color = "#F8FAFC" if is_dark else "#0F172A"
                            divider_color = "#1F2937" if is_dark else "#E2E8F0"

                            pill_bg = "rgba(37, 99, 235, 0.18)" if is_dark else "#EFF6FF"
                            pill_border = "rgba(37, 99, 235, 0.35)" if is_dark else "#DBEAFE"
                            pill_color = "#60A5FA" if is_dark else "#2563EB"

                            peach_bg = "rgba(239, 68, 68, 0.2)" if is_dark else "#FEE2E2"
                            peach_color = "#F87171" if is_dark else "#DC2626"

                            green_bg = "rgba(34, 197, 94, 0.2)" if is_dark else "#DCFCE7"
                            green_color = "#4ADE80" if is_dark else "#16A34A"

                            blue_bg = "rgba(37, 99, 235, 0.2)" if is_dark else "#DBEAFE"
                            blue_color = "#60A5FA" if is_dark else "#2563EB"

                            with st.container(border=True, key=f"yoga_card_box_{chunk_start}_{y_idx}"):
                                yoga_card_html = f"""<div class="mm-yoga-card-content" style="width: 100%; box-sizing: border-box; display: flex; flex-direction: column; height: 100%;">
    <div style="width: 100%; height: 185px; min-height: 185px; max-height: 185px; border-radius: 14px; overflow: hidden; background: {box_bg}; margin-bottom: 12px; position: relative; display: flex; align-items: center; justify-content: center;">
    <img src="{y_img}" referrerpolicy="no-referrer" onerror="this.onerror=null; this.src='{fallback_yoga_img}';" style="max-width: 100%; max-height: 100%; width: 100%; height: 100%; object-fit: contain; border-radius: 14px; display: block;" alt="{main_name}" />
    <div style="position: absolute; bottom: 8px; right: 8px; background: rgba(15, 23, 42, 0.78); backdrop-filter: blur(4px); color: #F8FAFC; font-size: 0.60rem; font-weight: 700; padding: 2px 7px; border-radius: 6px; letter-spacing: 0.02em; display: inline-flex; align-items: center; gap: 3px; box-shadow: 0 2px 6px rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.15); pointer-events: none;">
    <span style="color: #60A5FA; font-weight: 900;">*</span> {T.get("similar_image_badge", "Similar Image")}
    </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 4px;">
    <div style="flex: 1; overflow: hidden;">
    <div class="mm-yoga-title-top" style="font-size: 1.25rem; font-weight: 800; color: {title_color}; line-height: 1.2; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;" title="{main_name}">{main_name}</div>
    <div style="font-size: 0.80rem; color: {desc_color}; font-style: italic; margin-top: 2px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;">{sub_text}</div>
    </div>
    <div style="background: {pill_bg}; color: {pill_color}; border: 1.2px solid {pill_border}; border-radius: 999px; padding: 4px 12px; font-size: 0.72rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; flex-shrink: 0;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-1.5 5c-.83 0-1.5.67-1.5 1.5v3.25l-2.42.8c-.46.15-.75.61-.69 1.09.07.56.59.95 1.15.82l2.96-.99V16h2v-2.53l2.96.99c.56.13 1.08-.26 1.15-.82.06-.48-.23-.94-.69-1.09l-2.42-.8V8.5c0-.83-.67-1.5-1.5-1.5h-1zm-4.73 10.02c-.37-.02-.73.16-.9.5-.2.4-.04.88.36 1.08l3.27 1.63V22h2v-2.38l-4.14-2.07c-.19-.1-.39-.15-.59-.15zm12.46 0c-.2 0-.4.05-.59.15L12.5 19.62V22h2v-1.77l3.27-1.63c.4-.2.56-.68.36-1.08-.17-.34-.53-.52-.9-.5z"/></svg>
    <span>{T.get("yoga_pose_tag", "Yoga Pose")}</span>
    </div>
    </div>
    <div class="mm-yoga-desc" style="font-size: 0.82rem; color: {desc_color}; line-height: 1.4; margin: 8px 0 12px 0; height: 38px; min-height: 38px; max-height: 38px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{y_ben}</div>
    <div class="mm-yoga-info-box-grid" style="background: {box_bg}; border: 1.2px solid {box_border}; border-radius: 14px; padding: 8px 6px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 4px; box-sizing: border-box; min-height: 68px;">
    <div style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {peach_bg}; display: flex; align-items: center; justify-content: center; color: {peach_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3C5 5 4 8 4 12c0 5 4 9 9 9 3.5 0 6-2 7-5 1-3 0-6-1-8-1-2-3-5-6-5H7z"/><path d="M10 3v4"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div style="font-size: 0.62rem; color: {title_color}; font-weight: 700; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">{T.get("yoga_stat_improves", "Improves")}</div>
    <div style="font-size: 0.62rem; font-weight: 600; color: {desc_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{imp_val}">{imp_val}</div>
    </div>
    </div>
    <div style="width: 1px; height: 32px; background: {divider_color}; flex-shrink: 0;"></div>
    <div style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {green_bg}; display: flex; align-items: center; justify-content: center; color: {green_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M20.57 14.86L22 13.43 20.57 12 17 15.57 8.43 7 12 3.43 10.57 2 9.14 3.43 7.71 2 5.57 4.14 4.14 2.71 2.71 4.14l1.43 1.43L2 7.71l1.43 1.43L2 10.57 3.43 12 7 8.43 15.57 17 12 20.57 13.43 22l1.43-1.43 1.43 1.43 2.14-2.14 1.43 1.43 1.43-1.43-1.43-1.43 1.43-1.43zM5.57 7l1.43-1.43 1.43 1.43L7 8.43 5.57 7zm10 10l1.43-1.43 1.43 1.43L17 18.43 15.57 17z"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div style="font-size: 0.62rem; color: {title_color}; font-weight: 700; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">{T.get("yoga_stat_strengthens", "Strengthens")}</div>
    <div style="font-size: 0.62rem; font-weight: 600; color: {desc_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{str_val}">{str_val}</div>
    </div>
    </div>
    <div style="width: 1px; height: 32px; background: {divider_color}; flex-shrink: 0;"></div>
    <div style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {blue_bg}; display: flex; align-items: center; justify-content: center; color: {blue_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zm-1 7c-1.66 0-3 1.34-3 3v2.5c0 .55.45 1 1 1s1-.45 1-1V12h4v2.5c0 .55.45 1 1 1s1-.45 1-1V12c0-1.66-1.34-3-3-3h-2zm-5.5 8c-.83 0-1.5.67-1.5 1.5S4.67 20 5.5 20h13c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5h-13z"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div style="font-size: 0.62rem; color: {title_color}; font-weight: 700; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">{T.get("yoga_stat_relieves", "Relieves")}</div>
    <div style="font-size: 0.62rem; font-weight: 600; color: {desc_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{rel_val}">{rel_val}</div>
    </div>
    </div>
    </div>
    <a href="{yt_link}" target="_blank" style="text-decoration: none; display: block; width: 100%; margin-top: auto; margin-bottom: 6px;">
    <div style="width: 100%; height: 44px; min-height: 44px; background: #2563EB; color: #FFFFFF; border-radius: 12px; font-size: 0.88rem; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25); transition: all 0.2s ease; cursor: pointer; box-sizing: border-box;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg>
    <span>{T.get("watch_youtube_video", "Watch Video Tutorial")} →</span>
    </div>
    </a>
    </div>"""
                                st.markdown(yoga_card_html, unsafe_allow_html=True)

        # 6. Thermal Compress & Fomentation Therapy (Ice / Hot Sek / Cold Sponging)
        compress_rec = care_res.get("compress_guidance")
        if compress_rec and isinstance(compress_rec, dict) and compress_rec.get("mode") in ["ice", "hot", "cold_sponging"]:
            c_mode = compress_rec.get("mode")
            if c_mode == "ice":
                c_border = "#3B82F6"
                c_badge = T.get("compress_mode_ice", "Cold / Cryotherapy")
                c_badge_style = "background: rgba(59, 130, 246, 0.12); color: #2563EB; border: 1.2px solid rgba(59, 130, 246, 0.4);"
                c_icon_bg = "#DBEAFE"
                c_icon_border = "#93C5FD"
                c_icon_color = "#2563EB"
            elif c_mode == "cold_sponging":
                c_border = "#06B6D4"
                c_badge = T.get("compress_mode_sponge", "Tepid Sponge / Cold Sponging")
                c_badge_style = "background: rgba(6, 182, 212, 0.12); color: #0891B2; border: 1.2px solid rgba(6, 182, 212, 0.4);"
                c_icon_bg = "#CFFAFE"
                c_icon_border = "#67E8F9"
                c_icon_color = "#0891B2"
            else:
                c_border = "#F97316"
                c_badge = T.get("compress_mode_hot", "Warm / Hot Fomentation")
                c_badge_style = "background: rgba(249, 115, 22, 0.12); color: #EA580C; border: 1.2px solid rgba(249, 115, 22, 0.4);"
                c_icon_bg = "#FFEDD5"
                c_icon_border = "#FDBA74"
                c_icon_color = "#EA580C"
                
            c_title = compress_rec.get("title") or f"{c_badge} Guidance"
            c_inst = compress_rec.get("instructions") or compress_rec.get("text", "")
            c_dur = compress_rec.get("duration", "")
            c_caut = compress_rec.get("cautions", "")
            
            duration_html = f"""
            <div class="mm-subbox-blue" style="flex: 1; min-width: 250px; display: flex; align-items: center; gap: 12px; padding: 12px 16px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                <div>
                    <b class="mm-text-blue" style="color: #1D4ED8; font-size: 0.84rem; font-weight: 700; display: block;">{T.get("recommended_duration", "Recommended Duration")}</b>
                    <span style="color: var(--mm-text-primary); font-size: 0.82rem; margin-top: 2px; display: block;">{c_dur}</span>
                </div>
            </div>
            """ if c_dur else ""

            caution_html = f"""
            <div class="mm-subbox-red" style="flex: 1; min-width: 250px; display: flex; align-items: center; gap: 12px; padding: 12px 16px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <div>
                    <b class="mm-text-red" style="color: #DC2626; font-size: 0.84rem; font-weight: 700; display: block;">{T.get("clinical_caution", "Clinical Caution")}</b>
                    <span style="color: var(--mm-text-primary); font-size: 0.82rem; margin-top: 2px; display: block;">{c_caut}</span>
                </div>
            </div>
            """ if c_caut else ""

            boxes_row = f"""
            <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 14px;">
                {duration_html}
                {caution_html}
            </div>
            """ if (duration_html or caution_html) else ""
            
            st.markdown(f"""
            <div class="mm-foment-card">
                <div style="display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                    <div style="display: flex; align-items: flex-start; gap: 14px; flex: 1; min-width: 260px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: {c_icon_bg}; border: 1.5px solid {c_icon_border}; display: flex; align-items: center; justify-content: center; color: {c_icon_color}; flex-shrink: 0;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>
                        </div>
                        <div>
                            <b style="font-size: 1.15rem; font-weight: 800; color: var(--mm-text-primary); display: block; line-height: 1.25;">{c_title}</b>
                            <div style="font-size: 0.83rem; color: var(--mm-text-secondary); margin-top: 4px; line-height: 1.45;">{c_inst}</div>
                        </div>
                    </div>
                    <div>
                        <span class="mm-badge" style="{c_badge_style} border-radius: 999px; padding: 6px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.4px; white-space: nowrap;">
                            {c_badge.upper()}
                        </span>
                    </div>
                </div>
                {boxes_row}
            </div>
            """, unsafe_allow_html=True)

        # 6.5. Targeted Physiotherapy & Rehabilitation Routines (Strictly Conditional)
        physio_data = care_res.get("physiotherapy_guidance", {})
        if physio_data and physio_data.get("is_indicated") and physio_data.get("exercises"):
            exercises_list = physio_data.get("exercises", [])
            p_rationale = physio_data.get("clinical_rationale", "")
            p_cautions = physio_data.get("cautions", "")
            
            st.markdown(f"""
            <div class="mm-card" style="border-top: 3.5px solid #8B5CF6; margin-top: 14px; margin-bottom: 18px; padding: 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <h4 style="margin: 0; font-size: 1.05rem; color: var(--mm-text-primary); display: flex; align-items: center; gap: 8px;">
                            {T.get('physiotherapy_title', 'Targeted Physiotherapy & Rehabilitation')}
                        </h4>
                        <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">
                            {T.get('physiotherapy_sub', 'Condition-specific mobility routines and strengthening exercises.')}
                        </div>
                    </div>
                    <span class="mm-badge" style="background: rgba(139, 92, 246, 0.15); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.4); font-weight: 700;">{T.get("physical_therapy_tag", "Physical Therapy")}</span>
                </div>
                {f'<p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.5; margin: 4px 0 12px 0;"><b>{T.get("clinical_rationale", "Clinical Rationale")}:</b> {p_rationale}</p>' if p_rationale else ''}
            """, unsafe_allow_html=True)
            
            p_cols = st.columns(min(3, len(exercises_list)))
            for ex_idx, ex in enumerate(exercises_list):
                with p_cols[ex_idx % len(p_cols)]:
                    yt_ex_url = ex.get("youtube_search_url") or f"https://www.youtube.com/results?search_query=how+to+do+{ex.get('name', 'physiotherapy')}+exercise+tutorial"
                    st.markdown(f"""
                    <div style="background: rgba(139, 92, 246, 0.06); border: 1.2px solid rgba(139, 92, 246, 0.3); border-radius: 10px; padding: 12px; margin-bottom: 10px; height: 215px; min-height: 215px; max-height: 215px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box;">
                        <div>
                            <b style="font-size: 0.90rem; color: var(--mm-text-primary); display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;">{ex.get('name', 'Exercise')}</b>
                            <div style="font-size: 0.74rem; color: #8B5CF6; font-weight: 600; margin: 2px 0 4px 0;">{ex.get('focus', '')} • {ex.get('reps', '10 reps')}</div>
                            <p style="font-size: 0.76rem; color: var(--mm-text-secondary); line-height: 1.35; margin: 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">{ex.get('description', '')}</p>
                        </div>
                        <div>
                            <a href="{yt_ex_url}" target="_blank" style="text-decoration: none; display: block;">
                                <button style="width: 100%; height: 32px; min-height: 32px; background: rgba(225, 29, 72, 0.12); color: #FF2E5B; border: 1.2px solid rgba(225, 29, 72, 0.4); border-radius: 6px; font-size: 0.74rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                                    {T.get("watch_youtube_video", "Watch Video Tutorial")}
                                </button>
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            if p_cautions:
                st.markdown(f"<div style='font-size: 0.72rem; color: #EF4444; font-style: italic; margin-top: 4px;'>* Caution: {p_cautions}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 6.6. Specialized Hospital Clinical Therapies & Procedures (Strictly Conditional)
        spec_data = care_res.get("specialized_therapies", {})
        if spec_data and spec_data.get("is_indicated") and spec_data.get("therapies"):
            therapies_list = spec_data.get("therapies", [])
            specialist = spec_data.get("specialist_type", "Specialist Physician")
            sp_overview = spec_data.get("overview", "")
            
            st.markdown(f"""
            <div class="mm-card" style="border-top: 3.5px solid #0284C7; margin-top: 14px; margin-bottom: 18px; padding: 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <h4 style="margin: 0; font-size: 1.05rem; color: var(--mm-text-primary); display: flex; align-items: center; gap: 8px;">
                            {T.get('specialized_therapies_title', 'Specialized Hospital Clinical Therapies & Procedures')}
                        </h4>
                        <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">
                            {T.get('specialized_therapies_sub', 'Advanced clinical treatments (Chemotherapy, Dialysis, Nebulization) required for this condition.')}
                        </div>
                    </div>
                    <span class="mm-badge" style="background: rgba(2, 132, 199, 0.15); color: #0284C7; border: 1px solid rgba(2, 132, 199, 0.4); font-weight: 700;">Referral: {specialist}</span>
                </div>
                {f'<p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.5; margin: 4px 0 12px 0;"><b>Clinical Overview:</b> {sp_overview}</p>' if sp_overview else ''}
            """, unsafe_allow_html=True)
            
            sp_cols = st.columns(min(3, len(therapies_list)))
            for th_idx, th in enumerate(therapies_list):
                with sp_cols[th_idx % len(sp_cols)]:
                    st.markdown(f"""
                    <div style="background: rgba(2, 132, 199, 0.06); border: 1.2px solid rgba(2, 132, 199, 0.3); border-radius: 10px; padding: 12px; margin-bottom: 10px; height: 180px; min-height: 180px; max-height: 180px; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box;">
                        <div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                                <b style="font-size: 0.90rem; color: var(--mm-text-primary); display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;">{th.get('name', 'Therapy')}</b>
                                <span class="mm-badge" style="background: rgba(2, 132, 199, 0.15); color: #0284C7; border: 1px solid rgba(2, 132, 199, 0.3); font-size: 0.62rem;">{th.get('category', 'Specialized')}</span>
                            </div>
                            <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-bottom: 4px;">Setting: <b>{th.get('setting', 'Tertiary Hospital')}</b></div>
                            <p style="font-size: 0.76rem; color: var(--mm-text-secondary); line-height: 1.35; margin: 0; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">{th.get('description', '')}</p>
                        </div>
                        <div style="font-size: 0.70rem; color: #0284C7; font-weight: 600;">
                            * Requires specialized multidisciplinary clinical team
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 7. Potential Conditions (Ranked by ICD-11 Confidence)
        def get_condition_avatar_svg(name: str) -> str:
            n = (name or "").lower()
            if any(k in n for k in ["ulcer", "peptic", "acid", "gastric", "gerd", "stomach", "abdomen", "digest", "gastro"]):
                return (
                    '<div style="width: 38px; height: 38px; min-width: 38px; border-radius: 50%; background: #FEE2E2; display: flex; align-items: center; justify-content: center; color: #DC2626; flex-shrink: 0; box-shadow: 0 2px 6px rgba(220, 38, 38, 0.15);">'
                    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19.5 7.5C18.8 5.4 16.9 4 14.5 4c-3.6 0-6.5 2.9-6.5 6.5 0 .5.1 1 .2 1.5C6.4 12.6 5 14.4 5 16.5 5 19 7 21 9.5 21c3.6 0 7.5-3 8.5-7.5.5-2.2 2-4.1 1.5-6z"/></svg>'
                    '</div>'
                )
            elif any(k in n for k in ["glaucoma", "eye", "vision", "cataract", "retin", "conjunctiv"]):
                return (
                    '<div style="width: 38px; height: 38px; min-width: 38px; border-radius: 50%; background: #DCFCE7; display: flex; align-items: center; justify-content: center; color: #16A34A; flex-shrink: 0; box-shadow: 0 2px 6px rgba(22, 163, 74, 0.15);">'
                    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>'
                    '</div>'
                )
            elif any(k in n for k in ["malaria", "dengue", "mosquito", "fever", "infect", "typhoid", "parasite", "virus"]):
                return (
                    '<div style="width: 38px; height: 38px; min-width: 38px; border-radius: 50%; background: #FFE4E6; display: flex; align-items: center; justify-content: center; color: #E11D48; flex-shrink: 0; box-shadow: 0 2px 6px rgba(225, 29, 72, 0.15);">'
                    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a1 1 0 0 1 1 1v2.07A8.006 8.006 0 0 1 19.93 11H22a1 1 0 1 1 0 2h-2.07A8.006 8.006 0 0 1 13 18.93V21a1 1 0 1 1-2 0v-2.07A8.006 8.006 0 0 1 4.07 13H2a1 1 0 1 1 0-2h2.07A8.006 8.006 0 0 1 11 5.07V3a1 1 0 0 1 1-1zm-3.5 6.5a1 1 0 0 0-1.41 1.41L8.5 11.33A3.99 3.99 0 0 1 12 9a3.99 3.99 0 0 1 3.5 2.33l1.41-1.42a1 1 0 1 0-1.41-1.41L14.2 9.8A5.98 5.98 0 0 0 12 7c-.82 0-1.6.17-2.3.47L8.5 8.5z"/></svg>'
                    '</div>'
                )
            elif any(k in n for k in ["heart", "cardiac", "hypertension", "artery", "bp", "chest"]):
                return (
                    '<div style="width: 38px; height: 38px; min-width: 38px; border-radius: 50%; background: #FEE2E2; display: flex; align-items: center; justify-content: center; color: #EF4444; flex-shrink: 0; box-shadow: 0 2px 6px rgba(239, 68, 68, 0.15);">'
                    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>'
                    '</div>'
                )
            elif any(k in n for k in ["lung", "respiratory", "asthma", "cough", "bronch", "pneumonia"]):
                return (
                    '<div style="width: 38px; height: 38px; min-width: 38px; border-radius: 50%; background: #DBEAFE; display: flex; align-items: center; justify-content: center; color: #2563EB; flex-shrink: 0; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);">'
                    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4c.55 0 1 .45 1 1v5.18c2.18-.75 4-2.58 4-5.18 0-.55.45-1 1-1s1 .45 1 1c0 3.84-2.73 7.04-6.42 7.82L15 20c0 .55-.45 1-1 1s-1-.45-1-1v-6h-2v6c0 .55-.45 1-1 1s-1-.45-1-1l2.42-7.18C7.73 12.04 5 8.84 5 5c0-.55.45-1 1-1s1 .45 1 1c0 2.6 1.82 4.43 4 5.18V5c0-.55.45-1 1-1z"/></svg>'
                    '</div>'
                )
            else:
                return (
                    '<div style="width: 38px; height: 38px; min-width: 38px; border-radius: 50%; background: #EFF6FF; display: flex; align-items: center; justify-content: center; color: #2563EB; flex-shrink: 0; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15);">'
                    '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M19 10.5h-5.5V5c0-.55-.45-1-1-1h-1c-.55 0-1 .45-1 1v5.5H5c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h5.5V19c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-5.5H19c.55 0 1-.45 1-1v-1c0-.55-.45-1-1-1z"/></svg>'
                    '</div>'
                )

        conditions_list = t_res.get("ranked_conditions", [])[:3]
        if conditions_list:
            with st.container(border=True):
                st.markdown(f"""
                <div class="mm-section-header-card" style="margin-top: 2px; margin-bottom: 14px;">
                    <div style="display: flex; align-items: center; gap: 16px; flex: 1; min-width: 280px;">
                        <div class="mm-section-header-avatar">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M19 10.5h-5.5V5c0-.55-.45-1-1-1h-1c-.55 0-1 .45-1 1v5.5H5c-.55 0-1 .45-1 1v1c0 .55.45 1 1 1h5.5V19c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-5.5H19c.55 0 1-.45 1-1v-1c0-.55-.45-1-1-1z"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 1.18rem; font-weight: 850; color: var(--mm-text-primary); line-height: 1.25; letter-spacing: -0.3px;">
                                {T.get('possible_conditions_title', 'Identified Potential Conditions:')}
                            </div>
                            <div style="font-size: 0.84rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 450;">
                                Differential diagnostic assessment ranked by ICD-11 algorithmic confidence. ({len(conditions_list)} conditions evaluated)
                            </div>
                        </div>
                    </div>
                    <div>
                        <span class="mm-badge" style="background: #EFF6FF; color: #2563EB; border: 1.2px solid #BFDBFE; border-radius: 999px; padding: 6px 16px; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase;">
                            {len(conditions_list)} CONDITIONS
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                res_cols = st.columns(len(conditions_list))
                for idx, cond in enumerate(conditions_list):
                    with res_cols[idx]:
                        prob_pct = cond.get("match_percentage", 65)
                        urgency = "HIGH" if prob_pct > 70 else ("MODERATE" if prob_pct > 45 else "LOW")
                        badge_class = "mm-badge-critical" if urgency == "HIGH" else ("mm-badge-warning" if urgency == "MODERATE" else "mm-badge-success")
                        c_name = cond.get("name_gu") if lang_code == "gu" and cond.get("name_gu") else (cond.get("name_hi") if lang_code == "hi" and cond.get("name_hi") else cond.get("name", "Condition"))
                        priority_str = "Very High Priority" if prob_pct > 75 else ("High Priority" if prob_pct > 60 else "Medium Priority")
                        c_desc = cond.get("mohfw_note") or f"Official National Priority Condition ({priority_str}) under MoHFW guidelines."
                        c_icd = cond.get("icd_code") or cond.get("icd11_code") or "N/A"
                        cond_icon_html = get_condition_avatar_svg(c_name)

                        st.markdown(f"""
                        <div class="mm-cond-card">
                            <div>
                                <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px;">
                                    <div style="display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0;">
                                        {cond_icon_html}
                                        <b style="font-size: 0.94rem; color: var(--mm-text-primary); line-height: 1.25; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{c_name}</b>
                                    </div>
                                    <span class="mm-badge {badge_class}" style="border-radius: 999px; padding: 3px 10px; font-size: 0.70rem; font-weight: 800; text-transform: uppercase; flex-shrink: 0;">{urgency}</span>
                                </div>
                                <div style="font-size: 0.76rem; color: var(--mm-text-secondary); margin-bottom: 6px;">
                                    Confidence Match: <b style="color: #2563EB;">{prob_pct}%</b> · ICD-11: {c_icd}
                                </div>
                            </div>
                            <div style="border-top: 1px solid var(--mm-border-color); padding-top: 8px; margin-top: 6px; display: flex; align-items: flex-start; gap: 10px;">
                                <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(37, 99, 235, 0.25); display: flex; align-items: center; justify-content: center; color: #2563EB; flex-shrink: 0; margin-top: 1px;">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 9" stroke="#2563EB" stroke-width="2.3"/></svg>
                                </div>
                                <div style="font-size: 0.76rem; color: var(--mm-text-secondary); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 32px;">
                                    {c_desc}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)


        # 7.5. Recommended Clinical Diagnostic Laboratory Tests
        tests_list = t_res.get("tests_to_discuss", [])
        if tests_list:
            def get_diag_test_svg(test_name: str) -> str:
                t_lower = str(test_name).lower()
                if any(k in t_lower for k in ["eye", "vision", "perimetry", "tonometry", "humphrey", "iop", "glaucoma", "fundus", "retin"]):
                    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>'
                elif any(k in t_lower for k in ["blood", "cbc", "bleeding", "hemoglobin", "serum", "lipid", "platelet", "glucose", "sugar"]):
                    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>'
                elif any(k in t_lower for k in ["endoscopy", "egd", "colonoscopy", "gastroscopy", "stool", "occult", "gi", "gastro"]):
                    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M8 3h8a3 3 0 0 1 3 3v2a7 7 0 0 1-7 7H9a4 4 0 0 1-4-4V6a3 3 0 0 1 3-3z"/><path d="M12 15v6"/></svg>'
                elif any(k in t_lower for k in ["h. pylori", "pylori", "antigen", "ubt", "culture", "bacteria", "pcr", "swab"]):
                    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><line x1="4.5" y1="19.5" x2="19.5" y2="4.5"/><path d="M10.5 4.5a4.24 4.24 0 0 0-6 6l9 9a4.24 4.24 0 0 0 6-6l-9-9z"/></svg>'
                elif any(k in t_lower for k in ["ecg", "ekg", "echo", "cardiac", "heart"]):
                    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>'
                else:
                    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M10 2v7.31L4.17 19.5A2 2 0 0 0 6 22h12a2 2 0 0 0 1.83-2.5L14 9.31V2"/><line x1="8" y1="2" x2="16" y2="2"/><line x1="6.5" y1="15" x2="17.5" y2="15"/></svg>'

            tests_chips_html = "".join([f'<span class="mm-diag-chip">{get_diag_test_svg(t)} <span>{t}</span></span>' for t in tests_list])
            st.markdown(f"""
            <div class="mm-diag-test-card">
                <div style="display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 14px;">
                    <div style="display: flex; align-items: flex-start; gap: 14px; flex: 1; min-width: 260px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%); display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 3px 10px rgba(109, 40, 217, 0.28);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.31L4.17 19.5A2 2 0 0 0 6 22h12a2 2 0 0 0 1.83-2.5L14 9.31V2"/><line x1="8" y1="2" x2="16" y2="2"/><line x1="6.5" y1="15" x2="17.5" y2="15"/></svg>
                        </div>
                        <div>
                            <div style="display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px;">
                                <b class="mm-text-purple" style="font-size: 1.15rem; font-weight: 800; color: #5B21B6;">{T.get('diagnostic_tests_title', 'Recommended Clinical Diagnostic Tests')}</b>
                            </div>
                            <div style="font-size: 0.80rem; color: var(--mm-text-secondary); margin-top: 3px;">
                                {T.get('diagnostic_tests_sub', 'Share these standard laboratory and diagnostic workup recommendations with your consulting physician.')}
                            </div>
                        </div>
                    </div>
                    <div>
                        <span class="mm-badge" style="background: rgba(124, 58, 237, 0.12); color: #6D28D9; border: 1.2px solid rgba(124, 58, 237, 0.35); border-radius: 999px; padding: 6px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;">
                            {len(tests_list)} {T.get('lab_tests_badge', 'LAB TESTS').upper()}
                        </span>
                    </div>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    {tests_chips_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 8. Nutrition & Clinical Care Guidelines (Foods to Eat / Avoid, Dos & Don'ts)
        col_ns1, col_ns2 = st.columns(2)
        
        # Dietary Data (100% Dynamic from Live AI API)
        raw_eat = care_res.get("foods_to_eat") or care_res.get("dietary_guidelines") or []
        foods_eat = [raw_eat] if isinstance(raw_eat, str) else [str(x) for x in raw_eat if str(x).strip()]
        
        raw_avoid = care_res.get("foods_to_avoid") or []
        foods_avoid = [raw_avoid] if isinstance(raw_avoid, str) else [str(x) for x in raw_avoid if str(x).strip()]
        
        hyd_text = care_res.get("hydration_advice") or ""

        # Clinical Care Data (100% Dynamic from Live AI API)
        raw_dos = care_res.get("clinical_dos") or care_res.get("dos") or []
        clinical_dos = [raw_dos] if isinstance(raw_dos, str) else [str(x) for x in raw_dos if str(x).strip()]
        
        raw_donts = care_res.get("clinical_donts") or care_res.get("donts") or []
        clinical_donts = [raw_donts] if isinstance(raw_donts, str) else [str(x) for x in raw_donts if str(x).strip()]
        
        raw_warn = care_res.get("red_flags") or []
        warning_signs = [raw_warn] if isinstance(raw_warn, str) else [str(x) for x in raw_warn if str(x).strip()]

        with col_ns1:
            eat_items_html = "".join([
                f'<div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 7px;">'
                f'<span style="width: 7px; height: 7px; min-width: 7px; border-radius: 50%; background: #059669; margin-top: 6px; flex-shrink: 0;"></span>'
                f'<span style="font-size: 0.83rem; color: var(--mm-text-primary); line-height: 1.45; font-weight: 500;">{item}</span>'
                f'</div>'
                for item in foods_eat
            ]) if foods_eat else f'<div style="color: var(--mm-text-secondary); font-size: 0.82rem;">{T.get("personalized_diet_text", "Follow personalized light and nutritious diet.")}</div>'

            avoid_items_html = "".join([
                f'<div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 7px;">'
                f'<span style="width: 7px; height: 7px; min-width: 7px; border-radius: 50%; background: #EA580C; margin-top: 6px; flex-shrink: 0;"></span>'
                f'<span style="font-size: 0.83rem; color: var(--mm-text-primary); line-height: 1.45; font-weight: 500;">{item}</span>'
                f'</div>'
                for item in foods_avoid
            ]) if foods_avoid else f'<div style="color: var(--mm-text-secondary); font-size: 0.82rem;">{T.get("avoid_heavy_food_text", "Avoid oily, spicy, and heavily processed food.")}</div>'

            hyd_section = f"""
            <div class="mm-subbox-blue" style="margin-top: 14px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
                    </div>
                    <b class="mm-text-blue" style="font-size: 0.94rem; font-weight: 800; color: #1D4ED8;">{T.get('hydration_advice_title', 'Hydration Advice')}</b>
                </div>
                <div style="font-size: 0.83rem; color: var(--mm-text-primary); margin-top: 8px; line-height: 1.5; font-weight: 500; padding-left: 2px;">
                    {hyd_text}
                </div>
            </div>
            """ if hyd_text else ""

            st.markdown(f"""
            <div class="mm-dietary-card">
                <div>
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: #059669; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 3px 10px rgba(5, 150, 105, 0.28);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
                        </div>
                        <div>
                            <b class="mm-text-green" style="font-size: 1.22rem; font-weight: 800; color: #065F46; display: block; line-height: 1.2;">
                                {T.get('dietary_nutrition_title', 'Dietary Nutrition Guide')}
                            </b>
                            <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px; font-weight: 500;">
                                {T.get("diet_subtitle", "Eat Right • Stay Healthy • Feel Better")}
                            </div>
                        </div>
                    </div>
                    <div class="mm-subbox-green" style="margin-bottom: 14px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: #059669; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2v6a3 3 0 0 1-3 3 3 3 0 0 1-3-3V2"/><path d="M15 11v11"/><path d="M5 2v8a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2V2"/><path d="M7 12v10"/></svg>
                            </div>
                            <div>
                                <b class="mm-text-green" style="font-size: 0.94rem; font-weight: 800; color: #047857; display: block; line-height: 1.2;">
                                    {T.get('foods_to_eat_title', 'Recommended Foods')}
                                </b>
                                <div style="font-size: 0.74rem; color: #059669; margin-top: 1px;">
                                    {T.get("foods_to_eat_sub", "Nutritious choices for better digestion and overall health")}
                                </div>
                            </div>
                        </div>
                        <div style="padding-left: 2px;">
                            {eat_items_html}
                        </div>
                    </div>
                    <div class="mm-subbox-orange" style="margin-bottom: 14px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: #EA580C; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                            </div>
                            <div>
                                <b class="mm-text-orange" style="font-size: 0.94rem; font-weight: 800; color: #C2410C; display: block; line-height: 1.2;">
                                    {T.get('foods_to_avoid_title', 'Foods to Avoid / Limit')}
                                </b>
                                <div style="font-size: 0.74rem; color: #C2410C; margin-top: 1px;">
                                    {T.get("foods_to_avoid_sub", "These can irritate the digestive system")}
                                </div>
                            </div>
                        </div>
                        <div style="padding-left: 2px;">
                            {avoid_items_html}
                        </div>
                    </div>
                </div>
                {hyd_section}
            </div>
            """, unsafe_allow_html=True)

        with col_ns2:
            dos_items_html = "".join([
                f'<div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 7px;">'
                f'<span style="width: 7px; height: 7px; min-width: 7px; border-radius: 50%; background: #2563EB; margin-top: 6px; flex-shrink: 0;"></span>'
                f'<span style="font-size: 0.83rem; color: var(--mm-text-primary); line-height: 1.45; font-weight: 500;">{item}</span>'
                f'</div>'
                for item in clinical_dos
            ]) if clinical_dos else f'<div style="color: var(--mm-text-secondary); font-size: 0.82rem;">{T.get("take_meds_text", "Take prescribed medications on time and take adequate rest.")}</div>'

            donts_items_html = "".join([
                f'<div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 7px;">'
                f'<span style="width: 7px; height: 7px; min-width: 7px; border-radius: 50%; background: #DC2626; margin-top: 6px; flex-shrink: 0;"></span>'
                f'<span style="font-size: 0.83rem; color: var(--mm-text-primary); line-height: 1.45; font-weight: 500;">{item}</span>'
                f'</div>'
                for item in clinical_donts
            ]) if clinical_donts else f'<div style="color: var(--mm-text-secondary); font-size: 0.82rem;">{T.get("dont_exert_text", "Do not alter dosages or perform heavy physical exertion.")}</div>'

            warn_items_html = "".join([
                f'<div style="display: flex; align-items: flex-start; gap: 10px; margin-bottom: 6px;">'
                f'<span style="width: 7px; height: 7px; min-width: 7px; border-radius: 50%; background: #7C3AED; margin-top: 6px; flex-shrink: 0;"></span>'
                f'<span style="font-size: 0.83rem; color: var(--mm-text-primary); line-height: 1.45; font-weight: 500;">{item}</span>'
                f'</div>'
                for item in warning_signs
            ]) if warning_signs else ""

            warn_section = f"""
            <div class="mm-subbox-purple" style="margin-top: 14px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                    <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: #7C3AED; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                    </div>
                    <div>
                        <b class="mm-text-purple" style="font-size: 0.94rem; font-weight: 800; color: #7C3AED; display: block; line-height: 1.2;">
                            {T.get('warning_signs_title', 'Key Warning Signs')}
                        </b>
                        <div style="font-size: 0.74rem; color: #7C3AED; margin-top: 1px;">
                            {T.get("warning_signs_sub", "Seek medical attention if you notice any of these symptoms")}
                        </div>
                    </div>
                </div>
                <div style="padding-left: 2px;">
                    {warn_items_html}
                </div>
            </div>
            """ if warn_items_html else ""

            st.markdown(f"""
            <div class="mm-clinical-care-card">
                <div>
                    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 3px 10px rgba(37, 99, 235, 0.28);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/></svg>
                        </div>
                        <div>
                            <b class="mm-text-blue" style="font-size: 1.22rem; font-weight: 800; color: #1E40AF; display: block; line-height: 1.2;">
                                {T.get('care_safety_title', "Clinical Care Dos & Don'ts")}
                            </b>
                            <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px; font-weight: 500;">
                                {T.get("clinical_care_sub", "Small Steps • Safer Days • Better Living")}
                            </div>
                        </div>
                    </div>
                    <div class="mm-subbox-blue" style="margin-bottom: 14px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: #2563EB; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                            </div>
                            <div>
                                <b class="mm-text-blue" style="font-size: 0.94rem; font-weight: 800; color: #1D4ED8; display: block; line-height: 1.2;">
                                    {T.get('clinical_dos_title', 'Essential Dos')}
                                </b>
                                <div style="font-size: 0.74rem; color: #1D4ED8; margin-top: 1px;">
                                    {T.get("clinical_dos_sub", "Follow these habits for better care and recovery")}
                                </div>
                            </div>
                        </div>
                        <div style="padding-left: 2px;">
                            {dos_items_html}
                        </div>
                    </div>
                    <div class="mm-subbox-red" style="margin-bottom: 14px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <div style="width: 32px; height: 32px; min-width: 32px; border-radius: 50%; background: #DC2626; display: flex; align-items: center; justify-content: center; color: #FFFFFF; flex-shrink: 0;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                            </div>
                            <div>
                                <b class="mm-text-red" style="font-size: 0.94rem; font-weight: 800; color: #DC2626; display: block; line-height: 1.2;">
                                    {T.get('clinical_donts_title', "Critical Don'ts")}
                                </b>
                                <div style="font-size: 0.74rem; color: #DC2626; margin-top: 1px;">
                                    {T.get("clinical_donts_sub", "Avoid these habits to prevent irritation and complications")}
                                </div>
                            </div>
                        </div>
                        <div style="padding-left: 2px;">
                            {donts_items_html}
                        </div>
                    </div>
                </div>
                {warn_section}
            </div>
            """, unsafe_allow_html=True)

        # 8.4. Seasonal Health & Outbreak Intelligence Advisory (Positioned below clinical care)
        seasonal_alert = care_res.get("seasonal_alert", {})
        if seasonal_alert and seasonal_alert.get("is_active"):
            s_season = seasonal_alert.get("season_name", "Seasonal")
            s_state = seasonal_alert.get("state", u_ctx.get("state", "India"))
            s_risk = seasonal_alert.get("risk_level", "MODERATE")
            s_headline = seasonal_alert.get("headline", f"{s_season} Health Advisory")
            s_msg = seasonal_alert.get("message", "")
            s_adv = seasonal_alert.get("advisory", "")
            risk_badge_cls = "mm-badge-critical" if s_risk in ["HIGH", "SEVERE"] else "mm-badge-warning"
            
            s_risk_translated = T.get(f"risk_{s_risk.lower()}", s_risk.upper())
            outbreak_risk_label = T.get("seasonal_outbreak_risk", "OUTBREAK RISK")
            risk_badge_html = f"""<span class="mm-badge" style="background: rgba(239, 68, 68, 0.12); color: #DC2626; border: 1.2px solid rgba(239, 68, 68, 0.35); border-radius: 999px; padding: 6px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;">{s_risk_translated} {outbreak_risk_label}</span>""" if s_risk in ["HIGH", "SEVERE"] else f"""<span class="mm-badge" style="background: rgba(245, 158, 11, 0.12); color: #D97706; border: 1.2px solid rgba(245, 158, 11, 0.35); border-radius: 999px; padding: 6px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;">{s_risk_translated} {outbreak_risk_label}</span>"""
            
            pub_adv_label = T.get("public_health_advisory", "Public Health Advisory")
            season_sub_msg = T.get("seasonal_stay_informed", f"Stay informed. Stay safe during the {s_season.lower()} season.")
            
            st.markdown(f"""
            <div class="mm-seasonal-card">
                <div style="display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                    <div style="display: flex; align-items: flex-start; gap: 14px; flex: 1; min-width: 260px;">
                        <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 50%; background: #FFEDD5; border: 1.5px solid #FDBA74; display: flex; align-items: center; justify-content: center; color: #EA580C; flex-shrink: 0; box-shadow: 0 2px 8px rgba(234, 88, 12, 0.2);">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/><line x1="21" y1="4" x2="23" y2="4"/><line x1="19" y1="2" x2="20.5" y2="3.5"/></svg>
                        </div>
                        <div>
                            <b class="mm-text-orange" style="font-size: 1.15rem; font-weight: 800; color: #EA580C; display: block; line-height: 1.25;">
                                {s_headline}
                            </b>
                            <div style="font-size: 0.80rem; color: var(--mm-text-secondary); margin-top: 3px;">
                                {season_sub_msg}
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                        <span class="mm-badge" style="background: rgba(234, 88, 12, 0.12); color: #EA580C; border: 1.2px solid rgba(234, 88, 12, 0.35); border-radius: 999px; padding: 6px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;">
                            {s_season.upper()} • {s_state.upper()}
                        </span>
                        {risk_badge_html}
                    </div>
                </div>
                <p style="color: var(--mm-text-primary); font-size: 0.86rem; line-height: 1.6; margin: 14px 0 0 0; padding-left: 2px;">
                    {s_msg}
                </p>
                {f'<div style="font-size: 0.80rem; color: var(--mm-text-secondary); background: rgba(0,0,0,0.05); border-radius: 8px; padding: 8px 12px; margin-top: 10px;"><b>{pub_adv_label}:</b> {s_adv}</div>' if s_adv else ''}
            </div>
            """, unsafe_allow_html=True)

        # 8.5. Emergency Red-Flag Alert Banner (Positioned at the bottom before Action Bar)
        if t_res.get("is_emergency") and t_res.get("red_flags"):
            rf_items_html = "".join([f"<li style='margin-bottom: 4px;'><b>{rf.get('symptom_name', 'Critical Symptom')}:</b> {rf.get('immediate_action_protocol', 'Seek prompt emergency medical evaluation.')}</li>" for rf in t_res.get("red_flags", [])])
            st.markdown(f"""
            <div style="background: rgba(220, 38, 38, 0.12); border: 1.5px solid #EF4444; border-left: 5px solid #DC2626; border-radius: 12px; padding: 14px 18px; margin-top: 16px; margin-bottom: 8px;">
                <b style="color: #EF4444; font-size: 0.98rem; display: flex; align-items: center; gap: 8px;">
                    EMERGENCY RED FLAG DETECTED — IMMEDIATE MEDICAL EVALUATION REQUIRED
                </b>
                <ul style="font-size: 0.82rem; color: var(--mm-text-primary); margin: 8px 0 0 0; padding-left: 20px; line-height: 1.55;">
                    {rf_items_html}
                </ul>
            </div>
            """, unsafe_allow_html=True)

        # 9. ACTION BAR: DEEP EXPLAIN, DOWNLOAD REPORT (PDF), SCAN NEW (Positioned right above Medical Disclaimer)
        st.markdown("""
        <style>
        .st-key-mm_triage_actions_bar {
            width: 100% !important;
            margin-top: 14px !important;
            margin-bottom: 8px !important;
        }
        .st-key-mm_triage_actions_bar [data-testid="stHorizontalBlock"] {
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            width: 100% !important;
        }
        .st-key-mm_triage_actions_bar [data-testid="stColumn"] {
            flex: 1 1 0px !important;
            width: 33.333% !important;
            min-width: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .st-key-mm_triage_actions_bar [data-testid="stElementContainer"],
        .st-key-mm_triage_actions_bar [data-testid="stMarkdownContainer"],
        .st-key-mm_triage_actions_bar [data-testid="stMarkdownContainer"] > p,
        .st-key-mm_triage_actions_bar [data-testid="stMarkdownContainer"] > div,
        .st-key-mm_triage_actions_bar .stButton {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            display: block !important;
            line-height: 1 !important;
        }
        .st-key-mm_triage_actions_bar a.btn-download-pdf-direct {
            text-decoration: none !important;
            width: 100% !important;
            display: block !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
        }
        .st-key-mm_triage_actions_bar button {
            width: 100% !important;
            height: 44px !important;
            min-height: 44px !important;
            max-height: 44px !important;
            margin: 0 !important;
            padding: 0 12px !important;
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-sizing: border-box !important;
            line-height: 1.2 !important;
            text-align: center !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            background-color: #2563EB !important;
            border: 1px solid #2563EB !important;
            color: #FFFFFF !important;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25) !important;
            transition: all 0.15s ease !important;
            cursor: pointer !important;
        }
        .st-key-mm_triage_actions_bar button:hover {
            background-color: #1D4ED8 !important;
            border-color: #1D4ED8 !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.38) !important;
            transform: translateY(-1px) !important;
        }
        .st-key-mm_triage_actions_bar button:active {
            transform: translateY(0) scale(0.99) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container(key="mm_triage_actions_bar"):
            col_act1, col_act2, col_act3 = st.columns([1, 1, 1], gap="small", vertical_alignment="center")
            with col_act1:
                if st.button(T.get("deep_explain_btn", "Deep Explain with DocMindX AI"), key="btn_toggle_deep_explain", type="primary", use_container_width=True):
                    st.session_state["floating_chat_open"] = True
                    with st.spinner("Generating clinical deep consultation in AI Assistant..."):
                        deep_text = generate_deep_explanation(
                            symptoms=st.session_state.get("selected_symptoms_list", []),
                            user_context=u_ctx,
                            top_condition=top_disease_name,
                            ranked_conditions=t_res.get("ranked_conditions", []),
                            medicines=care_res.get("medicine_gallery", []),
                            yoga_recs=care_res.get("yoga_recommendations", []),
                            lang=lang_code
                        )
                        st.session_state["floating_chat_history"].append({
                            "role": "assistant",
                            "content": deep_text
                        })
                        st.rerun()

            with col_act2:
                try:
                    pdf_user_ctx = {
                        "age": u_ctx.get("age", u_ctx.get("age_group", "21-30 Years")),
                        "gender": u_ctx.get("gender", "Male"),
                        "state": u_ctx.get("state") or u_ctx.get("location", "India"),
                        "location": u_ctx.get("state") or u_ctx.get("location", "India"),
                        "height": u_ctx.get("height", "None"),
                        "weight": u_ctx.get("weight", "None"),
                        "duration": u_ctx.get("duration", "1-3 Days"),
                        "severity": u_ctx.get("severity", "Moderate"),
                        "blood_group": u_ctx.get("blood_group", "None"),
                        "pre_existing": ", ".join(u_ctx.get("conditions", ["None"])) if isinstance(u_ctx.get("conditions"), list) else str(u_ctx.get("conditions", "None")),
                        "current_meds": u_ctx.get("medications", u_ctx.get("current_meds", "None")),
                        "allergies": u_ctx.get("allergies", "None"),
                        "surgeries": u_ctx.get("surgeries", "None"),
                        "family_history": u_ctx.get("surgeries", "None"),
                        "symptoms": st.session_state.get("selected_symptoms_list", [])
                    }
                    pdf_data = generate_pdf_report(pdf_user_ctx, t_res, care_res)
                    pdf_filename = f"DocMindX_AI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    b64_pdf = base64.b64encode(pdf_data.getvalue()).decode()
                    btn_label = T.get("download_report_btn", "Download Clinical Report (PDF)")
                    st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}" class="btn-download-pdf-direct" style="text-decoration:none!important;width:100%!important;display:block!important;margin:0;padding:0;"><button type="button" style="width:100%!important;margin:0;">{btn_label}</button></a>', unsafe_allow_html=True)
                except Exception as e:
                    st.button(T.get("download_report_btn", "Download Clinical Report (PDF)"), key="btn_download_disabled", disabled=True, use_container_width=True)

            with col_act3:
                if st.button(T.get("scan_new_btn", "Scan New Assessment"), key="btn_scan_new_triage", type="primary", use_container_width=True):
                    st.session_state["assessment_completed"] = False
                    st.session_state["assessment_step"] = 1
                    st.session_state["p1_triage_results"] = None
                    st.session_state["triage_result"] = None
                    st.session_state["care_recommendations"] = None
                    st.session_state["selected_symptoms_list"] = []
                    st.session_state["detected_chief_condition"] = None
                    st.session_state["show_free_text_nlp"] = False
                    st.session_state["triage_qa_history"] = []
                    st.session_state["floating_chat_open"] = False
                    if "user_context" in st.session_state and isinstance(st.session_state["user_context"], dict):
                        st.session_state["user_context"]["symptoms"] = []
                    st.rerun()

        # 10. Clinical Advisory & Medical Disclaimer
        st.markdown(f"""
        <div class="mm-clinical-advisory-banner"style="background: rgba(234, 88, 12, 0.08); border: 1.2px solid rgba(234, 88, 12, 0.35); border-left: 5px solid #EA580C; border-radius: 10px; padding: 12px 16px; margin-top: 14px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span style="font-size: 1.1rem;"></span>
                <b style="color: #FB923C; font-size: 0.88rem; letter-spacing: 0.02em; text-transform: uppercase;">{T.get("sidebar_warning_title", "Clinical Advisory")}</b>
            </div>
            <p style="margin: 0; font-size: 0.82rem; color: var(--mm-text-primary); line-height: 1.5;">
                {T.get("sidebar_warning_desc", "DocMindX AI can make mistakes. Do not rely solely on AI suggestions — always consult a certified doctor or licensed physician for clinical decisions.")}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)

# ==============================================================================
# MODULE 2: CLINICAL REPORT & PRESCRIPTION ANALYZER
# ==============================================================================
elif st.session_state["active_panel"] == "Medical Report":
    report_icon_html = '<div style="width: 52px; height: 52px; border-radius: 14px; background: rgba(37, 99, 235, 0.08); border: 1.5px solid #2563EB; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); flex-shrink: 0;"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M12 7v4"/><path d="M10 9h4"/></svg></div>'
    with st.container(key="mm_top_header_card_2"):
        hdr2_c1, hdr2_c2, hdr2_c3, hdr2_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr2_c1:
            title_p2 = T.get("p2_header_title", "Medical Report & Prescription Analyzer")
            sub_p2 = T.get("p2_header_subtitle", "Automated laboratory reference interval comparison, layman explanations, and prescription guidance.")
            safe_markdown(
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{report_icon_html}'
                f'<div style="min-width: 0; flex: 1;">'
                f'<div style="margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">{title_p2}</div>'
                f'<div style="margin-top: 4px; font-size: 0.85rem; color: var(--mm-text-secondary); line-height: 1.35;">{sub_p2}</div>'
                f'</div>'
                f'</div>'
            )
        with hdr2_c2:
            safe_markdown(
                f'<div style="display: flex; justify-content: center; align-items: center; height: 38px;">'
                f'<span style="height: 36px; padding: 0 16px; border-radius: 20px; background: #E0F2FE; border: 1px solid #BAE6FD; color: #0284C7; font-weight: 700; font-size: 0.80rem; display: inline-flex; align-items: center; gap: 6px;">'
                f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
                f'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                f'<polyline points="14 2 14 8 20 8"/>'
                f'</svg>'
                f'OCR + CLINICAL AI'
                f'</span>'
                f'</div>'
            )
        with hdr2_c3:
            header_lang_2 = st.selectbox(
                "Header Lang Selector 2",
                options=LANG_OPTIONS,
                key="hdr_lang_p2",
                label_visibility="collapsed",
                on_change=sync_language,
                args=("hdr_lang_p2",)
            )
        with hdr2_c4:
            new_theme_p2 = theme_toggle_switch(is_dark=st.session_state.get("dark_mode", False), key="hdr_sun_moon_p2")
            if new_theme_p2 != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = new_theme_p2
                st.rerun()

    if "p2_step" not in st.session_state:
        st.session_state["p2_step"] = 1

    p2_cur_step = st.session_state.get("p2_step", 1)

    s1_cls = "done" if p2_cur_step > 1 else "active"
    s2_cls = "active" if p2_cur_step == 2 else ("done" if p2_cur_step > 2 else "")
    s3_cls = "active" if p2_cur_step == 3 else ""
    st.markdown(f"""
    <div class="mm-stepper">
        <div class="mm-step-item">
            <div class="mm-step-num {s1_cls}">1</div>
            <div>
                <div class="mm-step-text-title {'active'if p2_cur_step == 1 else ''}">{T.get("p2_step1_title", "Upload & Profile")}</div>
                <div class="mm-step-text-sub">{T.get("p2_step1_sub", "Upload documents & info")}</div>
            </div>
        </div>
        <div class="mm-step-arrow">→</div>
        <div class="mm-step-item">
            <div class="mm-step-num {s2_cls}">2</div>
            <div>
                <div class="mm-step-text-title {'active'if p2_cur_step == 2 else ''}">{T.get("p2_step2_title", "Analysis")}</div>
                <div class="mm-step-text-sub">{T.get("p2_step2_sub", "AI processing & comparison")}</div>
            </div>
        </div>
        <div class="mm-step-arrow">→</div>
        <div class="mm-step-item">
            <div class="mm-step-num {s3_cls}">3</div>
            <div>
                <div class="mm-step-text-title {'active'if p2_cur_step == 3 else ''}">{T.get("p2_step3_title", "Results")}</div>
                <div class="mm-step-text-sub">{T.get("p2_step3_sub", "Insights & guidance")}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Patient Profile / Family Member Selection for Authenticated Sessions
    curr_auth_user = auth_ui.get_current_user()
    if curr_auth_user and auth_ui.is_authenticated():
        p2_patient_ctx = family_ui.render_scan_patient_selector(curr_auth_user, key_prefix="p2_scan_selector")
        st.session_state["p2_patient_context"] = p2_patient_ctx
    else:
        st.session_state["p2_patient_context"] = {"mode": "GENERAL", "member_id": None, "name": "General Patient"}

    # ----------------- STEP 1 & 2: UPLOAD & OCR EXTRACTION -----------------
    if p2_cur_step < 3:
        st.markdown("""
        <style>
        /* Force equal height on Medical Report columns & cards in both light & dark mode */
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card),
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]),
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_ocr_card),
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_ocr_card"]) {
            align-items: stretch !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"] {
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
            height: 100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) [data-testid="stLayoutWrapper"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) [data-testid="stLayoutWrapper"] {
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
            height: 100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.st-key-med_report_upload_card) [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-med_report_upload_card"]) [data-testid="stVerticalBlockBorderWrapper"] {
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
            height: 100% !important;
        }
        .st-key-med_report_upload_card,
        .st-key-med_report_ocr_card,
        div[class*="st-key-med_report_upload_card"],
        div[class*="st-key-med_report_ocr_card"] {
            height: 100% !important;
            min-height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
            box-sizing: border-box !important;
            border-radius: 14px !important;
        }
        .st-key-med_report_upload_card > div[data-testid="stVerticalBlock"],
        .st-key-med_report_ocr_card > div[data-testid="stVerticalBlock"],
        div[class*="st-key-med_report_upload_card"] > div[data-testid="stVerticalBlock"],
        div[class*="st-key-med_report_ocr_card"] > div[data-testid="stVerticalBlock"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
        }
        .st-key-med_report_upload_card .stButton,
        div[class*="st-key-med_report_upload_card"] .stButton {
            margin-top: auto !important;
            padding-top: 10px !important;
        }
        .st-key-med_report_ocr_card [data-testid="stTextArea"],
        div[class*="st-key-med_report_ocr_card"] [data-testid="stTextArea"],
        .st-key-med_report_ocr_card .stTextArea,
        div[class*="st-key-med_report_ocr_card"] .stTextArea {
            flex: 1 1 auto !important;
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
            margin-bottom: 0 !important;
        }
        .st-key-med_report_ocr_card [data-testid="stTextArea"] > div,
        div[class*="st-key-med_report_ocr_card"] [data-testid="stTextArea"] > div {
            flex: 1 1 auto !important;
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
        }
        .st-key-med_report_ocr_card textarea,
        div[class*="st-key-med_report_ocr_card"] textarea {
            flex: 1 1 auto !important;
            height: 100% !important;
            min-height: 180px !important;
            box-sizing: border-box !important;
            resize: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        col_p2_1, col_p2_2 = st.columns([1, 1], gap="medium")

        with col_p2_1:
            with st.container(key="med_report_upload_card", border=True):
                safe_markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <div style="width: 40px; height: 40px; border-radius: 12px; background: rgba(37, 99, 235, 0.1); display: flex; align-items: center; justify-content: center;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                            <line x1="16" y1="13" x2="8" y2="13"/>
                            <line x1="16" y1="17" x2="8" y2="17"/>
                        </svg>
                    </div>
                    <div>
                        <b style="font-size: 1.0rem; color: var(--mm-text-primary); display: block;">{T.get("p2_doc_upload_title", "Document Upload & Patient Profile")}</b>
                        <span style="font-size: 0.80rem; color: var(--mm-text-secondary);">{T.get("p2_doc_upload_sub", "Select document type and provide basic information.")}</span>
                    </div>
                </div>
                <div style="font-size: 0.82rem; font-weight: 700; color: var(--mm-text-primary); margin-bottom: 6px;">{T.get("p2_select_doc_type", "Select Document Type")}</div>
                """)

                doc_type_choice = st.radio(
                    "Select Document Type",
                    [
                        T.get("doc_type_lab", "Blood / Pathology Lab Report"),
                        T.get("doc_type_presc", "Doctor Prescription"),
                        T.get("doc_type_imaging", "Diagnostic Imaging / Radiology Report"),
                        T.get("doc_type_other", "Other Medical Document")
                    ],
                    horizontal=True,
                    label_visibility="collapsed"
                )

                uploaded_doc = st.file_uploader(
                    "Upload or Drag and Drop Medical Document",
                    type=["pdf", "png", "jpg", "jpeg"],
                    key="p2_doc_uploader",
                    help="Supports PDF, PNG, JPG, JPEG (Max 200MB)"
                )

                if uploaded_doc and st.session_state.get("p2_step", 1) == 1:
                    st.session_state["p2_step"] = 2

                d_col1, d_col2 = st.columns(2)
                with d_col1:
                    age_for_report = st.selectbox(f"{T.get('label_age_group', 'Age Group')}", ["Adult", "Senior (60+)", "Pediatric (0-18)"], index=0)
                with d_col2:
                    gender_for_report = st.selectbox(f"{T.get('label_gender', 'Biological Gender')}", ["Male", "Female", "Other"], index=0)

                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                analyze_doc_btn = st.button(T.get("btn_analyze_doc", "Analyze Medical Document"), type="primary", use_container_width=True)

        with col_p2_2:
            with st.container(key="med_report_ocr_card", border=True):
                safe_markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 40px; height: 40px; border-radius: 12px; background: rgba(16, 185, 129, 0.1); display: flex; align-items: center; justify-content: center;">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14 2 14 8 20 8"/>
                                <line x1="16" y1="13" x2="8" y2="13"/>
                                <line x1="16" y1="17" x2="8" y2="17"/>
                            </svg>
                        </div>
                        <div>
                            <b style="font-size: 1.0rem; color: var(--mm-text-primary); display: block;">{T.get("p2_ocr_title", "OCR Text Stream & Extraction")}</b>
                            <span style="font-size: 0.80rem; color: var(--mm-text-secondary);">{T.get("p2_ocr_sub", "Upload your file above or review the extracted clinical text stream below.")}</span>
                        </div>
                    </div>
                    <span style="background: {'rgba(16, 185, 129, 0.12)' if uploaded_doc else 'rgba(16, 185, 129, 0.08)'}; border: 1px solid {'rgba(16, 185, 129, 0.4)' if uploaded_doc else 'rgba(16, 185, 129, 0.25)'}; color: #059669; font-weight: 700; font-size: 0.72rem; padding: 4px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">
                        <span style="width: 7px; height: 7px; border-radius: 50%; background: #10B981; display: inline-block;"></span>
                        {'DOCUMENT LOADED' if uploaded_doc else 'AWAITING FILE'}
                    </span>
                </div>
                <div style="font-size: 0.78rem; color: #1D4ED8; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 8px 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <span>{T.get("p2_ocr_tip", "Upload a medical document (PDF or Image) to extract clinical text using OCR. (Read-Only Copyable)")}</span>
                </div>
                """)

                if uploaded_doc:
                    doc_cache_key = f"{uploaded_doc.name}_{uploaded_doc.size}"
                    cached_text = st.session_state.get("p2_cached_doc_text", "")
                    if st.session_state.get("p2_cached_doc_key") != doc_cache_key or not cached_text:
                        with st.spinner("Extracting clinical text with DocMindX AI Vision OCR..."):
                            raw_extracted = extract_text_from_file(uploaded_doc)
                        st.session_state["p2_cached_doc_key"] = doc_cache_key
                        st.session_state["p2_cached_doc_text"] = raw_extracted
                    else:
                        raw_extracted = cached_text

                    if raw_extracted and raw_extracted.strip():
                        doc_text_stream = st.text_area(
                            "Extracted OCR Text Stream",
                            value=raw_extracted,
                            height=195,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    else:
                        doc_text_stream = ""
                        safe_markdown("""
                        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px; margin-top: 4px; min-height: 100px; display: flex; flex-direction: column; justify-content: center; text-align: center; align-items: center;">
                            <b style="color: #EF4444; font-size: 0.95rem; margin-bottom: 8px; display: flex; align-items: center; justify-content: center; gap: 6px;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                                No Valid Medical Text Detected
                            </b>
                            <span style="font-size: 0.84rem; color: var(--mm-text-secondary); line-height: 1.5; max-width: 480px; margin: 0 auto;">
                                The uploaded file could not be read or does not contain readable clinical test parameters, doctor prescriptions, or radiology findings.<br/>
                                Please upload a clear photo or PDF of an actual medical report, doctor prescription, or radiology document.
                            </span>
                        </div>
                        """)
                else:
                    doc_text_stream = ""
                    st.text_area(
                        "Extracted OCR Text Stream",
                        value="",
                        placeholder="No document uploaded yet. Please upload a PDF or Image on the left to scan real medical parameters...",
                        height=195,
                        disabled=True,
                        label_visibility="collapsed"
                    )

        # Side-by-side Live Document Preview Card (Rendered if file is uploaded)
        if uploaded_doc:
            st.markdown(f"""
            <div class="mm-card"style="margin-top: 4px; border: 1.5px solid #3B82F6;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <b style="font-size: 0.95rem; color: var(--mm-text-primary);"> {T.get('doc_preview_title', 'Live Uploaded Document Preview')} — {uploaded_doc.name}</b>
                    <span class="mm-badge mm-badge-info">{round(uploaded_doc.size / 1024, 1)} KB</span>
                </div>
            """, unsafe_allow_html=True)
            
            file_ext = uploaded_doc.name.lower()
            if file_ext.endswith((".png", ".jpg", ".jpeg")):
                st.image(uploaded_doc, caption=uploaded_doc.name, use_container_width=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.08); border-radius: 8px; padding: 14px; text-align: center; color: var(--mm-text-primary);">
                    <b>PDF Document Preview:</b> {uploaded_doc.name}<br/>
                    <span style="font-size: 0.78rem; color: var(--mm-text-secondary);">Native PDF text stream processed by DocMindX OCR Engine.</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # BioPortal Clinical Ontology Lookup (Contained in clean expandable drawer)
        with st.expander(" " + T.get("p2_bioportal_title", "BioPortal Clinical Ontology Lookup"), expanded=False):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="width: 38px; height: 38px; border-radius: 10px; background: rgba(139, 92, 246, 0.1); display: flex; align-items: center; justify-content: center;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <ellipse cx="12" cy="5" rx="9" ry="3"/>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                    </svg>
                </div>
                <div>
                    <b style="font-size: 1.0rem; color: var(--mm-text-primary); display: block;">{T.get("p2_bioportal_title", "BioPortal Clinical Ontology Lookup")}</b>
                    <span style="font-size: 0.80rem; color: var(--mm-text-secondary);">{T.get("p2_bioportal_sub", "Search clinical concepts in SNOMED-CT, LOINC, MeSH, and MedDRA:")}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if "bioportal_query" not in st.session_state:
                st.session_state["bioportal_query"] = ""

            bp_c1, bp_c2 = st.columns([3.5, 1.2])
            with bp_c1:
                bioportal_input = st.text_input(
                    "BioPortal Search Input",
                    value=st.session_state.get("bioportal_query", ""),
                    placeholder="e.g. Hypertension, Serum Creatinine, Metformin, Diabetes",
                    key="bp_search_text_input",
                    label_visibility="collapsed"
                )
            with bp_c2:
                search_bp_btn = st.button(T.get("btn_search_bioportal", "Search Ontology"), key="btn_run_bioportal_search", type="primary", use_container_width=True)

            # Quick Search Suggestion Chips
            st.markdown("<div style='display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 6px 0 10px 0;'><span style='font-size: 0.76rem; color: var(--mm-text-secondary); font-weight: 600;'>Quick Search:</span>", unsafe_allow_html=True)
            chip_cols = st.columns(6)
            quick_terms = ["Hypertension", "Diabetes", "Creatinine", "Metformin", "Paracetamol", "Pneumonia"]
            for q_idx, term in enumerate(quick_terms):
                with chip_cols[q_idx]:
                    if st.button(term, key=f"bp_chip_{term.lower()}", use_container_width=True):
                        st.session_state["bioportal_query"] = term
                        st.session_state["bp_active_search"] = term
                        st.rerun()

            st.markdown("""
            <div class="mm-ontology-grid" style="margin-top: 10px; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">
                <div class="mm-ontology-pill" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: var(--mm-bg-surface, #FFFFFF); border: 1.5px solid var(--mm-brand-border, #E2E8F0); border-radius: 10px;">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(37, 99, 235, 0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <ellipse cx="12" cy="5" rx="9" ry="3"/>
                            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                        </svg>
                    </div>
                    <div>
                        <b style="color: var(--mm-text-primary); display: block; font-size: 0.84rem;">SNOMED-CT</b>
                        <span style="font-size: 0.72rem; color: var(--mm-text-secondary);">Clinical terminology standards</span>
                    </div>
                </div>
                <div class="mm-ontology-pill" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: var(--mm-bg-surface, #FFFFFF); border: 1.5px solid var(--mm-brand-border, #E2E8F0); border-radius: 10px;">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(14, 165, 233, 0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
                            <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
                            <line x1="9" y1="12" x2="15" y2="12"/>
                            <line x1="9" y1="16" x2="13" y2="16"/>
                        </svg>
                    </div>
                    <div>
                        <b style="color: var(--mm-text-primary); display: block; font-size: 0.84rem;">LOINC</b>
                        <span style="font-size: 0.72rem; color: var(--mm-text-secondary);">Lab & clinical observations</span>
                    </div>
                </div>
                <div class="mm-ontology-pill" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: var(--mm-bg-surface, #FFFFFF); border: 1.5px solid var(--mm-brand-border, #E2E8F0); border-radius: 10px;">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(16, 185, 129, 0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                        </svg>
                    </div>
                    <div>
                        <b style="color: var(--mm-text-primary); display: block; font-size: 0.84rem;">MeSH</b>
                        <span style="font-size: 0.72rem; color: var(--mm-text-secondary);">Medical subject headings</span>
                    </div>
                </div>
                <div class="mm-ontology-pill" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: var(--mm-bg-surface, #FFFFFF); border: 1.5px solid var(--mm-brand-border, #E2E8F0); border-radius: 10px;">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(139, 92, 246, 0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/>
                            <path d="m8.5 8.5 7 7"/>
                        </svg>
                    </div>
                    <div>
                        <b style="color: var(--mm-text-primary); display: block; font-size: 0.84rem;">RxNorm / MedDRA</b>
                        <span style="font-size: 0.72rem; color: var(--mm-text-secondary);">Clinical drug formulations</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            active_bp_query = bioportal_input.strip() if (search_bp_btn and bioportal_input.strip()) else st.session_state.get("bp_active_search", "")

            if active_bp_query:
                with st.spinner(f"Querying biomedical ontology knowledgebase for '{active_bp_query}'..."):
                    bp_results = search_bioportal_concept(active_bp_query)
                    if bp_results:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; justify-content: space-between; margin: 14px 0 8px 0;">
                            <b style="font-size: 0.90rem; color: var(--mm-text-primary);">Ontology Results for "{active_bp_query}"</b>
                            <span class="mm-badge mm-badge-success">{len(bp_results)} Standard Concepts</span>
                        </div>
                        """, unsafe_allow_html=True)
                        for c in bp_results:
                            c_label = c.get("pref_label") or c.get("prefLabel") or active_bp_query
                            c_ont = c.get("ontology", "Ontology Standard")
                            c_id = c.get("concept_id") or c.get("id", "")
                            c_def = c.get("definition", "Verified medical terminology mapping.")
                            c_cui = c.get("cui", "")
                            c_syns = c.get("synonyms", [])

                            syn_badges = "".join([f"<span class='mm-badge mm-badge-neutral' style='font-size: 0.68rem; margin-right: 4px; padding: 2px 6px;'>{s}</span>" for s in c_syns])
                            cui_html = f"<span class='mm-badge mm-badge-info' style='font-size: 0.68rem; padding: 2px 7px;'>UMLS CUI: {c_cui}</span>" if c_cui else ""
                            def_html = f'<p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 6px 0; line-height: 1.45;">{c_def}</p>' if c_def else ''
                            syn_html = f'<div style="margin-top: 6px; display: flex; align-items: center; flex-wrap: wrap; gap: 4px;"><span style="font-size: 0.70rem; color: var(--mm-text-muted); font-weight: 600;">Synonyms:</span> {syn_badges}</div>' if syn_badges else ''
                            id_html = f'<div style="font-size: 0.70rem; color: var(--mm-text-muted); margin-top: 6px; font-family: monospace; word-break: break-all;">ID: {c_id}</div>' if c_id else ''
                            card_html = (
                                f'<div class="mm-card" style="padding: 14px 16px; margin-bottom: 8px; border-left: 3.5px solid #2563EB;">'
                                f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">'
                                f'<b style="font-size: 0.92rem; color: var(--mm-text-primary);">{c_label}</b>'
                                f'<div style="display: flex; align-items: center; gap: 6px;">{cui_html}<span class="mm-badge mm-badge-brand" style="font-size: 0.70rem; padding: 2px 8px;">{c_ont}</span></div>'
                                f'</div>'
                                f'{def_html}'
                                f'{syn_html}'
                                f'{id_html}'
                                f'</div>'
                            )
                            st.markdown(card_html, unsafe_allow_html=True)
                    else:
                        st.info(f"No direct ontology mapping found for '{active_bp_query}'. Try searching for generic condition or medication names.")

        # Trigger Analysis & Transition to Step 3
        if analyze_doc_btn:
            if not uploaded_doc:
                st.error(f" {T.get('err_no_doc_uploaded', 'Please upload a medical report or prescription document (PDF or Image) before clicking Analyze.')}")
            else:
                if not doc_text_stream or not doc_text_stream.strip():
                    with st.spinner("Extracting clinical text with DocMindX AI Vision OCR..."):
                        doc_text_stream = extract_text_from_file(uploaded_doc)
                        st.session_state["p2_cached_doc_text"] = doc_text_stream

                if not doc_text_stream or not doc_text_stream.strip():
                    st.warning("No valid medical test parameters or prescription text were found in the uploaded file. Please upload a clear photo or PDF of an actual medical report or doctor prescription.")
                else:
                    st.session_state["p2_step"] = 3
                    st.session_state["p2_doc_type_choice"] = doc_type_choice
                    st.session_state["p2_doc_text_stream"] = doc_text_stream
                    st.session_state["p2_doc_name"] = uploaded_doc.name if uploaded_doc else "Medical Document"
                    st.session_state["p2_age"] = age_for_report
                    st.session_state["p2_gender"] = gender_for_report
                    st.session_state["p2_deep_ai_chat"] = []
                    st.rerun()


    # ----------------- STEP 3: RESULTS & DIAGNOSTIC EVALUATION -----------------
    elif p2_cur_step == 3:
        doc_text_stream = st.session_state.get("p2_doc_text_stream", "")
        doc_type_choice = st.session_state.get("p2_doc_type_choice", "Blood / Pathology Lab Report")
        age_for_report = st.session_state.get("p2_age", "Adult")
        gender_for_report = st.session_state.get("p2_gender", "Male")
        doc_name = st.session_state.get("p2_doc_name", "Medical Document")

        is_prescription = "Prescription" in str(doc_type_choice) or "पर्ची" in str(doc_type_choice) or "પ્રિસ્ક્રિપ્શન" in str(doc_type_choice) or "Presc" in str(doc_type_choice)
        is_imaging = "Imaging" in str(doc_type_choice) or "Radiology" in str(doc_type_choice) or "रेडियोलॉजी" in str(doc_type_choice) or "इमेजिंग" in str(doc_type_choice) or "રેડિયોલોજી" in str(doc_type_choice) or "ઇમેજિંગ" in str(doc_type_choice)

        if is_prescription:
            presc_res = prescription_analyzer.parse_prescription_text(doc_text_stream)
            total_meds = presc_res.get("total_medicines_identified", 0)
            if total_meds == 0:
                st.markdown(f"""
                <div class="mm-card" style="border-left: 4px solid #F59E0B; background: rgba(245, 158, 11, 0.05); padding: 18px; margin-top: 10px;">
                    <h4 style="color: #F59E0B; margin: 0 0 6px 0; font-size: 1.05rem;"> No Prescription Medications Detected</h4>
                    <p style="margin: 0; font-size: 0.90rem; color: var(--mm-text-secondary);">
                        {presc_res.get("summary", "The uploaded document does not contain recognizable doctor-prescribed medications or dosage instructions. Please ensure you upload a valid medical prescription (PDF or Image).")}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Automatic Clinical AI Patient Guide for Prescriptions
                rx_cache_key = f"p2_breakdown_{doc_name}_{lang_code}"
                if rx_cache_key not in st.session_state:
                    with st.spinner("Generating Comprehensive Clinical AI Guide & Medication Safety Plan..."):
                        rx_breakdown = generate_medical_report_comprehensive_breakdown(
                            report_type="Doctor Prescription",
                            doc_text=doc_text_stream,
                            findings=presc_res.get("medicines", []),
                            age_group=age_for_report,
                            gender=gender_for_report,
                            lang=lang_code
                        )
                        st.session_state[rx_cache_key] = rx_breakdown
                else:
                    rx_breakdown = st.session_state[rx_cache_key]

                warn_count = sum(1 for m in presc_res.get("medicines", []) if "warning" in m.get("info", {}).get("warnings", "").lower() or "caution" in m.get("info", {}).get("warnings", "").lower())
                kpi_data = {
                    "card1": {
                        "label": "TOTAL MEDICINES IDENTIFIED",
                        "val": total_meds,
                        "sub": "From Doctor Prescription"
                    },
                    "card2": {
                        "label": "SAFETY PRECAUTIONS NOTED",
                        "val": warn_count,
                        "sub": f"↑ {warn_count}" if warn_count > 0 else "↓ 0"
                    },
                    "card3": {
                        "label": "OVERALL CLINICAL STATUS",
                        "val": "Verified Regimen" if warn_count == 0 else "Review Precautions",
                        "sub": "Prescription Regimen Ready"
                    }
                }

                render_diagnostic_evaluation_view(
                    doc_name=doc_name,
                    doc_type_choice=doc_type_choice,
                    age_for_report=age_for_report,
                    gender_for_report=gender_for_report,
                    findings=presc_res.get("medicines", []),
                    breakdown_text=rx_breakdown,
                    kpi_data=kpi_data,
                    report_category="prescription",
                    T=T,
                    lang_code=lang_code
                )

                # Auto-persist complete Prescription record
                curr_auth_user = auth_ui.get_current_user()
                p2_ctx = st.session_state.get("p2_patient_context") or {}
                p_mode = p2_ctx.get("mode", "GENERAL") if curr_auth_user else "GENERAL"
                p_mem_id = p2_ctx.get("member_id") if p_mode == "FAMILY_MEMBER" else None
                p_name = p2_ctx.get("name") or (curr_auth_user.get("full_name") if curr_auth_user else "General Patient")

                rx_save_key = f"p2_saved_rx_{doc_name}_{p_mode}_{p_mem_id}"
                if rx_save_key not in st.session_state:
                    full_rx_record = {
                        "scan_type": "Prescription",
                        "scan_mode": p_mode,
                        "result_reference": doc_name,
                        "summary": f"{total_meds} Medicines Identified ({'Regimen Verified' if warn_count == 0 else 'Review Precautions'})",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "patient_name": p_name,
                        "family_member_name": p_name if p_mode == "FAMILY_MEMBER" else None,
                        "patient_context": p2_ctx,
                        "doc_name": doc_name,
                        "medicines": presc_res.get("medicines", []),
                        "total_medicines": total_meds,
                        "warning_count": warn_count,
                        "breakdown": rx_breakdown,
                        "kpi_data": kpi_data,
                        "extracted_text": doc_text_stream,
                        "user_inputs": {
                            "age": age_for_report,
                            "gender": gender_for_report,
                            "doc_type": doc_type_choice
                        }
                    }
                    if curr_auth_user:
                        try:
                            auth_db.save_medical_scan(
                                user_id=curr_auth_user["id"],
                                family_member_id=p_mem_id,
                                scan_type="Prescription",
                                scan_mode=p_mode,
                                result_reference=doc_name,
                                summary=f"{total_meds} Prescribed Medicines — Regimen Verified",
                                details=full_rx_record
                            )
                        except Exception as save_err:
                            print(f"Notice auto-saving prescription scan: {save_err}")
                    st.session_state["current_session_scan"] = full_rx_record
                    if "session_scans" not in st.session_state:
                        st.session_state["session_scans"] = []
                    if not any(s.get("result_reference") == doc_name and s.get("created_at") == full_rx_record["created_at"] for s in st.session_state["session_scans"]):
                        st.session_state["session_scans"].insert(0, full_rx_record)
                    st.session_state[rx_save_key] = True

        elif is_imaging:
            with st.spinner("Analyzing radiological findings, imaging impressions, and anatomical structures..."):
                rad_res = radiology_analyzer.analyze_imaging_report(doc_text_stream, user_lang=lang_code)

            total_findings = rad_res.get("total_findings", 0)
            if total_findings == 0 or not rad_res.get("is_valid_radiology_report", True):
                st.markdown(f"""
                <div class="mm-card" style="border-left: 4px solid #F59E0B; background: rgba(245, 158, 11, 0.05); padding: 18px; margin-top: 10px;">
                    <h4 style="color: #F59E0B; margin: 0 0 6px 0; font-size: 1.05rem;"> No Radiology / Diagnostic Imaging Findings Detected</h4>
                    <p style="margin: 0; font-size: 0.92rem; color: var(--mm-text-secondary);">
                        {rad_res.get("summary", "The uploaded document does not contain recognizable diagnostic imaging or radiology impressions (such as X-Ray, CT Scan, MRI, Ultrasound, etc.). Please upload a valid medical radiology report.")}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Log analysis to SQLite database
                try:
                    log_report_analysis(
                        report_name=doc_name,
                        report_type="Radiology Analysis",
                        extracted_text=doc_text_stream,
                        summary=rad_res.get("summary", f"Detected {total_findings} radiological findings."),
                        findings=rad_res.get("findings", []),
                        abnormal_count=total_findings
                    )
                except Exception as e:
                    print(f"Notice logging radiology report: {e}")

                rad_cache_key = f"p2_breakdown_{doc_name}_{lang_code}"
                if rad_cache_key not in st.session_state:
                    with st.spinner("Generating Comprehensive Clinical AI Radiology Interpretation..."):
                        rad_breakdown = generate_medical_report_comprehensive_breakdown(
                            report_type="Diagnostic Imaging / Radiology Report",
                            doc_text=doc_text_stream,
                            findings=rad_res.get("findings", []),
                            age_group=age_for_report,
                            gender=gender_for_report,
                            lang=lang_code
                        )
                        st.session_state[rad_cache_key] = rad_breakdown
                else:
                    rad_breakdown = st.session_state[rad_cache_key]

                sev_status = rad_res.get("overall_severity", "Normal")
                acute_count = sum(1 for f in rad_res.get("findings", []) if f.get("severity") in ["High", "Emergency", "Medium"])
                kpi_data = {
                    "card1": {
                        "label": "TOTAL IMAGING FINDINGS",
                        "val": total_findings,
                        "sub": "From Radiology Scan"
                    },
                    "card2": {
                        "label": "ABNORMAL / ACUTE FLAGS",
                        "val": acute_count,
                        "sub": f"↑ {acute_count}" if acute_count > 0 else "↓ 0"
                    },
                    "card3": {
                        "label": "OVERALL CLINICAL STATUS",
                        "val": sev_status,
                        "sub": "Diagnostic Impression"
                    }
                }

                render_diagnostic_evaluation_view(
                    doc_name=doc_name,
                    doc_type_choice=doc_type_choice,
                    age_for_report=age_for_report,
                    gender_for_report=gender_for_report,
                    findings=rad_res.get("findings", []),
                    breakdown_text=rad_breakdown,
                    kpi_data=kpi_data,
                    report_category="radiology",
                    T=T,
                    lang_code=lang_code
                )

                # Auto-persist complete Radiology record
                curr_auth_user = auth_ui.get_current_user()
                p2_ctx = st.session_state.get("p2_patient_context") or {}
                p_mode = p2_ctx.get("mode", "GENERAL") if curr_auth_user else "GENERAL"
                p_mem_id = p2_ctx.get("member_id") if p_mode == "FAMILY_MEMBER" else None
                p_name = p2_ctx.get("name") or (curr_auth_user.get("full_name") if curr_auth_user else "General Patient")

                rad_save_key = f"p2_saved_rad_{doc_name}_{p_mode}_{p_mem_id}"
                if rad_save_key not in st.session_state:
                    full_rad_record = {
                        "scan_type": "Radiology",
                        "scan_mode": p_mode,
                        "result_reference": doc_name,
                        "summary": f"{sev_status} ({total_findings} findings, {acute_count} acute)",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "patient_name": p_name,
                        "family_member_name": p_name if p_mode == "FAMILY_MEMBER" else None,
                        "patient_context": p2_ctx,
                        "doc_name": doc_name,
                        "findings": rad_res.get("findings", []),
                        "total_findings": total_findings,
                        "acute_count": acute_count,
                        "overall_severity": sev_status,
                        "breakdown": rad_breakdown,
                        "kpi_data": kpi_data,
                        "extracted_text": doc_text_stream,
                        "user_inputs": {
                            "age": age_for_report,
                            "gender": gender_for_report,
                            "doc_type": doc_type_choice
                        }
                    }
                    if curr_auth_user:
                        try:
                            auth_db.save_medical_scan(
                                user_id=curr_auth_user["id"],
                                family_member_id=p_mem_id,
                                scan_type="Radiology",
                                scan_mode=p_mode,
                                result_reference=doc_name,
                                summary=f"Radiology — {sev_status} ({total_findings} findings)",
                                details=full_rad_record
                            )
                        except Exception as save_err:
                            print(f"Notice auto-saving radiology scan: {save_err}")
                    st.session_state["current_session_scan"] = full_rad_record
                    if "session_scans" not in st.session_state:
                        st.session_state["session_scans"] = []
                    if not any(s.get("result_reference") == doc_name and s.get("created_at") == full_rad_record["created_at"] for s in st.session_state["session_scans"]):
                        st.session_state["session_scans"].insert(0, full_rad_record)
                    st.session_state[rad_save_key] = True

        else:
            with st.spinner("Evaluating clinical parameters against biological reference intervals..."):
                lab_res = lab_analyzer.parse_and_evaluate(doc_text_stream, age_group=age_for_report, gender=gender_for_report, lang=lang_code)
            
            total_detected = lab_res.get("total_tests_detected", 0)

            if total_detected == 0:
                st.markdown(f"""
                <div class="mm-card" style="border-left: 4px solid #F59E0B; background: rgba(245, 158, 11, 0.05); padding: 18px; margin-top: 10px;">
                    <h4 style="color: #F59E0B; margin: 0 0 6px 0; font-size: 1.05rem;"> No Clinical Lab Parameters Detected</h4>
                    <p style="margin: 0; font-size: 0.92rem; color: var(--mm-text-secondary);">
                        {lab_res.get("summary", "The uploaded document does not appear to be a medical lab report or does not contain recognized diagnostic test values. Please ensure you upload a clear laboratory report, blood test (CBC, LFT, KFT, Lipid Profile), or pathology document.")}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Log analysis to SQLite database DocMindX.db
                try:
                    log_report_analysis(
                        report_name=doc_name,
                        report_type="Lab Evaluation",
                        extracted_text=doc_text_stream,
                        summary=lab_res.get("summary", f"Detected {lab_res.get('abnormal_count', 0)} abnormal parameters out of {total_detected} total."),
                        findings=lab_res.get("findings", []),
                        abnormal_count=lab_res.get("abnormal_count", 0)
                    )
                except Exception as e:
                    print(f"Notice logging report analysis: {e}")

                ab_count = lab_res.get("abnormal_count", 0)
                status_overall = "Needs Attention" if ab_count > 0 else "All Normal"

                # Automatic Clinical AI Patient Guide for Blood / Pathology Lab Reports
                lab_cache_key = f"p2_breakdown_{doc_name}_{lang_code}"
                if lab_cache_key not in st.session_state:
                    with st.spinner("Generating Comprehensive Clinical AI Patient Guide & Recovery Plan..."):
                        lab_breakdown = generate_medical_report_comprehensive_breakdown(
                            report_type="Blood / Pathology Lab Report",
                            doc_text=doc_text_stream,
                            findings=lab_res.get("findings", []),
                            age_group=age_for_report,
                            gender=gender_for_report,
                            lang=lang_code
                        )
                        st.session_state[lab_cache_key] = lab_breakdown
                else:
                    lab_breakdown = st.session_state[lab_cache_key]

                kpi_data = {
                    "card1": {
                        "label": "TOTAL PARAMETERS EVALUATED",
                        "val": total_detected,
                        "sub": "From Lab Report"
                    },
                    "card2": {
                        "label": "ABNORMAL / OUT-OF-RANGE",
                        "val": ab_count,
                        "sub": f"↑ {ab_count}" if ab_count > 0 else "↓ 0"
                    },
                    "card3": {
                        "label": "OVERALL CLINICAL STATUS",
                        "val": status_overall,
                        "sub": "Within Reference Range" if status_overall == "All Normal" else "Review Recommended"
                    }
                }

                render_diagnostic_evaluation_view(
                    doc_name=doc_name,
                    doc_type_choice=doc_type_choice,
                    age_for_report=age_for_report,
                    gender_for_report=gender_for_report,
                    findings=lab_res.get("findings", []),
                    breakdown_text=lab_breakdown,
                    kpi_data=kpi_data,
                    report_category="lab",
                    T=T,
                    lang_code=lang_code
                )

                # Auto-persist complete Lab record
                curr_auth_user = auth_ui.get_current_user()
                p2_ctx = st.session_state.get("p2_patient_context") or {}
                p_mode = p2_ctx.get("mode", "GENERAL") if curr_auth_user else "GENERAL"
                p_mem_id = p2_ctx.get("member_id") if p_mode == "FAMILY_MEMBER" else None
                p_name = p2_ctx.get("name") or (curr_auth_user.get("full_name") if curr_auth_user else "General Patient")

                lab_save_key = f"p2_saved_lab_{doc_name}_{p_mode}_{p_mem_id}"
                if lab_save_key not in st.session_state:
                    full_lab_record = {
                        "scan_type": "Lab Report",
                        "scan_mode": p_mode,
                        "result_reference": doc_name,
                        "summary": f"{status_overall} ({ab_count} abnormal / {total_detected} total)",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "patient_name": p_name,
                        "family_member_name": p_name if p_mode == "FAMILY_MEMBER" else None,
                        "patient_context": p2_ctx,
                        "doc_name": doc_name,
                        "findings": lab_res.get("findings", []),
                        "abnormal_count": ab_count,
                        "total_tests": total_detected,
                        "breakdown": lab_breakdown,
                        "kpi_data": kpi_data,
                        "extracted_text": doc_text_stream,
                        "user_inputs": {
                            "age": age_for_report,
                            "gender": gender_for_report,
                            "doc_type": doc_type_choice
                        }
                    }
                    if curr_auth_user:
                        try:
                            auth_db.save_medical_scan(
                                user_id=curr_auth_user["id"],
                                family_member_id=p_mem_id,
                                scan_type="Lab Report",
                                scan_mode=p_mode,
                                result_reference=doc_name,
                                summary=f"Lab Report — {status_overall} ({ab_count} abnormal)",
                                details=full_lab_record
                            )
                        except Exception as save_err:
                            print(f"Notice auto-saving lab scan: {save_err}")
                    st.session_state["current_session_scan"] = full_lab_record
                    if "session_scans" not in st.session_state:
                        st.session_state["session_scans"] = []
                    if not any(s.get("result_reference") == doc_name and s.get("created_at") == full_lab_record["created_at"] for s in st.session_state["session_scans"]):
                        st.session_state["session_scans"].insert(0, full_lab_record)
                    st.session_state[lab_save_key] = True

    # Footer
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)


elif st.session_state["active_panel"] == "Nearby Healthcare":
    gis_icon_html = '<img src="https://cdn-icons-png.flaticon.com/512/4002/4002972.png" style="width: 52px; height: 52px; border-radius: 14px; object-fit: contain; padding: 5px; background: rgba(2,132,199,0.08); box-shadow: 0 4px 14px rgba(2,132,199,0.35); border: 1.5px solid #0284C7;" alt="Healthcare Finder Icon"/>'
    with st.container(key="mm_top_header_card_3"):
        hdr3_c1, hdr3_c2, hdr3_c3, hdr3_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr3_c1:
            title_p3 = T.get("p3_header_title", "Nearby Healthcare & Emergency Finder")
            sub_p3 = T.get("p3_header_subtitle", "Locate verified 24/7 trauma centers, hospitals, clinics, and pharmacies with live routing.")
            safe_markdown(
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{gis_icon_html}'
                f'<div style="min-width: 0; flex: 1;">'
                f'<div style="margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">{title_p3}</div>'
                f'<div style="margin-top: 4px; font-size: 0.85rem; color: var(--mm-text-secondary); line-height: 1.35;">{sub_p3}</div>'
                f'</div>'
                f'</div>'
            )
        with hdr3_c2:
            safe_markdown(
                f'<div style="display: flex; justify-content: center; align-items: center; height: 38px;">'
                f'<span class="mm-gis-engine-badge">'
                f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>'
                f'{T.get("p3_gis_badge", "LIVE GIS HEALTHCARE ENGINE")}'
                f'</span>'
                f'</div>'
            )
        with hdr3_c3:
            header_lang_3 = st.selectbox(
                "Header Lang Selector 3",
                options=LANG_OPTIONS,
                key="hdr_lang_p3",
                label_visibility="collapsed",
                on_change=sync_language,
                args=("hdr_lang_p3",)
            )
        with hdr3_c4:
            new_theme_p3 = theme_toggle_switch(is_dark=st.session_state.get("dark_mode", False), key="hdr_sun_moon_p3")
            if new_theme_p3 != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = new_theme_p3
                st.rerun()

    gis_c1, gis_c2, gis_c3 = st.columns([1.1, 1.1, 1.1])

    with gis_c1:
        with st.container(border=True, key="gis_panel_col_1"):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                <div class="mm-gis-icon-box">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="#2563EB"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                </div>
                <div class="mm-gis-title">{T.get("gis_step1_title", "Location & Perimeter")}</div>
            </div>
            """, unsafe_allow_html=True)

            loc_source = st.radio(
                "Choose Location Source:",
                [
                    "Live Device GPS",
                    "Auto-Detect via Network IP",
                    "Search Specific Indian City / Area"
                ],
                index=2,
                label_visibility="collapsed"
            )

            selected_lat = 23.0225
            selected_lon = 72.5714
            loc_name = "Ahmedabad, Gujarat"

            if "Live Device GPS" in loc_source:
                gps_status = st.query_params.get("gps_status", "")
                if gps_status == "SUCCESS" and "gps_lat" in st.query_params and "gps_lon" in st.query_params:
                    try:
                        selected_lat = float(st.query_params["gps_lat"])
                        selected_lon = float(st.query_params["gps_lon"])
                        loc_name = reverse_geocode(selected_lat, selected_lon)
                    except Exception:
                        selected_lat, selected_lon, loc_name = 23.0225, 72.5714, "Ahmedabad, Gujarat"
                elif gps_status == "ERROR":
                    err_code = str(st.query_params.get("gps_err_code", "1"))
                    if err_code == "1":
                        st.warning("Location Permission Denied in browser.")
                    elif err_code == "2":
                        st.warning("Device GPS is Turned OFF.")
                    else:
                        st.warning("Location Request Timed Out.")
                    selected_lat, selected_lon, loc_name = 23.0225, 72.5714, "Ahmedabad, Gujarat"

                # Auto-requesting Geolocation JavaScript Bridge
                gps_html = """
                <script>
                function autoRequestGPS() {
                    if (!navigator.geolocation) {
                        try {
                            const url = new URL(window.parent.location.href);
                            url.searchParams.set("gps_status", "ERROR");
                            url.searchParams.set("gps_err_code", "1");
                            window.parent.location.href = url.toString();
                        } catch(e) {}
                        return;
                    }
                    navigator.geolocation.getCurrentPosition(
                        function(pos) {
                            try {
                                const url = new URL(window.parent.location.href);
                                const lat = pos.coords.latitude.toFixed(6);
                                const lon = pos.coords.longitude.toFixed(6);
                                if (url.searchParams.get("gps_lat") !== lat || url.searchParams.get("gps_lon") !== lon) {
                                    url.searchParams.set("gps_lat", lat);
                                    url.searchParams.set("gps_lon", lon);
                                    url.searchParams.set("gps_status", "SUCCESS");
                                    url.searchParams.delete("gps_err_code");
                                    window.parent.location.href = url.toString();
                                }
                            } catch(e) {
                                console.error(e);
                            }
                        },
                        function(err) {
                            try {
                                const url = new URL(window.parent.location.href);
                                if (url.searchParams.get("gps_status") !== "ERROR" || url.searchParams.get("gps_err_code") !== String(err.code)) {
                                    url.searchParams.set("gps_status", "ERROR");
                                    url.searchParams.set("gps_err_code", String(err.code));
                                    window.parent.location.href = url.toString();
                                }
                            } catch(e) {
                                console.error(e);
                            }
                        },
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                }
                autoRequestGPS();
                </script>
                """
                components.html(gps_html, height=0)

            elif "Auto-Detect" in loc_source:
                client_ip = get_client_ip()
                auto_geo = detect_auto_location(client_ip=client_ip)
                selected_lat = float(auto_geo.get("lat", 23.0225))
                selected_lon = float(auto_geo.get("lon", 72.5714))
                loc_name = auto_geo.get("formatted_address") or f"{auto_geo.get('city', 'Ahmedabad')}, {auto_geo.get('region', 'Gujarat')}"

            else:
                search_addr = st.text_input("Enter City or District:", value="Ahmedabad, Gujarat", key="gis_city_search_input", label_visibility="collapsed")
                geo = geocode_address(search_addr)
                if geo:
                    selected_lat = geo["latitude"]
                    selected_lon = geo["longitude"]
                    loc_name = geo["formatted_address"]
                else:
                    selected_lat, selected_lon, loc_name = geocode_city_district(search_addr)

            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.76rem; color: #64748B; margin-top: 14px; font-weight: 500;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="#2563EB" style="flex-shrink: 0;"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                <span><b style="color: var(--mm-text-primary);">Location:</b> {loc_name} ({selected_lat:.4f}, {selected_lon:.4f})</span>
            </div>
            """, unsafe_allow_html=True)

    with gis_c2:
        with st.container(border=True, key="gis_panel_col_2"):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                <div class="mm-gis-icon-box">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="#2563EB"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-3v3h-4v-3H7v-4h3V6h4v3h3v4z"/></svg>
                </div>
                <div class="mm-gis-title">{T.get("gis_step2_title", "Facility Category")}</div>
            </div>
            """, unsafe_allow_html=True)

            facility_cat_map = {
                T.get("fac_emergency", "24/7 Emergency & Trauma Centers"): "emergency_24x7",
                T.get("fac_hospital", "Multi-Speciality Hospitals"): "hospital",
                T.get("fac_clinic", "Specialized Clinics & Daycare"): "clinic",
                T.get("fac_pharmacy", "24/7 Pharmacies & Chemists"): "pharmacy",
                T.get("fac_blood_bank", "Regional Blood Banks"): "blood_bank",
                T.get("fac_diagnostic", "Diagnostic & Pathology Labs"): "diagnostic"
            }

            cat_choice = st.selectbox(
                "Facility Type",
                list(facility_cat_map.keys()),
                index=0,
                label_visibility="collapsed"
            )
            active_facility_key = facility_cat_map.get(cat_choice, "hospital")

            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.88rem; font-weight: 800; color: #1E3A8A; margin-top: 14px; margin-bottom: 2px;">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="22" y1="12" x2="18" y2="12"/>
                    <line x1="6" y1="12" x2="2" y2="12"/>
                    <line x1="12" y1="6" x2="12" y2="2"/>
                    <line x1="12" y1="22" x2="12" y2="18"/>
                </svg>
                <span>{T.get("gis_radius_label", "Perimeter Radius (KM)")}</span>
            </div>
            """, unsafe_allow_html=True)

            search_radius = st.slider("Perimeter Radius (KM)", min_value=1, max_value=25, value=5, step=1, label_visibility="collapsed")
            st.markdown("""
            <div style="display: flex; justify-content: space-between; font-size: 0.74rem; color: #64748B; font-weight: 700; margin-top: -6px; padding: 0 4px;">
                <span>1 KM</span>
                <span>25 KM</span>
            </div>
            """, unsafe_allow_html=True)

    with gis_c3:
        with st.container(border=True, key="gis_panel_col_3"):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 16px;">
                <div class="mm-gis-icon-box">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="6" cy="19" r="3" fill="#2563EB"/>
                        <circle cx="18" cy="5" r="3" fill="#2563EB"/>
                        <path d="M12 19h4.5a3.5 3.5 0 0 0 0-7h-8a3.5 3.5 0 0 1 0-7H18"/>
                    </svg>
                </div>
                <div class="mm-gis-title">{T.get("gis_step3_title", "Navigation Mode & Sort")}</div>
            </div>
            """, unsafe_allow_html=True)

            sort_by = st.selectbox(
                "Sort Facilities By:",
                [T.get("sort_distance", "Distance (Closest First)"), T.get("sort_rating", "Highest Rating (4.0+ Stars)"), T.get("sort_emergency", "Emergency Priority")],
                index=0,
                label_visibility="collapsed"
            )

            travel_mode_choice = st.selectbox(
                "Travel Mode:",
                [
                    T.get("mode_car", "Car / Ambulance (Driving)"),
                    T.get("mode_bike", "Two-Wheeler / Bike"),
                    T.get("mode_walk", "Walking"),
                    T.get("mode_bus", "Public Transit")
                ],
                index=0,
                label_visibility="collapsed"
            )
            mode_code = "car" if "Car" in str(travel_mode_choice) else ("bike" if "Bike" in str(travel_mode_choice) else ("walk" if "Walk" in str(travel_mode_choice) else "bus"))

            st.markdown("""
            <div class="mm-gis-helpline-box">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="#0284C7" style="flex-shrink: 0;">
                    <path d="M19 10.5V8c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v7c0 .55.45 1 1 1h1.05c.44 1.19 1.58 2 2.95 2s2.51-.81 2.95-2h4.1c.44 1.19 1.58 2 2.95 2s2.51-.81 2.95-2H21c.55 0 1-.45 1-1v-2.5l-3-4.5zM7.5 17c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm10.5 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM8 12H6v-2h2v2zm6-4h-3v1h3V8zm0 2h-3v1h3v-1zm4.5 2h-2.5V9.5h1.67L18.5 12z"/>
                </svg>
                <div style="font-size: 0.76rem; color: #0284C7; line-height: 1.35;">
                    <b>Emergency Helplines:</b> Ambulance <b>108</b> · National <b>112</b> · AIIMS <b>1910</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Search nearby healthcare facilities
    with st.spinner(f"Locating verified facilities near {loc_name}..."):
        try:
            facilities = search_nearby_healthcare(
                selected_lat,
                selected_lon,
                facility_category=active_facility_key,
                radius_meters=search_radius * 1000
            )
        except Exception as e:
            print(f"Error querying healthcare: {e}")
            facilities = []

    facilities = facilities or []

    # Sorting
    if "Rating"in str(sort_by):
        facilities.sort(key=lambda x: (float(x.get("rating") or 0.0), -float(x.get("distance_km") or 999.0)), reverse=True)
    elif "Emergency"in str(sort_by):
        facilities.sort(key=lambda x: (0 if ("24/7"in str(x.get("emergency", "")) or "Yes"in str(x.get("emergency", "")) or x.get("is_emergency")) else 1, float(x.get("distance_km") or 999.0)))
    else:
        facilities.sort(key=lambda x: float(x.get("distance_km") or 999.0))

    active_fac_idx = st.session_state.get("selected_nav_fac_idx", None)
    selected_fac = None
    route_info = None

    if isinstance(active_fac_idx, int) and 0 <= active_fac_idx < len(facilities):
        selected_fac = facilities[active_fac_idx]
        try:
            route_info = get_route(selected_lat, selected_lon, selected_fac['lat'], selected_fac['lon'], mode=mode_code)
        except Exception:
            route_info = None

    if selected_fac is not None and route_info is not None:
        r_c1, r_c2 = st.columns([4.2, 1.0])
        with r_c1:
            st.markdown(f"""
            <div style="background: rgba(37, 99, 235, 0.08); border: 1.5px solid rgba(37, 99, 235, 0.4); border-radius: 10px; padding: 10px 14px; margin-bottom: 10px;">
                <div style="font-size: 0.88rem; font-weight: 800; color: #06B6D4;">Active Route: {selected_fac['name']}</div>
                <div style="font-size: 0.78rem; color: var(--mm-text-secondary);">Mode: <b>{travel_mode_choice}</b> · Distance: <b>{route_info.get('distance_km', selected_fac.get('distance_km'))} KM</b> · Est. Time: <b>~{route_info.get('duration', '10 mins')}</b></div>
            </div>
            """, unsafe_allow_html=True)
        with r_c2:
            if st.button(T.get("btn_clear_route", "Clear Route"), key="btn_clear_active_route", type="secondary", use_container_width=True):
                st.session_state["selected_nav_fac_idx"] = None
                st.rerun()

    # Map Component
    map_html = generate_google_map_html(
        user_lat=selected_lat,
        user_lon=selected_lon,
        facilities=facilities,
        location_name=loc_name,
        selected_facility=selected_fac,
        route_data=route_info
    )
    components.html(map_html, height=450)

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin: 20px 0 10px 0;">
        <b style="font-size: 1.1rem; color: var(--mm-text-primary);">Verified Facilities ({len(facilities)} Found within {search_radius} KM)</b>
    </div>
    """, unsafe_allow_html=True)

    if not facilities:
        st.info("No facilities found for this specific filter within the radius. Try increasing the search radius.")
    else:
        FAC_AVATARS = [
            {"bg": "#EFF6FF", "border": "#BFDBFE", "fg": "#2563EB", "dark_bg": "rgba(37, 99, 235, 0.2)", "dark_border": "rgba(59, 130, 246, 0.4)", "dark_fg": "#60A5FA"},   # Blue
            {"bg": "#ECFDF5", "border": "#A7F3D0", "fg": "#059669", "dark_bg": "rgba(5, 150, 105, 0.2)", "dark_border": "rgba(16, 185, 129, 0.4)", "dark_fg": "#34D399"},   # Green
            {"bg": "#FEF2F2", "border": "#FECACA", "fg": "#DC2626", "dark_bg": "rgba(220, 38, 38, 0.2)", "dark_border": "rgba(239, 68, 68, 0.4)", "dark_fg": "#F87171"},   # Red
            {"bg": "#F5F3FF", "border": "#DDD6FE", "fg": "#7C3AED", "dark_bg": "rgba(124, 58, 237, 0.2)", "dark_border": "rgba(139, 92, 246, 0.4)", "dark_fg": "#A78BFA"},  # Purple
            {"bg": "#FFF7ED", "border": "#FED7AA", "fg": "#EA580C", "dark_bg": "rgba(234, 88, 12, 0.2)", "dark_border": "rgba(249, 115, 22, 0.4)", "dark_fg": "#FB923C"},   # Orange
            {"bg": "#F0FDFA", "border": "#99F6E4", "fg": "#0D9488", "dark_bg": "rgba(13, 148, 136, 0.2)", "dark_border": "rgba(20, 184, 166, 0.4)", "dark_fg": "#2DD4BF"},  # Teal
        ]

        for row_start in range(0, len(facilities), 3):
            row_facs = facilities[row_start:row_start + 3]
            f_cols = st.columns(3)
            for c_idx, fac in enumerate(row_facs):
                i = row_start + c_idx
                with f_cols[c_idx]:
                    rating_val = fac.get("rating", 4.5)
                    dist_val = fac.get("distance_km", 1.5)
                    fac_name = fac.get("name", "Healthcare Facility")
                    fac_type = fac.get("type", "Hospital")
                    fac_address = fac.get("address", "Nearby Area")
                    fac_phone = fac.get("phone", "108 / Reception Desk")
                    fac_emergency = fac.get("emergency", "24/7 ACTIVE CARE")

                    is_dark = st.session_state.get("dark_mode", False)
                    av = FAC_AVATARS[i % len(FAC_AVATARS)]
                    av_bg = av["dark_bg"] if is_dark else av["bg"]
                    av_border = av["dark_border"] if is_dark else av["border"]
                    av_fg = av["dark_fg"] if is_dark else av["fg"]

                    with st.container():
                        st.markdown(f"""
                        <div class="mm-hospital-card">
                            <div>
                                <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 12px;">
                                    <div style="display: flex; align-items: flex-start; gap: 12px; flex: 1; min-width: 0;">
                                        <div style="width: 48px; height: 48px; min-width: 48px; border-radius: 12px; background: {av_bg}; border: 1.5px solid {av_border}; display: flex; align-items: center; justify-content: center; color: {av_fg}; flex-shrink: 0; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);">
                                            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>
                                        </div>
                                        <b style="font-size: 0.98rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.32; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; min-height: 42px;">{fac_name}</b>
                                    </div>
                                    <span class="mm-fac-dist-badge">
                                        <svg width="12" height="12" viewBox="0 0 24 24" fill="#0284C7"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
                                        <span>{dist_val:.2f} KM</span>
                                    </span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <div style="display: flex; align-items: center; gap: 7px; font-size: 0.80rem; color: var(--mm-text-secondary); font-weight: 600;">
                                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #64748B; flex-shrink: 0;"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>
                                        <span>{fac_type}</span>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 4px; font-size: 0.88rem; font-weight: 800; color: #EA580C;">
                                        <svg width="15" height="15" viewBox="0 0 24 24" fill="#F59E0B" stroke="#F59E0B"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                                        <span>{rating_val}</span>
                                    </div>
                                </div>
                                <div style="display: flex; align-items: flex-start; gap: 8px; font-size: 0.78rem; color: var(--mm-text-secondary); margin-bottom: 8px; line-height: 1.4; height: 38px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none" style="color: #64748B; flex-shrink: 0; margin-top: 1px;"><path d="M12 0C7.58 0 4 3.58 4 8c0 5.25 7 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/></svg>
                                    <span>{fac_address}</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: var(--mm-text-secondary); margin-bottom: 10px;">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none" style="color: #64748B; flex-shrink: 0;"><path d="M6.62 10.79a15.053 15.053 0 0 0 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                                    <span>{fac_phone}</span>
                                </div>
                            </div>
                            <div style="margin-top: auto;">
                                <span class="mm-fac-active-badge">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="#059669"><circle cx="12" cy="12" r="10"/><polyline points="8 12 11 15 16 9" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                                    <span>{fac_emergency}</span>
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("<div class='mm-gis-action-row'>", unsafe_allow_html=True)
                        b_c1, b_c2 = st.columns(2)
                        with b_c1:
                            if st.button(T.get("btn_route", "Route"), key=f"fac_route_{i}", type="primary", icon=":material/near_me:", use_container_width=True):
                                st.session_state["selected_nav_fac_idx"] = i
                                st.rerun()
                        with b_c2:
                            direct_maps_url = fac.get("google_maps_uri") or f"https://www.google.com/maps/dir/?api=1&destination={fac['lat']},{fac['lon']}"
                            st.link_button(T.get("btn_view_map", "View on Map"), direct_maps_url, icon=":material/map:", use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)


# ==============================================================================
# MODULE 4: HEALTH RECORDS & MEDICAL HISTORY (SQLite Vault)
# ==============================================================================
elif st.session_state["active_panel"] == "Health Records":
    # 1. Consistent Top Header Bar (Module 4)
    records_icon_html = (
        '<div style="width: 52px; height: 52px; border-radius: 14px; background: rgba(37, 99, 235, 0.08); '
        'border: 1.5px solid #2563EB; display: flex; align-items: center; justify-content: center; '
        'box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); flex-shrink: 0;">'
        '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<path d="M12 18v-6"/>'
        '<path d="M9 15h6"/>'
        '</svg></div>'
    )
    
    curr_auth_user = auth_ui.get_current_user()
    is_user_auth = bool(curr_auth_user and auth_ui.is_authenticated())

    with st.container(key="mm_top_header_card_4"):
        hdr4_c1, hdr4_c2, hdr4_c3, hdr4_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr4_c1:
            title_p4 = T.get("p4_header_title", "Health Records & Clinical Vault")
            sub_p4 = T.get("p4_header_subtitle", "Cryptographically secured medical vault, family longitudinal tracking, and diagnostic archive.")
            safe_markdown(
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{records_icon_html}'
                f'<div style="min-width: 0; flex: 1;">'
                f'<div style="margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">{title_p4}</div>'
                f'<div style="margin-top: 4px; font-size: 0.85rem; color: var(--mm-text-secondary); line-height: 1.35;">{sub_p4}</div>'
                f'</div>'
                f'</div>'
            )
        with hdr4_c2:
            if is_user_auth:
                badge_html = (
                    '<span style="height: 36px; padding: 0 16px; border-radius: 20px; background: rgba(16, 185, 129, 0.10); '
                    'border: 1px solid rgba(16, 185, 129, 0.3); color: #059669; font-weight: 700; font-size: 0.80rem; '
                    'display: inline-flex; align-items: center; gap: 8px;">'
                    '<span style="width: 8px; height: 8px; border-radius: 50%; background: #10B981; display: inline-block;"></span>'
                    'ENCRYPTED VAULT ACTIVE'
                    '</span>'
                )
            else:
                badge_html = (
                    '<span style="height: 36px; padding: 0 16px; border-radius: 20px; background: rgba(37, 99, 235, 0.10); '
                    'border: 1px solid rgba(37, 99, 235, 0.3); color: #2563EB; font-weight: 700; font-size: 0.80rem; '
                    'display: inline-flex; align-items: center; gap: 8px;">'
                    '<span style="width: 8px; height: 8px; border-radius: 50%; background: #2563EB; display: inline-block;"></span>'
                    'GUEST SESSION MODE'
                    '</span>'
                )
            st.markdown(f"<div style='display: flex; justify-content: center; align-items: center; height: 38px;'>{badge_html}</div>", unsafe_allow_html=True)
        with hdr4_c3:
            st.selectbox(
                "Header Lang Selector 4",
                options=LANG_OPTIONS,
                key="hdr_lang_p4",
                label_visibility="collapsed",
                on_change=sync_language,
                args=("hdr_lang_p4",)
            )
        with hdr4_c4:
            new_theme_p4 = theme_toggle_switch(is_dark=st.session_state.get("dark_mode", False), key="hdr_sun_moon_p4")
            if new_theme_p4 != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = new_theme_p4
                st.rerun()

    # Reusable Clinical Record Card Renderer
    def render_clinical_record_view(scan: dict, idx: int, is_authenticated: bool = True):
        scan_id = scan.get("id") or f"sess_{idx}"
        scan_type = scan.get("scan_type", "Health Assessment")
        scan_mode = scan.get("scan_mode", "GENERAL")
        created_at = str(scan.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))[:16]
        ref_title = scan.get("result_reference") or scan.get("doc_name") or f"{scan_type} Record"
        summary = scan.get("summary", "Clinical assessment evaluated.")
        
        details = scan.get("details") or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}
        
        patient_name = scan.get("patient_name") or details.get("patient_name") or ("General Patient" if scan_mode == "GENERAL" else "Patient")
        urgency = details.get("urgency_level") or details.get("overall_severity") or scan.get("urgency_level") or ("Needs Attention" if details.get("abnormal_count", 0) > 0 else "Normal")
        is_emerg = bool(details.get("is_emergency") or details.get("red_flag_alert") or str(urgency).upper() in ["EMERGENCY", "HIGH", "CRITICAL"])
        
        if is_emerg or str(urgency).upper() in ["EMERGENCY", "HIGH", "CRITICAL"]:
            badge_bg = "rgba(239, 68, 68, 0.12)"
            badge_border = "#EF4444"
            badge_color = "#DC2626"
            badge_label = f"HIGH URGENCY: {urgency}".upper()
        elif str(urgency).upper() in ["MEDIUM", "MODERATE", "NEEDS ATTENTION", "REVIEW PRECAUTIONS"]:
            badge_bg = "rgba(245, 158, 11, 0.12)"
            badge_border = "#F59E0B"
            badge_color = "#D97706"
            badge_label = f"MODERATE: {urgency}".upper()
        else:
            badge_bg = "rgba(16, 185, 129, 0.12)"
            badge_border = "#10B981"
            badge_color = "#059669"
            badge_label = "NORMAL / STABLE"

        if "Assessment" in scan_type or "Triage" in scan_type:
            type_icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 3v5a5.5 5.5 0 0 0 11 0V3"></path><path d="M10 13.5v3.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-1.5"></path><circle cx="17" cy="15.5" r="2.5"></circle></svg>'
            type_color = "#2563EB"
        elif "Prescription" in scan_type:
            type_icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>'
            type_color = "#10B981"
        elif "Radiology" in scan_type or "Imaging" in scan_type:
            type_icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>'
            type_color = "#8B5CF6"
        else:
            type_icon = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
            type_color = "#0284C7"

        with st.container(key=f"rec_card_{scan_id}_{idx}", border=True):
            safe_markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 42px; height: 42px; border-radius: 10px; background: rgba(37, 99, 235, 0.08); border: 1.5px solid {type_color}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        {type_icon}
                    </div>
                    <div>
                        <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.2;">
                            {ref_title}
                        </div>
                        <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 3px;">
                            <span style="font-weight: 700; color: {type_color};">{scan_type.upper()}</span> &bull; <span>{created_at}</span> &bull; <span>Patient: <b>{patient_name}</b> ({scan_mode})</span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: {badge_bg}; border: 1px solid {badge_border}; color: {badge_color}; font-weight: 800; font-size: 0.72rem; padding: 4px 10px; border-radius: 20px;">
                        {badge_label}
                    </span>
                </div>
            </div>
            <div style="font-size: 0.86rem; color: var(--mm-text-primary); margin-bottom: 12px; padding: 8px 12px; background: var(--mm-card-bg, rgba(255,255,255,0.03)); border-radius: 8px; border-left: 3px solid {type_color};">
                <b>Summary:</b> {summary}
            </div>
            """)

            with st.expander("View Complete Clinical Details & Protocols", expanded=False):
                sec1, sec2 = st.columns(2)
                
                # Section 1: User Reported Inputs / Context
                u_inputs = details.get("user_inputs") or {}
                with sec1:
                    st.markdown("""<div style="font-size: 0.82rem; font-weight: 800; color: #2563EB; text-transform: uppercase; margin-bottom: 6px;">1. Patient Context & Reported Inputs</div>""", unsafe_allow_html=True)
                    inp_items = []
                    if u_inputs.get("age"): inp_items.append(f"<b>Age:</b> {u_inputs['age']}")
                    if u_inputs.get("gender"): inp_items.append(f"<b>Gender:</b> {u_inputs['gender']}")
                    if u_inputs.get("duration"): inp_items.append(f"<b>Duration:</b> {u_inputs['duration']}")
                    if u_inputs.get("severity"): inp_items.append(f"<b>Severity:</b> {u_inputs['severity']}")
                    if u_inputs.get("blood_group") and u_inputs["blood_group"] != "None": inp_items.append(f"<b>Blood Group:</b> {u_inputs['blood_group']}")
                    if u_inputs.get("existing_conditions"):
                        cond_str = ", ".join(u_inputs["existing_conditions"]) if isinstance(u_inputs["existing_conditions"], list) else str(u_inputs["existing_conditions"])
                        inp_items.append(f"<b>Conditions:</b> {cond_str}")
                    if u_inputs.get("current_medicines"):
                        med_str = ", ".join(u_inputs["current_medicines"]) if isinstance(u_inputs["current_medicines"], list) else str(u_inputs["current_medicines"])
                        inp_items.append(f"<b>Active Meds:</b> {med_str}")
                    if u_inputs.get("symptoms"):
                        sym_str = ", ".join(u_inputs["symptoms"]) if isinstance(u_inputs["symptoms"], list) else str(u_inputs["symptoms"])
                        inp_items.append(f"<b>Symptoms:</b> {sym_str}")
                    
                    if inp_items:
                        st.markdown("<div style='font-size: 0.78rem; line-height: 1.6; color: var(--mm-text-secondary);'>" + "<br/>".join(inp_items) + "</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='font-size: 0.78rem; color: var(--mm-text-secondary);'>Standard clinical demographic profile recorded.</div>", unsafe_allow_html=True)

                # Section 2: Clinical Findings / Extracted Data
                with sec2:
                    st.markdown("""<div style="font-size: 0.82rem; font-weight: 800; color: #10B981; text-transform: uppercase; margin-bottom: 6px;">2. Extracted Findings & Parameters</div>""", unsafe_allow_html=True)
                    findings = details.get("findings") or []
                    medicines = details.get("medicines") or []
                    
                    if medicines:
                        med_html = "<div style='display: flex; flex-direction: column; gap: 6px;'>"
                        for m in medicines[:5]:
                            m_name = m.get("name") or m.get("medicine_name") or "Medicine"
                            dosage = m.get("dosage") or m.get("frequency") or "As directed"
                            purpose = m.get("purpose") or m.get("indications") or "Prescribed Therapy"
                            med_html += f"<div style='background: rgba(16, 185, 129, 0.05); padding: 6px 10px; border-radius: 6px; border-left: 2px solid #10B981; font-size: 0.76rem;'><b>{m_name}</b> &bull; {dosage}<br/><span style='color: var(--mm-text-secondary); font-size: 0.72rem;'>{purpose}</span></div>"
                        med_html += "</div>"
                        st.markdown(med_html, unsafe_allow_html=True)
                    elif findings:
                        f_html = "<div style='display: flex; flex-direction: column; gap: 4px;'>"
                        for f in findings[:6]:
                            t_name = f.get("test_name") or f.get("parameter") or f.get("observation") or "Finding"
                            val = f"{f.get('value', '')} {f.get('unit', '')}".strip()
                            st_txt = f.get("status") or f.get("severity") or "Evaluated"
                            color = "#EF4444" if str(st_txt).lower() in ["high", "low", "abnormal", "critical"] else "#10B981"
                            f_html += f"<div style='display: flex; justify-content: space-between; font-size: 0.76rem; border-bottom: 1px solid rgba(148,163,184,0.15); padding: 3px 0;'><span>{t_name}: <b>{val}</b></span><span style='color: {color}; font-weight: 700;'>{st_txt}</span></div>"
                        f_html += "</div>"
                        st.markdown(f_html, unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size: 0.78rem; color: var(--mm-text-secondary);'>{summary}</div>", unsafe_allow_html=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                # Section 3: AI Clinical Analysis & Ranked Conditions
                st.markdown("""<div style="font-size: 0.82rem; font-weight: 800; color: #8B5CF6; text-transform: uppercase; margin-bottom: 6px;">3. AI Clinical Evaluation & Diagnostic Analysis</div>""", unsafe_allow_html=True)
                ranked_conds = details.get("ranked_conditions") or []
                breakdown = details.get("breakdown") or ""
                red_flags = details.get("red_flags") or []

                if red_flags:
                    rf_html = "<div style='background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 8px 12px; margin-bottom: 8px; font-size: 0.76rem; color: #DC2626;'><b>CRITICAL RED FLAGS NOTED:</b> " + ", ".join([str(rf) for rf in red_flags]) + "</div>"
                    st.markdown(rf_html, unsafe_allow_html=True)

                if ranked_conds:
                    rc_html = "<div style='display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;'>"
                    for rc in ranked_conds[:3]:
                        rc_name = rc.get("name") or "Condition"
                        rc_prob = int(float(rc.get("confidence", rc.get("probability", 0.5))) * 100) if isinstance(rc.get("confidence") or rc.get("probability"), (int, float)) else 50
                        rc_html += f"<span style='background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); color: #7C3AED; font-weight: 700; font-size: 0.74rem; padding: 3px 10px; border-radius: 12px;'>{rc_name} ({rc_prob}%)</span>"
                    rc_html += "</div>"
                    st.markdown(rc_html, unsafe_allow_html=True)
                
                if breakdown:
                    st.markdown(f"<div style='font-size: 0.78rem; color: var(--mm-text-secondary); line-height: 1.5; max-height: 140px; overflow-y: auto; padding: 8px; background: rgba(0,0,0,0.02); border-radius: 6px;'>{breakdown[:600]}...</div>", unsafe_allow_html=True)

                # Section 4: Care Guidance, Yoga, Lifestyle
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.markdown("""<div style="font-size: 0.82rem; font-weight: 800; color: #D97706; text-transform: uppercase; margin-bottom: 6px;">4. Personalized Regimen & Care Guidance</div>""", unsafe_allow_html=True)
                yoga = details.get("yoga_recommendations") or []
                diet = details.get("diet_guidance") or {}
                lifestyle = details.get("lifestyle_guidance") or []
                
                g_col1, g_col2 = st.columns(2)
                with g_col1:
                    if yoga:
                        y_html = "<div style='font-size: 0.76rem; color: var(--mm-text-secondary);'><b>Targeted Yoga & Physical Therapy:</b><ul style='margin: 4px 0 0 16px; padding: 0;'>"
                        for y in yoga[:3]:
                            y_name = y.get("asana_name") or y.get("name") or "Asana"
                            y_html += f"<li>{y_name}</li>"
                        y_html += "</ul></div>"
                        st.markdown(y_html, unsafe_allow_html=True)
                    elif lifestyle:
                        l_html = "<div style='font-size: 0.76rem; color: var(--mm-text-secondary);'><b>Lifestyle Protocols:</b><ul style='margin: 4px 0 0 16px; padding: 0;'>"
                        for l in lifestyle[:3]:
                            l_html += f"<li>{str(l)}</li>"
                        l_html += "</ul></div>"
                        st.markdown(l_html, unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='font-size: 0.76rem; color: var(--mm-text-secondary);'>General hydration & rest protocol recommended.</div>", unsafe_allow_html=True)
                with g_col2:
                    if isinstance(diet, dict) and (diet.get("foods_to_eat") or diet.get("foods_to_avoid")):
                        d_html = "<div style='font-size: 0.76rem; color: var(--mm-text-secondary);'>"
                        if diet.get("foods_to_eat"):
                            d_html += f"<b>Include:</b> {', '.join(diet['foods_to_eat'][:4])}<br/>"
                        if diet.get("foods_to_avoid"):
                            d_html += f"<b>Limit:</b> {', '.join(diet['foods_to_avoid'][:4])}"
                        d_html += "</div>"
                        st.markdown(d_html, unsafe_allow_html=True)
                    else:
                        prec = details.get("precautions") or []
                        if prec:
                            p_html = "<div style='font-size: 0.76rem; color: var(--mm-text-secondary);'><b>Clinical Precautions:</b><ul style='margin: 4px 0 0 16px; padding: 0;'>"
                            for p in prec[:2]:
                                p_html += f"<li>{str(p)}</li>"
                            p_html += "</ul></div>"
                            st.markdown(p_html, unsafe_allow_html=True)

            # Card Bottom Actions: Direct PDF Download & Deletion
            st.markdown("<div style='border-top: 1px solid rgba(148,163,184,0.15); margin-top: 10px; padding-top: 10px;'></div>", unsafe_allow_html=True)
            act_c1, act_c2, act_c3 = st.columns([1.8, 1.2, 1.0], vertical_alignment="center")
            with act_c1:
                st.markdown(f"<div style='font-size: 0.72rem; color: var(--mm-text-secondary);'>Vault ID: <code>{scan_id}</code> &bull; Cryptographically Verified</div>", unsafe_allow_html=True)
            with act_c2:
                try:
                    pdf_bytes = generate_scan_record_pdf(scan)
                    clean_ref = "".join(c for c in ref_title if c.isalnum() or c in (' ', '_', '-')).rstrip()
                    pdf_filename = f"DocMindX_{scan_type.replace(' ', '_')}_{clean_ref[:20]}_{scan_id}.pdf"
                    st.download_button(
                        label="Download Report (PDF)",
                        data=pdf_bytes.getvalue(),
                        file_name=pdf_filename,
                        mime="application/pdf",
                        key=f"btn_dl_scan_{scan_id}_{idx}",
                        use_container_width=True
                    )
                except Exception as pdf_err:
                    st.caption(f"PDF unavailable: {pdf_err}")
            with act_c3:
                if is_authenticated and scan.get("id"):
                    if st.button("Delete Record", key=f"btn_del_scan_{scan_id}_{idx}", type="secondary", use_container_width=True):
                        try:
                            auth_db.delete_medical_scan(scan_id=scan["id"], user_id=curr_auth_user["id"])
                            st.success("Record deleted.")
                            st.rerun()
                        except Exception as del_err:
                            st.error(f"Error: {del_err}")

    # =========================================================================
    # A. USER IS NOT LOGGED IN: GUEST / CURRENT SESSION MODE
    # =========================================================================
    if not is_user_auth:
        safe_markdown(f"""
        <div style="background: rgba(37, 99, 235, 0.05); border: 1.5px solid rgba(59, 130, 246, 0.25); border-left: 5px solid #2563EB; border-radius: 14px; padding: 18px 22px; margin-bottom: 20px;">
            <div style="display: flex; align-items: flex-start; gap: 14px;">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: #2563EB; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #FFFFFF;">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="font-size: 1.05rem; font-weight: 800; color: var(--mm-text-primary);">
                        {T.get("guest_mode_title", "Guest / Current Session Mode")}
                    </div>
                    <div style="font-size: 0.84rem; color: var(--mm-text-secondary); margin-top: 4px; line-height: 1.45;">
                        {T.get("guest_mode_desc", "You are viewing clinical records for your active browser session only. Historical records from other accounts or past visits are not accessible. To permanently store records in an encrypted vault, create family member profiles, and track multi-year diagnostic trends, please sign in or register.")}
                    </div>
                </div>
            </div>
        </div>
        """)

        # Fetch current session scans (strictly in memory, ZERO database queries)
        session_scans = list(st.session_state.get("session_scans", []))
        current_sess_scan = st.session_state.get("current_session_scan")
        if current_sess_scan and not any(s.get("result_reference") == current_sess_scan.get("result_reference") and s.get("created_at") == current_sess_scan.get("created_at") for s in session_scans):
            session_scans.insert(0, current_sess_scan)

        if session_scans:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <div style="font-size: 1.10rem; font-weight: 800; color: var(--mm-text-primary);">
                    Active Session Records ({len(session_scans)})
                </div>
                <span style="background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: #2563EB; font-weight: 700; font-size: 0.74rem; padding: 4px 12px; border-radius: 12px;">
                    TEMPORARY BROWSER STORAGE
                </span>
            </div>
            """, unsafe_allow_html=True)

            for idx, sc in enumerate(session_scans):
                render_clinical_record_view(sc, idx, is_authenticated=False)

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                c_msg, c_btn = st.columns([3, 1], vertical_alignment="center")
                with c_msg:
                    st.markdown("""
                    <b style="color: var(--mm-text-primary); font-size: 0.95rem;">Save your session history permanently</b><br/>
                    <span style="color: var(--mm-text-secondary); font-size: 0.82rem;">Create a free clinical account to permanently encrypt and sync these scans across devices.</span>
                    """, unsafe_allow_html=True)
                with c_btn:
                    if st.button("Sign In / Register", key="btn_guest_save_sync", type="primary", use_container_width=True):
                        st.session_state["active_panel"] = "Account / Authentication"
                        st.rerun()

        else:
            # Polished empty state with actionable CTAs
            st.markdown(f"""
            <div class="mm-card" style="text-align: center; padding: 48px 24px; margin-top: 10px; background: var(--mm-card-bg, #FFFFFF); border: 1.5px dashed #CBD5E1; border-radius: 16px;">
                <div style="width: 58px; height: 58px; margin: 0 auto 16px auto; border-radius: 16px; background: rgba(37, 99, 235, 0.08); border: 1.5px solid rgba(59, 130, 246, 0.25); display: flex; align-items: center; justify-content: center; color: #2563EB;">
                    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </div>
                <h3 style="color: var(--mm-text-primary); font-size: 1.25rem; font-weight: 800; margin: 0 0 8px 0;">No Active Session Records</h3>
                <p style="color: var(--mm-text-secondary); font-size: 0.88rem; max-width: 560px; margin: 0 auto 24px auto; line-height: 1.5;">
                    You are browsing DocMindX AI as a guest. Any health assessment or medical document you analyze during this visit will be shown here temporarily. Sign in to access your encrypted clinical vault and family member profiles.
                </p>
            </div>
            """, unsafe_allow_html=True)

            cta1, cta2, cta3 = st.columns(3)
            with cta1:
                if st.button("Run Health Assessment", key="cta_guest_triage", type="primary", use_container_width=True):
                    st.session_state["active_panel"] = "Health Assessment"
                    st.rerun()
            with cta2:
                if st.button("Analyze Medical Report", key="cta_guest_report", type="secondary", use_container_width=True):
                    st.session_state["active_panel"] = "Medical Report"
                    st.rerun()
            with cta3:
                if st.button("Sign In / Register", key="cta_guest_auth", type="primary", use_container_width=True):
                    st.session_state["active_panel"] = "Account / Authentication"
                    st.rerun()

            st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 28px; height: 28px; border-radius: 8px; background: #10B981; display: flex; align-items: center; justify-content: center; color: #FFFFFF;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    </div>
                    <span style="font-size: 0.82rem; font-weight: 700; color: #059669;">Zero Data Exposure &bull; Strict Guest Session Privacy Guarantees</span>
                </div>
                <span style="font-size: 0.74rem; color: #64748B;">HIPAA &amp; WHO Compliant Architecture</span>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # B. USER IS LOGGED IN: MULTI-PROFILE ENCRYPTED CLINICAL VAULT
    # =========================================================================
    else:
        user_id = curr_auth_user["id"]
        profile_summary = auth_db.get_user_profile_summary(user_id)
        family_members = auth_db.get_family_members(user_id)

        options_list = ["General Scan", "My Profile"]
        option_map = {
            "General Scan": {"mode": "GENERAL", "member_id": None, "name": "General Scan", "type": "GENERAL"},
            "My Profile": {"mode": "PROFILE", "member_id": None, "name": curr_auth_user.get("full_name", "My Profile"), "type": "PROFILE", "details": profile_summary}
        }
        for m in family_members:
            opt_label = f"{m['name']} ({m.get('relationship', 'Family')})"
            options_list.append(opt_label)
            option_map[opt_label] = {"mode": "FAMILY_MEMBER", "member_id": m["id"], "name": m["name"], "type": "FAMILY_MEMBER", "details": m}

        sel_col, btn_col = st.columns([3, 1], vertical_alignment="bottom")
        with sel_col:
            selected_patient_opt = st.selectbox(
                "Active Patient / Record Selector",
                options=options_list,
                index=0,
                key="hr_patient_selector_dropdown"
            )
        with btn_col:
            if st.button("Manage Family Profiles", key="hr_manage_fam_btn", type="secondary", use_container_width=True):
                st.session_state["active_panel"] = "Family Management"
                st.rerun()

        target_cfg = option_map[selected_patient_opt]
        target_mode = target_cfg["mode"]
        target_member_id = target_cfg["member_id"]

        # Profile Summary Card
        if target_mode == "GENERAL":
            safe_markdown(f"""
            <div style="background: rgba(37, 99, 235, 0.05); border: 1.5px solid rgba(59, 130, 246, 0.25); border-left: 5px solid #2563EB; border-radius: 12px; padding: 14px 18px; margin: 12px 0 16px 0;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <div style="font-weight: 800; font-size: 0.96rem; color: #1E40AF;">GENERAL SCAN VAULT</div>
                        <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">
                            Displaying unlinked clinical assessments and triage records performed under this account. Private family member records are isolated and excluded.
                        </div>
                    </div>
                    <span style="font-size: 0.72rem; background: rgba(37, 99, 235, 0.15); color: #2563EB; padding: 3px 10px; border-radius: 12px; font-weight: 700;">DEFAULT REPOSITORY</span>
                </div>
            </div>
            """)
        elif target_mode == "PROFILE":
            p_det = target_cfg.get("details") or {}
            p_name = p_det.get("name") or curr_auth_user.get("full_name", "Account Owner")
            p_age = p_det.get("age") or "Adult"
            p_gen = p_det.get("gender") or "Unspecified"
            p_bg = p_det.get("blood_group") or "None"
            p_h = f"{p_det['height']} cm" if p_det.get("height") else "None"
            p_w = f"{p_det['weight']} kg" if p_det.get("weight") else "None"
            p_conds = p_det.get("conditions") or []
            p_meds = p_det.get("medications") or []

            cond_badges = " ".join([f"<span style='background: rgba(239, 68, 68, 0.1); color: #DC2626; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;'>{c}</span>" for c in p_conds]) if p_conds else "<span style='color: var(--mm-text-secondary); font-size: 0.74rem;'>None recorded</span>"
            med_badges = " ".join([f"<span style='background: rgba(16, 185, 129, 0.1); color: #059669; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;'>{m}</span>" for m in p_meds]) if p_meds else "<span style='color: var(--mm-text-secondary); font-size: 0.74rem;'>None recorded</span>"

            safe_markdown(f"""
            <div style="background: rgba(37, 99, 235, 0.04); border: 1.5px solid rgba(59, 130, 246, 0.25); border-left: 5px solid #2563EB; border-radius: 12px; padding: 14px 18px; margin: 12px 0 16px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <span style="font-weight: 800; font-size: 1.0rem; color: var(--mm-text-primary);">{p_name}</span>
                        <span style="background: rgba(37, 99, 235, 0.1); color: #2563EB; font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 10px; margin-left: 6px;">MY PROFILE (SELF)</span>
                    </div>
                    <div style="font-size: 0.76rem; color: var(--mm-text-secondary);">
                        Age: <b>{p_age}</b> &bull; Gender: <b>{p_gen}</b> &bull; Blood: <b>{p_bg}</b> &bull; Height: <b>{p_h}</b> &bull; Weight: <b>{p_w}</b>
                    </div>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 0.76rem; padding-top: 6px; border-top: 1px solid rgba(148,163,184,0.15);">
                    <div><b style="color: var(--mm-text-primary);">Known Conditions:</b> {cond_badges}</div>
                    <div><b style="color: var(--mm-text-primary);">Active Meds:</b> {med_badges}</div>
                </div>
            </div>
            """)
        else:
            m_det = target_cfg.get("details") or {}
            m_name = m_det.get("name", "Family Member")
            m_rel = m_det.get("relationship", "Family")
            m_age = m_det.get("age") or "Adult"
            m_gen = m_det.get("gender") or "Unspecified"
            m_bg = m_det.get("blood_group") or "None"
            m_h = f"{m_det['height']} cm" if m_det.get("height") else "None"
            m_w = f"{m_det['weight']} kg" if m_det.get("weight") else "None"
            raw_conds = m_det.get("conditions") or []
            m_conds = [c["condition_name"] if isinstance(c, dict) else str(c) for c in raw_conds]
            raw_meds = m_det.get("medications") or []
            m_meds = [med["medicine_name"] if isinstance(med, dict) else str(med) for med in raw_meds]

            cond_badges = " ".join([f"<span style='background: rgba(239, 68, 68, 0.1); color: #DC2626; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;'>{c}</span>" for c in m_conds]) if m_conds else "<span style='color: var(--mm-text-secondary); font-size: 0.74rem;'>None recorded</span>"
            med_badges = " ".join([f"<span style='background: rgba(16, 185, 129, 0.1); color: #059669; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;'>{m}</span>" for m in m_meds]) if m_meds else "<span style='color: var(--mm-text-secondary); font-size: 0.74rem;'>None recorded</span>"

            safe_markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.04); border: 1.5px solid rgba(16, 185, 129, 0.25); border-left: 5px solid #10B981; border-radius: 12px; padding: 14px 18px; margin: 12px 0 16px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <span style="font-weight: 800; font-size: 1.0rem; color: var(--mm-text-primary);">{m_name}</span>
                        <span style="background: rgba(16, 185, 129, 0.1); color: #059669; font-size: 0.70rem; font-weight: 700; padding: 2px 8px; border-radius: 10px; margin-left: 6px;">{m_rel.upper()}</span>
                    </div>
                    <div style="font-size: 0.76rem; color: var(--mm-text-secondary);">
                        Age: <b>{m_age}</b> &bull; Gender: <b>{m_gen}</b> &bull; Blood: <b>{m_bg}</b> &bull; Height: <b>{m_h}</b> &bull; Weight: <b>{m_w}</b>
                    </div>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 0.76rem; padding-top: 6px; border-top: 1px solid rgba(148,163,184,0.15);">
                    <div><b style="color: var(--mm-text-primary);">Recorded Conditions:</b> {cond_badges}</div>
                    <div><b style="color: var(--mm-text-primary);">Active Meds:</b> {med_badges}</div>
                </div>
            </div>
            """)

        # 3. Query Database with strict profile isolation
        scans = auth_db.get_user_scans(
            user_id=user_id,
            family_member_id=target_member_id,
            scan_mode=target_mode
        )

        reports_scans = [s for s in scans if s.get("scan_type") in ["Lab Report", "Radiology", "Medical Report", "Diagnostic Imaging"]]
        presc_scans = [s for s in scans if s.get("scan_type") == "Prescription" or (s.get("details") and s["details"].get("medicines"))]
        assess_scans = [s for s in scans if s.get("scan_type") in ["Health Assessment", "Triage"]]

        # 4. Five Dynamic Tabs
        tab_all, tab_reports, tab_presc, tab_assess, tab_insights = st.tabs([
            f"All Records ({len(scans)})",
            f"Medical Reports ({len(reports_scans)})",
            f"Prescriptions ({len(presc_scans)})",
            f"Previous Assessments ({len(assess_scans)})",
            "Saved Insights & Guidance"
        ])

        # TAB 1: ALL RECORDS & TIMELINE
        with tab_all:
            if scans:
                for idx, sc in enumerate(scans):
                    render_clinical_record_view(sc, idx, is_authenticated=True)
            else:
                st.markdown(f"""
                <div class="mm-card" style="text-align: center; padding: 36px 20px;">
                    <b style="color: var(--mm-text-primary); font-size: 1.0rem;">No clinical records found for {selected_patient_opt}</b>
                    <p style="color: var(--mm-text-secondary); font-size: 0.84rem; margin-top: 6px;">Assess symptoms in Panel 1 or upload medical documents in Panel 2 to build this patient's vault.</p>
                </div>
                """, unsafe_allow_html=True)

        # TAB 2: MEDICAL REPORTS
        with tab_reports:
            if reports_scans:
                for idx, sc in enumerate(reports_scans):
                    render_clinical_record_view(sc, idx, is_authenticated=True)
            else:
                st.markdown(f"""
                <div class="mm-card" style="text-align: center; padding: 36px 20px;">
                    <b style="color: var(--mm-text-primary); font-size: 1.0rem;">No medical reports or imaging records for {selected_patient_opt}</b>
                    <p style="color: var(--mm-text-secondary); font-size: 0.84rem; margin-top: 6px;">Upload a blood test, pathology report, or radiology scan in Panel 2.</p>
                </div>
                """, unsafe_allow_html=True)

        # TAB 3: PRESCRIPTIONS
        with tab_presc:
            if presc_scans:
                for idx, sc in enumerate(presc_scans):
                    render_clinical_record_view(sc, idx, is_authenticated=True)
            else:
                st.markdown(f"""
                <div class="mm-card" style="text-align: center; padding: 36px 20px;">
                    <b style="color: var(--mm-text-primary); font-size: 1.0rem;">No prescription records for {selected_patient_opt}</b>
                    <p style="color: var(--mm-text-secondary); font-size: 0.84rem; margin-top: 6px;">Upload a doctor's prescription in Panel 2 to extract active medicines and dosage schedules.</p>
                </div>
                """, unsafe_allow_html=True)

        # TAB 4: PREVIOUS ASSESSMENTS
        with tab_assess:
            if assess_scans:
                for idx, sc in enumerate(assess_scans):
                    render_clinical_record_view(sc, idx, is_authenticated=True)
            else:
                st.markdown(f"""
                <div class="mm-card" style="text-align: center; padding: 36px 20px;">
                    <b style="color: var(--mm-text-primary); font-size: 1.0rem;">No triage assessment records for {selected_patient_opt}</b>
                    <p style="color: var(--mm-text-secondary); font-size: 0.84rem; margin-top: 6px;">Perform a symptom assessment in Panel 1 to store risk evaluations and ranked conditions.</p>
                </div>
                """, unsafe_allow_html=True)

        # TAB 5: SAVED INSIGHTS & GUIDANCE (100% Dynamic from actual patient scans)
        with tab_insights:
            insights_found = []
            for sc in scans:
                dt = sc.get("details") or {}
                if isinstance(dt, str):
                    try: dt = json.loads(dt)
                    except Exception: dt = {}
                
                cond_name = sc.get("result_reference") or dt.get("ranked_conditions", [{}])[0].get("name") if dt.get("ranked_conditions") else sc.get("scan_type")
                yoga = dt.get("yoga_recommendations") or []
                diet = dt.get("diet_guidance") or {}
                lifestyle = dt.get("lifestyle_guidance") or []
                precautions = dt.get("precautions") or []
                
                if yoga or diet or lifestyle or precautions:
                    insights_found.append({
                        "condition": cond_name,
                        "date": str(sc.get("created_at", ""))[:10],
                        "yoga": yoga,
                        "diet": diet,
                        "lifestyle": lifestyle,
                        "precautions": precautions
                    })

            if insights_found:
                for ins in insights_found:
                    with st.container(border=True):
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight: 800; font-size: 0.95rem; color: #2563EB;">Clinical Regimen: {ins['condition']}</span>
                            <span style="font-size: 0.72rem; color: var(--mm-text-secondary);">Recorded: {ins['date']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        i_c1, i_c2 = st.columns(2)
                        with i_c1:
                            if ins["yoga"]:
                                st.markdown("<b style='font-size: 0.80rem; color: #7C3AED;'>Yoga & Physio Protocols:</b>", unsafe_allow_html=True)
                                y_str = "".join([f"<li style='font-size: 0.76rem;'>{y.get('asana_name', y.get('name', 'Asana'))}</li>" for y in ins["yoga"][:4]])
                                st.markdown(f"<ul style='margin: 4px 0 0 16px; padding: 0;'>{y_str}</ul>", unsafe_allow_html=True)
                            elif ins["lifestyle"]:
                                st.markdown("<b style='font-size: 0.80rem; color: #0284C7;'>Lifestyle Protocols:</b>", unsafe_allow_html=True)
                                l_str = "".join([f"<li style='font-size: 0.76rem;'>{str(l)}</li>" for l in ins["lifestyle"][:3]])
                                st.markdown(f"<ul style='margin: 4px 0 0 16px; padding: 0;'>{l_str}</ul>", unsafe_allow_html=True)
                        with i_c2:
                            diet_obj = ins.get("diet")
                            if isinstance(diet_obj, dict) and (diet_obj.get("foods_to_eat") or diet_obj.get("foods_to_avoid")):
                                st.markdown("<b style='font-size: 0.80rem; color: #059669;'>Dietary Guidelines:</b>", unsafe_allow_html=True)
                                d_str = ""
                                if diet_obj.get("foods_to_eat"):
                                    d_str += f"<div style='font-size: 0.76rem;'><b>Recommended:</b> {', '.join(diet_obj['foods_to_eat'][:4])}</div>"
                                if diet_obj.get("foods_to_avoid"):
                                    d_str += f"<div style='font-size: 0.76rem;'><b>Limit:</b> {', '.join(diet_obj['foods_to_avoid'][:4])}</div>"
                                st.markdown(d_str, unsafe_allow_html=True)
                            elif ins["precautions"]:
                                st.markdown("<b style='font-size: 0.80rem; color: #D97706;'>Clinical Precautions:</b>", unsafe_allow_html=True)
                                p_str = "".join([f"<li style='font-size: 0.76rem;'>{str(p)}</li>" for p in ins["precautions"][:3]])
                                st.markdown(f"<ul style='margin: 4px 0 0 16px; padding: 0;'>{p_str}</ul>", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="mm-card" style="text-align: center; padding: 36px 20px;">
                    <b style="color: var(--mm-text-primary); font-size: 1.0rem;">No personalized lifestyle insights recorded yet for {selected_patient_opt}</b>
                    <p style="color: var(--mm-text-secondary); font-size: 0.84rem; margin-top: 6px;">Run a health assessment in Panel 1 to generate personalized dietary plans, yoga asanas, and lifestyle protocols.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Run Health Assessment for this Patient", key="btn_run_triage_for_insights", type="primary"):
                    st.session_state["active_panel"] = "Health Assessment"
                    st.rerun()
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)


elif st.session_state["active_panel"] == "About DocMindX AI":
    about_icon_b64 = get_base64_image(FAVICON_PATH)
    about_icon_html = f'<img src="{about_icon_b64}" style="width: 52px; height: 52px; border-radius: 14px; object-fit: contain; padding: 4px; background: rgba(245,158,11,0.08); box-shadow: 0 4px 14px rgba(245,158,11,0.35); border: 1.5px solid #F59E0B;" alt="DocMindX Brand Icon"/>' if about_icon_b64 else '<img src="https://cdn-icons-png.flaticon.com/512/4712/4712109.png" style="width: 52px; height: 52px; border-radius: 14px; object-fit: contain; padding: 5px; background: rgba(245,158,11,0.08); box-shadow: 0 4px 14px rgba(245,158,11,0.35); border: 1.5px solid #F59E0B;" alt="DocMindX Brand Icon"/>'
    with st.container(key="mm_top_header_card_5"):
        hdr5_c1, hdr5_c2, hdr5_c3, hdr5_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr5_c1:
            title_p5 = T.get("p5_header_title", "About DocMindX AI")
            sub_p5 = T.get("p5_header_subtitle", "Architecture, system intelligence, clinical datasets, and development credits.")
            st.markdown(
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{about_icon_html}'
                f'<div style="min-width: 0; flex: 1;">'
                f'<div style="margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">{title_p5}</div>'
                f'<div style="margin-top: 4px; font-size: 0.85rem; color: var(--mm-text-secondary); line-height: 1.35;">{sub_p5}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with hdr5_c2:
            st.markdown("<div style='display: flex; justify-content: center; align-items: center; height: 38px;'><span class='mm-badge mm-badge-success' style='height: 38px; line-height: 38px; padding: 0 16px; display: inline-flex; align-items: center;'>V2.0 PRODUCTION</span></div>", unsafe_allow_html=True)
        with hdr5_c3:
            header_lang_5 = st.selectbox(
                "Header Lang Selector 5",
                options=LANG_OPTIONS,
                key="hdr_lang_p5",
                label_visibility="collapsed",
                on_change=sync_language,
                args=("hdr_lang_p5",)
            )
        with hdr5_c4:
            new_theme_p5 = theme_toggle_switch(is_dark=st.session_state.get("dark_mode", False), key="hdr_sun_moon_p5")
            if new_theme_p5 != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = new_theme_p5
                st.rerun()

    # Localized Content Dictionary for About DocMindX AI (En / Hi / Gu)
    ABOUT_TEXT = {
        "en": {
            "creator_badge": "Founder, Architect & Creator",
            "creator_name": "Developed by Daksh Vasani",
            "creator_sub": "M.Sc. Data Science Student | Python & Machine Learning Enthusiast · Gujarat, India",
            "mission_title": "Project Vision & Architecture",
            "mission_body": "DocMindX AI was conceptualized and developed by <b>Daksh Vasani</b> (M.Sc. Data Science student) to create an evidence-based, transparent, and audited AI healthcare platform. The system integrates a <b>Random Forest Disease Classifier (99.01% train accuracy, 97.8% CV)</b>, a <b>Demand Forecaster (6.53% WAPE, 0.9839 R²)</b>, an <b>Official WHO Outbreak Intelligence pipeline</b>, a <b>100+ Major Indian Diseases Knowledge Graph</b>, and <b>Multimodal Generative AI (Groq / Gemini)</b> with strict clinical provenance standards.",
            "tab_models": "AI & ML Models & Accuracy",
            "tab_diseases": "100+ Major Indian Diseases",
            "tab_datasources": "Authentic Data Sources & Live APIs",
            "tab_features": "Architecture, Security & Privacy",
            "tab_support": "Customer Support & Helpdesk",
            # Models Tab
            "ml_title": "1. Clinical Disease Prediction Model (Local Engine)",
            "ml_sub": "Scikit-Learn Random Forest Classifier trained over clinical symptom-disease bipartite matrix.",
            "stat_acc": "99.01%",
            "stat_acc_sub": "Training Accuracy (97.8% 5-Fold CV)",
            "stat_algo": "Random Forest",
            "stat_algo_sub": "50 Decision Trees (Scikit-Learn)",
            "stat_features": "280 Symptoms",
            "stat_features_sub": "Binary Indicator Features",
            "stat_classes": "101 Diseases",
            "stat_classes_sub": "WHO ICD-11 Standard Classes",
            "ml_step1": "<b>1. Feature Engineering:</b> Bipartite mappings from <code>symptoms_master.csv</code> convert patient symptom sets into 280-dimensional binary vectors.",
            "ml_step2": "<b>2. Ensemble Training:</b> 50 specialized decision trees evaluate symptom combinations with Gini impurity optimization (<code>train.py</code>).",
            "ml_step3": "<b>3. Model Serialization:</b> Pre-trained weights serialized into <code>models/disease_model.pkl</code> (5.5 MB) for instant sub-millisecond local inference.",
            "demand_title": "2. Medicine Demand Forecasting Model (HMIS Supply Chain)",
            "demand_sub": "Chronologically validated Random Forest Regressor predicting weekly institutional medicine consumption without future leakage.",
            "stat_wape": "6.53%",
            "stat_wape_sub": "Held-Out Test WAPE",
            "stat_r2": "0.9839",
            "stat_r2_sub": "R² Variance Explained",
            "stat_mae": "12.17",
            "stat_mae_sub": "Mean Absolute Error",
            "stat_rmse": "19.50",
            "stat_rmse_sub": "Root Mean Squared Error",
            "demand_step1": "<b>1. Data Ingestion:</b> 20,904 institutional consumption records from MoHFW HMIS partitioned with zero chronological leakage.",
            "demand_step2": "<b>2. Feature Lagging:</b> Rolling 4-week, 12-week consumption trends and seasonal epidemiological indices.",
            "demand_step3": "<b>3. Model File:</b> Serialized in <code>models/demand_model.pkl</code> with empirical residual uncertainty standard error (±19.50 units).",
            "stockout_title": "3. Operational Stockout Risk Engine (Honest Rule-Based Engine)",
            "stockout_sub": "Deterministic inventory risk thresholding based on days-of-stock buffer calculations.",
            "stockout_desc": "<b>Operational Decision Thresholds:</b><br/>• <b>Critical Risk:</b> Stock < 3 Days remaining (Immediate Red Flag)<br/>• <b>Urgent Risk:</b> Stock < 7 Days remaining (Priority Replenishment)<br/>• <b>Watchlist:</b> Stock < 14 Days remaining (Normal Tracking)<br/>• <b>Safe Buffer:</b> Stock ≥ 14 Days remaining (Operational Stability)<br/><i>Note: Categorized honestly as 'RULE_BASED' to eliminate misleading classification claims.</i>",
            "kg_title": "4. Clinical Knowledge Graph & Triage Engine",
            "kg_sub": "Deterministic expert system ensuring clinical safety, emergency triggers, and demographic exclusions.",
            "kg_item1": "<b>ICD-11 Bipartite Scoring:</b> Weighted matching with 1.6x multiplier for mandatory primary clinical symptoms.",
            "kg_item2": "<b>Emergency Red-Flag Protocols:</b> Instant detection of critical warning signs (e.g. chest pain with breathlessness).",
            "kg_item3": "<b>Demographic Clinical Filtering:</b> Automatic gender/age exclusions to eliminate biologically impossible diagnoses.",
            "llm_title": "5. Medical Foundation LLMs (Live AI Engine)",
            "llm_sub": "High-speed reasoning via Groq (LLaMA-3.3 70B, Qwen 27B) and Google Gemini 2.5 Flash.",
            "llm_item1": "<b>Dynamic Care Prescriptions:</b> Calculates illness-specific medicines, exact food timing ('After Food' vs 'Empty Stomach'), and course duration.",
            "llm_item2": "<b>Drug-Drug & Allergy Shield:</b> Evaluates patient ongoing medications and allergies to prevent adverse drug reactions.",
            "llm_item3": "<b>Multilingual Generation:</b> Real-time native clinical advice generation in English, Hindi, and Gujarati.",
            "ocr_title": "6. Computer Vision & Medical Document OCR",
            "ocr_sub": "Gemini Multimodal Vision API + Tesseract OCR for automated clinical entity extraction.",
            "ocr_item1": "<b>Blood Lab Report Analyzer:</b> Extracts CBC, LFT, KFT, Lipid, HbA1c values and highlights out-of-range biomarkers.",
            "ocr_item2": "<b>Prescription & Medicine Scanner:</b> Extracts drug names, dosages, and cross-references OpenFDA chemical profiles.",
            # Diseases Tab
            "dis_title": "100+ Official Major Indian Diseases Taxonomy",
            "dis_sub": "Curated clinical profiles spanning 18 official disease categories under MoHFW and WHO ICD-10/11 guidelines.",
            "dis_cat_1": "<b><img src='https://cdn-icons-png.flaticon.com/512/3888/3888124.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Cancer & Oncology:</b> Leukemia (Blood Cancer), Breast Cancer, Oral/Mouth Cancer, Lung Cancer, Cervical Cancer, Colorectal Cancer, Stomach Cancer, Liver Cancer, Prostate Cancer, Lymphoma.",
            "dis_cat_2": "<b><img src='https://cdn-icons-png.flaticon.com/512/508/508735.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Heart & Circulatory:</b> Coronary Heart Disease, Heart Attack (Myocardial Infarction), Heart Failure, Hypertension, Stroke, Peripheral Artery Disease.",
            "dis_cat_3": "<b><img src='https://cdn-icons-png.flaticon.com/512/10784/10784622.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Diabetes & Metabolic:</b> Type 1 Diabetes, Type 2 Diabetes, Gestational Diabetes, Obesity, Metabolic Syndrome, Thyroid Disorders.",
            "dis_cat_4": "<b><img src='https://cdn-icons-png.flaticon.com/512/10154/10154217.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Respiratory:</b> COPD, Asthma, Pneumonia, Tuberculosis (TB), Acute Respiratory Infections, Pulmonary Fibrosis.",
            "dis_cat_5": "<b><img src='https://cdn-icons-png.flaticon.com/512/15625/15625461.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Kidney & Renal:</b> Chronic Kidney Disease (CKD), Acute Kidney Injury (AKI), Kidney Stones, Glomerulonephritis, Polycystic Kidney Disease.",
            "dis_cat_6": "<b><img src='https://cdn-icons-png.flaticon.com/512/508/508735.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Liver & Gastrointestinal:</b> Liver Cirrhosis, Viral Hepatitis (B, C), Fatty Liver (NAFLD), GERD, Peptic Ulcer, Pancreatitis, Gallstones.",
            "dis_cat_7": "<b><img src='https://cdn-icons-png.flaticon.com/512/3286/3286097.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Neurological:</b> Epilepsy, Parkinson's Disease, Alzheimer's/Dementia, Migraine, Neuropathy.",
            "dis_cat_8": "<b><img src='https://cdn-icons-png.flaticon.com/128/13286/13286061.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Infectious & Vector-Borne:</b> Dengue Fever, Malaria, Chikungunya, Typhoid, Cholera, Japanese Encephalitis, Kala-Azar, Scrub Typhus.",
            "dis_cat_9": "<b><img src='https://cdn-icons-png.flaticon.com/512/10784/10784622.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Blood Disorders:</b> Sickle Cell Disease, Thalassemia, Iron Deficiency Anemia, Aplastic Anemia, Hemophilia.",
            "dis_cat_10": "<b><img src='https://cdn-icons-png.flaticon.com/512/9418/9418433.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Musculoskeletal & Joint:</b> Osteoarthritis, Rheumatoid Arthritis, Gout, Osteoporosis, Ankylosing Spondylitis.",
            "dis_cat_11": "<b><img src='https://cdn-icons-png.flaticon.com/512/8256/8256189.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Eye & Vision:</b> Cataract, Glaucoma, Diabetic Retinopathy, Conjunctivitis.",
            "dis_cat_12": "<b><img src='https://cdn-icons-png.flaticon.com/512/15305/15305545.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> Zoonotic & Emergency:</b> Snakebite, Rabies (Dog bite), Leptospirosis, Sepsis, Anaphylaxis.",
            # Data Sources Tab
            "sources_title": "Authentic Clinical Data Sources (Where Does the Data Come From?)",
            "sources_sub": "DocMindX AI strictly uses official, verified, and audited data sources with complete provenance traceability.",
            "src_who_title": "WHO Official Outbreak News API (DON API)",
            "src_who_desc": "Automated ingestion via official WHO Disease Outbreak News REST API (<code>https://www.who.int/api/news/diseaseoutbreaknews</code>). Ingests 100 official global events categorized into Direct India, Relevant to India, and Global Outbreaks.",
            "src_hmis_title": "MoHFW HMIS Health Facility Data (Govt. of India)",
            "src_hmis_desc": "20,904 institutional health service records from the Ministry of Health and Family Welfare, providing empirical medicine utilization and facility workload metrics.",
            "src_nfhs_title": "National Family Health Survey (NFHS-5)",
            "src_nfhs_desc": "District-level epidemiological, maternal, and nutritional indicators across 706 districts in India.",
            "src_nlem_title": "National List of Essential Medicines (NLEM 2022)",
            "src_nlem_desc": "Official Indian formulary catalog establishing 20 essential core pharmaceutical entities under Reference provenance.",
            "src_fda_title": "US FDA (OpenFDA & DailyMed)",
            "src_fda_desc": "Authentic pharmaceutical database for active chemical compounds, National Drug Codes (NDC), drug contraindications, and verified packaging metadata.",
            "src_nih_title": "NIH / NCBI & LOINC Diagnostic Reference Standards",
            "src_nih_desc": "Standard reference intervals for blood panels (CBC, Lipid, LFT, KFT, HbA1c, Thyroid) derived from peer-reviewed National Institutes of Health databases.",
            "src_gis_title": "OpenStreetMap & Healthcare Overpass API",
            "src_gis_desc": "Live spatial coordinates of registered 24/7 hospitals, trauma care centers, clinics, and pharmacies mapped via OpenStreetMap GIS.",
            "src_ayush_title": "Ayush & Evidence-Based Yoga / Physiotherapy",
            "src_ayush_desc": "Condition-specific supportive restorative yoga postures and physical therapy exercises with anatomical safety precautions and video tutorial links.",
            # Features Tab
            "feat_title": "Comprehensive Healthcare Technology Suite & Security",
            "feat_1_title": "Trilingual Clinical Portal",
            "feat_1_desc": "Full native experience in English, Hindi (हिंदी), and Gujarati (ગુજરાતી) with zero language barriers.",
            "feat_2_title": "Provenance Standards Enforcement",
            "feat_2_desc": "Every single alert card and metric carries transparent provenance tags (PROVENANCE_OBSERVED, PROVENANCE_REFERENCE, PROVENANCE_DERIVED).",
            "feat_3_title": "Strict Privacy & Zero Data Reselling",
            "feat_3_desc": "No health data is sold or stored for advertising. Assessments operate with client-side session isolation following HIPAA guidelines.",
            "feat_4_title": "Offline Resilience & Local Datasets",
            "feat_4_desc": "If cloud APIs are unreachable, local clinical datasets instantly activate to ensure uninterrupted medical guidance.",
            "feat_5_title": "AI Medical Report Analysis",
            "feat_5_desc": "Upload lab reports, prescriptions and scans — Gemini Vision AI with automated OCR extracts structured clinical insights, flags abnormal values and generates a detailed medical summary.",
            "feat_6_title": "Family Health Profiles",
            "feat_6_desc": "Manage complete medical history for up to 10 family members. Store conditions, medications, blood groups and health metrics securely under one account."
        },
        "hi": {
            "creator_badge": "संस्थापक, आर्किटेक्ट एवं निर्माता",
            "creator_name": "दक्ष वसानी (Daksh Vasani) द्वारा विकसित",
            "creator_sub": "एम.एससी. डेटा साइंस छात्र | पायथन एवं मशीन लर्निंग उत्साही · गुजरात, भारत",
            "mission_title": "प्रोजेक्ट का उद्देश्य एवं वास्तुकला (Architecture)",
            "mission_body": "DocMindX AI की परिकल्पना और विकास <b>दक्ष वसानी</b> (M.Sc. Data Science छात्र) द्वारा एक प्रामाणिक, पारदर्शी और सत्यापित AI हेल्थकेयर प्लेटफॉर्म के रूप में किया गया है। यह प्लेटफॉर्म <b>कस्टम-ट्रेन्ड रैंडम फॉरेस्ट डिजीज मॉडल (99.01% ट्रेनिंग सटीकता)</b>, <b>दवा मांग पूर्वानुमान मॉडल (6.53% WAPE, 0.9839 R²)</b>, <b>WHO आउटब्रेक API पाइपलाइन</b>, <b>भारत की 100+ प्रमुख बीमारियों का नॉलेज बेस</b>, और <b>Groq / Gemini AI</b> को जोड़ता है।",
            "tab_models": "AI एवं ML मॉडल व सटीक मैट्रिक्स",
            "tab_diseases": "भारत की 100+ प्रमुख बीमारियां",
            "tab_datasources": "प्रामाणिक डेटा स्रोत व लाइव APIs",
            "tab_features": "आर्किटेक्चर, सुरक्षा व प्राइवेसी",
            "tab_support": "ग्राहक सहायता एवं हेल्पडेस्क (Customer Support)",
            # Models Tab
            "ml_title": "1. क्लिनिकल डिजीज प्रेडिक्शन मॉडल (लोकल इंजन)",
            "ml_sub": "क्लिनिकल लक्षण-रोग मैट्रिक्स पर प्रशिक्षित Scikit-Learn रैंडम फॉरेस्ट क्लासिफायर।",
            "stat_acc": "99.01%",
            "stat_acc_sub": "ट्रेनिंग सटीकता (97.8% 5-Fold CV)",
            "stat_algo": "Random Forest",
            "stat_algo_sub": "50 डिसीजन ट्री (Scikit-Learn)",
            "stat_features": "280 लक्षण",
            "stat_features_sub": "बाइनरी इंडिकेटर फीचर्स",
            "stat_classes": "101 बीमारियाँ",
            "stat_classes_sub": "WHO ICD-11 मानक श्रेणियाँ",
            "ml_step1": "<b>1. फीचर इंजीनियरिंग:</b> <code>symptoms_master.csv</code> से मरीज के लक्षणों को 280-आयामी बाइनरी वेक्टर में बदला जाता है।",
            "ml_step2": "<b>2. एन्सेम्बल ट्रेनिंग:</b> 50 विशेषज्ञ डिसीजन ट्री गिन्नी इम्प्योरिटी ऑप्टिमाइज़ेशन के साथ लक्षणों का मूल्यांकन करते हैं (<code>train.py</code>)।",
            "ml_step3": "<b>3. मॉडल सीरियलाइज़ेशन:</b> प्रशिक्षित मॉडल <code>models/disease_model.pkl</code> (5.5 MB) में सहेजा गया है।",
            "demand_title": "2. मेडिसिन डिमांड फोरकास्टिंग मॉडल (HMIS सप्लाई चेन)",
            "demand_sub": "लीकेज-मुक्त HMIS डेटा पर प्रशिक्षित रैंडम फॉरेस्ट रिग्रेसर जो दवाओं की साप्ताहिक खपत का सटीक अनुमान लगाता है।",
            "stat_wape": "6.53%",
            "stat_wape_sub": "हेल्ड-आउट टेस्ट WAPE",
            "stat_r2": "0.9839",
            "stat_r2_sub": "R² वेरियंस स्कोर",
            "stat_mae": "12.17",
            "stat_mae_sub": "मीन एब्सोल्यूट एरर (MAE)",
            "stat_rmse": "19.50",
            "stat_rmse_sub": "रूट मीन स्क्वेयर्ड एरर",
            "demand_step1": "<b>1. डेटा इनजेशन:</b> MoHFW HMIS के 20,904 रिकॉर्ड्स से समयबद्ध विभाजन।",
            "demand_step2": "<b>2. ट्रेंड एनालिसिस:</b> 4-हफ्ते और 12-हफ्ते के रोलिंग ट्रेंड्स और मौसमी बदलावों का विश्लेषण।",
            "demand_step3": "<b>3. मॉडल फाइल:</b> <code>models/demand_model.pkl</code> में अनिश्चितता मानक त्रुटि (±19.50 यूनिट्स) के साथ सहेजा गया।",
            "stockout_title": "3. ऑपरेशनल स्टॉकाउट रिस्क इंजन (सटीक रूल-बेस्ड सिस्टम)",
            "stockout_sub": "बफर दिनों के आधार पर दवाओं की कमी का पारदर्शी और ईमानदार आकलन।",
            "stockout_desc": "<b>ऑपरेशनल सीमाएं:</b><br/>• <b>क्रिटिकल रिस्क:</b> 3 दिन से कम का स्टॉक (तुरंत रेड अलर्ट)<br/>• <b>अर्जेंट रिस्क:</b> 7 दिन से कम का स्टॉक (प्राथमिकता से आपूर्ति)<br/>• <b>वॉचलिस्ट:</b> 14 दिन से कम का स्टॉक (सामान्य निगरानी)<br/>• <b>सुरक्षित बफर:</b> 14 दिन या अधिक का स्टॉक (स्थिर स्थिति)<br/><i>पारदर्शिता: इसे पूरी ईमानदारी से 'RULE_BASED' श्रेणी में रखा गया है (कोई झूठा दावा नहीं)।</i>",
            "kg_title": "4. क्लिनिकल नॉलेज ग्राफ एवं ट्राइएज इंजन",
            "kg_sub": "क्लिनिकल सुरक्षा, आपातकालीन चेतावनी और जनसांख्यिकीय नियमों को सुनिश्चित करने वाला विशेषज्ञ सिस्टम।",
            "kg_item1": "<b>ICD-11 बाइपार्टाइट स्कोरिंग:</b> मुख्य प्राथमिक लक्षणों के लिए 1.6x गुणक के साथ भारित मिलान।",
            "kg_item2": "<b>इमरजेंसी रेड-फ्लैग प्रोटोकॉल:</b> गंभीर खतरों (जैसे सांस फूलने के साथ सीने में दर्द) की तुरंत पहचान।",
            "kg_item3": "<b>जनसांख्यिकीय क्लिनिकल फिल्टर:</b> जैविक रूप से असंभव रोगों को हटाने के लिए लिंग और आयु का स्वचालित फिल्टर।",
            "llm_title": "5. मेडिकल फाउंडेशन LLMs (लाइव AI इंजन)",
            "llm_sub": "Groq (LLaMA-3.3 70B, Qwen 27B) और Google Gemini 2.5 Flash द्वारा तेज़ तार्किक विश्लेषण।",
            "llm_item1": "<b>डायनामिक केयर प्रिस्क्रिप्शन:</b> बीमारी के अनुसार दवाइयां, भोजन का सही समय ('खाने के बाद' या 'खाली पेट') और कोर्स तय करता है।",
            "llm_item2": "<b>ड्रग इंटरेक्शन एवं एलर्जी शील्ड:</b> पुरानी दवाओं और एलर्जी से होने वाले नुकसान को रोकता है।",
            "llm_item3": "<b>त्रिभाषी जेनरेशन:</b> हिंदी, अंग्रेजी और गुजराती में सटीक मेडिकल सलाह प्रदान करता है।",
            "ocr_title": "6. कंप्यूटर विज़न एवं मेडिकल डॉक्यूमेंट OCR",
            "ocr_sub": "ब्लड रिपोर्ट और डॉक्टर पर्चियों के स्वचालित विश्लेषण के लिए Gemini Vision + Tesseract OCR।",
            "ocr_item1": "<b>ब्लड लैब रिपोर्ट विश्लेषक:</b> CBC, LFT, KFT, लिपिड, HbA1c निकालता है और असामान्य मानों को हाइलाइट करता है।",
            "ocr_item2": "<b>दवा पर्ची स्कैनर:</b> दवाओं के नाम, खुराक पढ़कर OpenFDA डेटाबेस से मिलान करता है।",
            # Diseases Tab
            "dis_title": "भारत की 100+ प्रमुख बीमारियों की आधिकारिक टैक्सोनॉमी",
            "dis_sub": "MoHFW और WHO ICD-10/11 के तहत सभी 18 प्रमुख श्रेणियों का संपूर्ण डेटाबेस।",
            "dis_cat_1": "<b><img src='https://cdn-icons-png.flaticon.com/512/3888/3888124.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> कैंसर व ऑन्कोलॉजी:</b> ब्लड कैंसर (Leukemia), स्तन कैंसर, मुख कैंसर, फेफड़ों का कैंसर, सर्वाइकल कैंसर, पेट का कैंसर, लिवर कैंसर, प्रोस्टेट कैंसर, लिम्फोमा।",
            "dis_cat_2": "<b><img src='https://cdn-icons-png.flaticon.com/512/508/508735.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> हृदय और रक्तसंचार:</b> हार्ट अटैक (Myocardial Infarction), स्ट्रोक/लकवा, उच्च रक्तचाप (Hypertension), हार्ट फेलियर।",
            "dis_cat_3": "<b><img src='https://cdn-icons-png.flaticon.com/512/10784/10784622.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> डायबिटीज व मेटाबॉलिक:</b> Type 1 व Type 2 डायबिटीज, मोटापा, थायरॉइड विकार।",
            "dis_cat_4": "<b><img src='https://cdn-icons-png.flaticon.com/512/10154/10154217.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> श्वसन रोग:</b> COPD, अस्थमा, निमोनिया, टीबी (Tuberculosis)।",
            "dis_cat_5": "<b><img src='https://cdn-icons-png.flaticon.com/512/15625/15625461.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> गुर्दा (किडनी):</b> क्रोनिक किडनी डिजीज (CKD), एक्यूट किडनी इंजरी, पथरी, डायलिसिस।",
            "dis_cat_6": "<b><img src='https://cdn-icons-png.flaticon.com/512/508/508735.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> लिवर व पाचन:</b> लिवर सिरोसिस, हेपेटाइटिस B/C, फैटी लिवर, अल्सर, पीलिया।",
            "dis_cat_7": "<b><img src='https://cdn-icons-png.flaticon.com/512/3286/3286097.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> न्यूरोलॉजिकल:</b> मिर्गी (Epilepsy), पार्किंसंस (Parkinson's), अल्जाइमर/डिमेंशिया, माइग्रेन।",
            "dis_cat_8": "<b><img src='https://cdn-icons-png.flaticon.com/128/13286/13286061.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> संक्रामक व मच्छर-जनित:</b> डेंगू (Dengue), मलेरिया (Malaria), चिकनगुनिया, टाइफाइड, हैजा, कालाजार।",
            "dis_cat_9": "<b><img src='https://cdn-icons-png.flaticon.com/512/10784/10784622.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> रक्त विकार:</b> सिकल सेल एनीमिया (Sickle Cell), थैलेसीमिया, एनीमिया, हीमोफिलिया।",
            "dis_cat_10": "<b><img src='https://cdn-icons-png.flaticon.com/512/9418/9418433.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> जोड़ व हड्डियां:</b> ऑस्टियोआर्थराइटिस, रूमेटाइड आर्थराइटिस, गाउट, ऑस्टियोपोरोसिस।",
            "dis_cat_11": "<b><img src='https://cdn-icons-png.flaticon.com/512/8256/8256189.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> आंखें:</b> मोतियाबिंद (Cataract), ग्लूकोमा, डायबिटिक रेटिनोपैथी।",
            "dis_cat_12": "<b><img src='https://cdn-icons-png.flaticon.com/512/15305/15305545.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> ज़ूनोटिक व आपातकाल:</b> सर्पदंश (Snakebite), रेबीज (Dog bite), सेप्सिस।",
            # Data Sources Tab
            "sources_title": "प्रामाणिक क्लिनिकल डेटा स्रोत (डेटा कहाँ से आता है?)",
            "sources_sub": "DocMindX AI केवल आधिकारिक, सत्यापित और सरकारी स्वास्थ्य रजिस्ट्रीयों का उपयोग करता है।",
            "src_who_title": "WHO आधिकारिक आउटब्रेक API (DON API)",
            "src_who_desc": "विश्व स्वास्थ्य संगठन (WHO) के आधिकारिक Disease Outbreak News REST API (<code>https://www.who.int/api/news/diseaseoutbreaknews</code>) से सीधे 100 प्रमाणित महामारियों का लाइव डेटा।",
            "src_hmis_title": "MoHFW HMIS स्वास्थ्य डेटा (भारत सरकार)",
            "src_hmis_desc": "स्वास्थ्य एवं परिवार कल्याण मंत्रालय के 20,904 संस्थागत रिकॉर्ड्स से प्राप्त दवाओं की वास्तविक खपत का डेटा।",
            "src_nfhs_title": "राष्ट्रीय परिवार स्वास्थ्य सर्वेक्षण (NFHS-5)",
            "src_nfhs_desc": "भारत के 706 जिलों का आधिकारिक मातृ, पोषण और स्वास्थ्य सूचकांक डेटा।",
            "src_nlem_title": "राष्ट्रीय आवश्यक दवा सूची (NLEM 2022)",
            "src_nlem_desc": "भारत सरकार द्वारा मान्यता प्राप्त 20 आवश्यक जीवनरक्षक दवाओं की आधिकारिक संदर्भ सूची।",
            "src_fda_title": "यूएस एफडीए (OpenFDA एवं DailyMed)",
            "src_fda_desc": "दवाइयों के सक्रिय रासायनिक घटक, NDC कोड, साइड-इफेक्ट्स और सत्यापित पैकेजिंग तस्वीरों के लिए आधिकारिक डेटाबेस।",
            "src_nih_title": "NIH / NCBI एवं LOINC डायग्नोस्टिक रेंज",
            "src_nih_desc": "ब्लड टेस्ट (CBC, लिपिड, LFT, KFT, HbA1c, थायरॉइड) के लिए <b>National Institutes of Health (NIH/NCBI)</b> की संदर्भ श्रेणियां।",
            "src_gis_title": "OpenStreetMap एवं हेल्थकेयर Overpass API",
            "src_gis_desc": "निकटतम 24/7 अस्पतालों, ट्रॉमा सेंटरों, क्लीनिकों और फार्मेसियों के लाइव भौगोलिक निर्देशांक।",
            "src_ayush_title": "आयुष एवं साक्ष्य-आधारित योग व फिजियोथेरेपी",
            "src_ayush_desc": "बीमारी के अनुसार सहायक रिकवरी योग आसन और फिजियोथेरेपी व्यायाम वीडियो ट्यूटोरियल लिंक के साथ।",
            # Features Tab
            "feat_title": "संपूर्ण हेल्थकेयर टेक्नोलॉजी सूट एवं सुरक्षा",
            "feat_1_title": "त्रिभाषी क्लिनिकल पोर्टल",
            "feat_1_desc": "अंग्रेजी, हिंदी (Hindi), और गुजराती (Gujarati) में सहज अनुभव।",
            "feat_2_title": "डेटा प्रोवेनेंस (Provenance) मानक",
            "feat_2_desc": "हर अलर्ट और डेटा कार्ड पर स्पष्ट टैग (PROVENANCE_OBSERVED, REFERENCE, DERIVED) दिए गए हैं।",
            "feat_3_title": "सख्त गोपनीयता एवं शून्य डेटा बिक्री",
            "feat_3_desc": "मरीजों का डेटा किसी विज्ञापनदाता को नहीं बेचा जाता। क्लाइंट-साइड सेशन आइसोलेशन।",
            "feat_4_title": "ऑफ़लाइन फ़ॉलबैक सुरक्षा जाल",
            "feat_4_desc": "इंटरनेट या API उपलब्ध न होने पर भी लोकल डेटासेट से बिना रुकावट सेवा।",
            "feat_5_title": "AI मेडिकल रिपोर्ट विश्लेषण",
            "feat_5_desc": "लैब रिपोर्ट, पर्चे और स्कैन अपलोड करें — Gemini Vision AI और स्वचालित OCR संरचित क्लिनिकल जानकारी निकालता है, असामान्य मानों को हाइलाइट करता है और विस्तृत मेडिकल सारांश तैयार करता है।",
            "feat_6_title": "परिवार स्वास्थ्य प्रोफाइल",
            "feat_6_desc": "10 परिवार सदस्यों तक का पूर्ण चिकित्सा इतिहास प्रबंधित करें। रोग, दवाएं, ब्लड ग्रुप और स्वास्थ्य डेटा सुरक्षित रूप से एक खाते में संग्रहीत करें।"
        },
        "gu": {
            "creator_badge": "સ્થાપક, આર્કિટેક્ટ અને સર્જક",
            "creator_name": "દક્ષ વસાણી (Daksh Vasani) દ્વારા નિર્મિત",
            "creator_sub": "એમ.એસસી. ડેટા સાયન્સ વિદ્યાર્થી | પાયથોન અને મશીન લર્નિંગ ઉત્સાહી · ગુજરાત, ભારત",
            "mission_title": "પ્રોજેક્ટ વિઝન અને આર્કિટેક્ચર",
            "mission_body": "DocMindX AI ની કલ્પના અને વિકાસ <b>દક્ષ વસાણી</b> (M.Sc. Data Science વિદ્યાર્થી) દ્વારા એક પારદર્શક અને ચકાસાયેલ AI હેલ્થકેર પ્લેટફોર્મ તરીકે કરવામાં આવ્યો છે. આ સિસ્ટમ <b>કસ્ટમ-ટ્રેઇન્ડ રેન્ડમ ફોરેસ્ટ ML મોડેલ (99.01% સચોટતા)</b>, <b>દવા માંગ પૂર્વાનુમાન મોડેલ (6.53% WAPE, 0.9839 R²)</b>, <b>સત્તાવાર WHO API આઉટબ્રેક ડેટા</b>, <b>ભારતના 100+ મુખ્ય રોગોનો ડેટાબેઝ</b>, અને <b>Groq / Gemini AI</b> ને જોડે છે.",
            "tab_models": "AI અને ML મોડેલ્સ અને સચોટતા",
            "tab_diseases": "ભારતના 100+ મુખ્ય રોગો",
            "tab_datasources": "અધિકૃત ડેટા સ્ત્રોતો અને Live APIs",
            "tab_features": "આર્કિટેક્ચર, સુરક્ષા અને પ્રાઇવસી",
            "tab_support": "ગ્રાહક સહાય અને હેલ્પડેસ્ક (Customer Support)",
            # Models Tab
            "ml_title": "1. ક્લિનિકલ રોગ અનુમાન મોડેલ (લોકલ એન્જિન)",
            "ml_sub": "ક્લિનિકલ લક્ષણ-રોગ મેટ્રિક્સ પર પ્રશિક્ષિત Scikit-Learn રેન્ડમ ફોરેસ્ટ ક્લાસિફાયર.",
            "stat_acc": "99.01%",
            "stat_acc_sub": "તાલીમ સચોટતા (97.8% 5-Fold CV)",
            "stat_algo": "Random Forest",
            "stat_algo_sub": "50 ડિસિઝન ટ્રી (Scikit-Learn)",
            "stat_features": "280 લક્ષણો",
            "stat_features_sub": "બાઈનરી ઇન્ડિકેટર ફીચર્સ",
            "stat_classes": "101 રોગો",
            "stat_classes_sub": "WHO ICD-11 માનક શ્રેણીઓ",
            "ml_step1": "<b>1. ફીચર એન્જિનિયરિંગ:</b> <code>symptoms_master.csv</code> માંથી દર્દીના લક્ષણોને 280-પરિમાણીય બાઈનરી વેક્ટરમાં રૂપાંતરિત કરવામાં આવે છે.",
            "ml_step2": "<b>2. એન્સેમ્બલ ટ્રેનિંગ:</b> 50 વિશેષ ડિસિઝન ટ્રી ગિની ઇમ્પ્યોરિટી ઑપ્ટિમાઇઝેશન સાથે લક્ષણોનું વિશ્લેષણ કરે છે (<code>train.py</code>).",
            "ml_step3": "<b>3. મોડેલ સિરિયલાઇઝેશન:</b> પ્રશિક્ષિત મોડેલ <code>models/disease_model.pkl</code> (5.5 MB) માં સંગ્રહિત છે.",
            "demand_title": "2. દવા માંગ પૂર્વાનુમાન મોડેલ (HMIS સપ્લાય ચેઇન)",
            "demand_sub": "સમયસર ડેટા વિભાજન સાથે દવાઓની સાપ્તાહિક જરૂરિયાતનું સચોટ અનુમાન.",
            "stat_wape": "6.53%",
            "stat_wape_sub": "ટેસ્ટ સેટ WAPE",
            "stat_r2": "0.9839",
            "stat_r2_sub": "R² વેરિઅન્સ સ્કોર",
            "stat_mae": "12.17",
            "stat_mae_sub": "મીન એબ્સોલ્યુટ એરર",
            "stat_rmse": "19.50",
            "stat_rmse_sub": "રૂટ મીન સ્ક્વેર્ડ એરર",
            "demand_step1": "<b>1. ડેટા ઇન્જેશન:</b> MoHFW HMIS ના 20,904 અધિકૃત રેકોર્ડ્સમાંથી વિશ્લેષણ.",
            "demand_step2": "<b>2. ટ્રેન્ડ એનાલિસિસ:</b> 4-અઠવાડિયા અને 12-અઠવાડિયાના રોલિંગ ટ્રેન્ડ્સનું આકલન.",
            "demand_step3": "<b>3. મોડેલ ફાઇલ:</b> <code>models/demand_model.pkl</code> માં અનિશ્ચિતતા સ્ટાન્ડર્ડ એરર (±19.50) સાથે સુરક્ષિત.",
            "stockout_title": "3. ઓપરેશનલ સ્ટોકઆઉટ રિસ્ક એન્જિન (રૂલ-બેઝ્ડ સિસ્ટમ)",
            "stockout_sub": "સ્ટોકના બાકી દિવસોના આધારે પારદર્શક ચેતવણી પ્રણાલી.",
            "stockout_desc": "<b>ઓપરેશનલ મર્યાદાઓ:</b><br/>• <b>ક્રિટિકલ રિસ્ક:</b> 3 દિવસથી ઓછો સ્ટોક (તાત્કાલિક લાલ ચેતવણી)<br/>• <b>અર્જન્ટ રિસ્ક:</b> 7 દિવસથી ઓછો સ્ટોક (પ્રાથમિકતા પુરવઠો)<br/>• <b>વોચલિસ્ટ:</b> 14 દિવસથી ઓછો સ્ટોક (સામાન્ય ટ્રેકિંગ)<br/>• <b>સલામત બફર:</b> 14 દિવસ કે તેથી વધુ સ્ટોક (સ્થિર પરિસ્થિતિ)<br/><i>નોંધ: સંપૂર્ણ પારદર્શિતા માટે તેને 'RULE_BASED' તરીકે વર્ગીકૃત કરવામાં આવ્યું છે.</i>",
            "kg_title": "4. ક્લિનિકલ નોલેજ ગ્રાફ અને ટ્રાયેજ એન્જિન",
            "kg_sub": "ક્લિનિકલ સલામતી, કટોકટીની ચેતવણીઓ અને વસ્તી વિષયક નિયમો સુનિશ્ચિત કરતી સિસ્ટમ.",
            "kg_item1": "<b>ICD-11 બાયપાર્ટાઇટ સ્કોરિંગ:</b> મુખ્ય પ્રાથમિક લક્ષણો માટે 1.6x ગુણક સાથે મેચિંગ.",
            "kg_item2": "<b>ઇમરજન્સી રેડ-ફ્લેગ પ્રોટોકોલ:</b> ગંભીર જોખમો (જેમ કે શ્વાસ ચડવો અને છાતીમાં દુખાવો) ની તાત્કાલિક ઓળખ.",
            "kg_item3": "<b>વસ્તી વિષયક ક્લિનિકલ ફિલ્ટર:</b> જૈવિક રીતે અસંભવિત રોગોને દૂર કરવા માટે લિંગ અને વયનું ફિલ્ટર.",
            "llm_title": "5. મેડિકલ ફાઉન્ડેશન LLMs (લાઇવ AI એન્જિન)",
            "llm_sub": "Groq (LLaMA-3.3 70B, Qwen 27B) અને Google Gemini 2.5 Flash દ્વારા ઝડપી તાર્કિક વિશ્લેષણ.",
            "llm_item1": "<b>ડાયનેમિક કેર પ્રિસ્ક્રિપ્શન:</b> રોગ મુજબ દવાઓ, જમવાનો યોગ્ય સમય ('જમ્યા પછી' કે 'ખાલી પેટે') અને દિવસો નક્કી કરે છે.",
            "llm_item2": "<b>ડ્રગ ઇન્ટરેક્શન અને એલર્જી શીલ્ડ:</b> જૂની દવાઓ અને એલર્જીથી થતા નુકસાનને અટકાવે છે.",
            "llm_item3": "<b>ત્રિભાષી જનરેશન:</b> ગુજરાતી, હિન્દી અને અંગ્રેજીમાં સચોટ તબીબી સલાહ પ્રદાન કરે છે.",
            "ocr_title": "6. કમ્પ્યુટર વિઝન અને મેડિકલ ડોક્યુમેન્ટ OCR",
            "ocr_sub": "બ્લડ રિપોર્ટ અને ડૉક્ટરની પ્રિસ્ક્રિપ્શનના વિશ્લેષણ માટે Gemini Vision + Tesseract OCR.",
            "ocr_item1": "<b>બ્લડ લેબ રિપોર્ટ વિશ્લેષક:</b> CBC, LFT, KFT, લિપિડ, HbA1c ચકાસીને અસામાન્ય પરિણામો દર્શાવે છે.",
            "ocr_item2": "<b>દવા પ્રિસ્ક્રિપ્શન સ્કેનર:</b> દવાઓના નામ, ડોઝ વાંચીને OpenFDA ડેટાબેઝ સાથે સરખાવે છે.",
            # Diseases Tab
            "dis_title": "ભારતના 100+ મુખ્ય રોગોની સત્તાવાર ટેક્સોનોમી",
            "dis_sub": "MoHFW અને WHO ICD-10/11 હેઠળ તમામ 18 શ્રેણીઓનો વ્યાપક ડેટાબેઝ.",
            "dis_cat_1": "<b><img src='https://cdn-icons-png.flaticon.com/512/3888/3888124.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> કેન્સર અને ઓન્કોલોજી:</b> બ્લડ કેન્સર (Leukemia), સ્તન કેન્સર, મુખનું કેન્સર, ફેફસાંનું કેન્સર, સર્વાઇકલ કેન્સર, પેટનું કેન્સર, લિવર કેન્સર, પ્રોસ્ટેટ કેન્સર, લિમ્ફોમા.",
            "dis_cat_2": "<b><img src='https://cdn-icons-png.flaticon.com/512/508/508735.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> હૃદય અને રક્તસંચાર:</b> હાર્ટ એટેક (Myocardial Infarction), સ્ટ્રોક/લકવો, હાઈ બ્લડ પ્રેશર (Hypertension), હાર્ટ ફેલિયર.",
            "dis_cat_3": "<b><img src='https://cdn-icons-png.flaticon.com/512/10784/10784622.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> ડાયાબિટીસ અને મેટાબોલિક:</b> Type 1 અને Type 2 ડાયાબિટીસ, મેદસ્વીતા, થાઇરોઇડ સમસ્યાઓ.",
            "dis_cat_4": "<b><img src='https://cdn-icons-png.flaticon.com/512/10154/10154217.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> શ્વસનતંત્રના રોગો:</b> COPD, અસ્થમા, ન્યુમોનિયા, ટીબી (Tuberculosis).",
            "dis_cat_5": "<b><img src='https://cdn-icons-png.flaticon.com/512/15625/15625461.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> કિડની અને મૂત્રપિંડ:</b> ક્રોનિક કિડની ડિસીઝ (CKD), કિડની ફેલિયર, પથરી, ડાયાલિસિસ.",
            "dis_cat_6": "<b><img src='https://cdn-icons-png.flaticon.com/512/508/508735.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> લિવર અને પાચનતંત્ર:</b> લિવર સિરોસિસ, હેપેટાઇટિસ B/C, ફેટી લિવર, અલ્સર, કમળો.",
            "dis_cat_7": "<b><img src='https://cdn-icons-png.flaticon.com/512/3286/3286097.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> ન્યુરોલોજીકલ:</b> વાઈ/ખેંચ (Epilepsy), પાર્કિન્સન (Parkinson's), ડિમેન્શિયા, આધાશીશી (Migraine).",
            "dis_cat_8": "<b><img src='https://cdn-icons-png.flaticon.com/128/13286/13286061.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> ચેપી અને મચ્છરજન્ય:</b> ડેન્ગ્યુ (Dengue), મેલેરિયા (Malaria), ચિકનગુનિયા, ટાઇફોઇડ, કોલેરા.",
            "dis_cat_9": "<b><img src='https://cdn-icons-png.flaticon.com/512/10784/10784622.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> રક્ત વિકૃતિઓ:</b> સિકલ સેલ એનિમિયા (Sickle Cell), થેલેસેમિયા, એનિમિયા, હિમોફિલિયા.",
            "dis_cat_10": "<b><img src='https://cdn-icons-png.flaticon.com/512/9418/9418433.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> સાંધા અને હાડકાં:</b> ઓસ્ટિઓઆર્થરાઇટિસ, સંધિવા (Rheumatoid Arthritis), ગાઉટ, ઓસ્ટિઓપોરોસિસ.",
            "dis_cat_11": "<b><img src='https://cdn-icons-png.flaticon.com/512/8256/8256189.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> આંખો:</b> મોતિયો (Cataract), ગ્લુકોમા, ડાયાબિટીક રેટિનોપેથી.",
            "dis_cat_12": "<b><img src='https://cdn-icons-png.flaticon.com/512/15305/15305545.png' style='width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;' /> ઝૂનોટિક અને ઈમરજન્સી:</b> સાપ કરડવો (Snakebite), હડકવા (Dog bite), સેપ્સિસ.",
            # Data Sources Tab
            "sources_title": "પ્રમાણિક ક્લિનિકલ ડેટા સ્ત્રોત (ડેટા ક્યાંથી આવે છે?)",
            "sources_sub": "DocMindX AI માત્ર અધિકૃત, ચકાસાયેલ અને સરકારી આરોગ્ય રજિસ્ટ્રીઝનો ઉપયોગ કરે છે.",
            "src_who_title": "WHO સત્તાવાર આઉટબ્રેક API (DON API)",
            "src_who_desc": "વિશ્વ આરોગ્ય સંસ્થા (WHO) ના સત્તાવાર Disease Outbreak News REST API (<code>https://www.who.int/api/news/diseaseoutbreaknews</code>) દ્વારા 100 પ્રમાણિત રોગચાળાની લાઇવ માહિતી.",
            "src_hmis_title": "MoHFW HMIS આરોગ્ય સુવિધા ડેટા (ભારત સરકાર)",
            "src_hmis_desc": "ભારત સરકારના આરોગ્ય મંત્રાલયના 20,904 સંસ્થાકીય રેકોર્ડ્સમાંથી દવાઓના વાસ્તવિક વપરાશનો ડેટા.",
            "src_nfhs_title": "રાષ્ટ્રીય પરિવાર આરોગ્ય સર્વેક્ષણ (NFHS-5)",
            "src_nfhs_desc": "ભારતના 706 જિલ્લાઓનો અધિકૃત રોગચાળો, માતૃત્વ અને પોષણ સૂચકાંક ડેટા.",
            "src_nlem_title": "રાષ્ટ્રીય આવશ્યક દવાઓની યાદી (NLEM 2022)",
            "src_nlem_desc": "ભારત સરકાર દ્વારા માન્યતા પ્રાપ્ત 20 આવશ્યક જીવનરક્ષક દવાઓની અધિકૃત યાદી.",
            "src_fda_title": "યુએસ એફડીએ (OpenFDA અને DailyMed)",
            "src_fda_desc": "દવાઓના રાસાયણિક ઘટકો, NDC કોડ, આડઅસરો અને ચકાસાયેલ પેકેજિંગ ફોટા માટે અધિકૃત ડેટાબેઝ.",
            "src_nih_title": "NIH / NCBI અને LOINC ડાયગ્નોસ્ટિક રેન્જ",
            "src_nih_desc": "બ્લડ ટેસ્ટ (CBC, લિપિડ, LFT, KFT, HbA1c, થાઇરોઇડ) માટે <b>National Institutes of Health (NIH/NCBI)</b> ની સંદર્ભ શ્રેણીઓ.",
            "src_gis_title": "OpenStreetMap અને હેલ્થકેર Overpass API",
            "src_gis_desc": "નજીકની 24/7 હોસ્પિટલો, ટ્રોમા કેન્દ્રો, ક્લિનિક્સ અને ફાર્મસીઓના લાઇવ ભૌગોલિક નિર્દેશાંક.",
            "src_ayush_title": "આયુષ અને પુરાવા-આધારિત યોગ અને ફિઝિયોથેરાપી",
            "src_ayush_desc": "રોગ મુજબ સહાયક પુનઃપ્રાપ્તિ યોગ આસનો અને ફિઝિયોથેરાપી કસરતો વિડિયો ટ્યુટોરીયલ લિંક્સ સાથે.",
            # Features Tab
            "feat_title": "સંપૂર્ણ હેલ્થકેર ટેકનોલોજી સ્યુટ અને સુરક્ષા",
            "feat_1_title": "ત્રિભાષી ક્લિનિકલ પોર્ટલ",
            "feat_1_desc": "ગુજરાતી (Gujarati), હિન્દી (Hindi), અને અંગ્રેજી (English) માં સરળ અનુભવ.",
            "feat_2_title": "ડેટા પ્રોવેનન્સ સ્ટાન્ડર્ડ્સ",
            "feat_2_desc": "દરેક ચેતવણી અને ડેટા કાર્ડ પર સ્પષ્ટ ટૅગ્સ (PROVENANCE_OBSERVED, REFERENCE, DERIVED) પ્રદર્શિત થાય છે.",
            "feat_3_title": "સખત ગોપનીયતા અને શૂન્ય ડેટા વેચાણ",
            "feat_3_desc": "દર્દીઓનો ડેટા કોઈ જાહેરાતકર્તાને વેચવામાં આવતો નથી. સંપૂર્ણ તબીબી ગોપનીયતા.",
            "feat_4_title": "ઑફલાઇન ફોલબેક સુરક્ષા કવચ",
            "feat_4_desc": "ઇન્ટરનેટ કે API ઉપલબ્ધ ન હોય ત્યારે પણ લોકલ ડેટાસેટથી અવિરત સેવા.",
            "feat_5_title": "AI મેડિકલ રિપોર્ટ વિશ્લેષણ",
            "feat_5_desc": "લૅબ રિપોર્ટ, પ્રિસ્ક્રિપ્શન અને સ્કૅન અપલોડ કરો — Gemini Vision AI અને સ્વચાલિત OCR માળખાગત ક્લિનિકલ માહિતી કાઢે છે, અસાધારણ મૂલ્યો ચિહ્નિત કરે છે અને વિગતવાર મેડિકલ સારાંશ બનાવે છે.",
            "feat_6_title": "કુટુંબ આરોગ્ય પ્રોફાઇલ",
            "feat_6_desc": "10 કુટુંબ સભ્યો સુધીનો સંપૂર્ણ તબીબી ઇતિહાસ સંચાલિત કરો. રોગ, દવા, બ્લડ ગ્રૂપ અને આરોગ્ય ડેટા એક જ ખાતા હેઠળ સુરક્ષિત રીતે સ્ટોર કરો."
        }
    }
    
    A = ABOUT_TEXT.get(lang_code, ABOUT_TEXT["en"])

    # Multilingual labels for badges, tooltips and callout boxes
    ABOUT_LABELS = {
        "en": {
            "trained_val": "Trained & Validated",
            "time_series": "Time Series + ML",
            "risk_detect": "Risk Detection",
            "knowledge_base": "Knowledge Base",
            "generative_ai": "Generative AI",
            "vision_ai": "Computer Vision",
            "fast_reliable": "Fast, accurate and reliable local prediction engine",
            "ensure_stock": "Helps ensure medicine availability and reduce stockouts",
            "prevent_stockouts": "Prevent stockouts & ensure continuity",
            "safe_triage": "Evidence-based & safe triage",
            "natural_advice": "Natural, safe & personalized advice",
            "automated_ocr": "Automated clinical report analysis",
            "quote": "AI for Accessible, Accurate and Equitable Healthcare for Everyone.",
            "quote_author": "— Daksh Vasani",
            "doc_btn": "View Project Documentation",
            "official_cats_sub": "Official Categories",
            "major_diseases_sub": "Major Indian Diseases",
            "who_compliant_sub": "WHO ICD-10/11 Compliant Taxonomy",
            "accuracy_lbl": "ACCURACY",
            # Tab 3 Data Source button labels
            "btn_view_api_doc": "View API Documentation",
            "btn_view_govt_data": "View Government Data",
            "btn_view_district_data": "View District Data",
            "btn_view_nlem_cat": "View NLEM Catalog",
            "btn_browse_fda": "Browse FDA Data",
            "btn_view_ref_standards": "View Reference Standards",
            "btn_explore_location": "Explore Location Data",
            "btn_view_guidelines": "View Practices & Guidelines",
            # Tab 4 Feature tags
            "tag_feat_1": "Multilingual • Accessible • Inclusive",
            "tag_feat_2": "Transparent • Auditable • Reliable",
            "tag_feat_3": "Private • Secure • HIPAA Compliant",
            "tag_feat_4": "Always Available • Reliable • Patient-First",
            "suite_sub": "Empowering a secure, accessible and resilient healthcare ecosystem.",
            "secure_hc": "Secure Healthcare",
            "smarter_tom": "Smarter Tomorrow",
            "trusted_data": "Trusted Data. Better Care.",
        },
        "hi": {
            "trained_val": "प्रशिक्षित एवं सत्यापित",
            "time_series": "टाइम सीरीज + ML",
            "risk_detect": "जोखिम पहचान",
            "knowledge_base": "नॉलेज बेस",
            "generative_ai": "जनरेटिव AI",
            "vision_ai": "कंप्यूटर विज़न",
            "fast_reliable": "तेज़, सटीक एवं विश्वसनीय लोकल प्रेडिक्शन इंजन",
            "ensure_stock": "दवा उपलब्धता सुनिश्चित एवं कमी को कम करता है",
            "prevent_stockouts": "दवाओं की कमी रोकें और आपूर्ति बनाए रखें",
            "safe_triage": "साक्ष्य-आधारित एवं सुरक्षित ट्राइएज",
            "natural_advice": "स्वाभाविक, सुरक्षित एवं व्यक्तिगत सलाह",
            "automated_ocr": "स्वचालित क्लिनिकल रिपोर्ट विश्लेषण",
            "quote": "सुलभ, सटीक और निष्पक्ष स्वास्थ्य सेवा सभी के लिए।",
            "quote_author": "— दक्ष वसानी",
            "doc_btn": "प्रोजेक्ट डॉक्यूमेंटेशन देखें",
            "official_cats_sub": "आधिकारिक श्रेणियां",
            "major_diseases_sub": "प्रमुख भारतीय बीमारियां",
            "who_compliant_sub": "WHO ICD-10/11 अनुपालक टैक्सोनॉमी",
            "accuracy_lbl": "सटीकता",
            # Tab 3 Data Source button labels
            "btn_view_api_doc": "API दस्तावेज़ देखें",
            "btn_view_govt_data": "सरकारी डेटा देखें",
            "btn_view_district_data": "ज़िला-स्तरीय डेटा देखें",
            "btn_view_nlem_cat": "NLEM कैटलॉग देखें",
            "btn_browse_fda": "FDA डेटा ब्राउज़ करें",
            "btn_view_ref_standards": "रेफरेंस मानक देखें",
            "btn_explore_location": "लोकेशन डेटा एक्सप्लोर करें",
            "btn_view_guidelines": "दिशानिर्देश व पद्धतियाँ देखें",
            # Tab 4 Feature tags
            "tag_feat_1": "त्रिभाषी • सुलभ • समावेशी",
            "tag_feat_2": "पारदर्शी • ऑडिट योग्य • विश्वसनीय",
            "tag_feat_3": "निजी • सुरक्षित • HIPAA अनुपालन",
            "tag_feat_4": "सदैव उपलब्ध • विश्वसनीय • मरीज-प्रथम",
            "suite_sub": "एक सुरक्षित, सुलभ और सशक्त स्वास्थ्य सेवा तंत्र का निर्माण।",
            "secure_hc": "सुरक्षित स्वास्थ्य सेवा",
            "smarter_tom": "बेहतर भविष्य",
            "trusted_data": "विश्वसनीय डेटा, बेहतर देखभाल।",
        },
        "gu": {
            "trained_val": "પ્રશિક્ષિત અને પ્રમાણિત",
            "time_series": "ટાઇમ સિરીઝ + ML",
            "risk_detect": "જોખમ શોધ",
            "knowledge_base": "નોલેજ બેઝ",
            "generative_ai": "જનરેટિવ AI",
            "vision_ai": "કમ્પ્યુટર વિઝન",
            "fast_reliable": "ઝડપી, સચોટ અને વિશ્વસનીય સ્થાનિક અનુમાન એન્જિન",
            "ensure_stock": "દવાની ઉપલબ્ધતા સુનિશ્ચિત કરે છે અને અછત ઘટાડે છે",
            "prevent_stockouts": "દવાની અછત અટકાવો અને પુરવઠો જાળવો",
            "safe_triage": "પુરાવા-આધારિત અને સુરક્ષિત ટ્રાયેજ",
            "natural_advice": "કુદરતી, સુરક્ષિત અને વ્યક્તિગત સલાહ",
            "automated_ocr": "સ્વચાલિત ક્લિનિકલ રિપોર્ટ વિશ્લેષણ",
            "quote": "દરેક માટે સુલભ, સચોટ અને સમાન આરોગ્ય સેવા.",
            "quote_author": "— દક્ષ વસાણી",
            "doc_btn": "પ્રોજેક્ટ દસ્તાવેજીકરણ જુઓ",
            "official_cats_sub": "સત્તાવાર શ્રેણીઓ",
            "major_diseases_sub": "મુખ્ય ભારતીય રોગો",
            "who_compliant_sub": "WHO ICD-10/11 સુસંગત ટેક્સોનોમી",
            "accuracy_lbl": "સચોટતા",
            # Tab 3 Data Source button labels
            "btn_view_api_doc": "API દસ્તાવેજ જુઓ",
            "btn_view_govt_data": "સરકારી ડેટા જુઓ",
            "btn_view_district_data": "જિલ્લા ડેટા જુઓ",
            "btn_view_nlem_cat": "NLEM કેટલોગ જુઓ",
            "btn_browse_fda": "FDA ડેટા બ્રાઉઝ કરો",
            "btn_view_ref_standards": "સંદર્ભ માપદંડો જુઓ",
            "btn_explore_location": "સ્થાન ડેટા જુઓ",
            "btn_view_guidelines": "માર્ગદર્શિકા જુઓ",
            # Tab 4 Feature tags
            "tag_feat_1": "ત્રિભાષી • સુલભ • સમાવેશી",
            "tag_feat_2": "પારદર્શક • ઓડિટ યોગ્ય • વિશ્વસનીય",
            "tag_feat_3": "ખાનગી • સુરક્ષિત • HIPAA સુસંગત",
            "tag_feat_4": "હંમેશા ઉપલબ્ધ • વિશ્વસનીય • દર્દી-પ્રથમ",
            "suite_sub": "એક સુરક્ષિત, સુલભ અને સક્ષમ હેલ્થકેર સિસ્ટમનું નિર્માણ.",
            "secure_hc": "સુરક્ષિત આરોગ્ય સેવા",
            "smarter_tom": "ઉજ્જવળ ભવિષ્ય",
            "trusted_data": "વિશ્વસનીય ડેટા, બહેતર સારવાર.",
        }
    }
    L = ABOUT_LABELS.get(lang_code, ABOUT_LABELS["en"])

    def _strip_num(s):
        import re
        return re.sub(r'^\d+\.\s*', '', s).strip()

    def _parse_dis_cat(raw_html):
        import re
        clean = re.sub(r'<img[^>]*>', '', raw_html).strip()
        m = re.match(r'<b>(.*?)[:：]?</b>\s*[:：]?\s*(.*)', clean, re.DOTALL)
        if m:
            return m.group(1).strip().rstrip(':'), m.group(2).strip()
        parts = clean.split(':', 1)
        if len(parts) == 2:
            return re.sub(r'<[^>]+>', '', parts[0]).strip(), parts[1].strip()
        return clean, ""

    def _format_stockout_bullets(desc):
        import re
        def repl(match):
            term = match.group(1)
            lower = term.lower()
            color = "#3B82F6"
            if any(k in lower for k in ["critical", "क्रिटिकल", "ક્રિટિકલ"]):
                color = "#EF4444"
            elif any(k in lower for k in ["urgent", "अर्जेंट", "અર્જન્ટ"]):
                color = "#F97316"
            elif any(k in lower for k in ["safe", "सुरक्षित", "સલામત"]):
                color = "#10B981"
            return f'<span style="display: inline-flex; align-items: center; gap: 7px;"><span style="width: 8px; height: 8px; border-radius: 50%; background: {color}; flex-shrink: 0; display: inline-block;"></span><b>{term}</b></span>'
        return re.sub(r'•\s*<b>(.*?)</b>', repl, desc)

    blue_check_svg = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10" fill="#2563EB"/><path d="M8 12.5l2.5 2.5L16 9.5" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    chevron_right_svg = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'

    # 1. Creator & Mission Banner Card
    st.markdown(f"""
    <div class="mm-card" style="border: 1px solid var(--mm-border-color); border-radius: 16px; padding: 22px 24px; margin-bottom: 18px; background: var(--mm-card-bg); box-shadow: 0 4px 20px rgba(0,0,0,0.03);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
            <div style="display: flex; align-items: flex-start; gap: 16px; flex: 1 1 450px;">
                <div style="width: 52px; height: 52px; border-radius: 14px; background: #EFF6FF; border: 1.5px solid #DBEAFE; display: flex; align-items: center; justify-content: center; color: #2563EB; flex-shrink: 0; box-shadow: 0 2px 8px rgba(37,99,235,0.12);">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3z M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82z"/></svg>
                </div>
                <div>
                    <div style="font-size: 0.72rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px;">
                        {A['creator_badge']}
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">
                        {A['creator_name']}
                    </div>
                    <div style="font-size: 0.83rem; color: var(--mm-text-secondary); margin-top: 3px;">
                        {A['creator_sub']}
                    </div>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 10px;">
                        <span class="mm-badge" style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); color: #DC2626; font-size: 0.74rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">
                            <span style="display: inline-block; width: 14px; height: 10px; border-radius: 2px; background: linear-gradient(180deg, #FF9933 33%, #FFFFFF 33%, #FFFFFF 66%, #128807 66%); border: 1px solid rgba(0,0,0,0.15);"></span>
                            MADE IN INDIA
                        </span>
                        <span class="mm-badge" style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); color: #059669; font-size: 0.74rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 5px;">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                            DISEASE ML 99.01%
                        </span>
                        <span class="mm-badge" style="background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.3); color: #2563EB; font-size: 0.74rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 5px;">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                            DEMAND WAPE 6.53%
                        </span>
                        <span class="mm-badge" style="background: rgba(147, 51, 234, 0.08); border: 1px solid rgba(147, 51, 234, 0.3); color: #9333EA; font-size: 0.74rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 5px;">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                            WHO DATA ACTIVE
                        </span>
                    </div>
                </div>
            </div>
            <div style="background: rgba(37, 99, 235, 0.04); border: 1px solid rgba(37, 99, 235, 0.15); border-radius: 12px; padding: 12px 16px; min-width: 240px; max-width: 320px; flex: 1 1 auto;">
                <div style="display: flex; align-items: flex-start; gap: 8px;">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="#3B82F6" style="flex-shrink: 0; margin-top: 1px;"><path d="M6 17h3l2-4V7H5v6h3zm8 0h3l2-4V7h-6v6h3z"/></svg>
                    <div>
                        <div style="font-size: 0.80rem; font-style: italic; color: var(--mm-text-primary); line-height: 1.45;">
                            "{L['quote']}"
                        </div>
                        <div style="font-size: 0.74rem; font-weight: 700; color: #2563EB; margin-top: 4px; text-align: right;">
                            {L['quote_author']}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px dashed var(--mm-border-color);">
            <p style="font-size: 0.84rem; color: var(--mm-text-secondary); line-height: 1.6; margin: 0; flex: 1 1 500px;">
                <b>{A['mission_title']}:</b> {A['mission_body']}
            </p>
            <a href="https://github.com/VASANI007/DocMindX-AI" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.76rem; font-weight: 700; color: #2563EB; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 8px; padding: 6px 12px; text-decoration: none;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                {L['doc_btn']}
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Main About Tabs (5 Comprehensive Tabs including Official Support)
    tab_a1, tab_a2, tab_a3, tab_a4, tab_a5 = st.tabs([
        A["tab_models"],
        A["tab_diseases"],
        A["tab_datasources"],
        A["tab_features"],
        A.get("tab_support", "Customer Support & Helpdesk")
    ])

    # ==================== TAB 1: AI & ML MODELS & ACCURACY ====================
    with tab_a1:
        # Card 1: Custom Trained Disease ML Model
        st.markdown(f"""
        <div class="mm-card" style="border: 1px solid var(--mm-border-color); border-radius: 14px; padding: 20px 22px; margin-bottom: 16px; background: var(--mm-card-bg);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <span style="width: 24px; height: 24px; border-radius: 50%; background: #EF4444; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.78rem; flex-shrink: 0;">1</span>
                    <b style="font-size: 1.10rem; color: var(--mm-text-primary);">{_strip_num(A['ml_title'])}</b>
                    <span style="background: rgba(16, 185, 129, 0.1); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 14px; font-size: 0.72rem; font-weight: 700; padding: 2px 10px;">{L['trained_val']}</span>
                </div>
                <span class="mm-badge" style="background: rgba(16, 185, 129, 0.1); border: 1.5px solid rgba(16, 185, 129, 0.4); color: #059669; font-size: 0.78rem; font-weight: 800; padding: 5px 14px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                    {L['accuracy_lbl']}: {A['stat_acc']}
                </span>
            </div>
            <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 0 0 14px 0;">{A['ml_sub']}</p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 12px 0 14px 0;">
                <div style="background: rgba(16, 185, 129, 0.06); border: 1.5px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #10B981; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/></svg>
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #10B981;">{A['stat_acc']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_acc_sub']}</div>
                </div>
                <div style="background: rgba(59, 130, 246, 0.06); border: 1.5px solid rgba(59, 130, 246, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #3B82F6; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="5" r="3"/><circle cx="6" cy="19" r="3"/><circle cx="18" cy="19" r="3"/><path d="M12 8v4m0 0l-6 4m6-4l6 4"/></svg>
                    </div>
                    <div style="font-size: 1.08rem; font-weight: 800; color: #3B82F6; margin-top: 4px;">{A['stat_algo']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_algo_sub']}</div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.06); border: 1.5px solid rgba(245, 158, 11, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #F59E0B; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #F59E0B;">{A['stat_features']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_features_sub']}</div>
                </div>
                <div style="background: rgba(168, 85, 247, 0.06); border: 1.5px solid rgba(168, 85, 247, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #A855F7; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #A855F7;">{A['stat_classes']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_classes_sub']}</div>
                </div>
            </div>
            <div style="display: flex; gap: 14px; flex-wrap: wrap; align-items: stretch; margin-top: 14px;">
                <div style="flex: 1 1 520px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 10px; padding: 12px 16px; font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.6;">
                    <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                        {blue_check_svg}
                        <div>{A['ml_step1']}</div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                        {blue_check_svg}
                        <div>{A['ml_step2']}</div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 8px;">
                        {blue_check_svg}
                        <div>{A['ml_step3']}</div>
                    </div>
                </div>
                <div style="flex: 0 1 230px; min-width: 190px; background: rgba(59, 130, 246, 0.05); border: 1.5px solid rgba(59, 130, 246, 0.25); border-radius: 10px; padding: 14px; display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #EFF6FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-5.04z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-5.04z"/></svg>
                    </div>
                    <div style="font-size: 0.78rem; font-weight: 600; color: #2563EB; line-height: 1.35;">
                        {L['fast_reliable']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card 2: Medicine Demand Forecasting Model (HMIS Supply Chain)
        st.markdown(f"""
        <div class="mm-card" style="border: 1px solid var(--mm-border-color); border-radius: 14px; padding: 20px 22px; margin-bottom: 16px; background: var(--mm-card-bg);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <span style="width: 24px; height: 24px; border-radius: 50%; background: #EF4444; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.78rem; flex-shrink: 0;">2</span>
                    <b style="font-size: 1.10rem; color: var(--mm-text-primary);">{_strip_num(A['demand_title'])}</b>
                    <span style="background: rgba(59, 130, 246, 0.1); color: #2563EB; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 14px; font-size: 0.72rem; font-weight: 700; padding: 2px 10px;">{L['time_series']}</span>
                </div>
                <span class="mm-badge" style="background: rgba(59, 130, 246, 0.1); border: 1.5px solid rgba(59, 130, 246, 0.4); color: #2563EB; font-size: 0.78rem; font-weight: 800; padding: 5px 14px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                    WAPE: {A['stat_wape']} | R²: {A['stat_r2']}
                </span>
            </div>
            <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 0 0 14px 0;">{A['demand_sub']}</p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 12px 0 14px 0;">
                <div style="background: rgba(59, 130, 246, 0.06); border: 1.5px solid rgba(59, 130, 246, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #3B82F6; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #3B82F6;">{A['stat_wape']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_wape_sub']}</div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.06); border: 1.5px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #10B981; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #10B981;">{A['stat_r2']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_r2_sub']}</div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.06); border: 1.5px solid rgba(245, 158, 11, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #F59E0B; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 4H6l7 8-7 8h12"/></svg>
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #F59E0B;">{A['stat_mae']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_mae_sub']}</div>
                </div>
                <div style="background: rgba(168, 85, 247, 0.06); border: 1.5px solid rgba(168, 85, 247, 0.3); border-radius: 10px; padding: 14px 12px; text-align: center;">
                    <div style="display: flex; justify-content: center; color: #A855F7; margin-bottom: 4px;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="6" width="4" height="14" rx="1"/><rect x="17" y="9" width="4" height="11" rx="1"/></svg>
                    </div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #A855F7;">{A['stat_rmse']}</div>
                    <div style="font-size: 0.72rem; color: var(--mm-text-secondary); margin-top: 3px; font-weight: 500;">{A['stat_rmse_sub']}</div>
                </div>
            </div>
            <div style="display: flex; gap: 14px; flex-wrap: wrap; align-items: stretch; margin-top: 14px;">
                <div style="flex: 1 1 520px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 10px; padding: 12px 16px; font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.6;">
                    <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                        {blue_check_svg}
                        <div>{A['demand_step1']}</div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                        {blue_check_svg}
                        <div>{A['demand_step2']}</div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 8px;">
                        {blue_check_svg}
                        <div>{A['demand_step3']}</div>
                    </div>
                </div>
                <div style="flex: 0 1 230px; min-width: 190px; background: rgba(59, 130, 246, 0.05); border: 1.5px solid rgba(59, 130, 246, 0.25); border-radius: 10px; padding: 14px; display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; border-radius: 50%; background: #EFF6FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                    </div>
                    <div style="font-size: 0.78rem; font-weight: 600; color: #2563EB; line-height: 1.35;">
                        {L['ensure_stock']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4-Card Unified 2x2 Grid (Strictly 2 per row on desktop, flexible on mobile)
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr)); gap: 16px; margin-top: 14px; align-items: stretch;">
            <!-- Card 3: Operational Stockout Risk Engine -->
            <div class="mm-card" style="margin: 0; display: flex; flex-direction: column; justify-content: space-between; border-top: 4px solid #EF4444; border-radius: 12px; padding: 18px 20px; background: var(--mm-card-bg);">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                        <span style="width: 22px; height: 22px; border-radius: 50%; background: #EF4444; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.74rem; flex-shrink: 0;">3</span>
                        <b style="font-size: 1.02rem; color: var(--mm-text-primary);">{_strip_num(A['stockout_title'])}</b>
                        <span style="background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; font-size: 0.70rem; font-weight: 700; padding: 2px 8px;">{L['risk_detect']}</span>
                    </div>
                    <p style="font-size: 0.79rem; color: var(--mm-text-secondary); margin: 2px 0 12px 0;">{A['stockout_sub']}</p>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: stretch;">
                        <div style="flex: 1 1 260px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.6;">
                            {_format_stockout_bullets(A['stockout_desc'])}
                        </div>
                        <div style="flex: 0 1 140px; min-width: 120px; background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 10px; padding: 12px 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 6px;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                            <span style="font-size: 0.72rem; font-weight: 700; color: #EF4444; line-height: 1.3;">{L['prevent_stockouts']}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mm-card" style="margin: 0; display: flex; flex-direction: column; justify-content: space-between; border-top: 4px solid #3B82F6; border-radius: 12px; padding: 18px 20px; background: var(--mm-card-bg);">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                        <span style="width: 22px; height: 22px; border-radius: 50%; background: #3B82F6; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.74rem; flex-shrink: 0;">4</span>
                        <b style="font-size: 1.02rem; color: var(--mm-text-primary);">{_strip_num(A['kg_title'])}</b>
                        <span style="background: rgba(59, 130, 246, 0.1); color: #2563EB; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; font-size: 0.70rem; font-weight: 700; padding: 2px 8px;">{L['knowledge_base']}</span>
                    </div>
                    <p style="font-size: 0.79rem; color: var(--mm-text-secondary); margin: 2px 0 12px 0;">{A['kg_sub']}</p>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: stretch;">
                        <div style="flex: 1 1 260px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.6;">
                            <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                                {blue_check_svg}
                                <div>{A['kg_item1']}</div>
                            </div>
                            <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                                {blue_check_svg}
                                <div>{A['kg_item2']}</div>
                            </div>
                            <div style="display: flex; align-items: flex-start; gap: 8px;">
                                {blue_check_svg}
                                <div>{A['kg_item3']}</div>
                            </div>
                        </div>
                        <div style="flex: 0 1 140px; min-width: 120px; background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 10px; padding: 12px 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 6px;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="12" y1="6" x2="12" y2="12"/><line x1="9" y1="9" x2="15" y2="9"/></svg>
                            <span style="font-size: 0.72rem; font-weight: 700; color: #2563EB; line-height: 1.3;">{L['safe_triage']}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mm-card" style="margin: 0; display: flex; flex-direction: column; justify-content: space-between; border-top: 4px solid #EA580C; border-radius: 12px; padding: 18px 20px; background: var(--mm-card-bg);">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                        <span style="width: 22px; height: 22px; border-radius: 50%; background: #EA580C; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.74rem; flex-shrink: 0;">5</span>
                        <b style="font-size: 1.02rem; color: var(--mm-text-primary);">{_strip_num(A['llm_title'])}</b>
                        <span style="background: rgba(234, 88, 12, 0.1); color: #EA580C; border: 1px solid rgba(234, 88, 12, 0.3); border-radius: 12px; font-size: 0.70rem; font-weight: 700; padding: 2px 8px;">{L['generative_ai']}</span>
                    </div>
                    <p style="font-size: 0.79rem; color: var(--mm-text-secondary); margin: 2px 0 12px 0;">{A['llm_sub']}</p>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: stretch;">
                        <div style="flex: 1 1 260px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.6;">
                            <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10" fill="#EA580C"/><path d="M8 12.5l2.5 2.5L16 9.5" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                                <div>{A['llm_item1']}</div>
                            </div>
                            <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10" fill="#EA580C"/><path d="M8 12.5l2.5 2.5L16 9.5" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                                <div>{A['llm_item2']}</div>
                            </div>
                            <div style="display: flex; align-items: flex-start; gap: 8px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10" fill="#EA580C"/><path d="M8 12.5l2.5 2.5L16 9.5" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                                <div>{A['llm_item3']}</div>
                            </div>
                        </div>
                        <div style="flex: 0 1 140px; min-width: 120px; background: rgba(234, 88, 12, 0.05); border: 1px solid rgba(234, 88, 12, 0.2); border-radius: 10px; padding: 12px 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EA580C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 6px;"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                            <span style="font-size: 0.72rem; font-weight: 700; color: #EA580C; line-height: 1.3;">{L['natural_advice']}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mm-card" style="margin: 0; display: flex; flex-direction: column; justify-content: space-between; border-top: 4px solid #8B5CF6; border-radius: 12px; padding: 18px 20px; background: var(--mm-card-bg);">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                        <span style="width: 22px; height: 22px; border-radius: 50%; background: #8B5CF6; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.74rem; flex-shrink: 0;">6</span>
                        <b style="font-size: 1.02rem; color: var(--mm-text-primary);">{_strip_num(A['ocr_title'])}</b>
                        <span style="background: rgba(139, 92, 246, 0.1); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; font-size: 0.70rem; font-weight: 700; padding: 2px 8px;">{L['vision_ai']}</span>
                    </div>
                    <p style="font-size: 0.79rem; color: var(--mm-text-secondary); margin: 2px 0 12px 0;">{A['ocr_sub']}</p>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: stretch;">
                        <div style="flex: 1 1 260px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.6;">
                            <div style="display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10" fill="#8B5CF6"/><path d="M8 12.5l2.5 2.5L16 9.5" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                                <div>{A['ocr_item1']}</div>
                            </div>
                            <div style="display: flex; align-items: flex-start; gap: 8px;">
                                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" style="flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10" fill="#8B5CF6"/><path d="M8 12.5l2.5 2.5L16 9.5" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                                <div>{A['ocr_item2']}</div>
                            </div>
                        </div>
                        <div style="flex: 0 1 140px; min-width: 120px; background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 10px; padding: 12px 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 6px;"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><rect x="7" y="7" width="10" height="10" rx="1"/><line x1="7" y1="12" x2="17" y2="12"/></svg>
                            <span style="font-size: 0.72rem; font-weight: 700; color: #8B5CF6; line-height: 1.3;">{L['automated_ocr']}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== TAB 2: 100+ MAJOR INDIAN DISEASES ====================
    with tab_a2:
        # Disease categories metadata with dedicated SVG icons and palette
        dis_meta = [
            {"color": "#F43F5E", "bg": "rgba(244, 63, 94, 0.08)", "border": "rgba(244, 63, 94, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F43F5E" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4.5c2 2 2 5-1 8L7 20"/><path d="M9.5 4.5c-2 2-2 5 1 8L17 20"/><path d="M8.5 7.5c2-2.5 5-2.5 7 0"/></svg>'},
            {"color": "#EF4444", "bg": "rgba(239, 68, 68, 0.08)", "border": "rgba(239, 68, 68, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>'},
            {"color": "#10B981", "bg": "rgba(16, 185, 129, 0.08)", "border": "rgba(16, 185, 129, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>'},
            {"color": "#F97316", "bg": "rgba(249, 115, 22, 0.08)", "border": "rgba(249, 115, 22, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F97316" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v7"/><path d="M12 11c-2-2-4-2-6-1-2.5 1.2-3.5 4.5-2.5 7.5 1 3 3.5 4.5 5.5 4.5 3 0 3-3 3-5"/><path d="M12 11c2-2 4-2 6-1 2.5 1.2 3.5 4.5 2.5 7.5-1 3-3.5 4.5-5.5 4.5-3 0-3-3-3-5"/></svg>'},
            {"color": "#2563EB", "bg": "rgba(37, 99, 235, 0.08)", "border": "rgba(37, 99, 235, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 5c-2.5 2-3 6.5-1.5 9.5 1.5 3 4.5 3.5 5.5 1.5 1-2 0-5-1.5-6.5C7.5 8.5 7 6.5 6 5z"/><path d="M18 5c2.5 2 3 6.5 1.5 9.5-1.5 3-4.5 3.5-5.5 1.5-1-2 0-5 1.5-6.5C16.5 8.5 17 6.5 18 5z"/></svg>'},
            {"color": "#9333EA", "bg": "rgba(147, 51, 234, 0.08)", "border": "rgba(147, 51, 234, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8c2-3 8-4 13-2 3 1.2 4 4.5 3 7.5-1.5 4.5-6 6.5-11 5.5-3-.6-5.5-3.5-5-7 .2-1.5 0-3 0-4z"/></svg>'},
            {"color": "#F59E0B", "bg": "rgba(245, 158, 11, 0.08)", "border": "rgba(245, 158, 11, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-5.04z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-5.04z"/></svg>'},
            {"color": "#E11D48", "bg": "rgba(225, 29, 72, 0.08)", "border": "rgba(225, 29, 72, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M4.93 4.93l2.12 2.12m9.9 9.9l2.12 2.12M4.93 19.07l2.12-2.12m9.9-9.9l2.12-2.12"/></svg>'},
            {"color": "#DC2626", "bg": "rgba(220, 38, 38, 0.08)", "border": "rgba(220, 38, 38, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/><path d="M12 12a3 3 0 0 0 3-3"/></svg>'},
            {"color": "#0EA5E9", "bg": "rgba(14, 165, 233, 0.08)", "border": "rgba(14, 165, 233, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0EA5E9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="7" r="3"/><circle cx="17" cy="17" r="3"/><line x1="9" y1="9" x2="15" y2="15"/><circle cx="17" cy="7" r="2.5"/><line x1="15.5" y1="8.5" x2="8.5" y2="15.5"/></svg>'},
            {"color": "#6366F1", "bg": "rgba(99, 102, 241, 0.08)", "border": "rgba(99, 102, 241, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>'},
            {"color": "#10B981", "bg": "rgba(16, 185, 129, 0.08)", "border": "rgba(16, 185, 129, 0.22)", "svg": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="7" r="2"/><circle cx="16" cy="7" r="2"/><circle cx="4.5" cy="12" r="1.8"/><circle cx="19.5" cy="12" r="1.8"/><path d="M8 14c0 3 2.5 6 4 6s4-3 4-6a4 4 0 0 0-8 0z"/></svg>'},
        ]

        # Build cards html dynamically without indentation to prevent markdown code block
        cards_html_list = []
        for i in range(1, 13):
            cat_key = f"dis_cat_{i}"
            raw_text = A.get(cat_key, "")
            title, desc = _parse_dis_cat(raw_text)
            meta = dis_meta[i - 1]
            cards_html_list.append(
                f'<div class="mm-card" style="margin: 0; padding: 14px 16px; border: 1.5px solid var(--mm-border-color); border-radius: 12px; display: flex; align-items: flex-start; gap: 14px; background: var(--mm-card-bg); transition: transform 0.15s ease, box-shadow 0.15s ease;">'
                f'<div style="width: 44px; height: 44px; border-radius: 10px; background: {meta["bg"]}; border: 1px solid {meta["border"]}; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">{meta["svg"]}</div>'
                f'<div style="flex: 1 1 auto; min-width: 0;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">'
                f'<b style="font-size: 0.90rem; color: var(--mm-text-primary); font-weight: 700; line-height: 1.25;">{title}</b>'
                f'<span style="color: #94A3B8; flex-shrink: 0;">{chevron_right_svg}</span>'
                f'</div>'
                f'<p style="font-size: 0.77rem; color: var(--mm-text-secondary); line-height: 1.45; margin: 4px 0 0 0;">{desc}</p>'
                f'</div>'
                f'</div>'
            )
        cards_grid_html = "".join(cards_html_list)

        safe_markdown(f"""
        <div class="mm-card" style="border: 1.5px solid var(--mm-border-color); border-radius: 14px; padding: 22px 24px; margin-bottom: 18px; position: relative; overflow: hidden; background: var(--mm-card-bg);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div style="flex: 1 1 500px; min-width: 280px; z-index: 2;">
                    <div style="font-size: 0.72rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;">
                        NATIONAL HEALTH TAXONOMY (MOHFW & WHO ICD)
                    </div>
                    <div style="font-size: 1.30rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">
                        {A['dis_title']}
                    </div>
                    <p style="font-size: 0.84rem; color: var(--mm-text-secondary); line-height: 1.55; margin: 8px 0 16px 0;">
                        {A['dis_sub']}
                    </p>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                        <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 10px; padding: 8px 14px; display: inline-flex; align-items: center; gap: 8px;">
                            <div style="width: 28px; height: 28px; border-radius: 6px; background: rgba(37, 99, 235, 0.12); display: flex; align-items: center; justify-content: center; color: #2563EB;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                            </div>
                            <div>
                                <div style="font-size: 0.90rem; font-weight: 800; color: #2563EB; line-height: 1.1;">18</div>
                                <div style="font-size: 0.70rem; color: var(--mm-text-secondary); font-weight: 600;">{L['official_cats_sub']}</div>
                            </div>
                        </div>
                        <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 10px; padding: 8px 14px; display: inline-flex; align-items: center; gap: 8px;">
                            <div style="width: 28px; height: 28px; border-radius: 6px; background: rgba(37, 99, 235, 0.12); display: flex; align-items: center; justify-content: center; color: #2563EB;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                            </div>
                            <div>
                                <div style="font-size: 0.90rem; font-weight: 800; color: #2563EB; line-height: 1.1;">100+</div>
                                <div style="font-size: 0.70rem; color: var(--mm-text-secondary); font-weight: 600;">{L['major_diseases_sub']}</div>
                            </div>
                        </div>
                        <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 10px; padding: 8px 14px; display: inline-flex; align-items: center; gap: 8px;">
                            <div style="width: 28px; height: 28px; border-radius: 6px; background: rgba(37, 99, 235, 0.12); display: flex; align-items: center; justify-content: center; color: #2563EB;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                            </div>
                            <div>
                                <div style="font-size: 0.90rem; font-weight: 800; color: #2563EB; line-height: 1.1;">WHO ICD-10/11</div>
                                <div style="font-size: 0.70rem; color: var(--mm-text-secondary); font-weight: 600;">{L['who_compliant_sub']}</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: space-between; min-height: 120px; z-index: 2;">
                    <span class="mm-badge" style="background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(37, 99, 235, 0.3); color: #2563EB; font-size: 0.75rem; font-weight: 800; padding: 6px 14px; border-radius: 20px;">
                        18 OFFICIAL CATEGORIES
                    </span>
                    <div style="opacity: 0.45; margin-top: 10px;">
                        <svg width="130" height="90" viewBox="0 0 100 75" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 20v15a15 15 0 0 0 30 0v-15"/>
                            <path d="M35 50v8a14 14 0 0 0 28 0v-4"/>
                            <circle cx="63" cy="54" r="5" fill="rgba(37,99,235,0.2)"/>
                            <path d="M50 22c4-8 14-8 18 0 4-8 14-8 18 0-6 10-18 16-18 16s-12-6-18-16z" stroke="#3B82F6" stroke-width="2" fill="rgba(59,130,246,0.08)"/>
                        </svg>
                    </div>
                </div>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 14px;">
{cards_grid_html}
        </div>
        """)

    # ==================== TAB 3: AUTHENTIC DATA SOURCES & APIS ====================
    with tab_a3:
        st.markdown(f"""
        <div class="mm-card" style="border-left: 5px solid #2563EB; border-radius: 16px; padding: 22px 26px; margin-bottom: 20px;">
            <!-- Header Row -->
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-bottom: 8px;">
                <div style="max-width: 720px;">
                    <div style="font-size: 0.74rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 3px;">
                        CLINICAL DATA GOVERNANCE &amp; PROVENANCE
                    </div>
                    <b style="font-size: 1.25rem; color: var(--mm-text-primary); display: block; line-height: 1.3;">{A['sources_title']}</b>
                    <p style="font-size: 0.84rem; color: var(--mm-text-secondary); line-height: 1.5; margin: 4px 0 0 0;">
                        {A['sources_sub']}
                    </p>
                </div>
                <!-- Right side trust badge -->
                <div style="display: flex; align-items: center; gap: 12px; margin-left: auto;">
                    <div style="opacity: 0.75;">
                        <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <ellipse cx="12" cy="5" rx="9" ry="3" fill="rgba(37,99,235,0.06)"/>
                            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                        </svg>
                    </div>
                    <div style="background: rgba(224, 242, 254, 0.85); border: 1.5px solid #7DD3FC; border-radius: 9999px; padding: 7px 16px; display: flex; align-items: center; gap: 10px;">
                        <div style="width: 22px; height: 22px; border-radius: 50%; background: #0284C7; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        </div>
                        <div>
                            <div style="font-size: 0.72rem; font-weight: 800; color: #0369A1; letter-spacing: 0.04em; text-transform: uppercase; line-height: 1.2;">100% REAL, AUDITED &amp; NON-FABRICATED</div>
                            <div style="font-size: 0.68rem; color: #0284C7; font-weight: 500; line-height: 1.2;">{L.get('trusted_data', 'Trusted Data. Better Care.')}</div>
                        </div>
                    </div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 270px), 1fr)); gap: 16px; margin-top: 18px;">
                <div style="background: var(--mm-card-bg); border: 1.5px solid #BFDBFE; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(37, 99, 235, 0.12); border: 1px solid rgba(37, 99, 235, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"/>
                                    <line x1="2" y1="12" x2="22" y2="12"/>
                                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #1D4ED8; line-height: 1.35;">{A['src_who_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_who_desc']}
                        </div>
                    </div>
                    <a href="https://www.who.int/api/news/diseaseoutbreaknews" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.25); color: #2563EB; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                        <span>{L.get('btn_view_api_doc', 'View API Documentation')}</span>
                    </a>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #A7F3D0; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <line x1="3" y1="21" x2="21" y2="21"/>
                                    <line x1="4" y1="10" x2="20" y2="10"/>
                                    <polyline points="12 2 20 7 4 7"/>
                                    <line x1="6" y1="10" x2="6" y2="21"/>
                                    <line x1="10" y1="10" x2="10" y2="21"/>
                                    <line x1="14" y1="10" x2="14" y2="21"/>
                                    <line x1="18" y1="10" x2="18" y2="21"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #059669; line-height: 1.35;">{A['src_hmis_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_hmis_desc']}
                        </div>
                    </div>
                    <a href="https://hmis.mohfw.gov.in/" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); color: #059669; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                        <span>{L.get('btn_view_govt_data', 'View Government Data')}</span>
                    </a>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #FDE68A; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(245, 158, 11, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                                    <circle cx="9" cy="7" r="4"/>
                                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #D97706; line-height: 1.35;">{A['src_nfhs_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_nfhs_desc']}
                        </div>
                    </div>
                    <a href="http://rchiips.org/nfhs/" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); color: #D97706; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        <span>{L.get('btn_view_district_data', 'View District Data')}</span>
                    </a>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #DDD6FE; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(168, 85, 247, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                    <polyline points="14 2 14 8 20 8"/>
                                    <line x1="16" y1="13" x2="8" y2="13"/>
                                    <line x1="16" y1="17" x2="8" y2="17"/>
                                    <polyline points="10 9 9 9 8 9"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #9333EA; line-height: 1.35;">{A['src_nlem_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_nlem_desc']}
                        </div>
                    </div>
                    <a href="https://cdsco.gov.in/opencms/opencms/en/Home/" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.25); color: #9333EA; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>
                        <span>{L.get('btn_view_nlem_cat', 'View NLEM Catalog')}</span>
                    </a>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #FECDD3; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(244, 63, 94, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #E11D48; line-height: 1.35;">{A['src_fda_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_fda_desc']}
                        </div>
                    </div>
                    <a href="https://open.fda.gov/apis/drug/" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(244, 63, 94, 0.08); border: 1px solid rgba(244, 63, 94, 0.25); color: #E11D48; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        <span>{L.get('btn_browse_fda', 'Browse FDA Data')}</span>
                    </a>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #BFDBFE; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(37, 99, 235, 0.12); border: 1px solid rgba(37, 99, 235, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M6 18h8"/>
                                    <path d="M3 22h18"/>
                                    <path d="M14 22a7 7 0 1 0 0-14h-1"/>
                                    <path d="M9 14h2"/>
                                    <path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>
                                    <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #2563EB; line-height: 1.35;">{A['src_nih_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_nih_desc']}
                        </div>
                    </div>
                    <a href="https://loinc.org/" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.25); color: #2563EB; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                        <span>{L.get('btn_view_ref_standards', 'View Reference Standards')}</span>
                    </a>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #E9D5FF; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(168, 85, 247, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                                    <circle cx="12" cy="10" r="3"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #9333EA; line-height: 1.35;">{A['src_gis_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_gis_desc']}
                        </div>
                    </div>
                    <a href="https://overpass-turbo.eu/" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.25); color: #9333EA; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9333EA" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>
                        <span>{L.get('btn_explore_location', 'Explore Location Data')}</span>
                    </a>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #A7F3D0; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.04);">
                    <div>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                            <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="4" r="2"/>
                                    <path d="m14 10 2 2 3-1"/>
                                    <path d="m10 10-2 2-3-1"/>
                                    <path d="M12 6v6"/>
                                    <path d="m9 16 3 2 3-2"/>
                                    <path d="M8 21h8"/>
                                </svg>
                            </div>
                            <b style="font-size: 0.90rem; color: #059669; line-height: 1.35;">{A['src_ayush_title']}</b>
                        </div>
                        <div style="font-size: 0.81rem; color: var(--mm-text-secondary); line-height: 1.55; margin-bottom: 16px;">
                            {A['src_ayush_desc']}
                        </div>
                    </div>
                    <a href="https://ayush.gov.in/" target="_blank" rel="noopener noreferrer" style="text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; padding: 8px 14px; border-radius: 10px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); color: #059669; font-size: 0.78rem; font-weight: 700; transition: all 0.2s ease; margin-top: auto;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
                        <span>{L.get('btn_view_guidelines', 'View Practices & Guidelines')}</span>
                    </a>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== TAB 4: ARCHITECTURE, PRIVACY & SECURITY ====================
    with tab_a4:
        st.markdown(f"""
        <div class="mm-card" style="border-left: 5px solid #2563EB; border-radius: 16px; padding: 22px 26px; margin-bottom: 20px; position: relative;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(37, 99, 235, 0.1); border: 1.5px solid rgba(37, 99, 235, 0.25); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            <polyline points="9 12 11 14 15 10"/>
                        </svg>
                    </div>
                    <div>
                        <b style="font-size: 1.25rem; color: var(--mm-text-primary); display: block; line-height: 1.3;">{A['feat_title']}</b>
                        <span style="font-size: 0.84rem; color: var(--mm-text-secondary); margin-top: 2px; display: block;">{L.get('suite_sub', 'Empowering a secure, accessible and resilient healthcare ecosystem.')}</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; margin-left: auto;">
                    <div style="opacity: 0.75;">
                        <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#93C5FD" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="rgba(37,99,235,0.06)"/>
                            <rect x="9" y="11" width="6" height="5" rx="1" fill="#3B82F6"/>
                            <path d="M10 11V9a2 2 0 1 1 4 0v2"/>
                        </svg>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.74rem; color: var(--mm-text-secondary); font-weight: 500;">{L.get('secure_hc', 'Secure Healthcare')}</div>
                        <div style="font-size: 0.78rem; color: #2563EB; font-weight: 700;">{L.get('smarter_tom', 'Smarter Tomorrow')}</div>
                        <div style="width: 28px; height: 2.5px; background: #2563EB; border-radius: 4px; margin-left: auto; margin-top: 2px;"></div>
                    </div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 255px), 1fr)); gap: 16px; margin-top: 20px;">
                <div style="background: var(--mm-card-bg); border: 1.5px solid #BFDBFE; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.04);">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 38px; height: 38px; border-radius: 50%; background: rgba(37, 99, 235, 0.12); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="10"/>
                                        <line x1="2" y1="12" x2="22" y2="12"/>
                                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                                    </svg>
                                </div>
                                <b style="font-size: 0.92rem; color: #1D4ED8;">{A['feat_1_title']}</b>
                            </div>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.55; margin: 0 0 16px 0;">{A['feat_1_desc']}</p>
                    </div>
                    <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.72rem; font-weight: 600; color: #2563EB; text-align: center; margin-top: auto;">
                        {L.get('tag_feat_1', 'Multilingual • Accessible • Inclusive')}
                    </div>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #BBF7D0; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.04);">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 38px; height: 38px; border-radius: 50%; background: rgba(16, 185, 129, 0.12); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                                        <polyline points="9 12 11 14 15 10"/>
                                    </svg>
                                </div>
                                <b style="font-size: 0.92rem; color: #059669;">{A['feat_2_title']}</b>
                            </div>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.55; margin: 0 0 16px 0;">{A['feat_2_desc']}</p>
                    </div>
                    <div style="background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.72rem; font-weight: 600; color: #059669; text-align: center; margin-top: auto;">
                        {L.get('tag_feat_2', 'Transparent • Auditable • Reliable')}
                    </div>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #FED7AA; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; box-shadow: 0 2px 8px rgba(245, 158, 11, 0.04);">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 38px; height: 38px; border-radius: 50%; background: rgba(245, 158, 11, 0.12); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                                    </svg>
                                </div>
                                <b style="font-size: 0.92rem; color: #D97706;">{A['feat_3_title']}</b>
                            </div>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.55; margin: 0 0 16px 0;">{A['feat_3_desc']}</p>
                    </div>
                    <div style="background: rgba(245, 158, 11, 0.06); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.72rem; font-weight: 600; color: #D97706; text-align: center; margin-top: auto;">
                        {L.get('tag_feat_3', 'Private • Secure • HIPAA Compliant')}
                    </div>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #E9D5FF; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; box-shadow: 0 2px 8px rgba(168, 85, 247, 0.04);">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 38px; height: 38px; border-radius: 50%; background: rgba(168, 85, 247, 0.12); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#A855F7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <ellipse cx="12" cy="5" rx="9" ry="3"/>
                                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                                    </svg>
                                </div>
                                <b style="font-size: 0.92rem; color: #9333EA;">{A['feat_4_title']}</b>
                            </div>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.55; margin: 0 0 16px 0;">{A['feat_4_desc']}</p>
                    </div>
                    <div style="background: rgba(168, 85, 247, 0.06); border: 1px solid rgba(168, 85, 247, 0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.72rem; font-weight: 600; color: #9333EA; text-align: center; margin-top: auto;">
                        {L.get('tag_feat_4', 'Always Available \u2022 Reliable \u2022 Patient-First')}
                    </div>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #FECACA; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; box-shadow: 0 2px 8px rgba(244, 63, 94, 0.04);">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 38px; height: 38px; border-radius: 50%; background: rgba(244, 63, 94, 0.10); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#F43F5E" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                        <polyline points="14 2 14 8 20 8"/>
                                        <line x1="12" y1="18" x2="12" y2="12"/>
                                        <line x1="9" y1="15" x2="15" y2="15"/>
                                    </svg>
                                </div>
                                <b style="font-size: 0.92rem; color: #E11D48;">{A['feat_5_title']}</b>
                            </div>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.55; margin: 0 0 16px 0;">{A['feat_5_desc']}</p>
                    </div>
                    <div style="background: rgba(244, 63, 94, 0.06); border: 1px solid rgba(244, 63, 94, 0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.72rem; font-weight: 600; color: #E11D48; text-align: center; margin-top: auto;">
                        {L.get('tag_feat_5', 'Intelligent \u2022 Accurate \u2022 Clinical-Grade')}
                    </div>
                </div>
                <div style="background: var(--mm-card-bg); border: 1.5px solid #A5F3FC; border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.25s ease; box-shadow: 0 2px 8px rgba(6, 182, 212, 0.04);">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="width: 38px; height: 38px; border-radius: 50%; background: rgba(6, 182, 212, 0.10); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                                        <circle cx="9" cy="7" r="4"/>
                                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                                    </svg>
                                </div>
                                <b style="font-size: 0.92rem; color: #0891B2;">{A['feat_6_title']}</b>
                            </div>
                        </div>
                        <p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.55; margin: 0 0 16px 0;">{A['feat_6_desc']}</p>
                    </div>
                    <div style="background: rgba(6, 182, 212, 0.06); border: 1px solid rgba(6, 182, 212, 0.2); border-radius: 8px; padding: 6px 10px; font-size: 0.72rem; font-weight: 600; color: #0891B2; text-align: center; margin-top: auto;">
                        {L.get('tag_feat_6', 'Multi-Member \u2022 Secure \u2022 Comprehensive')}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== TAB 5: OFFICIAL CLINICAL HELPDESK & SUPPORT ====================
    with tab_a5:
        # Top Protocol Banner Card
        st.markdown(f"""
        <div class="mm-card" style="background: linear-gradient(135deg, rgba(239, 246, 255, 0.85) 0%, rgba(219, 234, 254, 0.5) 100%); border: 1.5px solid #BFDBFE; border-radius: 16px; padding: 22px 26px; margin-bottom: 22px; position: relative; overflow: hidden;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div style="display: flex; align-items: center; gap: 16px;">
                    <div style="width: 52px; height: 52px; border-radius: 14px; background: #DBEAFE; border: 1.5px solid #93C5FD; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 12px rgba(37,99,235,0.12);">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
                            <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
                        </svg>
                    </div>
                    <div>
                        <div style="font-size: 0.74rem; font-weight: 800; color: #2563EB; letter-spacing: 0.08em; text-transform: uppercase;">
                            NATIONAL PATIENT &amp; CLINICIAN SUPPORT PROTOCOL
                        </div>
                        <div style="font-size: 1.50rem; font-weight: 800; color: #1E293B; line-height: 1.25; margin-top: 2px;">
                            Official Clinical <span style="color: #2563EB;">Helpdesk &amp; Grievance Redressal</span>
                        </div>
                        <div style="font-size: 0.86rem; color: #64748B; margin-top: 3px;">
                            Submit any technical issue, clinical query or system feedback directly to the National System Administration.
                        </div>
                    </div>
                </div>
                <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(224, 242, 254, 0.95); border: 1.5px solid #38BDF8; color: #0284C7; padding: 8px 16px; border-radius: 9999px; font-weight: 800; font-size: 0.76rem; letter-spacing: 0.04em;">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    24-HOUR RESOLUTION PROMISE
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin-top: 16px; padding-top: 14px; border-top: 1px solid rgba(191, 219, 254, 0.8);">
                <div style="display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.75); border: 1px solid #DBEAFE; border-radius: 10px; padding: 8px 12px;">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: #EFF6FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#2563EB" stroke="#2563EB" stroke-width="1"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                    </div>
                    <div>
                        <div style="font-size: 0.82rem; font-weight: 700; color: #1E293B;">Quick Response</div>
                        <div style="font-size: 0.72rem; color: #64748B;">Acknowledgment within minutes</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.75); border: 1px solid #DBEAFE; border-radius: 10px; padding: 8px 12px;">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: #EFF6FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
                    </div>
                    <div>
                        <div style="font-size: 0.82rem; font-weight: 700; color: #1E293B;">Direct to Administration</div>
                        <div style="font-size: 0.72rem; color: #64748B;">Secure &amp; authenticated channel</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.75); border: 1px solid #DBEAFE; border-radius: 10px; padding: 8px 12px;">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: #EFF6FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                    </div>
                    <div>
                        <div style="font-size: 0.82rem; font-weight: 700; color: #1E293B;">Automated Confirmation</div>
                        <div style="font-size: 0.72rem; color: #64748B;">Instant email notification</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.75); border: 1px solid #DBEAFE; border-radius: 10px; padding: 8px 12px;">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: #EFF6FF; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
                    </div>
                    <div>
                        <div style="font-size: 0.82rem; font-weight: 700; color: #1E293B;">Dedicated Support</div>
                        <div style="font-size: 0.72rem; color: #64748B;">For clinical &amp; technical issues</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <style>
        /* Force equal height on Customer Support columns & cards in both light & dark mode */
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]),
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) {
            align-items: stretch !important;
        }
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: stretch !important;
            height: 100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
        }
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) [data-testid="stLayoutWrapper"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) [data-testid="stLayoutWrapper"] {
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 auto !important;
        }
        /* Left card container stretches full height */
        div[class*="st-key-about_supp_form_card"],
        .st-key-about_supp_form_card,
        .st-key-about_supp_form_card > div[data-testid="stVerticalBlockBorderWrapper"],
        .st-key-about_supp_form_card div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div[class*="st-key-about_supp_form_card"]),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_form_card) {
            height: 100% !important;
            min-height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
            box-sizing: border-box !important;
            border-radius: 14px !important;
        }
        div[class*="st-key-about_supp_form_card"] > div[data-testid="stVerticalBlock"],
        .st-key-about_supp_form_card > div[data-testid="stVerticalBlock"],
        .st-key-about_supp_form_card [data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            flex: 1 1 100% !important;
        }
        .st-key-about_supp_form_card .stButton,
        div[class*="st-key-about_supp_form_card"] .stButton {
            margin-top: auto !important;
            padding-top: 10px !important;
        }
        /* Right column stretches cards to fill vertical space */
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(.st-key-about_supp_form_card) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-about_supp_form_card"]) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"] {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: space-between !important;
            gap: 12px !important;
        }
        .st-key-about_supp_card_info,
        .st-key-about_supp_card_report,
        .st-key-about_supp_card_help,
        div[class*="st-key-about_supp_card_info"],
        div[class*="st-key-about_supp_card_report"],
        div[class*="st-key-about_supp_card_help"],
        .st-key-about_supp_card_info > div[data-testid="stVerticalBlockBorderWrapper"],
        .st-key-about_supp_card_report > div[data-testid="stVerticalBlockBorderWrapper"],
        .st-key-about_supp_card_help > div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_card_info),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_card_report),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-about_supp_card_help) {
            flex: 1 1 auto !important;
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            box-sizing: border-box !important;
            border-radius: 12px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        col_supp_left, col_supp_right = st.columns([1.75, 1.0], gap="large")

        with col_supp_left:
            with st.container(key="about_supp_form_card", border=True):
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 14px;">
                    <div style="width: 42px; height: 42px; border-radius: 10px; background: rgba(37,99,235,0.08); border: 1.5px solid #BFDBFE; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                            <polyline points="22,6 12,13 2,6"/>
                        </svg>
                    </div>
                    <div>
                        <b style="font-size: 1.05rem; color: var(--mm-text-primary);">Submit Clinical &amp; System Inquiry</b>
                        <div style="font-size: 0.80rem; color: var(--mm-text-secondary); margin-top: 1px;">
                            Direct dispatch to Administration (docmindxai@gmail.com) with automated confirmation.
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                default_email = st.session_state.get("auth_user", {}).get("email", "") if isinstance(st.session_state.get("auth_user"), dict) else ""

                st.markdown("""
                <div style="display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.86rem; color: var(--mm-text-primary); margin-bottom: 4px;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    <span>Your Registered Email Address</span> <span style="color: #EF4444;">*</span>
                </div>
                """, unsafe_allow_html=True)
                supp_email = st.text_input(
                    "Your Registered Email Address",
                    value=default_email,
                    placeholder="yourname@domain.com",
                    key="about_supp_email_input",
                    label_visibility="collapsed"
                )
                st.caption("Enter the email address registered with your DocMindX AI account.")

                st.markdown("""
                <div style="display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 0.86rem; color: var(--mm-text-primary); margin-top: 10px; margin-bottom: 4px;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                    <span>Detailed Problem Description / Support Inquiry</span> <span style="color: #EF4444;">*</span>
                </div>
                """, unsafe_allow_html=True)
                supp_desc = st.text_area(
                    "Detailed Problem Description / Support Inquiry",
                    placeholder="Please describe your issue, affected module, error message, or inquiry in detail...",
                    key="about_supp_desc_input",
                    max_chars=1000,
                    height=135,
                    label_visibility="collapsed"
                )
                chars_used = len(supp_desc) if supp_desc else 0
                st.markdown(f"<div style='text-align: right; font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: -8px; margin-bottom: 10px;'>{chars_used}/1000 characters</div>", unsafe_allow_html=True)

                submit_btn = st.button(
                    "Send Support Ticket to Admin →",
                    key="btn_about_support_submit",
                    type="primary",
                    use_container_width=True
                )

                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: center; gap: 6px; font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 10px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>Your information is secure and will be sent directly to the National System Administration.</span>
                </div>
                """, unsafe_allow_html=True)

                if submit_btn:
                    if not supp_email or "@" not in supp_email or "." not in supp_email:
                        st.error("Please provide a valid registered email address.")
                    elif not supp_desc or len(supp_desc.strip()) < 8:
                        st.error("Please provide a detailed problem description or inquiry before submitting.")
                    else:
                        ticket_id = f"TKT-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
                        user_full_name = "DocMindX AI User"
                        if isinstance(st.session_state.get("auth_user"), dict):
                            user_full_name = st.session_state["auth_user"].get("full_name") or "DocMindX AI User"

                        with st.spinner("Dispatching clinical support ticket..."):
                            admin_ok = email_service.send_support_ticket_to_admin(
                                user_email=supp_email.strip(),
                                issue_text=supp_desc.strip(),
                                ticket_id=ticket_id,
                                user_name=user_full_name
                            )
                            user_ok = email_service.send_support_ticket_confirmation_to_user(
                                user_email=supp_email.strip(),
                                issue_text=supp_desc.strip(),
                                ticket_id=ticket_id,
                                user_name=user_full_name
                            )

                        st.success(
                            f"Support Ticket **#{ticket_id}** has been registered successfully! An automated confirmation has been dispatched to `{supp_email.strip()}`. Our National Administration will review and respond within 24 hours."
                        )

        with col_supp_right:
            # Card 1: Support Information
            with st.container(key="about_supp_card_info", border=True):
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: rgba(37,99,235,0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
                    </div>
                    <div>
                        <b style="font-size: 0.95rem; color: var(--mm-text-primary);">Support Information</b>
                        <div style="font-size: 0.75rem; color: var(--mm-text-secondary);">We are here to help you</div>
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 12px; font-size: 0.82rem;">
                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" style="flex-shrink:0; margin-top:2px;"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                        <div>
                            <div style="font-size: 0.74rem; color: var(--mm-text-secondary);">Admin Email</div>
                            <div style="font-weight: 600; color: #2563EB;">docmindxai@gmail.com</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" style="flex-shrink:0; margin-top:2px;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        <div>
                            <div style="font-size: 0.74rem; color: var(--mm-text-secondary);">Response Time</div>
                            <div style="font-weight: 600; color: var(--mm-text-primary);">Within 24 hours</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" style="flex-shrink:0; margin-top:2px;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                        <div>
                            <div style="font-size: 0.74rem; color: var(--mm-text-secondary);">Supported By</div>
                            <div style="font-weight: 600; color: var(--mm-text-primary);">National System Administration</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: flex-start; gap: 10px;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" style="flex-shrink:0; margin-top:2px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        <div>
                            <div style="font-size: 0.74rem; color: var(--mm-text-secondary);">Data Security</div>
                            <div style="font-weight: 600; color: var(--mm-text-primary);">Your data is encrypted and secure</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Card 2: What Can You Report?
            with st.container(key="about_supp_card_report", border=True):
                st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.04); border-radius: 8px; margin: -8px; padding: 12px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                        <div style="width: 26px; height: 26px; border-radius: 50%; background: #10B981; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        </div>
                        <b style="font-size: 0.90rem; color: var(--mm-text-primary);">What Can You Report?</b>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.80rem; color: var(--mm-text-secondary);">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="16 9 10 15 8 13"/></svg>
                            <span>Technical issues or errors</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="16 9 10 15 8 13"/></svg>
                            <span>Clinical query or guidance</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="16 9 10 15 8 13"/></svg>
                            <span>Feature requests</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="16 9 10 15 8 13"/></svg>
                            <span>System feedback</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="16 9 10 15 8 13"/></svg>
                            <span>Any other support related issue</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Card 3: Need Immediate Help?
            with st.container(key="about_supp_card_help", border=True):
                st.markdown("""
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <div style="width: 36px; height: 36px; border-radius: 50%; background: rgba(37,99,235,0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
                            <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
                        </svg>
                    </div>
                    <div>
                        <b style="font-size: 0.90rem; color: var(--mm-text-primary);">Need Immediate Help?</b>
                        <p style="font-size: 0.80rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.45;">
                            For urgent clinical or security issues, please mark it as <b style="color: #EF4444;">URGENT</b> in your message.
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)

# ==============================================================================
# MODULE 6: NATIONAL HEALTH RESOURCE COMMAND CENTER (HACKATHON TRACK)
# ==============================================================================
elif st.session_state["active_panel"] == "National Command Center":
    cc_icon_html = '<div style="width: 52px; height: 52px; border-radius: 14px; background: rgba(16, 185, 129, 0.08); border: 1.5px solid #10B981; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.25); flex-shrink: 0;"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg></div>'
    with st.container(key="mm_top_header_card_6"):
        hdr6_c1, hdr6_c2, hdr6_c3, hdr6_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr6_c1:
            title_p6 = T.get("p6_header_title", "National Health Resource Command Center")
            sub_p6 = T.get("p6_header_subtitle", "Data-driven intelligence platform for public health supply chains, bed capacity & cross-district redistribution.")
            safe_markdown(
                f'<div style="display: flex; align-items: center; gap: 16px;">'
                f'{cc_icon_html}'
                f'<div style="min-width: 0; flex: 1;">'
                f'<div style="margin: 0; font-size: 1.45rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.25;">{title_p6}</div>'
                f'<div style="margin-top: 4px; font-size: 0.85rem; color: var(--mm-text-secondary); line-height: 1.35;">{sub_p6}</div>'
                f'</div>'
                f'</div>'
            )
        with hdr6_c2:
            st.markdown(f"<div style='display: flex; justify-content: center; align-items: center; height: 38px;'><span class='mm-badge mm-badge-brand' style='height: 38px; line-height: 38px; padding: 0 16px; display: inline-flex; align-items: center;'>{T.get('p6_badge', 'OFFICIAL DATA INTEGRATED')}</span></div>", unsafe_allow_html=True)
        with hdr6_c3:
            header_lang_6 = st.selectbox(
                "Header Lang Selector 6",
                options=LANG_OPTIONS,
                key="hdr_lang_p6",
                label_visibility="collapsed",
                on_change=sync_language,
                args=("hdr_lang_p6",)
            )
        with hdr6_c4:
            new_theme_p6 = theme_toggle_switch(is_dark=st.session_state.get("dark_mode", False), key="hdr_sun_moon_p6")
            if new_theme_p6 != st.session_state.get("dark_mode", False):
                st.session_state["dark_mode"] = new_theme_p6
                st.rerun()

    render_command_center_dashboard(lang_code=lang_code, is_dark=st.session_state.get("dark_mode", False))
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)

elif st.session_state["active_panel"] == "Account / Authentication":
    auth_ui.render_auth_portal_panel(T=T, lang_code=lang_code, LANG_OPTIONS=LANG_OPTIONS, sync_language=sync_language)
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)

elif st.session_state["active_panel"] in ("Family Management", "My Profile & Family"):
    curr_auth_user = auth_ui.get_current_user()
    if curr_auth_user and auth_ui.is_authenticated():
        family_ui.render_family_management_view(curr_auth_user)
    else:
        st.session_state["active_panel"] = "Account / Authentication"
        st.rerun()
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)

elif st.session_state["active_panel"] in ("Admin Panel", "Admin Console"):
    curr_auth_user = auth_ui.get_current_user()
    if curr_auth_user and auth_svc.is_admin_session(curr_auth_user):
        admin_ui.render_admin_dashboard_view()
    else:
        st.error("Admin session required. Please sign in with administrator credentials.")
        st.session_state["active_panel"] = "Account / Authentication"
        st.session_state["auth_view"] = "ADMIN_LOGIN"
        st.rerun()
    st.markdown("<div style='height: 2.5px; background: linear-gradient(90deg, rgba(37, 99, 235, 0.05) 0%, #2563EB 50%, rgba(37, 99, 235, 0.05) 100%); margin: 24px 0 18px 0; border-radius: 99px;'></div>", unsafe_allow_html=True)
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)

else:
    # Fail-safe handler to ensure white screen NEVER occurs under any circumstance
    curr_fallback_user = auth_ui.get_current_user()
    if curr_fallback_user and auth_ui.is_authenticated():
        if auth_svc.is_admin_session(curr_fallback_user):
            st.session_state["active_panel"] = "Admin Panel"
        else:
            st.session_state["active_panel"] = "Family Management"
    else:
        st.session_state["active_panel"] = "Health Assessment"
    st.rerun()


# ==============================================================================
# FLOATING AI ASSISTANT POPUP WIDGET (IMAGE 2 REPLICA & FULL RESPONSIVE)
# ==============================================================================
if "floating_chat_open" not in st.session_state:
    st.session_state["floating_chat_open"] = False
if "floating_chat_history" not in st.session_state:
    st.session_state["floating_chat_history"] = []

def toggle_floating_chat():
    st.session_state["floating_chat_open"] = not st.session_state["floating_chat_open"]

def clear_floating_chat():
    st.session_state["floating_chat_history"] = []

chat_is_open = st.session_state["floating_chat_open"]
btn_transform = "rotate(45deg) scale(1.08)" if chat_is_open else "rotate(0deg) scale(1)"

# Inject styling for the floating assistant drawer and elements (non-f-string style block to avoid bracket escaping issues)
st.markdown("""
<style>
/* Animated Eye Movement (Left, Right, Up, Down) & Blink */
@keyframes eye-look-and-blink {
    0%, 15% {
        transform: translate(0, 0) scaleY(1);
    }
    20%, 35% {
        transform: translate(-2.5px, 0) scaleY(1); /* Look Left */
    }
    40%, 50% {
        transform: translate(2.5px, 0) scaleY(1);  /* Look Right */
    }
    55%, 65% {
        transform: translate(0, -2.5px) scaleY(1); /* Look Up */
    }
    70%, 80% {
        transform: translate(0, 2.5px) scaleY(1);  /* Look Down */
    }
    85% {
        transform: translate(0, 0) scaleY(1);      /* Center */
    }
    90% {
        transform: translate(0, 0) scaleY(0.08);   /* Blink */
    }
    94%, 100% {
        transform: translate(0, 0) scaleY(1);      /* Open */
    }
}

/* Floating Compact Medical Cross '+' Robot Button */
.st-key-floating_ai_assistant,
div.st-key-floating_ai_assistant,
.st-key-floating_chat_pill,
div.st-key-floating_chat_pill {
    position: fixed !important;
    bottom: 22px !important;
    right: 22px !important;
    width: 48px !important;
    height: 48px !important;
    z-index: 999995 !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
}

.st-key-floating_ai_assistant button,
.st-key-floating_chat_pill button {
    width: 48px !important;
    height: 48px !important;
    min-width: 48px !important;
    min-height: 48px !important;
    clip-path: polygon(
        30% 0%, 70% 0%, 70% 30%,
        100% 30%, 100% 70%, 70% 70%,
        70% 100%, 30% 100%, 30% 70%,
        0% 70%, 0% 30%, 30% 30%
    ) !important;
    border-radius: 4px !important;
    background: linear-gradient(135deg, #06B6D4 0%, #2563EB 100%) !important;
    border: none !important;
    filter: drop-shadow(0 0 12px rgba(37, 99, 235, 0.85)) drop-shadow(0 0 24px rgba(6, 182, 212, 0.55)) drop-shadow(0 6px 16px rgba(0, 0, 0, 0.45)) !important;
    cursor: pointer !important;
    transition: transform 0.32s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.3s ease !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    position: relative !important;
}

/* Animated Synchronized Glowing Eyes */
.st-key-floating_ai_assistant button::before,
.st-key-floating_ai_assistant button::after,
.st-key-floating_chat_pill button::before,
.st-key-floating_chat_pill button::after {
    content: "" !important;
    position: absolute !important;
    width: 4px !important;
    height: 7px !important;
    background: #FFFFFF !important;
    border-radius: 2px !important;
    top: 50% !important;
    margin-top: -3.5px !important;
    transform-origin: center !important;
    animation: eye-look-and-blink 4.5s infinite ease-in-out !important;
    box-shadow: 0 0 6px rgba(255, 255, 255, 0.95) !important;
    z-index: 10 !important;
}

.st-key-floating_ai_assistant button::before,
.st-key-floating_chat_pill button::before {
    left: 16px !important;
}

.st-key-floating_ai_assistant button::after,
.st-key-floating_chat_pill button::after {
    right: 16px !important;
}

.st-key-floating_ai_assistant button p,
.st-key-floating_ai_assistant button span,
.st-key-floating_ai_assistant button div,
.st-key-floating_chat_pill button p,
.st-key-floating_chat_pill button span,
.st-key-floating_chat_pill button div {
    display: none !important;
}

/* Backdrop for Click-Outside-to-Close */
#mm-chat-backdrop {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: 999995 !important;
    background: rgba(15, 23, 42, 0.28) !important;
    backdrop-filter: blur(2px) !important;
    cursor: pointer !important;
    animation: mmBackdropFade 0.22s ease-out forwards !important;
}

@keyframes mmBackdropFade {
    0% { opacity: 0; }
    100% { opacity: 1; }
}

@keyframes mmDrawerSlideUp {
    0% {
        opacity: 0;
        transform: translateY(24px) scale(0.95);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
    }
}

/* Floating AI Assistant Drawer Window */
/* Floating AI Assistant Drawer Window */
.st-key-slide_chat_drawer,
div.st-key-slide_chat_drawer,
div[data-testid="stVerticalBlock"]:has(> div.st-key-slide_chat_drawer) {
    position: fixed !important;
    bottom: 74px !important;
    right: 22px !important;
    width: 440px !important;
    max-width: calc(100vw - 28px) !important;
    height: auto !important;
    max-height: calc(100vh - 84px) !important;
    background: #FFFFFF !important;
    border: 1.2px solid rgba(226, 232, 240, 0.95) !important;
    border-radius: 24px !important;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22), 0 0 1px rgba(0, 0, 0, 0.08) !important;
    z-index: 999999 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    animation: mmDrawerSlideUp 0.26s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
    padding: 0 0 10px 0 !important;
}

/* Vibrant Blue Gradient Header matching Image 2 */
.st-key-popup_unified_header {
    background: linear-gradient(135deg, #0A58CA 0%, #1D4ED8 50%, #2563EB 100%) !important;
    padding: 14px 16px !important;
    border-radius: 23px 23px 0 0 !important;
    margin: 0 !important;
}

/* Round White Header Close & Refresh Buttons */
.st-key-drawer_close_x_btn button,
.st-key-drawer_clear_chat_btn button,
div[class*="st-key-drawer_close_x_btn"] button,
div[class*="st-key-drawer_clear_chat_btn"] button {
    height: 36px !important;
    width: 36px !important;
    min-height: 36px !important;
    max-height: 36px !important;
    min-width: 36px !important;
    padding: 0 !important;
    border-radius: 50% !important;
    background: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.6) !important;
    color: #1E293B !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    margin: 0 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.14) !important;
    transition: all 0.18s ease !important;
}
.st-key-drawer_close_x_btn button:hover,
.st-key-drawer_clear_chat_btn button:hover {
    background: #F8FAFC !important;
    transform: scale(1.08) !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.20) !important;
}
.st-key-drawer_clear_chat_btn button:hover {
    transform: rotate(-180deg) scale(1.08) !important;
    transition: transform 0.35s ease !important;
}

/* Active Context Banner */
.mm-chat-context-card {
    background: #F0F9FF;
    border-bottom: 1px solid #BAE6FD;
    padding: 9px 16px;
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 0.78rem;
}
.mm-chat-context-icon {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    background: #E0F2FE;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.mm-chat-context-title {
    font-weight: 800;
    color: #0284C7;
    margin-right: 4px;
}
.mm-chat-context-val {
    color: #0369A1;
    font-weight: 600;
}

/* Greeting Card */
.mm-chat-greeting-wrap {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    margin: 6px 0 14px 0;
}
.mm-chat-avatar {
    width: 38px;
    height: 38px;
    min-width: 38px;
    border-radius: 50%;
    background: #0B1930;
    border: 2px solid #0284C7;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 3px 10px rgba(2, 132, 199, 0.28);
    flex-shrink: 0;
}
.mm-chat-greeting-card {
    background: #F8FAFC;
    border: 1.2px solid #E2E8F0;
    border-radius: 18px;
    padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
    flex: 1;
}
.mm-chat-greeting-title {
    font-size: 0.92rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.3;
    margin-bottom: 3px;
}
.mm-chat-greeting-sub {
    font-size: 0.80rem;
    color: #64748B;
    font-weight: 500;
}

/* Quick Actions Section Header */
.mm-chat-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 10px 0 10px 0;
}
.mm-chat-section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.96rem;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.2px;
}
.mm-chat-section-badge {
    background: #EFF6FF;
    border: 1px solid #DBEAFE;
    border-radius: 9999px;
    padding: 3px 10px;
    font-size: 0.68rem;
    color: #3B82F6;
    font-weight: 500;
}

/* Quick Action Cards matching Image 3 */
.mm-qa-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 2px;
}
.mm-qa-card {
    background: #FFFFFF;
    border: 1.2px solid #E2E8F0;
    border-radius: 14px;
    cursor: pointer;
    transition: all 0.20s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}
.mm-qa-card:hover {
    border-color: #2563EB;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.12);
}

/* Full Width Card (Cards 1 & 2) */
.mm-qa-card-full {
    display: flex;
    align-items: center;
    padding: 12px 14px;
    gap: 12px;
}
.mm-qa-card-full .mm-qa-text {
    flex: 1;
    min-width: 0;
}
.mm-qa-card-full .mm-qa-title {
    font-size: 0.90rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.25;
}
.mm-qa-card-full .mm-qa-sub {
    font-size: 0.76rem;
    color: #64748B;
    margin-top: 3px;
    line-height: 1.25;
}
.mm-qa-chevron {
    color: #94A3B8;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.18s ease;
    flex-shrink: 0;
}
.mm-qa-card:hover .mm-qa-chevron {
    transform: translateX(3px);
    color: #2563EB;
}

/* Row 3: 3-column Grid */
.mm-qa-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}
.mm-qa-card-col {
    display: flex;
    flex-direction: column;
    padding: 10px 8px;
    justify-content: space-between;
    min-height: 80px;
}
.mm-qa-col-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
    margin-bottom: 4px;
}
.mm-qa-card-col .mm-qa-icon {
    width: 32px;
    height: 32px;
    min-width: 32px;
}
.mm-qa-col-title-wrap {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex: 1;
    min-width: 0;
    gap: 2px;
}
.mm-qa-card-col .mm-qa-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.mm-qa-card-col .mm-qa-sub {
    font-size: 0.67rem;
    color: #64748B;
    line-height: 1.25;
}

/* Row 4: 2-column Grid */
.mm-qa-grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}
.mm-qa-card-2col {
    display: flex;
    align-items: center;
    padding: 10px 10px;
    gap: 8px;
    min-height: 54px;
}
.mm-qa-card-2col .mm-qa-icon {
    width: 36px;
    height: 36px;
    min-width: 36px;
}
.mm-qa-card-2col .mm-qa-text {
    flex: 1;
    min-width: 0;
}
.mm-qa-card-2col .mm-qa-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.mm-qa-card-2col .mm-qa-sub {
    font-size: 0.68rem;
    color: #64748B;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
}

/* Icon Badges */
.mm-qa-icon {
    width: 42px;
    height: 42px;
    min-width: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.mm-qa-icon-doc { background: #E0F2FE; }
.mm-qa-icon-med { background: #F3E8FF; }
.mm-qa-icon-food { background: #DCFCE7; }
.mm-qa-icon-danger { background: #FEE2E2; }
.mm-qa-icon-yoga { background: #EDE9FE; }
.mm-qa-icon-lab { background: #E0F2FE; }
.mm-qa-icon-hospital { background: #D1FAE5; }

/* Input Bar matching Image 2 */
div[class*="st-key-slide_chat_form"] form,
.st-key-slide_chat_form [data-testid="stForm"] {
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 9999px !important;
    padding: 3px 6px 3px 16px !important;
    background: #FFFFFF !important;
    margin: 4px 12px 2px 12px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.2s ease !important;
}
div[class*="st-key-slide_chat_form"] form:focus-within,
.st-key-slide_chat_form [data-testid="stForm"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14) !important;
}
div[class*="st-key-slide_chat_form"] input {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 6px 0 !important;
    font-size: 0.84rem !important;
    color: #0F172A !important;
}
div[class*="st-key-slide_chat_form"] input::placeholder {
    color: #94A3B8 !important;
}
div[class*="st-key-slide_chat_form"] [data-testid="stFormSubmitButton"] button {
    width: 38px !important;
    height: 38px !important;
    min-width: 38px !important;
    min-height: 38px !important;
    border-radius: 50% !important;
    background: #0066FF !important;
    border: none !important;
    color: #FFFFFF !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    cursor: pointer !important;
    box-shadow: 0 4px 12px rgba(0, 102, 255, 0.4) !important;
    transition: all 0.18s ease !important;
}
div[class*="st-key-slide_chat_form"] [data-testid="stFormSubmitButton"] button:hover {
    background: #0052CC !important;
    transform: scale(1.08) !important;
}

/* Disclaimer below input */
.mm-chat-disclaimer {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    padding: 4px 14px 8px 14px !important;
    font-size: 0.70rem !important;
    color: #64748B !important;
    line-height: 1.35 !important;
    flex-shrink: 0 !important;
    box-sizing: border-box !important;
    margin: 0 !important;
    background: transparent !important;
}

/* Visible Action Buttons Container */
.st-key-slide_chat_drawer .mm-qa-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 4px;
    margin-bottom: 8px;
}

/* Dark Mode Comprehensive Overrides */
[data-theme="dark"] .st-key-slide_chat_drawer,
[data-theme="dark"] div.st-key-slide_chat_drawer,
[data-theme="dark"] div[data-testid="stVerticalBlock"]:has(> div.st-key-slide_chat_drawer) {
    background: #0B1220 !important;
    border-color: #1E293B !important;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.55), 0 0 1px rgba(255, 255, 255, 0.1) !important;
}
[data-theme="dark"] .st-key-popup_unified_header {
    background: linear-gradient(135deg, #071E3D 0%, #0F3460 50%, #1A56DB 100%) !important;
}
[data-theme="dark"] .st-key-drawer_close_x_btn button,
[data-theme="dark"] .st-key-drawer_clear_chat_btn button,
[data-theme="dark"] div[class*="st-key-drawer_close_x_btn"] button,
[data-theme="dark"] div[class*="st-key-drawer_clear_chat_btn"] button {
    background: #1E293B !important;
    border-color: #334155 !important;
    color: #F8FAFC !important;
}
[data-theme="dark"] .st-key-drawer_close_x_btn button:hover,
[data-theme="dark"] .st-key-drawer_clear_chat_btn button:hover {
    background: #334155 !important;
}
[data-theme="dark"] .mm-chat-context-card {
    background: rgba(14, 165, 233, 0.12) !important;
    border-color: rgba(14, 165, 233, 0.3) !important;
}
[data-theme="dark"] .mm-chat-context-icon {
    background: rgba(14, 165, 233, 0.22) !important;
}
[data-theme="dark"] .mm-chat-context-title {
    color: #38BDF8 !important;
}
[data-theme="dark"] .mm-chat-context-val {
    color: #7DD3FC !important;
}
[data-theme="dark"] .mm-chat-greeting-card {
    background: #141D2E !important;
    border-color: #1E293B !important;
}
[data-theme="dark"] .mm-chat-greeting-title {
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-chat-greeting-sub {
    color: #94A3B8 !important;
}
[data-theme="dark"] .mm-chat-section-title {
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-chat-section-badge {
    background: rgba(37, 99, 235, 0.20) !important;
    border-color: rgba(37, 99, 235, 0.45) !important;
    color: #60A5FA !important;
}
[data-theme="dark"] .mm-qa-card {
    background: #141D2E !important;
    border-color: #1E293B !important;
}
[data-theme="dark"] .mm-qa-card:hover {
    background: #1E293B !important;
    border-color: #38BDF8 !important;
}
[data-theme="dark"] .mm-qa-card-full .mm-qa-title,
[data-theme="dark"] .mm-qa-col-title-wrap .mm-qa-title,
[data-theme="dark"] .mm-qa-card-2col .mm-qa-title {
    color: #F8FAFC !important;
}
[data-theme="dark"] .mm-qa-card-full .mm-qa-sub,
[data-theme="dark"] .mm-qa-card-col .mm-qa-sub,
[data-theme="dark"] .mm-qa-card-2col .mm-qa-sub {
    color: #94A3B8 !important;
}
[data-theme="dark"] .mm-qa-card-full .mm-qa-chevron,
[data-theme="dark"] .mm-qa-col-title-wrap .mm-qa-chevron,
[data-theme="dark"] .mm-qa-card-2col .mm-qa-chevron {
    color: #64748B !important;
}
[data-theme="dark"] .mm-qa-icon-doc {
    background: rgba(37, 99, 235, 0.20) !important;
    border-color: rgba(37, 99, 235, 0.4) !important;
}
[data-theme="dark"] .mm-qa-icon-med {
    background: rgba(124, 58, 237, 0.20) !important;
    border-color: rgba(124, 58, 237, 0.4) !important;
}
[data-theme="dark"] .mm-qa-icon-food {
    background: rgba(22, 163, 74, 0.20) !important;
    border-color: rgba(22, 163, 74, 0.4) !important;
}
[data-theme="dark"] .mm-qa-icon-danger {
    background: rgba(220, 38, 38, 0.20) !important;
    border-color: rgba(220, 38, 38, 0.4) !important;
}
[data-theme="dark"] .mm-qa-icon-yoga {
    background: rgba(147, 51, 234, 0.20) !important;
    border-color: rgba(147, 51, 234, 0.4) !important;
}
[data-theme="dark"] .mm-qa-icon-lab {
    background: rgba(37, 99, 235, 0.20) !important;
    border-color: rgba(37, 99, 235, 0.4) !important;
}
[data-theme="dark"] .mm-qa-icon-hospital {
    background: rgba(5, 150, 105, 0.20) !important;
    border-color: rgba(5, 150, 105, 0.4) !important;
}
[data-theme="dark"] div[class*="st-key-slide_chat_form"] form,
[data-theme="dark"] .st-key-slide_chat_form [data-testid="stForm"] {
    background: #141D2E !important;
    border-color: #1E293B !important;
}
[data-theme="dark"] div[class*="st-key-slide_chat_form"] input {
    color: #F8FAFC !important;
}
[data-theme="dark"] div[class*="st-key-slide_chat_form"] input::placeholder {
    color: #64748B !important;
}
[data-theme="dark"] .mm-chat-disclaimer {
    color: #94A3B8 !important;
}

/* Quick Actions Action Cards (Direct Interactive Buttons) */
.st-key-slide_chat_drawer div[data-testid="stHorizontalBlock"] {
    gap: 8px !important;
    margin-bottom: 8px !important;
}
.st-key-slide_chat_drawer div[data-testid="stHorizontalBlock"] > div {
    min-width: 0 !important;
}

/* Base style for all 7 QA action buttons */
.st-key-dyn_chip_r1 button,
.st-key-dyn_chip_r2 button,
.st-key-dyn_chip_r3_1 button,
.st-key-dyn_chip_r3_2 button,
.st-key-dyn_chip_r3_3 button,
.st-key-dyn_chip_r4_1 button,
.st-key-dyn_chip_r4_2 button {
    background: #FFFFFF !important;
    border: 1.2px solid #E2E8F0 !important;
    border-radius: 14px !important;
    cursor: pointer !important;
    transition: all 0.20s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    position: relative !important;
    text-align: left !important;
    width: 100% !important;
    height: auto !important;
    margin: 0 0 8px 0 !important;
    overflow: hidden !important;
}

.st-key-dyn_chip_r1 button:hover,
.st-key-dyn_chip_r2 button:hover,
.st-key-dyn_chip_r3_1 button:hover,
.st-key-dyn_chip_r3_2 button:hover,
.st-key-dyn_chip_r3_3 button:hover,
.st-key-dyn_chip_r4_1 button:hover,
.st-key-dyn_chip_r4_2 button:hover {
    border-color: #2563EB !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.12) !important;
    background: #FFFFFF !important;
}

/* Typography inside QA buttons */
div[class*="st-key-dyn_chip_"] button div[data-testid="stMarkdownContainer"] {
    width: 100% !important;
    text-align: left !important;
}
div[class*="st-key-dyn_chip_"] button p {
    margin: 0 !important;
    text-align: left !important;
    line-height: 1.25 !important;
    color: #64748B !important;
    font-size: 0.76rem !important;
    font-weight: 400 !important;
}
div[class*="st-key-dyn_chip_"] button p strong {
    display: block !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    line-height: 1.25 !important;
    margin-bottom: 2px !important;
}

/* Card 1 & Card 2: Full-Width Row Cards */
.st-key-dyn_chip_r1 button,
.st-key-dyn_chip_r2 button {
    padding: 12px 36px 12px 62px !important;
    min-height: 58px !important;
    display: flex !important;
    align-items: center !important;
}
.st-key-dyn_chip_r1 button::after,
.st-key-dyn_chip_r2 button::after {
    content: '' !important;
    position: absolute !important;
    right: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 16px !important;
    height: 16px !important;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='9 18 15 12 9 6'/%3E%3C/svg%3E") no-repeat center !important;
    background-size: 14px 14px !important;
    transition: transform 0.18s ease !important;
}
.st-key-dyn_chip_r1 button:hover::after,
.st-key-dyn_chip_r2 button:hover::after {
    transform: translateY(-50%) translateX(3px) !important;
}

/* Card 1 Icon: Clinical Symptoms / Doc */
.st-key-dyn_chip_r1 button::before {
    content: '' !important;
    position: absolute !important;
    left: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 10px !important;
    background-color: #EFF6FF !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='4' y='2' width='16' height='20' rx='3' ry='3'/%3E%3Cline x1='8' y1='7' x2='16' y2='7'/%3E%3Cline x1='8' y1='11' x2='16' y2='11'/%3E%3Cline x1='8' y1='15' x2='13' y2='15'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 20px 20px !important;
}

/* Card 2 Icon: Medication Guidance / Stethoscope */
.st-key-dyn_chip_r2 button::before {
    content: '' !important;
    position: absolute !important;
    left: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 10px !important;
    background-color: #F5F3FF !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237C3AED' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4.5 3v5a5.5 5.5 0 0 0 11 0V3'/%3E%3Cpath d='M10 13.5v3.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-1.5'/%3E%3Ccircle cx='17' cy='15.5' r='2.5'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 20px 20px !important;
}

/* Row 3 & Row 4: 2 Column Compact Horizontal Cards (Food timing?, Danger signs, Yoga poses, Lab report) */
.st-key-dyn_chip_r3_1 button,
.st-key-dyn_chip_r3_2 button,
.st-key-dyn_chip_r3_3 button,
.st-key-dyn_chip_r4_1 button {
    padding: 10px 28px 10px 48px !important;
    min-height: 64px !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    text-align: left !important;
    justify-content: flex-start !important;
    overflow: visible !important;
    box-sizing: border-box !important;
}
.st-key-dyn_chip_r3_1 button div[data-testid="stMarkdownContainer"],
.st-key-dyn_chip_r3_2 button div[data-testid="stMarkdownContainer"],
.st-key-dyn_chip_r3_3 button div[data-testid="stMarkdownContainer"],
.st-key-dyn_chip_r4_1 button div[data-testid="stMarkdownContainer"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    width: 100% !important;
    text-align: left !important;
}
.st-key-dyn_chip_r3_1 button div[data-testid="stMarkdownContainer"] p,
.st-key-dyn_chip_r3_2 button div[data-testid="stMarkdownContainer"] p,
.st-key-dyn_chip_r3_3 button div[data-testid="stMarkdownContainer"] p,
.st-key-dyn_chip_r4_1 button div[data-testid="stMarkdownContainer"] p {
    display: flex !important;
    flex-direction: column !important;
    gap: 2px !important;
    margin: 0 !important;
    padding: 0 !important;
    font-size: 0.72rem !important;
    line-height: 1.25 !important;
    color: #64748B !important;
}
.st-key-dyn_chip_r3_1 button div[data-testid="stMarkdownContainer"] p br,
.st-key-dyn_chip_r3_2 button div[data-testid="stMarkdownContainer"] p br,
.st-key-dyn_chip_r3_3 button div[data-testid="stMarkdownContainer"] p br,
.st-key-dyn_chip_r4_1 button div[data-testid="stMarkdownContainer"] p br {
    display: none !important;
}
.st-key-dyn_chip_r3_1 button div[data-testid="stMarkdownContainer"] p strong,
.st-key-dyn_chip_r3_2 button div[data-testid="stMarkdownContainer"] p strong,
.st-key-dyn_chip_r3_3 button div[data-testid="stMarkdownContainer"] p strong,
.st-key-dyn_chip_r4_1 button div[data-testid="stMarkdownContainer"] p strong {
    font-size: 0.86rem !important;
    font-weight: 700 !important;
    line-height: 1.20 !important;
    color: #0F172A !important;
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
}

/* Right Chevron Arrows on 2-Column Cards */
.st-key-dyn_chip_r3_1 button::after,
.st-key-dyn_chip_r3_2 button::after,
.st-key-dyn_chip_r3_3 button::after,
.st-key-dyn_chip_r4_1 button::after {
    content: '' !important;
    position: absolute !important;
    right: 10px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 14px !important;
    height: 14px !important;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='9 18 15 12 9 6'/%3E%3C/svg%3E") no-repeat center !important;
    background-size: 12px 12px !important;
    transition: transform 0.18s ease !important;
}
.st-key-dyn_chip_r3_1 button:hover::after,
.st-key-dyn_chip_r3_2 button:hover::after,
.st-key-dyn_chip_r3_3 button:hover::after,
.st-key-dyn_chip_r4_1 button:hover::after {
    transform: translateY(-50%) translateX(2px) !important;
}

/* Left Icons for 2-Column Cards */
.st-key-dyn_chip_r3_1 button::before,
.st-key-dyn_chip_r3_2 button::before,
.st-key-dyn_chip_r3_3 button::before,
.st-key-dyn_chip_r4_1 button::before {
    content: '' !important;
    position: absolute !important;
    left: 10px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 30px !important;
    height: 30px !important;
    border-radius: 8px !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 16px 16px !important;
}
.st-key-dyn_chip_r3_1 button::before {
    background-color: #F0FDF4 !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2316A34A' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M18 2v20'/%3E%3Cpath d='M21 15a3 3 0 0 1-3 3h0a3 3 0 0 1-3-3V2'/%3E%3Cpath d='M3 2v6a3 3 0 0 0 6 0V2'/%3E%3Cpath d='M6 8v14'/%3E%3C/svg%3E") !important;
}
.st-key-dyn_chip_r3_2 button::before {
    background-color: #FEF2F2 !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23DC2626' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z'/%3E%3Cline x1='12' y1='9' x2='12' y2='13'/%3E%3Cline x1='12' y1='17' x2='12.01' y2='17'/%3E%3C/svg%3E") !important;
}
.st-key-dyn_chip_r3_3 button::before {
    background-color: #FAF5FF !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%239333EA'%3E%3Ccircle cx='12' cy='4.5' r='2.2'/%3E%3Cpath d='M15 8h-6c-1.1 0-2 .9-2 2v3c0 .55.45 1 1 1s1-.45 1-1v-2h1v7l-2.2 1.3c-.45.26-.6.85-.34 1.3.26.45.85.6 1.3.34L11 19.3V22h2v-2.7l2.24 1.24c.45.26 1.04.11 1.3-.34.26-.45.11-1.04-.34-1.3L14 17.5V10h1v2c0 .55.45 1 1 1s1-.45 1-1v-3c0-1.1-.9-2-2-2z'/%3E%3C/svg%3E") !important;
}
.st-key-dyn_chip_r4_1 button::before {
    background-color: #EFF6FF !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%232563EB' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 2v7.31L4.2 18.5a2 2 0 0 0 1.7 2.9h12.2a2 2 0 0 0 1.7-2.9L14 9.31V2'/%3E%3Cpath d='M8.5 2h7'/%3E%3Cpath d='M14 9.3h-4'/%3E%3C/svg%3E") !important;
}

/* Row 5: Full-Width Nearby Hospitals Card */
.st-key-dyn_chip_r4_2 button {
    padding: 12px 36px 12px 62px !important;
    min-height: 58px !important;
    display: flex !important;
    align-items: center !important;
}
.st-key-dyn_chip_r4_2 button::after {
    content: '' !important;
    position: absolute !important;
    right: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 16px !important;
    height: 16px !important;
    background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='9 18 15 12 9 6'/%3E%3C/svg%3E") no-repeat center !important;
    background-size: 14px 14px !important;
    transition: transform 0.18s ease !important;
}
.st-key-dyn_chip_r4_2 button:hover::after {
    transform: translateY(-50%) translateX(3px) !important;
}
.st-key-dyn_chip_r4_2 button::before {
    content: '' !important;
    position: absolute !important;
    left: 14px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 10px !important;
    background-color: #ECFDF5 !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23059669' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 21h18'/%3E%3Cpath d='M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16'/%3E%3Cpath d='M10 9h4'/%3E%3Cpath d='M12 7v4'/%3E%3Cpath d='M9 16h2'/%3E%3Cpath d='M13 16h2'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 20px 20px !important;
}

/* Dark Mode Overrides for QA Action Cards */
[data-theme="dark"] .st-key-dyn_chip_r1 button,
[data-theme="dark"] .st-key-dyn_chip_r2 button,
[data-theme="dark"] .st-key-dyn_chip_r3_1 button,
[data-theme="dark"] .st-key-dyn_chip_r3_2 button,
[data-theme="dark"] .st-key-dyn_chip_r3_3 button,
[data-theme="dark"] .st-key-dyn_chip_r4_1 button,
[data-theme="dark"] .st-key-dyn_chip_r4_2 button {
    background: #141D2E !important;
    border-color: #283347 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
}
[data-theme="dark"] .st-key-dyn_chip_r1 button:hover,
[data-theme="dark"] .st-key-dyn_chip_r2 button:hover,
[data-theme="dark"] .st-key-dyn_chip_r3_1 button:hover,
[data-theme="dark"] .st-key-dyn_chip_r3_2 button:hover,
[data-theme="dark"] .st-key-dyn_chip_r3_3 button:hover,
[data-theme="dark"] .st-key-dyn_chip_r4_1 button:hover,
[data-theme="dark"] .st-key-dyn_chip_r4_2 button:hover {
    background: #1A2540 !important;
    border-color: #38BDF8 !important;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.6) !important;
}
[data-theme="dark"] div[class*="st-key-dyn_chip_"] button p {
    color: #94A3B8 !important;
}
[data-theme="dark"] div[class*="st-key-dyn_chip_"] button p strong {
    color: #F8FAFC !important;
}
[data-theme="dark"] .st-key-dyn_chip_r1 button::before,
[data-theme="dark"] .st-key-dyn_chip_r2 button::before,
[data-theme="dark"] .st-key-dyn_chip_r3_1 button::before,
[data-theme="dark"] .st-key-dyn_chip_r3_2 button::before,
[data-theme="dark"] .st-key-dyn_chip_r3_3 button::before,
[data-theme="dark"] .st-key-dyn_chip_r4_1 button::before,
[data-theme="dark"] .st-key-dyn_chip_r4_2 button::before {
    background-color: #1E293B !important;
}
</style>
""", unsafe_allow_html=True)

# Dynamic rotation transform for medical cross button on open/close
st.markdown(f"""
<style>
.st-key-floating_ai_assistant button,
.st-key-floating_chat_pill button {{
    transform: {btn_transform} !important;
}}
.st-key-floating_ai_assistant button:hover,
.st-key-floating_chat_pill button:hover {{
    transform: {btn_transform} translateY(-5px) scale(1.10) !important;
    filter: drop-shadow(0 0 20px rgba(37, 99, 235, 1)) drop-shadow(0 0 36px rgba(6, 182, 212, 0.85)) drop-shadow(0 10px 22px rgba(0, 0, 0, 0.55)) !important;
}}
</style>
""", unsafe_allow_html=True)

# Floating '+' Trigger Button
st.button("＋", key="floating_ai_assistant", on_click=toggle_floating_chat, help="Open Clinical AI Assistant")

# Dynamic Clinical Context for Real AI Inquiries
current_context = {
    "symptoms": (st.session_state.get("selected_symptoms_list") or st.session_state.get("user_context", {}).get("symptoms", [])),
    "top_disease": st.session_state.get("p1_triage_results", {}).get("ranked_conditions", [{}])[0].get("name", "") if st.session_state.get("p1_triage_results") else (st.session_state.get("triage_result", {}).get("ranked_conditions", [{}])[0].get("name", "") if st.session_state.get("triage_result") else ""),
    "medicines": st.session_state.get("nlp_medicines", []),
    "age": st.session_state.get("user_context", {}).get("age", "Adult"),
    "gender": st.session_state.get("user_context", {}).get("gender", "Unspecified"),
    "conditions": st.session_state.get("user_context", {}).get("conditions", []),
    "allergies": st.session_state.get("user_context", {}).get("allergies", "None"),
    "medications": st.session_state.get("user_context", {}).get("medications", "None"),
    "family_history": st.session_state.get("user_context", {}).get("surgeries", "None")
}

if chat_is_open:
    # 1. Full-screen backdrop for outside-click to close
    st.markdown("""
    <div id="mm-chat-backdrop" onclick="const x = window.parent.document.querySelector('.st-key-drawer_close_x_btn button') || document.querySelector('.st-key-drawer_close_x_btn button'); if(x) x.click();"></div>
    """, unsafe_allow_html=True)

    with st.container(key="slide_chat_drawer"):
        # 2. Seamless Full-Width Blue Header with Clear Chat & Close Buttons (Image 2)
        with st.container(key="popup_unified_header"):
            hdr_c1, hdr_c2, hdr_c3 = st.columns([3.3, 0.48, 0.48], vertical_alignment="center")
            with hdr_c1:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 34px; height: 34px; border-radius: 50%; background: #0B1E3D; border: 1.6px solid #06B6D4; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 2px 8px rgba(6, 182, 212, 0.35);">
                        <svg viewBox="0 0 36 36" width="18" height="18" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="18" cy="4.5" r="2.2" fill="#FFFFFF"/>
                            <path d="M18 6.7V9.5" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
                            <rect x="7" y="9.5" width="22" height="19" rx="6" fill="#FFFFFF"/>
                            <rect x="3.5" y="14.5" width="3.5" height="9" rx="1.7" fill="#FFFFFF"/>
                            <rect x="29" y="14.5" width="3.5" height="9" rx="1.7" fill="#FFFFFF"/>
                            <rect x="9.5" y="12" width="17" height="14" rx="4" fill="#0B132B"/>
                            <circle cx="14" cy="17.5" r="2" fill="#38BDF8"/>
                            <circle cx="22" cy="17.5" r="2" fill="#38BDF8"/>
                            <path d="M14.5 22C16 23.2 20 23.2 21.5 22" stroke="#38BDF8" stroke-width="1.6" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div>
                        <div style="font-weight: 800; font-size: 0.90rem; color: #FFFFFF; line-height: 1.25; letter-spacing: -0.2px;">
                            DocMindX AI Clinical Assistant
                        </div>
                        <div style="font-size: 0.72rem; color: #E0E7FF; font-weight: 500; margin-top: 2px; display: flex; align-items: center; gap: 5px;">
                            <span style="color: #4ADE80; font-size: 0.65rem;">🟢</span> Online • Triage & Medical Guidance
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with hdr_c2:
                st.button("", key="drawer_clear_chat_btn", on_click=clear_floating_chat, help="Clear Chat History", icon=":material/refresh:")
            with hdr_c3:
                st.button("", key="drawer_close_x_btn", on_click=toggle_floating_chat, help="Close Assistant", icon=":material/close:")

        # Active Context Bar
        context_str = current_context.get("top_disease") or (", ".join(current_context.get("symptoms", [])[:2])) or "Peptic Ulcer Disease & Acid Peptic Disorders"
        st.markdown(f"""
        <div class="mm-chat-context-card">
            <div class="mm-chat-context-icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="4" y="2" width="16" height="20" rx="3" ry="3"></rect>
                    <line x1="8" y1="8" x2="16" y2="8"></line>
                    <line x1="8" y1="12" x2="16" y2="12"></line>
                    <line x1="8" y1="16" x2="12" y2="16"></line>
                </svg>
            </div>
            <div>
                <span class="mm-chat-context-title">Active Context:</span>
                <span class="mm-chat-context-val">{context_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. Scrollable Message & Interactive Suggestions Container
        chat_box = st.container(height=265)
        with chat_box:
            # A. Greeting Card with DocMindX robot avatar
            safe_markdown("""<div class="mm-chat-greeting-wrap">
<div class="mm-chat-avatar">
<svg viewBox="0 0 36 36" width="20" height="20" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="18" cy="4.5" r="2.2" fill="#FFFFFF"/>
<path d="M18 6.7V9.5" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
<rect x="7" y="9.5" width="22" height="19" rx="6" fill="#FFFFFF"/>
<rect x="3.5" y="14.5" width="3.5" height="9" rx="1.7" fill="#FFFFFF"/>
<rect x="29" y="14.5" width="3.5" height="9" rx="1.7" fill="#FFFFFF"/>
<rect x="9.5" y="12" width="17" height="14" rx="4" fill="#0B132B"/>
<circle cx="14" cy="17.5" r="2" fill="#38BDF8"/>
<circle cx="22" cy="17.5" r="2" fill="#38BDF8"/>
<path d="M14.5 22C16 23.2 20 23.2 21.5 22" stroke="#38BDF8" stroke-width="1.6" stroke-linecap="round"/>
</svg>
</div>
<div class="mm-chat-greeting-card">
<div class="mm-chat-greeting-title">Hello! I'm your <b>DocMindX Clinical AI Assistant</b>.</div>
<div class="mm-chat-greeting-sub">How can I help you today?</div>
</div>
</div>""")

            # B. Quick Actions Section Header
            safe_markdown("""<div class="mm-chat-section-header">
<div class="mm-chat-section-title">
<svg width="17" height="17" viewBox="0 0 24 24" fill="#2563EB" stroke="none">
<path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/>
</svg>
<span>Quick Actions</span>
</div>
<div class="mm-chat-section-badge">Choose a topic or type your question below.</div>
</div>""")

            # C. Rich Interactive Quick Action Cards
            if st.button("**Explain my symptoms in simple words**  \nGet easy-to-understand explanations", key="dyn_chip_r1", use_container_width=True):
                st.session_state["floating_chat_history"].append({"role": "user", "content": "Please explain my current symptoms and what they indicate in simple terms."})
                with st.spinner("Analyzing query..."):
                    reply = ask_DocMindX_ai("Please explain my current symptoms and what they indicate in simple terms.", st.session_state["floating_chat_history"], current_context, lang_code)
                st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
                st.rerun()

            if st.button("**Which medicine should I take?**  \nGet guidance on medications", key="dyn_chip_r2", use_container_width=True):
                st.session_state["floating_chat_history"].append({"role": "user", "content": "Can you explain the prescribed medicines and active compounds?"})
                with st.spinner("Analyzing query..."):
                    reply = ask_DocMindX_ai("Can you explain the prescribed medicines and active compounds?", st.session_state["floating_chat_history"], current_context, lang_code)
                st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
                st.rerun()

            col_qa3_1, col_qa3_2 = st.columns(2)
            with col_qa3_1:
                if st.button("**Food timing?**  \nDiet & meal guidance", key="dyn_chip_r3_1", use_container_width=True):
                    st.session_state["floating_chat_history"].append({"role": "user", "content": "When should I take my medicines with food?"})
                    with st.spinner("Analyzing query..."):
                        reply = ask_DocMindX_ai("When should I take my medicines with food?", st.session_state["floating_chat_history"], current_context, lang_code)
                    st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
                    st.rerun()
            with col_qa3_2:
                if st.button("**Danger signs**  \nImmediate care signs", key="dyn_chip_r3_2", use_container_width=True):
                    st.session_state["floating_chat_history"].append({"role": "user", "content": "What are emergency red flags and danger signs?"})
                    with st.spinner("Analyzing query..."):
                        reply = ask_DocMindX_ai("What are emergency red flags and danger signs?", st.session_state["floating_chat_history"], current_context, lang_code)
                    st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
                    st.rerun()

            col_qa4_1, col_qa4_2 = st.columns(2)
            with col_qa4_1:
                if st.button("**Yoga poses**  \nHelpful postures", key="dyn_chip_r3_3", use_container_width=True):
                    st.session_state["floating_chat_history"].append({"role": "user", "content": "Which restorative yoga postures will speed up my recovery?"})
                    with st.spinner("Analyzing query..."):
                        reply = ask_DocMindX_ai("Which restorative yoga postures will speed up my recovery?", st.session_state["floating_chat_history"], current_context, lang_code)
                    st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
                    st.rerun()
            with col_qa4_2:
                if st.button("**Lab report**  \nUpload & analyze reports", key="dyn_chip_r4_1", use_container_width=True):
                    st.session_state["floating_chat_history"].append({"role": "user", "content": "How and where do I scan my lab blood report or doctor prescription in DocMindX AI?"})
                    with st.spinner("Analyzing query..."):
                        reply = ask_DocMindX_ai("How and where do I scan my lab blood report or doctor prescription in DocMindX AI?", st.session_state["floating_chat_history"], current_context, lang_code)
                    st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
                    st.rerun()

            if st.button("**Nearby hospitals & emergency clinics**  \nFind trusted medical centers", key="dyn_chip_r4_2", use_container_width=True):
                st.session_state["floating_chat_history"].append({"role": "user", "content": "Where are nearby emergency hospitals and clinics and how do I find them?"})
                with st.spinner("Analyzing query..."):
                    reply = ask_DocMindX_ai("Where are nearby emergency hospitals and clinics and how do I find them?", st.session_state["floating_chat_history"], current_context, lang_code)
                st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
                st.rerun()

            # D. Dynamic Chat history messages
            if st.session_state["floating_chat_history"]:
                st.markdown("<div style='border-top: 1px dashed var(--mm-border-color); margin: 14px 0 12px 0;'></div>", unsafe_allow_html=True)
                for msg_idx, msg in enumerate(st.session_state["floating_chat_history"]):
                    if msg["role"] == "user":
                        st.markdown(f"""
                        <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                            <div style="background: #2563EB; color: #FFFFFF; border-radius: 14px 14px 2px 14px; padding: 8px 13px; max-width: 86%; font-size: 0.82rem; line-height: 1.35; word-break: break-word; box-shadow: 0 2px 6px rgba(37, 99, 235,0.3);">
                                {msg['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        ai_bubble_bg = "#1A2540" if is_dark else "rgba(255,255,255,0.9)"
                        ai_bubble_border = "#1E293B" if is_dark else "var(--mm-border-color)"
                        ai_bubble_text = "#E2E8F0" if is_dark else "var(--mm-text-primary)"
                        raw_ai_text = msg.get("content", "")
                        try:
                            clean_ai_html = markdown.markdown(raw_ai_text, extensions=['tables', 'fenced_code', 'nl2br'])
                        except Exception:
                            clean_ai_html = raw_ai_text.replace("\n", "<br/>")

                        st.markdown(f"""
                        <div style="display: flex; gap: 8px; align-items: flex-start; margin-bottom: 10px;">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background: #0B1E3D; border: 1.5px solid #06B6D4; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                                <svg viewBox="0 0 36 36" width="16" height="16" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="18" cy="4.5" r="2.2" fill="#FFFFFF"/>
                                    <path d="M18 6.7V9.5" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
                                    <rect x="7" y="9.5" width="22" height="19" rx="6" fill="#FFFFFF"/>
                                    <rect x="3.5" y="14.5" width="3.5" height="9" rx="1.7" fill="#FFFFFF"/>
                                    <rect x="29" y="14.5" width="3.5" height="9" rx="1.7" fill="#FFFFFF"/>
                                    <rect x="9.5" y="12" width="17" height="14" rx="4" fill="#0B132B"/>
                                    <circle cx="14" cy="17.5" r="2" fill="#38BDF8"/>
                                    <circle cx="22" cy="17.5" r="2" fill="#38BDF8"/>
                                    <path d="M14.5 22C16 23.2 20 23.2 21.5 22" stroke="#38BDF8" stroke-width="1.6" stroke-linecap="round"/>
                                </svg>
                            </div>
                            <div class="mm-ai-chat-bubble" style="background: {ai_bubble_bg}; color: {ai_bubble_text}; border-radius: 14px 14px 14px 2px; padding: 10px 12px; max-width: calc(100% - 38px); font-size: 0.82rem; line-height: 1.45; border: 1.2px solid {ai_bubble_border}; word-break: break-word; overflow-x: auto; box-sizing: border-box;">
                                {clean_ai_html}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        action = detect_redirect_action(msg.get("content", ""), lang_code)
                        if action:
                            st.markdown("<div style='margin: -2px 0 8px 36px;'>", unsafe_allow_html=True)
                            if st.button(f" {action['label']}", key=f"nav_action_btn_{msg_idx}", use_container_width=True):
                                st.session_state["active_panel"] = action["panel"]
                                st.session_state["floating_chat_open"] = False
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

        # 4. Chat Input Form (Pill with Circular Send Button matching Image 2)
        with st.form(key="slide_chat_form", clear_on_submit=True):
            fc_in, fc_btn = st.columns([5.3, 1], vertical_alignment="center")
            with fc_in:
                user_msg_input = st.text_input(
                    "Chat Input",
                    placeholder="Ask any medical, symptom, or medication question...",
                    key="floating_chat_user_input_val",
                    label_visibility="collapsed"
                )
            with fc_btn:
                send_pressed = st.form_submit_button("", icon=":material/send:", help="Send message")

        if send_pressed and user_msg_input and user_msg_input.strip():
            clean_user_q = user_msg_input.strip()
            st.session_state["floating_chat_history"].append({"role": "user", "content": clean_user_q})
            with st.spinner("Analyzing query..."):
                reply = ask_DocMindX_ai(clean_user_q, st.session_state["floating_chat_history"], current_context, lang_code)
            st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()

        # 5. Security & Medical Disclaimer Bar below input (Image 2 & 3)
        safe_markdown("""
        <div class="mm-chat-disclaimer">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#64748B" stroke="none">
                <path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3z"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round"/>
                <circle cx="12" cy="15.5" r="1.1" fill="#FFFFFF"/>
            </svg>
            <span>This AI provides general information only. Always consult a qualified doctor.</span>
        </div>
        """)

        # 6. Automatic Outside-Click Listener Script
        components.html("""
        <script>
        (function() {
            try {
                var parentDoc = window.parent.document;
                var drawer = parentDoc.querySelector('.st-key-slide_chat_drawer');
                var toggleBtn = parentDoc.querySelector('.st-key-floating_ai_assistant');
                var closeBtn = parentDoc.querySelector('.st-key-drawer_close_x_btn button');
                
                if (!drawer || !closeBtn) return;
                
                function handleOutsidePointer(e) {
                    if (!drawer.contains(e.target) && (!toggleBtn || !toggleBtn.contains(e.target))) {
                        parentDoc.removeEventListener('pointerdown', handleOutsidePointer, true);
                        closeBtn.click();
                    }
                }
                setTimeout(function() {
                    parentDoc.addEventListener('pointerdown', handleOutsidePointer, true);
                }, 200);
            } catch(e) {}
        })();
        </script>
        """, height=0)

        if st.session_state.get("pending_chat_query"):
            q_to_process = st.session_state.pop("pending_chat_query")
            with st.spinner("Analyzing query..."):
                reply = ask_DocMindX_ai(q_to_process, st.session_state["floating_chat_history"], current_context, lang_code)
            st.session_state["floating_chat_history"].append({"role": "assistant", "content": reply})
            st.rerun()


