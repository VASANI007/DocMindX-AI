import os
import sys
from docx.shared import Inches

from .styler import (
    create_base_document, add_heading_1, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_callout, add_styled_table, add_code_block
)

def generate_dev_guide_en(output_path):
    doc = create_base_document(
        title="DocMindX AI — Developer Manual & Technical Guide",
        subtitle="Local Environment Setup, Internal API Interfaces, Database Migrations & Deployment",
        doc_type="Developer Manual & Technical Documentation",
        lang="EN"
    )

    # 1. Developer Environment & Local Setup
    add_heading_1(doc, "1. Developer Environment & Local Setup Guide")
    add_body_p(doc, "This guide details the complete procedure to install, configure, debug, and run DocMindX AI on a local developer workstation or production cloud instance.")

    add_heading_2(doc, "1.1 System Prerequisites")
    add_bullet_p(doc, " Python 3.10 or 3.11 installed (Python 3.12+ may have wheel compatibility issues with certain ML libraries).", bold_prefix="Python Runtime:")
    add_bullet_p(doc, " Git 2.30+ installed and configured with SSH/HTTPS credentials.", bold_prefix="Version Control:")
    add_bullet_p(doc, " Tesseract-OCR binary installed (v5.0+) for local offline fallback OCR.", bold_prefix="System OCR Binary:")
    add_bullet_p(doc, " Minimum 8 GB RAM (16 GB recommended), multi-core CPU.", bold_prefix="Hardware Specs:")

    add_heading_2(doc, "1.2 Step-by-Step Installation Commands")
    add_code_block(doc,
"""# 1. Clone the official repository
git clone https://github.com/vasani007/DocMindX-AI.git
cd DocMindX-AI

# 2. Initialize and activate Python Virtual Environment
# On Windows (PowerShell):
python -m venv venv
venv/Scripts/Activate.ps1

# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and install production dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt"""
    )

    add_heading_2(doc, "1.3 Environment Variable Configuration (.env)")
    add_body_p(doc, "Create a '.env' file in the project root directory. Populate the following configuration variables:")
    add_code_block(doc,
"""# ==============================================================================
# DOCMINDX AI — ENVIRONMENT CONFIGURATION (.env)
# ==============================================================================
# 1. Google Gemini API (Required: Multimodal Vision OCR & Clinical NLP)
GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere"

# 2. Groq Cloud API (Required: High-speed Llama-3.3-70B fallback copilot)
GROQ_API_KEY="gsk_YourGroqApiKeyHere"

# 3. OpenFDA API Key (Optional/Recommended: Live Drug Labeling & Interactions)
OPENFDA_API_KEY="your_openfda_key_here"

# 4. WHO ICD-11 API Credentials (Optional: Official Global Disease Ontology)
WHO_ICD_CLIENT_ID="your_who_client_id"
WHO_ICD_CLIENT_SECRET="your_who_client_secret"

# 5. NCBO BioPortal API Key (Optional: SNOMED-CT / LOINC Terminology Lookup)
BIOPORTAL_API_KEY="your_bioportal_key"

# 6. Google Maps Platform API Key (Required: Live Hospital Radar & Geocoding)
GOOGLE_MAPS_API_KEY="AIzaSyYourGoogleMapsKeyHere"

# 7. Supabase PostgreSQL Connection String (Optional for Cloud Persistence)
DATABASE_URL="postgresql://postgres:password@db.supabase.co:5432/postgres"

# 8. Google Cloud BigQuery Project ID (Optional for National Telemetry Sync)
BIGQUERY_PROJECT_ID="docmindx-ai-prod"
BIGQUERY_DATASET_ID="command_center" """
    )

    add_heading_2(doc, "1.4 Launching the Application Locally")
    add_code_block(doc,
"""# Launch the interactive Streamlit server
streamlit run app.py --server.port 8501 --server.enableCORS false

# Open your web browser at: http://localhost:8501"""
    )

    # 2. Internal Module Reference & Code Interfaces
    add_heading_1(doc, "2. Internal Module Reference & API Contracts")
    add_body_p(doc, "Core Python services provide programmatic interfaces for clinical inference, document parsing, and logistics optimization:")

    add_heading_2(doc, "2.1 Clinical Diagnostic Engine ('ai/disease_prediction/predict.py')")
    add_code_block(doc,
"""from ai.disease_prediction.predict import SymptomTriageEngine

# Initialize Triage Engine (loads serialized 50-tree Random Forest model)
triage_engine = SymptomTriageEngine()

# Execute Differential Prediction
result = triage_engine.predict(
    symptoms_text="Severe chest pain, left arm radiating numbness, shortness of breath",
    duration_days=2,
    age=54,
    gender="Male"
)

# Return Contract:
# {
#   "top_conditions": [
#       {"name": "Acute Myocardial Infarction", "icd11": "BA41", "probability": 0.88},
#       {"name": "Unstable Angina", "icd11": "BA42", "probability": 0.08}
#   ],
#   "red_flags": ["RF002: Acute Coronary Syndrome Warning"],
#   "urgency": "EMERGENCY_EVACUATION",
#   "evidence_summary": {"patient_tokens": ["chest_pain", "left_arm_pain", "dyspnea"]}
# }"""
    )

    add_heading_2(doc, "2.2 Multimodal Vision OCR ('ai/ocr/text_extractor.py')")
    add_code_block(doc,
"""from ai.ocr.text_extractor import extract_text_from_file

# Extracts digitized entities from image (PNG/JPG) or PDF
extracted_data = extract_text_from_file(
    file_bytes=uploaded_file.read(),
    filename="doctor_prescription.jpg",
    doc_type="prescription"
)

# Return Contract:
# {
#   "raw_text": "Tab Paracetamol 650mg TDS x 3d...",
#   "medicines": [
#       {"name": "Paracetamol", "dosage": "650mg", "frequency": "3 times a day", "duration": "3 days"}
#   ],
#   "doctor_notes": "Take after meals. Maintain hydration."
# }"""
    )

    add_heading_2(doc, "2.3 Two-Stage Redistribution Solver ('ai/supply_chain/redistribution_engine.py')")
    add_code_block(doc,
"""from ai.supply_chain.redistribution_engine import RedistributionEngine

# Initialize Linear Solver
engine = RedistributionEngine()

# Solve optimal inter-facility rebalancing
manifest = engine.calculate_transfers(
    state="Gujarat",
    district="Surat",
    critical_stockout_facilities=["PHC_Mandvi", "PHC_Umarpada"],
    surplus_facilities=["Civil_Hospital_Surat"]
)

# Produces official transfer manifest with route distances and quantities."""
    )

    # 3. Database Operations & Migrations
    add_heading_1(doc, "3. Database Operations & Migrations")
    add_body_p(doc, "DocMindX AI includes automated migration scripts to establish PostgreSQL tables and Row-Level Security on Supabase:")
    add_code_block(doc,
"""# 1. Run PostgreSQL table migrations
python database/migrate_to_supabase.py

# 2. Apply Row-Level Security (RLS) policies
python database/apply_rls_policies.py

# 3. Seed initial sample records into local SQLite vault
python database/insert_data.py"""
    )

    # 4. Testing & Quality Assurance
    add_heading_1(doc, "4. Testing & Verification Suite")
    add_body_p(doc, "The repository provides automated test suites verifying clinical root causes, regression safety, ML model accuracy, and logistics integrity:")
    
    test_table = [
        ["Verification Command", "Target Subsystem", "Acceptance Criteria"],
        ["python verify_ml_model.py", "Random Forest ML Classifier", "Textbook Acc >= 98%, Top-3 Acc >= 95%."],
        ["python verify_supply_chain.py", "Command Center & Outbreaks", "Pass all 27 automated production checkpoints."],
        ["pytest tests/test_clinical_surgical_v3_root_cause.py -v", "Clinical Pipeline v3", "14/14 root-cause safety test cases pass."],
        ["pytest tests/test_symptom_normalization_matrix.py -v", "Multilingual Symptom NLP", "22/22 translation & negation tests pass."],
        ["pytest tests/test_dosage_forms.py -v", "OpenFDA / DailyMed Provenance", "16/16 dosage form validation tests pass."]
    ]
    add_styled_table(doc, test_table[0], test_table[1:], [2.2, 2.0, 2.3])

    # 5. Production Deployment Guide
    add_heading_1(doc, "5. Production Deployment Guide")
    add_heading_2(doc, "5.1 Streamlit Community Cloud Deployment")
    add_bullet_p(doc, " Link your GitHub repository at 'share.streamlit.io'. Select 'app.py' as the main entry point.", bold_prefix="Repository Link:")
    add_bullet_p(doc, " Under 'App Settings > Secrets', paste the contents of your '.env' file in TOML format.", bold_prefix="Secrets Configuration:")
    add_bullet_p(doc, " Streamlit automatically parses 'packages.txt' (installing system Tesseract packages) and 'requirements.txt'.", bold_prefix="Build Execution:")

    add_heading_2(doc, "5.2 Docker Containerization Specification")
    add_code_block(doc,
"""FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y \\
    tesseract-ocr \\
    libtesseract-dev \\
    libgl1-mesa-glx \\
    git \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]"""
    )

    doc.save(output_path)
    print(f"Generated: {output_path}")

