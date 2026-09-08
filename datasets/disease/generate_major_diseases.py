"""
DocMindX AI — India Comprehensive Major Disease Master Dataset (100+ Diseases)
Covers all 18 MoHFW / CBHI / NCDC disease categories with ICD codes, multilingual names (EN, HI, GU),
clinical symptoms, medications, diagnostic tests, specialist referrals, and dietary guidance.
"""
import os
import json
import pandas as pd

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, "datasets", "disease")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAJOR_DISEASES = [
    # ================= 1. CARDIOVASCULAR DISEASES =================
    {
        "disease_id": "CVD001", "disease_name": "Hypertension (High Blood Pressure)",
        "disease_name_hi": "हाई ब्लड प्रेशर / उच्च रक्तचाप (Hypertension)",
        "disease_name_gu": "હાઈ બ્લડ પ્રેશર (Hypertension)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Very High", "icd_code": "I10",
        "communicable": False, "outbreak_prone": False, "specialist": "Cardiologist / General Physician",
        "urgency": "Moderate Attention (Regular Monitoring)",
        "symptoms": ["Headache", "Dizziness", "Shortness of breath", "Chest discomfort", "Blurred vision", "Fatigue"],
        "medicines": ["Amlodipine 5mg", "Telmisartan 40mg", "Hydrochlorothiazide 12.5mg"],
        "tests": ["Blood Pressure Monitoring", "Lipid Profile", "ECG", "Serum Creatinine"],
        "diet": "Low sodium DASH diet, high potassium fruits, avoid processed and salty foods."
    },
    {
        "disease_id": "CVD002", "disease_name": "Ischemic Heart Disease (IHD)",
        "disease_name_hi": "इस्केमिक हृदय रोग (Ischemic Heart Disease)",
        "disease_name_gu": "ઇસ્કેમિક હૃદય રોગ (IHD)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Very High", "icd_code": "I25.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Cardiologist",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Chest pain (Angina)", "Shortness of breath", "Pain radiating to left arm/jaw", "Cold sweat", "Dizziness"],
        "medicines": ["Aspirin 75mg", "Atorvastatin 20mg", "Sorbitrate (Isosorbide Dinitrate)", "Metoprolol 25mg"],
        "tests": ["12-Lead ECG", "Troponin I/T", "2D Echocardiogram", "Coronary Angiography"],
        "diet": "Low fat, zero trans-fat heart-healthy Mediterranean diet with nuts and fiber."
    },
    {
        "disease_id": "CVD003", "disease_name": "Coronary Artery Disease (CAD)",
        "disease_name_hi": "कोरोनरी आर्टरी रोग (Coronary Artery Disease)",
        "disease_name_gu": "કોરોનરી આર્ટરી ડિસીઝ (CAD)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Very High", "icd_code": "I25.1",
        "communicable": False, "outbreak_prone": False, "specialist": "Cardiologist",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Chest tightness", "Shortness of breath with exertion", "Fatigue", "Heart palpitations"],
        "medicines": ["Clopidogrel 75mg", "Atorvastatin 40mg", "Rosuvastatin 10mg"],
        "tests": ["CT Coronary Angiogram", "Lipid Profile", "ECG", "TMT Stress Test"],
        "diet": "Strict low cholesterol, rich in garlic, omega-3, leafy greens and oats."
    },
    {
        "disease_id": "CVD004", "disease_name": "Acute Myocardial Infarction (Heart Attack)",
        "disease_name_hi": "हार्ट अटैक / मायोकार्डियल इन्फ्रक्शन (Heart Attack)",
        "disease_name_gu": "હાર્ટ એટેક (Heart Attack)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Very High", "icd_code": "I21.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Interventional Cardiologist / Emergency Physician",
        "urgency": "Critical / Emergency Immediate Hospitalization",
        "symptoms": ["Severe crushing chest pain", "Pain radiating to jaw, neck, left arm", "Shortness of breath", "Cold sweating", "Nausea", "Fainting"],
        "medicines": ["Aspirin 300mg chewable", "Clopidogrel 300mg", "Atorvastatin 80mg", "Sublingual Nitroglycerin"],
        "tests": ["Emergency 12-Lead ECG", "High-Sensitivity Troponin-T/I", "Emergency Angiography"],
        "diet": "Emergency cardiac protocol; post-stabilization strict cardiac rehabilitation diet."
    },
    {
        "disease_id": "CVD005", "disease_name": "Heart Failure",
        "disease_name_hi": "हार्ट फेलियर (Heart Failure)",
        "disease_name_gu": "હાર્ટ ફેલિયર (Heart Failure)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "High", "icd_code": "I50.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Cardiologist",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Shortness of breath while lying flat (Orthopnea)", "Swollen legs/ankles (Edema)", "Rapid weight gain", "Extreme fatigue"],
        "medicines": ["Furosemide (Lasix) 40mg", "Spironolactone 25mg", "Sacubitril/Valsartan", "Dapagliflozin 10mg"],
        "tests": ["NT-proBNP Serum Marker", "Echocardiogram (EF Calculation)", "Chest X-Ray"],
        "diet": "Strict fluid restriction (< 1.5 L/day), strict low salt (< 2g/day)."
    },
    {
        "disease_id": "CVD006", "disease_name": "Stroke (Cerebrovascular Accident)",
        "disease_name_hi": "स्ट्रोक / लकवा / पक्षाघात (Brain Stroke)",
        "disease_name_gu": "બ્રેઈન સ્ટ્રોક / લકવો (Stroke)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Very High", "icd_code": "I64",
        "communicable": False, "outbreak_prone": False, "specialist": "Neurologist / Emergency Stroke Team",
        "urgency": "Critical / Emergency Immediate Hospitalization",
        "symptoms": ["Sudden facial drooping", "Arm weakness or numbness", "Slurred speech / difficulty speaking", "Sudden severe headache", "Loss of balance"],
        "medicines": ["tPA Thrombolysis (Within 4.5h window)", "Aspirin 150mg", "Atorvastatin 40mg", "Mannitol"],
        "tests": ["Emergency Non-Contrast Brain CT Scan", "Brain MRI / MRA", "Carotid Doppler"],
        "diet": "Swallowing-safe soft diet, low sodium, neuro-protective nutrition."
    },
    {
        "disease_id": "CVD007", "disease_name": "Cerebrovascular Disease",
        "disease_name_hi": "सेरेब्रोवास्कुलर रोग (Cerebrovascular Disease)",
        "disease_name_gu": "સેરેબ્રોવાસ્ક્યુલર ડિસીઝ",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Very High", "icd_code": "I67.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Neurologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Transient ischemic attacks (Mini-strokes)", "Memory decline", "Dizziness", "Visual disturbances"],
        "medicines": ["Clopidogrel 75mg", "Atorvastatin 20mg", "Cilostazol"],
        "tests": ["Brain MRI MRA", "Carotid Ultrasound", "Lipid Profile"],
        "diet": "Low sodium, plant-forward antioxidant diet."
    },
    {
        "disease_id": "CVD008", "disease_name": "Rheumatic Heart Disease (RHD)",
        "disease_name_hi": "रुमेटिक हृदय रोग (Rheumatic Heart Disease)",
        "disease_name_gu": "રૂમેટિક હાર્ટ ડિસીઝ (RHD)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "High", "icd_code": "I09.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Cardiologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["History of sore throat / fever", "Heart murmur", "Joint pain and swelling", "Shortness of breath"],
        "medicines": ["Benzathine Penicillin G (Prophylaxis)", "Digoxin", "Diuretics"],
        "tests": ["ASO Titre Test", "2D Echocardiogram (Valvular assessment)", "ECG"],
        "diet": "Well-balanced protein and micronutrient diet, monitor salt."
    },
    {
        "disease_id": "CVD009", "disease_name": "Congenital Heart Disease (CHD)",
        "disease_name_hi": "जन्मजात हृदय रोग (Congenital Heart Disease)",
        "disease_name_gu": "જન્મજાત હૃદય રોગ (CHD)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Medium", "icd_code": "Q24.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Pediatric Cardiologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Cyanosis (Bluish skin/lips)", "Poor feeding in infants", "Fast breathing", "Heart murmur", "Failure to thrive"],
        "medicines": ["Diuretics", "Digoxin", "Sildenafil (if pulmonary hypertension)"],
        "tests": ["Pediatric Echocardiogram", "Pulse Oximetry", "Chest X-Ray"],
        "diet": "Calorie-dense nutrition, frequent small feedings for infants."
    },
    {
        "disease_id": "CVD010", "disease_name": "Peripheral Artery Disease (PAD)",
        "disease_name_hi": "पेरिफेरल आर्टरी रोग (Peripheral Artery Disease)",
        "disease_name_gu": "પેરિફેરલ આર્ટરી ડિસીઝ (PAD)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Medium", "icd_code": "I73.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Vascular Surgeon / Cardiologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Painful leg cramping while walking (Claudication)", "Cold legs/feet", "Weak pulse in legs", "Hair loss on legs"],
        "medicines": ["Cilostazol 100mg", "Aspirin 75mg", "Atorvastatin 40mg"],
        "tests": ["Ankle-Brachial Index (ABI)", "Arterial Doppler Ultrasound of Legs"],
        "diet": "Smoking cessation, low saturated fat diet, structured walking exercise."
    },
    {
        "disease_id": "CVD011", "disease_name": "Cardiomyopathy (Dilated / Hypertrophic)",
        "disease_name_hi": "कार्डियोमायोपैथी (Cardiomyopathy)",
        "disease_name_gu": "કાર્ડિયોમાયોપેથી (Cardiomyopathy)",
        "category": "Cardiovascular Diseases", "category_icon": "", "priority": "Medium", "icd_code": "I42.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Cardiologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Breathlessness", "Chest pain", "Fainting episodes (Syncope)", "Palpitations", "Swollen abdomen and legs"],
        "medicines": ["Beta Blockers (Bisoprolol)", "ACE Inhibitors", "Spironolactone"],
        "tests": ["Cardiac MRI", "2D Echo with Strain Imaging", "Holter Monitor 24h"],
        "diet": "Low sodium, avoid strenuous unmonitored exertion."
    },

    # ================= 2. CANCER & ONCOLOGY =================
    {
        "disease_id": "CAN001", "disease_name": "Breast Cancer",
        "disease_name_hi": "स्तन कैंसर (Breast Cancer)",
        "disease_name_gu": "સ્તન કેન્સર (Breast Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Very High", "icd_code": "C50.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Surgical / Medical Oncologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Painless breast lump or thickening", "Change in breast shape/size", "Nipple discharge (bloody/clear)", "Skin dimpling", "Swollen underarm lymph nodes"],
        "medicines": ["Tamoxifen 20mg", "Anastrozole 1mg", "Trastuzumab", "Chemotherapy (Doxorubicin/Paclitaxel)"],
        "tests": ["Digital Bilateral Mammography", "Breast Ultrasound", "Tru-Cut Biopsy / FNAC", "ER/PR/HER2 IHC Panel"],
        "diet": "Antioxidant-rich whole foods, cruciferous vegetables (broccoli), zero alcohol."
    },
    {
        "disease_id": "CAN002", "disease_name": "Cervical Cancer",
        "disease_name_hi": "गर्भाशय ग्रीवा का कैंसर (Cervical Cancer)",
        "disease_name_gu": "ગર્ભાશયના મુખનું કેન્સર (Cervical Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Very High", "icd_code": "C53.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Gynaecological Oncologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Abnormal vaginal bleeding between periods", "Post-coital bleeding", "Foul-smelling vaginal discharge", "Pelvic pain"],
        "medicines": ["Cisplatin", "Paclitaxel", "Carboplatin", "Bevacizumab"],
        "tests": ["Pap Smear Screening", "HPV DNA High-Risk Testing", "Colposcopy with Directed Biopsy", "Pelvic MRI"],
        "diet": "High folate and carotenoid foods (spinach, carrots, citrus fruits)."
    },
    {
        "disease_id": "CAN003", "disease_name": "Oral / Mouth Cancer",
        "disease_name_hi": "मुंह का कैंसर (Oral / Mouth Cancer)",
        "disease_name_gu": "મોંનું કેન્સર (Oral Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Very High", "icd_code": "C06.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Head & Neck Oncosurgeon",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Non-healing mouth ulcer (> 2 weeks)", "White/red patches in mouth (Leukoplakia)", "Difficulty chewing/swallowing", "Lump in neck/jaw", "Restricted mouth opening"],
        "medicines": ["Chemotherapy (Cisplatin + 5-FU)", "Cetuximab", "Pain management (Morphine/Tramadol)"],
        "tests": ["Incisional Biopsy of Oral Lesion", "CT / MRI Neck and Face", "PET-CT Whole Body"],
        "diet": "Soft non-spicy nutrient-dense diet; immediate cessation of tobacco, betel nut (Gutkha), and smoking."
    },
    {
        "disease_id": "CAN004", "disease_name": "Lung Cancer",
        "disease_name_hi": "फेफड़ों का कैंसर (Lung Cancer)",
        "disease_name_gu": "ફેફસાંનું કેન્સર (Lung Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Very High", "icd_code": "C34.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Thoracic Medical Oncologist / Pulmonologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Persistent chronic cough (> 3 weeks)", "Coughing up blood (Hemoptysis)", "Shortness of breath", "Unexplained weight loss", "Chest pain", "Hoarseness"],
        "medicines": ["Osimertinib / Gefitinib (EGFR+)", "Pembrolizumab (Immunotherapy)", "Carboplatin + Pemetrexed"],
        "tests": ["High-Resolution CT (HRCT) Chest", "Bronchoscopy with EBUS-TBNA Biopsy", "EGFR / ALK / ROS1 Genetic Panel"],
        "diet": "High calorie, high protein anti-inflammatory diet."
    },
    {
        "disease_id": "CAN005", "disease_name": "Colorectal Cancer (Colon & Rectal)",
        "disease_name_hi": "कोलोरेक्टल / आंतों का कैंसर (Colorectal Cancer)",
        "disease_name_gu": "મોટા આંતરડાનું કેન્સર (Colorectal Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C18.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Gastrointestinal Oncologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Blood in stool (Dark red or bright red)", "Persistent change in bowel habits (Diarrhea/Constipation)", "Unexplained weight loss", "Abdominal cramps", "Iron deficiency anemia"],
        "medicines": ["FOLFOX / FOLFIRI Regimens", "Capecitabine", "Bevacizumab"],
        "tests": ["Full Colonoscopy with Biopsy", "Fecal Occult Blood Test (FOBT)", "Serum CEA Tumor Marker", "Abdominal CT"],
        "diet": "High soluble fiber, avoid red meat and ultra-processed cured meats."
    },
    {
        "disease_id": "CAN006", "disease_name": "Stomach / Gastric Cancer",
        "disease_name_hi": "पेट का कैंसर (Stomach / Gastric Cancer)",
        "disease_name_gu": "જઠરનું કેન્સર (Stomach Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C16.9",
        "communicable": False, "outbreak_prone": False, "specialist": "GI Surgical Oncologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Persistent indigestion and heartburn", "Early satiety (feeling full after small bites)", "Vomiting blood or coffee-ground vomit", "Black tarry stools (Melena)", "Weight loss"],
        "medicines": ["FLOT Chemotherapy Regimen", "Trastuzumab (if HER2+)", "Capecitabine + Oxaliplatin"],
        "tests": ["Upper GI Endoscopy with Biopsy", "CT Abdomen & Pelvis", "H. pylori Testing"],
        "diet": "Small frequent bland meals, avoid salty preserved foods and pickled items."
    },
    {
        "disease_id": "CAN007", "disease_name": "Liver Cancer (Hepatocellular Carcinoma)",
        "disease_name_hi": "लिवर कैंसर (Liver Cancer / HCC)",
        "disease_name_gu": "લિવર કેન્સર (Liver Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C22.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Hepatologist / Hepato-Biliary Oncosurgeon",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Right upper quadrant abdominal pain", "Severe jaundice", "Swelling of abdomen (Ascites)", "Unexplained weight loss and fatigue", "Enlarged hard liver (Hepatomegaly)"],
        "medicines": ["Atezolizumab + Bevacizumab", "Sorafenib / Lenvatinib 4mg/8mg"],
        "tests": ["Serum Alpha-Fetoprotein (AFP)", "Triple Phase Contrast CT Abdomen / MRI", "Liver Biopsy"],
        "diet": "Low sodium (< 2g/day), adequate clean protein, zero alcohol."
    },
    {
        "disease_id": "CAN008", "disease_name": "Prostate Cancer",
        "disease_name_hi": "प्रोस्टेट कैंसर (Prostate Cancer)",
        "disease_name_gu": "પ્રોસ્ટેટ કેન્સર (Prostate Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C61",
        "communicable": False, "outbreak_prone": False, "specialist": "Uro-Oncologist",
        "urgency": "Specialist Oncology Consultation",
        "symptoms": ["Difficulty starting or stopping urination", "Weak or interrupted urine flow", "Frequent urination especially at night", "Blood in urine or semen", "Bone pain in hips/lower back"],
        "medicines": ["Bicalutamide 50mg", "Leuprolide / Goserelin Injections (Androgen Deprivation)", "Enzalutamide"],
        "tests": ["Serum Prostate-Specific Antigen (Total & Free PSA)", "Digital Rectal Examination (DRE)", "Multiparametric Prostate MRI (mpMRI)", "TRUS-Guided Biopsy"],
        "diet": "Lycopene-rich foods (cooked tomatoes), green tea, pomegranate, cruciferous vegetables."
    },
    {
        "disease_id": "CAN009", "disease_name": "Ovarian Cancer",
        "disease_name_hi": "अंडाशय का कैंसर (Ovarian Cancer)",
        "disease_name_gu": "અંડાશયનું કેન્સર (Ovarian Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C56.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Gynaecological Oncologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Persistent abdominal bloating and swelling", "Quickly feeling full when eating", "Pelvic and lower abdominal pain", "Frequent urgent need to urinate", "Fatigue and weight loss"],
        "medicines": ["Carboplatin + Paclitaxel", "PARP Inhibitors (Olaparib)", "Bevacizumab"],
        "tests": ["Serum CA-125 Tumor Marker", "Transvaginal Ultrasound (TVS)", "CECT Abdomen and Pelvis", "BRCA1 / BRCA2 Genetic Testing"],
        "diet": "High protein wholesome anti-inflammatory nutrition."
    },
    {
        "disease_id": "CAN010", "disease_name": "Esophageal / Food Pipe Cancer",
        "disease_name_hi": "भोजन नली का कैंसर (Esophageal Cancer)",
        "disease_name_gu": "અન્નનળીનું કેન્સર (Esophageal Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C15.9",
        "communicable": False, "outbreak_prone": False, "specialist": "GI Surgical Oncologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Progressive difficulty swallowing (Dysphagia - solids first, then liquids)", "Painful swallowing (Odynophagia)", "Chest pain or burning sensation", "Regurgitation of food", "Significant weight loss"],
        "medicines": ["Chemotherapy (CROSS Regimen: Paclitaxel + Carboplatin)", "Radiation therapy", "Pain management"],
        "tests": ["Upper GI Endoscopy with Biopsy", "Barium Swallow X-Ray", "CT Chest and Abdomen", "Endoscopic Ultrasound (EUS)"],
        "diet": "Soft, pureed, high-calorie liquid nutrition; avoid hot beverages and irritants."
    },
    {
        "disease_id": "CAN014", "disease_name": "Thyroid Cancer",
        "disease_name_hi": "थायरॉइड कैंसर (Thyroid Cancer)",
        "disease_name_gu": "થાઇરોઇડ કેન્સર (Thyroid Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Medium", "icd_code": "C73",
        "communicable": False, "outbreak_prone": False, "specialist": "Endocrine Surgeon / Oncosurgeon",
        "urgency": "Specialist Consultation",
        "symptoms": ["Painless growing lump/nodule in front of neck", "Hoarseness of voice (Vocal cord palsy)", "Difficulty swallowing or breathing", "Swollen neck lymph nodes"],
        "medicines": ["Levothyroxine (TSH suppression therapy)", "Radioactive Iodine (RAI - I-131)", "Lenvatinib / Sorafenib"],
        "tests": ["High-Resolution Neck Ultrasound", "USG-Guided FNAC (Fine Needle Aspiration)", "Serum Thyroglobulin", "Serum Calcitonin (for Medullary)"],
        "diet": "Iodine-adjusted diet depending on radioactive iodine therapy timing."
    },
    {
        "disease_id": "CAN015", "disease_name": "Leukemia (Blood Cancer)",
        "disease_name_hi": "ब्लड कैंसर / ल्यूकेमिया (Leukemia / Blood Cancer)",
        "disease_name_gu": "બ્લડ કેન્સર / લ્યુકેમિયા (Blood Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Very High", "icd_code": "C95.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Hematologist / Hemato-Oncologist",
        "urgency": "Critical / Urgent Hemato-Oncology Hospitalization",
        "symptoms": ["Severe unexplained fatigue & pallor", "Frequent recurrent infections & fever", "Easy bruising and petechial bleeding", "Bleeding gums / nosebleeds", "Unexplained weight loss & night sweats", "Bone and joint pain", "Swollen lymph nodes and spleen (Splenomegaly)"],
        "medicines": ["Imatinib / Dasatinib (for CML)", "Cytarabine + Daunorubicin (for AML)", "Supportive blood products (Platelets/PRBC)", "Piperacillin-Tazobactam"],
        "tests": ["Complete Blood Count (CBC) with Peripheral Blood Smear (PBS)", "Bone Marrow Aspiration & Biopsy", "Flow Cytometry Immunophenotyping", "Cytogenetics (Philadelphia Chromosome / BCR-ABL PCR)"],
        "diet": "Strict neutropenic diet (well-cooked food, boiled water, strictly peel all fruits, zero raw salads)."
    },
    {
        "disease_id": "CAN016", "disease_name": "Lymphoma (Hodgkin / Non-Hodgkin)",
        "disease_name_hi": "लिम्फोमा कैंसर (Lymphoma)",
        "disease_name_gu": "લિમ્ફોમા કેન્સર (Lymphoma)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C85.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Hemato-Oncologist",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Painless enlarged lymph nodes in neck, armpit or groin", "Drenching night sweats", "Unexplained high fever (Pel-Ebstein fever)", "Unexplained weight loss (> 10% in 6 months)", "Severe generalized itching (Pruritus)"],
        "medicines": ["ABVD Regimen (for Hodgkin)", "R-CHOP Regimen (for Non-Hodgkin)", "Rituximab"],
        "tests": ["Excisional Whole Lymph Node Biopsy with Histopathology", "Whole Body PET-CT Scan", "Bone Marrow Biopsy"],
        "diet": "High protein, balanced clean wholesome diet."
    },
    {
        "disease_id": "CAN017", "disease_name": "Multiple Myeloma (Bone Marrow Plasma Cancer)",
        "disease_name_hi": "मल्टीपल मायलोमा (Multiple Myeloma)",
        "disease_name_gu": "મલ્ટીપલ માયલોમા (Multiple Myeloma)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Medium", "icd_code": "C90.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Hemato-Oncologist",
        "urgency": "Specialist Oncology Consultation",
        "symptoms": ["Persistent deep bone pain (especially spine, ribs, hips)", "Pathological bone fractures", "Unexplained kidney failure", "High blood calcium (Hypercalcemia)", "Fatigue and anemia (CRAB criteria)"],
        "medicines": ["Bortezomib (Velcade)", "Lenalidomide 10mg/25mg", "Dexamethasone", "Bisphosphonates (Zoledronic Acid)"],
        "tests": ["Serum Protein Electrophoresis (SPEP - M Band)", "Serum Free Light Chains (Kappa/Lambda)", "Bone Marrow Biopsy", "Whole Body Low-Dose CT (Skeletal Survey)"],
        "diet": "High hydration (minimum 3 liters/day to protect kidneys), avoid nephrotoxic NSAIDs."
    },
    {
        "disease_id": "CAN018", "disease_name": "Brain / CNS Tumor",
        "disease_name_hi": "ब्रेन ट्यूमर / मस्तिष्क कैंसर (Brain Tumor)",
        "disease_name_gu": "બ્રેઈન ટ્યુમર / મગજનું કેન્સર (Brain Tumor)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "High", "icd_code": "C71.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Neurosurgeon / Neuro-Oncologist",
        "urgency": "Urgent Neurosurgical Consultation",
        "symptoms": ["New onset severe morning headaches with vomiting", "New onset seizures / fits (Epileptic convulsions)", "Progressive limb weakness or paralysis on one side", "Vision loss or double vision", "Personality and memory changes"],
        "medicines": ["Dexamethasone (to reduce brain edema)", "Levetiracetam (Keppra) 500mg", "Temozolomide", "Mannitol"],
        "tests": ["Brain MRI with Contrast (Spectroscopy)", "Brain CT Scan", "Stereotactic Brain Biopsy"],
        "diet": "Anti-inflammatory, ketogenic or low glycemic index nutrition under clinical supervision."
    },
    {
        "disease_id": "CAN019", "disease_name": "Bone Cancer (Osteosarcoma / Ewing Sarcoma)",
        "disease_name_hi": "हड्डियों का कैंसर (Bone Cancer / Osteosarcoma)",
        "disease_name_gu": "હાડકાંનું કેન્સર (Bone Cancer)",
        "category": "Cancer & Oncology", "category_icon": "", "priority": "Medium", "icd_code": "C40.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Orthopaedic Oncosurgeon",
        "urgency": "Urgent Oncology Consultation",
        "symptoms": ["Persistent deep bone pain worsening at night", "Visible firm swelling/lump on bone", "Limping or difficulty bearing weight", "Pathological fracture from trivial injury"],
        "medicines": ["MAP Regimen (Methotrexate, Doxorubicin, Cisplatin)", "Ifosfamide + Etoposide", "Pain relief analgesics"],
        "tests": ["X-Ray of Affected Bone (Sunburst / Onion-skin appearance)", "MRI of Affected Limb", "Core Needle Bone Biopsy", "Chest CT (to rule out lung metastasis)"],
        "diet": "High calcium, vitamin D, and high calorie-protein diet for tissue healing."
    },

    # ================= 3. DIABETES & METABOLIC DISEASES =================
    {
        "disease_id": "MET001", "disease_name": "Type 1 Diabetes Mellitus",
        "disease_name_hi": "टाइप 1 डायबिटीज (Type 1 Diabetes)",
        "disease_name_gu": "ટાઈપ 1 ડાયાબિટીસ (Type 1 Diabetes)",
        "category": "Diabetes & Metabolic Diseases", "category_icon": "", "priority": "High", "icd_code": "E10.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Endocrinologist / Diabetologist",
        "urgency": "Urgent Clinical Attention (Risk of DKA)",
        "symptoms": ["Excessive thirst (Polydipsia)", "Frequent urination (Polyuria)", "Extreme hunger (Polyphagia)", "Rapid unexplained weight loss", "Fruity breath odor (Ketones)", "Fatigue and blurred vision"],
        "medicines": ["Insulin Glargine / Degludec (Basal)", "Insulin Aspart / Lispro (Bolus Rapid)", "Continuous Glucose Monitoring (CGM)"],
        "tests": ["Fasting Blood Sugar & PPBS", "HbA1c Glycated Hemoglobin", "C-Peptide Fasting", "Anti-GAD Antibodies", "Urine Ketones"],
        "diet": "Strict carbohydrate counting, complex low-GI carbs, structured meal timing."
    },
    {
        "disease_id": "MET002", "disease_name": "Type 2 Diabetes Mellitus",
        "disease_name_hi": "टाइप 2 डायबिटीज / मधुमेह (Type 2 Diabetes)",
        "disease_name_gu": "ટાઈપ 2 ડાયાબિટીસ (Type 2 Diabetes)",
        "category": "Diabetes & Metabolic Diseases", "category_icon": "", "priority": "Very High", "icd_code": "E11.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Diabetologist / Physician",
        "urgency": "Specialist Consultation (Ongoing Care)",
        "symptoms": ["Increased thirst & urination", "Slow healing wounds / sores", "Tingling / numbness in feet (Neuropathy)", "Frequent fungal infections", "Blurry vision", "Chronic fatigue"],
        "medicines": ["Metformin 500mg / 1000mg", "Glimepiride 1mg/2mg", "Dapagliflozin / Empagliflozin 10mg", "Teneligliptin 20mg"],
        "tests": ["Fasting Blood Glucose", "Post-Prandial Blood Glucose", "HbA1c (Target < 7.0%)", "Urine Microalbumin/Creatinine Ratio"],
        "diet": "Millets (Ragi, Jowar, Bajra), high dietary fiber, green vegetables, zero refined sugars, daily 30-min brisk walk."
    },
    {
        "disease_id": "MET003", "disease_name": "Gestational Diabetes Mellitus (GDM)",
        "disease_name_hi": "गर्भावस्था में डायबिटीज (Gestational Diabetes)",
        "disease_name_gu": "ગર્ભાવસ્થામાં ડાયાબિટીસ (GDM)",
        "category": "Diabetes & Metabolic Diseases", "category_icon": "", "priority": "High", "icd_code": "O24.4",
        "communicable": False, "outbreak_prone": False, "specialist": "Obstetrician & Endocrinologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["High blood sugar detected during pregnancy screening", "Excessive thirst", "Frequent urination", "Excessive fetal growth on ultrasound"],
        "medicines": ["Human Insulin (Regular/NPH)", "Metformin (under specialist guidance)"],
        "tests": ["Oral Glucose Tolerance Test (OGTT 75g)", "Fasting and Post-Meal Blood Glucose", "Obstetric Ultrasound (Fetal Wellbeing)"],
        "diet": "Balanced low-GI maternal meal plan divided into 3 main meals and 3 healthy snacks."
    },
    {
        "disease_id": "MET005", "disease_name": "Obesity & Metabolic Syndrome",
        "disease_name_hi": "मोटापा और मेटाबोलिक सिंड्रोम (Obesity & Metabolic Syndrome)",
        "disease_name_gu": "સ્થૂળતા અને મેટાબોલિક સિન્ડ્રોમ (Obesity)",
        "category": "Diabetes & Metabolic Diseases", "category_icon": "", "priority": "High", "icd_code": "E66.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Bariatric / Metabolic Physician",
        "urgency": "Lifestyle & Clinical Consultation",
        "symptoms": ["Excessive visceral abdominal fat", "BMI >= 25 kg/m2 (Asian Indian criteria)", "Breathlessness with minor activity", "Joint pain in knees/back", "Snoring and daytime sleepiness"],
        "medicines": ["Semaglutide / Tirzepatide (under prescription)", "Orlistat 120mg"],
        "tests": ["Lipid Profile", "Fasting Glucose & Insulin Resistance (HOMA-IR)", "Liver Function Test", "Thyroid Profile (TSH)"],
        "diet": "Caloric deficit diet (-500 kcal/day), high protein, intermittent fasting, structured strength & aerobic training."
    },
    {
        "disease_id": "MET007", "disease_name": "Non-Alcoholic Fatty Liver Disease (NAFLD / MASLD)",
        "disease_name_hi": "फैटी लिवर रोग (Fatty Liver Disease)",
        "disease_name_gu": "ફેટી લિવર રોગ (NAFLD)",
        "category": "Diabetes & Metabolic Diseases", "category_icon": "", "priority": "High", "icd_code": "K76.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Gastroenterologist / Hepatologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Mild right upper abdomen discomfort", "General fatigue", "Abdominal bloating", "Metabolic syndrome features"],
        "medicines": ["Saroglitazar 4mg", "Vitamin E 400IU", "Ursodeoxycholic Acid (UDCA) 300mg"],
        "tests": ["Liver Function Test (SGOT/SGPT)", "Abdominal Ultrasound", "FibroScan (Transient Elastography)", "Lipid Profile"],
        "diet": "Target 7-10% weight reduction, Mediterranean diet, eliminate all sugary beverages, fructose, and fried snacks."
    },
    {
        "disease_id": "MET008", "disease_name": "Dyslipidemia & Hypercholesterolemia",
        "disease_name_hi": "हाई कोलेस्ट्रॉल / डिस्लिपिडेमिया (High Cholesterol)",
        "disease_name_gu": "હાઈ કોલેસ્ટ્રોલ (Dyslipidemia)",
        "category": "Diabetes & Metabolic Diseases", "category_icon": "", "priority": "High", "icd_code": "E78.5",
        "communicable": False, "outbreak_prone": False, "specialist": "Physician / Cardiologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Asymptomatic in early stages", "Yellowish fatty deposits around eyes (Xanthelasma)", "Chest pain on exertion (if advanced atherosclerosis)"],
        "medicines": ["Atorvastatin 10mg/20mg", "Rosuvastatin 10mg", "Ezetimibe 10mg", "Fenofibrate (for high triglycerides)"],
        "tests": ["Fasting Lipid Profile (Total Cholesterol, LDL, HDL, Triglycerides)", "ApoB / Lipoprotein(a)"],
        "diet": "Zero trans fats, rich in soluble fiber (psyllium husk, oats, legumes), walnuts, flaxseeds, olive/mustard oil."
    },

    # ================= 4. RESPIRATORY DISEASES =================
    {
        "disease_id": "RES001", "disease_name": "Chronic Obstructive Pulmonary Disease (COPD)",
        "disease_name_hi": "सीओपीडी / क्रॉनिक ऑब्सट्रक्टिव पल्मोनरी डिजीज (COPD)",
        "disease_name_gu": "સીઓપીડી (COPD)",
        "category": "Respiratory Diseases", "category_icon": "", "priority": "Very High", "icd_code": "J44.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Pulmonologist / Chest Physician",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Chronic progressive shortness of breath", "Chronic morning cough with mucus", "Wheezing and chest tightness", "Frequent respiratory infections", "Low blood oxygen levels"],
        "medicines": ["Tiotropium Inhaler (LAMA)", "Formoterol + Budesonide Inhaler", "Salbutamol MDI (SOS Rescue)", "Home Oxygen Therapy"],
        "tests": ["Spirometry / Pulmonary Function Test (PFT with Reversibility)", "Chest X-Ray / HRCT", "Arterial Blood Gas (ABG)", "Pulse Oximetry"],
        "diet": "Small frequent high-protein meals; stay well hydrated to thin mucus; avoid indoor smoke/chulha."
    },
    {
        "disease_id": "RES002", "disease_name": "Bronchial Asthma",
        "disease_name_hi": "अस्थमा / दमा (Asthma)",
        "disease_name_gu": "અસ્થમા / દમ (Asthma)",
        "category": "Respiratory Diseases", "category_icon": "", "priority": "Very High", "icd_code": "J45.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Pulmonologist / Allergist",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Recurrent wheezing", "Breathlessness triggered by cold/dust/pollen", "Nighttime or early morning cough", "Chest tightness"],
        "medicines": ["Budesonide + Formoterol Inhaler (Foracort)", "Levosalbutamol Inhaler (Asthalin SOS)", "Montelukast 10mg"],
        "tests": ["Spirometry with Bronchodilator Challenge", "Fractional Exhaled Nitric Oxide (FeNO)", "Total Serum IgE & Absolute Eosinophil Count (AEC)"],
        "diet": "Avoid cold foods/beverages, keep home dust-free, practice pranayama/breathing exercises."
    },
    {
        "disease_id": "RES003", "disease_name": "Pneumonia (Bacterial / Viral)",
        "disease_name_hi": "निमोनिया (Pneumonia)",
        "disease_name_gu": "ન્યુમોનિયા (Pneumonia)",
        "category": "Respiratory Diseases", "category_icon": "", "priority": "Very High", "icd_code": "J18.9",
        "communicable": True, "outbreak_prone": False, "specialist": "Pulmonologist / General Physician",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["High fever with shaking chills", "Cough with yellow/green phlegm", "Sharp chest pain on breathing (Pleuritic)", "Rapid shallow breathing", "Extreme fatigue and low SpO2"],
        "medicines": ["Amoxicillin + Clavulanate (Augmentin) 625mg", "Azithromycin 500mg", "Ceftriaxone IV", "Paracetamol 650mg"],
        "tests": ["Chest X-Ray PA View", "Complete Blood Count (Leukocytosis)", "Sputum Culture & Sensitivity", "Serum CRP / Procalcitonin"],
        "diet": "Warm fluids, ginger-tulsi tea, high-calorie soups, plenty of hydration and steam."
    },
    {
        "disease_id": "RES004", "disease_name": "Tuberculosis (Pulmonary TB)",
        "disease_name_hi": "तपेदिक / टीबी (Tuberculosis)",
        "disease_name_gu": "ક્ષય રોગ / ટીબી (Tuberculosis)",
        "category": "Respiratory Diseases", "category_icon": "", "priority": "Very High", "icd_code": "A15.0",
        "communicable": True, "outbreak_prone": False, "specialist": "NTEP Chest Physician / Pulmonologist",
        "urgency": "Urgent Clinical Attention (NTEP Mandatory Reporting)",
        "symptoms": ["Cough lasting more than 2 weeks", "Coughing up blood (Hemoptysis)", "Low-grade evening fever", "Profuse night sweats", "Unexplained severe weight loss and loss of appetite"],
        "medicines": ["NTEP 4-Drug FDC (Rifampicin, Isoniazid, Pyrazinamide, Ethambutol)", "Pyridoxine (Vitamin B6) 10mg"],
        "tests": ["CBNAAT / GeneXpert Sputum Test", "Sputum AFB Smear Microscopy", "Chest X-Ray PA View", "Mantoux / IGRA Test"],
        "diet": "High protein nutritional support (Nikshay Poshan Yojana), milk, eggs, pulses, soya and bananas."
    },
    {
        "disease_id": "RES007", "disease_name": "Pulmonary Fibrosis / ILD",
        "disease_name_hi": "पल्मोनरी फाइब्रोसिस (Pulmonary Fibrosis)",
        "disease_name_gu": "પલ્મોનરી ફાઈબ્રોસિસ (Pulmonary Fibrosis)",
        "category": "Respiratory Diseases", "category_icon": "", "priority": "Medium", "icd_code": "J84.1",
        "communicable": False, "outbreak_prone": False, "specialist": "Pulmonologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Progressive dry hacking cough", "Severe breathlessness with minor activity", "Velcro-like crackles in lungs", "Clubbing of fingernails"],
        "medicines": ["Pirfenidone 200mg/800mg", "Nintedanib 100mg/150mg", "N-Acetylcysteine (NAC) 600mg", "Supplemental Oxygen"],
        "tests": ["High-Resolution CT (HRCT) Chest", "Diffusion Capacity of Lungs (DLCO)", "6-Minute Walk Test (6MWT)"],
        "diet": "Nutritious easily digestible food, pulmonary rehabilitation exercises, avoid air pollution."
    },

    # ================= 5. INFECTIOUS & VECTOR-BORNE DISEASES =================
    {
        "disease_id": "INF001", "disease_name": "HIV / AIDS",
        "disease_name_hi": "एचआईवी / एड्स (HIV / AIDS)",
        "disease_name_gu": "એચઆઈવી / એઇડ્સ (HIV / AIDS)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "Very High", "icd_code": "B24",
        "communicable": True, "outbreak_prone": False, "specialist": "NACO ART Specialist / Infectious Diseases",
        "urgency": "Specialist Consultation (ART Center)",
        "symptoms": ["Prolonged unexplained fever (> 1 month)", "Chronic diarrhea (> 1 month)", "Significant weight loss (Wasting syndrome)", "Recurrent oral thrush (Fungal candidiasis)", "Swollen lymph nodes"],
        "medicines": ["NACO First-Line ART (Tenofovir + Lamivudine + Dolutegravir - TLD Single Tablet)", "Cotrimoxazole (Septran) Prophylaxis"],
        "tests": ["Rapid HIV 1 & 2 Antibody Screening", "CD4 Count", "HIV Viral Load (RT-PCR)"],
        "diet": "Clean hygienic nutrition, well-cooked meals, boiled water, multivitamin support."
    },
    {
        "disease_id": "INF003", "disease_name": "Dengue Fever / Severe Dengue",
        "disease_name_hi": "डेंगू बुखार (Dengue Fever)",
        "disease_name_gu": "ડેન્ગ્યુ તાવ (Dengue Fever)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "Very High", "icd_code": "A90",
        "communicable": True, "outbreak_prone": True, "specialist": "Infectious Disease Specialist / Physician",
        "urgency": "Urgent Clinical Monitoring (Risk of Plasma Leak)",
        "symptoms": ["Sudden high fever (104°F)", "Severe retro-orbital eye pain", "Severe joint and muscle pain (Breakbone fever)", "Skin rash", "Bleeding from gums/nose", "Severe abdominal pain and persistent vomiting"],
        "medicines": ["Paracetamol 650mg ONLY (Strictly AVOID Aspirin/Ibuprofen/NSAIDs)", "Oral Rehydration Salts (ORS)", "IV Ringer Lactate fluids"],
        "tests": ["Dengue NS1 Antigen (Day 1-5)", "Dengue IgM/IgG Antibody (Day 5+)", "Daily Complete Blood Count (CBC for Platelets & Hematocrit)"],
        "diet": "Extensive oral fluids (coconut water, ORS, fresh fruit juices, pomegranate), light khichdi."
    },
    {
        "disease_id": "INF004", "disease_name": "Malaria (P. vivax / P. falciparum)",
        "disease_name_hi": "मलेरिया बुखार (Malaria)",
        "disease_name_gu": "મેલેરિયા તાવ (Malaria)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "Very High", "icd_code": "B54",
        "communicable": True, "outbreak_prone": True, "specialist": "Physician",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["High fever with intense shivering chills (Rigor)", "Profuse sweating as fever drops", "Severe headache and body ache", "Nausea and vomiting", "Anemia and mild jaundice"],
        "medicines": ["Artemether + Lumefantrine (ACT for Falciparum)", "Chloroquine + Primaquine 14-day radical cure (for Vivax)"],
        "tests": ["Rapid Diagnostic Test (RDT) Malaria Pf/Pv Antigen", "Thick and Thin Blood Smear Giemsa Microscopy", "CBC"],
        "diet": "Adequate fluids, glucose water, high carbohydrate soft diet."
    },
    {
        "disease_id": "INF005", "disease_name": "Typhoid / Enteric Fever",
        "disease_name_hi": "टाइफाइड / मियादी बुखार (Typhoid Fever)",
        "disease_name_gu": "ટાઈફોઈડ તાવ (Typhoid)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "High", "icd_code": "A01.0",
        "communicable": True, "outbreak_prone": True, "specialist": "General Physician",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Step-ladder rising persistent high fever", "Severe headache and weakness", "Stomach pain and constipation/diarrhea", "Coated tongue", "Loss of appetite and rose spots"],
        "medicines": ["Azithromycin 500mg (Oral) OR Ceftriaxone 1g/2g IV", "Paracetamol 650mg", "Probiotics"],
        "tests": ["Blood Culture (Gold standard in 1st week)", "Widal Test (after Day 7-10)", "TyphiDot IgM", "Stool Culture"],
        "diet": "Strict boiled water, soft bland diet (boiled rice, curd, boiled potatoes, soups); avoid spicy and raw food."
    },
    {
        "disease_id": "INF006", "disease_name": "Cholera & Acute Watery Diarrhea",
        "disease_name_hi": "हैजा / कॉलरा (Cholera)",
        "disease_name_gu": "કોલેરા (Cholera)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "High", "icd_code": "A00.9",
        "communicable": True, "outbreak_prone": True, "specialist": "Emergency Physician / Infectious Diseases",
        "urgency": "Critical / Emergency Immediate Hospitalization",
        "symptoms": ["Profuse painless watery 'rice-water' stools", "Rapid severe dehydration", "Sunken eyes, dry mouth, skin tenting", "Muscle cramps in legs", "Rapid weak pulse and low BP"],
        "medicines": ["Aggressive WHO-ORS Solution", "IV Ringer Lactate / Normal Saline", "Doxycycline 300mg single dose OR Azithromycin 1g", "Zinc Sulfate 20mg"],
        "tests": ["Stool Hanging Drop Microscopy (Darting motility)", "Stool Culture on TCBS Agar", "Serum Electrolytes & Renal Function"],
        "diet": "Continuous oral rehydration with WHO ORS, electrolyte fluids; boiled safe drinking water."
    },
    {
        "disease_id": "INF007", "disease_name": "Chikungunya Fever",
        "disease_name_hi": "चिकनगुनिया बुखार (Chikungunya)",
        "disease_name_gu": "ચિકનગુનિયા તાવ (Chikungunya)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "High", "icd_code": "A92.0",
        "communicable": True, "outbreak_prone": True, "specialist": "Physician / Rheumatologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Sudden onset high fever", "Severe crippling polyarthralgia / joint pain (wrists, ankles, knees)", "Joint swelling", "Maculopapular skin rash", "Nausea and fatigue"],
        "medicines": ["Paracetamol 650mg", "NSAIDs (once Dengue excluded)", "Hydrochloroquine (for chronic arthritis)"],
        "tests": ["Chikungunya IgM ELISA", "RT-PCR (within first 5 days)", "CBC and CRP"],
        "diet": "Anti-inflammatory diet (turmeric milk, ginger, omega-3, adequate hydration), gentle joint mobilization."
    },
    {
        "disease_id": "INF014", "disease_name": "Hepatitis B (Viral Hepatitis)",
        "disease_name_hi": "हेपेटाइटिस बी (Hepatitis B)",
        "disease_name_gu": "હેપેટાઇટિસ બી (Hepatitis B)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "Very High", "icd_code": "B16.9",
        "communicable": True, "outbreak_prone": False, "specialist": "Hepatologist / Gastroenterologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Yellow skin and eyes (Jaundice)", "Dark tea-colored urine", "Pale clay-colored stools", "Severe fatigue and nausea", "Loss of appetite and right upper belly pain"],
        "medicines": ["Tenofovir Disoproxil (TDF) 300mg / Entecavir 0.5mg", "Hepatoprotective agents"],
        "tests": ["HBsAg (Surface Antigen)", "HBV DNA Quantitative PCR (Viral Load)", "HBeAg / Anti-HBe", "Liver Function Test & FibroScan"],
        "diet": "High carbohydrate, low fat, adequate protein, strictly zero alcohol."
    },
    {
        "disease_id": "INF015", "disease_name": "Hepatitis C (Viral Hepatitis)",
        "disease_name_hi": "हेपेटाइटिस सी (Hepatitis C)",
        "disease_name_gu": "હેપેટાઇટિસ સી (Hepatitis C)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "Very High", "icd_code": "B18.2",
        "communicable": True, "outbreak_prone": False, "specialist": "Hepatologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Chronic fatigue", "Mild jaundice", "Joint and muscle aches", "Fluid accumulation in belly (if cirrhotic)"],
        "medicines": ["Sofosbuvir 400mg + Velpatasvir 100mg (12-week curative DAA regimen)", "Ledipasvir (for Genotype 1)"],
        "tests": ["Anti-HCV Antibody ELISA", "HCV RNA Quantitative RT-PCR", "HCV Genotype", "LFT"],
        "diet": "Healthy balanced diet, zero alcohol, avoid untested herbal supplements."
    },
    {
        "disease_id": "INF017", "disease_name": "Japanese Encephalitis (JE)",
        "disease_name_hi": "जापानी एन्सेफलाइटिस / दिमागी बुखार (Japanese Encephalitis)",
        "disease_name_gu": "જાપાનીઝ એન્સેફાલીટીસ (JE)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "High", "icd_code": "A83.0",
        "communicable": True, "outbreak_prone": True, "specialist": "Neurologist / Pediatric Intensivist",
        "urgency": "Critical / Emergency Immediate Hospitalization",
        "symptoms": ["Sudden high fever and intense headache", "Neck stiffness and confusion", "Seizures / convulsions", "Altered sensorium and coma", "Spastic paralysis"],
        "medicines": ["Intensive ICU supportive management", "Mannitol (to reduce cerebral edema)", "Anti-epileptics (Levetiracetam/Phenytoin)", "IV Fluids & airway protection"],
        "tests": ["JE-specific IgM Capture ELISA (CSF & Serum)", "Lumbar Puncture (CSF Analysis)", "Brain MRI"],
        "diet": "Strict ICU tube feeding / total parenteral nutrition as indicated."
    },
    {
        "disease_id": "INF020", "disease_name": "Kala-azar (Visceral Leishmaniasis)",
        "disease_name_hi": "काला-अज़ार / लिशमैनियासिस (Kala-azar)",
        "disease_name_gu": "કાલા-અઝાર (Kala-azar)",
        "category": "Infectious & Vector-Borne", "category_icon": "", "priority": "High", "icd_code": "B55.0",
        "communicable": True, "outbreak_prone": True, "specialist": "Infectious Disease Specialist / Physician",
        "urgency": "Urgent Clinical Attention (National Programme)",
        "symptoms": ["Prolonged persistent fever with double daily rise", "Massive enlargement of spleen (Splenomegaly) and liver", "Darkening/pigmentation of facial skin (Kala-azar)", "Severe anemia and weight loss (Wasting)"],
        "medicines": ["Liposomal Amphotericin B (Single dose 10mg/kg IV - First line NVBDCP)", "Miltefosine 50mg"],
        "tests": ["rK39 Rapid Immunochromatographic Dipstick Test", "Bone Marrow / Splenic Aspiration (LD Bodies)", "Complete Blood Count (Pancytopenia)"],
        "diet": "High protein high calorie nutrition, iron and micronutrient supplementation."
    },

    # ================= 6. KIDNEY & RENAL DISEASES =================
    {
        "disease_id": "REN001", "disease_name": "Chronic Kidney Disease (CKD)",
        "disease_name_hi": "क्रॉनिक किडनी रोग (Chronic Kidney Disease)",
        "disease_name_gu": "ક્રોનિક કિડની ડિસીઝ (CKD)",
        "category": "Kidney & Renal Diseases", "category_icon": "", "priority": "Very High", "icd_code": "N18.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Nephrologist",
        "urgency": "Specialist Consultation (Renal Management)",
        "symptoms": ["Swelling around eyes (Periorbital edema) and feet", "Decreased or foamy urine output", "Chronic fatigue and pallor (Anemia)", "Loss of appetite, metallic taste, nausea", "High uncontrolled blood pressure", "Persistent itchy skin (Uremic pruritus)"],
        "medicines": ["Erythropoietin (EPO) injections", "Iron sucrose IV", "Sodium Bicarbonate", "Calcium Acetate / Sevelamer", "Telmisartan / Dapagliflozin (in early stages)"],
        "tests": ["Serum Creatinine & Blood Urea Nitrogen (BUN)", "Estimated GFR (eGFR)", "Urine Albumin-to-Creatinine Ratio (UACR)", "Ultrasound Kidneys & Bladder (KUB)"],
        "diet": "Strict low sodium, restricted protein (0.6-0.8g/kg), low potassium (avoid coconut water, banana, citrus), restricted phosphorus."
    },
    {
        "disease_id": "REN003", "disease_name": "End-Stage Renal Disease (Kidney Failure)",
        "disease_name_hi": "किडनी फेलियर / अंतिम चरण गुर्दे की बीमारी (Kidney Failure)",
        "disease_name_gu": "કિડની ફેલિયર (Kidney Failure)",
        "category": "Kidney & Renal Diseases", "category_icon": "", "priority": "Very High", "icd_code": "N18.6",
        "communicable": False, "outbreak_prone": False, "specialist": "Nephrologist / Dialysis Unit",
        "urgency": "Critical / Urgent Dialysis Evaluation",
        "symptoms": ["Severe breathlessness (Fluid overload / pulmonary edema)", "Marked oliguria/anuria (near zero urine)", "Drowsiness, confusion, uremic encephalopathy", "Severe intractable nausea and vomiting", "Refractory high blood pressure"],
        "medicines": ["Hemodialysis / Peritoneal Dialysis", "Diuretics (High dose loop diuretics)", "Potassium binding resins (K-Bind)", "Emergency Calcium Gluconate (if hyperkalemia)"],
        "tests": ["Serum Electrolytes (Potassium - Urgent)", "Arterial Blood Gas (ABG - Acidosis)", "Serum Creatinine & Urea", "ECG (Tall T waves)"],
        "diet": "Strict fluid limit (< 1 liter total per 24 hours including all liquids), strict renal dialysis nutritional protocol."
    },
    {
        "disease_id": "REN005", "disease_name": "Kidney Stones (Nephrolithiasis / Renal Calculi)",
        "disease_name_hi": "किडनी की पथरी / गुर्दे की पथरी (Kidney Stones)",
        "disease_name_gu": "કિડનીની પથરી (Kidney Stones)",
        "category": "Kidney & Renal Diseases", "category_icon": "", "priority": "High", "icd_code": "N20.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Urologist",
        "urgency": "Urgent Clinical Attention (if severe obstruction)",
        "symptoms": ["Severe sharp cramping pain in back and side (Renal colic)", "Pain radiating to lower belly and groin", "Blood in urine (Pink/red/brown urine)", "Burning urination and frequent urge to urinate", "Nausea and vomiting with pain"],
        "medicines": ["Tamsulosin 0.4mg (Alpha blocker for stone expulsion)", "Potassium Citrate solution", "Drotaverine + Aceclofenac (Pain relief)", "Tramadol SOS"],
        "tests": ["Non-Contrast CT KUB (Gold standard)", "Ultrasound KUB", "Urine Routine & Microscopy", "Serum Calcium & Uric Acid"],
        "diet": "High water intake (> 3 liters/day), lemon water (citrate), reduce animal protein, avoid high oxalate foods (spinach, chocolate, nuts)."
    },

    # ================= 7. NEUROLOGICAL DISEASES =================
    {
        "disease_id": "NEU001", "disease_name": "Epilepsy & Seizure Disorders",
        "disease_name_hi": "मिर्गी / दौरे का रोग (Epilepsy)",
        "disease_name_gu": "વાઈ / ખેંચ / એપીલેપ્સી (Epilepsy)",
        "category": "Neurological Diseases", "category_icon": "", "priority": "High", "icd_code": "G40.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Neurologist",
        "urgency": "Urgent Clinical Attention (Emergency if Status Epilepticus)",
        "symptoms": ["Uncontrollable jerking movements of arms and legs", "Temporary loss of consciousness", "Staring spells / blank staring", "Tongue biting and urinary incontinence during seizure", "Post-ictal confusion and sleepiness"],
        "medicines": ["Levetiracetam 500mg", "Sodium Valproate 300mg/500mg", "Carbamazepine 200mg", "Midazolam Nasal Spray (Emergency rescue)"],
        "tests": ["Electroencephalogram (EEG / Video EEG)", "Brain MRI Epilepsy Protocol", "Serum Calcium, Sodium, Blood Glucose"],
        "diet": "Consistent meal and sleep schedule, ketogenic diet (in refractory childhood epilepsy), avoid flickering lights and sleep deprivation."
    },
    {
        "disease_id": "NEU002", "disease_name": "Alzheimer's Disease & Dementia",
        "disease_name_hi": "अल्जाइमर रोग और डिमेंशिया (Alzheimer's Disease)",
        "disease_name_gu": "અલ્ઝાઇમર રોગ અને ડિમેન્શિયા (Dementia)",
        "category": "Neurological Diseases", "category_icon": "", "priority": "High", "icd_code": "G30.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Cognitive Neurologist / Geriatrician",
        "urgency": "Specialist Consultation",
        "symptoms": ["Progressive short-term memory loss (forgetting recent events)", "Getting lost in familiar places / wandering", "Difficulty performing daily familiar tasks", "Language problems (struggling for words)", "Mood swings and disorientation"],
        "medicines": ["Donepezil 5mg/10mg (Cholinesterase inhibitor)", "Memantine 10mg/20mg", "Rivastigmine Transdermal Patch"],
        "tests": ["Mini-Mental State Examination (MMSE / MoCA)", "Brain MRI (Hippocampal Volume / Atrophy)", "Serum Vitamin B12, TSH, Folate"],
        "diet": "MIND diet (Mediterranean-DASH intervention for neurodegenerative delay), berries, green leafy vegetables, cognitive puzzles."
    },
    {
        "disease_id": "NEU004", "disease_name": "Parkinson's Disease",
        "disease_name_hi": "पार्किंसंस रोग (Parkinson's Disease)",
        "disease_name_gu": "પાર્કિન્સન્સ રોગ (Parkinson's)",
        "category": "Neurological Diseases", "category_icon": "", "priority": "High", "icd_code": "G20",
        "communicable": False, "outbreak_prone": False, "specialist": "Movement Disorder Neurologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Resting tremor (Pill-rolling tremor in hands)", "Muscle rigidity and stiffness", "Slowness of movement (Bradykinesia)", "Shuffling gait with loss of balance", "Soft monotone voice and masked face"],
        "medicines": ["Levodopa + Carbidopa (Syndopa) 110mg/275mg", "Pramipexole 0.5mg", "Rasagiline 1mg", "Trihexyphenidyl 2mg"],
        "tests": ["Clinical Neurological Examination", "Brain MRI (to rule out secondary parkinsonism)", "DaTscan (where available)"],
        "diet": "High fiber diet (to prevent constipation), separate protein intake from Levodopa dosing by 1 hour, daily physical balance therapy."
    },
    {
        "disease_id": "NEU005", "disease_name": "Migraine Headache Disorder",
        "disease_name_hi": "माइग्रेन / आधासीसी का दर्द (Migraine)",
        "disease_name_gu": "આધાશીશી / માઇગ્રેન (Migraine)",
        "category": "Neurological Diseases", "category_icon": "", "priority": "High", "icd_code": "G43.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Neurologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Intense throbbing pulsing headache on one side", "Sensitivity to light (Photophobia) and sound (Phonophobia)", "Nausea and vomiting with headache", "Visual aura (Flashing lights or blind spots before pain)", "Pain aggravated by physical activity"],
        "medicines": ["Sumatriptan 50mg/100mg (Acute abortive)", "Naproxen 500mg", "Propranolol 40mg / Topiramate 25mg (Prophylaxis)", "Domperidone (Anti-emetic)"],
        "tests": ["Clinical Diagnosis according to ICHD-3 criteria", "Brain MRI (if red flags or atypical features)"],
        "diet": "Maintain regular sleep and meals, identify triggers (aged cheese, MSG, chocolate, caffeine withdrawal), magnesium-rich foods."
    },

    # ================= 8. BLOOD DISORDERS =================
    {
        "disease_id": "BLO001", "disease_name": "Iron Deficiency Anemia",
        "disease_name_hi": "एनीमिया / खून की कमी (Iron Deficiency Anemia)",
        "disease_name_gu": "એનિમિયા / લોહીની ઉણપ (Anemia)",
        "category": "Blood Disorders", "category_icon": "", "priority": "Very High", "icd_code": "D50.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Physician / Hematologist",
        "urgency": "Moderate Attention",
        "symptoms": ["Extreme fatigue and weakness", "Pale skin, tongue and conjunctiva", "Shortness of breath on mild exertion", "Brittle nails / spoon nails (Koilonychia)", "Cravings for non-food items like chalk/ice (Pica)"],
        "medicines": ["Ferrous Ascorbate + Folic Acid Tablets", "Injectable Ferric Carboxymaltose (FCM) IV", "Vitamin C (to enhance absorption)"],
        "tests": ["Complete Blood Count (Hemoglobin & MCV)", "Serum Ferritin", "Total Iron Binding Capacity (TIBC)", "Peripheral Smear (Microcytic Hypochromic)"],
        "diet": "Jaggery (Gur), pomegranate, spinach, beetroot, chickpeas, dates, green leafy vegetables, amla."
    },
    {
        "disease_id": "BLO003", "disease_name": "Sickle Cell Disease",
        "disease_name_hi": "सिकल सेल एनीमिया (Sickle Cell Disease)",
        "disease_name_gu": "સિકલ સેલ એનિમિયા (Sickle Cell)",
        "category": "Blood Disorders", "category_icon": "", "priority": "Very High", "icd_code": "D57.1",
        "communicable": False, "outbreak_prone": False, "specialist": "Hematologist",
        "urgency": "Urgent Clinical Attention (Crisis Care)",
        "symptoms": ["Severe episodes of bone and chest pain (Vaso-occlusive crisis)", "Chronic fatigue and jaundice", "Swelling in hands and feet (Dactylitis)", "Frequent infections", "Delayed growth"],
        "medicines": ["Hydroxyurea 500mg", "Folic Acid 5mg daily", "Analgesics (Tramadol/Paracetamol for crisis)", "Pneumococcal Vaccination"],
        "tests": ["Hemoglobin Electrophoresis (HPLC)", "Sickling Solubility Test", "CBC with Reticulocyte Count"],
        "diet": "High hydration (minimum 3-4 liters water daily), folic acid-rich foods, strictly avoid extreme cold, dehydration, and high altitudes."
    },
    {
        "disease_id": "BLO004", "disease_name": "Thalassemia Major / Intermedia",
        "disease_name_hi": "थैलेसीमिया (Thalassemia Major)",
        "disease_name_gu": "થેલેસેમિયા (Thalassemia)",
        "category": "Blood Disorders", "category_icon": "", "priority": "High", "icd_code": "D56.1",
        "communicable": False, "outbreak_prone": False, "specialist": "Hematologist / Transfusion Medicine",
        "urgency": "Specialist Consultation (Regular Transfusions)",
        "symptoms": ["Severe pallor and fatigue appearing in early infancy", "Enlarged spleen and liver (Hepatosplenomegaly)", "Chipmunk facies (Prominent facial bones)", "Dark urine and slow growth"],
        "medicines": ["Regular Leucodepleted Packed Red Blood Cell Transfusions", "Iron Chelators (Deferasirox / Deferiprone)", "Folic Acid"],
        "tests": ["Hemoglobin HPLC (HbA2 & HbF quantification)", "Serum Ferritin (Iron Overload Monitoring)", "Genetic Mutation Analysis"],
        "diet": "Strict low iron diet (avoid iron-rich tonics, red meat, iron-fortified cereals), high antioxidant nutrition, regular iron chelation."
    },

    # ================= 9. LIVER & DIGESTIVE DISEASES =================
    {
        "disease_id": "LIV002", "disease_name": "Liver Cirrhosis & Chronic Liver Failure",
        "disease_name_hi": "लिवर सिरोसिस / लिवर की बीमारी (Liver Cirrhosis)",
        "disease_name_gu": "લિવર સિરોસિસ (Liver Cirrhosis)",
        "category": "Liver & Digestive Diseases", "category_icon": "", "priority": "High", "icd_code": "K74.6",
        "communicable": False, "outbreak_prone": False, "specialist": "Gastroenterologist / Hepatologist",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Severe yellowing of eyes and skin (Jaundice)", "Swelling of abdomen (Ascites)", "Vomiting blood (Esophageal variceal bleeding)", "Confusion and altered sleep cycle (Hepatic encephalopathy)", "Easy bruising and bleeding"],
        "medicines": ["Lactulose Syrup (to clear ammonia)", "Rifaximin 550mg", "Spironolactone + Furosemide", "Propranolol 20mg (to prevent variceal bleeding)"],
        "tests": ["Liver Function Test (Bilirubin, Albumin, SGOT/SGPT)", "Prothrombin Time / INR (Coagulation)", "Upper GI Endoscopy", "Abdominal Ultrasound / CT"],
        "diet": "Strict zero alcohol, restricted sodium (< 2g/day), adequate high-quality plant/dairy protein, frequent small meals."
    },
    {
        "disease_id": "LIV008", "disease_name": "Peptic Ulcer Disease & Acid Peptic Disorders",
        "disease_name_hi": "पेट का अल्सर / पेप्टिक अल्सर (Peptic Ulcer)",
        "disease_name_gu": "જઠરનું અલ્સર (Peptic Ulcer)",
        "category": "Liver & Digestive Diseases", "category_icon": "", "priority": "Medium", "icd_code": "K27.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Gastroenterologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Burning stomach pain between meals or at night", "Feeling of fullness, bloating or belching", "Heartburn and acid reflux", "Nausea and intolerance to fatty foods"],
        "medicines": ["Pantoprazole / Rabeprazole 40mg (PPIs)", "Sucralfate Suspension 1g", "H. pylori Kit (Clarithromycin + Amoxicillin + PPI)"],
        "tests": ["Upper GI Endoscopy (EGD)", "H. pylori Stool Antigen / UBT", "Complete Blood Count (to rule out occult bleeding)"],
        "diet": "Avoid spicy, deeply fried and acidic foods, eliminate NSAIDs/painkillers, avoid tobacco and alcohol."
    },
    {
        "disease_id": "LIV009", "disease_name": "Inflammatory Bowel Disease (Ulcerative Colitis / Crohn's)",
        "disease_name_hi": "सूजन आंत्र रोग / अल्सरेटिव कोलाइटिस (IBD)",
        "disease_name_gu": "આંતરડાનો સોજો / આઈબીડી (IBD)",
        "category": "Liver & Digestive Diseases", "category_icon": "", "priority": "Medium", "icd_code": "K51.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Gastroenterologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Chronic bloody diarrhea with mucus", "Severe abdominal cramps and pain", "Urgent need to defecate (Tenesmus)", "Weight loss and chronic fatigue", "Fever and joint pains"],
        "medicines": ["Mesalamine (5-ASA) 1.2g/2.4g", "Corticosteroids (Prednisolone for flares)", "Azathioprine", "Biologics (Infliximab / Vedolizumab)"],
        "tests": ["Full Colonoscopy with Mucosal Biopsy", "Fecal Calprotectin Test", "CT / MRI Enterography", "CBC, CRP, ESR"],
        "diet": "Low FODMAP, low residue diet during active flare-ups; maintain adequate hydration and nutrient supplementation."
    },

    # ================= 10. MENTAL HEALTH =================
    {
        "disease_id": "MEN001", "disease_name": "Major Depressive Disorder (Clinical Depression)",
        "disease_name_hi": "डिप्रेशन / गहरा अवसाद (Major Depression)",
        "disease_name_gu": "ડિપ્રેશન / હતાશા (Clinical Depression)",
        "category": "Mental Health", "category_icon": "", "priority": "Very High", "icd_code": "F32.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Psychiatrist / Clinical Psychologist",
        "urgency": "Urgent Psychiatric Attention (Critical if Suicidal Ideation)",
        "symptoms": ["Persistent sadness, emptiness or hopelessness (> 2 weeks)", "Loss of interest or pleasure in all activities (Anhedonia)", "Insomnia or excessive sleeping", "Severe fatigue and low energy", "Feelings of worthlessness or guilt", "Difficulty concentrating and recurrent suicidal thoughts"],
        "medicines": ["Escitalopram 10mg/20mg (SSRI)", "Sertraline 50mg", "Duloxetine 30mg", "Cognitive Behavioral Therapy (CBT)"],
        "tests": ["PHQ-9 Depression Severity Questionnaire", "Thyroid Profile (TSH - to rule out hypothyroidism)", "Serum Vitamin D & B12"],
        "diet": "Nutrient-dense brain-healthy diet (omega-3 fatty acids, walnuts, seeds, bananas), regular exercise, supportive psychotherapy."
    },
    {
        "disease_id": "MEN002", "disease_name": "Generalized Anxiety Disorder (GAD) & Panic Disorder",
        "disease_name_hi": "चिंता विकार और पैनिक अटैक (Anxiety & Panic Disorder)",
        "disease_name_gu": "ચિંતા રોગ અને ગભરાટ (Anxiety Disorder)",
        "category": "Mental Health", "category_icon": "", "priority": "Very High", "icd_code": "F41.1",
        "communicable": False, "outbreak_prone": False, "specialist": "Psychiatrist / Psychologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Excessive persistent worry difficult to control", "Restlessness and feeling on edge", "Rapid heartbeat (Palpitations) and trembling", "Sudden overwhelming fear of disaster/death (Panic attacks)", "Muscle tension and sleep disturbance"],
        "medicines": ["Escitalopram / Paroxetine", "Clonazepam 0.25mg (Short term SOS for panic)", "Propranolol 10mg (for somatic palpitations)"],
        "tests": ["GAD-7 Anxiety Scale Evaluation", "ECG & Cardiac Evaluation (to rule out arrhythmias during panic attacks)"],
        "diet": "Cut down caffeine, energy drinks, and alcohol; practice deep diaphragmatic breathing and mindfulness meditation."
    },

    # ================= 11. BONE & JOINT DISEASES =================
    {
        "disease_id": "BON001", "disease_name": "Osteoarthritis (Degenerative Joint Disease)",
        "disease_name_hi": "ऑस्टियोआर्थराइटिस / जोड़ों का घिसना (Osteoarthritis)",
        "disease_name_gu": "સંધિવા / ઓસ્ટિઓઆર્થરાઇટિસ (Osteoarthritis)",
        "category": "Bone & Joint Diseases", "category_icon": "", "priority": "High", "icd_code": "M19.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Orthopaedic Surgeon / Rheumatologist",
        "urgency": "Specialist Consultation",
        "symptoms": ["Deep aching joint pain worsening with use (knees, hips)", "Morning joint stiffness lasting < 30 minutes", "Grating or crackling sensation (Crepitus) during movement", "Loss of joint flexibility and bone spurs"],
        "medicines": ["Paracetamol 650mg / Topical Diclofenac Gel", "Glucosamine + Diacerein", "Intra-articular Hyaluronic Acid / PRP injections", "Total Knee Replacement (in severe Stage IV)"],
        "tests": ["Weight-Bearing Standing X-Rays of Knees/Hips (Joint space narrowing)", "Serum Uric Acid (to rule out gout)"],
        "diet": "Weight reduction (reduces knee load by 4x body weight lost), anti-inflammatory foods (turmeric, omega-3, ginger), low-impact swimming/cycling."
    },
    {
        "disease_id": "BON002", "disease_name": "Rheumatoid Arthritis (Autoimmune Arthritis)",
        "disease_name_hi": "रूमेटाइड अर्थराइटिस / गठिया (Rheumatoid Arthritis)",
        "disease_name_gu": "રૂમેટોઇડ આર્થરાઇટિસ (Gout / Arthritis)",
        "category": "Bone & Joint Diseases", "category_icon": "", "priority": "High", "icd_code": "M06.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Rheumatologist",
        "urgency": "Specialist Consultation (Early DMARD Therapy)",
        "symptoms": ["Symmetrical joint pain, warmth and swelling (wrists, fingers)", "Prolonged morning stiffness lasting > 1 hour", "Joint deformities (Swan-neck, Boutonniere)", "Fatigue, low-grade fever and rheumatoid nodules"],
        "medicines": ["Methotrexate 15mg weekly + Folic Acid", "Hydroxychloroquine 200mg", "Sulfasalazine 1g", "Biological DMARDs (Anti-TNF Adalimumab/Etanercept)"],
        "tests": ["Rheumatoid Factor (RA Factor Titre)", "Anti-CCP Antibodies (High specificity)", "Serum CRP & ESR", "Hand & Wrist Bilateral X-Rays"],
        "diet": "Anti-inflammatory Mediterranean diet, zero refined sugars, gentle physical occupational therapy."
    },
    {
        "disease_id": "BON003", "disease_name": "Osteoporosis & Bone Fragility",
        "disease_name_hi": "ऑस्टियोपोरोसिस / हड्डियों की कमजोरी (Osteoporosis)",
        "disease_name_gu": "ઓસ્ટિયોપોરોસિસ (Osteoporosis)",
        "category": "Bone & Joint Diseases", "category_icon": "", "priority": "High", "icd_code": "M81.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Endocrinologist / Orthopaedician",
        "urgency": "Specialist Consultation",
        "symptoms": ["Silent disease until fracture occurs", "Loss of height over time and stooped posture (Kyphosis / Dowager's hump)", "Back pain caused by fractured/collapsed vertebra", "Bone fractures from minor falls (hip, wrist, spine)"],
        "medicines": ["Zoledronic Acid 5mg IV yearly OR Alendronate 70mg weekly", "Calcium Carbonate 500mg + Vitamin D3 60,000 IU", "Teriparatide (PTH analogue)"],
        "tests": ["DEXA Bone Mineral Density Scan (T-Score <= -2.5)", "Serum Calcium, Phosphorus, Alkaline Phosphatase", "Serum 25-OH Vitamin D3"],
        "diet": "Calcium-rich dairy (milk, curd, paneer), sesame seeds (til), ragi, sunlight exposure for natural vitamin D, fall-prevention home modifications."
    },

    # ================= 12. EYE DISEASES =================
    {
        "disease_id": "EYE001", "disease_name": "Cataract (Senile / Traumatic)",
        "disease_name_hi": "मोतियाबिंद (Cataract)",
        "disease_name_gu": "મોતીબિંદુ / મોતિયો (Cataract)",
        "category": "Eye Diseases", "category_icon": "", "priority": "Very High", "icd_code": "H26.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Ophthalmologist / Cataract Surgeon",
        "urgency": "Specialist Consultation (Elective Surgery)",
        "symptoms": ["Cloudy, blurry or dim vision", "Difficulty seeing at night", "Sensitivity to light and glare / halos around lights", "Fading or yellowing of colors", "Frequent changes in eyeglass prescription"],
        "medicines": ["Phacoemulsification with Foldable Intraocular Lens (IOL) Implantation (Definitive Cure)", "Post-operative Antibiotic-Steroid Eye Drops (Moxifloxacin + Prednisolone)"],
        "tests": ["Slit Lamp Biomicroscopy", "Visual Acuity Testing", "Optical Biometry (IOL Master / A-Scan for lens power)"],
        "diet": "Lutein and zeaxanthin rich leafy greens, vitamin C and E, UV protection sunglasses."
    },
    {
        "disease_id": "EYE002", "disease_name": "Glaucoma (Open-Angle / Angle-Closure)",
        "disease_name_hi": "काला मोतिया / ग्लूकोमा (Glaucoma)",
        "disease_name_gu": "ઝામર / ગ્લુકોમા (Glaucoma)",
        "category": "Eye Diseases", "category_icon": "", "priority": "High", "icd_code": "H40.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Glaucoma Specialist / Ophthalmologist",
        "urgency": "Urgent Clinical Attention (Emergency if Acute Angle Closure)",
        "symptoms": ["Gradual loss of peripheral side vision (Tunnel vision)", "Severe throbbing eye pain with headache and nausea (in Acute Glaucoma)", "Seeing rainbow-colored halos around lights", "Red eye and blurred vision"],
        "medicines": ["Latanoprost / Bimatoprost Eye Drops (Prostaglandin analogues)", "Timolol 0.5% Eye Drops", "Brimonidine Eye Drops", "Oral Acetazolamide (Diamox) for acute pressure"],
        "tests": ["Intraocular Pressure (IOP) Goldmann Applanation Tonometry", "Visual Field Humphrey Perimetry", "Optical Coherence Tomography (OCT RNFL)", "Gonioscopy"],
        "diet": "Strict lifelong compliance with daily pressure-lowering eye drops, avoid heavy weight lifting with breath holding."
    },
    {
        "disease_id": "EYE003", "disease_name": "Diabetic Retinopathy",
        "disease_name_hi": "डायबिटिक रेटिनोपैथी (Diabetic Retinopathy)",
        "disease_name_gu": "ડાયાબિટીક રેટિનોપેથી (Diabetic Retinopathy)",
        "category": "Eye Diseases", "category_icon": "", "priority": "High", "icd_code": "H36.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Vitreoretinal Surgeon",
        "urgency": "Urgent Retinal Consultation",
        "symptoms": ["Spots or dark strings floating in vision (Floaters)", "Blurred, fluctuating or distorted vision", "Impaired color vision", "Dark or empty areas in vision / sudden vision loss (Vitreous hemorrhage)"],
        "medicines": ["Intravitreal Anti-VEGF Injections (Ranibizumab / Aflibercept)", "Retinal Pan-Retinal Photocoagulation (PRP Laser)", "Vitrectomy Surgery"],
        "tests": ["Dilated Fundus Examination", "Fundus Fluorescein Angiography (FFA)", "Macular Optical Coherence Tomography (OCT)"],
        "diet": "Strict blood sugar and HbA1c control (< 7.0%), tight blood pressure and lipid control, annual mandatory retinal screening for all diabetics."
    },

    # ================= 13. ORAL HEALTH =================
    {
        "disease_id": "ORL001", "disease_name": "Dental Caries & Tooth Decay",
        "disease_name_hi": "दांतों में कीड़ा / कैविटी (Dental Caries)",
        "disease_name_gu": "દાંતનો સડો / કેવિટી (Dental Caries)",
        "category": "Oral Health", "category_icon": "", "priority": "Very High", "icd_code": "K02.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Dental Surgeon / Endodontist",
        "urgency": "Dental Consultation",
        "symptoms": ["Toothache and spontaneous pain without cause", "Tooth sensitivity to sweet, hot or cold food/drinks", "Visible holes or pits in teeth", "Brown, black or white staining on tooth surface"],
        "medicines": ["Fluoride Varnish / Toothpaste", "Dental Composite Restorations / Root Canal Treatment (RCT)", "Amoxicillin + Clavulanate (if periapical abscess)", "Ibuprofen / Paracetamol for pain"],
        "tests": ["Dental Clinical Examination with Explorer Probe", "Intraoral Periapical (IOPA) X-Rays / OPG Panoramic X-Ray"],
        "diet": "Cut down sticky sugary snacks, brush twice daily with fluoridated toothpaste, floss daily, rinse mouth after every meal."
    },
    {
        "disease_id": "ORL002", "disease_name": "Periodontal Disease (Gingivitis & Periodontitis)",
        "disease_name_hi": "पायरिया / मसूड़ों की बीमारी (Periodontitis)",
        "disease_name_gu": "પાયોરિયા / પેઢાનો સોજો (Periodontal Disease)",
        "category": "Oral Health", "category_icon": "", "priority": "High", "icd_code": "K05.6",
        "communicable": False, "outbreak_prone": False, "specialist": "Periodontist",
        "urgency": "Dental Consultation",
        "symptoms": ["Swollen, tender, dusky red gums", "Gums that bleed easily when brushing or flossing", "Persistent bad breath (Halitosis)", "Receding gumline making teeth look longer", "Loose teeth and pus between teeth and gums"],
        "medicines": ["Chlorhexidine 0.2% Antiseptic Mouthwash", "Professional Ultrasonic Scaling & Root Planing", "Doxycycline / Metronidazole (if aggressive)"],
        "tests": ["Periodontal Probing Depth (PPD) Measurement", "Full Mouth Dental Radiographs"],
        "diet": "Vitamin C rich citrus fruits, crisp raw vegetables, avoid smoking and gutkha chewing."
    },

    # ================= 14. MATERNAL HEALTH =================
    {
        "disease_id": "MAT001", "disease_name": "Maternal Anemia in Pregnancy",
        "disease_name_hi": "गर्भावस्था में एनीमिया (Maternal Anemia)",
        "disease_name_gu": "ગર્ભાવસ્થામાં એનિમિયા (Maternal Anemia)",
        "category": "Maternal Health", "category_icon": "", "priority": "Very High", "icd_code": "O99.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Obstetrician & Gynaecologist",
        "urgency": "Urgent Antenatal Care",
        "symptoms": ["Hemoglobin < 11 g/dL in pregnancy", "Severe exhaustion, weakness and dizziness", "Shortness of breath on walking", "Palpitations and swollen feet", "Risk of preterm delivery and low birth weight"],
        "medicines": ["Iron & Folic Acid (IFA) Tablets (100mg elemental iron + 500mcg folic acid daily)", "Injectable Ferric Carboxymaltose (FCM) IV (for moderate-severe anemia)"],
        "tests": ["Serial Hemoglobin Testing at each ANC visit", "Complete Blood Count", "Serum Ferritin"],
        "diet": "Green leafy vegetables, jaggery, drumstick leaves, pomegranate, pulses, meat/eggs under PMSMA antenatal program."
    },
    {
        "disease_id": "MAT002", "disease_name": "Pre-eclampsia & Eclampsia",
        "disease_name_hi": "प्री-एक्लेम्पसिया / गर्भावस्था में उच्च रक्तचाप (Pre-eclampsia)",
        "disease_name_gu": "પ્રિ-એક્લેમ્પસિયા (Pre-eclampsia)",
        "category": "Maternal Health", "category_icon": "", "priority": "Very High", "icd_code": "O14.9",
        "communicable": False, "outbreak_prone": False, "specialist": "High-Risk Obstetrician",
        "urgency": "Critical / Emergency Immediate Hospitalization",
        "symptoms": ["New onset high blood pressure (BP >= 140/90 mmHg after 20 weeks)", "Severe persistent frontal headache", "Visual disturbances (blurring, flashing lights)", "Sudden severe swelling of face and hands", "Severe pain in upper right abdomen (under ribs)", "Convulsions/fits (in Eclampsia)"],
        "medicines": ["Magnesium Sulfate (Pritchard Regimen - Anticonvulsant of choice)", "Labetalol 100mg/200mg / Nifedipine 10mg retard", "Urgent delivery planning"],
        "tests": ["Urine Protein Dipstick (Albuminuria >= 2+)", "24-Hour Urine Protein", "Platelet Count & Liver Enzymes (to rule out HELLP syndrome)", "Fetal Doppler Ultrasound"],
        "diet": "Careful salt monitoring, high calcium and protein maternal nutrition, continuous medical monitoring."
    },
    {
        "disease_id": "MAT005", "disease_name": "Postpartum Hemorrhage (PPH)",
        "disease_name_hi": "प्रसवोत्तर रक्तस्राव (Postpartum Hemorrhage)",
        "disease_name_gu": "પ્રસૂતિ પછી વધુ પડતો રક્તસ્રાવ (PPH)",
        "category": "Maternal Health", "category_icon": "", "priority": "Very High", "icd_code": "O72.1",
        "communicable": False, "outbreak_prone": False, "specialist": "Obstetrician & Emergency Delivery Team",
        "urgency": "Critical / Emergency Immediate Obstetric Resuscitation",
        "symptoms": ["Excessive vaginal bleeding (> 500ml after vaginal delivery or > 1000ml after C-section)", "Continuous soaking of pads", "Rapid drop in blood pressure and rapid weak pulse (Hypovolemic shock)", "Dizziness, cold clammy skin, confusion and loss of consciousness"],
        "medicines": ["Oxytocin 10 IU IM/IV infusion", "Misoprostol 800mcg per rectum", "Carboprost / Methylergometrine", "Tranexamic Acid (TXA) 1g IV within 3 hours", "Emergency Blood Transfusion"],
        "tests": ["Bedside Blood Clotting Test", "Cross-matching and grouping (PRBC, FFP, Platelets)", "Uterine Tone Assessment"],
        "diet": "Active management of third stage of labor (AMTSL) is standard lifesaving protocol."
    },

    # ================= 15. CHILD & NEONATAL HEALTH =================
    {
        "disease_id": "PED001", "disease_name": "Neonatal Sepsis & Severe Infection",
        "disease_name_hi": "नवजात सेप्सिस / नवजात शिशु संक्रमण (Neonatal Sepsis)",
        "disease_name_gu": "નવજાત શિશુમાં સેપ્સિસ (Neonatal Sepsis)",
        "category": "Child & Neonatal Health", "category_icon": "", "priority": "Very High", "icd_code": "P36.9",
        "communicable": True, "outbreak_prone": False, "specialist": "Neonatologist / Pediatrician (SNCU/NICU)",
        "urgency": "Critical / Emergency Immediate NICU Admission",
        "symptoms": ["Poor sucking or inability to feed", "Lethargy, drowsiness or floppiness", "Hypothermia (< 36.5°C) or high fever", "Fast breathing (> 60 breaths/min) and chest in-drawing", "Cyanosis or prolonged capillary refill time (> 3s)"],
        "medicines": ["IV Ampicillin + Gentamicin (First line)", "IV Cefotaxime / Amikacin (Second line)", "Oxygen therapy & thermoregulation (Radiant warmer)"],
        "tests": ["Blood Culture (Gold standard)", "Complete Blood Count with Band cells (I:T Ratio)", "Serum CRP / Micro-ESR", "Lumbar Puncture (to rule out meningitis)"],
        "diet": "Expressed breast milk (EBM) via paladai or orogastric tube when clinically stable; exclusive breastfeeding."
    },
    {
        "disease_id": "PED005", "disease_name": "Childhood Pneumonia & Acute Respiratory Distress",
        "disease_name_hi": "बच्चों में निमोनिया (Childhood Pneumonia)",
        "disease_name_gu": "બાળકોમાં ન્યુમોનિયા (Childhood Pneumonia)",
        "category": "Child & Neonatal Health", "category_icon": "", "priority": "Very High", "icd_code": "J18.0",
        "communicable": True, "outbreak_prone": False, "specialist": "Pediatrician",
        "urgency": "Urgent Clinical Attention (IMNCI Protocols)",
        "symptoms": ["Fast breathing (Age 2-11m: >= 50/min; Age 1-5y: >= 40/min)", "Lower chest in-drawing", "Stridor in calm child", "Nasal flaring and grunting", "Inability to drink or breastfeed"],
        "medicines": ["Oral Amoxicillin 40-45 mg/kg/day (IMNCI First line)", "Injectable Ampicillin + Gentamicin (for severe pneumonia)", "Oxygen therapy if SpO2 < 90%"],
        "tests": ["IMNCI Clinical Respiratory Rate Counting", "Pulse Oximetry", "Chest X-Ray"],
        "diet": "Continue frequent breastfeeding, warm fluids, small frequent nutritious meals."
    },
    {
        "disease_id": "PED007", "disease_name": "Severe Acute Malnutrition (SAM)",
        "disease_name_hi": "अति कुपोषण (Severe Acute Malnutrition - SAM)",
        "disease_name_gu": "ગંભીર કુપોષણ (Severe Acute Malnutrition)",
        "category": "Child & Neonatal Health", "category_icon": "", "priority": "Very High", "icd_code": "E43",
        "communicable": False, "outbreak_prone": False, "specialist": "Pediatrician / NRC Nutritionist",
        "urgency": "Urgent Nutrition Rehabilitation Center (NRC) Care",
        "symptoms": ["Weight-for-height < -3 Z-scores (WHO growth charts)", "Mid-Upper Arm Circumference (MUAC < 11.5 cm)", "Bilateral pitting edema of feet (Kwashiorkor)", "Severe visible muscle wasting (Marasmus)", "Appetite loss and apathy"],
        "medicines": ["F-75 and F-100 Therapeutic Milk Formulas", "Ready-to-Use Therapeutic Food (RUTF)", "Broad-spectrum Amoxicillin", "Vitamin A megadose + Folic Acid + Zinc"],
        "tests": ["Appetite Test with RUTF", "MUAC Measurement", "Blood Glucose (to prevent hypoglycemia)", "Urine Routine & Electrolytes"],
        "diet": "Structured phased nutritional rehabilitation: Stabilization phase (F-75) followed by Catch-up growth phase (F-100 / RUTF)."
    },

    # ================= 16. ZOONOTIC & ENVIRONMENTAL EMERGENCIES =================
    {
        "disease_id": "ZOO001", "disease_name": "Rabies Post-Exposure / Encephalitis",
        "disease_name_hi": "रेबीज / हाइड्रोफोबिया (Rabies)",
        "disease_name_gu": "હડકવા (Rabies)",
        "category": "Zoonotic & Emergency", "category_icon": "", "priority": "Very High", "icd_code": "A82.9",
        "communicable": True, "outbreak_prone": False, "specialist": "Infectious Disease / Anti-Rabies Clinic",
        "urgency": "Critical / Emergency Immediate Post-Exposure Prophylaxis",
        "symptoms": ["History of animal bite/scratch (Dog, cat, monkey)", "Fear of water (Hydrophobia) and drafts of air (Aerophobia)", "Agitation, confusion, and hyper-salivation", "Fever and tingling at bite wound site", "Paralysis and convulsions"],
        "medicines": ["Immediate wound washing with soap and running water for 15 mins", "Anti-Rabies Vaccine (ARV) Day 0, 3, 7, 14, 28", "Rabies Immunoglobulin (RIG) directly into wound"],
        "tests": ["Clinical History of Exposure", "Skin Biopsy nuchal / Saliva RT-PCR"],
        "diet": "Preventive post-exposure prophylaxis is 100% lifesaving; symptomatic rabies has >99.9% fatality."
    },
    {
        "disease_id": "ZOO002", "disease_name": "Snakebite Envenoming",
        "disease_name_hi": "सर्पदंश / सांप का काटना (Snakebite Envenoming)",
        "disease_name_gu": "સાપ કરડવો (Snakebite)",
        "category": "Zoonotic & Emergency", "category_icon": "", "priority": "Very High", "icd_code": "T63.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Emergency Medical Team",
        "urgency": "Critical / Emergency Immediate Hospitalization",
        "symptoms": ["Fang puncture marks with severe pain/swelling", "Bleeding from bite wound and gums", "Drooping eyelids (Ptosis), difficulty speaking/swallowing", "Paralysis and respiratory arrest (Neurotoxic)", "Dark reddish urine and kidney shutdown (Hemotoxic/Russell's viper)"],
        "medicines": ["Polyvalent Anti-Snake Venom (ASV) IV (10 vials initial dose)", "Neostigmine + Atropine (for neurotoxic bite)", "Tetanus Toxoid Booster", "IV Fluids"],
        "tests": ["20-Minute Whole Blood Clotting Test (20WBCT - bedside)", "Serum Creatinine / Electrolytes", "Prothrombin Time / INR", "Urine Routine (Hematuria)"],
        "diet": "Strict NPO (Nil by mouth) during acute emergency management until airway and breathing secured."
    },
    {
        "disease_id": "ZOO003", "disease_name": "Nipah Virus Disease (NiV)",
        "disease_name_hi": "निपाह वायरस रोग (Nipah Virus)",
        "disease_name_gu": "નિપાહ વાયરસ રોગ (Nipah Virus)",
        "category": "Zoonotic & Emergency", "category_icon": "", "priority": "Very High", "icd_code": "B27.8",
        "communicable": True, "outbreak_prone": True, "specialist": "High Containment Infectious Disease Team",
        "urgency": "Critical / Emergency Immediate Isolation & Strict Barrier Nursing",
        "symptoms": ["High fever, headache, myalgia and sore throat", "Dizziness, drowsiness, altered consciousness", "Acute respiratory distress / severe atypical pneumonia", "Rapid progression to acute encephalitis, seizures and coma (within 24-48 hours)"],
        "medicines": ["Strict Intensive ICU Supportive Care", "Monoclonal Antibody m102.4 (Compassionate use)", "Ribavirin (Adjunct)"],
        "tests": ["Real-Time RT-PCR (Throat swab, CSF, Urine)", "IgM & IgG ELISA Serology", "High-Containment BSL-4 Laboratory Confirmation (NIV Pune)"],
        "diet": "Strict negative pressure isolation, dedicated barrier nursing, avoid raw date palm sap and bat-bitten fruits."
    },
    {
        "disease_id": "ZOO007", "disease_name": "Kyasanur Forest Disease (KFD / Monkey Fever)",
        "disease_name_hi": "क्यासानूर फॉरेस्ट डिजीज / मंकी फीवर (KFD)",
        "disease_name_gu": "મંકી ફીવર (KFD)",
        "category": "Zoonotic & Emergency", "category_icon": "", "priority": "High", "icd_code": "A98.2",
        "communicable": True, "outbreak_prone": True, "specialist": "Infectious Disease Physician",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["Sudden onset high fever with severe headache and frontal pain", "Severe muscle stiffness and body pain", "Gastrointestinal bleeding and epistaxis (nosebleeds)", "Tremors, neck stiffness, and mental confusion in second phase"],
        "medicines": ["Supportive maintenance of hydration and blood pressure", "Blood and platelet transfusions if severe bleeding", "KFD Vaccine (in endemic forest districts)"],
        "tests": ["Nested RT-PCR for KFD Virus", "IgM ELISA Serology (NIV Pune / VRDL)"],
        "diet": "Nutritious easily digestible diet, plenty of oral fluids and electrolytes."
    },
    {
        "disease_id": "ZOO008", "disease_name": "Leptospirosis (Weil's Disease)",
        "disease_name_hi": "लेप्टोस्पायरोसिस (Leptospirosis)",
        "disease_name_gu": "લેપ્ટોસ્પાયરોસિસ (Leptospirosis)",
        "category": "Zoonotic & Emergency", "category_icon": "", "priority": "High", "icd_code": "A27.9",
        "communicable": True, "outbreak_prone": True, "specialist": "Physician",
        "urgency": "Urgent Clinical Attention",
        "symptoms": ["History of wading in floodwater or contact with animal urine", "High fever with intense calf muscle tenderness", "Conjunctival suffusion (Red eyes without discharge)", "Jaundice and acute kidney injury (Weil's disease)", "Pulmonary hemorrhage with coughing up blood"],
        "medicines": ["Doxycycline 100mg twice daily (Oral)", "Crystalline Penicillin G IV (for severe cases)", "Ceftriaxone 1g IV"],
        "tests": ["Leptospira IgM ELISA", "Microscopic Agglutination Test (MAT - Gold Standard)", "Renal & Liver Function Tests"],
        "diet": "Adequate fluids, kidney protective care, avoid wading in stagnated urban floodwater."
    },

    # ================= 17. INJURIES & TRAUMA EMERGENCIES =================
    {
        "disease_id": "INJ001", "disease_name": "Traumatic Brain Injury & Head Trauma (TBI)",
        "disease_name_hi": "सिर की गंभीर चोट / दर्दनाक मस्तिष्क की चोट (TBI)",
        "disease_name_gu": "માથાની ગંભીર ઇજા / ટ્રોમેટિક બ્રેઈન ઇન્જરી (TBI)",
        "category": "Injuries & Emergency", "category_icon": "", "priority": "Very High", "icd_code": "S06.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Neurosurgeon / Trauma Team",
        "urgency": "Critical / Emergency Immediate Trauma Resuscitation",
        "symptoms": ["History of road traffic accident (RTA) or fall", "Loss of consciousness", "Repeated vomiting and severe headache", "Unequal pupil size (Anisocoria)", "Clear fluid leaking from nose/ears (CSF Rhinorrhea/Otorrhea)", "Glasgow Coma Scale (GCS) drop"],
        "medicines": ["Mannitol 20% / 3% Hypertonic Saline", "Levetiracetam 1g IV", "Tranexamic Acid (CRASH-3 protocol)", "Emergency Craniotomy / Hematoma Evacuation"],
        "tests": ["Emergency Non-Contrast Brain CT Scan (NCCT)", "C-Spine X-Ray / CT", "GCS Score Monitoring"],
        "diet": "Strict trauma airway protection; post-stabilization enteral neuro-rehabilitation nutrition."
    },
    {
        "disease_id": "INJ003", "disease_name": "Severe Thermal Burns",
        "disease_name_hi": "गंभीर जलन / बर्न इंजरी (Severe Burns)",
        "disease_name_gu": "દાઝી જવું / બર્ન્સ (Severe Burns)",
        "category": "Injuries & Emergency", "category_icon": "", "priority": "High", "icd_code": "T30.0",
        "communicable": False, "outbreak_prone": False, "specialist": "Burns & Plastic Surgeon",
        "urgency": "Critical / Emergency Specialized Burns Center Care",
        "symptoms": ["Blistering, charred or white skin", "Severe burning pain or numbness (in 3rd degree burns)", "Rapid loss of body fluids and hypovolemic shock", "Smoke inhalation injury with soot in airway"],
        "medicines": ["Aggressive Parkland Fluid Resuscitation (4ml x kg x %TBSA Ringer Lactate in 24h)", "Silver Sulfadiazine / Collagen Dressing", "IV Tramadol / Fentanyl for analgesia", "Tetanus Toxoid"],
        "tests": ["Total Body Surface Area (% TBSA - Rule of Nines)", "Serum Electrolytes, Renal Function", "Arterial Blood Gas & Carboxyhemoglobin"],
        "diet": "Hyper-metabolic nutritional support: high calorie, very high protein, zinc, vitamin C."
    },
    {
        "disease_id": "INJ006", "disease_name": "Acute Poisoning & Chemical Ingestion",
        "disease_name_hi": "विषाक्तता / जहर का सेवन (Acute Poisoning)",
        "disease_name_gu": "ઝેર ખાવું / પોઈઝનિંગ (Acute Poisoning)",
        "category": "Injuries & Emergency", "category_icon": "", "priority": "High", "icd_code": "T65.9",
        "communicable": False, "outbreak_prone": False, "specialist": "Emergency Toxicologist / Intensivist",
        "urgency": "Critical / Emergency Immediate Medical Toxicology Care",
        "symptoms": ["History of pesticide, organophosphate, rodenticide, or drug overdose", "Constricted pinpoint pupils or widely dilated pupils", "Excessive salivation, sweating, and wheezing (SLUDGE syndrome in OP poisoning)", "Vomiting, abdominal cramps, seizures and unconsciousness"],
        "medicines": ["Atropine IV (titrated until full atropinization for OP poisoning)", "Pralidoxime (2-PAM)", "Activated Charcoal (if within 1-2 hours of non-corrosive ingestion)", "N-Acetylcysteine (for Paracetamol poisoning)"],
        "tests": ["Serum Cholinesterase Levels", "Serum Electrolytes, ABG, Renal & Hepatic Function", "Toxicology Screen & ECG"],
        "diet": "Strict NPO during resuscitation; gastric lavage only if indicated (strictly contraindicated in acids/alkalies/hydrocarbons)."
    }
]

def generate_master_datasets():
    df = pd.DataFrame(MAJOR_DISEASES)
    
    # Save CSV in datasets/disease
    csv_path = os.path.join(OUTPUT_DIR, "india_major_diseases.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Saved {len(df)} comprehensive Indian major diseases to {csv_path}")
    
    # Save Parquet in datasets/disease
    parquet_path = os.path.join(OUTPUT_DIR, "india_major_diseases.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"Saved {len(df)} comprehensive Indian major diseases to {parquet_path}")

    # Also sync to data/processed/command_center
    proc_cc = os.path.join(WORKSPACE_ROOT, "data", "processed", "command_center")
    if os.path.exists(proc_cc):
        df.to_parquet(os.path.join(proc_cc, "india_major_diseases.parquet"), index=False)
        print(f"Synced india_major_diseases.parquet to command_center processed data.")

if __name__ == "__main__":
    generate_master_datasets()
