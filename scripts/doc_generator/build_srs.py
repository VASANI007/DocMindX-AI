import os
import sys
from docx.shared import Inches

from .styler import (
    create_base_document, add_heading_1, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_callout, add_styled_table, add_code_block
)

def generate_srs_en(output_path):
    doc = create_base_document(
        title="DocMindX AI — Software Requirements Specification (SRS)",
        subtitle="Formal Engineering Specifications, Functional Logic & Clinical Data Contracts",
        doc_type="Software Requirements Specification",
        lang="EN"
    )

    # 1. Introduction
    add_heading_1(doc, "1. Introduction")
    add_heading_2(doc, "1.1 Purpose & Scope")
    add_body_p(doc, "This Software Requirements Specification (SRS) document formalizes the complete technical, functional, algorithmic, and architectural requirements for DocMindX AI (Version 2.0 Enterprise Clinical Red Edition). This document serves as the binding technical contract for software engineers, machine learning researchers, clinical safety auditors, and devops infrastructure teams.")
    
    add_heading_2(doc, "1.2 Definitions, Acronyms & Abbreviations")
    glossary = [
        ["Term / Acronym", "Full Expansion", "Operational Definition in DocMindX AI"],
        ["PHC / CHC", "Primary / Community Health Centre", "Tier-1 and Tier-2 rural/semi-urban government healthcare facilities."],
        ["NLEM 2022", "National List of Essential Medicines", "384 essential drug formulations mandated by MoHFW India."],
        ["WHO ICD-11", "International Classification of Diseases 11th Rev.", "Global standard diagnostic classification ontology used for disease classes."],
        ["DOIR", "Days of Inventory Remaining", "Metric: [Stock on Hand / Daily Consumption Rate]. DOIR < 7 triggers stockout alert."],
        ["WAPE", "Weighted Absolute Percentage Error", "Primary metric for demand forecasting error: (Sum |Actual - Forecast| / Sum Actual)."],
        ["RLS", "Row-Level Security", "PostgreSQL database security layer restricting record visibility strictly to the owning user."],
        ["Pipeline v3", "Surgical Clinical Intelligence Pipeline", "Three-tier architecture isolating patient evidence from candidate ontology titles."]
    ]
    add_styled_table(doc, glossary[0], glossary[1:], [1.4, 2.3, 2.8])

    # 2. Overall System Description
    add_heading_1(doc, "2. Overall System Description")
    add_body_p(doc, "DocMindX AI operates as a distributed, dual-tier hybrid platform combining an ultra-fast, local-first client dashboard with an enterprise cloud persistence and analytics layer. The platform executes machine learning inference, medical computer vision, multilingual natural language parsing, and linear supply chain optimization.")
    
    add_heading_2(doc, "2.1 User Classes & Operational Environment")
    add_bullet_p(doc, " Interacting via mobile or desktop web browsers (Chrome, Edge, Safari, Firefox). Consumes trilingual audio/text assessments and layman diagnostic explanations.", bold_prefix="Citizens & Patients:")
    add_bullet_p(doc, " Using portable Android tablets and laptops in community clinics. Utilizes offline-resilient local caches and emergency triage red-flag gates.", bold_prefix="Frontline Workers & Nurses:")
    add_bullet_p(doc, " Operating high-throughput command consoles. Reviews state-wide heatmaps, multi-day demand predictions, and executes cross-district transfer manifests.", bold_prefix="Public Health Administrators:")

    # 3. Functional Requirements
    add_heading_1(doc, "3. Detailed Functional Requirements (FR)")
    add_body_p(doc, "The following 15 functional requirements govern the behavioral logic of the DocMindX AI platform:")

    fr_items = [
        ("FR-01: Multilingual Indic NLP & Negation Engine", 
         "The system SHALL accept free-text and audio input in English, Hindi, Gujarati, Marathi, Bengali, Telugu, and Tamil. The system SHALL execute phonetic transliteration and regular expression normalization against 'ai/disease_prediction/canonical_concepts.py'. The system SHALL strictly detect and filter negated clinical entities (e.g. 'no fever', 'mathu nathi dukhtu') from positive symptom vectors."),
        
        ("FR-02: 280-Dimensional Clinical Feature Vectorization",
         "The system SHALL map extracted canonical tokens into a fixed 280-dimensional binary feature vector. Any recognized symptom SHALL set the corresponding feature index to 1, while absent or denied symptoms SHALL remain 0."),
        
        ("FR-03: Dual-Tier Random Forest Machine Learning Inference",
         "The system SHALL execute inference using a Scikit-Learn RandomForestClassifier (50 Decision Trees, Gini Impurity, serialized as 'models/disease_model.pkl'). The model SHALL output calibrated class probabilities across 101 ICD-11 aligned disease classes within <45 milliseconds on standard CPU."),
        
        ("FR-04: Knowledge Graph Validation & Candidate Re-Ranking",
         "The system SHALL cross-reference ML candidate diseases against a bipartite clinical disease-symptom knowledge graph and live WHO ICD-11 ontology. Candidate diseases lacking verifiable overlap with authentic patient-reported symptoms SHALL be dropped to prevent hallucination."),
        
        ("FR-05: Constituent Red Flag Safety Gating",
         "The system SHALL evaluate rule-based emergency triggers (RF001 to RF035). For composite emergencies (e.g. RF030 Head Injury with Vomiting), the gate SHALL require constituent head trauma PLUS persistent vomiting; isolated headaches SHALL NOT trigger emergency evacuation status."),
        
        ("FR-06: Multimodal Medical Vision & Prescription OCR",
         "The system SHALL process uploaded image files (PNG, JPG, WEBP) and PDF documents. The system SHALL invoke Google Gemini 2.5 Flash Vision (with local PyTesseract + OpenCV thresholding fallback) to extract drug names, dosages, frequencies, and cautionary guidelines."),
        
        ("FR-07: Biochemical Reference Range & Blood Analyzer",
         "The system SHALL parse Complete Blood Count (CBC), Liver Function Tests (LFT), Lipid Profiles, and Metabolic Panels against clinical reference ranges defined in 'datasets/blood_report/'. Any out-of-range value SHALL be classified as High/Low with a clinical severity rating."),
        
        ("FR-08: DailyMed & OpenFDA Truthful Provenance Verification",
         "The system SHALL query NIH DailyMed REST API and OpenFDA API to retrieve authentic packaging images and active ingredients. If an authoritative SPL record is not found, the drug SHALL be flagged as 'UNVERIFIED', strictly preventing fabricated dosage forms or artificial promotions."),
        
        ("FR-09: ICMR-NIN Evidence-Based Nutrition & Duration-Gated Care",
         "The system SHALL generate dietary advice adhering to ICMR-NIN guidelines. If the reported symptom duration is acute (<= 4 days), routine non-emergency diagnostics (e.g. Brain MRI, EEG, Lipid profile) SHALL be suppressed, prioritizing immediate exposure evaluations (rabies, tetanus, wound care)."),
        
        ("FR-10: Overpass QL & Google Maps Real-Time Healthcare Geolocation",
         "The system SHALL query the OpenStreetMap Overpass API and Google Maps Places API within a user-configurable radius (5 to 50 km). It SHALL return verified 24x7 emergency hospitals, ICUs, and trauma centers with turn-by-turn routing distances."),
        
        ("FR-11: Public Health Ingestion Manager (Track 03)",
         "The system SHALL ingest and reconcile 10 official public health data streams (MoHFW HMIS 2019-20, Rajya Sabha Session 266, NFHS-5 706 districts, NLEM 2022, IPHS 2022 norms, and WHO Outbreak reports). Each ingested record SHALL carry an immutable provenance tag."),
        
        ("FR-12: Multi-Factor Epidemic Demand Forecaster",
         "The system SHALL compute 7-day predictive medicine demand forecasts across 225+ health facilities using Scikit-Learn Random Forest Regressor models trained on consumption velocity, seasonal rainfall indices, and disease transmission rates, achieving a WAPE of <= 6.53%."),
        
        ("FR-13: DOIR Stockout Detection & Alerting",
         "The system SHALL compute Days of Inventory Remaining (DOIR) for all facilities. A DOIR < 3 days SHALL trigger a CRITICAL STOCKOUT ALERT; a DOIR between 3 and 7 days SHALL trigger a WARNING ALERT with automated incident summaries generated by Gemini Flash."),
        
        ("FR-14: Two-Stage Logistics Transit & Redistribution Solver",
         "The system SHALL execute a two-stage linear transit solver to resolve regional stockouts. Stage 1 executes intra-district rebalancing between neighboring PHCs. Stage 2 executes inter-district transfers from tertiary district warehouses, producing official transfer manifests."),
        
        ("FR-15: User Authentication, Family Profiles & Supabase RLS",
         "The system SHALL provide email/password registration with Bcrypt hashing, SHA-256 hashed OTP verification, and multi-profile family management. In cloud environments, PostgreSQL Row-Level Security (RLS) SHALL enforce strict tenancy isolation.")
    ]

    for req_title, req_desc in fr_items:
        add_heading_2(doc, req_title)
        add_body_p(doc, req_desc)

    # 4. Non-Functional Requirements
    add_heading_1(doc, "4. Non-Functional Requirements (NFR)")
    
    nfrs = [
        ["NFR Code", "Requirement Category", "Specification Standard", "Verification Method"],
        ["NFR-01", "Inference Latency", "Random Forest vector inference < 45 ms on standard CPU.", "Automated benchmark in verify_ml_model.py"],
        ["NFR-02", "End-to-End Latency", "Full multilingual triage response rendered within 2.5 seconds.", "Streamlit session state timer logging"],
        ["NFR-03", "Security & Encryption", "Passwords hashed via Bcrypt (cost factor 12); TLS 1.3 in transit.", "Security audit in database/supabase_rls_security.sql"],
        ["NFR-04", "Data Privacy & Isolation", "Zero cross-user data leakage enforced via PostgreSQL Row-Level Security.", "Unit tests in tests/test_supabase_rls_security.py"],
        ["NFR-05", "Fault Tolerance", "Zero-crash offline mode using compressed Parquet edge stores.", "Offline simulation tests in verify_supply_chain.py"],
        ["NFR-06", "Scalability", "Support 1,000+ concurrent sessions; BigQuery partition by DATE.", "Load testing & BigQuery partitioning schema"],
        ["NFR-07", "Accessibility", "WCAG 2.1 AA compliant contrast ratio (>= 4.5:1); Zero-emoji clinical UI.", "Theme color tokens in config/theme.py"],
        ["NFR-08", "Multilingual Fidelity", "Consistent semantic intent across English, Hindi, and Gujarati.", "Matrix test in tests/test_symptom_normalization_matrix.py"]
    ]
    add_styled_table(doc, nfrs[0], nfrs[1:], [1.0, 1.8, 2.3, 1.4])

    # 5. External System Interfaces & APIs
    add_heading_1(doc, "5. External System Interfaces & APIs")
    add_body_p(doc, "DocMindX AI integrates with external specialized clinical, geographical, and governmental web services:")

    apis = [
        ["External Service", "Protocol / Endpoint", "Data Exchanged", "Failover Strategy"],
        ["Google Gemini 2.5", "HTTPS REST API (generativelanguage.googleapis.com)", "Multimodal prescription OCR, symptom NLP, deep medical explanations.", "Groq Cloud (Llama-3.3-70B) & local regex."],
        ["NIH DailyMed", "HTTPS REST API (dailymed.nlm.nih.gov/spl-resources)", "Official SPL packaging photos, drug ingredients, and warnings.", "Local NLEM 2022 cached metadata."],
        ["OpenFDA", "HTTPS REST API (api.fda.gov/drug/label.json)", "Drug interactions, boxed warnings, adverse reactions.", "UNVERIFIED provenance fallback flag."],
        ["WHO ICD-11", "OAuth2 / REST API (id.who.int/icd/release/11)", "Global disease ontology entities, clinical coding.", "Local ICD-11 aligned disease dictionary."],
        ["NCBO BioPortal", "REST API (data.bioontology.org/annotator)", "SNOMED-CT, LOINC, and MeSH medical concept mapping.", "Local canonical concepts mapping."],
        ["OpenStreetMap / Overpass", "HTTPS POST (overpass-api.de/api/interpreter)", "Overpass QL queries for 24x7 hospitals, clinics, trauma centers.", "Google Maps Platform Geocoding/Places API."],
        ["Google Cloud Speech", "gRPC / Python SDK (speech.googleapis.com)", "Real-time speech-to-text audio streaming across Indic dialects.", "Local SpeechRecognition / gTTS."]
    ]
    add_styled_table(doc, apis[0], apis[1:], [1.3, 2.0, 1.9, 1.3])

    # 6. Data Flow Architecture
    add_heading_1(doc, "6. Data Flow & Processing Contracts")
    add_body_p(doc, "Data flowing through the clinical pipeline adheres to strict evidence channel separation:")
    add_code_block(doc, 
"""[User Input: Voice / Text / Image]
       │
       ▼
[ai/ocr/text_extractor.py & multilingual_symptom_extractor.py]
       │ (Extracts: patient_raw_tokens, patient_canonical_tokens)
       ▼
[Evidence Isolation Gate: pipeline_v3]
       │ (Purges external candidate contamination; Evaluates Constituent Red Flags)
       ▼
[ai/disease_prediction/predict.py]
       │ (Feature Vectorizer: 280 dims -> RandomForestClassifier: 50 Trees)
       ▼
[Clinical Knowledge Graph & ICD-11 Validator]
       │ (Requires genuine patient evidence overlap before candidate promotion)
       ▼
[Truthful Care & Formulary Gate: care_recommendations.py]
       │ (OpenFDA/DailyMed Verification; Duration-gated diagnostic testing)
       ▼
[Client Presentation: Streamlit Dashboard / ReportLab Clinical PDF]"""
    )

    doc.save(output_path)
    print(f"Generated: {output_path}")

