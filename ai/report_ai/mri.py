"""
    DocMindX AI - Magnetic Resonance Imaging (MRI) Report Analyzer
Extracts radiological findings from Brain, Spine, and Musculoskeletal Joint MRI scans.
"""
import re

MRI_FINDING_PATTERNS = [
    {
        "pattern": r"(acute infarct|diffusion restriction|ischemic stroke|dwi bright)",
        "finding": "Acute Cerebral Infarction / Ischemic Stroke",
        "finding_hi": "मस्तिष्क में तीव्र इस्केमिक स्ट्रोक (रक्त प्रवाह रुकना)",
        "finding_gu": "મગજમાં ઇસ્કેમિક સ્ટ્રોક",
        "severity": "Emergency",
        "explanation": "Sudden loss of blood circulation to an area of the brain causing acute tissue ischemia.",
        "recommendation": "CRITICAL EMERGENCY: Immediate admission to a specialized Stroke / Neurology unit."
    },
    {
        "pattern": r"(disc herniation|disc bulge|disc extrusion|thecal sac compression|nerve root impingement)",
        "finding": "Intervertebral Disc Herniation / Nerve Compression",
        "finding_hi": "स्लिप डिस्क / नस पर दबाव (डिस्क हर्निएशन)",
        "finding_gu": "સ્લિપ ડિસ્ક / નસ દબાવી (હર્નિએશન)",
        "severity": "Medium",
        "explanation": "Displacement of intervertebral disc material pressing on spinal nerves or thecal sac.",
        "recommendation": "Spine specialist review, physiotherapy, core strengthening, and ergonomic posture management."
    },
    {
        "pattern": r"(meniscal tear|acl tear|cruciate ligament tear|mcl tear|ligamentous disruption)",
        "finding": "Ligament / Meniscal Tear (Joint Injury)",
        "finding_hi": "घुटने या जोड़ के लिगामेंट / मेनिस्कस में चोट या फटन",
        "finding_gu": "સાંધા અથવા લિગામેન્ટમાં ઈજા / ફાટી જવું",
        "severity": "Medium",
        "explanation": "Structural disruption of stabilizing ligaments or shock-absorbing cartilage.",
        "recommendation": "Orthopedic evaluation, joint rest (R.I.C.E. protocol), and physical therapy or arthroscopic review."
    },
    {
        "pattern": r"(normal brain parenchyma|no focal abnormality|unremarkable mri|normal study)",
        "finding": "Normal / Unremarkable MRI Study",
        "finding_hi": "सामान्य एमआरआई रिपोर्ट",
        "finding_gu": "સામાન્ય એમઆરઆઈ રિપોર્ટ",
        "severity": "Normal",
        "explanation": "No structural intracranial, spinal, or joint pathology detected on this sequence.",
        "recommendation": "Routine clinical follow-up as advised by your healthcare provider."
    }
]

class MRIReportAnalyzer:
    """
    Parses MRI scan impressions.
    """
    def analyze_report_text(self, report_text: str, user_lang: str = "en") -> dict:
        if not report_text or not report_text.strip():
            return {"findings": [], "has_abnormality": False, "overall_severity": "Normal"}

        text_lower = report_text.lower()
        detected_findings = []
        has_abnormality = False
        highest_severity = "Normal"
        for item in MRI_FINDING_PATTERNS:
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

mri_analyzer = MRIReportAnalyzer()
