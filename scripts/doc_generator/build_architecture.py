import os
import sys
from docx.shared import Inches

from .styler import (
    create_base_document, add_heading_1, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_callout, add_styled_table, add_code_block
)

def generate_arch_en(output_path):
    doc = create_base_document(
        title="DocMindX AI — System Architecture Document",
        subtitle="Dual-Tier Hybrid Infrastructure, Clinical Pipeline v3 & National Cloud Architecture",
        doc_type="System Architecture Document",
        lang="EN"
    )

    # 1. High-Level Architectural Rationale
    add_heading_1(doc, "1. High-Level Architectural Blueprint & Strategy")
    add_body_p(doc, "DocMindX AI implements a deliberate Dual-Tier Hybrid Architecture designed to operate seamlessly across high-latency rural field deployments and massive national cloud aggregation centers. In India's public health landscape, over 30,000 Primary Health Centres (PHCs) frequently experience intermittent cellular coverage and electrical disruptions. A monolithic cloud-only architecture introduces unacceptable single points of failure.")

    add_callout(
        doc,
        "Architectural Rationale: Dual-Tier Resilience combines instantaneous edge autonomy (<15ms inference via compressed Parquet and SQLite) with massive national-scale analytical aggregation in Google Cloud BigQuery.",
        title="Dual-Tier Hybrid Architecture",
        alert_type="info"
    )

    add_heading_2(doc, "1.1 Architectural Tiers")
    add_bullet_p(doc, " Operates client-side using embedded Python runtimes, Apache Parquet columnar storage, and local SQLite vaults. All diagnostic models, red-flag triggers, and two-stage redistribution solvers execute locally in under 45ms with zero cloud dependency.", bold_prefix="Tier 1 — Edge-Local Autonomy:")
    add_bullet_p(doc, " Ingests multi-district telemetry into Google Cloud BigQuery ('command_center' dataset). Partitioned by snapshot date and clustered by administrative geography for sub-second macro-telemetry across all 36 Indian States and Union Territories.", bold_prefix="Tier 2 — National BigQuery Cloud Aggregation:")

    # 2. Comprehensive Technology Stack
    add_heading_1(doc, "2. Comprehensive Technology Stack")
    add_body_p(doc, "The DocMindX AI platform leverages battle-tested, enterprise-grade open-source and cloud technologies:")

    stack_data = [
        ["Subsystem Layer", "Technology / Framework", "Version / Model Specification", "Architectural Role"],
        ["Client Presentation", "Streamlit & Streamlit-Folium", "v1.35.0+ / Folium 0.16.0", "Reactive single-page web UI, interactive GIS maps."],
        ["Styling & Theme", "Vanilla CSS / Design System", "High-Contrast Clinical Tokens", "Zero external CSS frameworks; WCAG AAA compliant."],
        ["Core Runtime", "Python", "3.10 / 3.11", "High-performance asynchronous backend execution."],
        ["Machine Learning", "Scikit-Learn & NumPy", "v1.9.1 / NumPy 1.24+", "50-tree Random Forest classifier & demand regressor."],
        ["Multimodal Vision", "Google Gemini 2.5 Flash Vision", "gemini-2.5-flash", "Handwritten prescription & radiology OCR."],
        ["Conversational AI", "Google Gemini & Groq Cloud", "Gemini 2.5 / Llama-3.3-70B", "24x7 clinical assistant with failover routing."],
        ["Voice & Audio", "Google Cloud Speech & TTS", "Cloud Speech v2 / gTTS", "Trilingual voice input (Hindi, Gujarati, English)."],
        ["Relational Database", "Supabase PostgreSQL", "PostgreSQL 15+ (psycopg2)", "User accounts, family vault, Row-Level Security."],
        ["Local Storage", "SQLite & Apache Parquet", "SQLite 3 / PyArrow", "Local offline cache and 10 official ingested datasets."],
        ["Big Data Warehouse", "Google Cloud BigQuery", "BigQuery SDK 3.20+", "National-scale telemetry, partitioned & clustered tables."]
    ]
    add_styled_table(doc, stack_data[0], stack_data[1:], [1.4, 1.8, 1.8, 1.5])

    # 3. System Component Architecture
    add_heading_1(doc, "3. System Component Architecture")
    add_body_p(doc, "DocMindX AI is organized into six decoupled functional subsystems:")

    add_heading_2(doc, "3.1 Component 1: Client Presentation Layer ('app.py', 'components/')")
    add_bullet_p(doc, " Manages top navigation, trilingual localization (EN, HI, GU), theme switching (Light/Dark), and active panel routing without page reloads.", bold_prefix="Application Controller:")
    add_bullet_p(doc, " Captures patient demographics (Age, Gender, State, Height, Weight, Blood Group: A+, A-, B+, B-, AB+, AB-, O+, O-, Unknown) and pre-existing comorbidities. Selecting a family profile instantly auto-fills these fields.", bold_prefix="Panel 1 Intake & Family Profiles:")
    add_bullet_p(doc, " Multi-channel ingestion accepting colloquial speech (Whisper ASR), natural text, and clinical photo uploads with temporal duration buttons ('today', '1-3 days', '4-7 days', '1-2 weeks', '>2 weeks').", bold_prefix="Multimodal Symptom Capture:")
    add_bullet_p(doc, " Ingests lab reports (CBC, LFT, Lipid, KFT), radiology, and prescriptions, delivering layman translations, underlying causes, and actionable tips.", bold_prefix="Panel 2: Medical Report Scanner:")
    add_bullet_p(doc, " Live Overpass OpenStreetMap radar filtering 24/7 emergency hospitals, clinics, pharmacies, blood banks, and labs across an interactive 1 to 25 km radius slider.", bold_prefix="Panel 3: Nearby Healthcare Radar:")
    add_bullet_p(doc, " Centralized digital vault displaying previous scans, prescriptions, triage assessments, and clinical regimens with PDF export.", bold_prefix="Panel 4: Health Records Vault:")
    add_bullet_p(doc, " Dedicated administrative console gated strictly to authorized admin users (is_admin=True) with 7-day epidemic forecasting and supply chain rebalancing.", bold_prefix="Panel 5: National Command Center:")

    add_heading_2(doc, "3.2 Component 2: Clinical Intelligence Engine ('ai/disease_prediction/')")
    add_bullet_p(doc, " Translates multilingual colloquial symptom phrases into 280 standardized clinical features while stripping denied symptoms.", bold_prefix="Canonical Normalizer:")
    add_bullet_p(doc, " Strict evidence boundary ensuring patient findings are never contaminated by external clinical ontology candidate titles.", bold_prefix="Evidence Isolation Gate (Pipeline v3):")
    add_bullet_p(doc, " 50-tree Random Forest classifier generating calibrated disease probability distributions across 101 ICD-11 classes with 97.58% Top-3 accuracy.", bold_prefix="Dual-Tier ML Classifier:")
    add_bullet_p(doc, " Synthesizes verified OTC medicines (OpenFDA), ICMR-NIN dietary guidelines ('Foods to Eat' & 'Foods to Avoid'), restorative yoga asanas, and disease etiology.", bold_prefix="Tri-Pillar Holistic Regimen Engine:")
    add_bullet_p(doc, " Constituent emergency rules (RF001 to RF035) triggering instant triage alerts and 108 emergency dialers.", bold_prefix="Red Flag Safety Gates:")

    add_heading_2(doc, "3.3 Component 3: Multimodal Vision & Report Analyzer ('ai/ocr/', 'ai/report_ai/')")
    add_bullet_p(doc, " Preprocesses images using OpenCV (adaptive thresholding, contrast enhancement) before OCR parsing.", bold_prefix="Image Preprocessor:")
    add_bullet_p(doc, " Extracts drug schedules, frequencies, and cautionary guidelines from handwritten doctor scripts using Gemini Vision.", bold_prefix="Prescription Analyzer:")
    add_bullet_p(doc, " Evaluates biochemical markers (Hemoglobin, Platelets, SGPT, Bilirubin, HbA1c) against clinical reference ranges with layman breakdown.", bold_prefix="Biochemical Lab Analyzer:")

    add_heading_2(doc, "3.4 Component 4: National Command Logistics Engine ('ai/supply_chain/')")
    add_bullet_p(doc, " Automated pipelines reconciling HMIS, NFHS-5, Beds, IPHS, and NLEM 2022 datasets with immutable provenance tags.", bold_prefix="Data Ingestion Manager:")
    add_bullet_p(doc, " Multi-factor time-series regressor forecasting 7-day medicine consumption with 6.53% WAPE.", bold_prefix="Demand Forecaster:")
    add_bullet_p(doc, " Calculates Days of Inventory Remaining (DOIR) and issues critical stockout warnings when DOIR < 3.", bold_prefix="DOIR Stockout Detector:")
    add_bullet_p(doc, " Linear transit solver resolving inter-facility shortages and generating downloadable PDF transfer manifests.", bold_prefix="Two-Stage Redistribution Solver:")

    add_heading_2(doc, "3.5 Component 5: External API Gateway ('api/')")
    add_bullet_p(doc, " Integrates live NIH DailyMed, OpenFDA, WHO ICD-11, NCBO BioPortal, OpenStreetMap Overpass (1-25 km), and Google Maps with robust offline fallbacks.", bold_prefix="Resilient API Clients:")

    add_heading_2(doc, "3.6 Component 6: Security, Auth & Data Persistence Layer ('database/')")
    add_bullet_p(doc, " Enforces role-based access control (RBAC), encrypted SQLite local storage, Supabase PostgreSQL Row-Level Security, and BigQuery cloud sync.", bold_prefix="Tenancy & Security Layer:")

    # 4. Data Flow Architecture
    add_heading_1(doc, "4. Data Flow & Ingestion Pipelines")
    add_heading_2(doc, "4.1 Pipeline v3 Clinical Evidence Flow")
    add_code_block(doc,
"""1. PATIENT INGESTION:
   [Patient Speech / Text] ──> [ai/voice/speech_to_text.py]
                             ──> [multilingual_symptom_extractor.py]
                                 • Extracts raw colloquial tokens
                                 • Normalizes via canonical regex
                                 • Strips denied/negated symptoms

2. EVIDENCE ISOLATION (Pipeline v3 Gate):
   • Input: { patient_raw_tokens, patient_canonical_tokens, patient_positive_tokens }
   • Hard separation: External candidate titles (NLM/BioPortal) NEVER entered into patient evidence.
   • Constituent Gate: Evaluates composite emergency rules (e.g. RF030 requires Head Trauma + Vomiting).

3. DUAL-TIER INFERENCE:
   • 280-dim Binary Feature Vector ──> [RandomForestClassifier (50 Trees, Gini)]
                                   ──> [Top-5 Differential Predictions]
   • Quality Gate: Drop candidates lacking genuine patient evidence overlap.

4. TRUTHFUL CARE & MEDICATION GATE:
   • Cross-reference predicted drugs with NIH DailyMed & OpenFDA APIs.
   • Unmatched drugs flagged UNVERIFIED (zero hallucinated dosage forms).
   • Suppress non-emergency diagnostic tests (MRI, EEG) if duration <= 4 days.

5. PRESENTATION & EXPORT:
   • Render interactive dashboard cards + ReportLab consultation PDF."""
    )

    add_heading_2(doc, "4.2 National Supply Chain Ingestion & BigQuery Flow")
    add_code_block(doc,
"""1. GOVERNMENT DATA INGESTION:
   [HMIS (20,904 rows) + Beds (36 States) + NFHS-5 (706 Districts) + NLEM 2022 (384 Drugs)]
        │
        ▼ (Canonical Normalization & Immutable Provenance Tagging)
   [Local Edge Store: Apache Parquet / In-Memory DataFrame Cache]

2. OPERATIONAL TELEMETRY & PREDICTIVE ANALYTICS:
   • Compute Days of Inventory Remaining: DOIR = Stock_On_Hand / Consumption_Rate
   • Multi-Factor ML Forecaster: Predicts 7-Day Demand (WAPE 6.53%)
   • Two-Stage Transit Solver: Rebalances stock between surplus and deficit PHCs

3. NATIONAL CLOUD STREAMING:
   • Asynchronous streaming to Google Cloud BigQuery ('command_center' dataset)
   • Partitioning: DATE(snapshot_date)
   • Clustering: state, district, facility_type
   • Enables sub-second macro queries across 30,000+ facilities simultaneously."""
    )

    # 5. Security, Tenancy & Scalability Plan
    add_heading_1(doc, "5. Security, Tenancy & Scalability Plan")
    add_heading_2(doc, "5.1 Supabase PostgreSQL Row-Level Security (RLS)")
    add_body_p(doc, "In multi-user cloud deployments, DocMindX AI enforces strict tenant data isolation at the database engine level via PostgreSQL Row-Level Security policies. Even if application-layer authentication is misconfigured, database policies prevent users from viewing or altering records belonging to other users:")
    
    add_code_block(doc,
"""-- Supabase PostgreSQL RLS Policies (database/supabase_rls_security.sql)
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access their own family members"
ON family_members FOR ALL
USING (auth.uid() = user_id);

ALTER TABLE medical_conditions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access conditions of their family"
ON medical_conditions FOR ALL
USING (family_member_id IN (SELECT id FROM family_members WHERE user_id = auth.uid()));

ALTER TABLE medical_scans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can only access their own uploaded scans"
ON medical_scans FOR ALL
USING (auth.uid() = user_id);"""
    )

    add_heading_2(doc, "5.2 Architecture for 1 Million (10 Lakh) Concurrent Users")
    add_body_p(doc, "To handle nationwide surge traffic during epidemic crises, DocMindX AI implements a horizontally scalable cloud deployment model:")
    add_bullet_p(doc, " The Streamlit application and ML triage engine are containerized using Docker and deployed on Google Kubernetes Engine (GKE) with Horizontal Pod Autoscaling (HPA) triggered by CPU/Memory utilization.", bold_prefix="Stateless Microservices:")
    add_bullet_p(doc, " User sessions, active triage parameters, and recent NLP queries are cached in a distributed Redis cluster, minimizing database reads.", bold_prefix="Distributed Redis Caching:")
    add_bullet_p(doc, " Static logos, icons, CSS styles, and precomputed NLEM drug reference tables are served via Google Cloud CDN with global edge caching.", bold_prefix="Cloud CDN Edge Caching:")
    add_bullet_p(doc, " Analytical queries from the National Command Center bypass operational databases entirely, querying BigQuery partitioned tables without degrading transactional performance.", bold_prefix="BigQuery Read Separation:")

    doc.save(output_path)
    print(f"Generated: {output_path}")

