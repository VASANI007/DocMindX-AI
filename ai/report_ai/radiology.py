"""
    Unified Diagnostic Imaging & Radiology Report Analyzer
Analyzes X-Rays, CT Scans, MRI, Ultrasound (USG), and Mammography reports
using AI vision / clinical LLM with resilient deterministic radiological fallback.
"""
import re
import json
import requests
from config.settings import GEMINI_API_KEY, GROQ_API_KEY
from ai.report_ai.medical_verifier import verify_medical_document

RADIOLOGY_PATTERNS = [
    # Chest / Pulmonology
    {
        "pattern": r"\b(consolidation|pneumonia|bronchopneumonia|infiltrat\w*|patchy opacity)\b",
        "modality": "Chest X-Ray / CT",
        "finding": "Lung Consolidation / Potential Pneumonia",
        "finding_hi": "फेफड़ों में संक्रमण / निमोनिया के संकेत",
        "finding_gu": "ફેફસાંમાં ચેપ / ન્યુમોનિયાના સંકેત",
        "severity": "High",
        "explanation": "Alveolar airspace filling or inflammation in lung tissue suggesting active respiratory infection or pneumonia.",
        "recommendation": "Consult a pulmonologist or physician promptly for clinical auscultation and targeted antibiotic therapy."
    },
    {
        "pattern": r"\b(pleural effusion|costophrenic angle blunting|blunted costophrenic|fluid in pleural space)\b",
        "modality": "Chest X-Ray / Ultrasound",
        "finding": "Pleural Effusion (Fluid in Chest Cavity)",
        "finding_hi": "फेफड़ों के चारों ओर पानी भरना (प्लुरल इफ्यूजन)",
        "finding_gu": "ફેફસાંની આસપાસ પ્રવાહી ભરાવું",
        "severity": "High",
        "explanation": "Abnormal fluid accumulation within the pleural space surrounding the lungs.",
        "recommendation": "Pulmonology evaluation advised to determine underlying cause (infectious, cardiac, or inflammatory)."
    },
    {
        "pattern": r"\b(ground glass|ggo|interstitial thickening|corads|viral pneumonia)\b",
        "modality": "HRCT Chest",
        "finding": "Ground Glass Opacities (GGO) / Pneumonitis",
        "finding_hi": "फेफड़ों में ग्राउंड ग्लास ओपेसिटी (निमोनिटिस)",
        "finding_gu": "ફેફસાંમાં ગ્રાઉન્ડ ગ્લાસ ઓપેસિટી",
        "severity": "High",
        "explanation": "Hazy opacity seen on high-resolution chest CT indicating alveolar inflammation or pneumonitis.",
        "recommendation": "Monitor oxygen levels (SpO2) and consult a pulmonologist for appropriate medical management."
    },
    {
        "pattern": r"\b(cardiomegaly|enlarged cardiac shadow|ctr\s*>\s*0\.5|increased cardiothoracic)\b",
        "modality": "Chest X-Ray",
        "finding": "Cardiomegaly (Enlarged Cardiac Silhouette)",
        "finding_hi": "हृदय का आकार बढ़ना (कार्डियोमेगाली)",
        "finding_gu": "હૃદયનું કદ મોટું થવું (કાર્ડિયોમેગાલી)",
        "severity": "Medium",
        "explanation": "Enlarged heart shadow seen on chest radiograph, often related to hypertension or cardiac strain.",
        "recommendation": "Echocardiogram (2D Echo) and ECG advised under cardiologist supervision."
    },
    # Neurology / Brain
    {
        "pattern": r"\b(intracranial hemorrhage|subdural hematoma|extradural hematoma|subarachnoid bleed|acute bleed)\b",
        "modality": "Brain CT / MRI",
        "finding": "Intracranial Hemorrhage / Acute Bleed",
        "finding_hi": "मस्तिष्क में रक्तस्राव (इंतराक्रेनियल ब्लीड)",
        "finding_gu": "મગજમાં રક્તસ્રાવ",
        "severity": "Emergency",
        "explanation": "Accumulation of blood within brain parenchyma or surrounding cranial compartments.",
        "recommendation": "CRITICAL EMERGENCY: Immediate neurosurgical consultation and emergency ICU care required."
    },
    {
        "pattern": r"\b(acute infarct|diffusion restriction|ischemic stroke|dwi bright|cytotoxic edema)\b",
        "modality": "Brain MRI",
        "finding": "Acute Cerebral Infarction / Ischemic Stroke",
        "finding_hi": "मस्तिष्क में तीव्र इस्केमिक स्ट्रोक (रक्त प्रवाह अवरोध)",
        "finding_gu": "મગજમાં ઇસ્કેમિક સ્ટ્રોક",
        "severity": "Emergency",
        "explanation": "Acute compromise of cerebral blood supply causing localized brain tissue ischemia.",
        "recommendation": "CRITICAL EMERGENCY: Immediate stroke neurology team intervention and monitoring required."
    },
    # Spine & Orthopedics
    {
        "pattern": r"\b(fracture|cortical break|displaced fracture|undisplaced fracture|callus formation)\b",
        "modality": "X-Ray / CT",
        "finding": "Bone Fracture / Cortical Disruption",
        "finding_hi": "हड्डी में फ्रैक्चर / दरार",
        "finding_gu": "હાડકામાં ફ્રેક્ચર / તિરાડ",
        "severity": "High",
        "explanation": "Disruption or crack in the structural continuity of the bone cortex.",
        "recommendation": "Orthopedic consultation for immobilization (cast/splint) and pain management."
    },
    {
        "pattern": r"\b(disc herniation|disc bulge|disc extrusion|thecal sac compression|nerve root compression)\b",
        "modality": "Spine MRI",
        "finding": "Intervertebral Disc Herniation / Nerve Compression",
        "finding_hi": "स्लिप डिस्क / नस पर दबाव (डिस्क हर्निएशन)",
        "finding_gu": "સ્લિપ ડિસ્ક / નસ દબાવી (હર્નિએશન)",
        "severity": "Medium",
        "explanation": "Displaced disc material exerting pressure against adjacent nerve roots or spinal cord.",
        "recommendation": "Spine specialist review, physical therapy, core strengthening, and ergonomic posture care."
    },
    {
        "pattern": r"\b(degenerative changes|osteophyte|joint space narrowing|spondylosis|spondylitis)\b",
        "modality": "X-Ray / MRI",
        "finding": "Degenerative Changes / Spondylosis",
        "finding_hi": "हड्डियों व जोड़ों में उम्र संबंधी घिसावट",
        "finding_gu": "સાંધા અને કરોડરજ્જુનો ઘસારો",
        "severity": "Low",
        "explanation": "Age-related wear-and-tear in joints or vertebrae with narrowing and bone spur formation.",
        "recommendation": "Physiotherapy, low-impact exercise, and joint supportive care under physician guidance."
    },
    # Abdominal / Urology
    {
        "pattern": r"\b(calculus|calculi|nephrolithiasis|ureteric stone|hydronephrosis|cholelithiasis|gallstone)\b",
        "modality": "Ultrasound / CT Abdomen",
        "finding": "Calculus (Stone) / Hydronephrosis",
        "finding_hi": "पथरी (किडनी / पित्ताशय स्टोन) या सूजन",
        "finding_gu": "પથરી (કિડની / પિત્તાશય સ્ટોન)",
        "severity": "Medium",
        "explanation": "Calculus formation in the urinary tract or gallbladder causing flow resistance or dilation.",
        "recommendation": "Urology / Gastroenterology consultation for stone management, hydration, and diet planning."
    },
    {
        "pattern": r"\b(appendicitis|inflamed appendix|periappendiceal stranding)\b",
        "modality": "CT Abdomen / USG",
        "finding": "Acute Appendicitis",
        "finding_hi": "तीव्र एपेंडिसाइटिस (एपेंडिक्स में सूजन)",
        "finding_gu": "એપેન્ડિક્સમાં સોજો (એપેન્ડિસાઇટિસ)",
        "severity": "High",
        "explanation": "Acute inflammation and enlargement of the appendix.",
        "recommendation": "Urgent general surgical review for clinical examination and possible appendectomy."
    },
    # Normal / Unremarkable
    {
        "pattern": r"\b(normal study|no acute abnormality|no focal abnormality|unremarkable study|within normal limits|clear lung fields)\b",
        "modality": "Radiology",
        "finding": "Unremarkable / Normal Radiological Study",
        "finding_hi": "सामान्य रेडियोलॉजिकल रिपोर्ट (कोई बड़ी असामान्यता नहीं)",
        "finding_gu": "સામાન્ય રેડિયોલોજી રિપોર્ટ",
        "severity": "Normal",
        "explanation": "No significant structural, pathological, or acute lesions detected on this imaging study.",
        "recommendation": "Routine clinical follow-up as advised by your healthcare provider."
    }
]

