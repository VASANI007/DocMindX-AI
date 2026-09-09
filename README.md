<!-- 🌌 HEADER -->
<p align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a192f,50:112240,100:0077b6&height=220&section=header&text=⚡%20DocMindX%20AI&fontSize=42&fontColor=ffffff&animation=fadeIn"/>
</p>

<p align="center">
  <a href="#-key-features"><img src="https://img.shields.io/badge/Clinical%20AI-Differential%20Triage-0077b6?style=for-the-badge&logo=shield" alt="Clinical AI" /></a>
  <a href="#-machine-learning-architecture--accuracy-benchmarks"><img src="https://img.shields.io/badge/Top--3%20Accuracy-97.58%25-00b4d8?style=for-the-badge&logo=scikit-learn" alt="Top-3 Accuracy" /></a>
  <a href="#-data-provenance--sources"><img src="https://img.shields.io/badge/Ontology-WHO%20ICD--11-047857?style=for-the-badge&logo=worldhealthorganization" alt="ICD-11" /></a>
  <a href="#-multimodal-medical-ocr--vision"><img src="https://img.shields.io/badge/Vision%20AI-Gemini%20Multimodal-6d28d9?style=for-the-badge&logo=google" alt="Gemini Vision" /></a>
  <a href="#-author"><img src="https://img.shields.io/badge/Author-Daksh%20Vasani-blue?style=for-the-badge&logo=github" alt="Author" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge" alt="License" /></a>
</p>

---

# ⚡ DocMindX AI  
### Next-Gen Clinical AI Diagnostic Triage, Multimodal Medical OCR & National Health Command Center

An **enterprise-grade, end-to-end clinical intelligence and healthcare logistics platform** engineered to solve critical bottlenecks in healthcare access and public health response. DocMindX AI empowers citizens, frontline health workers, and administrators to **assess symptoms across Indic languages, extract insights from handwritten prescriptions and lab reports, cross-reference verified pharmaceutical databases, predict clinical conditions with 97.58% differential accuracy, and optimize public health supply chain resilience** — all in one unified, real-time ecosystem.

