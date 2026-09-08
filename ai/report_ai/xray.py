"""
    DocMindX AI - Chest & Musculoskeletal X-Ray Report Analyzer
Extracts radiological findings, checks for abnormalities, and translates into patient guidance.
"""
import re

XRAY_FINDING_PATTERNS = [
    {
        "pattern": r"(consolidation|pneumonia|infiltrat|patchy opacity)",
        "finding": "Lung Consolidation / Potential Pneumonia",
        "finding_hi": "फेफड़ों में संक्रमण / निमोनिया के संकेत",
        "finding_gu": "ફેફસાંમાં ચેપ / ન્યુમોનિયાના સંકેત",
        "severity": "High",
        "explanation": "Opacity or density in the lung tissue suggesting fluid, inflammation, or infection.",
        "recommendation": "Urgent physician review recommended for targeted antibiotics and clinical auscultation."
    },
    {
        "pattern": r"(pleural effusion|blunted costophrenic|fluid in pleural)",
        "finding": "Pleural Effusion (Fluid Around Lung)",
        "finding_hi": "फेफड़ों के चारों ओर पानी भरना (प्लुरल इफ्यूजन)",
        "finding_gu": "ફેફસાંની આસપાસ પ્રવાહી ભરાવું",
        "severity": "High",
        "explanation": "Abnormal accumulation of fluid between the layers of tissue that line the lungs and chest cavity.",
        "recommendation": "Consult a pulmonologist promptly for diagnostic evaluation and physical examination."
    },
    {
        "pattern": r"(cardiomegaly|enlarged cardiac shadow|ctr > 0\.5|increased cardiothoracic)",
        "finding": "Cardiomegaly (Enlarged Heart Shadow)",
        "finding_hi": "हृदय का आकार बढ़ना (कार्डियोमेगाली)",
        "finding_gu": "હૃદયનું કદ મોટું થવું (કાર્ડિયોમેગાલી)",
        "severity": "Medium",
        "explanation": "Enlarged cardiac silhouette seen on chest radiograph, often related to hypertension or cardiac strain.",
        "recommendation": "Echocardiogram (2D Echo) and ECG advised under cardiologist supervision."
    },
    {
        "pattern": r"(fracture|cortical break|displaced|undisplaced fracture|callus)",
        "finding": "Bone Fracture / Cortical Disruption",
        "finding_hi": "हड्डी में फ्रैक्चर / दरार",
        "finding_gu": "હાડકામાં ફ્રેક્ચર / તિરાડ",
        "severity": "High",
        "explanation": "Disruption or break in the continuity of bone cortex.",
        "recommendation": "Orthopedic consultation for immobilization (splint/cast) and pain management."
    },
    {
        "pattern": r"(degenerative|osteophyte|joint space narrowing|spondylosis|reduced disc space)",
        "finding": "Degenerative Changes / Spondylosis",
        "finding_hi": "हड्डियों व जोड़ों में उम्र संबंधी घिसावट",
        "finding_gu": "સાંધા અને કરોડરજ્જુનો ઘસારો",
        "severity": "Low",
        "explanation": "Wear-and-tear changes in joints or vertebrae with narrowing and bone spur formation.",
        "recommendation": "Physical therapy, core strengthening, posture correction, and supportive joint care."
    },
    {
        "pattern": r"(clear lung fields|no focal lesion|normal cardiac size|unremarkable|within normal limits)",
        "finding": "Normal / Unremarkable Findings",
        "finding_hi": "सामान्य रिपोर्ट (कोई बड़ी असामान्यता नहीं)",
        "finding_gu": "સામાન્ય રિપોર્ટ",
        "severity": "Normal",
        "explanation": "No acute bony or soft tissue abnormalities identified on this radiograph.",
        "recommendation": "Routine clinical follow-up as advised by your healthcare provider."
    }
]

class XRayReportAnalyzer:
    """Parses X-Ray textual impressions and reports."""
    def analyze_report_text(self, report_text: str, user_lang: str = "en") -> dict:
        if not report_text or not report_text.strip():
            return {"findings": [], "overall_status": "No text provided", "has_abnormality": False}

        text_lower = report_text.lower()
        detected_findings = []
        has_abnormality = False
        highest_severity = "Normal"
        for item in XRAY_FINDING_PATTERNS:
            if re.search(item["pattern"], text_lower):
                sev = item["severity"]
                if sev != "Normal":
                    has_abnormality = True
                
                if sev == "High":
                    highest_severity = "High"
                elif sev == "Medium" and highest_severity != "High":
                    highest_severity = "Medium"

                disp_name = item["finding"]
                if user_lang == "hi":
                    disp_name = item["finding_hi"]
                elif user_lang == "gu":
                    disp_name = item["finding_gu"]

                detected_findings.append({
                    "name": disp_name,
                    "english_name": item["finding"],
                    "severity": sev,
                    "explanation": item["explanation"],
                    "recommendation": item["recommendation"]
                })

        return {
            "findings": detected_findings,
            "has_abnormality": has_abnormality,
            "overall_severity": highest_severity,
            "total_findings": len(detected_findings)
        }

xray_analyzer = XRayReportAnalyzer()