def generate_srs_hi(output_path):
    doc = create_base_document(
        title="DocMindX AI — सॉफ्टवेयर आवश्यकता विनिर्देश (SRS)",
        subtitle="औपचारिक तकनीकी विनिर्देश, कार्यात्मक तर्क एवं क्लिनिकल डेटा अनुबंध",
        doc_type="सॉफ्टवेयर आवश्यकता विनिर्देश (SRS)",
        lang="HI"
    )

    # 1. परिचय
    add_heading_1(doc, "1. परिचय एवं उद्देश्य (Introduction & Scope)")
    add_body_p(doc, "यह सॉफ्टवेयर आवश्यकता विनिर्देश (SRS) दस्तावेज़ DocMindX AI (संस्करण 2.0 एंटरप्राइज क्लिनिकल रेड एडिशन) के सभी तकनीकी, कार्यात्मक, एल्गोरिथम और आर्किटेक्चरल आवश्यकताओं को औपचारिक रूप से परिभाषित करता है। यह दस्तावेज़ सॉफ्टवेयर इंजीनियरों, मशीन लर्निंग शोधकर्ताओं, क्लिनिकल परीक्षकों और DevOps टीमों के लिए तकनीकी अनुबंध के रूप में कार्य करता है।")

    add_heading_2(doc, "1.1 शब्दावली एवं संक्षिप्त रूप (Definitions & Acronyms)")
    glossary_hi = [
        ["शब्द / संक्षिप्त रूप", "पूर्ण रूप", "DocMindX AI में उपयोग एवं परिभाषा"],
        ["PHC / CHC", "प्राथमिक / सामुदायिक स्वास्थ्य केंद्र", "ग्रामीण एवं अर्ध-शहरी सरकारी स्वास्थ्य सुविधाएं।"],
        ["NLEM 2022", "राष्ट्रीय आवश्यक दवा सूची", "भारत सरकार द्वारा निर्धारित 384 अनिवार्य दवाओं का आधिकारिक संग्रह।"],
        ["WHO ICD-11", "इंटरनेशनल क्लासिफिकेशन ऑफ डिजीज 11th Rev.", "विश्व स्वास्थ्य संगठन का अंतर्राष्ट्रीय रोग वर्गीकरण मानक।"],
        ["DOIR", "डेज ऑफ इन्वेंटरी रिमेनिंग (शेष दिनों का स्टॉक)", "फॉर्मूला: [वर्तमान स्टॉक / दैनिक खपत दर]। DOIR < 7 पर चेतावनी जारी होती है।"],
        ["WAPE", "वेटेड एब्सोल्यूट पर्सेंटेज एरर", "मांग पूर्वानुमान त्रुटि मापने का मानक पैमाना: (कुल अंतर / कुल वास्तविक मांग)।"],
        ["RLS", "रो-लेवल सिक्योरिटी (Row-Level Security)", "PostgreSQL सुरक्षा स्तर जो सुनिश्चित करता है कि यूजर केवल अपना डेटा देख सके।"],
        ["Pipeline v3", "सर्जिकल क्लिनिकल इंटेलिजेंस पाइपलाइन", "रोगी के लक्षणों को बाहरी मेडिकल शोर से अलग रखने वाला सुरक्षा ढांचा।"]
    ]
    add_styled_table(doc, glossary_hi[0], glossary_hi[1:], [1.4, 2.3, 2.8])

    # 2. समग्र सिस्टम विवरण
    add_heading_1(doc, "2. समग्र सिस्टम विवरण (Overall System Description)")
    add_body_p(doc, "DocMindX AI एक वितरित, दोहरे स्तर (Dual-Tier Hybrid) का प्लेटफॉर्म है। यह लोकल-फर्स्ट क्लाइंट डैशबोर्ड और एंटरप्राइज क्लाउड स्टोरेज व एनालिटिक्स को जोड़ता है। यह मशीन लर्निंग इन्फेरेंस, कंप्यूटर विजन OCR, बहुभाषी NLP और लीनियर सप्लाई चेन ऑप्टिमाइजेशन को एक साथ संचालित करता है।")

    # 3. कार्यात्मक आवश्यकताएं
    add_heading_1(doc, "3. विस्तृत कार्यात्मक आवश्यकताएं (Functional Requirements - FR)")

    fr_items_hi = [
        ("FR-01: बहुभाषी भारतीय NLP एवं निषेध (Negation) डिटेक्टर",
         "सिस्टम हिंदी, गुजराती, अंग्रेजी, मराठी, बंगाली, तेलुगु और तमिल में टेक्स्ट और वॉयस इनपुट स्वीकार करेगा। यह 'ai/disease_prediction/canonical_concepts.py' के आधार पर फोनेटिक और रेगेक्स नॉर्मलाइजेशन करेगा। यदि मरीज ने 'बुखार नहीं है' या 'माथु नथी दुखतु' कहा है, तो उस लक्षण को धनात्मक साक्ष्य से बाहर रखा जाएगा।"),

        ("FR-02: 280-आयामी क्लिनिकल फीचर वेक्टर निर्माण",
         "सिस्टम निष्कर्षित लक्षणों को एक निश्चित 280-आयामी बाइनरी वेक्टर में बदलेगा। पहचाने गए लक्षण का मान 1 होगा और अनुपस्थित लक्षण का मान 0 रहेगा।"),

        ("FR-03: डुअल-टियर रैंडम फॉरेस्ट मशीन लर्निंग इन्फेरेंस",
         "सिस्टम Scikit-Learn RandomForestClassifier (50 Decision Trees, Gini Impurity, मॉडल फाइल 'models/disease_model.pkl') द्वारा 101 ICD-11 रोग श्रेणियों पर अनुमान लगाएगा। मानक CPU पर इसका इन्फेरेंस समय 45 मिलीसेकंड से कम होगा।"),

        ("FR-04: क्लिनिकल नॉलेज ग्राफ सत्यापन एवं री-रैंकिंग",
         "सिस्टम ML द्वारा सुझाई गई बीमारियों का सत्यापन कोलंबिया नॉलेज ग्राफ और WHO ICD-11 डेटा से करेगा। जिन बीमारियों का मरीज के लक्षणों से वास्तविक मेल नहीं होगा, उन्हें सूची से हटा दिया जाएगा।"),

        ("FR-05: घटक रेड फ्लैग इमरजेंसी सुरक्षा गेट्स",
         "सिस्टम RF001 से RF035 तक के इमरजेंसी नियमों की जांच करेगा। संयुक्त आपात स्थितियों में (जैसे RF030 सिर में चोट + उल्टी) दोनों घटकों का उपस्थित होना अनिवार्य होगा; केवल सिरदर्द पर इमरजेंसी घोषित नहीं होगी।"),

        ("FR-06: मल्टीमॉडल मेडिकल विजन एवं पर्ची OCR",
         "सिस्टम डॉक्टर की हाथ से लिखी पर्चियों (PNG, JPG, PDF) को Google Gemini 2.5 Flash Vision और Tesseract द्वारा स्कैन करके दवाओं के नाम, खुराक (Dosage) और समय सारणी निकालेगा।"),

        ("FR-07: बायोकेमिकल रेफरेंस रेंज एवं ब्लड रिपोर्ट विश्लेषक",
         "सिस्टम कम्पलीट ब्लड काउंट (CBC), LFT और लिपिड प्रोफाइल की जांच 'datasets/blood_report/' के मानकों के अनुसार करेगा और असामान्य मानों को क्लिनिकल गंभीरता के साथ दर्शाएगा।"),

        ("FR-08: DailyMed एवं OpenFDA दवा प्रामाणिकता सत्यापन",
         "सिस्टम US FDA और NIH DailyMed API से दवा की असली पैकेजिंग और तत्वों का मिलान करेगा। आधिकारिक रिकॉर्ड न मिलने पर दवा को 'UNVERIFIED' चिन्हित करेगा ताकि झूठी जानकारी न फैले।"),

        ("FR-09: ICMR-NIN आहार एवं अवधि-आधारित स्वास्थ्य परामर्श",
         "सिस्टम बीमारी की अवधि के अनुसार आहार और थेरेपी सुझाएगा। यदि बीमारी 4 दिन से कम पुरानी है, तो गैर-जरूरी महंगे टेस्ट (जैसे Brain MRI, EEG) को रोककर केवल आपातकालीन जांचों को प्राथमिकता देगा।"),

        ("FR-10: Overpass एवं Google Maps आपातकालीन अस्पताल रडार",
         "सिस्टम OpenStreetMap Overpass API और Google Maps का उपयोग करके 5 से 50 किमी के दायरे में 24x7 खुले आपातकालीन अस्पतालों और ICU का रास्ता दिखाएगा।"),

        ("FR-11: राष्ट्रीय सार्वजनिक स्वास्थ्य डेटा अंतर्ग्रहण (ट्रैक 03)",
         "सिस्टम HMIS 20,904 रिकॉर्ड्स, NFHS-5 706 जिलों और NLEM 2022 के डेटा को एकीकृत करेगा। प्रत्येक रिकॉर्ड पर अपरिवर्तनीय स्रोत पहचान (Provenance Tag) दर्ज होगी।"),

        ("FR-12: मल्टी-फैक्टर महामारी मांग पूर्वानुमानकर्ता",
         "सिस्टम 225+ स्वास्थ्य केंद्रों में दवाओं की आगामी 7-दिवसीय मांग का पूर्वानुमान लगाएगा (WAPE त्रुटि दर 6.53% या उससे कम)।"),

        ("FR-13: DOIR स्टॉकआउट पहचान एवं अलर्ट सिस्टम",
         "सिस्टम प्रत्येक केंद्र के शेष दिनों के स्टॉक (DOIR) की गणना करेगा। DOIR 3 दिन से कम होने पर तत्काल क्रिटिकल अलर्ट जारी होगा।"),

        ("FR-14: दो-चरणीय लॉजिस्टिक्स दवा पुनर्वितरण सॉल्वर",
         "सिस्टम लीनियर प्रोग्रामिंग द्वारा अतिरिक्त स्टॉक वाले केंद्रों से कमी वाले केंद्रों में दवा ट्रांसफर का आधिकारिक मैनिफेस्ट स्वतः तैयार करेगा।"),

        ("FR-15: उपयोगकर्ता प्रमाणीकरण, पारिवारिक प्रोफाइल एवं Supabase RLS",
         "सिस्टम Bcrypt हैशिंग, OTP सुरक्षा और Supabase PostgreSQL Row-Level Security के साथ मरीजों और परिवारों का डेटा पूर्णतः गोपनीय रखेगा।")
    ]

    for req_title, req_desc in fr_items_hi:
        add_heading_2(doc, req_title)
        add_body_p(doc, req_desc)

    # 4. गैर-कार्यात्मक आवश्यकताएं
    add_heading_1(doc, "4. गैर-कार्यात्मक आवश्यकताएं (Non-Functional Requirements - NFR)")

    nfrs_hi = [
        ["NFR कोड", "आवश्यकता श्रेणी", "तकनीकी मानक", "सत्यापन विधि"],
        ["NFR-01", "इन्फेरेंस लेटेंसी", "मानक CPU पर Random Forest अनुमान 45 मिलीसेकंड से कम।", "verify_ml_model.py द्वारा प्रमाणित"],
        ["NFR-02", "संपूर्ण रिस्पांस समय", "मल्टीलिंग्वल ट्राइएज का पूरा उत्तर 2.5 सेकंड के भीतर।", "सेशन टाइमर लॉगिंग"],
        ["NFR-03", "सुरक्षा व एन्क्रिप्शन", "Bcrypt हैशिंग (कॉस्ट फैक्टर 12); नेटवर्क पर TLS 1.3।", "सुरक्षा ऑडिट स्क्रिप्ट"],
        ["NFR-04", "डेटा गोपनीयता", "PostgreSQL Row-Level Security द्वारा यूजर डेटा का पूर्ण अलगाव।", "test_supabase_rls_security.py"],
        ["NFR-05", "त्रुटि सहनशीलता (Offline)", "इंटरनेट न होने पर कंप्रेस्ड Parquet स्टोर से 100% कार्य।", "verify_supply_chain.py"],
        ["NFR-06", "स्केलेबिलिटी", "1,000+ समवर्ती यूजर्स; BigQuery में तारीख के आधार पर पार्टिशनिंग।", "BigQuery पार्टिशनिंग स्कीमा"],
        ["NFR-07", "एक्सेसिबिलिटी", "WCAG 2.1 AA अनुपात (>= 4.5:1); जीरो-इमोजी क्लिनिकल इंटरफ़ेस।", "config/theme.py कलर सिस्टम"],
        ["NFR-08", "बहुभाषी सटीकता", "हिंदी, अंग्रेजी और गुजराती में समान चिकित्सीय अर्थ।", "test_symptom_normalization_matrix.py"]
    ]
    add_styled_table(doc, nfrs_hi[0], nfrs_hi[1:], [1.0, 1.8, 2.3, 1.4])

    # 5. बाह्य सिस्टम इंटरफेस
    add_heading_1(doc, "5. बाह्य सिस्टम इंटरफेस एवं APIs (External System Interfaces)")

    apis_hi = [
        ["बाहरी सेवा / API", "प्रोटोकॉल / एंडपॉइंट", "डेटा आदान-प्रदान", "वैकल्पिक फॉलबैक (Failover)"],
        ["Google Gemini 2.5", "HTTPS REST API", "मल्टीमॉडल पर्ची OCR, लक्षण NLP, क्लिनिकल व्याख्या।", "Groq Cloud (Llama-3.3-70B) व लोकल रेगेक्स।"],
        ["NIH DailyMed", "HTTPS REST API", "दवाओं के आधिकारिक फोटो, घटक और सावधानियां।", "स्थानीय NLEM 2022 डेटाबेस।"],
        ["OpenFDA", "HTTPS REST API", "दवाओं के दुष्प्रभाव (Side Effects) व परस्पर प्रभाव।", "UNVERIFIED स्टेटस फ्लैग।"],
        ["WHO ICD-11", "OAuth2 REST API", "विश्व स्वास्थ्य संगठन रोग वर्गीकरण कोड।", "स्थानीय 101 रोग ऑन्टोलॉजी।"],
        ["NCBO BioPortal", "REST API", "SNOMED-CT व LOINC मेडिकल शब्दावली मैपिंग।", "स्थानीय कैनोनिकल लक्षण मैपिंग।"],
        ["OpenStreetMap / Overpass", "HTTPS POST (Overpass QL)", "निकटतम 24x7 आपातकालीन अस्पताल व ICU खोज।", "Google Maps Platform APIs।"],
        ["Google Cloud Speech", "gRPC / Python SDK", "भारतीय बोलियों में रीयल-टाइम वॉइस स्पीच-टू-टेक्स्ट।", "लोकल SpeechRecognition / gTTS।"]
    ]
    add_styled_table(doc, apis_hi[0], apis_hi[1:], [1.3, 2.0, 1.9, 1.3])

    doc.save(output_path)
    print(f"Generated: {output_path}")