def generate_arch_hi(output_path):
    doc = create_base_document(
        title="DocMindX AI — सिस्टम आर्किटेक्चर दस्तावेज़",
        subtitle="डुअल-टियर हाइब्रिड इंफ्रास्ट्रक्चर, क्लिनिकल पाइपलाइन v3 एवं नेशनल क्लाउड ब्लूप्रिंट",
        doc_type="सिस्टम आर्किटेक्चर दस्तावेज़",
        lang="HI"
    )

    # 1. उच्च स्तरीय आर्किटेक्चरल विजन
    add_heading_1(doc, "1. उच्च स्तरीय सिस्टम ब्लूप्रिंट एवं रणनीति (High-Level Architecture)")
    add_body_p(doc, "DocMindX AI को एक विशिष्ट 'डुअल-टियर हाइब्रिड आर्किटेक्चर' पर डिज़ाइन किया गया है। यह ग्रामीण भारत के कमजोर नेटवर्क वाले क्षेत्रों में स्वतंत्र रूप से काम करने और राष्ट्रीय स्तर पर विशाल क्लाउड डेटा का विश्लेषण करने में सक्षम है। भारत के 30,000+ प्राथमिक स्वास्थ्य केंद्रों में इंटरनेट का टूटना सामान्य है; अतः केवल क्लाउड पर निर्भर रहने वाला सिस्टम विफल हो सकता है।")

    add_callout(
        doc,
        "आर्किटेक्चरल रणनीति: डुअल-टियर हाइब्रिड मॉडल के तहत ग्रामीण केंद्रों पर सब-सेकंड लोकल प्रोसेसिंग (Parquet और SQLite द्वारा 15ms में) होती है, जबकि देशव्यापी डेटा एकत्रीकरण गूगल क्लाउड BigQuery में सेकंडों में पूरा होता है।",
        title="डुअल-टियर हाइब्रिड लचीलापन",
        alert_type="info"
    )

    add_heading_2(doc, "1.1 दोहरे स्तरों का विभाजन")
    add_bullet_p(doc, " प्राथमिक स्वास्थ्य केंद्रों के कंप्यूटरों पर बिना इंटरनेट के भी सभी ML मॉडल, रेड फ्लैग सेफ्टी गेट्स और दवा पुनर्वितरण सॉल्वर 45ms में स्थानीय रूप से चलते हैं।", bold_prefix="टियर 1 — एज-लोकल स्वायत्तता (Edge-Local):")
    add_bullet_p(doc, " देश के 36 राज्यों/केंद्र शासित प्रदेशों के 225+ केंद्रों का डेटा गूगल क्लाउड BigQuery में रियल-टाइम स्ट्रीम होता है, जहाँ तारीख और जिले के आधार पर सेकंडों में बड़े पैमाने पर विश्लेषण होता है।", bold_prefix="टियर 2 — राष्ट्रीय BigQuery क्लाउड एकत्रीकरण:")

    # 2. संपूर्ण तकनीकी स्टैक
    add_heading_1(doc, "2. संपूर्ण तकनीकी स्टैक (Technology Stack)")
    add_body_p(doc, "DocMindX AI में उपयोग किए गए आधुनिक और प्रमाणित तकनीकी घटक निम्नलिखित हैं:")

    stack_data_hi = [
        ["सिस्टम स्तर (Layer)", "प्रौद्योगिकी / फ्रेमवर्क", "वर्जन / मॉडल विवरण", "सिस्टम में भूमिका"],
        ["क्लाइंट प्रेजेंटेशन", "Streamlit एवं Streamlit-Folium", "v1.35.0+ / Folium 0.16.0", "उत्तरदायी वेब डैशबोर्ड, इंटरैक्टिव नक्शे।"],
        ["स्टाइलिंग व थीम", "प्योर वैनिला CSS / डिजाइन टोकन्स", "हाई-कॉन्ट्रास्ट क्लिनिकल थीम", "हल्का, तेज और बिना बाहरी फ्रेमवर्क का UI।"],
        ["कोर बैकएंड", "Python", "3.10 / 3.11", "अत्यधिक तीव्र डेटा प्रोसेसिंग एवं बैकएंड निष्पादन।"],
        ["मशीन लर्निंग", "Scikit-Learn एवं NumPy", "v1.9.1 / NumPy 1.24+", "50-ट्री रैंडम फॉरेस्ट क्लासिफायर व रिग्रेशन मॉडल।"],
        ["मल्टीमॉडल विजन", "Google Gemini 2.5 Flash Vision", "gemini-2.5-flash", "डॉक्टर की पर्चियों और लैब रिपोर्टों का OCR।"],
        ["संवादात्मक AI", "Google Gemini एवं Groq Cloud", "Gemini 2.5 / Llama-3.3-70B", "24x7 क्लिनिकल चैटबॉट और फॉलबैक मॉडल।"],
        ["वॉयस व ऑडियो", "Google Cloud Speech एवं TTS", "Cloud Speech v2 / gTTS", "हिंदी, गुजराती और अंग्रेजी में वॉयस इनपुट व ऑडियो।"],
        ["रिलेशनल डेटाबेस", "Supabase PostgreSQL", "PostgreSQL 15+ (psycopg2)", "यूजर अकाउंट्स, पारिवारिक वॉल्ट, रो-लेवल सुरक्षा।"],
        ["लोकल स्टोरेज", "SQLite एवं Apache Parquet", "SQLite 3 / PyArrow", "स्थानीय ऑफलाइन कैश और 10 सरकारी डेटासेट्स।"],
        ["बिग डेटा वेयरहाउस", "Google Cloud BigQuery", "BigQuery SDK 3.20+", "राष्ट्रीय स्तर का टेलीमेट्री डेटा वेयरहाउस।"]
    ]
    add_styled_table(doc, stack_data_hi[0], stack_data_hi[1:], [1.4, 1.8, 1.8, 1.5])

    # 3. सिस्टम घटक आर्किटेक्चर
    add_heading_1(doc, "3. सिस्टम घटक आर्किटेक्चर (System Components)")
    add_bullet_p(doc, " टॉप नेविगेशन बार, बहुभाषी नियंत्रण (हिंदी, गुजराती, अंग्रेजी), डार्क मोड टॉगल और 5 मुख्य पैनलों का प्रबंधन। इसमें मरीज डेमोग्राफिक्स (उम्र, लिंग, राज्य, ऊंचाई, वजन, ब्लड ग्रुप: A+, A-, B+, B-, AB+, AB-, O+, O-, अज्ञात) और फैमिली प्रोफाइल ऑटो-फिल शामिल है।", bold_prefix="1. क्लाइंट प्रेजेंटेशन लेयर (app.py):")
    add_bullet_p(doc, " 280 लक्षणों का फोनेटिक नॉर्मलाइज़र, साक्ष्य पृथक्करण गेट, 50-ट्री रैंडम फॉरेस्ट (97.58% सटीकता), RF001-RF035 रेड फ्लैग गेट्स और त्रि-स्तरीय परामर्श इंजन (दवा, आहार, योग, कारण)।", bold_prefix="2. क्लिनिकल इंटेलिजेंस इंजन (ai/disease_prediction/):")
    add_bullet_p(doc, " Gemini Vision व Tesseract द्वारा डॉक्टर पर्ची, CBC/LFT/Lipid/KFT ब्लड रिपोर्ट व रेडियोलॉजी का विश्लेषण और आम भाषा में सारांश।", bold_prefix="3. मल्टीमॉडल विजन व रिपोर्ट एनालाइज़र (ai/ocr/):")
    add_bullet_p(doc, " 225+ PHC का डेटा अंतर्ग्रहण, WAPE 6.53% मांग पूर्वानुमानकर्ता, DOIR स्टॉकआउट डिटेक्टर और लीनियर ट्रांसफर सॉल्वर (केवल एडमिन हेतु)।", bold_prefix="4. राष्ट्रीय स्वास्थ्य कमान केंद्र (ai/supply_chain/):")
    add_bullet_p(doc, " DailyMed, OpenFDA, WHO ICD-11, BioPortal और Overpass (1 से 25 किमी दायरा) के साथ सुरक्षित संपर्क।", bold_prefix="5. बाहरी API गेटवे लेयर (api/):")
    add_bullet_p(doc, " स्थानीय एन्क्रिप्टेड SQLite डेटाबेस, Supabase PostgreSQL Row-Level Security और BigQuery क्लाउड सिंक।", bold_prefix="6. डेटाबेस एवं सुरक्षा लेयर (database/):")

    # 4. डेटा फ्लो
    add_heading_1(doc, "4. डेटा प्रवाह एवं पाइपलाइन (Data Flow Pipelines)")
    add_heading_2(doc, "4.1 पाइपलाइन v3 क्लिनिकल डेटा फ्लो")
    add_code_block(doc,
"""रोगी इनपुट (वॉयस / टेक्स्ट / पर्ची इमेज)
       │
       ▼
[मल्टीलिंग्वल सिम्प्टम एक्सट्रैक्टर एवं OCR]
       │ (रोगी के असली लक्षण निकाले जाते हैं)
       ▼
[पाइपलाइन v3 साक्ष्य पृथक्करण गेट]
       │ (बाहरी मेडिकल शोर हटाया जाता है; रेड फ्लैग चेक)
       ▼
[280-फीचर वेक्टर एवं रैंडम फॉरेस्ट 50 ट्रीज]
       │ (Top-5 संभावित बीमारियों का अनुमान)
       ▼
[WHO ICD-11 एवं नॉलेज ग्राफ वैलिडेशन]
       │ (असली लक्षणों से मेल न खाने वाले विकल्प खारिज)
       ▼
[DailyMed / OpenFDA दवा प्रामाणिकता गेट]
       │ (सत्यापित पैकेजिंग व खुराक; 4 दिन से कम बीमारी पर रूटीन टेस्ट ब्लॉक)
       ▼
[इंटरैक्टिव यूजर डैशबोर्ड व PDF रिपोर्ट जनरेटर]"""
    )

    # 5. सुरक्षा एवं 10 लाख समवर्ती यूजर्स की योजना
    add_heading_1(doc, "5. सुरक्षा एवं 10 लाख यूजर्स स्केलेबिलिटी योजना")
    add_heading_2(doc, "5.1 Supabase PostgreSQL Row-Level Security (RLS)")
    add_body_p(doc, "क्लाउड वातावरण में डेटा सुरक्षा के लिए डेटाबेस स्तर पर RLS लागू है, जिससे यह असंभव हो जाता है कि कोई यूजर किसी अन्य व्यक्ति का मेडिकल डेटा या पर्चियां देख सके:")
    
    add_code_block(doc,
"""-- परिवार के सदस्यों के लिए रो-लेवल सुरक्षा (RLS)
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY "यूजर केवल अपने परिवार का डेटा देख सकते हैं"
ON family_members FOR ALL
USING (auth.uid() = user_id);"""
    )

    add_heading_2(doc, "5.2 दस लाख (1 Million) समवर्ती यूजर्स के लिए क्लाउड स्केलिंग")
    add_bullet_p(doc, " एप्लिकेशन को Docker कंटेनर में पैक करके Google Kubernetes Engine (GKE) पर ऑटो-स्केलिंग के साथ चलाया जाता है।", bold_prefix="स्टेटलेस माइक्रोसर्विसेज:")
    add_bullet_p(doc, " यूजर सेशन्स और बार-बार पूछे जाने वाले लक्षणों को Redis क्लस्टर में कैश किया जाता है ताकि डेटाबेस पर लोड न पड़े।", bold_prefix="डिस्ट्रिब्यूटेड Redis कैशिंग:")
    add_bullet_p(doc, " सभी लोगो, फोंट्स, CSS और NLEM संदर्भ फाइलों को Google Cloud CDN के माध्यम से एज सर्वर्स से भेजा जाता है।", bold_prefix="Cloud CDN एज कैशिंग:")
    add_bullet_p(doc, " कमान केंद्र के भारी विश्लेषणात्मक प्रश्न मुख्य डेटाबेस के बजाय सीधे BigQuery पर चलते हैं।", bold_prefix="BigQuery एनालिटिक्स अलगाव:")

    doc.save(output_path)
    print(f"Generated: {output_path}")