def generate_dev_guide_hi(output_path):
    doc = create_base_document(
        title="DocMindX AI — डेवलपर मैनुअल और तकनीकी गाइड",
        subtitle="लोकल डेवलपमेंट सेटअप, आंतरिक API इंटरफेस, डेटाबेस माइग्रेशन एवं डिप्लॉयमेंट गाइड",
        doc_type="डेवलपर मैनुअल एवं तकनीकी गाइड",
        lang="HI"
    )

    # 1. डेवलपमेंट सेटअप
    add_heading_1(doc, "1. डेवलपर एनवायरनमेंट एवं लोकल सेटअप गाइड (Developer Setup)")
    add_body_p(doc, "यह गाइड किसी भी नए डेवलपर के कंप्यूटर पर DocMindX AI प्रोजेक्ट को शुरू से सेटअप करने, चलाने और डिबग करने की संपूर्ण प्रक्रिया का विवरण देती है।")

    add_heading_2(doc, "1.1 आवश्यक सिस्टम सॉफ्टवेयर (Prerequisites)")
    add_bullet_p(doc, " Python 3.10 या 3.11 इंस्टॉल होना अनिवार्य है।", bold_prefix="Python रनटाइम:")
    add_bullet_p(doc, " Git 2.30+ वर्ज़न कंट्रोल।", bold_prefix="Git:")
    add_bullet_p(doc, " Tesseract-OCR सॉफ्टवेयर (ऑफ़लाइन इमेज टेक्स्ट निकालने के लिए)।", bold_prefix="Tesseract OCR:")
    add_bullet_p(doc, " न्यूनतम 8 GB रैम और मल्टी-कोर प्रोसेसर।", bold_prefix="हार्डवेयर:")

    add_heading_2(doc, "1.2 प्रोजेक्ट डाउनलोड एवं इंस्टॉलेशन कमांड्स")
    add_code_block(doc,
"""# 1. गिटहब से प्रोजेक्ट क्लोन करें
git clone https://github.com/vasani007/DocMindX-AI.git
cd DocMindX-AI

# 2. पायथन वर्चुअल एनवायरनमेंट बनाएं और सक्रिय करें
# Windows (PowerShell):
python -m venv venv
venv/Scripts/Activate.ps1

# Linux / Mac:
python3 -m venv venv
source venv/bin/activate

# 3. सभी जरूरी लाइब्रेरी इंस्टॉल करें
pip install --upgrade pip
pip install -r requirements.txt"""
    )

    add_heading_2(doc, "1.3 एनवायरनमेंट वेरिएबल कॉन्फ़िगरेशन (.env)")
    add_body_p(doc, "प्रोजेक्ट के मुख्य फोल्डर में '.env' नाम की फाइल बनाएं और उसमें अपनी API Keys डालें:")
    add_code_block(doc,
"""# ==============================================================================
# DOCMINDX AI — API KEYS कॉन्फ़िगरेशन (.env)
# ==============================================================================
# 1. Google Gemini API Key (मेडिकल विजन और क्लिनिकल व्याख्या के लिए आवश्यक)
GEMINI_API_KEY="AIzaSyYourGeminiApiKeyHere"

# 2. Groq Cloud API Key (तेज Llama-3.3 मॉडल फॉलबैक के लिए)
GROQ_API_KEY="gsk_YourGroqApiKeyHere"

# 3. Google Maps API Key (निकटतम अस्पताल रडार और जीपीएस नेविगेशन के लिए)
GOOGLE_MAPS_API_KEY="AIzaSyYourGoogleMapsKeyHere"

# 4. Supabase PostgreSQL URL (क्लाउड डेटाबेस के लिए)
DATABASE_URL="postgresql://postgres:password@db.supabase.co:5432/postgres" """
    )

    add_heading_2(doc, "1.4 प्रोजेक्ट को लोकल कंप्यूटर पर चलाना")
    add_code_block(doc,
"""# Streamlit वेब सर्वर शुरू करें
streamlit run app.py

# अपने ब्राउज़र में खोलें: http://localhost:8501"""
    )

    # 2. आंतरिक API इंटरफेस
    add_heading_1(doc, "2. मुख्य कोड मॉड्यूल एवं आंतरिक API इंटरफेस")
    add_heading_2(doc, "2.1 क्लिनिकल ट्राइएज इंजन ('ai/disease_prediction/predict.py')")
    add_code_block(doc,
"""from ai.disease_prediction.predict import SymptomTriageEngine

# ट्राइएज इंजन प्रारंभ करें
engine = SymptomTriageEngine()

# लक्षणों की जांच करें
result = engine.predict(
    symptoms_text="3 din se tej bukhar aur sharir dard",
    duration_days=3,
    age=30,
    gender="Female"
)
# रिटर्न में संभावित बीमारियां (Top-3) और रेड फ्लैग्स प्राप्त होते हैं।"""
    )

    # 3. डेटाबेस माइग्रेशन
    add_heading_1(doc, "3. डेटाबेस माइग्रेशन एवं सुरक्षा नीतियां (Database Migrations)")
    add_code_block(doc,
"""# Supabase PostgreSQL टेबल बनाएं
python database/migrate_to_supabase.py

# रो-लेवल सुरक्षा (RLS) नीतियां लागू करें
python database/apply_rls_policies.py"""
    )

    # 4. स्वचालित टेस्टिंग
    add_heading_1(doc, "4. स्वचालित परीक्षण एवं मॉडल ऑडिट (Testing Suites)")
    add_code_block(doc,
"""# ML मॉडल की 97.58% एक्यूरेसी और 101 बीमारियों का ऑडिट
python verify_ml_model.py

# राष्ट्रीय कमान केंद्र और 27 प्रोडक्शन चेकपॉइंट्स का परीक्षण
python verify_supply_chain.py

# बहुभाषी अनुवाद और निषेध (Negation) टेस्ट्स
pytest tests/test_symptom_normalization_matrix.py -v"""
    )

    # 5. प्रोडक्शन डिप्लॉयमेंट
    add_heading_1(doc, "5. लाइव सर्वर पर डिप्लॉयमेंट गाइड (Production Deployment)")
    add_bullet_p(doc, " GitHub से Streamlit Community Cloud (share.streamlit.io) पर कनेक्ट करें और Secrets में .env की वैल्यूज डालें।", bold_prefix="Streamlit Cloud:")
    add_bullet_p(doc, " 'Dockerfile' का उपयोग करके Google Cloud Run या Docker Swarm पर कंटेनर चलाएं।", bold_prefix="Docker कंटेनराइजेशन:")

    doc.save(output_path)
    print(f"Generated: {output_path}")
