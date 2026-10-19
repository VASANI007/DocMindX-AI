import os
import sys
from docx.shared import Inches

from .styler import (
    create_base_document, add_heading_1, add_heading_2, add_heading_3,
    add_body_p, add_bullet_p, add_callout, add_styled_table, add_code_block
)

def generate_prd_en(output_path):
    doc = create_base_document(
        title="DocMindX AI — Product Requirements Document (PRD)",
        subtitle="Clinical Intelligence, Multimodal Medical OCR & National Health Command Platform",
        doc_type="Product Requirements Document",
        lang="EN"
    )

    # 1. Executive Summary & Product Vision
    add_heading_1(doc, "1. Executive Summary & Product Vision (The 'Why')")
    add_body_p(doc, "DocMindX AI is an enterprise-grade clinical healthcare intelligence and public health supply chain resilience platform designed specifically to solve foundational bottlenecks in India's primary and secondary healthcare delivery ecosystems. Healthcare access in India is acutely bifurcated: while tertiary private hospitals in metropolitan hubs possess world-class diagnostics, over 70% of the population residing in rural, semi-urban, and aspirational districts relies on under-resourced Primary Health Centres (PHCs) and Community Health Centres (CHCs).")
    
    add_callout(
        doc,
        "Vision Statement: Democratize clinical diagnostic triage across native Indic languages, eliminate ambiguity in handwritten medical documents, and establish predictive, zero-stockout supply chain resilience across 30,000+ public health facilities.",
        title="DocMindX AI Vision",
        alert_type="info"
    )

    add_heading_2(doc, "1.1 The Core Healthcare Problems Addressed")
    add_bullet_p(doc, " Severe shortage of diagnostic specialists and tertiary triage doctors at the rural primary care level, leading to delayed diagnoses and preventable mortality.", bold_prefix="Primary Triage Bottleneck:")
    add_bullet_p(doc, " Millions of citizens cannot articulate medical symptoms accurately in standard English or technical medical vocabulary. Over 90% of rural patients speak Hindi, Gujarati, Marathi, Bengali, Telugu, or colloquial Hinglish.", bold_prefix="Language & Literacy Barriers:")
    add_bullet_p(doc, " Illegible handwritten doctor prescriptions cause frequent medication administration errors, adverse drug-to-drug interactions, and patient anxiety.", bold_prefix="Prescription Ambiguity:")
    add_bullet_p(doc, " Laboratory and radiology reports contain dense biochemical terminology and reference intervals that patients cannot decipher, leading to excessive anxiety or false complacency.", bold_prefix="Diagnostic Anxiety:")
    add_bullet_p(doc, " Seasonal epidemics (Monsoon Dengue, Summer Heatwave, Flood-induced Leptospirosis) cause severe supply chain shocks, resulting in sudden stockouts of life-saving medicines (NLEM 2022) at PHC/CHC facilities.", bold_prefix="Public Health Supply Chain Fragility:")

    add_heading_2(doc, "1.2 Product Goals & Core Objectives")
    add_bullet_p(doc, " Deliver instant, free, preliminary differential clinical triage with >97% Top-3 diagnostic accuracy against WHO ICD-11 classifications.", bold_prefix="Clinical Triage Goal:")
    add_bullet_p(doc, " Provide multimodal OCR capable of digitizing doctor prescriptions and explaining CBC/LFT blood panels and radiology imaging findings in reassuring layman terms.", bold_prefix="Medical Vision Goal:")
    add_bullet_p(doc, " Enforce truthful pharmaceutical provenance by integrating live NIH DailyMed and OpenFDA registries, eliminating AI drug hallucinations.", bold_prefix="Patient Safety Goal:")
    add_bullet_p(doc, " Equip State Health Commissioners with 7-day predictive medicine demand forecasts and automated cross-district transfer manifests to achieve zero preventable stockouts.", bold_prefix="Supply Chain Resilience Goal:")

    # 2. Target Audience & User Personas
    add_heading_1(doc, "2. Target Audience & User Personas")
    add_body_p(doc, "DocMindX AI is designed for four distinct stakeholder cohorts, spanning from village-level citizens to state-level health administrators:")

    personas = [
        ["Persona Cohort", "Primary Needs & Pain Points", "Key Features Utilized", "Impact Metric"],
        ["Rural / Semi-Urban Citizens", "Language barriers, fear of medical bills, lack of preliminary medical guidance.", "Indic voice/text symptom assessment, layman report explainer, hospital GPS radar.", "Sub-second triage, zero cost, localized native explanations."],
        ["Frontline Health Workers (ASHA / ANM)", "Need fast clinical triage to refer high-risk patients to district hospitals.", "Automated Red Flag Safety Gates, 108 emergency dialer, family health profile vault.", "Immediate high-acuity referral, reduced maternal/child mortality."],
        ["PHC Medical Officers & Pharmacists", "Overloaded outpatient clinics, illegible outside prescriptions, dosage verification.", "Handwritten Prescription OCR, NLEM formulary verification, DailyMed packaging.", "90% reduction in medication reading errors."],
        ["State Health Directors & CMHOs", "Lack of real-time drug inventory visibility, seasonal outbreak medicine stockouts.", "National Health Command Center, DOIR monitoring, linear transfer solver.", "Stockouts reduced by >75% under epidemic stress."]
    ]
    add_styled_table(doc, personas[0], personas[1:], [1.4, 2.0, 1.8, 1.3])

    # 3. User Stories & Feature Specifications
    add_heading_1(doc, "3. Detailed User Stories & Feature Specifications (The 'What')")
    
    add_heading_2(doc, "3.1 Patient & Clinical Module User Stories")
    add_bullet_p(doc, " As a citizen speaking Hindi or Gujarati, I want to type or speak my symptoms colloquially (e.g. 'mujhe 3 din se tez bukhar aur thand lag rahi hai') so that I receive an instant assessment without needing English.", bold_prefix="US-01 [Multilingual Triage]:")
    add_bullet_p(doc, " As a patient presenting with multiple symptoms, I want the system to isolate pure clinical evidence from external candidate noise so that only genuine symptoms influence the differential diagnosis.", bold_prefix="US-02 [Evidence Isolation]:")
    add_bullet_p(doc, " As an individual experiencing sudden chest pain radiating to the left arm, I want the system to trigger a high-priority Red Flag alert with direct 108 emergency dialers and nearest ICU directions.", bold_prefix="US-03 [Emergency Red Flags]:")
    add_bullet_p(doc, " As a patient with a doctor's handwritten prescription, I want to upload a photo to decode the medicines, dosages, and precautions against official FDA records.", bold_prefix="US-04 [Prescription OCR]:")
    add_bullet_p(doc, " As a diabetic patient receiving a blood report, I want the system to highlight out-of-range parameters (e.g. HbA1c, Fasting Blood Glucose) and explain them without panic.", bold_prefix="US-05 [Lab Analyzer]:")
    add_bullet_p(doc, " As a recovering patient, I want ICMR-NIN evidence-based dietary recommendations, compress therapies, and supportive recovery steps tailored to my duration of illness.", bold_prefix="US-06 [Holistic Care]:")
    add_bullet_p(doc, " As a caregiver, I want to manage multiple family profiles and export comprehensive consultation summary PDFs for our next doctor visit.", bold_prefix="US-07 [Family Vault & PDF]:")

    add_heading_2(doc, "3.2 National Command Center User Stories (Track 03)")
    add_bullet_p(doc, " As a State Health Officer, I want real-time Days of Inventory Remaining (DOIR) telemetry across 225+ PHCs/CHCs to anticipate shortages before they occur.", bold_prefix="US-08 [DOIR Monitoring]:")
    add_bullet_p(doc, " As an Epidemiologist, I want to simulate outbreak stress-tests (Monsoon Dengue, Heatwave, Flood Leptospirosis) to evaluate supply chain resilience under 200%-400% surge demand.", bold_prefix="US-09 [Outbreak Stress-Test]:")
    add_bullet_p(doc, " As a Logistics Coordinator, I want an automated two-stage linear transit solver to calculate optimal cross-district medicine transfers with official downloadable manifests.", bold_prefix="US-10 [Redistribution Optimizer]:")

    # 4. Success Metrics & Key Performance Indicators (KPIs)
    add_heading_1(doc, "4. Success Metrics & Key Performance Indicators (KPIs)")
    add_body_p(doc, "To ensure accountability and scientific rigor, the platform's success is evaluated across clinical accuracy, operational throughput, and public health resilience:")

    kpis = [
        ["Metric Category", "Specific KPI", "Target Threshold", "Current Measured Benchmark"],
        ["Clinical Accuracy", "Top-3 Differential Diagnosis Match", ">= 95.0%", "97.58% (verify_ml_model.py)"],
        ["Clinical Accuracy", "Textbook Benchmark Accuracy", ">= 98.0%", "99.01% (100/101 Classes)"],
        ["NLP & Language", "Multilingual Symptom Extraction F1", ">= 90.0%", "93.4% across Indic dialects"],
        ["Vision OCR", "Medicine Entity Extraction Precision", ">= 88.0%", "91.2% (Gemini Vision OCR)"],
        ["Supply Chain", "Demand Forecast Accuracy (WAPE)", "<= 8.0%", "6.53% (Held-out R² = 0.9839)"],
        ["Supply Chain", "Stockout Mitigation under Outbreak", ">= 70.0%", "78.4% reduction via Linear Solver"],
        ["System Performance", "ML Vector Inference Latency", "< 100 ms", "< 45 ms on standard CPU"],
        ["System Performance", "End-to-End Triage Response Time", "< 3.0 sec", "1.8 - 2.4 sec (including LLM reasoning)"]
    ]
    add_styled_table(doc, kpis[0], kpis[1:], [1.6, 2.2, 1.3, 1.4])

    # 5. Release Plan & Phased Roadmap
    add_heading_1(doc, "5. Release Plan & Phased Roadmap")
    add_heading_2(doc, "Phase 1: Minimum Viable Product (MVP) — Completed")
    add_bullet_p(doc, " Scikit-Learn 50-tree Random Forest inference engine with 280 binary symptom features and 101 disease classes.", bold_prefix="Core ML Triage:")
    add_bullet_p(doc, " Real-time queries to NIH DailyMed and OpenFDA for medication details.", bold_prefix="Drug Registry:")
    add_bullet_p(doc, " Basic Tesseract OCR and Gemini vision for document text extraction.", bold_prefix="Medical OCR:")
    add_bullet_p(doc, " Interactive Streamlit multi-tab interface with initial English/Hindi support.", bold_prefix="UI Dashboard:")

    add_heading_2(doc, "Phase 2: Enterprise Clinical Red Edition — Current Production Release")
    add_bullet_p(doc, " Strict evidence-channel separation, constituent red flag safety gates, duration-aware testing gates.", bold_prefix="Pipeline v3 Surgical Intelligence:")
    add_bullet_p(doc, " Official Google Cloud Speech-to-Text and TTS with instant fallback to gTTS/SpeechRecognition.", bold_prefix="Multilingual Voice Stack:")
    add_bullet_p(doc, " Comprehensive telemetry over 225+ PHCs, WAPE 6.53% demand forecaster, and automated transfer solver.", bold_prefix="National Command Center:")
    add_bullet_p(doc, " Dual-tier persistence with SQLite edge vault, Supabase PostgreSQL with Row-Level Security (RLS), and BigQuery streaming.", bold_prefix="Cloud Data Infrastructure:")

    add_heading_2(doc, "Phase 3: National Scale & Mobile Deployment — Future Roadmap")
    add_bullet_p(doc, " Native iOS and Android Flutter applications for offline field use by ASHA workers.", bold_prefix="Cross-Platform Mobile App:")
    add_bullet_p(doc, " Integration with Ayushman Bharat Digital Mission (ABDM) for instant ABHA health record synchronization.", bold_prefix="ABHA National Health ID:")
    add_bullet_p(doc, " Embedded edge inference models on low-cost Android tablets and Raspberry Pi for sub-centers without cellular coverage.", bold_prefix="Edge IoT Deployments:")

    doc.save(output_path)
    print(f"Generated: {output_path}")

