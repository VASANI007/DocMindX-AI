"""
    Blood & Lab Test Report Analysis Engine
Powered by Gemini Vision / Groq AI with local lab reference range fallback.
"""
import os
import re
import json
import requests
import pandas as pd

from config.settings import GEMINI_API_KEY, GROQ_API_KEY
from ai.report_ai.medical_verifier import verify_medical_document

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")

class LabReportAnalyzer:
    def __init__(self):
        ref_path = os.path.join(DATASETS_DIR, "blood_report", "lab_test_reference.csv")
        self.df_ref = pd.read_csv(ref_path, encoding="utf-8") if os.path.exists(ref_path) else pd.DataFrame()

    def parse_and_evaluate(self, raw_text: str, age_group: str = "Adult", gender: str = "Male", lang: str = "en") -> dict:
        """
        Extract laboratory test parameters and evaluate against biological reference intervals.
        Uses Gemini / Groq AI first for complete clinical accuracy, with local regex fallback.
        """
        doc_eval = verify_medical_document(raw_text, expected_type="lab")
        if not doc_eval["is_valid"]:
            return {
                "is_valid_medical_report": False,
                "total_tests_detected": 0,
                "abnormal_count": 0,
                "findings": [],
                "summary": "The uploaded document does not appear to be a medical laboratory report. No clinical diagnostic test parameters were found."
            }

        # 1. Primary: Try Gemini / Groq Structured Extraction
        ai_res = self._evaluate_with_ai(raw_text, age_group, gender, lang)
        if ai_res is not None:
            return ai_res

        # 2. Resilient Regex & Dataset Fallback
        return self._evaluate_with_regex(raw_text, age_group, gender)

    def _evaluate_with_ai(self, raw_text: str, age_group: str, gender: str, lang: str) -> dict | None:
        prompt = f"""You are a clinical laboratory pathologist and diagnostic AI.
CRITICAL VALIDATION INSTRUCTION:
First, inspect the following extracted document text to determine if it is a genuine Medical Laboratory / Pathology / Diagnostic Report (e.g., Blood Test, CBC, LFT, KFT, Lipid Profile, Urine Examination, Thyroid panel).
If the document is NOT a medical lab report (for example, if it is a college letter, student project confirmation, resume, receipt, invoice, general letter, or non-medical document), return:
{{
  "is_medical_report": false,
  "summary": "The uploaded document is not a medical laboratory report. No clinical diagnostic test parameters were detected.",
  "findings": []
}}

If it IS a valid medical lab report:
1. Identify all genuine diagnostic test parameters actually present in the text (e.g. Hemoglobin, Total WBC, Platelets, Fasting Glucose, HbA1c, Creatinine, Bilirubin, SGPT, Cholesterol, Vitamin D3, Thyroid, etc.).
2. Extract the observed numerical value and unit. Do NOT invent or hallucinate parameters not present in the text.
3. Compare against standard biological reference ranges for an {age_group} {gender} patient.
4. Classify status as "Normal", "High", or "Low".
5. Provide a plain-language explanation and clinical advice.

REPORT TEXT:
\"\"\"{raw_text}\"\"\"

OUTPUT FORMAT:
Return strictly a valid JSON object matching this schema:
{{
  "is_medical_report": true,
  "summary": "Concise 1-2 sentence overall clinical summary.",
  "findings": [
    {{
      "test_name": "Parameter Name",
      "value": 12.5,
      "unit": "g/dL",
      "reference_range": "13.0 - 17.0 g/dL",
      "status": "Low / High / Normal",
      "explanation": "...",
      "action_advice": "..."
    }}
  ]
}}"""

        # Try Gemini API
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
                                is_med = parsed.get("is_medical_report", True)
                                findings = parsed.get("findings", [])
                                if not is_med or not findings:
                                    return {
                                        "is_valid_medical_report": False,
                                        "total_tests_detected": 0,
                                        "abnormal_count": 0,
                                        "findings": [],
                                        "summary": parsed.get("summary", "The uploaded document is not a medical laboratory report. No clinical parameters were detected.")
                                    }
                                
                                abnormal_count = sum(1 for item in findings if item.get("status") in ["Low", "High"])
                                return {
                                    "is_valid_medical_report": True,
                                    "total_tests_detected": len(findings),
                                    "abnormal_count": abnormal_count,
                                    "findings": findings,
                                    "summary": parsed.get("summary", "")
                                }
                except Exception as e:
                    print(f"Gemini report analyzer note ({model}): {e}")

        # Try Groq API
        if GROQ_API_KEY:
            for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]:
                try:
                    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                    body = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a clinical diagnostic pathologist. Return JSON only."},
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
                            is_med = parsed.get("is_medical_report", True)
                            findings = parsed.get("findings", [])
                            if not is_med or not findings:
                                return {
                                    "is_valid_medical_report": False,
                                    "total_tests_detected": 0,
                                    "abnormal_count": 0,
                                    "findings": [],
                                    "summary": parsed.get("summary", "The uploaded document is not a medical laboratory report. No clinical parameters were detected.")
                                }

                            abnormal_count = sum(1 for item in findings if item.get("status") in ["Low", "High"])
                            return {
                                "is_valid_medical_report": True,
                                "total_tests_detected": len(findings),
                                "abnormal_count": abnormal_count,
                                "findings": findings,
                                "summary": parsed.get("summary", "")
                            }
                except Exception as e:
                    print(f"Groq report analyzer note ({model}): {e}")

        return None

    def _evaluate_with_regex(self, raw_text: str, age_group: str, gender: str) -> dict:
        text_lower = raw_text.lower()

        # Check if text contains at least some medical lab or unit indicators
        medical_context_indicators = [
            "hemoglobin", "haemoglobin", "wbc", "leukocyte", "platelet", "glucose", "sugar",
            "creatinine", "bilirubin", "sgpt", "sgot", "alt", "ast", "cholesterol", "triglyceride",
            "thyroid", "tsh", "vitamin", "cbc", "lft", "kft", "lipid", "pathology", "g/dl",
            "mg/dl", "cells/mcl", "cells/cumm", "u/l", "ng/ml", "pg/ml", "reference interval"
        ]
        if not any(kw in text_lower for kw in medical_context_indicators):
            return {
                "is_valid_medical_report": False,
                "total_tests_detected": 0,
                "abnormal_count": 0,
                "findings": [],
                "summary": "No clinical laboratory parameters detected in this document. Please upload a genuine medical laboratory report."
            }

        results = []
        abnormal_count = 0
        
        # Test patterns: (display_name, regex_pattern, unit, (min_bio_val, max_bio_val))
        test_patterns = [
            ("Hemoglobin (Hb)", r"\b(?:hemoglobin|haemoglobin|hb)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:g/dl|gm/dl|g/l|%|\b)", "g/dL", (2.0, 25.0)),
            ("Total WBC Count", r"\b(?:wbc|total\s*(?:leukocyte|wbc)\s*count|tlc)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:cells/mcl|cells/cumm|/mcl|/cumm|/ul|k/ul|thou/mcl|\b)", "cells/mcL", (500.0, 100000.0)),
            ("Platelet Count", r"\b(?:platelet(?:s|\s*count)?|plt)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:lakh/mcl|/mcl|/cumm|/ul|k/ul|lakhs|\b)", "lakh/mcL", (0.1, 20.0)),
            ("Fasting Blood Sugar (FBS)", r"\b(?:fasting\s*blood\s*(?:sugar|glucose)|fbs|fasting\s*glucose)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl|mmol/l|\b)", "mg/dL", (20.0, 700.0)),
            ("Post Prandial Blood Sugar (PPBS)", r"\b(?:ppbs|post\s*prandial\s*(?:blood\s*)?(?:sugar|glucose)|pp\s*sugar)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl|mmol/l|\b)", "mg/dL", (20.0, 700.0)),
            ("HbA1c (Glycated Hemoglobin)", r"\b(?:hba1c|glycated\s*hemoglobin)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:%|\b)", "%", (2.0, 25.0)),
            ("Serum Creatinine", r"\b(?:creatinine|serum\s*creatinine)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl|\b)", "mg/dL", (0.1, 25.0)),
            ("Total Bilirubin", r"\b(?:total\s*bilirubin|bilirubin\s*total|serum\s*bilirubin)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl|\b)", "mg/dL", (0.1, 40.0)),
            ("SGPT / ALT (Alanine Aminotransferase)", r"\b(?:sgpt|alt)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:u/l|iu/l|\b)", "U/L", (2.0, 3000.0)),
            ("SGOT / AST (Aspartate Aminotransferase)", r"\b(?:sgot|ast)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:u/l|iu/l|\b)", "U/L", (2.0, 3000.0)),
            ("Serum Total Cholesterol", r"\b(?:total\s*cholesterol|cholesterol\s*total|serum\s*cholesterol)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl|\b)", "mg/dL", (30.0, 800.0)),
            ("Serum Triglycerides", r"\b(?:triglycerides|triglyceride)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl|\b)", "mg/dL", (20.0, 2000.0)),
            ("Thyroid Stimulating Hormone (TSH)", r"\b(?:tsh|thyroid\s*stimulating\s*hormone)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:uIU/ml|miu/l|uiu/ml|\b)", "uIU/mL", (0.01, 150.0)),
            ("Serum Vitamin D3 (25-OH)", r"\b(?:vitamin\s*d3?|vit\s*d3?|25-oh\s*vit(?:amin)?\s*d)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:ng/ml|\b)", "ng/mL", (1.0, 300.0)),
            ("Serum Vitamin B12", r"\b(?:vitamin\s*b12|vit\s*b12|b12)\b\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:pg/ml|\b)", "pg/mL", (20.0, 4000.0))
        ]

        for test_name, pattern, unit, (bio_min, bio_max) in test_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    val = float(match.group(1))

                    # Normalize WBC count if written in thousands (e.g. 7.5 meaning 7500)
                    if "WBC" in test_name and 2.0 <= val <= 30.0:
                        val = val * 1000.0

                    # Normalize Platelet count if given in raw counts (e.g. 250000)
                    if "Platelet" in test_name and val > 1000:
                        val = round(val / 100000.0, 2)

                    # Reject values that fall outside biological plausibility (false OCR artifacts / serial numbers)
                    if val < bio_min or val > bio_max:
                        continue
                        
                    ref_min, ref_max = self.get_reference_range(test_name, gender)
                    
                    status = "Normal"
                    explanation = ""
                    action_advice = ""
                    if val < ref_min:
                        status = "Low"
                        abnormal_count += 1
                        explanation = f"Value ({val} {unit}) is lower than typical reference range ({ref_min} - {ref_max} {unit})."
                        action_advice = self.get_low_advice(test_name)
                    elif val > ref_max:
                        status = "High"
                        abnormal_count += 1
                        explanation = f"Value ({val} {unit}) is higher than typical reference range ({ref_min} - {ref_max} {unit})."
                        action_advice = self.get_high_advice(test_name)
                    else:
                        status = "Normal"
                        explanation = f"Value ({val} {unit}) is within healthy reference range ({ref_min} - {ref_max} {unit})."
                        action_advice = "Maintain current healthy lifestyle habits."

                    results.append({
                        "test_name": test_name,
                        "value": val,
                        "unit": unit,
                        "reference_range": f"{ref_min} - {ref_max} {unit}",
                        "status": status,
                        "explanation": explanation,
                        "action_advice": action_advice
                    })
                except Exception:
                    continue

        if not results:
            return {
                "is_valid_medical_report": False,
                "total_tests_detected": 0,
                "abnormal_count": 0,
                "findings": [],
                "summary": "No clinical laboratory parameters detected in this document. Please upload a genuine medical laboratory report."
            }

        return {
            "is_valid_medical_report": True,
            "total_tests_detected": len(results),
            "abnormal_count": abnormal_count,
            "findings": results,
            "summary": f"Evaluated {len(results)} lab parameters. Found {abnormal_count} abnormal values."
        }

    def get_reference_range(self, test_name: str, gender: str = "Male"):
        if not self.df_ref.empty:
            match = self.df_ref[(self.df_ref["test_name"] == test_name) & (self.df_ref["sex"].isin([gender, "Both"]))]
            if not match.empty:
                return float(match.iloc[0]["reference_min"]), float(match.iloc[0]["reference_max"])
        return 0.0, 100.0

    def get_low_advice(self, test_name: str):
        low_map = {
            "Hemoglobin (Hb)": "May indicate nutritional anemia. Discuss iron, folate and vitamin B12 rich foods with doctor.",
            "Platelet Count": "Lower platelets require clinical attention. Avoid NSAID painkillers and consult physician.",
            "Serum Vitamin D3 (25-OH)": "Vitamin D deficiency is common. Consult doctor regarding D3 supplementation.",
            "Serum Vitamin B12": "Low B12 can cause fatigue and nerve numbness. Discuss supplements with physician."
        }
        return low_map.get(test_name, "Discuss this lower-than-normal result during your medical consultation.")

    def get_high_advice(self, test_name: str):
        high_map = {
            "Total WBC Count": "Elevated white cells indicate active immune response to infection.",
            "Fasting Blood Sugar (FBS)": "Elevated fasting sugar indicates prediabetes/diabetes risk. Consult physician.",
            "Post Prandial Blood Sugar (PPBS)": "High post-meal sugar indicates reduced insulin sensitivity.",
            "HbA1c (Glycated Hemoglobin)": "Reflects elevated average blood sugar over 3 months.",
            "Serum Creatinine": "High creatinine suggests reduced kidney filtration. Consult nephrologist/physician.",
            "Total Bilirubin": "Elevated bilirubin indicates jaundice or liver strain.",
            "SGPT / ALT (Alanine Aminotransferase)": "Elevated liver enzymes indicate liver strain. Avoid alcohol and heavy fats.",
            "Serum Total Cholesterol": "Elevated cholesterol increases cardiovascular risk. Switch to heart-healthy diet."
        }
        return high_map.get(test_name, "Discuss this elevated value with your doctor for clinical correlation.")