class RadiologyReportAnalyzer:
    def __init__(self):
        pass

    def analyze_imaging_report(self, raw_text: str, user_lang: str = "en") -> dict:
        """
        Main entry point for Diagnostic Imaging / Radiology Report evaluation.
        Evaluates validity first, then uses AI / Deterministic regex pattern matching.
        """
        # Step 1: Universal Medical Document Verification
        doc_eval = verify_medical_document(raw_text, expected_type="radiology")
        if not doc_eval["is_valid"]:
            return {
                "is_valid_radiology_report": False,
                "total_findings": 0,
                "findings": [],
                "overall_severity": "Unknown",
                "summary": "The uploaded document does not appear to be a diagnostic radiology or imaging report. No radiological impressions were detected."
            }

        # Step 2: Try AI Structured Radiology Extraction
        ai_res = self._evaluate_with_ai(raw_text, user_lang)
        if ai_res is not None and ai_res.get("is_valid_radiology_report") and len(ai_res.get("findings", [])) > 0:
            return ai_res

        # Step 3: Resilient Deterministic Pattern Fallback
        return self._evaluate_with_patterns(raw_text, user_lang)

    def _evaluate_with_ai(self, raw_text: str, user_lang: str) -> dict | None:
        prompt = f"""
        You are a board-certified Radiologist and diagnostic imaging AI.
CRITICAL VALIDATION:
1. Verify if the following document text represents a genuine Diagnostic Imaging / Radiology Report (e.g., Chest X-Ray, Bone X-Ray, CT Scan, HRCT, MRI Brain/Spine/Joint, Ultrasound / USG, Mammography).
2. If the document is NOT a radiological report (e.g., general letter, college certificate, invoice, non-medical document), return:
{{
  "is_valid_radiology_report": false,
  "summary": "The uploaded document is not a radiological imaging report. No imaging findings detected.",
  "findings": []
}}

3. If it IS a valid radiology report:
Extract all significant radiological findings, impressions, severity (Normal, Low, Medium, High, Emergency), anatomical modality, plain-language patient explanations, and clinical recommendations.

REPORT TEXT:
\"\"\"{raw_text}\"\"\"

OUTPUT FORMAT:
Return strictly a valid JSON object matching this schema:
{{
  "is_valid_radiology_report": true,
  "modality": "X-Ray / CT Scan / MRI / Ultrasound / Other",
  "overall_severity": "Normal / Low / Medium / High / Emergency",
  "summary": "Concise 1-2 sentence overall radiological impression.",
  "findings": [
    {{
      "finding_name": "Name of finding",
      "severity": "Normal / Low / Medium / High / Emergency",
      "modality": "...",
      "explanation": "Clear explanation for patient...",
      "recommendation": "Recommended clinical action..."
    }}
  ]
}}"""

        if GEMINI_API_KEY:
            for model in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-2.5-flash"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048, "responseMimeType": "application/json"}
                    }
                    res = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            txt = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            parsed = json.loads(txt)
                            if parsed:
                                is_rad = parsed.get("is_valid_radiology_report", True)
                                findings = parsed.get("findings", [])
                                if not is_rad or not findings:
                                    return {
                                        "is_valid_radiology_report": False,
                                        "total_findings": 0,
                                        "findings": [],
                                        "overall_severity": "Unknown",
                                        "summary": parsed.get("summary", "The uploaded document is not a radiological imaging report. No imaging findings detected.")
                                    }
                                return {
                                    "is_valid_radiology_report": True,
                                    "total_findings": len(findings),
                                    "overall_severity": parsed.get("overall_severity", "Normal"),
                                    "findings": findings,
                                    "summary": parsed.get("summary", "")
                                }
                except Exception as e:
                    print(f"Gemini radiology note ({model}): {e}")

        if GROQ_API_KEY:
            for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
                try:
                    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                    body = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a clinical radiologist AI. Return JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1600,
                        "response_format": {"type": "json_object"}
                    }
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8)
                    if res.status_code == 200:
                        txt = res.json()["choices"][0]["message"]["content"]
                        parsed = json.loads(txt)
                        if parsed:
                            is_rad = parsed.get("is_valid_radiology_report", True)
                            findings = parsed.get("findings", [])
                            if not is_rad or not findings:
                                return {
                                    "is_valid_radiology_report": False,
                                    "total_findings": 0,
                                    "findings": [],
                                    "overall_severity": "Unknown",
                                    "summary": parsed.get("summary", "The uploaded document is not a radiological imaging report. No imaging findings detected.")
                                }
                            return {
                                "is_valid_radiology_report": True,
                                "total_findings": len(findings),
                                "overall_severity": parsed.get("overall_severity", "Normal"),
                                "findings": findings,
                                "summary": parsed.get("summary", "")
                            }
                except Exception as e:
                    print(f"Groq radiology note ({model}): {e}")

        return None

    def _evaluate_with_patterns(self, raw_text: str, user_lang: str) -> dict:
        text_lower = raw_text.lower()
        findings = []
        highest_severity = "Normal"
        sev_rank = {"Normal": 0, "Low": 1, "Medium": 2, "High": 3, "Emergency": 4}


        for item in RADIOLOGY_PATTERNS:
            if re.search(item["pattern"], text_lower):
                sev = item["severity"]
                if sev_rank.get(sev, 0) > sev_rank.get(highest_severity, 0):
                    highest_severity = sev

                disp_name = item["finding"]
                if user_lang == "hi":
                    disp_name = item["finding_hi"]
                elif user_lang == "gu":
                    disp_name = item["finding_gu"]

                findings.append({
                    "finding_name": disp_name,
                    "english_name": item["finding"],
                    "modality": item["modality"],
                    "severity": sev,
                    "explanation": item["explanation"],
                    "recommendation": item["recommendation"]
                })

        if not findings:
            return {
                "is_valid_radiology_report": False,
                "total_findings": 0,
                "findings": [],
                "overall_severity": "Unknown",
                "summary": "No specific radiological or imaging findings identified in this document. Please ensure you upload a clear X-Ray, CT Scan, MRI, or Ultrasound report."
            }

        return {
            "is_valid_radiology_report": True,
            "total_findings": len(findings),
            "overall_severity": highest_severity,
            "findings": findings,
            "summary": f"Identified {len(findings)} radiological findings with overall status '{highest_severity}'."
        }

radiology_analyzer = RadiologyReportAnalyzer()
