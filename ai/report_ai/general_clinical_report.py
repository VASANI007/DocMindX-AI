"""
    DocMindX AI — General Clinical Document & Medical Health Summary Analyzer
    Analyzes Clinical Health Summaries, Doctor Consultation Notes, Triage Reports,
    Discharge Summaries, and Other Medical Documents using Gemini Multi-Key Failover
    with robust local deterministic clinical parsing fallback.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional

from config.settings import gemini_pool, GROQ_API_KEY
from ai.report_ai.medical_verifier import verify_medical_document

_logger = logging.getLogger("DocMindX.ReportAI.GeneralClinical")


class GeneralClinicalDocumentAnalyzer:
    """
    Analyzes General Medical Documents, Clinical Health Summaries, Consultation Notes,
    Triage Assessments, and Medical Certificates.
    """

    def __init__(self):
        pass

    def parse_and_evaluate(
        self,
        raw_text: str,
        age_group: str = "Adult",
        gender: str = "Male",
        lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Parses general medical documents and extracts clinical findings,
        observations, patient profile, and triage status.
        """
        if not raw_text or len(raw_text.strip()) < 10:
            return {
                "is_valid_medical_report": False,
                "document_title": "Empty Document",
                "total_findings": 0,
                "abnormal_count": 0,
                "overall_severity": "Normal",
                "findings": [],
                "summary": "No readable clinical text detected in the uploaded file."
            }

        # 1. Verify that document is authentic medical
        v_res = verify_medical_document(raw_text, expected_type="general_medical")
        if not v_res.get("is_valid", True) and v_res.get("detected_type") == "non_medical":
            return {
                "is_valid_medical_report": False,
                "document_title": "Non-Medical Document",
                "total_findings": 0,
                "abnormal_count": 0,
                "overall_severity": "Unknown",
                "findings": [],
                "summary": "The uploaded file does not appear to be a medical document. No clinical parameters, diagnosis, or health summary detected."
            }

        lang_label = "Hindi" if lang == "hi" else ("Gujarati" if lang == "gu" else "English")

        prompt = f"""You are DocMindX Senior Medical Reviewer and Clinical Document Analyst.
Analyze the following authentic medical document / clinical health summary.
Extract structured clinical parameters, patient profile, clinical assessment, observations, and recommendations.

PATIENT PROFILE: Age: {age_group}, Gender: {gender}
LANGUAGE: Provide explanations and advice in {lang_label}.

DOCUMENT TEXT EXCERPT:
\"\"\"{raw_text[:2800]}\"\"\"

CRITICAL INSTRUCTIONS:
1. Extract ALL key clinical parameters, patient details, diagnoses, triage findings, vitals, and physician notes.
2. Return strictly valid JSON only with this EXACT schema:
{{
  "is_valid_medical_report": true,
  "document_title": "Descriptive title (e.g. Clinical Health Summary & Triage Report, Consultation Note, Discharge Summary)",
  "document_category": "Clinical Summary / Consultation / Health Assessment",
  "overall_severity": "Normal / Moderate / Severe / Critical",
  "summary": "2-3 sentence clinical overview of this document and patient status in {lang_label}",
  "findings": [
    {{
      "parameter": "Clinical Observation / Test Name (e.g. Assessed Severity, Blood Group, Symptom Duration, Primary Diagnosis, Vital Signs)",
      "observation": "Observed value or finding (e.g. Severe, O-, More than 2 Weeks, Lumbar Spondylosis)",
      "status": "Normal / Needs Attention / Severe / Documented / High Risk",
      "clinical_notes": "Clinical significance in {lang_label}",
      "action_advice": "Actionable medical recommendation for patient in {lang_label}"
    }}
  ]
}}
Do NOT output anything outside the JSON object."""

        # 2. Try Gemini Multi-Key Failover Pool
        if gemini_pool.get_active_keys():
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 2048,
                    "responseMimeType": "application/json"
                }
            }
            res_data, model_used, _ = gemini_pool.execute_with_failover(
                payload=payload,
                models=["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"],
                timeout=12
            )
            if res_data:
                candidates = res_data.get("candidates", [])
                if candidates:
                    raw_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    parsed = self._safe_parse_json(raw_out)
                    if parsed and parsed.get("findings"):
                        return self._format_result(parsed)

        # 3. Try Groq API Fallback
        if GROQ_API_KEY:
            try:
                import requests
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a senior clinical document analyst. Output strict JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1800,
                    "response_format": {"type": "json_object"}
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8)
                if res.status_code == 200:
                    raw_out = res.json()["choices"][0]["message"]["content"]
                    parsed = self._safe_parse_json(raw_out)
                    if parsed and parsed.get("findings"):
                        return self._format_result(parsed)
            except Exception as e:
                _logger.warning("Groq general clinical doc notice: %s", e)

        # 4. Deterministic Clinical Regex / Rule Fallback (100% Offline Resilient)
        return self._deterministic_fallback_parser(raw_text, lang_label)

    def _safe_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Safely parses JSON string with markdown stripping."""
        if not text:
            return None
        text = re.sub(r"^```json\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
        return None

    def _format_result(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures standard keys and calculates KPI counts."""
        findings = parsed.get("findings", [])
        abnormal_count = sum(
            1 for f in findings
            if f.get("status", "").lower() in ["needs attention", "severe", "high risk", "critical", "abnormal"]
        )
        overall_severity = parsed.get("overall_severity", "Normal")
        if abnormal_count > 0 and overall_severity == "Normal":
            overall_severity = "Needs Attention"

        return {
            "is_valid_medical_report": parsed.get("is_valid_medical_report", True),
            "document_title": parsed.get("document_title", "Clinical Health Summary & Assessment"),
            "document_category": parsed.get("document_category", "Clinical Summary"),
            "total_findings": len(findings),
            "abnormal_count": abnormal_count,
            "overall_severity": overall_severity,
            "findings": findings,
            "summary": parsed.get("summary", f"Detected {len(findings)} clinical observations and parameters.")
        }

    def _deterministic_fallback_parser(self, raw_text: str, lang_label: str) -> Dict[str, Any]:
        """
        Resilient rule-based extractor for structured clinical summaries,
        health cards, triage records, and doctor notes.
        """
        findings = []
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        # Common clinical key-value patterns
        patterns = [
            (r"assessed severity\s*[:\-]\s*(.+)", "Assessed Clinical Severity"),
            (r"symptom duration\s*[:\-]\s*(.+)", "Symptom Duration"),
            (r"blood group\s*[:\-]\s*(.+)", "Blood Group"),
            (r"age group\s*[:\-]\s*(.+)", "Patient Age Group"),
            (r"gender\s*[:\-]\s*(.+)", "Biological Gender"),
            (r"location\s*[:\-]\s*(.+)", "Patient Location"),
            (r"report id\s*[:\-]\s*(.+)", "Medical Report ID"),
            (r"primary (?:condition|diagnosis)\s*[:\-]\s*(.+)", "Primary Clinical Diagnosis"),
            (r"chief complaint\s*[:\-]\s*(.+)", "Chief Complaint / Reported Symptoms"),
            (r"symptoms\s*[:\-]\s*(.+)", "Reported Clinical Symptoms"),
            (r"blood pressure\s*[:\-]\s*(.+)", "Blood Pressure"),
            (r"pulse(?: rate)?\s*[:\-]\s*(.+)", "Pulse Rate"),
            (r"temperature\s*[:\-]\s*(.+)", "Body Temperature"),
            (r"oxygen saturation|spo2\s*[:\-]\s*(.+)", "Oxygen Saturation (SpO2)"),
            (r"provisional diagnosis\s*[:\-]\s*(.+)", "Provisional Diagnosis"),
            (r"impression\s*[:\-]\s*(.+)", "Clinical Impression"),
            (r"advice|recommendations?\s*[:\-]\s*(.+)", "Clinical Advice & Follow-up"),
        ]

        matched_params = set()
        for line in lines:
            line_lower = line.lower()
            for pattern, param_name in patterns:
                if param_name in matched_params:
                    continue
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    val = match.group(1).split("|")[0].strip()
                    if val and len(val) >= 1:
                        status = "Normal"
                        val_lower = val.lower()
                        if any(w in val_lower for w in ["severe", "critical", "acute", "high"]):
                            status = "Severe"
                        elif any(w in val_lower for w in ["moderate", "needs attention", "abnormal"]):
                            status = "Needs Attention"
                        else:
                            status = "Documented"

                        findings.append({
                            "parameter": param_name,
                            "observation": val,
                            "status": status,
                            "clinical_notes": f"Documented clinical value: {val}.",
                            "action_advice": "Review with physician during follow-up."
                        })
                        matched_params.add(param_name)

        # If key-value didn't match enough, extract major sentences as clinical notes
        if len(findings) < 2:
            for l in lines[:8]:
                if len(l) > 15 and not l.startswith("http") and not any(k in l.lower() for k in ["generated:", "page", "copyright"]):
                    findings.append({
                        "parameter": "Clinical Observation",
                        "observation": l[:60] + ("..." if len(l) > 60 else ""),
                        "status": "Documented",
                        "clinical_notes": l,
                        "action_advice": "Discuss observations with attending physician."
                    })

        abnormal_count = sum(1 for f in findings if f.get("status") in ["Needs Attention", "Severe"])
        overall_severity = "Severe" if any(f.get("status") == "Severe" for f in findings) else ("Needs Attention" if abnormal_count > 0 else "Normal")

        doc_title = "Clinical Health Summary & Triage Report" if "triage" in raw_text.lower() or "medimind" in raw_text.lower() or "docmindx" in raw_text.lower() else "General Medical Assessment Document"

        return {
            "is_valid_medical_report": len(findings) > 0,
            "document_title": doc_title,
            "document_category": "Clinical Health Summary",
            "total_findings": len(findings),
            "abnormal_count": abnormal_count,
            "overall_severity": overall_severity,
            "findings": findings,
            "summary": f"Identified {len(findings)} clinical parameters and observations from the medical document."
        }


general_clinical_analyzer = GeneralClinicalDocumentAnalyzer()
