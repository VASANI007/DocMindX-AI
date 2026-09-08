"""
    DocMindX AI - Clinical Symptom Triage & Condition Assessment Engine
Powered by 100+ Official India Major Diseases Dataset, ICD-10/11 Knowledge Graph, and Generative AI Fallback.
"""
import os
import re
import json
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")

def normalize_id(item_id, prefix="D"):
    if not item_id or pd.isna(item_id):
        return ""
    s = str(item_id).strip().upper()
    try:
        clean = s.replace(prefix, "")
        return f"{prefix}{int(clean):04d}"
    except Exception:
        return s

class SymptomTriageEngine:
    def __init__(self):
        self.load_datasets()

    def load_datasets(self):
        symptoms_path = os.path.join(DATASETS_DIR, "symptoms", "symptoms_master.csv")
        diseases_path = os.path.join(DATASETS_DIR, "disease", "disease_master.csv")
        major_diseases_path = os.path.join(DATASETS_DIR, "disease", "india_major_diseases.csv")
        mappings_path = os.path.join(DATASETS_DIR, "disease", "disease_symptom_mapping.csv")
        red_flags_path = os.path.join(DATASETS_DIR, "symptoms", "emergency_red_flags.csv")
        guidance_path = os.path.join(DATASETS_DIR, "diet", "condition_guidance.csv")
        yoga_path = os.path.join(DATASETS_DIR, "yoga", "yoga_guidance.csv")
        physio_path = os.path.join(DATASETS_DIR, "physiotherapy", "physiotherapy_guidance.csv")

        self.df_symptoms = pd.read_csv(symptoms_path, encoding="utf-8") if os.path.exists(symptoms_path) else pd.DataFrame()
        self.df_diseases = pd.read_csv(diseases_path, encoding="utf-8") if os.path.exists(diseases_path) else pd.DataFrame()
        self.df_major_diseases = pd.read_csv(major_diseases_path, encoding="utf-8") if os.path.exists(major_diseases_path) else pd.DataFrame()
        self.df_mappings = pd.read_csv(mappings_path, encoding="utf-8") if os.path.exists(mappings_path) else pd.DataFrame()
        self.df_red_flags = pd.read_csv(red_flags_path, encoding="utf-8") if os.path.exists(red_flags_path) else pd.DataFrame()
        self.df_guidance = pd.read_csv(guidance_path, encoding="utf-8") if os.path.exists(guidance_path) else pd.DataFrame()
        self.df_yoga = pd.read_csv(yoga_path, encoding="utf-8") if os.path.exists(yoga_path) else pd.DataFrame()
        self.df_physio = pd.read_csv(physio_path, encoding="utf-8") if os.path.exists(physio_path) else pd.DataFrame()

        # Standardize IDs
        if not self.df_diseases.empty and "disease_id" in self.df_diseases.columns:
            self.df_diseases["disease_id"] = self.df_diseases["disease_id"].apply(lambda x: normalize_id(x, "D"))
        if not self.df_mappings.empty:
            if "disease_id" in self.df_mappings.columns:
                self.df_mappings["disease_id"] = self.df_mappings["disease_id"].apply(lambda x: normalize_id(x, "D"))
            if "symptom_id" in self.df_mappings.columns:
                self.df_mappings["symptom_id"] = self.df_mappings["symptom_id"].apply(lambda x: normalize_id(x, "S"))
        if not self.df_symptoms.empty and "symptom_id" in self.df_symptoms.columns:
            self.df_symptoms["symptom_id"] = self.df_symptoms["symptom_id"].apply(lambda x: normalize_id(x, "S"))
        if not self.df_red_flags.empty and "symptom_id" in self.df_red_flags.columns:
            self.df_red_flags["symptom_id"] = self.df_red_flags["symptom_id"].apply(lambda x: normalize_id(x, "S"))

    def check_red_flags(self, selected_symptom_ids):
        """
        Check if any selected symptoms trigger emergency red flag protocols.
        """
        if self.df_red_flags.empty or not selected_symptom_ids:
            return []

        norm_symptom_ids = [normalize_id(sid, "S") for sid in selected_symptom_ids]
        matched_flags = self.df_red_flags[self.df_red_flags["symptom_id"].isin(norm_symptom_ids)]
        return matched_flags.to_dict(orient="records")

    def _evaluate_via_ai(self, symptoms_list: List[str], patient_history: dict, lang_code: str = "en") -> Optional[dict]:
        """Dynamic Generative AI triage fallback for novel or complex medical queries."""
        if not GEMINI_API_KEY and not GROQ_API_KEY:
            return None

        syms_str = ", ".join(symptoms_list)
        lang_label = "Hindi" if lang_code == "hi" else ("Gujarati" if lang_code == "gu" else "English")
        
        prompt = f"""
You are DocMindX Clinical AI. Analyze this patient profile:
Reported Symptoms: {syms_str}
Age: {patient_history.get('age_group', 'Adult')}, Gender: {patient_history.get('gender', 'Male')}
Duration: {patient_history.get('duration', '3-5 Days')}, Severity: {patient_history.get('severity', 'Moderate')}

Provide clinical differential assessment strictly in valid JSON format:
{{
  "urgency_level": "Moderate Attention (Consult Physician)",
  "is_emergency": false,
  "ranked_conditions": [
    {{
      "disease_id": "AI_DIAG_01",
      "name": "Primary Clinical Condition Name",
      "name_hi": "प्राथमिक स्थिति का नाम",
      "name_gu": "પ્રાથમિક સ્થિતિનું નામ",
      "category": "Clinical Category",
      "icd_code": "ICD-10 Code",
      "match_percentage": 88,
      "description": "Comprehensive clinical overview and pathophysiology.",
      "specialist": "Medical Specialist to consult",
      "guidance": {{
        "diet_summary": "Recommended dietary modifications",
        "foods_to_avoid": "Foods or habits to avoid",
        "key_precautions": "Clinical precautions and when to seek urgent emergency care"
      }}
    }}
  ],
  "tests_to_discuss": ["Complete Blood Count (CBC)", "Diagnostic Test 2", "Imaging Test 3"]
}}
Translate condition names and guidance to {lang_label}.
"""
        # Try Gemini
        if GEMINI_API_KEY:
            for model in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-2.5-flash"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                    res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}}, timeout=10)
                    if res.status_code == 200:
                        raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                        if match:
                            return json.loads(match.group(0))
                except Exception:
                    pass

        # Try Groq
        if GROQ_API_KEY:
            try:
                headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                body = {"model": "qwen/qwen3.6-27b", "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=5)
                if res.status_code == 200:
                    content = res.json()["choices"][0]["message"]["content"]
                    match = re.search(r"\{.*\}", content, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
            except Exception:
                pass

        return None

    def evaluate_symptoms(self, selected_symptom_ids, age_group="21–30", gender="Male", duration="3–5 Days", existing_conditions=None, symptom_names=None, chief_condition=None):
        """
        Evaluates symptoms against both India 100+ Major Diseases dataset and weighted bipartite knowledge graph.
        """
        norm_symptom_ids = [normalize_id(sid, "S") for sid in (selected_symptom_ids or [])]
        symptom_names = symptom_names or []
        existing_conditions = existing_conditions or {}

        # 1. Red flag triage
        red_flags = self.check_red_flags(norm_symptom_ids)
        is_emergency = len(red_flags) > 0

        ranked_conditions = []
        matched_disease_ids = set()

        # 2. Check 100+ Major Indian Diseases
        if not self.df_major_diseases.empty:
            s_names_lower = [s.lower().strip() for s in symptom_names]
            
            for _, d_row in self.df_major_diseases.iterrows():
                d_id = str(d_row.get("disease_id", ""))
                d_name = str(d_row.get("disease_name", ""))
                d_cat = str(d_row.get("category", ""))
                
                # Check gender exclusions
                gen_lower = str(gender).lower()
                if "male" in gen_lower and "female" not in gen_lower:
                    if any(kw in (d_name + " " + d_cat).lower() for kw in ["breast", "cervical", "ovarian", "maternal", "pregnancy"]):
                        if "breast" not in d_name.lower(): # Men can get breast cancer rarely, but skip others
                            continue
                elif "female" in gen_lower:
                    if "prostate" in d_name.lower() or "testicular" in d_name.lower():
                        continue

                # Parse symptoms
                raw_syms = d_row.get("symptoms", [])
                if isinstance(raw_syms, str):
                    try:
                        d_syms = eval(raw_syms) if raw_syms.startswith("[") else [s.strip() for s in raw_syms.split(",")]
                    except Exception:
                        d_syms = [s.strip() for s in raw_syms.split(",")]
                else:
                    d_syms = list(raw_syms) if isinstance(raw_syms, (list, tuple)) else []

                # Count matches
                overlap_count = 0
                for ds in d_syms:
                    ds_lower = ds.lower()
                    if any(ds_lower in sn or sn in ds_lower for sn in s_names_lower):
                        overlap_count += 1

                # If explicit chief condition matches this disease
                is_chief_match = False
                if chief_condition:
                    c_lower = str(chief_condition).lower()
                    if d_name.lower() in c_lower or c_lower in d_name.lower() or str(d_row.get("disease_name_hi", "")).lower() in c_lower:
                        is_chief_match = True

                if is_chief_match or overlap_count >= 1:
                    match_pct = 95 if is_chief_match else min(92, max(45, round((overlap_count / max(len(d_syms), 1)) * 100 + 35)))
                    
                    tests_list = d_row.get("tests", [])
                    if isinstance(tests_list, str):
                        try:
                            tests_list = eval(tests_list) if tests_list.startswith("[") else [t.strip() for t in tests_list.split(",")]
                        except Exception:
                            tests_list = [t.strip() for t in tests_list.split(",")]

                    guidance = {
                        "diet_summary": str(d_row.get("diet", "Wholesome, balanced, clean diet.")),
                        "foods_to_avoid": "Ultra-processed foods, deep fried snacks, excessive sodium and sugar.",
                        "key_precautions": f"Consult {d_row.get('specialist', 'a physician')} for definitive diagnostic evaluation."
                    }

                    if "emergency" in str(d_row.get("urgency", "")).lower() or "critical" in str(d_row.get("urgency", "")).lower():
                        is_emergency = True

                    ranked_conditions.append({
                        "disease_id": d_id,
                        "name": d_name,
                        "name_hi": str(d_row.get("disease_name_hi", d_name)),
                        "name_gu": str(d_row.get("disease_name_gu", d_name)),
                        "icd_code": str(d_row.get("icd_code", "N/A")),
                        "category": d_cat,
                        "category_icon": str(d_row.get("category_icon", "")),
                        "specialist": str(d_row.get("specialist", "General Physician")),
                        "urgency": str(d_row.get("urgency", "Urgent Clinical Attention")),
                        "description": f"Official National Priority Condition ({d_row.get('priority', 'High')} Priority) under MoHFW guidelines.",
                        "match_percentage": match_pct,
                        "matched_symptoms_count": overlap_count,
                        "guidance": guidance,
                        "tests": tests_list,
                        "yoga": [],
                        "physiotherapy": []
                    })
                    matched_disease_ids.add(d_id)

        # 3. Traditional Bipartite Graph Knowledge Base
        scores = {}
        disease_matched_symptoms = {}
        if not self.df_mappings.empty and norm_symptom_ids:
            matched_mappings = self.df_mappings[self.df_mappings["symptom_id"].isin(norm_symptom_ids)]
            for _, row in matched_mappings.iterrows():
                d_id = row["disease_id"]
                weight = row["weight"]
                is_req = row.get("required", "No") == "Yes"
                if d_id not in scores:
                    scores[d_id] = 0
                    disease_matched_symptoms[d_id] = []
                scores[d_id] += weight * (1.6 if is_req else 1.0)
                disease_matched_symptoms[d_id].append(row["symptom_id"])

            for d_id, total_score in scores.items():
                if d_id in matched_disease_ids:
                    continue
                disease_info = self.df_diseases[self.df_diseases["disease_id"] == d_id]
                if disease_info.empty:
                    continue
                d_row = disease_info.iloc[0]
                all_mappings = self.df_mappings[self.df_mappings["disease_id"] == d_id]
                max_w = all_mappings["weight"].sum() if not all_mappings.empty else 1.0
                matched_cnt = len(disease_matched_symptoms[d_id])
                
                match_percentage = min(92, max(38, round(((total_score / max(max_w, 1.0)) * 0.65 + (matched_cnt / max(len(all_mappings), 1.0)) * 0.35) * 100)))

                ranked_conditions.append({
                    "disease_id": d_id,
                    "name": str(d_row["disease_name"]),
                    "name_hi": str(d_row.get("disease_name_hi", d_row["disease_name"])),
                    "name_gu": str(d_row.get("disease_name_gu", d_row["disease_name"])),
                    "icd_code": str(d_row.get("icd_code", "N/A")),
                    "category": str(d_row.get("category", "General Medicine")),
                    "category_icon": "",
                    "specialist": "General Physician / Specialist",
                    "urgency": "Moderate Attention (Consult Physician)",
                    "description": str(d_row.get("description", "Consult a physician for clinical diagnosis.")),
                    "match_percentage": match_percentage,
                    "matched_symptoms_count": matched_cnt,
                    "guidance": {},
                    "tests": ["Complete Blood Count (CBC)", "Serum Chemistry Panel"],
                    "yoga": [],
                    "physiotherapy": []
                })

        # 4. If no conditions matched locally, invoke Dynamic Generative AI Fallback
        if not ranked_conditions and (symptom_names or norm_symptom_ids):
            ai_res = self._evaluate_via_ai(symptom_names or ["Unspecified Symptoms"], {"age_group": age_group, "gender": gender, "duration": duration})
            if ai_res and ai_res.get("ranked_conditions"):
                return {
                    "is_emergency": bool(ai_res.get("is_emergency", False)),
                    "red_flags": red_flags,
                    "urgency_level": ai_res.get("urgency_level", "Moderate Attention"),
                    "ranked_conditions": ai_res.get("ranked_conditions", []),
                    "tests_to_discuss": ai_res.get("tests_to_discuss", ["Complete Blood Count (CBC)", "Consult Specialist"])
                }

        # Sort ranked conditions
        ranked_conditions.sort(key=lambda x: x["match_percentage"], reverse=True)

        # Determine overall urgency
        if is_emergency:
            urgency = "Critical / Urgent Medical Attention"
        elif any(c["match_percentage"] > 75 for c in ranked_conditions):
            urgency = "Moderate Attention (Consult Physician)"
        else:
            urgency = "Mild / Self-Monitoring"

        # Compile tests to discuss
        all_tests = []
        for rc in ranked_conditions[:3]:
            for t in rc.get("tests", []):
                if t not in all_tests:
                    all_tests.append(t)
        if not all_tests:
            all_tests = ["Complete Blood Count (CBC)", "Basic Metabolic Panel", "Consult Specialist"]

        return {
            "is_emergency": is_emergency,
            "red_flags": red_flags,
            "urgency_level": urgency,
            "ranked_conditions": ranked_conditions[:6],
            "tests_to_discuss": all_tests[:5]
        }

    def evaluate_triage(self, reported_symptom_ids, patient_history=None, symptom_names=None, chief_condition=None):
        """
        Adapter method called by the main Streamlit clinical portal.
        """
        patient_history = patient_history or {}
        return self.evaluate_symptoms(
            selected_symptom_ids=reported_symptom_ids,
            age_group=patient_history.get("age_group", "21-30"),
            gender=patient_history.get("gender", "Male"),
            duration=patient_history.get("duration", "1-3 Days"),
            existing_conditions=patient_history.get("conditions", {}),
            symptom_names=symptom_names or patient_history.get("symptom_names", []),
            chief_condition=chief_condition or patient_history.get("chief_condition")
        )

# Global singleton instance
triage_engine = SymptomTriageEngine()
