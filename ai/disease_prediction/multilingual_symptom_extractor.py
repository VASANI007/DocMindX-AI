"""
    Multilingual Natural Language Symptom & Disease Extraction Engine for DocMindX AI
Powered by Groq & Gemini Generative AI with resilient clinical knowledge base fallback (100+ Major Indian Diseases).
Supports English, Hindi, Gujarati, Hinglish, and other Indian languages.
"""
import os
import re
import json
import requests
import pandas as pd
from typing import Dict, Any, List, Optional
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")

def _safe_parse_json(text: str) -> Optional[dict]:
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass
    return None

class MultilingualSymptomExtractor:
    """
    Hybrid Generative AI (Groq & Gemini) + Clinical Knowledge Base Extractor.
    Understands free-form multilingual vernacular text (Hinglish, Hindi, Gujarati, English),
    identifies major Indian diseases, extracts clinical symptoms, and recommends evidence-based medications.
    """
    def __init__(self):
        self.symptoms_df = self._load_symptoms_df()
        self.major_diseases_df = self._load_major_diseases_df()
        self.id_lookup = self._build_id_lookup()
        self.disease_keyword_map = self._build_disease_keyword_map()

    def _load_symptoms_df(self) -> pd.DataFrame:
        csv_path = os.path.join(DATASETS_DIR, "symptoms", "symptoms_master.csv")
        if os.path.exists(csv_path):
            try:
                return pd.read_csv(csv_path, encoding="utf-8")
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    def _load_major_diseases_df(self) -> pd.DataFrame:
        csv_path = os.path.join(DATASETS_DIR, "disease", "india_major_diseases.csv")
        if os.path.exists(csv_path):
            try:
                return pd.read_csv(csv_path, encoding="utf-8")
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    def _build_id_lookup(self) -> Dict[str, str]:
        lookup = {}
        if not self.symptoms_df.empty:
            for _, row in self.symptoms_df.iterrows():
                sid = str(row.get("symptom_id", "")).strip().upper()
                name = str(row.get("symptom_name", "")).strip().lower()
                name_hi = str(row.get("symptom_name_hi", "")).strip().lower()
                name_gu = str(row.get("symptom_name_gu", "")).strip().lower()
                if sid:
                    lookup[name] = sid
                    if name_hi:
                        lookup[name_hi] = sid
                    if name_gu:
                        lookup[name_gu] = sid
        return lookup

    def _build_disease_keyword_map(self) -> List[Dict[str, Any]]:
        disease_entries = []
        if not self.major_diseases_df.empty:
            for _, row in self.major_diseases_df.iterrows():
                d_id = str(row.get("disease_id", ""))
                d_name = str(row.get("disease_name", ""))
                d_name_hi = str(row.get("disease_name_hi", ""))
                d_name_gu = str(row.get("disease_name_gu", ""))
                cat = str(row.get("category", ""))
                urgency = str(row.get("urgency", "Urgent Clinical Attention"))
                spec = str(row.get("specialist", "General Physician"))
                icd = str(row.get("icd_code", "N/A"))
                
                # Parse symptoms & medicines if list/str
                raw_syms = row.get("symptoms", [])
                if isinstance(raw_syms, str):
                    try:
                        syms = eval(raw_syms) if raw_syms.startswith("[") else [s.strip() for s in raw_syms.split(",")]
                    except Exception:
                        syms = [s.strip() for s in raw_syms.split(",")]
                else:
                    syms = list(raw_syms) if isinstance(raw_syms, (list, tuple)) else []

                raw_meds = row.get("medicines", [])
                if isinstance(raw_meds, str):
                    try:
                        meds = eval(raw_meds) if raw_meds.startswith("[") else [m.strip() for m in raw_meds.split(",")]
                    except Exception:
                        meds = [m.strip() for m in raw_meds.split(",")]
                else:
                    meds = list(raw_meds) if isinstance(raw_meds, (list, tuple)) else []

                keywords = set()
                keywords.add(d_name.lower())
                keywords.add(d_name_hi.lower())
                keywords.add(d_name_gu.lower())
                # Add individual words and variations
                for token in re.findall(r"[\w\u0900-\u097F\u0A80-\u0AFF]+", (d_name + " " + d_name_hi + " " + d_name_gu).lower()):
                    if len(token) >= 3 and token not in ["disease", "syndrome", "disorder", "acute", "chronic", "type"]:
                        keywords.add(token)

                disease_entries.append({
                    "disease_id": d_id,
                    "disease_name": d_name,
                    "disease_name_hi": d_name_hi,
                    "disease_name_gu": d_name_gu,
                    "category": cat,
                    "category_icon": str(row.get("category_icon", "")),
                    "icd_code": icd,
                    "specialist": spec,
                    "urgency": urgency,
                    "priority": str(row.get("priority", "High")),
                    "symptoms": syms,
                    "medicines": meds,
                    "diet": str(row.get("diet", "")),
                    "tests": row.get("tests", []),
                    "keywords": list(keywords)
                })
        return disease_entries

    def _find_matching_symptom_id(self, concept_name: str, fallback_id: str = ""):
        clean_name = str(concept_name).lower().strip()
        if clean_name in self.id_lookup:
            return self.id_lookup[clean_name], concept_name

        if not self.symptoms_df.empty:
            match = self.symptoms_df[self.symptoms_df["symptom_name"].str.lower().str.contains(clean_name, na=False)]
            if not match.empty:
                return match.iloc[0]["symptom_id"], match.iloc[0]["symptom_name"]

        return fallback_id or "S000001", concept_name

    def _extract_via_llm(self, user_text: str, user_lang: str = "en") -> Optional[dict]:
        """
        Uses Groq (Qwen) or Gemini REST API to understand complex multilingual medical text,
        detecting major diseases, clinical symptoms, and evidence-based medicine recommendations.
        """
        lang_label = "Hindi" if user_lang == "hi" else "Gujarati" if user_lang == "gu" else "English"
        
        prompt = f"""
You are DocMindX AI, an expert clinical triage engine for India. Analyze this patient input in any language (English/Hindi/Gujarati/Hinglish):
"{user_text}"

Task:
1. Detect if the user is mentioning or inquiring about a specific Major Disease or Health Condition (e.g. Blood Cancer / Leukemia, Breast Cancer, Heart Attack, Diabetes, Hypertension, Stroke, COPD, Tuberculosis, Dengue, Kidney Failure, Parkinson's, Epilepsy, Rabies, Snakebite, etc.).
2. Extract all key clinical symptoms associated with this condition or described by the patient.
3. Provide recommended first-line evidence-based medicines or emergency medical protocol for India.
4. Specify category, ICD-10 code, medical specialist, urgency level, and multilingual translations.

Respond strictly in valid JSON format:
{{
  "detected_disease": {{
    "name": "Leukemia (Blood Cancer)",
    "name_hi": "ब्लड कैंसर / ल्यूकेमिया",
    "name_gu": "બ્લડ કેન્સર (લ્યુકેમિયા)",
    "category": "Cancer & Oncology",
    "category_icon": "",
    "icd_code": "C95.9",
    "specialist": "Hematologist / Hemato-Oncologist",
    "urgency": "Critical / Urgent Hospitalization"
  }},
  "symptoms": [
    {{
      "concept": "Fever",
      "display_name": "बुखार (Fever)",
      "symptom_id": "S000001"
    }},
    {{
      "concept": "Severe Fatigue",
      "display_name": "गंभीर थकान (Severe Fatigue)",
      "symptom_id": "S000005"
    }},
    {{
      "concept": "Easy Bruising or Bleeding",
      "display_name": "आसानी से चोट या खून बहना (Easy Bruising/Bleeding)",
      "symptom_id": "S000014"
    }},
    {{
      "concept": "Frequent Infections",
      "display_name": "बार-बार संक्रमण (Frequent Infections)",
      "symptom_id": "S000021"
    }},
    {{
      "concept": "Bone and Joint Pain",
      "display_name": "हड्डियों और जोड़ों में दर्द (Bone Pain)",
      "symptom_id": "S000011"
    }}
  ],
  "medicines": [
    {{
      "for_symptom": "Supportive Care / Fever",
      "medicine_name": "Paracetamol 650mg",
      "brand_examples": "Dolo 650, Calpol",
      "indication": "Symptomatic fever and mild body ache relief",
      "dosage": "1 tablet after meals (max 3/day)",
      "warnings": "Avoid self-medicating with NSAIDs/Aspirin without blood counts.",
      "type": "Supportive OTC"
    }}
  ],
  "is_emergency": true,
  "clinical_summary": "Patient indicated symptoms or diagnosis consistent with Leukemia (Blood Cancer). Comprehensive hematological workup with Complete Blood Count and Bone Marrow Examination required."
}}

Translate display names to {lang_label}. Ensure high clinical precision.
"""

        # 1. Primary: Google Gemini Generative AI (3.5 Flash Lite / 3.6 Flash)
        if GEMINI_API_KEY:
            for gem_model in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{gem_model}:generateContent?key={GEMINI_API_KEY}"
                    gem_body = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
                    }
                    res_g = requests.post(url, json=gem_body, timeout=8)
                    if res_g.status_code == 200:
                        raw_text = res_g.json()["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = _safe_parse_json(raw_text)
                        if parsed and (parsed.get("symptoms") or parsed.get("detected_disease")):
                            return self._format_llm_result(parsed, user_lang)
                except Exception as e:
                    pass

        # 2. Secondary: Groq LLM Fallback
        if GROQ_API_KEY:
            for groq_model in ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]:
                try:
                    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                    body = {
                        "model": groq_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1
                    }
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=5)
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        parsed = _safe_parse_json(content)
                        if parsed and (parsed.get("symptoms") or parsed.get("detected_disease")):
                            return self._format_llm_result(parsed, user_lang)
                except Exception as e:
                    pass

        return None

    def _format_llm_result(self, parsed: dict, user_lang: str) -> dict:
        detected_items = []
        matched_symptom_ids = []
        matched_symptom_labels = []
        medication_list = parsed.get("medicines", [])
        is_emergency = bool(parsed.get("is_emergency", False))
        detected_disease = parsed.get("detected_disease")

        for sym in parsed.get("symptoms", []):
            concept = sym.get("concept", "Symptom")
            sid = sym.get("symptom_id")
            if not sid:
                sid, official_name = self._find_matching_symptom_id(concept)
            else:
                official_name = concept

            display_name = sym.get("display_name", concept)

            detected_items.append({
                "concept": concept,
                "icon": "",
                "symptom_id": sid,
                "official_name": official_name,
                "display_name": display_name,
                "category": "Clinical Symptom"
            })

            if sid not in matched_symptom_ids:
                matched_symptom_ids.append(sid)
            if official_name not in matched_symptom_labels:
                matched_symptom_labels.append(official_name)

        summary_text = parsed.get("clinical_summary", "")
        if not summary_text:
            d_name = detected_disease.get("name") if detected_disease else "Symptoms"
            summary_text = f"Identified condition '{d_name}' with {len(detected_items)} key clinical symptoms."

        return {
            "detected_disease": detected_disease,
            "detected_symptoms": detected_items,
            "symptom_ids": matched_symptom_ids,
            "symptom_labels": matched_symptom_labels,
            "recommended_medicines": medication_list,
            "is_emergency": is_emergency,
            "summary_text": summary_text,
            "source": "Online Generative AI (Groq / Gemini)"
        }

    def extract_symptoms_and_medicines(self, user_text: str, user_lang: str = "en") -> dict:
        """
        Parses free-text input via Online Generative LLM (Groq / Gemini) with
        instant local clinical disease & symptom knowledge graph fallback.
        """
        if not user_text or not isinstance(user_text, str) or not user_text.strip():
            return {
                "detected_disease": None,
                "detected_symptoms": [],
                "symptom_ids": [],
                "symptom_labels": [],
                "recommended_medicines": [],
                "is_emergency": False,
                "summary_text": "",
                "source": "Empty"
            }

        # 1. Primary: Try Online Generative AI (Groq / Gemini)
        llm_result = self._extract_via_llm(user_text, user_lang=user_lang)
        if llm_result and (llm_result.get("detected_symptoms") or llm_result.get("detected_disease")):
            return llm_result

        # 2. Resilient Offline Knowledge Graph Matching
        raw_text = user_text.lower().strip()
        clean_text = re.sub(r"[^\w\s\u0900-\u097F\u0A80-\u0AFF]", " ", raw_text)
        
        detected_disease = None
        detected_items = []
        matched_symptom_ids = []
        matched_symptom_labels = []
        medication_list = []
        is_emergency = False

        # Match against 100+ Major Diseases
        for d in self.disease_keyword_map:
            for kw in d["keywords"]:
                if kw in clean_text:
                    detected_disease = {
                        "disease_id": d["disease_id"],
                        "name": d["disease_name"],
                        "name_hi": d["disease_name_hi"],
                        "name_gu": d["disease_name_gu"],
                        "category": d["category"],
                        "category_icon": d["category_icon"],
                        "icd_code": d["icd_code"],
                        "specialist": d["specialist"],
                        "urgency": d["urgency"],
                        "priority": d["priority"],
                        "diet": d["diet"],
                        "tests": d["tests"]
                    }
                    if "critical" in d["urgency"].lower() or "emergency" in d["urgency"].lower():
                        is_emergency = True

                    # Populate symptoms from matched disease
                    for s_name in d["symptoms"]:
                        sid, off_name = self._find_matching_symptom_id(s_name)
                        if off_name not in matched_symptom_labels:
                            matched_symptom_labels.append(off_name)
                            matched_symptom_ids.append(sid)
                            detected_items.append({
                                "concept": off_name,
                                "icon": "",
                                "symptom_id": sid,
                                "official_name": off_name,
                                "display_name": off_name,
                                "category": d["category"]
                            })

                    # Populate medicines from matched disease
                    for med_str in d["medicines"]:
                        medication_list.append({
                            "for_symptom": d["disease_name"],
                            "medicine_name": med_str,
                            "indication": f"Clinical management of {d['disease_name']}",
                            "dosage": "As prescribed by physician",
                            "warnings": "Take only under clinical supervision",
                            "type": "Prescription / Clinical Protocol"
                        })
                    break
            if detected_disease:
                break

        # If no major disease matched, match individual symptom keywords from master
        if not detected_items and not self.symptoms_df.empty:
            for _, row in self.symptoms_df.iterrows():
                s_name = str(row.get("symptom_name", ""))
                s_hi = str(row.get("symptom_name_hi", ""))
                s_gu = str(row.get("symptom_name_gu", ""))
                sid = str(row.get("symptom_id", "S000001"))
                
                kws = [s_name.lower()]
                if s_hi:
                    kws.append(s_hi.lower())
                if s_gu:
                    kws.append(s_gu.lower())

                for kw in kws:
                    if kw in clean_text:
                        if s_name not in matched_symptom_labels:
                            matched_symptom_labels.append(s_name)
                            matched_symptom_ids.append(sid)
                            detected_items.append({
                                "concept": s_name,
                                "icon": "",
                                "symptom_id": sid,
                                "official_name": s_name,
                                "display_name": s_name,
                                "category": str(row.get("symptom_category", "General"))
                            })
                        break

        summary_text = ""
        if detected_disease:
            summary_text = f"Identified condition '{detected_disease['name']}' with {len(detected_items)} associated clinical symptoms."
        elif detected_items:
            summary_text = f"Identified {len(detected_items)} clinical symptoms: {', '.join(matched_symptom_labels[:4])}."

        return {
            "detected_disease": detected_disease,
            "detected_symptoms": detected_items,
            "symptom_ids": matched_symptom_ids,
            "symptom_labels": matched_symptom_labels,
            "recommended_medicines": medication_list,
            "is_emergency": is_emergency,
            "summary_text": summary_text,
            "source": "India Disease Master & Clinical Knowledge Graph"
        }

# Global singleton instance
symptom_extractor = MultilingualSymptomExtractor()