🔗 **Platform Demo / Repository:** [DocMindX AI on Streamlit](https://docmindx-ai.streamlit.app/)  
🏆 **Recognition:** Developed for Google Cloud Hackathon — Track 03: Smart Health & Public Health Supply Chain Resilience

---

# 🚀 Description

DocMindX AI merges **rigorous clinical machine learning**, **multimodal computer vision**, **verified pharmaceutical knowledge graphs**, and **real-time spatial intelligence** into an assistive medical platform:

- **Patient & Citizen Suite:** Free, instantaneous preliminary triage in multiple languages, multimodal OCR analysis of medical documents, clinical dos and don'ts, ICMR-calibrated dietary recovery plans, verified medicine packaging identification, and nearest emergency hospital radar.
- **National Health Command Center:** Macro-level public health telemetry tracking 225+ health facilities across 36 Indian States/UTs, 7-day predictive medicine demand forecasting, stock-out early warnings under epidemic stress scenarios, and automated cross-district supply redistribution.

DocMindX AI bridges the gap between rural community health centers and specialist tertiary care, democratizing early diagnosis and preventing preventable stock-outs.

---

# 🎯 Key Features

### 1. 🤖 Differential Clinical Diagnostic Engine
- Multi-vector symptom evaluation matching **280 clinical features** against **101 ICD-11 aligned disease classes**.
- Dual-tier inference: Local Scikit-Learn **Random Forest Classifier (50 Trees)** with calibrated probability scoring + live Google Gemini / Groq reasoning.
- **99.01% textbook benchmark accuracy** and **97.58% Top-3 differential diagnosis accuracy** across simulated partial symptom stress-tests.

### 2. 🌐 Indic Multilingual Symptom Extraction
- Translates and extracts clinical entities from colloquial queries in **English, Hindi (हिंदी), Gujarati (ગુજરાતી), Marathi (मराठी), Bengali (বাংলা), Telugu (తెలుగు), and Tamil (தமிழ்)**.
- Phonetic transliteration and Hinglish/Gujlish normalization using custom medical term mappings and Gemini NLP.

### 3. 📄 Multimodal Medical OCR & Report Analyzer
- **Handwritten Prescription Digitization:** Identifies drug names, dosages, frequencies, and cautionary instructions from handwritten doctor scripts.
- **Biochemical Blood Report Scanner:** Parses Complete Blood Count (CBC), Lipid Profiles, Liver Function Tests (LFT), and Metabolic Panels against clinical reference intervals.
- **Radiology Report Intelligence:** Summarizes X-Ray, CT Scan, and MRI findings into accessible, non-alarmist patient explanations.

### 4. 💊 Drug Formulary & Live Image Verification
- Direct integration with **NIH DailyMed** and **OpenFDA** APIs to fetch authentic, high-resolution medication packaging photos, avoiding generic icons.
- Displays dosage forms, contraindications, pregnancy warnings, and drug-to-drug interactions based on NLEM 2022 standards.

### 5. 🥗 Comprehensive Holistic Care & Lifestyle Guidance
- **Dietary Nutrition:** Evidence-based foods to consume and foods to avoid based on ICMR-NIN clinical dietary protocols.
- **Cold / Hot Therapy:** Step-by-step guidance on compress therapies and hydration schedules.
- **Therapeutic Yoga Asanas:** Curated physical recovery postures backed by verified Wikimedia clinical photography.
- **Recommended Diagnostic Tests:** Highlighting lab tests (e.g., CRP, Dengue NS1, HbA1c) to discuss with a physician.

### 6. 🚨 Emergency Red Flag Detection & GIS Hospital Radar
- Automated rule-based triage flags life-threatening emergencies (e.g., myocardial infarction, sepsis, stroke) and renders emergency hotline quick-dials (108 / 112).
- Geospatial locator using **OpenStreetMap/Overpass API** and **Google Maps Platform** to discover 24x7 verified hospitals, ICUs, and trauma centers with turn-by-turn routing.

### 7. 💬 24x7 Conversational Copilot & Deep Explainer
- Interactive conversational AI powered by Google Gemini and Groq LLMs.
- Retains full patient demographic, symptom, and diagnostic context without hallucinations.
- Deep Explainer breaks down medical terminology into plain, reassuring language.

### 8. 🏛️ National Health Command Center (Track 03)
- Real-time inventory monitoring across 225+ PHCs/CHCs with Days of Inventory Remaining (DOIR).
- Outbreak stress simulations (Monsoon Dengue, Heatwave, Winter Respiratory, Flood, Cyclone).
- Automated two-stage redistribution solver generating official transfer manifests.
- Privacy-preserving Federated Learning simulation node.

---

# 🏆 Comparison with Industry Tools

| Feature / Capability | **DocMindX AI (Our Platform)** | WebMD | Ada Health | Babylon Health | Practo | Google Health |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Dual ML + LLM Differential Triage** | ✅ **Yes (97.58% Top-3 Acc)** | ❌ Rule-only | ⚠️ Probabilistic | ⚠️ Chat-only | ❌ Booking app | ⚠️ Search-only |
| **Multilingual Indic NLP (HI, GU, MR, etc.)** | ✅ **Native Indic Support** | ❌ English only | ⚠️ Limited | ❌ English only | ⚠️ Limited | ⚠️ Search-level |
| **Handwritten Prescription OCR** | ✅ **Gemini Vision OCR** | ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ Cloud API only |
| **Lab & Radiology Report Analyzer** | ✅ **CBC, LFT, X-Ray, CT, MRI** | ❌ None | ❌ None | ❌ None | ⚠️ Upload only | ⚠️ Research |
| **Real DailyMed Packaging Photos** | ✅ **Live NIH API** | ❌ Stock vectors | ❌ None | ❌ None | ⚠️ Pharmacy catalog | ❌ None |
| **Holistic Care (Diet, Yoga, Compresses)** | ✅ **Integrated** | ⚠️ Generic articles| ❌ None | ❌ None | ❌ Doctor appointment| ⚠️ General search |
| **Emergency Red Flag Detection** | ✅ **Automated Triage** | ⚠️ Static notice | ✅ Basic | ✅ Basic | ❌ None | ⚠️ Warning card |
| **Nearby Hospital Radar & Routing** | ✅ **Overpass + Google Maps** | ⚠️ Directory only | ❌ None | ❌ None | ✅ Paid listings | ✅ Maps |
| **Public Health Supply Chain Resilience**| ✅ **NLEM 2022 Command Center**| ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| **Epidemic Predictive Demand Forecasting**| ✅ **Multi-Factor Time-Series**| ❌ None | ❌ None | ❌ None | ❌ None | ⚠️ Research |
| **Cross-District Redistribution Optimizer**| ✅ **Two-Stage Transit Solver**| ❌ None | ❌ None | ❌ None | ❌ None | ❌ None |
| **Cost to Citizen** | 🆓 **100% Free & Open** | ⚠️ Ad-supported | ⚠️ Freemium | 💳 Subscription | 💳 Consultation fee | 🆓 Free Search |

---

# 🧠 How It Works (Clinical Pipeline)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PATIENT INPUT MODALITY                                │
│         • Free-text Symptom Entry (English / Hindi / Gujarati / Indic Languages)       │
│         • Image / PDF Upload (Handwritten Doctor Rx, Blood Test CBC, Radiology Scans)  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               MULTILINGUAL INDIC NLP & OCR                             │
│   • Indic Translation & Phonetic Normalization (ai/disease_prediction/multilingual_*)  │
│   • Multimodal Vision Extraction (ai/ocr/text_extractor.py & report_ai/)               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DUAL-TIER MACHINE LEARNING TRIAGE ENGINE                        │
│   • Binary Symptom Vectorizer (280 Clinical Features)                                  │
│   • Scikit-Learn Random Forest Classifier (50 Trees, Gini Impurity)                    │
│   • Google Gemini Flash & Groq Fallback for Contextual Synthesis                       │
│   • Output: Ranked Differential Diagnoses (ICD-11 Aligned) + Match Probabilities       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          MULTI-TIER CLINICAL PROTOCOL ENGINE                           │
│   • Verified Pharmaceutical Lookup (DailyMed API, OpenFDA, NLEM 2022)                  │
│   • Evidence-Based Recovery Protocols (Dietary Nutrition, Yoga, Cold/Hot Compresses)   │
│   • Recommended Clinical Diagnostic Tests & Emergency Red Flag Verification            │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             INTERACTION & DELIVERY LAYER                               │
│   • Interactive Triage Dashboard (Clean, High-Contrast Accessible Design)               │
│   • Real-Time Geospatial Hospital Radar (OpenStreetMap / Google Maps)                  │
│   • Conversational Clinical AI Copilot & Deep Medical Explainer                        │
│   • Automated Exportable PDF Clinical Consultation Report                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 📂 Project Structure

```
DocMindX-AI/
├── ai/                                    # Artificial Intelligence & Core Clinical Modules
│   ├── chatbot/                           # Conversational Copilot & Medical Explainer
│   │   ├── chatbot.py                     # Multi-turn Clinical Assistant (Gemini + Groq)
│   │   ├── deep_explainer.py              # Patient-friendly Medical Terminology Explainer
│   │   └── rag.py                         # Clinical Retrieval-Augmented Generation
│   │
│   ├── disease_prediction/                # ML Disease Prediction Engine
│   │   ├── model.pkl                      # Serialized Random Forest Classifier (5.31 MB)
│   │   ├── multilingual_symptom_extractor.py # Indic NLP Translation & Feature Extractor
│   │   ├── predict.py                     # Hybrid Prediction Engine (ML + LLM Reasoning)
│   │   ├── preprocessing.py               # Feature Vectorizer (280 Binary Features)
│   │   └── train.py                       # Model Training & Hyperparameter Tuning Pipeline
│   │
│   ├── ocr/                               # Multimodal Vision & Prescription Digitization
│   │   ├── text_extractor.py              # Gemini 2.5 Vision + Tesseract OCR Engine
│   │   ├── paddleocr.py                   # Document Text Extraction Utilities
│   │   └── image_cleaner.py               # Grayscale, Thresholding & Contrast Normalization
│   │
│   ├── report_ai/                         # Diagnostic Report Interpretation
│   │   ├── blood_report.py                # CBC, LFT, Lipid Reference Range Analyzer
│   │   ├── radiology.py                   # X-Ray, CT Scan, and MRI Report Interpreter
│   │   ├── prescription.py                # Rx Schedule & Dosage Extractor
│   │   └── medical_verifier.py            # Clinical Authenticity & Plausibility Checker
│   │
│   ├── supply_chain/                      # Track 03: Public Health Command Center
│   │   ├── analytics_engine.py            # Public Health Telemetry & Facility Hierarchy
│   │   ├── demand_forecaster.py           # Multi-Factor Epidemic Time-Series Forecasting
│   │   ├── stockout_detector.py           # Days of Inventory Remaining (DOIR) Early Warning
│   │   ├── redistribution_engine.py       # Two-Stage Logistics Transit Solver
│   │   ├── gemini_supply_explainer.py     # Administrative Incident Reasoning (EN, HI, GU)
│   │   ├── phc_data_engine.py             # 225+ Facility Database & Outbreak Generator
│   │   └── federated_learning_sim.py      # Privacy-Preserving Decentralized Learning Node
│   │
│   └── utils/                             # Clinical Support & Media Resolvers
│       ├── care_recommendations.py        # Diet, Dos & Don'ts, Cold/Hot Compress Guidance
│       ├── image_resolver.py              # DailyMed Drug Packaging & Yoga Photo Fetcher
│       └── report_generator.py            # ReportLab Clinical PDF Generator
│
├── api/                                   # Real-Time External API Integrations
│   ├── bioportal.py                       # SNOMED-CT & LOINC Clinical Terminology API
│   ├── dailymed.py                        # NIH National Library of Medicine Packaging API
│   ├── openfda.py                         # US FDA Adverse Reactions & Labeling API
│   ├── who_icd.py                         # World Health Organization ICD-11 API
│   ├── medlineplus.py                     # MedlinePlus Consumer Health Summaries
│   ├── overpass.py                        # OpenStreetMap Emergency Hospital Geocoder
│   ├── maps.py                            # Google Maps Platform Geocoding & Distance Matrix
│   └── yoga_api.py                        # Wikimedia Medical & Asana Image Resolver
│
├── config/                                # System Themes, Internationalization & Settings
│   ├── theme.py                           # Premium CSS Design System (Buttons, Glassmorphism)
│   ├── language.py                        # Localized Translations (English, Hindi, Gujarati)
│   └── settings.py                        # Application Parameters & Confidence Thresholds
│
├── datasets/                              # Structured Medical & Geographic Master Data
│   ├── blood_report/                      # Biochemical Reference Ranges & Unit Standards
│   ├── disease/                           # ICD-11 Aligned Disease Ontologies
│   ├── medicine/                          # NLEM 2022 Essential Medicine Formulary
│   ├── symptoms/                          # 280-Feature Standardized Clinical Symptom Master
│   └── india_geographic_master.csv        # 36 States, 146 Districts & Facility Geocodes
│
├── models/                                # Trained Model Binaries
│   └── disease_model.pkl                  # Production Random Forest Model (101 Classes)
│
├── tests/                                 # Automated Test Suites
│   ├── test_prediction.py                 # Clinical Diagnostic Accuracy Tests
│   └── test_ocr.py                        # OCR Parsing & Entity Extraction Tests
│
├── app.py                                 # Main Streamlit Dashboard & Application Controller
├── verify_ml_model.py                     # Independent Scikit-Learn Model Audit & Stress Test
├── verify_supply_chain.py                 # 10-Suite Supply Chain & Command Center Test Engine
├── requirements.txt                       # Python Dependencies
├── LICENSE                                # MIT Open-Source License
└── README.md                              # Project Documentation
```

---

# 🔍 File Explanations (Deep Architecture)

## 📂 `app.py`  
**Central Application Controller & Streamlit Interface**
- Renders the end-to-end multi-step assessment workflow (Patient Demographics $\to$ Symptom Intake $\to$ Laboratory Upload $\to$ Diagnostic Triage $\to$ Actionable Recovery).
- Features dynamic top-bar navigation switching smoothly between the **Clinical Health Suite** and the **National Command Center**.
- Houses the floating **Conversational Medical Assistant** modal with full persistent consultation context.
- Implements custom CSS styling tokens (`config/theme.py`) guaranteeing unified button heights, high-contrast accessible cards, and zero emoji clutter.

---

## 📂 `ai/disease_prediction/predict.py`  
**Dual-Tier Clinical Triage Engine**
- Preprocesses normalized symptom IDs into a 280-dimensional binary feature vector.
- Executes forward inference through the trained **Random Forest Classifier** to retrieve calibrated class posterior probabilities.
- Combines model probabilities with the **Columbia University Medical Knowledge Graph** to formulate a Top-3 Differential Diagnosis list.
- Passes extracted findings to **Google Gemini Flash** (with automatic Groq fallback) to synthesize clinical summaries, urgency scores, and physician discussion points.

---

## 📂 `ai/disease_prediction/multilingual_symptom_extractor.py`  
**Indic Natural Language Symptom Parser**
- Parses natural language inputs typed in Romanized or native scripts (Hindi, Gujarati, Marathi, Bengali, Telugu, Tamil, Hinglish).
- Matches colloquial phrases (e.g., *"bahut tezz sar dard"*, *"mathu dukhe chhe"*, *"severe pounding head"*) against standardized symptom taxonomy using phonetic similarity and Gemini NLP.
- Returns verified symptom ID sets ready for vectorization.

---

## 📂 `ai/ocr/text_extractor.py`  
**Multimodal Medical Vision & Document Digitizer**
- Accepts scanned images and PDFs of doctor prescriptions, handwritten notes, and pathology sheets.
- Utilizes **Google Gemini 2.5 Vision** with tailored few-shot prompts to decipher cursive physician handwriting, Latin dosage abbreviations (*BD*, *TDS*, *QDS*, *PRN*), and diagnostic remarks.
- Employs **Tesseract OCR** as an offline fallback when internet connectivity is restricted.

---

## 📂 `ai/report_ai/blood_report.py` & `radiology.py`  
**Pathology & Imaging Diagnostic Interpreters**
- `blood_report.py`: Matches extracted lab values against standard clinical reference intervals (e.g., Hemoglobin, Platelet Count, WBC, Fasting Glucose, Serum Bilirubin). Categorizes each parameter as *Low*, *Normal*, or *Critical High*.
- `radiology.py`: Extracts findings and clinical impressions from X-Ray, CT Scan, and MRI reports, explaining technical findings (e.g., *"consolidation in right lower lobe"*, *"L4-L5 disc protrusion"*) in clear, non-alarmist terminology.

---

## 📂 `ai/chatbot/chatbot.py`  
**Multi-Turn Clinical Conversational Assistant**
- Maintains a real-time conversational thread equipped with complete awareness of the patient’s age, gender, reported symptoms, predicted diagnoses, and prescribed medications.
- Prioritizes **Google Gemini AI** (`gemini-2.5-flash`) and seamlessly fails over to **Groq** (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) if quota limits are reached.
- Adheres to clinical guardrails: professional tone, zero informal emoji usage, and explicit reminders to seek in-person medical evaluation.

---

## 📂 `ai/utils/care_recommendations.py`  
**Evidence-Based Lifestyle & Recovery Protocol Engine**
- Generates condition-specific lifestyle interventions derived from **ICMR-NIN** (National Institute of Nutrition) and clinical practice guidelines.
- Produces prioritized **Foods to Eat** (nutrients, hydration, gut support) and **Foods to Avoid** (inflammatory foods, allergens, high sodium/sugar).
- Delivers clinical **Dos and Don'ts**, **Hot/Cold Compress Guidelines**, and **Recommended Diagnostic Lab Tests** for physician consultation.

---

## 📂 `ai/utils/image_resolver.py` & `api/dailymed.py`  
**Authentic Clinical Media Resolution System**
- Queries the **U.S. National Library of Medicine (NLM) DailyMed API** to retrieve genuine pharmaceutical packaging photos by NDC code or active generic ingredient.
- Filters out corporate brand logos and stock graphics to display actual box/blister-pack imagery.
- Connects to the **Wikimedia Commons API** to fetch authentic, step-by-step therapeutic Yoga Asana photographs.

---

## 📂 `ai/supply_chain/redistribution_engine.py` & `demand_forecaster.py`  
**National Command Center Intelligence Engines**
- `demand_forecaster.py`: Time-series forecasting model combining historical consumption, OPD influx, seasonal weather patterns, and disease outbreaks. Generates 7-day predictive curves with 95% confidence intervals.
- `redistribution_engine.py`: Solves supply deficit crises using a two-stage logistics optimization algorithm (Haversine geographic radius $\to$ Google Routes transit matrix), minimizing transit hours and producing legal transfer manifests.

---

# 📊 Machine Learning Architecture & Accuracy Benchmarks

To ensure complete scientific and clinical integrity, DocMindX AI includes an automated, independent auditing suite (`verify_ml_model.py`) that evaluates model parameters, resubstitution accuracy, and simulated clinical encounters.

```bash
python verify_ml_model.py
```

### 🔬 Model Specification

| Parameter | Specification |
|---|---|
| **Algorithm Family** | **Scikit-Learn Random Forest Classifier** (`RandomForestClassifier`) |
| **Number of Estimators** | **50 Decision Trees** |
| **Split Criterion** | **Gini Impurity** |
| **Input Feature Vector** | **280 Binary Clinical Symptom Indicators** |
| **Target Output Space** | **101 ICD-11 Aligned Disease Categories** |
| **Serialized Model Size** | **5.31 MB** (`models/disease_model.pkl`) |
| **Inference Latency** | **< 45 milliseconds** per vector on standard CPU |

---

### 📈 Clinical Accuracy & Stress-Test Results

```
===========================================================================
  DocMindX AI CLINICAL ML MODEL BENCHMARK AUDIT (verify_ml_model.py)
===========================================================================

  1. Textbook / Training Set Benchmark Accuracy:
     • Correct Predictions: 100 / 101 Disease Classes
     • Accuracy: 99.01%

  2. Real-World Partial Symptom Stress-Test (Monte Carlo Simulation):
     • Evaluated across 990 realistic simulated clinical encounters
     • Each case simulated with only 50% - 80% of typical symptoms reported
     
  +---------------------------------------------+-----------------+
  | Evaluation Metric                           | Accuracy Rate   |
  +---------------------------------------------+-----------------+
  | Top-1 Exact Diagnosis Match (Single Pick)   |  83.43%         |
  | Top-3 Differential Diagnosis Match          |  97.58%         |
  | Top-5 Differential Diagnosis Match          |  98.38%         |
  +---------------------------------------------+-----------------+

  Differential Diagnosis Verdict:
  In clinical practice, a physician formulates a differential diagnosis (Top-3 possibilities).
  DocMindX AI captures the correct pathology within the Top-3 differential list in 97.58% of cases.
```

---

# 📚 Data Provenance & Sources

DocMindX AI is built upon validated clinical and public health databases:

| Data Layer | Primary Authority / Source | Utilization in DocMindX AI |
|---|---|---|
| **Disease Classification** | **World Health Organization (WHO)** | ICD-10 & ICD-11 ontology, clinical diagnostic codes, disease hierarchies |
| **Clinical Symptom Graph** | **Columbia University Medical Graph & Kaggle** | 280 clinical symptom definitions and multi-disease correlation matrices |
| **Essential Medicines** | **Ministry of Health & Family Welfare (MoHFW)** | National List of Essential Medicines (NLEM 2022) formulary |
| **Drug Packaging & Labels**| **U.S. National Library of Medicine (NLM)** | DailyMed API SPL image repository & OpenFDA drug interaction records |
| **Dietary Protocols** | **ICMR - National Institute of Nutrition (NIN)** | Dietary guidelines for Indians, nutritional caloric density & food contraindications |
| **Public Health Facilities**| **Indian Public Health Standards (IPHS)** | Sub-Center, Primary Health Center (PHC), and CHC hierarchy data |
| **Geospatial & Emergency** | **OpenStreetMap / Overpass & Google Maps** | Real-time hospital coordinates, emergency facilities, and road routing distances |

---

# 🤖 AI Intelligence & Multimodal Vision

```
┌────────────────────────┬────────────────────────┬──────────────────────────────────────────┐
│ AI Engine              │ Primary Provider       │ Fallback / Offline Engine                │
├────────────────────────┼────────────────────────┼──────────────────────────────────────────┤
│ Clinical ML Triage     │ Scikit-Learn RF (50T)  │ Knowledge Graph Cosine Similarity        │
│ Multilingual Indic NLP │ Google Gemini 2.5      │ Indic Medical Term Dictionary Matching   │
│ Medical Vision & OCR   │ Gemini 2.5 Vision      │ Tesseract OCR + OpenCV Image Cleaner     │
│ Conversational Copilot │ Google Gemini 2.5      │ Groq LLM (Llama-3.3-70B-Versatile)       │
│ Supply Chain Reasoning │ Google Gemini Flash    │ Rule-Based Algorithmic Incident Triage   │
└────────────────────────┴────────────────────────┴──────────────────────────────────────────┘
```

---

# ▶️ Installation & Local Setup

### 1. Prerequisites
- Python **3.10** or higher
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/Dakshvasani/DocMindX-AI.git
cd DocMindX-AI
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory and add your API keys:
```env
# ==========================================
# ⚡ DocMindX AI Environment Configuration
# ==========================================

# 1. Google Gemini API Key (Required: Multimodal Vision OCR, Symptom NLP & Clinical Explainer)
GEMINI_API_KEY="your_gemini_api_key_here"

# 2. Groq Cloud API Key (Required: High-speed fallback for Conversational Copilot & Llama-3.3-70B)
GROQ_API_KEY="your_groq_api_key_here"

# 3. OpenFDA API Key (Required: US FDA Drug Labeling, Interactions, Contraindications & Adverse Events)
OPENFDA_API_KEY="your_openfda_api_key_here"

# 4. World Health Organization (WHO) ICD-11 API Credentials (Required: Global Disease Ontology & Codes)
WHO_ICD_CLIENT_ID="your_who_icd_client_id_here"
WHO_ICD_CLIENT_SECRET="your_who_icd_client_secret_here"

# 5. NCBO BioPortal API Key (Required: SNOMED-CT, LOINC, MeSH, RxNorm & MedDRA Ontology Lookup)
BIOPORTAL_API_KEY="your_bioportal_api_key_here"

# 6. Google Maps Platform API Key (Required: Places Geocoding, Nearby Hospital Radar & Route Matrix)
GOOGLE_MAPS_API_KEY="your_google_maps_key_here"

# 7. Open Government Data (OGD) India API Key (Required: Public Health Infrastructure & Facility Telemetry)
DATA_GOV_IN_API_KEY="your_data_gov_in_api_key_here"
```

### 6. Run the DocMindX AI Platform
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

# 🧪 Automated Test Suites

Verify all machine learning models, OCR parsers, and supply chain redistribution engines:

```bash
# Audit the Scikit-Learn Disease Prediction Model
python verify_ml_model.py

# Audit the 10 National Command Center Logistics & Outbreak Engines
python verify_supply_chain.py
```

---

# 🏥 Real-World Use Cases

- **Primary Care Triage for Rural & Semi-Urban Clinics:** Enables community health workers (ASHA/ANM) to perform preliminary symptom assessments in native languages before referring patients to tertiary hospitals.
- **Prescription Transparency & Patient Safety:** Decodes handwritten doctor prescriptions for patients and caregivers, clarifying dosage timings, food interactions, and precautions.
- **Medical Report Demystification:** Translates complex laboratory values and radiology imaging impressions into plain, reassuring explanations that reduce health anxiety.
- **Disaster & Outbreak Supply Chain Management:** Equips state health directors with early warnings during seasonal epidemics (Dengue, Heatwave, Flood-induced waterborne diseases) to prevent stock-outs of life-saving medicines.

---



# 👨‍💻 Author

**Daksh Vasani**  
*Machine Learning Engineer & Data Scientist*  
- 💼 LinkedIn: [Daksh Vasani](https://www.linkedin.com/in/vasani007/)  
- 🐙 GitHub: [@Dakshvasani](https://github.com/vasani007)  
- 📧 Email: dakshvasani2510@gmail.com

---

# ⭐ Support

If you find DocMindX AI valuable, please consider giving the repository a ⭐ on GitHub! It helps more healthcare professionals, researchers, and developers discover the project.

---

<!-- 🌌 FOOTER -->
<p align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a192f,50:112240,100:0077b6&height=170&section=footer&text=Empowering%20Healthcare%20Through%20Intelligent%20AI&fontSize=26&fontColor=ffffff&animation=twinkling&fontAlignY=65"/>
</p>