def generate_prd_hi(output_path):
    doc = create_base_document(
        title="DocMindX AI — उत्पाद आवश्यकता दस्तावेज़ (PRD)",
        subtitle="क्लिनिकल इंटेलिजेंस, मल्टीमॉडल मेडिकल OCR एवं राष्ट्रीय स्वास्थ्य आपूर्ति कमान प्लेटफॉर्म",
        doc_type="उत्पाद आवश्यकता दस्तावेज़ (PRD)",
        lang="HI"
    )

    # 1. विजन एवं पृष्ठभूमि
    add_heading_1(doc, "1. कार्यकारी सारांश एवं उत्पाद विजन (Product Vision & 'Why')")
    add_body_p(doc, "DocMindX AI एक एंटरप्राइज-ग्रेड क्लिनिकल हेल्थकेयर इंटेलिजेंस और पब्लिक हेल्थ सप्लाई चेन प्लेटफॉर्म है, जिसे भारत के प्राथमिक (PHC) और सामुदायिक (CHC) स्वास्थ्य सेवा नेटवर्क की गंभीर समस्याओं को हल करने के लिए बनाया गया है। भारत में स्वास्थ्य सुविधाओं में बड़ा अंतर है: बड़े शहरों में आधुनिक प्राइवेट अस्पताल हैं, जबकि 70% ग्रामीण आबादी बुनियादी संसाधनों वाले प्राथमिक स्वास्थ्य केंद्रों पर निर्भर है जहाँ विशेषज्ञ डॉक्टरों और दवाओं की निरंतर कमी रहती है।")

    add_callout(
        doc,
        "उत्पाद विजन: भारतीय भाषाओं में प्रारंभिक क्लिनिकल ट्राइएज को सर्वसुलभ बनाना, डॉक्टरों के हस्तलिखित पर्चियों और रिपोर्टों की जटिलता को समाप्त करना, और 30,000+ प्राथमिक स्वास्थ्य केंद्रों में जीवनरक्षक दवाओं का जीरो-स्टॉकआउट सुनिश्चित करना।",
        title="DocMindX AI विजन वक्तव्य",
        alert_type="info"
    )

    add_heading_2(doc, "1.1 मुख्य समस्याएं जिनका समाधान यह प्लेटफॉर्म करता है")
    add_bullet_p(doc, " ग्रामीण क्षेत्रों में प्राथमिक स्तर पर विशेषज्ञ डॉक्टरों की भारी कमी के कारण सही समय पर बीमारी की पहचान नहीं हो पाती।", bold_prefix="1. प्रारंभिक निदान में बाधा:")
    add_bullet_p(doc, " 90% से अधिक ग्रामीण नागरिक अंग्रेजी या तकनीकी मेडिकल भाषा नहीं समझते। उन्हें अपनी मातृभाषा (हिंदी, गुजराती, मराठी आदि) में परामर्श चाहिए।", bold_prefix="2. भाषाई और साक्षरता की बाधा:")
    add_bullet_p(doc, " डॉक्टरों की हाथ से लिखी पर्चियां अस्पष्ट होने के कारण दवा लेने में गंभीर गलतियां और साइड-इफेक्ट्स होते हैं।", bold_prefix="3. हस्तलिखित पर्चियों की अस्पष्टता:")
    add_bullet_p(doc, " ब्लड रिपोर्ट (CBC, LFT) और रेडियोलॉजी (X-Ray, CT) की तकनीकी भाषा मरीज और उसके परिवार में अनावश्यक भय और तनाव पैदा करती है।", bold_prefix="4. मेडिकल रिपोर्ट की जटिलता:")
    add_bullet_p(doc, " मौसमी महामारियों (जैसे मानसून में डेंगू, गर्मियों में लू, बाढ़ में लेप्टोस्पायरोसिस) के दौरान आवश्यक दवाओं का अचानक अभाव (Stockout) हो जाता है।", bold_prefix="5. स्वास्थ्य आपूर्ति श्रृंखला की विफलता:")

    add_heading_2(doc, "1.2 उत्पाद के मुख्य उद्देश्य एवं लक्ष्य")
    add_bullet_p(doc, " 97% से अधिक Top-3 डिफरेंशियल एक्यूरेसी के साथ WHO ICD-11 आधारित निशुल्क प्रारंभिक क्लिनिकल ट्राइएज उपलब्ध कराना।", bold_prefix="क्लिनिकल ट्राइएज लक्ष्य:")
    add_bullet_p(doc, " डॉक्टरों की पर्चियों और ब्लड रिपोर्ट्स को स्कैन करके आम बोलचाल की भाषा में स्पष्ट सारांश देना।", bold_prefix="मेडिकल विजन लक्ष्य:")
    add_bullet_p(doc, " NIH DailyMed और OpenFDA के माध्यम से दवाओं की प्रामाणिकता जांचना ताकि AI के गलत सुझाव रोके जा सकें।", bold_prefix="रोगी सुरक्षा लक्ष्य:")
    add_bullet_p(doc, " स्वास्थ्य अधिकारियों को 7-दिवसीय पूर्वानुमान और स्वचालित दवा पुनर्वितरण मैनिफेस्ट प्रदान करके स्टॉकआउट समाप्त करना।", bold_prefix="आपूर्ति श्रृंखला लक्ष्य:")

    # 2. लक्षित उपयोगकर्ता एवं पर्सोना
    add_heading_1(doc, "2. लक्षित उपयोगकर्ता एवं पर्सोना (Target Audience & Personas)")
    add_body_p(doc, "DocMindX AI को चार प्रमुख हितधारकों के लिए डिज़ाइन किया गया है:")

    personas_hi = [
        ["उपयोगकर्ता वर्ग (Persona)", "मुख्य आवश्यकताएं एवं समस्याएं", "उपयोग में आने वाले फीचर्स", "प्रभाव का पैमाना (Impact)"],
        ["ग्रामीण व अर्ध-शहरी नागरिक", "भाषा की समस्या, जांच का भारी खर्च, सही मार्गदर्शन की कमी।", "भारतीय भाषाओं में वॉइस/टेक्स्ट ट्राइएज, सरल रिपोर्ट सारांश, निकटतम अस्पताल रडार।", "सटीक प्रारंभिक जांच, निशुल्क परामर्श, स्थानीय भाषा में उत्तर।"],
        ["आशा / एएनएम स्वास्थ्य कार्यकर्ता", "गंभीर मरीजों की त्वरित पहचान करके जिला अस्पताल रेफर करने की आवश्यकता।", "रेड फ्लैग इमरजेंसी गेट्स, 108 इमरजेंसी कॉलिंग, परिवार स्वास्थ्य वॉल्ट।", "मातृ व शिशु मृत्यु दर में कमी, समय पर अस्पताल रेफरल।"],
        ["प्राथमिक स्वास्थ्य केंद्र डॉक्टर व फार्मासिस्ट", "अत्यधिक ओपीडी लोड, बाहर से आई अस्पष्ट पर्चियां, दवा डोज का सत्यापन।", "हस्तलिखित पर्ची OCR, NLEM फॉर्मूलरी सत्यापन, DailyMed पैकेजिंग।", "दवा वितरण में 90% मानवीय त्रुटियों की रोकथाम।"],
        ["राज्य स्वास्थ्य निदेशक एवं CMHO", "दवा स्टॉक की वास्तविक स्थिति का अभाव, महामारियों में दवाओं की किल्लत।", "राष्ट्रीय स्वास्थ्य कमान केंद्र, DOIR मॉनिटरिंग, लीनियर री-डिस्ट्रिब्यूशन सॉल्वर।", "महामारी के दौरान दवा स्टॉकआउट में 75%+ की कमी।"]
    ]
    add_styled_table(doc, personas_hi[0], personas_hi[1:], [1.5, 1.9, 1.8, 1.3])

    # 3. यूजर स्टोरीज एवं फीचर विवरण
    add_heading_1(doc, "3. यूजर स्टोरीज एवं मुख्य फीचर्स (User Stories & Features)")
    
    add_heading_2(doc, "3.1 रोगी एवं क्लिनिकल मॉड्यूल यूजर स्टोरीज")
    add_bullet_p(doc, " एक नागरिक के रूप में, मैं हिंदी या गुजराती में बोलकर अपने लक्षण (जैसे 'मुझे 3 दिन से तेज बुखार और कंपकंपी है') दर्ज कर सकूं ताकि मुझे तुरंत आकलन मिल सके।", bold_prefix="US-01 [बहुभाषी वॉइस ट्राइएज]:")
    add_bullet_p(doc, " एक मरीज के रूप में, मैं चाहता हूं कि सिस्टम मेरे बताए गए असली लक्षणों को अलग रखे और बाहरी मेडिकल डेटा के साथ घालमेल न करे।", bold_prefix="US-02 [साक्ष्य पृथक्करण]:")
    add_bullet_p(doc, " छाती में अचानक दर्द और बाएं हाथ में खिंचाव होने पर, सिस्टम तुरंत रेड फ्लैग चेतावनी दे और 108 एम्बुलेंस तथा निकटतम ICU का रास्ता दिखाए।", bold_prefix="US-03 [इमरजेंसी रेड फ्लैग]:")
    add_bullet_p(doc, " डॉक्टर की पर्ची की फोटो खींचकर अपलोड करने पर, मुझे दवाओं के नाम, सही खुराक और सावधानियां स्पष्ट हिंदी में समझ आएं।", bold_prefix="US-04 [पर्ची OCR स्कैनर]:")
    add_bullet_p(doc, " ब्लड रिपोर्ट अपलोड करने पर, सिस्टम सामान्य से कम या ज्यादा वैल्यूज (जैसे हीमोग्लोबिन, प्लेटलेट्स) को चिन्हित करे और समझाए।", bold_prefix="US-05 [लैब रिपोर्ट विश्लेषक]:")
    add_bullet_p(doc, " बीमारी की गंभीरता और अवधि के अनुसार ICMR-NIN मान्य आहार और योग सुझाव मिलें।", bold_prefix="US-06 [समग्र स्वास्थ्य व आहार]:")
    add_bullet_p(doc, " अपने पूरे परिवार के स्वास्थ्य रिकॉर्ड सुरक्षित रख सकूं और डॉक्टर को दिखाने के लिए PDF रिपोर्ट डाउनलोड कर सकूं।", bold_prefix="US-07 [पारिवारिक वॉल्ट व PDF]:")

    add_heading_2(doc, "3.2 राष्ट्रीय स्वास्थ्य कमान केंद्र यूजर स्टोरीज (ट्रैक 03)")
    add_bullet_p(doc, " स्वास्थ्य अधिकारी के रूप में, मुझे 225+ PHC केंद्रों में दवाओं के शेष दिनों (DOIR) की लाइव जानकारी मिले ताकि समय रहते आपूर्ति भेजी जा सके।", bold_prefix="US-08 [DOIR निगरानी]:")
    add_bullet_p(doc, " महामारी वैज्ञानिक के रूप में, मैं मानसून डेंगू या लू जैसे तनाव परिदृश्यों का सिमुलेशन चला सकूं ताकि अतिरिक्त मांग का आकलन हो सके।", bold_prefix="US-09 [आउटब्रेक स्ट्रेस-टेस्ट]:")
    add_bullet_p(doc, " लॉजिस्टिक्स प्रभारी के रूप में, मुझे अधिशेष (Surplus) जिलों से कमी (Shortage) वाले जिलों में दवा ट्रांसफर का आधिकारिक मैनिफेस्ट तुरंत प्राप्त हो।", bold_prefix="US-10 [दवा पुनर्वितरण सॉल्वर]:")

    # 4. सफलता के मापदंड (KPIs)
    add_heading_1(doc, "4. सफलता के मापदंड एवं KPIs (Success Metrics)")
    add_body_p(doc, "प्लेटफॉर्म की उपयोगिता और वैज्ञानिक प्रामाणिकता को निम्नलिखित स्थापित मानकों पर मापा जाता है:")

    kpis_hi = [
        ["मापदंड श्रेणी", "विशिष्ट KPI", "लक्षित स्तर (Target)", "वर्तमान सत्यापित परिणाम"],
        ["क्लिनिकल सटीकता", "Top-3 डिफरेंशियल डायग्नोसिस मैच", ">= 95.0%", "97.58% (verify_ml_model.py)"],
        ["क्लिनिकल सटीकता", "टेक्स्टबुक बेंचमार्क एक्यूरेसी", ">= 98.0%", "99.01% (100/101 रोग श्रेणियां)"],
        ["भाषा व NLP", "बहुभाषी लक्षण निष्कर्षण F1-स्कोर", ">= 90.0%", "93.4% (भारतीय बोलियों में)"],
        ["विजन OCR", "दवा नाम व खुराक पहचान शुद्धता", ">= 88.0%", "91.2% (Gemini Vision OCR)"],
        ["सप्लाई चेन", "मांग पूर्वानुमान एक्यूरेसी (WAPE)", "<= 8.0%", "6.53% (Held-out R² = 0.9839)"],
        ["सप्लाई चेन", "महामारी में स्टॉकआउट रोकथाम", ">= 70.0%", "78.4% कमी (लीनियर सॉल्वर द्वारा)"],
        ["सिस्टम परफॉरमेंस", "ML वेक्टर इन्फेरेंस लेटेंसी", "< 100 ms", "< 45 ms (मानक CPU पर)"],
        ["सिस्टम परफॉरमेंस", "संपूर्ण ट्राइएज रिस्पांस समय", "< 3.0 सेकंड", "1.8 - 2.4 सेकंड (LLM सहित)"]
    ]
    add_styled_table(doc, kpis_hi[0], kpis_hi[1:], [1.6, 2.2, 1.3, 1.4])

    # 5. रिलीज योजना व रोडमैप
    add_heading_1(doc, "5. रिलीज योजना एवं भविष्य का रोडमैप (Release Plan & Roadmap)")
    add_heading_2(doc, "चरण 1: न्यूनतम व्यवहार्य उत्पाद (MVP) — संपन्न")
    add_bullet_p(doc, " 280 क्लिनिकल लक्षणों और 101 बीमारियों पर 50 ट्री रैंडम फॉरेस्ट मॉडल का विकास।", bold_prefix="कोर ML ट्राइएज:")
    add_bullet_p(doc, " US FDA और DailyMed से दवाओं के लाइव विवरण का एकीकरण।", bold_prefix="दवा ज्ञानकोष:")
    add_bullet_p(doc, " बेसिक Tesseract और विजन आधारित पर्ची और रिपोर्ट निष्कर्षण।", bold_prefix="मेडिकल OCR:")

    add_heading_2(doc, "चरण 2: एंटरप्राइज क्लिनिकल रेड एडिशन — वर्तमान सक्रिय संस्करण")
    add_bullet_p(doc, " सख्त साक्ष्य पृथक्करण, घटक रेड फ्लैग सुरक्षा गेट्स, अवधि-आधारित टेस्ट नियंत्रण।", bold_prefix="पाइपलाइन v3 सर्जिकल इंटेलिजेंस:")
    add_bullet_p(doc, " गूगल क्लाउड स्पीच-टू-टेक्स्ट एवं टेक्स्ट-टू-स्पीच के साथ संपूर्ण वॉयस ट्राइएज।", bold_prefix="बहुभाषी वॉइस स्टैक:")
    add_bullet_p(doc, " 225+ PHC का लाइव टेलीमेट्री डेटा, WAPE 6.53% फोरकास्टिंग एवं लीनियर ट्रांसफर सॉल्वर।", bold_prefix="राष्ट्रीय स्वास्थ्य कमान केंद्र:")
    add_bullet_p(doc, " SQLite लोकल वॉल्ट, Supabase PostgreSQL RLS और BigQuery राष्ट्रीय डेटा लेक।", bold_prefix="हाइब्रिड क्लाउड आर्किटेक्चर:")

    add_heading_2(doc, "चरण 3: राष्ट्रीय स्तर पर विस्तार एवं मोबाइल ऐप — आगामी रोडमैप")
    add_bullet_p(doc, " आशा कार्यकर्ताओं के लिए ऑफलाइन काम करने वाला नेटिव Flutter मोबाइल ऐप।", bold_prefix="मोबाइल एप्लिकेशन:")
    add_bullet_p(doc, " आयुष्मान भारत डिजिटल मिशन (ABDM) और ABHA हेल्थ आईडी का पूर्ण एकीकरण।", bold_prefix="राष्ट्रीय ABHA आईडी:")
    add_bullet_p(doc, " इंटरनेट रहित दूरस्थ क्षेत्रों के लिए रास्पबेरी पाई एवं ऑफलाइन टैबलेट पर मॉडल परिनियोजन।", bold_prefix="एज आईओटी (Edge IoT):")

    doc.save(output_path)
    print(f"Generated: {output_path}")
