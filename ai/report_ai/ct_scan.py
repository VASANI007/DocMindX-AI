"""
    DocMindX AI - Computed Tomography (CT Scan) Report Analyzer
Extracts radiological findings from Head, Chest (HRCT), and Abdominal CT scans.
"""
import re

CT_FINDING_PATTERNS = [
    {
        "pattern": r"(intracranial hemorrhage|subdural hematoma|extradural|bleed|hemorrhagic)",
        "finding": "Intracranial Hemorrhage / Acute Bleed",
        "finding_hi": "मस्तिष्क में रक्तस्राव (इंतराक्रेनियल ब्लीड)",
        "finding_gu": "મગજમાં રક્તસ્રાવ",
        "severity": "Emergency",
        "explanation": "Accumulation of blood within the brain tissue or surrounding cranial spaces.",
        "recommendation": "CRITICAL EMERGENCY: Immediate neurosurgical evaluation and ICU care required."
    },
    {
        "pattern": r"(ground glass opacity|ggo|corads|viral pneumonia|interstitial thickening)",
        "finding": "Ground Glass Opacities (GGO) / Pneumonitis",
        "finding_hi": "फेफड़ों में ग्राउंड ग्लास ओपेसिटी (निमोनिटिस)",
        "finding_gu": "ફેફસાંમાં ગ્રાઉન્ડ ગ્લાસ ઓપેસિટી",
        "severity": "High",
        "explanation": "Hazy opacity on lung CT scan signifying alveolar inflammation or fluid filling.",
        "recommendation": "Consult a pulmonologist; monitor oxygen saturation (SpO2) and clinical symptoms closely."
    },
    {
        "pattern": r"(appendicitis|inflamed appendix|periappendiceal fat stranding)",
        "finding": "Acute Appendicitis",
        "finding_hi": "तीव्र एपेंडिसाइटिस (एपेंडिक्स में सूजन)",
        "finding_gu": "એપેન્ડિક્સમાં સોજો (એપેન્ડિસાઇટિસ)",
        "severity": "High",
        "explanation": "Inflammation and swelling of the vermiform appendix in lower right abdomen.",
        "recommendation": "Urgent surgical consultation for potential laparoscopic appendectomy."
    },
    {
        "pattern": r"(calculus|calculi|nephrolithiasis|ureteric stone|hydronephrosis)",
        "finding": "Kidney / Ureteric Calculus with Hydronephrosis",
        "finding_hi": "गुर्दे या मूत्रनली में पथरी (किडनी स्टोन)",
        "finding_gu": "કિડની અથવા મૂત્રનળીમાં પથરી",
        "severity": "Medium",
        "explanation": "Mineral stone obstructing urinary flow causing swelling in the kidney.",
        "recommendation": "Urology review for hydration therapy, pain management, or lithotripsy."
    },
    {
        "pattern": r"(no acute abnormality|no significant abnormality|normal study|within normal limits)",
        "finding": "Unremarkable / Normal CT Study",
        "finding_hi": "सामान्य सीटी स्कैन रिपोर्ट",
        "finding_gu": "સામાન્ય સીટી સ્કેન રિપોર્ટ",
        "severity": "Normal",
        "explanation": "No acute structural pathology, mass effect, or focal lesion detected.",
        "recommendation": "Clinical correlation with your consulting physician."
    }
]

class CTScanAnalyzer:
    """
    Parses CT scan impressions.
    """
    def analyze_report_text(self, report_text: str, user_lang: str = "en") -> dict:
        if not report_text or not report_text.strip():
            return {"findings": [], "has_abnormality": False, "overall_severity": "Normal"}

        text_lower = report_text.lower()
        detected_findings = []
        has_abnormality = False
        highest_severity = "Normal"
        for item in CT_FINDING_PATTERNS:
            if re.search(item["pattern"], text_lower):
                sev = item["severity"]
                if sev != "Normal":
                    has_abnormality = True
                
                if sev == "Emergency":
                    highest_severity = "Emergency"
                elif sev == "High" and highest_severity != "Emergency":
                    highest_severity = "High"
                elif sev == "Medium" and highest_severity not in ["Emergency", "High"]:
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

ct_analyzer = CTScanAnalyzer()
