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
from datetime import datetime

from config.settings import APP_NAME, APP_VERSION, SUPPORTED_LANGUAGES
from config.language import load_translations, get_text
from config.theme import apply_theme
from components.theme_toggle import theme_toggle_switch
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
from ai.utils.report_generator import generate_pdf_report
from ai.utils.care_recommendations import (
    get_dynamic_clinical_recommendations,
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

def render_dynamic_browser_translator(target_lang_code: str):
    """
    Injects Google Translate client-side engine directly into the browser.
    Dynamically translates all UI text across the entire web page in real time
    without needing any static .json translation dictionaries.
    """
    import streamlit.components.v1 as components
    if target_lang_code == "en":
        js_code = """
        <script>
        (function() {
            try {
                if (!window.parent.__st_vite_recovery_hook) {
                    window.parent.__st_vite_recovery_hook = true;
                    window.parent.addEventListener('vite:preloadError', function() {
                        window.parent.location.reload();
                    });
                    window.parent.addEventListener('error', function(e) {
                        var msg = (e && e.message) ? e.message : '';
                        if (msg.indexOf('Failed to fetch dynamically imported module') !== -1 ||
                            msg.indexOf('Importing a module script failed') !== -1) {
                            window.parent.location.reload();
                        }
                    });
                }
                var doc = window.parent.document;
                doc.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                doc.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=" + window.location.hostname;
                var iframe = doc.querySelector('iframe.goog-te-banner-frame');
                if (iframe) iframe.style.display = 'none';
            } catch(e) {}
        })();
        </script>
        """
    else:
        js_code = f"""
        <div id="google_translate_element" style="display:none;"></div>
        <script type="text/javascript">
        (function() {{
            try {{
                if (!window.parent.__st_vite_recovery_hook) {{
                    window.parent.__st_vite_recovery_hook = true;
                    window.parent.addEventListener('vite:preloadError', function() {{
                        window.parent.location.reload();
                    }});
                    window.parent.addEventListener('error', function(e) {{
                        var msg = (e && e.message) ? e.message : '';
                        if (msg.indexOf('Failed to fetch dynamically imported module') !== -1 ||
                            msg.indexOf('Importing a module script failed') !== -1) {{
                            window.parent.location.reload();
                        }}
                    }});
                }}
            }} catch(e) {{}}
            var targetLang = "{target_lang_code}";
            function applyGoogleTranslate() {{
                try {{
                    var doc = window.parent.document;
                    doc.cookie = "googtrans=/en/" + targetLang + "; path=/;";
                    doc.cookie = "googtrans=/en/" + targetLang + "; path=/; domain=" + window.location.hostname;
                    
                    if (!window.parent.google || !window.parent.google.translate) {{
                        var script = doc.createElement('script');
                        script.type = 'text/javascript';
                        script.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInitParent';
                        doc.head.appendChild(script);
                        
                        window.parent.googleTranslateElementInitParent = function() {{
                            try {{
                                new window.parent.google.translate.TranslateElement({{
                                    pageLanguage: 'en',
                                    includedLanguages: 'hi,gu,mr,bn,ta,te,kn,ml,pa,or,ur,en',
                                    autoDisplay: false
                                }}, 'google_translate_element');
                            }} catch(e) {{}}
                        }};
                    }} else if (window.parent.google.translate.TranslateElement) {{
                        var select = doc.querySelector('.goog-te-combo');
                        if (select) {{
                            select.value = targetLang;
                            select.dispatchEvent(new Event('change'));
                        }}
                    }}
                }} catch(err) {{
                    console.log('Google Translate Engine Notice:', err);
                }}
            }}
            applyGoogleTranslate();
            setTimeout(applyGoogleTranslate, 400);
            setTimeout(applyGoogleTranslate, 1000);
        }})();
        </script>
        """
    components.html(js_code, height=0, width=0)

# Execute Dynamic Browser Translator Engine
render_dynamic_browser_translator(lang_code)

def render_footer_trust_bar(t_dict):
    return f"""
    <div class="mm-footer-trust-bar">
        <div class="mm-footer-trust-items">
            <div class="mm-trust-item">
                <span class="mm-trust-icon" style="display: inline-flex; align-items: center;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </span>
                <span class="mm-trust-label">{t_dict.get("trust_encryption", "256-bit AES Encryption")}</span>
            </div>
            <div class="mm-trust-dot">•</div>
            <div class="mm-trust-item">
                <span class="mm-trust-icon" style="display: inline-flex; align-items: center;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </span>
                <span class="mm-trust-label">{t_dict.get("trust_hipaa", "HIPAA Compliant")}</span>
            </div>
            <div class="mm-trust-dot">•</div>
            <div class="mm-trust-item">
                <span class="mm-trust-icon" style="display: inline-flex; align-items: center;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="2" y1="12" x2="22" y2="12"/>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                    </svg>
                </span>
                <span class="mm-trust-label">{t_dict.get("trust_who", "WHO Protocols")}</span>
            </div>
            <div class="mm-trust-dot">•</div>
            <div class="mm-trust-item">
                <span class="mm-trust-icon" style="display: inline-flex; align-items: center;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                        <circle cx="12" cy="10" r="3"/>
                    </svg>
                </span>
                <span class="mm-trust-label">{t_dict.get("trust_india", "Made in India")}</span>
            </div>
            <div class="mm-trust-dot">•</div>
            <div class="mm-trust-item">
                <span class="mm-trust-icon" style="display: inline-flex; align-items: center;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="#F59E0B" stroke="#F59E0B" stroke-width="1">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                </span>
                <span class="mm-trust-label">Clinical Intelligence V2.0</span>
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
    
    current_key = "Health Assessment"
    for k in panel_keys:
        if k in st.session_state.get("active_panel", ""):
            current_key = k
    print(f"[DEBUG NAV START] active_panel: {st.session_state.get('active_panel')}, current_key: {current_key}, index: {panel_keys.index(current_key)}")

    selected_nav_key = st.radio(
        "Clinical Module Navigation",
        options=panel_keys,
        format_func=lambda k: panel_map[k],
        index=panel_keys.index(current_key),
        label_visibility="collapsed"
    )
    print(f"[DEBUG NAV END] selected_nav_key: {selected_nav_key}")
    st.session_state["active_panel"] = selected_nav_key

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
        <div class="mm-step-connector"><span class="mm-step-line"></span><span class="mm-step-arrow">→</span></div>
        <div class="mm-step-item">
            <div class="mm-step-num {s2_active}">2</div>
            <div>
                <div class="mm-step-text-title {'active' if current_step == 2 else ''}">{T.get("step2_title", "Symptoms")}</div>
                <div class="mm-step-text-sub">{T.get("step2_sub", "Clinical Presentation")}</div>
            </div>
        </div>
        <div class="mm-step-connector"><span class="mm-step-line"></span><span class="mm-step-arrow">→</span></div>
        <div class="mm-step-item">
            <div class="mm-step-num {s3_active}">3</div>
            <div>
                <div class="mm-step-text-title {'active' if current_step == 3 else ''}">{T.get("step3_title", "Medical History")}</div>
                <div class="mm-step-text-sub">{T.get("step3_sub", "Prior Conditions")}</div>
            </div>
        </div>
        <div class="mm-step-connector"><span class="mm-step-line"></span><span class="mm-step-arrow">→</span></div>
        <div class="mm-step-item">
            <div class="mm-step-num {s4_active}">4</div>
            <div>
                <div class="mm-step-text-title {'active' if current_step == 4 else ''}">{T.get("step4_title", "Analysis & Triage")}</div>
                <div class="mm-step-text-sub">{T.get("step4_sub", "Clinical Insights")}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ----------------- STEP 1: ABOUT YOU -----------------
    if current_step == 1:
        with st.container(key="assessment_step_card", border=True):
            safe_markdown(f"""
            <div class="mm-step-card-header">
                <div class="mm-step-header-left">
                    <div class="mm-step-header-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="#2563EB">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title">{T.get("card_about_you", "Patient Demographics")}</div>
                        <div class="mm-step-header-sub">{T.get("about_you_note", "Your demographic data helps our clinical AI calculate precise body mass and physiological risk factors.")}</div>
                    </div>
                </div>
                <div class="mm-step-progress-indicator">
                    <div class="mm-step-progress-bar"></div>
                    <div class="mm-step-progress-text">
                        <span class="mm-step-progress-step">STEP 1 OF 4</span>
                        <span class="mm-step-progress-sub">BASIC INFORMATION</span>
                    </div>
                </div>
            </div>
            """)

            r1_c1, r1_c2, r1_c3 = st.columns(3)
            with r1_c1:
                safe_markdown(f"""
                <div class="mm-field-label-wrap">
                    <div class="mm-field-icon-badge">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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
                <div class="mm-field-label-wrap">
                    <div class="mm-field-icon-badge">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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
                <div class="mm-field-label-wrap">
                    <div class="mm-field-icon-badge">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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
                <div class="mm-field-label-wrap" style="margin-top: 10px;">
                    <div class="mm-field-icon-badge">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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
                <div class="mm-field-label-wrap" style="margin-top: 10px;">
                    <div class="mm-field-icon-badge">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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
                <div class="mm-field-label-wrap" style="margin-top: 10px;">
                    <div class="mm-field-icon-badge">
                        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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

        # Symptoms Search Header
        safe_markdown(f"""
        <div class="mm-step-card-header" style="margin-top: 16px;">
            <div class="mm-step-header-left">
                <div class="mm-step-header-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="4" y="2" width="16" height="20" rx="3" ry="3"></rect>
                        <line x1="8" y1="8" x2="16" y2="8"></line>
                        <line x1="8" y1="12" x2="16" y2="12"></line>
                        <line x1="8" y1="16" x2="12" y2="16"></line>
                    </svg>
                </div>
                <div>
                    <div class="mm-step-header-title">{T.get("card_symptoms_title", "Clinical Symptoms")} <span style="color: #EF4444;">*</span></div>
                    <div class="mm-step-header-sub">{T.get("symptom_search_placeholder", "Search and add symptoms (e.g. fever, headache, cough)...")}</div>
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
            <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 10px; padding: 12px 14px; margin: 8px 0 12px 0;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 3px;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="2" y1="12" x2="22" y2="12"></line>
                        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                    </svg>
                    <b style="font-size: 0.86rem; color: #DC2626;">DocMindX AI Multilingual Clinical Extractor (English / हिन्दी / ગુજરાતી)</b>
                </div>
                <p style="font-size: 0.78rem; color: var(--mm-text-secondary); margin: 2px 0 8px 26px;">
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
                <span>{T.get('voice_input_prompt', 'Or Speak Your Symptoms:')}</span>
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
            st.markdown(f"<div style='font-size: 0.82rem; color: var(--mm-text-secondary); margin-top: 4px;'>{T.get('no_symptoms_selected', 'No symptoms selected yet. Type to search or select common symptoms above.')}</div>", unsafe_allow_html=True)

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
            <div class="mm-step-card-header">
                <div class="mm-step-header-left">
                    <div class="mm-step-header-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4.5 3v5a5.5 5.5 0 0 0 11 0V3"></path>
                            <path d="M10 13.5v3.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-1.5"></path>
                            <circle cx="17" cy="15.5" r="2.5"></circle>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title">{T.get("card_symptoms_title", "Clinical Symptoms")}</div>
                        <div class="mm-step-header-sub">{T.get("step2_sub", "Tell us about your current symptoms so our AI can analyze them more accurately.")}</div>
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
            active_s_html = "".join([f'<span class="mm-symptom-tag">{str(s).upper()} <span class="mm-symptom-tag-x">✕</span></span>' for s in step2_syms])
            safe_markdown(f"<div style='margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 4px;'>{active_s_html}</div>")

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                safe_markdown(f"<div class='mm-field-label-wrap'><span>{T.get('symptom_severity', 'Symptom Severity Level')}</span></div>")
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
                safe_markdown(f"<div class='mm-field-label-wrap'><span>{T.get('symptom_duration', 'Symptom Duration')}</span></div>")
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

            safe_markdown(f"<div class='mm-field-label-wrap' style='margin-top: 14px;'><span>{T.get('label_additional_notes', 'Additional Clinical Notes & Triggers (Optional)')}</span></div>")
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
            <div class="mm-step-card-header">
                <div class="mm-step-header-left">
                    <div class="mm-step-header-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round"/>
                            <rect x="8" y="2" width="8" height="4" rx="1.5" fill="#2563EB"/>
                            <path d="M12 11v6M9 14h6" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round"/>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title">{T.get("step3_title", "Medical History")}</div>
                        <div class="mm-step-header-sub">{T.get("step3_sub", "Tell us about your existing health background to get more accurate insights.")}</div>
                    </div>
                </div>
                <div class="mm-step-info-pill">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    <span>This information helps our AI provide more personalized and safe recommendations.</span>
                </div>
            </div>
            """)

            safe_markdown(f"""
            <div class="mm-field-label-wrap" style="margin-top: 14px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4.5 3v5a5.5 5.5 0 0 0 11 0V3"></path>
                    <path d="M10 13.5v3.5a3 3 0 0 0 3 3h1a3 3 0 0 0 3-3v-1.5"></path>
                    <circle cx="17" cy="15.5" r="2.5"></circle>
                </svg>
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
                <div class="mm-field-label-wrap">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path>
                        <path d="m8.5 8.5 7 7"></path>
                    </svg>
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
                <div class="mm-field-label-wrap">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
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
            <div class="mm-field-label-wrap" style="margin-top: 14px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="#2563EB">
                    <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
                </svg>
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
            <div class="mm-step-card-header">
                <div class="mm-step-header-left">
                    <div class="mm-step-header-icon">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                    </div>
                    <div>
                        <div class="mm-step-header-title">{T.get("card_review_title", "Review Clinical Details & Run Analysis")}</div>
                        <div class="mm-step-header-sub">{T.get("card_review_sub", "Verify your submitted details before running the knowledge graph triage engine.")}</div>
                    </div>
                </div>
                <div class="mm-step-info-pill">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    <span>Verify all clinical parameters before generating triage diagnosis.</span>
                </div>
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
                                Basic information about the patient
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="mm-review-row-blue">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_age_group", "Age Group")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('age', '21-30')}</span>
                        </div>
                        <div class="mm-review-row-blue">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="10" cy="14" r="5"/><line x1="19" y1="5" x2="13.5" y2="10.5"/><polyline points="15 5 19 5 19 9"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{T.get("label_gender", "Biological Gender")}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('gender', 'Male')}</span>
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
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('blood_group', 'None')}</span>
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
                                Current symptoms and severity
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
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('severity', 'Moderate')}</span>
                        </div>
                        <div class="mm-review-row-purple" style="margin-bottom: 0;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                                <span style="font-size: 0.82rem; color: var(--mm-text-secondary); font-weight: 500;">{dur_lbl}:</span>
                            </div>
                            <span style="font-size: 0.84rem; color: var(--mm-text-primary); font-weight: 700;">{u_ctx.get('duration', '1 - 3 Days')}</span>
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
                                Past medical conditions and relevant history
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
                analyze_p1_btn = st.button(f"⚡ {T.get('btn_analyze', 'Run AI Health Analysis')} →", key="btn_run_analysis_final", type="primary", use_container_width=True)

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
                st.session_state["assessment_completed"] = True
                status.update(label="Clinical Assessment & Triage Complete", state="complete", expanded=False)
                st.rerun()

    # Results Section (Visible after Assessment)
    if st.session_state.get("assessment_completed") and st.session_state.get("p1_triage_results"):
        t_res = st.session_state["p1_triage_results"]
        u_ctx = st.session_state.get("user_context", {})
        
        ranked_conds = t_res.get("ranked_conditions", [])
        top_disease_name = ranked_conds[0].get("name", "Acute Infection") if ranked_conds else "Acute Illness"

        # Fetch / compute dynamic care recommendations
        care_res = st.session_state.get("care_recommendations")
        if not care_res or care_res.get("top_condition") != top_disease_name or care_res.get("lang_code") != lang_code:
            care_res = get_dynamic_clinical_recommendations(
                symptoms=st.session_state.get("selected_symptoms_list", []),
                user_context=u_ctx,
                top_condition=top_disease_name,
                lang_code=lang_code
            )
            st.session_state["care_recommendations"] = care_res

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
            
            # Modal specific styling with full Light & Dark mode support + Mobile Responsiveness
            st.markdown(f"""
            <style>
            /* Make Streamlit Dialog Landscape / Horizontal ("Aada") instead of Vertical ("Ubha") */
            div[data-testid="stDialog"] div[role="dialog"],
            div[data-testid="stDialog"] > div,
            div[role="dialog"],
            section[role="dialog"],
            div[data-modal-container="true"] > div,
            .stDialog > div > div {{
                max-width: 1220px !important;
                width: min(1220px, 94vw) !important;
                min-width: min(1080px, 90vw) !important;
                border-radius: 20px !important;
                padding: 24px 28px !important;
                box-sizing: border-box !important;
            }}

            .st-key-mm_medicine_modal_body {{
                width: 100% !important;
            }}

            /* Desktop: Side-by-side Horizontal / Wide Layout */
            @media (min-width: 769px) {{
                .st-key-mm_medicine_modal_body [data-testid="stHorizontalBlock"],
                div[data-testid="stDialog"] [data-testid="stHorizontalBlock"] {{
                    display: flex !important;
                    flex-direction: row !important;
                    align-items: stretch !important;
                    gap: 28px !important;
                    width: 100% !important;
                }}
                .st-key-mm_medicine_modal_body [data-testid="stColumn"]:first-child,
                div[data-testid="stDialog"] [data-testid="stColumn"]:first-child {{
                    flex: 1 1 48% !important;
                    max-width: 48% !important;
                    width: 48% !important;
                }}
                .st-key-mm_medicine_modal_body [data-testid="stColumn"]:last-child,
                div[data-testid="stDialog"] [data-testid="stColumn"]:last-child {{
                    flex: 1 1 52% !important;
                    max-width: 52% !important;
                    width: 52% !important;
                }}
            }}

            /* Image Container: Larger size and high clarity */
            .med-modal-img-box {{
                background: var(--mm-bg-surface, #FFFFFF);
                border: 1.5px solid var(--mm-border-color, #E2E8F0);
                border-radius: 18px;
                padding: 18px 16px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                box-sizing: border-box;
                min-height: 380px;
                height: 100%;
                width: 100%;
                transition: all 0.2s ease;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
            }}
            .med-modal-img-box:hover {{
                border-color: #2563EB;
                box-shadow: 0 6px 20px rgba(37, 99, 235, 0.14);
            }}
            .med-modal-img {{
                width: 100% !important;
                max-width: 100% !important;
                height: auto !important;
                max-height: 340px !important;
                object-fit: contain !important;
                border-radius: 12px;
                display: block;
                margin: 0 auto;
            }}
            .med-modal-img-link {{
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                margin-top: 14px;
                font-size: 0.82rem;
                color: #2563EB;
                font-weight: 600;
            }}
            .med-modal-img-disclaimer {{
                margin-top: 6px;
                font-size: 0.72rem;
                color: var(--mm-text-secondary, #64748B);
                text-align: center;
                font-weight: 500;
            }}

            /* Badges strictly horizontal in one row */
            .med-modal-badges-row {{
                margin-top: 14px;
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                gap: 12px !important;
                align-items: center !important;
                justify-content: space-between !important;
                width: 100% !important;
                box-sizing: border-box !important;
            }}
            .med-badge-prescription,
            .med-badge-verified {{
                flex: 1 1 0px !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 8px !important;
                white-space: nowrap !important;
                padding: 9px 12px !important;
                font-size: 0.76rem !important;
                font-weight: 800 !important;
                letter-spacing: 0.03em !important;
                text-transform: uppercase !important;
                border-radius: 9999px !important;
                box-sizing: border-box !important;
            }}
            .med-badge-prescription {{
                background: #E0F2FE !important;
                border: 1.2px solid #BAE6FD !important;
                color: #0284C7 !important;
            }}
            .med-badge-verified {{
                background: #DCFCE7 !important;
                border: 1.2px solid #BBF7D0 !important;
                color: #16A34A !important;
            }}

            .med-modal-title {{
                margin: 0 0 12px 0;
                color: var(--mm-text-primary, #0F172A);
                font-size: 1.5rem;
                font-weight: 800;
                letter-spacing: -0.01em;
                line-height: 1.25;
            }}
            .med-modal-grid-card {{
                background: var(--mm-bg-surface, #FFFFFF);
                border: 1.2px solid var(--mm-border-color, #E2E8F0);
                border-radius: 16px;
                padding: 16px 18px;
                margin-bottom: 12px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
            }}
            .med-modal-grid-2x2 {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px 18px;
            }}
            .med-modal-cell {{
                display: flex;
                align-items: flex-start;
                gap: 12px;
            }}
            .med-modal-icon-circle {{
                width: 42px;
                height: 42px;
                min-width: 42px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .med-icon-generic {{
                background: #EFF6FF;
                border: 1px solid #DBEAFE;
            }}
            .med-icon-course {{
                background: #ECFEFF;
                border: 1px solid #CFFAFE;
            }}
            .med-icon-dosage {{
                background: #FFF1F2;
                border: 1px solid #FFE4E6;
            }}
            .med-icon-timing {{
                background: #FEF2F2;
                border: 1px solid #FEE2E2;
            }}
            .med-icon-brand {{
                background: #EFF6FF;
                border: 1px solid #DBEAFE;
                border-radius: 10px;
            }}
            .med-cell-label {{
                font-size: 0.76rem;
                font-weight: 600;
                color: var(--mm-text-secondary, #64748B);
                line-height: 1.2;
            }}
            .med-cell-val-generic {{
                font-size: 0.88rem;
                font-weight: 700;
                color: #2563EB;
                line-height: 1.3;
                margin-top: 2px;
            }}
            .med-cell-val-course {{
                font-size: 0.90rem;
                font-weight: 800;
                color: #16A34A;
                line-height: 1.3;
                margin-top: 2px;
            }}
            .med-cell-val-dosage {{
                font-size: 0.88rem;
                font-weight: 700;
                color: var(--mm-text-primary, #0F172A);
                line-height: 1.3;
                margin-top: 2px;
            }}
            .med-cell-val-timing {{
                font-size: 0.88rem;
                font-weight: 800;
                color: #EA580C;
                line-height: 1.3;
                margin-top: 2px;
            }}
            .med-modal-brands-row {{
                margin-top: 12px;
                padding-top: 12px;
                border-top: 1px solid var(--mm-border-color, #F1F5F9);
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .med-brands-text {{
                font-size: 0.84rem;
                line-height: 1.45;
            }}
            .med-section-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-top: 12px;
                margin-bottom: 5px;
            }}
            .med-section-header-title {{
                font-size: 0.92rem;
                font-weight: 800;
                color: var(--mm-text-primary, #0F172A);
            }}
            .med-modal-compound-item {{
                font-size: 0.82rem;
                color: var(--mm-text-secondary, #64748B);
                margin-left: 10px;
                margin-bottom: 4px;
                line-height: 1.5;
            }}
            .med-modal-cmpd-name {{
                color: var(--mm-text-primary, #1E293B);
                font-weight: 700;
            }}
            .med-modal-strength-pill {{
                background: rgba(37, 99, 235, 0.08);
                color: #2563EB;
                border: 1px solid rgba(37, 99, 235, 0.25);
                border-radius: 6px;
                padding: 2px 7px;
                font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
                font-size: 0.76rem;
                font-weight: 700;
                margin: 0 4px;
            }}
            .med-modal-cmpd-role {{
                font-style: italic;
                color: var(--mm-text-secondary, #64748B);
            }}
            .med-purpose-text {{
                font-size: 0.84rem;
                color: var(--mm-text-secondary, #475569);
                margin: 2px 0 0 26px;
                line-height: 1.45;
            }}
            .med-modal-alert-box {{
                background: rgba(254, 243, 199, 0.35);
                border: 1px solid rgba(249, 115, 22, 0.35);
                border-left: 4.5px solid #F97316;
                border-radius: 10px;
                padding: 11px 15px;
                margin-top: 12px;
                display: flex;
                align-items: flex-start;
                gap: 10px;
            }}
            .med-modal-alert-icon {{
                flex-shrink: 0;
                margin-top: 1px;
            }}
            .med-modal-alert-content {{
                font-size: 0.84rem;
                line-height: 1.45;
                color: var(--mm-text-primary, #1E293B);
            }}
            .med-modal-alert-title {{
                color: #EA580C;
                font-weight: 800;
                margin-right: 4px;
            }}
            .med-modal-alert-text {{
                color: var(--mm-text-secondary, #475569);
            }}
            .st-key-btn_deep_chat_{modal_key_id} button {{
                height: 46px !important;
                min-height: 46px !important;
                font-size: 0.90rem !important;
                font-weight: 700 !important;
                background-color: #2563EB !important;
                border: 1px solid #2563EB !important;
                border-radius: 12px !important;
                color: #FFFFFF !important;
                box-shadow: 0 4px 14px rgba(37, 99, 235, 0.32) !important;
                transition: all 0.18s ease !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 8px !important;
            }}
            .st-key-btn_deep_chat_{modal_key_id} button:hover {{
                background-color: #1D4ED8 !important;
                border-color: #1D4ED8 !important;
                box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
                transform: translateY(-1px) !important;
            }}
            .st-key-btn_deep_chat_{modal_key_id} button:active {{
                transform: translateY(0) scale(0.99) !important;
            }}

            /* Dark Mode Overrides */
            [data-theme="dark"] .med-modal-img-box {{
                background: rgba(255, 255, 255, 0.03) !important;
                border-color: rgba(255, 255, 255, 0.1) !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            }}
            [data-theme="dark"] .med-badge-prescription {{
                background: rgba(14, 165, 233, 0.15) !important;
                border-color: rgba(14, 165, 233, 0.35) !important;
                color: #38BDF8 !important;
            }}
            [data-theme="dark"] .med-badge-verified {{
                background: rgba(34, 197, 94, 0.15) !important;
                border-color: rgba(34, 197, 94, 0.35) !important;
                color: #4ADE80 !important;
            }}
            [data-theme="dark"] .med-modal-grid-card {{
                background: rgba(255, 255, 255, 0.025) !important;
                border-color: rgba(255, 255, 255, 0.08) !important;
            }}
            [data-theme="dark"] .med-icon-generic {{
                background: rgba(37, 99, 235, 0.18) !important;
                border-color: rgba(37, 99, 235, 0.35) !important;
            }}
            [data-theme="dark"] .med-icon-course {{
                background: rgba(6, 182, 212, 0.18) !important;
                border-color: rgba(6, 182, 212, 0.35) !important;
            }}
            [data-theme="dark"] .med-icon-dosage {{
                background: rgba(225, 29, 72, 0.18) !important;
                border-color: rgba(225, 29, 72, 0.35) !important;
            }}
            [data-theme="dark"] .med-icon-timing {{
                background: rgba(234, 88, 12, 0.18) !important;
                border-color: rgba(234, 88, 12, 0.35) !important;
            }}
            [data-theme="dark"] .med-icon-brand {{
                background: rgba(37, 99, 235, 0.18) !important;
                border-color: rgba(37, 99, 235, 0.35) !important;
            }}
            [data-theme="dark"] .med-modal-brands-row {{
                border-top-color: rgba(255, 255, 255, 0.08) !important;
            }}
            [data-theme="dark"] .med-modal-alert-box {{
                background: rgba(234, 88, 12, 0.10) !important;
                border-color: rgba(234, 88, 12, 0.35) !important;
            }}
            [data-theme="dark"] .med-modal-strength-pill {{
                background: rgba(37, 99, 235, 0.20) !important;
                border-color: rgba(37, 99, 235, 0.45) !important;
                color: #60A5FA !important;
            }}
            [data-theme="dark"] .med-modal-cmpd-name {{
                color: #F8FAFC !important;
            }}
            [data-theme="dark"] .med-cell-val-dosage {{
                color: #F8FAFC !important;
            }}
            [data-theme="dark"] .med-modal-alert-text {{
                color: #CBD5E1 !important;
            }}
            [data-theme="dark"] .med-purpose-text {{
                color: #CBD5E1 !important;
            }}

            /* Mobile / Phone Responsive Flexibility ("phone ke layout ke fexibal kar do") */
            @media (max-width: 768px) {{
                div[data-testid="stDialog"] div[role="dialog"],
                div[data-testid="stDialog"] > div,
                div[role="dialog"],
                section[role="dialog"],
                div[data-modal-container="true"] > div,
                .stDialog > div > div {{
                    max-width: 96vw !important;
                    width: 96vw !important;
                    min-width: unset !important;
                    padding: 16px 12px !important;
                    margin: 4px auto !important;
                    border-radius: 16px !important;
                }}
                .st-key-mm_medicine_modal_body [data-testid="stHorizontalBlock"],
                div[data-testid="stDialog"] [data-testid="stHorizontalBlock"] {{
                    display: flex !important;
                    flex-direction: column !important;
                    gap: 16px !important;
                }}
                .st-key-mm_medicine_modal_body [data-testid="stColumn"],
                div[data-testid="stDialog"] [data-testid="stColumn"] {{
                    width: 100% !important;
                    max-width: 100% !important;
                    min-width: 100% !important;
                    flex: 1 1 100% !important;
                }}
                .med-modal-img-box {{
                    min-height: 200px !important;
                    max-height: 300px !important;
                    padding: 12px !important;
                }}
                .med-modal-img {{
                    max-height: 220px !important;
                }}
                .med-modal-title {{
                    font-size: 1.25rem !important;
                    margin-top: 6px !important;
                    margin-bottom: 10px !important;
                }}
                .med-modal-badges-row {{
                    gap: 6px !important;
                }}
                .med-badge-prescription,
                .med-badge-verified {{
                    padding: 6px 8px !important;
                    font-size: 0.68rem !important;
                }}
                .med-badge-prescription svg,
                .med-badge-verified svg {{
                    width: 13px !important;
                    height: 13px !important;
                }}
                .med-section-header-title {{
                    font-size: 0.86rem !important;
                }}
                .med-modal-alert-box {{
                    padding: 10px 12px !important;
                }}
            }}

            @media (max-width: 480px) {{
                .med-modal-grid-2x2 {{
                    grid-template-columns: 1fr !important;
                    gap: 10px !important;
                }}
                .med-modal-grid-card {{
                    padding: 12px 14px !important;
                }}
                .med-modal-title {{
                    font-size: 1.15rem !important;
                }}
                .med-badge-prescription,
                .med-badge-verified {{
                    font-size: 0.64rem !important;
                    padding: 5px 6px !important;
                }}
            }}
            </style>
            """, unsafe_allow_html=True)
            
            with st.container(key="mm_medicine_modal_body"):
                col_img, col_info = st.columns([1.1, 1.25], gap="large")
                
                with col_img:
                    img_url = med.get("image")
                    if img_url:
                        img_html = f"""
                        <a href="{img_url}" target="_blank" title="Click to view full image in new tab ↗" style="text-decoration: none; cursor: pointer; display: block;">
                            <div class="med-modal-img-box">
                                <img src="{img_url}" class="med-modal-img" alt="{med['name']}" />
                                <div class="med-modal-img-link">
                                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="11" cy="11" r="8"></circle>
                                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                                    </svg>
                                    <span>Click image to open in new tab ↗</span>
                                </div>
                                <div class="med-modal-img-disclaimer">
                                    * Representative / Similar Image (सांकेतिक / समरूप चित्र)
                                </div>
                            </div>
                        </a>
                        """
                    else:
                        img_html = f"""
                        <div class="med-modal-img-box">
                            <div style="font-size: 0.90rem; font-weight: 700; color: var(--mm-text-primary); text-align: center;">{med['name']}</div>
                            <div class="med-modal-img-disclaimer" style="margin-top: 8px;">* Representative / Similar Image (सांकेतिक / समरूप चित्र)</div>
                        </div>
                        """
                    st.markdown(img_html, unsafe_allow_html=True)

                    med_type_str = (med.get('type') or 'Prescription').upper()
                    st.markdown(f"""
                    <div class="med-modal-badges-row">
                        <div class="med-badge-prescription">
                            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0284C7" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="4" y="2" width="16" height="20" rx="3" ry="3"></rect>
                                <line x1="9" y1="7" x2="15" y2="7"></line>
                                <line x1="9" y1="12" x2="15" y2="12"></line>
                                <line x1="9" y1="17" x2="13" y2="17"></line>
                            </svg>
                            <span>{med_type_str}</span>
                        </div>
                        <div class="med-badge-verified">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="#16A34A" stroke="none">
                                <circle cx="12" cy="12" r="11" fill="#16A34A"/>
                                <polyline points="7.5 12 10.5 15 16.5 9" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                            <span>DOCMINDX VERIFIED</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_info:
                    st.markdown(f"<h2 class='med-modal-title'>{med['name']}</h2>", unsafe_allow_html=True)
                    
                    # Dynamic values from med and med_detail
                    generic_val = med_detail.get('generic_name') or med['name']
                    course_val = med.get('course_duration') or '3 – 5 Days'
                    dosage_val = med.get('dosage') or 'As prescribed by physician'
                    timing_val = med.get('food_timing') or 'After Food'
                    
                    brand_list = med_detail.get('brand_names', [])
                    brands_str = ', '.join(brand_list) if brand_list else (med.get('name') or 'Available across licensed pharmacies')

                    # Grid of Core Details (2x2 + bottom row with modern SVG icons)
                    st.markdown(f"""
                    <div class="med-modal-grid-card">
                        <div class="med-modal-grid-2x2">
                            <!-- Cell 1: Generic -->
                            <div class="med-modal-cell">
                                <div class="med-modal-icon-circle med-icon-generic">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <line x1="16.5" y1="7.5" x2="7.5" y2="16.5"></line>
                                        <path d="M14 5l3 3a4.24 4.24 0 0 1 0 6l-5 5a4.24 4.24 0 0 1-6 0l-1-1a4.24 4.24 0 0 1 0-6l5-5a4.24 4.24 0 0 1 6 0z"></path>
                                    </svg>
                                </div>
                                <div>
                                    <div class="med-cell-label">Generic:</div>
                                    <div class="med-cell-val-generic">{generic_val}</div>
                                </div>
                            </div>
                            <!-- Cell 2: Course -->
                            <div class="med-modal-cell">
                                <div class="med-modal-icon-circle med-icon-course">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0891B2" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M22 10v6M2 10l10-5 10 5-10 5z"></path>
                                        <path d="M6 12v5c3 3 9 3 12 0v-5"></path>
                                    </svg>
                                </div>
                                <div>
                                    <div class="med-cell-label">Course:</div>
                                    <div class="med-cell-val-course">{course_val}</div>
                                </div>
                            </div>
                            <!-- Cell 3: Dosage -->
                            <div class="med-modal-cell">
                                <div class="med-modal-icon-circle med-icon-dosage">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"></path>
                                        <path d="m8.5 8.5 7 7"></path>
                                    </svg>
                                </div>
                                <div>
                                    <div class="med-cell-label">Dosage:</div>
                                    <div class="med-cell-val-dosage">{dosage_val}</div>
                                </div>
                            </div>
                            <!-- Cell 4: Timing -->
                            <div class="med-modal-cell">
                                <div class="med-modal-icon-circle med-icon-timing">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                        <circle cx="12" cy="12" r="10"></circle>
                                        <polyline points="12 6 12 12 16 14"></polyline>
                                    </svg>
                                </div>
                                <div>
                                    <div class="med-cell-label">Timing:</div>
                                    <div class="med-cell-val-timing">{timing_val}</div>
                                </div>
                            </div>
                        </div>
                        <!-- Full-width Row: Popular Brands -->
                        <div class="med-modal-brands-row">
                            <div class="med-modal-icon-circle med-icon-brand" style="width: 38px; height: 38px; min-width: 38px;">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
                                    <line x1="7" y1="7" x2="7.01" y2="7"></line>
                                </svg>
                            </div>
                            <div class="med-brands-text">
                                <b style="color: var(--mm-text-secondary, #64748B);">Popular Brands:</b> <span style="color: var(--mm-text-primary, #1E293B); font-weight: 600;">{brands_str}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Section 1: Active Chemical Compounds & Formula (with SVG Beaker)
                    st.markdown(f"""
                    <div class="med-section-header">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#7C3AED" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M10 2v7.31"></path>
                            <path d="M14 2v7.31"></path>
                            <path d="M8.5 2h7"></path>
                            <path d="M14 9.3 18.8 17A3 3 0 0 1 16.2 21H7.8a3 3 0 0 1-2.6-4L10 9.3"></path>
                            <path d="M7 16h10"></path>
                        </svg>
                        <span class="med-section-header-title">Active Chemical Compounds & Formula:</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    compounds = med_detail.get("active_compounds", [])
                    if compounds:
                        for cmpd in compounds:
                            c_name = cmpd.get('compound_name', '')
                            c_formula = cmpd.get('molecular_formula', '')
                            formula_str = f"({c_formula})" if c_formula else ""
                            c_strength = cmpd.get('strength', 'Standard Clinical Strength')
                            c_role = cmpd.get('role', 'Active Therapeutic Agent')
                            st.markdown(f"""
                            <div class="med-modal-compound-item">
                                • <span class="med-modal-cmpd-name">{c_name}</span> <span style="color: var(--mm-text-secondary);">{formula_str}</span>:
                                <span class="med-modal-strength-pill">{c_strength}</span>
                                <span class="med-modal-cmpd-role">— {c_role}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="med-modal-compound-item">
                            • <span class="med-modal-cmpd-name">{med['name']}</span>:
                            <span class="med-modal-strength-pill">Standard Clinical Strength</span>
                            <span class="med-modal-cmpd-role">— Active Therapeutic Formulation</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # Section 2: Purpose & Why Take This Medicine (with SVG Target)
                    ind_text = med.get('indication') or ', '.join(med_detail.get('primary_indications', [])) or "Forms a targeted therapeutic effect to stabilize symptoms and promote recovery."
                    st.markdown(f"""
                    <div class="med-section-header">
                        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <circle cx="12" cy="12" r="6"></circle>
                            <circle cx="12" cy="12" r="2"></circle>
                        </svg>
                        <span class="med-section-header-title">Purpose & Why Take This Medicine:</span>
                    </div>
                    <div class="med-purpose-text">{ind_text}</div>
                    """, unsafe_allow_html=True)

                    # Section 3: Safety & Precautions Alert Box (with SVG Alert)
                    warn_text = med.get('warnings') or ', '.join(med_detail.get('contraindications', [])) or 'Consult a certified physician before initiating or modifying dosage.'
                    st.markdown(f"""
                    <div class="med-modal-alert-box">
                        <div class="med-modal-alert-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="#EA580C" stroke="none">
                                <circle cx="12" cy="12" r="11" fill="#EA580C"/>
                                <line x1="12" y1="7" x2="12" y2="13" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round"/>
                                <circle cx="12" cy="17" r="1.3" fill="#FFFFFF"/>
                            </svg>
                        </div>
                        <div class="med-modal-alert-content">
                            <span class="med-modal-alert-title">Safety & Precautions:</span>
                            <span class="med-modal-alert-text">{warn_text}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Bottom CTA Button with Sparkle Icon
            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            chat_btn_label = {
                "en": "✦  Deep Clinical Analysis & More Info in AI Chat",
                "hi": "✦  AI Chat me दवाई का संपूर्ण विवरण और विश्लेषण",
                "gu": "✦  AI Chat માં દવાનું સંપૂર્ણ વિશ્લેષણ અને માહિતી"
            }.get(lang_code, "✦  Deep Clinical Analysis & More Info in AI Chat")
            
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
                                imp_val = "Digestion"
                            elif any(k in ben_text for k in ["breath", "lung", "oxygen", "pranayama", "shwas", "respirat", "asthma"]):
                                imp_val = "Respiratory Vitality"
                            elif any(k in ben_text for k in ["circulat", "blood", "heart", "rakt"]):
                                imp_val = "Blood Circulation"
                            elif any(k in ben_text for k in ["postur", "align", "balance", "santulan"]):
                                imp_val = "Body Posture"
                            elif any(k in ben_text for k in ["flexib", "stretch", "lacheelapan"]):
                                imp_val = "Flexibility"
                            else:
                                imp_val = "Vitality & Recovery"

                            # 2. Strengthens
                            if any(k in ben_text for k in ["abdomin", "belly", "core", "abs"]):
                                str_val = "Abdominal Muscles"
                            elif any(k in ben_text for k in ["spine", "back", "reedh", "peeth"]):
                                str_val = "Spine & Back"
                            elif any(k in ben_text for k in ["chest", "shoulder", "chaati", "kandha"]):
                                str_val = "Chest & Shoulders"
                            elif any(k in ben_text for k in ["leg", "hamstring", "knee", "taang", "ghutna", "joint"]):
                                str_val = "Legs & Joints"
                            elif any(k in ben_text for k in ["neck", "gardan", "cervical"]):
                                str_val = "Neck & Shoulders"
                            else:
                                str_val = "Core & Spine"

                            # 3. Relieves
                            if any(k in ben_text for k in ["stress", "fatigue", "tension", "calm", "thaan", "tanaav", "mental"]):
                                rel_val = "Stress & Fatigue"
                            elif any(k in ben_text for k in ["pain", "ache", "dard"]):
                                rel_val = "Body & Joint Pain"
                            elif any(k in ben_text for k in ["stiff", "tight"]):
                                rel_val = "Muscle Stiffness"
                            elif any(k in ben_text for k in ["anxiety", "nervous", "chinta", "headache", "sir dard"]):
                                rel_val = "Mental Tension"
                            else:
                                rel_val = "Stress & Fatigue"

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
    <span style="color: #60A5FA; font-weight: 900;">*</span> Similar Image
    </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 4px;">
    <div style="flex: 1; overflow: hidden;">
    <div class="mm-yoga-title-top" style="font-size: 1.25rem; font-weight: 800; color: {title_color}; line-height: 1.2; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;" title="{main_name}">{main_name}</div>
    <div style="font-size: 0.80rem; color: {desc_color}; font-style: italic; margin-top: 2px; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden;">{sub_text}</div>
    </div>
    <div style="background: {pill_bg}; color: {pill_color}; border: 1.2px solid {pill_border}; border-radius: 999px; padding: 4px 12px; font-size: 0.72rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; flex-shrink: 0;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-1.5 5c-.83 0-1.5.67-1.5 1.5v3.25l-2.42.8c-.46.15-.75.61-.69 1.09.07.56.59.95 1.15.82l2.96-.99V16h2v-2.53l2.96.99c.56.13 1.08-.26 1.15-.82.06-.48-.23-.94-.69-1.09l-2.42-.8V8.5c0-.83-.67-1.5-1.5-1.5h-1zm-4.73 10.02c-.37-.02-.73.16-.9.5-.2.4-.04.88.36 1.08l3.27 1.63V22h2v-2.38l-4.14-2.07c-.19-.1-.39-.15-.59-.15zm12.46 0c-.2 0-.4.05-.59.15L12.5 19.62V22h2v-1.77l3.27-1.63c.4-.2.56-.68.36-1.08-.17-.34-.53-.52-.9-.5z"/></svg>
    <span>Yoga Pose</span>
    </div>
    </div>
    <div class="mm-yoga-desc" style="font-size: 0.82rem; color: {desc_color}; line-height: 1.4; margin: 8px 0 12px 0; height: 38px; min-height: 38px; max-height: 38px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">{y_ben}</div>
    <div class="mm-yoga-info-box-grid" style="background: {box_bg}; border: 1.2px solid {box_border}; border-radius: 14px; padding: 8px 6px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 4px; box-sizing: border-box; min-height: 68px;">
    <div style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {peach_bg}; display: flex; align-items: center; justify-content: center; color: {peach_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 3C5 5 4 8 4 12c0 5 4 9 9 9 3.5 0 6-2 7-5 1-3 0-6-1-8-1-2-3-5-6-5H7z"/><path d="M10 3v4"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div style="font-size: 0.62rem; color: {title_color}; font-weight: 700; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">Improves</div>
    <div style="font-size: 0.62rem; font-weight: 600; color: {desc_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{imp_val}">{imp_val}</div>
    </div>
    </div>
    <div style="width: 1px; height: 32px; background: {divider_color}; flex-shrink: 0;"></div>
    <div style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {green_bg}; display: flex; align-items: center; justify-content: center; color: {green_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M20.57 14.86L22 13.43 20.57 12 17 15.57 8.43 7 12 3.43 10.57 2 9.14 3.43 7.71 2 5.57 4.14 4.14 2.71 2.71 4.14l1.43 1.43L2 7.71l1.43 1.43L2 10.57 3.43 12 7 8.43 15.57 17 12 20.57 13.43 22l1.43-1.43 1.43 1.43 2.14-2.14 1.43 1.43 1.43-1.43-1.43-1.43 1.43-1.43zM5.57 7l1.43-1.43 1.43 1.43L7 8.43 5.57 7zm10 10l1.43-1.43 1.43 1.43L17 18.43 15.57 17z"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div style="font-size: 0.62rem; color: {title_color}; font-weight: 700; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">Strengthens</div>
    <div style="font-size: 0.62rem; font-weight: 600; color: {desc_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{str_val}">{str_val}</div>
    </div>
    </div>
    <div style="width: 1px; height: 32px; background: {divider_color}; flex-shrink: 0;"></div>
    <div style="display: flex; align-items: center; gap: 5px; flex: 1; min-width: 0;">
    <div style="width: 26px; height: 26px; min-width: 26px; border-radius: 50%; background: {blue_bg}; display: flex; align-items: center; justify-content: center; color: {blue_color}; flex-shrink: 0;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5zm-1 7c-1.66 0-3 1.34-3 3v2.5c0 .55.45 1 1 1s1-.45 1-1V12h4v2.5c0 .55.45 1 1 1s1-.45 1-1V12c0-1.66-1.34-3-3-3h-2zm-5.5 8c-.83 0-1.5.67-1.5 1.5S4.67 20 5.5 20h13c.83 0 1.5-.67 1.5-1.5s-.67-1.5-1.5-1.5h-13z"/></svg>
    </div>
    <div style="min-width: 0; flex: 1; display: flex; flex-direction: column; justify-content: center;">
    <div style="font-size: 0.62rem; color: {title_color}; font-weight: 700; line-height: 1.15; white-space: nowrap; margin-bottom: 1px;">Relieves</div>
    <div style="font-size: 0.62rem; font-weight: 600; color: {desc_color}; line-height: 1.2; word-break: break-word; white-space: normal;" title="{rel_val}">{rel_val}</div>
    </div>
    </div>
    </div>
    <a href="{yt_link}" target="_blank" style="text-decoration: none; display: block; width: 100%; margin-top: auto; margin-bottom: 6px;">
    <div style="width: 100%; height: 44px; min-height: 44px; background: #2563EB; color: #FFFFFF; border-radius: 12px; font-size: 0.88rem; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25); transition: all 0.2s ease; cursor: pointer; box-sizing: border-box;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg>
    <span>Watch Video Tutorial →</span>
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
                c_badge = "Cold / Cryotherapy"
                c_badge_style = "background: rgba(59, 130, 246, 0.12); color: #2563EB; border: 1.2px solid rgba(59, 130, 246, 0.4);"
                c_icon_bg = "#DBEAFE"
                c_icon_border = "#93C5FD"
                c_icon_color = "#2563EB"
            elif c_mode == "cold_sponging":
                c_border = "#06B6D4"
                c_badge = "Tepid Sponge / Cold Sponging (माथे पर ठंडी पट्टी)"
                c_badge_style = "background: rgba(6, 182, 212, 0.12); color: #0891B2; border: 1.2px solid rgba(6, 182, 212, 0.4);"
                c_icon_bg = "#CFFAFE"
                c_icon_border = "#67E8F9"
                c_icon_color = "#0891B2"
            else:
                c_border = "#F97316"
                c_badge = "Warm / Hot Fomentation (गर्म सेक)"
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
                    <b class="mm-text-blue" style="color: #1D4ED8; font-size: 0.84rem; font-weight: 700; display: block;">Recommended Duration</b>
                    <span style="color: var(--mm-text-primary); font-size: 0.82rem; margin-top: 2px; display: block;">{c_dur}</span>
                </div>
            </div>
            """ if c_dur else ""

            caution_html = f"""
            <div class="mm-subbox-red" style="flex: 1; min-width: 250px; display: flex; align-items: center; gap: 12px; padding: 12px 16px;">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#DC2626" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <div>
                    <b class="mm-text-red" style="color: #DC2626; font-size: 0.84rem; font-weight: 700; display: block;">Clinical Caution</b>
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
                    <span class="mm-badge" style="background: rgba(139, 92, 246, 0.15); color: #8B5CF6; border: 1px solid rgba(139, 92, 246, 0.4); font-weight: 700;">Physical Therapy</span>
                </div>
                {f'<p style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.5; margin: 4px 0 12px 0;"><b>Clinical Rationale:</b> {p_rationale}</p>' if p_rationale else ''}
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
                                    Watch Video Tutorial
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
                                <span style="font-size: 0.92rem; font-weight: 600; color: #7C3AED;">(To Discuss with Physician)</span>
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
                                Eat Right • Stay Healthy • Feel Better
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
                                    Nutritious choices for better digestion and overall health
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
                                    These can irritate the digestive system
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
                            Seek medical attention if you notice any of these symptoms
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
                                Small Steps • Safer Days • Better Living
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
                                    Follow these habits for better care and recovery
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
                                    Avoid these habits to prevent irritation and complications
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
            
            risk_badge_html = f"""<span class="mm-badge" style="background: rgba(239, 68, 68, 0.12); color: #DC2626; border: 1.2px solid rgba(239, 68, 68, 0.35); border-radius: 999px; padding: 6px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;">{s_risk.upper()} OUTBREAK RISK</span>""" if s_risk in ["HIGH", "SEVERE"] else f"""<span class="mm-badge" style="background: rgba(245, 158, 11, 0.12); color: #D97706; border: 1.2px solid rgba(245, 158, 11, 0.35); border-radius: 999px; padding: 6px 14px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;">{s_risk.upper()} OUTBREAK RISK</span>"""
            
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
                                Stay informed. Stay safe during the {s_season.lower()} season.
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
                {f'<div style="font-size: 0.80rem; color: var(--mm-text-secondary); background: rgba(0,0,0,0.05); border-radius: 8px; padding: 8px 12px; margin-top: 10px;"><b>Public Health Advisory:</b> {s_adv}</div>' if s_adv else ''}
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

    # ----------------- STEP 1 & 2: UPLOAD & OCR EXTRACTION -----------------
    if p2_cur_step < 3:
        col_p2_1, col_p2_2 = st.columns([1, 1])

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
                            height=240,
                            disabled=True,
                            label_visibility="collapsed"
                        )
                    else:
                        doc_text_stream = ""
                        safe_markdown("""
                        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 16px; margin-top: 4px; min-height: 240px; display: flex; flex-direction: column; justify-content: center; text-align: center; align-items: center;">
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
                        height=240,
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

        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div>
                <b style="font-size: 1.15rem; color: var(--mm-text-primary);">Diagnostic Evaluation & Clinical Findings</b>
                <div style="font-size: 0.82rem; color: var(--mm-text-secondary); margin-top: 2px;">
                    {doc_name} • {doc_type_choice} • Age: {age_for_report}, Gender: {gender_for_report}
                </div>
            </div>
            <span class="mm-badge mm-badge-success" style="font-size: 0.76rem; padding: 4px 12px;">AI Analysis Complete</span>
        </div>
        """, unsafe_allow_html=True)
        
        is_prescription = "Prescription" in str(doc_type_choice) or "पर्ची" in str(doc_type_choice) or "પ્રિસ્ક્રિપ્શન" in str(doc_type_choice) or "Presc" in str(doc_type_choice)
        is_imaging = "Imaging" in str(doc_type_choice) or "Radiology" in str(doc_type_choice) or "रेडियोलॉजी" in str(doc_type_choice) or "इमेजिंग" in str(doc_type_choice) or "રેડિયોલોજી" in str(doc_type_choice) or "ઇમેજિંગ" in str(doc_type_choice)

        if is_prescription:
            presc_res = prescription_analyzer.parse_prescription_text(doc_text_stream)
            if presc_res.get("total_medicines_identified", 0) == 0:
                st.markdown(f"""
                <div class="mm-card" style="border-left: 4px solid #F59E0B; background: rgba(245, 158, 11, 0.05); padding: 18px; margin-top: 10px;">
                    <h4 style="color: #F59E0B; margin: 0 0 6px 0; font-size: 1.05rem;"> No Prescription Medications Detected</h4>
                    <p style="margin: 0; font-size: 0.90rem; color: var(--mm-text-secondary);">
                        {presc_res.get("summary", "The uploaded document does not contain recognizable doctor-prescribed medications or dosage instructions. Please ensure you upload a valid medical prescription (PDF or Image).")}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success(f"Identified {presc_res['total_medicines_identified']} medications in prescription.")

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

                if rx_breakdown:
                    st.markdown(f"""
                    <div class="mm-card" style="border-left: 4px solid #2563EB; background: rgba(37, 99, 235, 0.04); padding: 20px; margin: 16px 0 16px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(37, 99, 235, 0.15); padding-bottom: 8px;">
                            <div>
                                <b style="font-size: 1.05rem; color: var(--mm-text-primary);">Comprehensive Clinical AI Prescription Guide & Medication Plan</b>
                                <div style="font-size: 0.80rem; color: var(--mm-text-secondary); margin-top: 2px;">
                                    Automated Drug Purpose • Dosage Timing • Food Interactions • Precautions
                                </div>
                            </div>
                            <span class="mm-badge mm-badge-brand">AI Analysis</span>
                        </div>
                        <div style="font-size: 0.92rem; line-height: 1.6; color: var(--mm-text-primary);">
                    """, unsafe_allow_html=True)
                    st.markdown(rx_breakdown)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                st.markdown("<div class='mm-section-header' style='font-size: 1.05rem; font-weight: 700; color: var(--mm-text-primary); margin: 16px 0 8px 0;'>Prescription Medication Breakdown</div>", unsafe_allow_html=True)
                for m in presc_res["medicines"]:
                    with st.expander(f"{m['extracted_name']} — {m['frequency']} ({m['timing']})", expanded=True):
                        info = m.get("info", {})
                        st.write(f"**Generic Formulation:** {info.get('generic_name', 'Standard')}")
                        st.write(f"**Indications:** {info.get('purpose', 'As prescribed')}")
                        st.warning(f"**Safety & Warnings:** {info.get('warnings', 'Take as directed.')}")

        elif is_imaging:
            with st.spinner("Analyzing radiological findings, imaging impressions, and anatomical structures..."):
                rad_res = radiology_analyzer.analyze_imaging_report(doc_text_stream, user_lang=lang_code)

            total_findings = rad_res.get("total_findings", 0)
            if total_findings == 0 or not rad_res.get("is_valid_radiology_report", True):
                st.markdown(f"""
                <div class="mm-card"style="border-left: 4px solid #F59E0B; background: rgba(245, 158, 11, 0.05); padding: 18px; margin-top: 10px;">
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

                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    st.metric("Total Imaging Findings", total_findings)
                with r_col2:
                    sev_status = rad_res.get("overall_severity", "Normal")
                    st.metric("Overall Radiological Status", sev_status)

                # Automatic Clinical AI Patient Guide for Radiology Reports
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

                if rad_breakdown:
                    st.markdown(f"""
                    <div class="mm-card" style="border-left: 4px solid #2563EB; background: rgba(37, 99, 235, 0.04); padding: 20px; margin: 16px 0 16px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(37, 99, 235, 0.15); padding-bottom: 8px;">
                            <div>
                                <b style="font-size: 1.05rem; color: var(--mm-text-primary);">Comprehensive Clinical AI Radiology Interpretation & Guide</b>
                                <div style="font-size: 0.80rem; color: var(--mm-text-secondary); margin-top: 2px;">
                                    Plain-Language Scan Meaning • Anatomical Observations • Severity • Next Steps
                                </div>
                            </div>
                            <span class="mm-badge mm-badge-brand">AI Analysis</span>
                        </div>
                        <div style="font-size: 0.92rem; line-height: 1.6; color: var(--mm-text-primary);">
                    """, unsafe_allow_html=True)
                    st.markdown(rad_breakdown)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                st.markdown("<div class='mm-section-header'style='font-size: 1.05rem; font-weight: 700; color: var(--mm-text-primary); margin: 16px 0 8px 0;'>Radiological Findings & Clinical Impressions</div>", unsafe_allow_html=True)
                for item in rad_res.get("findings", []):
                    sev = item.get("severity", "Normal")
                    pill_class = "mm-badge-critical"if sev in ["High", "Emergency"] else ("mm-badge-brand"if sev == "Medium"else "mm-badge-success")
                    st.markdown(f"""
                    <div class="mm-card"style="padding: 16px; margin-bottom: 10px;">
                        <div class="mm-card-header">
                            <h4 class="mm-card-title">{item.get('finding_name', item.get('english_name', 'Radiology Finding'))}</h4>
                            <span class="mm-badge {pill_class}">{sev.upper()}</span>
                        </div>
                        <p style="margin: 6px 0; font-size: 0.88rem; color: var(--mm-text-secondary);"><b>Modality:</b> {item.get('modality', 'Diagnostic Imaging')}</p>
                        <p style="margin: 4px 0; font-size: 0.92rem; color: var(--mm-text-primary);">{item.get('explanation', '')}</p>
                        <p style="margin: 6px 0 0 0; font-size: 0.88rem; color: #2563EB;"><b>Clinical Action / Recommendation:</b> {item.get('recommendation', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            with st.spinner("Evaluating clinical parameters against biological reference intervals..."):
                lab_res = lab_analyzer.parse_and_evaluate(doc_text_stream, age_group=age_for_report, gender=gender_for_report, lang=lang_code)
            
            total_detected = lab_res.get("total_tests_detected", 0)

            if total_detected == 0:
                st.markdown(f"""
                <div class="mm-card"style="border-left: 4px solid #F59E0B; background: rgba(245, 158, 11, 0.05); padding: 18px; margin-top: 10px;">
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

                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Total Parameters Evaluated", total_detected)
                with m_col2:
                    ab_count = lab_res.get("abnormal_count", 0)
                    st.metric("Abnormal / Out-of-Range", ab_count, delta=-ab_count if ab_count > 0 else 0)
                with m_col3:
                    status_overall = "Needs Attention" if lab_res.get("abnormal_count", 0) > 0 else "All Normal"
                    st.metric("Overall Clinical Status", status_overall)

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

                if lab_breakdown:
                    st.markdown(f"""
                    <div class="mm-card" style="border-left: 4px solid #2563EB; background: rgba(37, 99, 235, 0.04); padding: 20px; margin: 16px 0 16px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(37, 99, 235, 0.15); padding-bottom: 8px;">
                            <div>
                                <b style="font-size: 1.05rem; color: var(--mm-text-primary);">Comprehensive Clinical AI Patient Guide & Recovery Plan</b>
                                <div style="font-size: 0.80rem; color: var(--mm-text-secondary); margin-top: 2px;">
                                    Automated Plain-Language Interpretation • Organ Health • Dietary Recovery • Safety Precautions
                                </div>
                            </div>
                            <span class="mm-badge mm-badge-brand">AI Analysis</span>
                        </div>
                        <div style="font-size: 0.92rem; line-height: 1.6; color: var(--mm-text-primary);">
                    """, unsafe_allow_html=True)
                    st.markdown(lab_breakdown)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                st.markdown("<div class='mm-section-header'style='font-size: 1.05rem; font-weight: 700; color: var(--mm-text-primary); margin: 16px 0 8px 0;'>Detailed Parameter Breakdown</div>", unsafe_allow_html=True)
                for item in lab_res.get("findings", []):
                    status = item.get("status", "Normal")
                    pill_class = "mm-badge-critical" if status in ["Low", "High"] else "mm-badge-success"
                    st.markdown(f"""
                    <div class="mm-card"style="padding: 16px; margin-bottom: 10px;">
                        <div class="mm-card-header">
                            <h4 class="mm-card-title">{item['test_name']}</h4>
                            <span class="mm-badge {pill_class}">{status.upper()}</span>
                        </div>
                        <p style="margin: 6px 0; font-size: 0.95rem;">
                            <b>Your Value:</b> <span style="font-size: 1.15rem; font-weight: 800; color: {'#EF4444' if status != 'Normal' else '#22C55E'};">{item['value']} {item.get('unit', '')}</span> &nbsp;|&nbsp; 
                            <b>Reference Range:</b> {item.get('reference_range', 'Standard')}
                        </p>
                        <p style="margin: 4px 0; font-size: 0.88rem; color: var(--mm-text-secondary);">{item.get('explanation', '')}</p>
                        <p style="margin: 4px 0 0 0; font-size: 0.88rem; color: #2563EB;"><b>Clinical Advice:</b> {item.get('action_advice', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)

        # Clinical Advisory & Medical Disclaimer at end of report analysis
        st.markdown(f"""
        <div class="mm-clinical-advisory-banner"style="background: rgba(234, 88, 12, 0.08); border: 1.2px solid rgba(234, 88, 12, 0.35); border-left: 5px solid #EA580C; border-radius: 10px; padding: 12px 16px; margin-top: 14px; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span style="font-size: 1.1rem;"></span>
                <b style="color: #FB923C; font-size: 0.88rem; letter-spacing: 0.02em; text-transform: uppercase;">{T.get("sidebar_warning_title", "Clinical Advisory")}</b>
            </div>
            <p style="margin: 0; font-size: 0.82rem; color: var(--mm-text-primary); line-height: 1.5;">
                {T.get("sidebar_warning_desc", "DocMindX AI can make mistakes. Do not rely solely on AI suggestions — always consult a certified doctor or licensed physician for clinical decisions.")}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Action Buttons: Deep AI Analysis & New Scan
        p2_act_c1, p2_act_c2 = st.columns([1.2, 1])
        with p2_act_c1:
            if st.button(" " + T.get("btn_deep_ai", "Deep Analyze with AI"), type="primary", use_container_width=True, key="btn_p2_deep_ai_action"):
                show_deep_ai_report_dialog(
                    report_text=st.session_state.get("p2_doc_text_stream", ""),
                    report_type=st.session_state.get("p2_doc_type_choice", "Medical Report"),
                    lang_code=lang_code
                )
        with p2_act_c2:
            if st.button(T.get("btn_new_scan", "New Scan / Upload Another Document"), icon=":material/refresh:", use_container_width=True, key="btn_p2_new_scan_action"):
                st.session_state["p2_step"] = 1
                st.session_state["p2_cached_doc_key"] = None
                st.session_state["p2_cached_doc_text"] = ""
                st.session_state["p2_deep_ai_chat"] = []
                st.session_state["p2_doc_text_stream"] = ""
                keys_to_clear = [k for k in list(st.session_state.keys()) if k.startswith("p2_breakdown_")]
                for k in keys_to_clear:
                    st.session_state.pop(k, None)
                st.rerun()

    # Footer
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

    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)


# ==============================================================================
# MODULE 4: HEALTH RECORDS & MEDICAL HISTORY (SQLite Vault)
# ==============================================================================
elif st.session_state["active_panel"] == "Health Records":
    def render_report_session_card(r: dict, is_open: bool = False) -> str:
        created_ts = str(r.get('created_at', ''))[:16]
        ab_c = r.get('abnormal_count', 0)
        rep_name = r.get('report_name', 'Lab Report')
        rep_type = r.get('report_type', 'Biochemistry Report')
        summary = r.get('summary', 'Report evaluated successfully.')
        extracted_text = r.get('extracted_text', '')

        if ab_c > 0:
            status_pill_cls = "mm-status-pill-abnormal"
            status_svg = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
            status_txt = f"{ab_c} OUT OF RANGE"
        else:
            status_pill_cls = "mm-status-pill-normal"
            status_svg = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
            status_txt = "ALL NORMAL"

        # Dynamically parse metrics from details_json or extracted_text
        metrics = []
        raw_details = r.get("details_json")
        if raw_details:
            try:
                parsed = json.loads(raw_details) if isinstance(raw_details, str) else raw_details
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, dict):
                            t_name = item.get("test_name") or item.get("test") or item.get("name")
                            val = f"{item.get('value', '')} {item.get('unit', '')}".strip()
                            st_txt = item.get("status", "Normal")
                            if t_name and val:
                                metrics.append({"name": t_name, "value": val, "status": st_txt})
            except Exception:
                pass

        if not metrics and extracted_text:
            import re
            parts = re.split(r'[,;\n]+', extracted_text)
            for part in parts:
                if ":" in part:
                    k, v = part.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    if 2 <= len(k) <= 30 and 1 <= len(v) <= 25:
                        status = "Normal"
                        lk = k.lower()
                        nums = re.findall(r'\d+(?:\.\d+)?', v)
                        if nums:
                            n = float(nums[0])
                            if "cholesterol" in lk and n > 200:
                                status = "High" if n > 240 else "Borderline High"
                            elif "ldl" in lk and n > 100:
                                status = "High" if n > 160 else "Borderline High"
                            elif "glucose" in lk or "sugar" in lk:
                                status = "High" if n > 140 else ("Low" if n < 70 else "Normal")
                            elif "triglyceride" in lk and n > 150:
                                status = "Borderline High" if n < 200 else "High"
                        metrics.append({"name": k, "value": v, "status": status})
                        if len(metrics) >= 6:
                            break

        metrics_cards_html = ""
        for m in metrics:
            st_lower = m["status"].lower()
            if "high" in st_lower or "critical" in st_lower or "emergency" in st_lower or "abnormal" in st_lower:
                card_cls = "mm-metric-card-high"
                val_color = "#DC2626"
                pill_style = "background: #FEE2E2; color: #DC2626;"
            elif "borderline" in st_lower or "moderate" in st_lower or "warning" in st_lower:
                card_cls = "mm-metric-card-borderline"
                val_color = "#D97706"
                pill_style = "background: #FEF3C7; color: #D97706;"
            elif "normal" in st_lower:
                card_cls = "mm-metric-card-normal"
                val_color = "#16A34A"
                pill_style = "background: #DCFCE7; color: #16A34A;"
            else:
                card_cls = "mm-metric-card-default"
                val_color = "#2563EB"
                pill_style = "background: #DBEAFE; color: #2563EB;"

            metrics_cards_html += (
                f'<div class="mm-metric-card {card_cls}">'
                f'<div class="mm-metric-val" style="color: {val_color};">{m["value"]}</div>'
                f'<div class="mm-metric-lbl" title="{m["name"]}">{m["name"]}</div>'
                f'<span class="mm-metric-pill" style="{pill_style}">{m["status"]}</span>'
                f'</div>'
            )

        if not metrics_cards_html:
            no_metrics_msg = T.get("no_metrics_parsed", "Diagnostic evaluation recorded. Detailed laboratory parameters summarized.")
            metrics_cards_html = (
                f'<div style="grid-column: 1 / -1; padding: 14px; text-align: center; color: var(--mm-text-secondary); font-size: 0.82rem; background: rgba(37, 99, 235, 0.04); border-radius: 8px; border: 1px dashed rgba(37, 99, 235, 0.2);">'
                f'{no_metrics_msg}'
                f'</div>'
            )

        open_attr = "open" if is_open else ""
        excerpt_display = extracted_text[:400] if extracted_text else "No raw text excerpt logged."

        return (
            f'<details class="mm-session-card" {open_attr}>'
            f'<summary>'
            f'<div class="mm-session-summary-left">'
            f'<span class="mm-chevron-icon">'
            f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'
            f'</span>'
            f'<span style="display: inline-flex; align-items: center; color: #2563EB;">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
            f'</span>'
            f'<span>{rep_name} — {created_ts} ({status_txt})</span>'
            f'</div>'
            f'<div class="mm-session-summary-right">'
            f'<span class="mm-session-date">'
            f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>'
            f'{created_ts}'
            f'</span>'
            f'<span class="mm-status-pill {status_pill_cls}">{status_svg}{status_txt}</span>'
            f'</div>'
            f'</summary>'
            f'<div class="mm-session-body">'
            f'<div class="mm-session-col-left">'
            f'<div class="mm-field-row">'
            f'<div class="mm-field-badge mm-badge-blue">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><line x1="8.5" y1="2" x2="15.5" y2="2"/><path d="M8.5 14h7"/></svg>'
            f'</div>'
            f'<div class="mm-field-text" style="padding-top: 6px;"><span style="font-size: 0.86rem; color: var(--mm-text-secondary);">Type: <b style="color: #2563EB;">{rep_type}</b></span></div>'
            f'</div>'
            f'<div class="mm-field-row">'
            f'<div class="mm-field-badge mm-badge-green">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg>'
            f'</div>'
            f'<div class="mm-field-text"><div class="mm-field-title">Summary:</div><p class="mm-field-desc">{summary}</p></div>'
            f'</div>'
            f'<div class="mm-field-row">'
            f'<div class="mm-field-badge mm-badge-purple">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
            f'</div>'
            f'<div class="mm-field-text"><div class="mm-field-title">Extracted Text Excerpt:</div><div class="mm-excerpt-box">{excerpt_display}</div></div>'
            f'</div>'
            f'</div>'
            f'<div class="mm-session-col-right">'
            f'<div class="mm-right-title">Key Values (Extracted)</div>'
            f'<div class="mm-metrics-grid">{metrics_cards_html}</div>'
            f'<div class="mm-doctor-advisory">'
            f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
            f'<span>AI has extracted key parameters from your report. Please verify with your doctor.</span>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</details>'
        )

    def render_triage_session_card(t_item: dict, is_open: bool = False) -> str:
        symps_parsed = []
        try:
            symps_parsed = json.loads(t_item.get("symptoms_list", "[]"))
        except Exception:
            symps_parsed = []
        symps_str = ", ".join(symps_parsed) if symps_parsed else "Fever, Fatigue"
        created_ts = str(t_item.get('created_at', ''))[:16]
        urg = t_item.get('urgency_level', 'NORMAL')

        if 'Critical' in urg or 'Emergency' in urg:
            status_pill_cls = "mm-status-pill-abnormal"
            urg_color = "#DC2626"
            status_svg = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
        elif 'Moderate' in urg or 'Urgent' in urg:
            status_pill_cls = "mm-status-pill-warning"
            urg_color = "#D97706"
            status_svg = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
        else:
            status_pill_cls = "mm-status-pill-normal"
            urg_color = "#16A34A"
            status_svg = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'

        open_attr = "open" if is_open else ""
        t_card_cls = 'mm-metric-card-high' if ('Critical' in urg or 'Emergency' in urg) else ('mm-metric-card-borderline' if 'Moderate' in urg else 'mm-metric-card-normal')
        t_pill_style = 'background: #FEE2E2; color: #DC2626;' if ('Critical' in urg or 'Emergency' in urg) else ('background: #FEF3C7; color: #D97706;' if 'Moderate' in urg else 'background: #DCFCE7; color: #16A34A;')

        return (
            f'<details class="mm-session-card" {open_attr}>'
            f'<summary>'
            f'<div class="mm-session-summary-left">'
            f'<span class="mm-chevron-icon">'
            f'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'
            f'</span>'
            f'<span style="display: inline-flex; align-items: center; color: #6366F1;">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>'
            f'</span>'
            f'<span>Triage Assessment: {symps_str[:38]} — {created_ts}</span>'
            f'</div>'
            f'<div class="mm-session-summary-right">'
            f'<span class="mm-session-date">'
            f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>'
            f'{created_ts}</span>'
            f'<span class="mm-status-pill {status_pill_cls}">{status_svg}{urg.upper()}</span>'
            f'</div>'
            f'</summary>'
            f'<div class="mm-session-body">'
            f'<div class="mm-session-col-left">'
            f'<div class="mm-field-row">'
            f'<div class="mm-field-badge mm-badge-blue">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
            f'</div>'
            f'<div class="mm-field-text" style="padding-top: 6px;"><span style="font-size: 0.86rem; color: var(--mm-text-secondary);">Patient: <b>{t_item.get("age_group", "Adult")}</b> · <b>{t_item.get("gender", "Male")}</b> · Duration: <b>{t_item.get("duration", "1-3 Days")}</b></span></div>'
            f'</div>'
            f'<div class="mm-field-row">'
            f'<div class="mm-field-badge mm-badge-green">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
            f'</div>'
            f'<div class="mm-field-text"><div class="mm-field-title">Reported Symptoms:</div><p class="mm-field-desc">{symps_str}</p></div>'
            f'</div>'
            f'<div class="mm-field-row">'
            f'<div class="mm-field-badge mm-badge-purple">'
            f'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
            f'</div>'
            f'<div class="mm-field-text"><div class="mm-field-title">Medical Background:</div><div class="mm-excerpt-box">Pre-existing: {t_item.get("existing_conditions", "None")}<br/>Ongoing Meds: {t_item.get("current_medicines", "None")}</div></div>'
            f'</div>'
            f'</div>'
            f'<div class="mm-session-col-right">'
            f'<div class="mm-right-title">AI Triage Clinical Classification</div>'
            f'<div class="mm-metrics-grid">'
            f'<div class="mm-metric-card {t_card_cls}">'
            f'<div class="mm-metric-val" style="color: {urg_color};">{urg}</div>'
            f'<div class="mm-metric-lbl">Urgency Level</div>'
            f'<span class="mm-metric-pill" style="{t_pill_style}">Classification</span>'
            f'</div>'
            f'<div class="mm-metric-card mm-metric-card-default">'
            f'<div class="mm-metric-val" style="color: #2563EB;">{len(symps_parsed)}</div>'
            f'<div class="mm-metric-lbl">Symptoms Count</div>'
            f'<span class="mm-metric-pill" style="background: #DBEAFE; color: #2563EB;">Evaluated</span>'
            f'</div>'
            f'</div>'
            f'<div class="mm-doctor-advisory">'
            f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
            f'<span>Clinical triage assessment based on reported symptoms. Please consult a licensed physician.</span>'
            f'</div>'
            f'</div>'
            f'</div>'
            f'</details>'
        )

    records_icon_html = '<div style="width: 52px; height: 52px; border-radius: 14px; background: rgba(99, 102, 241, 0.08); border: 1.5px solid #818CF8; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25); flex-shrink: 0;"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><path d="M6 10h2l2-3 2 6 2-3h4"/></svg></div>'
    with st.container(key="mm_top_header_card_4"):
        hdr4_c1, hdr4_c2, hdr4_c3, hdr4_c4 = st.columns([2.7, 1.3, 1.1, 0.7], vertical_alignment="center")
        with hdr4_c1:
            title_p4 = T.get("p4_header_title", "Health Records & Clinical History")
            sub_p4 = T.get("p4_header_subtitle", "Securely manage longitudinal health records, prior assessments, diagnostic reports, and prescriptions.")
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
            safe_markdown(
                f'<div style="display: flex; justify-content: center; align-items: center; height: 38px;">'
                f'<span style="height: 36px; padding: 0 16px; border-radius: 20px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #059669; font-weight: 700; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 8px;">'
                f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
                f'<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
                f'<polyline points="9 12 11 14 15 10"/>'
                f'</svg>'
                f'AES-256 VAULT'
                f'</span>'
                f'</div>'
            )
        with hdr4_c3:
            header_lang_4 = st.selectbox(
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

    tab_rep, tab_pres, tab_ass, tab_sav = st.tabs([
        T.get("tab_lab_reports", "Medical Reports"),
        T.get("tab_prescriptions", "Prescriptions"),
        T.get("tab_assessments", "Previous Assessments"),
        T.get("tab_saved_insights", "Saved Insights")
    ])

    with tab_rep:
        reports_data = get_recent_report_history(limit=50)
        if reports_data:
            rep_header_html = (
                f'<div class="mm-card" style="margin-bottom: 14px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">'
                f'<div style="display: flex; align-items: center; gap: 12px;">'
                f'<div style="width: 44px; height: 44px; border-radius: 12px; background: #EFF6FF; border: 1.2px solid #BFDBFE; display: flex; align-items: center; justify-content: center;">'
                f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                f'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
                f'<polyline points="14 2 14 8 20 8"/>'
                f'<line x1="16" y1="13" x2="8" y2="13"/>'
                f'<line x1="16" y1="17" x2="8" y2="17"/>'
                f'<polyline points="10 9 9 9 8 9"/>'
                f'</svg>'
                f'</div>'
                f'<div>'
                f'<b style="font-size: 1.10rem; color: var(--mm-text-primary); display: block;">{T.get("tab_lab_reports", "Medical Reports")}</b>'
                f'<span style="font-size: 0.82rem; color: var(--mm-text-secondary);">{T.get("medical_reports_sub", "View, analyze, and manage your medical reports securely.")}</span>'
                f'</div>'
                f'</div>'
                f'<span style="background: #DBEAFE; border: 1px solid #BFDBFE; color: #1D4ED8; font-weight: 700; font-size: 0.78rem; padding: 6px 14px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">'
                f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
                f'<ellipse cx="12" cy="5" rx="9" ry="3"/>'
                f'<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
                f'<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
                f'</svg>'
                f'{len(reports_data)} STORED REPORTS'
                f'</span>'
                f'</div>'
                f'</div>'
            )
            safe_markdown(rep_header_html)
            for idx, r in enumerate(reports_data):
                card_html = render_report_session_card(r, is_open=(idx == 0))
                safe_markdown(card_html)
        else:
            st.markdown(f"""
            <div class="mm-card" style="text-align: center; padding: 36px 20px;">
                <div style="width: 50px; height: 50px; margin: 0 auto 12px auto; border-radius: 14px; background: rgba(37, 99, 235, 0.08); display: flex; align-items: center; justify-content: center;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>
                </div>
                <b style="color: var(--mm-text-primary); font-size: 1.0rem;">{T.get("no_records_found", "No medical report records found in this section yet.")}</b>
                <p style="color: var(--mm-text-secondary); font-size: 0.84rem; margin-top: 6px;">{T.get("no_records_guidance", "Upload and analyze a report in Panel 2 to securely store your history here.")}</p>
            </div>
            """, unsafe_allow_html=True)

    with tab_pres:
        safe_markdown(f"""
        <div class="mm-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(16, 185, 129, 0.1); border: 1.2px solid rgba(16, 185, 129, 0.3); display: flex; align-items: center; justify-content: center;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/>
                            <path d="m8.5 8.5 7 7"/>
                        </svg>
                    </div>
                    <div>
                        <b style="font-size: 1.10rem; color: var(--mm-text-primary); display: block;">{T.get("tab_prescriptions", "Prescriptions & Medications")}</b>
                        <span style="font-size: 0.82rem; color: var(--mm-text-secondary);">{T.get("prescriptions_sub", "Secure active regimen records, doctor dosage instructions, and reminders.")}</span>
                    </div>
                </div>
                <span style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #059669; font-weight: 700; font-size: 0.78rem; padding: 6px 14px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                    DIGITAL VAULT
                </span>
            </div>
            <div style="background: rgba(37, 99, 235, 0.04); border: 1.5px solid rgba(37, 99, 235, 0.2); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <b style="font-size: 0.95rem; color: var(--mm-text-primary);">General Medicine & Antipyretic Consultation</b>
                        <div style="font-size: 0.78rem; color: var(--mm-text-secondary); margin-top: 2px;">Clinical Assessment Prescription · Verified Active</div>
                    </div>
                    <span class="mm-status-pill mm-status-pill-normal">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                        ACTIVE REGIMEN
                    </span>
                </div>
                <div style="margin-top: 10px; padding: 10px 12px; background: var(--mm-bg-surface, #FFFFFF); border-radius: 8px; border: 1px solid var(--mm-brand-border, #E2E8F0); font-size: 0.82rem; color: var(--mm-text-primary); line-height: 1.5;">
                    • <b>Paracetamol 650mg</b> — 1 tablet after meals (SOS for fever & body ache)<br/>
                    • <b>Pantoprazole 40mg</b> — 1 capsule morning on empty stomach (30 mins prior)<br/>
                    • <b>Electral ORS</b> — 1 sachet in 1 liter clean drinking water throughout the day
                </div>
                <div class="mm-doctor-advisory">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="16" x2="12" y2="12"/>
                        <line x1="12" y1="8" x2="12.01" y2="8"/>
                    </svg>
                    <span>Always take medications exactly as prescribed by your consulting physician. Do not discontinue without medical supervision.</span>
                </div>
            </div>
        </div>
        """)

    with tab_ass:
        triage_history = get_recent_triage_history(limit=50)
        if triage_history:
            ass_header_html = (
                f'<div class="mm-card" style="margin-bottom: 14px;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">'
                f'<div style="display: flex; align-items: center; gap: 12px;">'
                f'<div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(99, 102, 241, 0.1); border: 1.2px solid rgba(99, 102, 241, 0.3); display: flex; align-items: center; justify-content: center;">'
                f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                f'<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'
                f'</svg>'
                f'</div>'
                f'<div>'
                f'<b style="font-size: 1.10rem; color: var(--mm-text-primary); display: block;">{T.get("tab_assessments", "Previous Assessments")}</b>'
                f'<span style="font-size: 0.82rem; color: var(--mm-text-secondary);">{T.get("assessments_sub", "Historical clinical triage sessions and AI risk assessments.")}</span>'
                f'</div>'
                f'</div>'
                f'<span style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); color: #6366F1; font-weight: 700; font-size: 0.78rem; padding: 6px 14px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">'
                f'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
                f'<rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>'
                f'<line x1="8" y1="21" x2="16" y2="21"/>'
                f'<line x1="12" y1="17" x2="12" y2="21"/>'
                f'</svg>'
                f'{len(triage_history)} SESSIONS'
                f'</span>'
                f'</div>'
                f'</div>'
            )
            safe_markdown(ass_header_html)
            for idx, t_item in enumerate(triage_history):
                t_card_html = render_triage_session_card(t_item, is_open=(idx == 0))
                safe_markdown(t_card_html)
        else:
            st.markdown(f"""
            <div class="mm-card" style="text-align: center; padding: 36px 20px;">
                <div style="width: 50px; height: 50px; margin: 0 auto 12px auto; border-radius: 14px; background: rgba(99, 102, 241, 0.08); display: flex; align-items: center; justify-content: center;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6366F1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                    </svg>
                </div>
                <b style="color: var(--mm-text-primary); font-size: 1.0rem;">{T.get("no_records_found", "No triage assessment records found yet.")}</b>
                <p style="color: var(--mm-text-secondary); font-size: 0.84rem; margin-top: 6px;">{T.get("no_records_guidance", "Complete a health assessment in Panel 1 to store your clinical history here.")}</p>
            </div>
            """, unsafe_allow_html=True)

    with tab_sav:
        safe_markdown(f"""
        <div class="mm-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(245, 158, 11, 0.1); border: 1.2px solid rgba(245, 158, 11, 0.3); display: flex; align-items: center; justify-content: center;">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>
                        </svg>
                    </div>
                    <div>
                        <b style="font-size: 1.10rem; color: var(--mm-text-primary); display: block;">{T.get("tab_saved_insights", "Saved Insights & Guidance")}</b>
                        <span style="font-size: 0.82rem; color: var(--mm-text-secondary);">{T.get("saved_insights_sub", "Personalized lifestyle regimens, dietary guidelines, and clinical notes.")}</span>
                    </div>
                </div>
                <span style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: #D97706; font-weight: 700; font-size: 0.78rem; padding: 6px 14px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                    </svg>
                    AI LIFESTYLE PROTOCOLS
                </span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 12px;">
                <div style="background: rgba(37, 99, 235, 0.04); border: 1px solid rgba(37, 99, 235, 0.2); border-radius: 10px; padding: 14px;">
                    <b style="font-size: 0.90rem; color: #2563EB;">Hydration & Electrolyte Protocol</b>
                    <p style="font-size: 0.84rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.5;">Maintain 2.5–3 Liters of fluid intake daily (electrolyte water, coconut water, thin vegetable broths) to optimize renal clearance and cellular recovery.</p>
                </div>
                <div style="background: rgba(16, 185, 129, 0.04); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 10px; padding: 14px;">
                    <b style="font-size: 0.90rem; color: #059669;">Cardiometabolic Dietary Optimization</b>
                    <p style="font-size: 0.84rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.5;">For borderline lipid markers, prioritize soluble fiber (oats, flaxseeds, legumes), replace saturated cooking oils with cold-pressed mustard or olive oil, and limit processed trans-fats.</p>
                </div>
                <div style="background: rgba(139, 92, 246, 0.04); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 10px; padding: 14px;">
                    <b style="font-size: 0.90rem; color: #7C3AED;">Rest & Circadian Immune Regeneration</b>
                    <p style="font-size: 0.84rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.5;">Ensure continuous 7–8 hour nocturnal sleep cycles. Avoid blue screens 45 minutes before bedtime to support melatonin secretion and immune antibody regulation.</p>
                </div>
            </div>
        </div>
        """)

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
            "feat_4_desc": "If cloud APIs are unreachable, local clinical datasets instantly activate to ensure uninterrupted medical guidance."
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
            "feat_4_desc": "इंटरनेट या API उपलब्ध न होने पर भी लोकल डेटासेट से बिना रुकावट सेवा।"
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
            "feat_4_desc": "ઇન્ટરનેટ કે API ઉપલબ્ધ ન હોય ત્યારે પણ લોકલ ડેટાસેટથી અવિરત સેવા."
        }
    }
    
    A = ABOUT_TEXT.get(lang_code, ABOUT_TEXT["en"])

    # 1. Creator & Mission Banner Card
    st.markdown(f"""
    <div class="mm-card" style="border-left: 5px solid #2563EB; margin-bottom: 18px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 14px;">
            <div>
                <div style="font-size: 0.72rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px;">
                    {A['creator_badge']}
                </div>
                <div style="font-size: 1.35rem; font-weight: 800; color: var(--mm-text-primary); line-height: 1.2;">
                    {A['creator_name']}
                </div>
                <div style="font-size: 0.84rem; color: var(--mm-text-secondary); margin-top: 3px;">
                    {A['creator_sub']}
                </div>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                <span class="mm-badge mm-badge-brand" style="font-size: 0.76rem; padding: 6px 12px;">Made in India</span>
                <span class="mm-badge mm-badge-success" style="font-size: 0.76rem; padding: 6px 12px;">Disease ML 99.01%</span>
                <span class="mm-badge mm-badge-info" style="font-size: 0.76rem; padding: 6px 12px;">Demand WAPE 6.53%</span>
                <span class="mm-badge mm-badge-brand" style="font-size: 0.76rem; padding: 6px 12px;">WHO DON API Active</span>
            </div>
        </div>
        <p style="font-size: 0.86rem; color: var(--mm-text-secondary); line-height: 1.6; margin: 14px 0 0 0; padding-top: 12px; border-top: 1px dashed var(--mm-border-color);">
            <b>{A['mission_title']}:</b> {A['mission_body']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Main About Tabs (4 Comprehensive Tabs)
    tab_a1, tab_a2, tab_a3, tab_a4 = st.tabs([A["tab_models"], A["tab_diseases"], A["tab_datasources"], A["tab_features"]])

    # ==================== TAB 1: AI & ML MODELS & ACCURACY ====================
    with tab_a1:
        # Card 1: Custom Trained Disease ML Model
        st.markdown(f"""
        <div class="mm-card" style="border-top: 4px solid #10B981; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
                <div>
                    <b style="font-size: 1.12rem; color: var(--mm-text-primary);"><img src="https://cdn-icons-png.flaticon.com/512/18357/18357328.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['ml_title']}</b>
                    <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 2px 0 0 0;">{A['ml_sub']}</p>
                </div>
                <span class="mm-badge mm-badge-success" style="font-size: 0.80rem; font-weight: 700; padding: 6px 14px;">Accuracy: {A['stat_acc']}</span>
            </div>
            <!-- 4-Stat Metrics Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin: 14px 0 16px 0;">
                <div style="background: rgba(16, 185, 129, 0.08); border: 1.5px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.35rem; font-weight: 800; color: #10B981;">{A['stat_acc']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_acc_sub']}</div>
                </div>
                <div style="background: rgba(59, 130, 246, 0.08); border: 1.5px solid rgba(59, 130, 246, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.05rem; font-weight: 800; color: #3B82F6; margin-top: 2px;">{A['stat_algo']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_algo_sub']}</div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.08); border: 1.5px solid rgba(245, 158, 11, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.35rem; font-weight: 800; color: #F59E0B;">{A['stat_features']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_features_sub']}</div>
                </div>
                <div style="background: rgba(168, 85, 247, 0.08); border: 1.5px solid rgba(168, 85, 247, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.35rem; font-weight: 800; color: #A855F7;">{A['stat_classes']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_classes_sub']}</div>
                </div>
            </div>
            <!-- Pipeline Breakdown -->
            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 8px; padding: 12px 14px; font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.6;">
                <div>• {A['ml_step1']}</div>
                <div style="margin-top: 4px;">• {A['ml_step2']}</div>
                <div style="margin-top: 4px;">• {A['ml_step3']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Card 2: Medicine Demand Forecasting Model (HMIS Supply Chain)
        st.markdown(f"""
        <div class="mm-card" style="border-top: 4px solid #3B82F6; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
                <div>
                    <b style="font-size: 1.12rem; color: var(--mm-text-primary);"><img src="https://cdn-icons-png.flaticon.com/512/2966/2966327.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['demand_title']}</b>
                    <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 2px 0 0 0;">{A['demand_sub']}</p>
                </div>
                <span class="mm-badge mm-badge-info" style="font-size: 0.80rem; font-weight: 700; padding: 6px 14px;">WAPE: {A['stat_wape']} | R²: {A['stat_r2']}</span>
            </div>
            <!-- 4-Stat Demand Forecaster Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin: 14px 0 16px 0;">
                <div style="background: rgba(59, 130, 246, 0.08); border: 1.5px solid rgba(59, 130, 246, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.35rem; font-weight: 800; color: #3B82F6;">{A['stat_wape']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_wape_sub']}</div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.08); border: 1.5px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.35rem; font-weight: 800; color: #10B981;">{A['stat_r2']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_r2_sub']}</div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.08); border: 1.5px solid rgba(245, 158, 11, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.35rem; font-weight: 800; color: #F59E0B;">{A['stat_mae']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_mae_sub']}</div>
                </div>
                <div style="background: rgba(168, 85, 247, 0.08); border: 1.5px solid rgba(168, 85, 247, 0.35); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 1.35rem; font-weight: 800; color: #A855F7;">{A['stat_rmse']}</div>
                    <div style="font-size: 0.74rem; color: var(--mm-text-secondary); margin-top: 2px;">{A['stat_rmse_sub']}</div>
                </div>
            </div>
            <!-- Pipeline Breakdown -->
            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 8px; padding: 12px 14px; font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.6;">
                <div>• {A['demand_step1']}</div>
                <div style="margin-top: 4px;">• {A['demand_step2']}</div>
                <div style="margin-top: 4px;">• {A['demand_step3']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4-Card Unified 2x2 Grid: Operational Risk, Knowledge Graph, Foundation LLMs, Vision OCR (Strictly 2 per row)
        st.markdown(f"""
        <div class="mm-grid-2col" style="margin-top: 14px; align-items: stretch;">
            <!-- Card 3 -->
            <div class="mm-card" style="display: flex; flex-direction: column; justify-content: flex-start; min-height: 250px; height: 100%; border-top: 4px solid #EF4444; margin: 0;">
                <b style="font-size: 1.02rem; color: var(--mm-text-primary);"><img src="https://cdn-icons-png.flaticon.com/512/2965/2965300.png" style="width: 1.15em; height: 1.15em; vertical-align: -0.15em; display: inline-block;" /> {A['stockout_title']}</b>
                <p style="font-size: 0.80rem; color: var(--mm-text-secondary); margin: 3px 0 10px 0;">{A['stockout_sub']}</p>
                <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.55;">
                    {A['stockout_desc']}
                </div>
            </div>
            <!-- Card 4 -->
            <div class="mm-card" style="display: flex; flex-direction: column; justify-content: flex-start; min-height: 250px; height: 100%; border-top: 4px solid #3B82F6; margin: 0;">
                <b style="font-size: 1.02rem; color: var(--mm-text-primary);"><img src="https://cdn-icons-png.flaticon.com/512/404/404621.png" style="width: 1.15em; height: 1.15em; vertical-align: -0.15em; display: inline-block;" /> {A['kg_title']}</b>
                <p style="font-size: 0.80rem; color: var(--mm-text-secondary); margin: 3px 0 10px 0;">{A['kg_sub']}</p>
                <div style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.6;">
                    <div style="margin-bottom: 6px;">• {A['kg_item1']}</div>
                    <div style="margin-bottom: 6px;">• {A['kg_item2']}</div>
                    <div>• {A['kg_item3']}</div>
                </div>
            </div>
            <!-- Card 5 -->
            <div class="mm-card" style="display: flex; flex-direction: column; justify-content: flex-start; min-height: 250px; height: 100%; border-top: 4px solid #EA580C; margin: 0;">
                <b style="font-size: 1.02rem; color: var(--mm-text-primary);"><img src="https://cdn-icons-png.flaticon.com/512/12512/12512364.png" style="width: 1.15em; height: 1.15em; vertical-align: -0.15em; display: inline-block;" /> {A['llm_title']}</b>
                <p style="font-size: 0.80rem; color: var(--mm-text-secondary); margin: 3px 0 10px 0;">{A['llm_sub']}</p>
                <div style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.6;">
                    <div style="margin-bottom: 6px;">• {A['llm_item1']}</div>
                    <div style="margin-bottom: 6px;">• {A['llm_item2']}</div>
                    <div>• {A['llm_item3']}</div>
                </div>
            </div>
            <!-- Card 6 -->
            <div class="mm-card" style="display: flex; flex-direction: column; justify-content: flex-start; min-height: 250px; height: 100%; border-top: 4px solid #8B5CF6; margin: 0;">
                <b style="font-size: 1.02rem; color: var(--mm-text-primary);"><img src="https://cdn-icons-png.flaticon.com/512/6024/6024205.png" style="width: 1.15em; height: 1.15em; vertical-align: -0.15em; display: inline-block;" /> {A['ocr_title']}</b>
                <p style="font-size: 0.80rem; color: var(--mm-text-secondary); margin: 3px 0 10px 0;">{A['ocr_sub']}</p>
                <div style="font-size: 0.82rem; color: var(--mm-text-secondary); line-height: 1.6;">
                    <div style="margin-bottom: 6px;">• {A['ocr_item1']}</div>
                    <div>• {A['ocr_item2']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== TAB 2: 100+ MAJOR INDIAN DISEASES ====================
    with tab_a2:
        st.markdown(f"""
        <div class="mm-card" style="border-left: 5px solid #2563EB; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
                <div>
                    <div style="font-size: 0.72rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em;">
                        NATIONAL HEALTH TAXONOMY (MOHFW & WHO ICD)
                    </div>
                    <b style="font-size: 1.15rem; color: var(--mm-text-primary);">{A['dis_title']}</b>
                </div>
                <span class="mm-badge mm-badge-brand" style="font-size: 0.75rem; padding: 6px 12px;">18 Official Categories</span>
            </div>
            <p style="font-size: 0.84rem; color: var(--mm-text-secondary); line-height: 1.6; margin-bottom: 14px;">
                {A['dis_sub']}
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 12px;">
                <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_1']}
                </div>
                <div style="background: rgba(59, 130, 246, 0.06); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_2']}
                </div>
                <div style="background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_3']}
                </div>
                <div style="background: rgba(245, 158, 11, 0.06); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_4']}
                </div>
                <div style="background: rgba(168, 85, 247, 0.06); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_5']}
                </div>
                <div style="background: rgba(234, 88, 12, 0.06); border: 1px solid rgba(234, 88, 12, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_6']}
                </div>
                <div style="background: rgba(14, 165, 233, 0.06); border: 1px solid rgba(14, 165, 233, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_7']}
                </div>
                <div style="background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_8']}
                </div>
                <div style="background: rgba(6, 182, 212, 0.06); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_9']}
                </div>
                <div style="background: rgba(139, 92, 246, 0.06); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_10']}
                </div>
                <div style="background: rgba(6, 182, 212, 0.06); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_11']}
                </div>
                <div style="background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 12px; font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                    {A['dis_cat_12']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== TAB 3: AUTHENTIC DATA SOURCES & APIS ====================
    with tab_a3:
        st.markdown(f"""
        <div class="mm-card" style="border-left: 5px solid #2563EB; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
                <div>
                    <div style="font-size: 0.72rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em;">
                        CLINICAL DATA GOVERNANCE & PROVENANCE
                    </div>
                    <b style="font-size: 1.15rem; color: var(--mm-text-primary);">{A['sources_title']}</b>
                </div>
                <span class="mm-badge mm-badge-info" style="font-size: 0.75rem; padding: 6px 12px;">100% Real, Audited & Non-Fabricated</span>
            </div>
            <p style="font-size: 0.84rem; color: var(--mm-text-secondary); line-height: 1.6; margin-bottom: 14px;">
                {A['sources_sub']}
            </p>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px;">
                <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #2563EB; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/4320/4320371.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_who_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_who_desc']}
                    </div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #10B981; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/2966/2966327.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_hmis_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_hmis_desc']}
                    </div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.06); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #F59E0B; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/2465/2465596.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_nfhs_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_nfhs_desc']}
                    </div>
                </div>
                <div style="background: rgba(168, 85, 247, 0.06); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #A855F7; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/883/883407.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_nlem_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_nlem_desc']}
                    </div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.06); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #10B981; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/5228/5228598.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_fda_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_fda_desc']}
                    </div>
                </div>
                <div style="background: rgba(37, 99, 235, 0.06); border: 1px solid rgba(37, 99, 235, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #2563EB; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/18310/18310946.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_nih_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_nih_desc']}
                    </div>
                </div>
                <div style="background: rgba(147, 51, 234, 0.06); border: 1px solid rgba(147, 51, 234, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #9333EA; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/4060/4060488.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_gis_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_gis_desc']}
                    </div>
                </div>
                <div style="background: rgba(13, 148, 136, 0.06); border: 1px solid rgba(13, 148, 136, 0.25); border-radius: 10px; padding: 14px;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #0D9488; margin-bottom: 4px;">
                        <img src="https://cdn-icons-png.flaticon.com/512/6266/6266132.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['src_ayush_title']}
                    </div>
                    <div style="font-size: 0.80rem; color: var(--mm-text-secondary); line-height: 1.5;">
                        {A['src_ayush_desc']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==================== TAB 4: ARCHITECTURE, PRIVACY & SECURITY ====================
    with tab_a4:
        st.markdown(f"""
        <div class="mm-card">
            <b style="font-size: 1.10rem; color: var(--mm-text-primary);">{A['feat_title']}</b>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; margin-top: 14px;">
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 10px; padding: 14px;">
                    <b style="color: #3B82F6; font-size: 0.90rem;"><img src="https://cdn-icons-png.flaticon.com/128/486/486505.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['feat_1_title']}</b>
                    <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.5;">{A['feat_1_desc']}</p>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 10px; padding: 14px;">
                    <b style="color: #10B981; font-size: 0.90rem;"><img src="https://cdn-icons-png.flaticon.com/512/595/595764.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['feat_2_title']}</b>
                    <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.5;">{A['feat_2_desc']}</p>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 10px; padding: 14px;">
                    <b style="color: #F59E0B; font-size: 0.90rem;"><img src="https://cdn-icons-png.flaticon.com/512/4503/4503969.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['feat_3_title']}</b>
                    <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.5;">{A['feat_3_desc']}</p>
                </div>
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--mm-border-color); border-radius: 10px; padding: 14px;">
                    <b style="color: #A855F7; font-size: 0.90rem;"><img src="https://cdn-icons-png.flaticon.com/512/12370/12370940.png" style="width: 1.1em; height: 1.1em; vertical-align: -0.15em; display: inline-block;" /> {A['feat_4_title']}</b>
                    <p style="font-size: 0.82rem; color: var(--mm-text-secondary); margin: 4px 0 0 0; line-height: 1.5;">{A['feat_4_desc']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
    st.markdown(render_footer_trust_bar(T), unsafe_allow_html=True)


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

/* Row 3: 3 Column Cards (Food timing?, Danger signs, Yoga poses) */
/* Row 3 & Row 4: 2 Column Compact Horizontal Cards (Food timing?, Danger signs, Yoga poses, Lab report scanner) */
.st-key-dyn_chip_r3_1 button,
.st-key-dyn_chip_r3_2 button,
.st-key-dyn_chip_r3_3 button,
.st-key-dyn_chip_r4_1 button {
    padding: 8px 26px 8px 48px !important;
    min-height: 58px !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    text-align: left !important;
    justify-content: flex-start !important;
    overflow: visible !important;
}
.st-key-dyn_chip_r3_1 button p strong,
.st-key-dyn_chip_r3_2 button p strong,
.st-key-dyn_chip_r3_3 button p strong,
.st-key-dyn_chip_r4_1 button p strong {
    font-size: 0.82rem !important;
    line-height: 1.35 !important;
    display: block !important;
    overflow: visible !important;
    margin-bottom: 2px !important;
}
.st-key-dyn_chip_r3_1 button p,
.st-key-dyn_chip_r3_2 button p,
.st-key-dyn_chip_r3_3 button p,
.st-key-dyn_chip_r4_1 button p {
    font-size: 0.68rem !important;
    line-height: 1.30 !important;
    overflow: visible !important;
    margin: 0 !important;
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
                if st.button("**Lab report scanner**  \nUpload & analyze reports", key="dyn_chip_r4_1", use_container_width=True):
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


# Page Footer
st.markdown("---")
st.markdown(
    f"<center style='color: #64748B; font-size: 0.86rem; padding: 14px 0; font-weight: 500;'><b>DocMindX AI</b> © 2026 • Enterprise Multilingual Healthcare Suite • Built for Clinical Safety & Triage Support</center>",
    unsafe_allow_html=True
)
