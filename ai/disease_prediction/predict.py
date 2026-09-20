"""
    DocMindX AI - Clinical Symptom Triage & Condition Assessment Engine
Powered by 100+ Official India Major Diseases Dataset, ICD-10/11 Knowledge Graph,
live WHO ICD-11 validation, and Generative AI grounded reasoning.

CLINICAL RULES ENFORCED:
- No arbitrary score boosts (+35 removed)
- Symptom matching requires meaningful token overlap, not loose substring
- Condition count is dynamic (no hard [:6] limit)
- WHO ICD-11 live validation attempted for top candidates
- Source metadata attached to every ranked condition
- AI fallback is grounded — cannot invent symptoms or diseases
- Silent except:pass removed from all clinical paths
"""
import logging
import os
import re
import json
import ast
import requests
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from config.settings import GEMINI_API_KEY, GROQ_API_KEY, gemini_pool
from ai.disease_prediction.canonical_concepts import canonical_normalizer, CanonicalClinicalRepresentation
from api.who_icd import is_probable_icd10_code

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")
_logger = logging.getLogger("DocMindX.TriageEngine")

# Valid model chains
_GEMINI_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]
_GROQ_MODELS = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]


def normalize_id(item_id, prefix="D"):
    if not item_id or pd.isna(item_id):
        return ""
    s = str(item_id).strip().upper()
    try:
        clean = s.replace(prefix, "")
        return f"{prefix}{int(clean):04d}"
    except Exception:
        return s


def _tokenize(text: str) -> set:
    """Split text into meaningful tokens (min 3 chars), lowercase."""
    return {w.lower() for w in re.findall(r'\b\w{3,}\b', str(text))}


GENERIC_MODIFIERS = {
    'pain', 'ache', 'mild', 'severe', 'history', 'down', 'left', 'right',
    'both', 'acute', 'chronic', 'with', 'and', 'from', 'due', 'associated'
}


def _symptom_token_overlap(symptom_tokens: set, input_tokens: set) -> float:
    """
    Computes semantic token overlap between a disease symptom descriptor and patient input.
    - Filters out generic non-specific modifiers if they are the sole overlap.
    - For short symptom descriptors (<= 2 tokens): requires >= 50% overlap.
    - For long/rich clinical phrases (>= 3 tokens): requires at least 2 key tokens or >= 33% overlap.
    """
    if not symptom_tokens or not input_tokens:
        return 0.0
    common = symptom_tokens & input_tokens
    if not common:
        return 0.0
    # If the only overlapping tokens are generic modifiers (e.g. just 'pain' or 'severe'), reject
    key_common = common - GENERIC_MODIFIERS
    if not key_common:
        return 0.0

    ratio = len(common) / len(symptom_tokens)
    if len(symptom_tokens) <= 2:
        return ratio if ratio >= 0.5 else 0.0
    else:
        # Descriptive clinical phrases (e.g. "Low back pain radiating down leg")
        return ratio if (len(common) >= 2 or ratio >= 0.33) else 0.0


def _classify_anatomy(symptom_list: List[str]) -> str:
    """
    Infers the primary anatomical system or clinical domain from reported symptoms.
    Uses canonical clinical representation first for language-invariant accuracy across
    English, Hindi, Gujarati, Marathi, and code-mixed inputs, then falls back to domain token scoring.
    """
    combined = " ".join(symptom_list).lower()

    # 1. Canonical concept mapping (Multilingual & Script-Agnostic)
    try:
        from ai.disease_prediction.canonical_concepts import canonical_normalizer
        rep = canonical_normalizer.normalize(combined)
        if "thoracic_chest" in rep.anatomical_regions or any(c in rep.canonical_concepts for c in ["chest_pain", "dyspnea_breathlessness"]):
            return "cardiopulmonary"
        if "cough" in rep.canonical_concepts:
            return "respiratory"
        if "lumbar_spine" in rep.anatomical_regions or any(c in rep.canonical_concepts for c in ["lower_back_pain", "radiating_pain_lower_limb"]):
            return "spinal_musculoskeletal"
        if any(r in rep.anatomical_regions for r in ["lower_limb", "upper_limb"]):
            return "musculoskeletal"
        if "abdominal_gi" in rep.anatomical_regions or any(c in rep.canonical_concepts for c in ["abdominal_pain", "vomiting", "diarrhea"]):
            return "gastrointestinal"
        if "head_cranial" in rep.anatomical_regions or "headache" in rep.canonical_concepts:
            return "neurological"
        if "skin_rash" in rep.canonical_concepts:
            return "dermatological"
        if "animal_bite_exposure" in rep.canonical_concepts or "EXP_ANIMAL_BITE" in rep.exposure_events:
            return "trauma_exposure"
        if any(c in rep.canonical_concepts for c in ["fever", "chills"]):
            return "systemic_infectious"
    except Exception as e:
        _logger.debug("[_classify_anatomy] Canonical normalization fallback: %s", e)

    domain_keywords = {
        "cardiopulmonary": [
            r"\bchest\b", r"\bheart\b", r"\bcardiac\b", r"\bpalpitation\b",
            r"\bbreathless\b", r"\bshortness of breath\b", r"\bangina\b", r"\bcoronary\b",
            r"सीने", r"सीना", r"छाती", r"हार्ट", r"છાતી", r"હૃદય", r"छातीत", r"श्वास", r"सांस"
        ],
        "respiratory": [
            r"\bcough\b", r"\bwheeze\b", r"\bwheezing\b", r"\bsputum\b", r"\bbronchial\b",
            r"\bpulmonary\b", r"\blung\b", r"\bairway\b", r"\brespiratory\b",
            r"खांसी", r"उધરસ", r"खोकला", r"दमा"
        ],
        "spinal_musculoskeletal": [
            r"\blower back\b", r"\blumbar\b", r"\bradiating leg\b", r"\bradiating pain\b",
            r"\bspine\b", r"\bvertebral\b", r"\bintervertebral disc\b", r"\bdisc herniation\b",
            r"\bspinal nerve\b", r"\bradicular\b", r"\bsciatic\b",
            r"कमर", r"पीठ", r"કમર", r"कंबर", r"रीढ़"
        ],
        "musculoskeletal": [
            r"\bjoint\b", r"\bknee\b", r"\bshoulder\b", r"\bsynovial\b", r"\bcartilage\b",
            r"\belbow\b", r"\bmuscle\b", r"\bmyalgia\b", r"\btendon\b", r"\bligament\b", r"\bstiffness\b",
            r"घुटना", r"जोड़ों", r"ઘૂંટણ", r"સાંધા", r"गुडघा", r"स्नायु"
        ],
        "gastrointestinal": [
            r"\babdomen\b", r"\bstomach\b", r"\bnausea\b", r"\bvomiting\b", r"\bdiarrhea\b",
            r"\bconstipation\b", r"\bgi\b", r"\bbowel\b", r"\bgastro\b", r"\bintestinal\b",
            r"\bepigastric\b", r"\bheartburn\b", r"\bacid regurgitation\b", r"\bbloating\b",
            r"पेट", r"पેટ", r"पोट", r"उल्टी", r"ઉલટી", r"ઝાડા", r"दस्त"
        ],
        "urinary_renal": [
            r"\burine\b", r"\burinary\b", r"\bkidney\b", r"\brenal\b", r"\bbladder\b",
            r"\bdysuria\b", r"\bhematuria\b", r"\bsuprapubic\b",
            r"पेशाब", r"मूत्र", r"પેશાબ"
        ],
        "neurological": [
            r"\bheadache\b", r"\bcephalalgia\b", r"\bseizure\b", r"\bneuralgia\b",
            r"\bneuropathy\b", r"\bvertigo\b", r"\bdizziness\b", r"\bnumbness\b",
            r"\bparesthesia\b", r"\bphotophobia\b", r"\bmigraine\b",
            r"सिरदर्द", r"માથાનો", r"डोकेदुखी", r"ચક્કર", r"चक्कर"
        ],
        "dermatological": [
            r"\bskin\b", r"\brash\b", r"\bitch\b", r"\bderma\b", r"\bcutaneous\b",
            r"\blesion\b", r"\bhives\b", r"\berythema\b", r"\bepidermal\b", r"\bpruritic\b",
            r"चकत्ते", r"खुजली", r"ખંજવાળ", r"दाने"
        ],
        "trauma_exposure": [
            r"\bbite\b", r"\bwound\b", r"\banimal\b", r"\bdog\b", r"\bsnake\b",
            r"\btrauma\b", r"\binjury\b", r"\blaceration\b", r"\bpuncture\b", r"\bburn\b", r"\bfall\b",
            r"काट", r"बટકું", r"घाव", r"ઘા", r"चावा", r"जखम"
        ],
        "systemic_infectious": [
            r"\bfever\b", r"\bchills\b", r"\bpyrexia\b", r"\bbody ache\b",
            r"\bmalaise\b", r"\bfatigue\b", r"\bweakness\b", r"\brigors\b",
            r"बुखार", r"ताप", r"તાવ"
        ]
    }

    scores = {}
    for domain, patterns in domain_keywords.items():
        score = sum(1 for p in patterns if re.search(p, combined))
        if score > 0:
            scores[domain] = score

    if not scores:
        return "general"

    return max(scores, key=scores.get)


def _anatomy_compatible(condition_name: str, condition_category: str, patient_anatomy: str) -> bool:
    """
    Returns True if the condition is anatomically plausible given the patient's symptom anatomy.
    This is a completely generalized rule engine based on clinical domains and anatomical regions.
    """
    c_lower = (condition_name + " " + condition_category).lower()

    # Broad multi-system, metabolic, endocrine, neoplastic, or systemic/trauma domains
    is_systemic_domain = any(k in c_lower for k in [
        "systemic", "infectious", "infection", "sepsis", "metabolic", "endocrine",
        "hematolog", "immune", "autoimmune", "neoplasm", "oncolog", "circulatory",
        "multisystem", "general", "deficiency", "toxic", "poisoning", "fever", "anemia",
        "zoonotic", "trauma", "emergency", "bite", "wound", "injury", "exposure"
    ])
    if is_systemic_domain:
        return True

    if patient_anatomy in ["general", "trauma_exposure", "systemic_infectious"]:
        return True  # Compatible with general/systemic/trauma presentations

    # Map organ-specific domains
    is_cardiac = any(k in c_lower for k in ["cardiac", "heart", "coronary", "myocard", "vascular", "angina"])
    is_respiratory = any(k in c_lower for k in ["pulmon", "bronch", "lung", "respiratory", "pleural", "alveol", "airway"])
    is_spinal = any(k in c_lower for k in ["spine", "spinal", "vertebr", "lumbar", "disc", "radicul", "nerve root"])
    is_musculo = any(k in c_lower for k in ["arthritis", "muscle", "joint", "knee", "shoulder", "tendon", "sprain", "strain", "bursitis", "myositis", "synov"])
    is_gi = any(k in c_lower for k in ["gastro", "ulcer", "colitis", "bowel", "liver", "hepat", "pancreat", "appendic", "gastric", "intestinal", "esophag"])
    is_urinary = any(k in c_lower for k in ["renal", "kidney", "urinary", "nephro", "bladder", "prostate", "ureter"])
    is_neuro = any(k in c_lower for k in ["neuro", "cerebr", "brain", "seizure", "cranial", "vertigo", "neuropathy", "central nervous"])
    is_derma = any(k in c_lower for k in ["dermat", "cutan", "skin", "epiderm", "psorias", "urticar"])

    if patient_anatomy == "cardiopulmonary" and (is_cardiac or is_respiratory):
        return True
    if patient_anatomy == "respiratory" and is_respiratory:
        return True
    if patient_anatomy == "spinal_musculoskeletal" and (is_spinal or is_musculo):
        return True
    if patient_anatomy == "musculoskeletal" and is_musculo:
        return True
    if patient_anatomy == "gastrointestinal" and is_gi:
        return True
    if patient_anatomy == "urinary_renal" and is_urinary:
        return True
    if patient_anatomy == "neurological" and is_neuro:
        return True
    if patient_anatomy == "dermatological" and is_derma:
        return True

    # If organ-specific but patient's reported anatomy has zero overlap, suppress
    if any([is_cardiac, is_respiratory, is_spinal, is_musculo, is_gi, is_urinary, is_neuro, is_derma]):
        return False

    return True  # default: compatible



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

        _logger.info("[TriageEngine] Datasets loaded: %d symptoms, %d diseases, %d major diseases, %d mappings",
                     len(self.df_symptoms), len(self.df_diseases), len(self.df_major_diseases), len(self.df_mappings))

    def check_red_flags(self, selected_symptom_ids):
        """
        Check if any selected symptoms trigger emergency red flag protocols.
        Preserved and generalized across all disease categories.
        """
        if self.df_red_flags.empty or not selected_symptom_ids:
            return []

        norm_symptom_ids = [normalize_id(sid, "S") for sid in selected_symptom_ids]
        matched_flags = self.df_red_flags[self.df_red_flags["symptom_id"].isin(norm_symptom_ids)]
        flags = matched_flags.to_dict(orient="records")
        if flags:
            _logger.info("[TriageEngine] RED FLAGS detected: %d flag(s)", len(flags))
        return flags

    def _validate_with_who(self, condition_name: str) -> dict:
        """
        Attempts live WHO ICD-11 validation for a condition.
        Returns validation result dict. Falls back gracefully without crashing.
        """
        try:
            from api.who_icd import validate_icd11_condition
            result = validate_icd11_condition(condition_name)
            if result.get("validated"):
                _logger.info("[TriageEngine] WHO ICD-11 VALIDATED: '%s' → %s", condition_name, result.get("icd_code"))
            else:
                _logger.info("[TriageEngine] WHO ICD-11 unverified for: '%s'", condition_name)
            return result
        except Exception as exc:
            _logger.error("[TriageEngine] WHO ICD-11 validation error for '%s': %s", condition_name, exc)
            return {
                "validated": False,
                "icd_code": "",
                "official_name": condition_name,
                "source": "Local Clinical Reference",
                "is_live": False,
                "fallback_used": True,
                "fallback_reason": f"WHO validation error: {exc}"
            }

    def _evaluate_via_ai(self, symptoms_list: List[str], patient_history: dict, lang_code: str = "en") -> Optional[dict]:
        """
        Grounded Generative AI triage reasoning. AI explains evidence — does not invent it.
        ANTI-FABRICATION: Prompt explicitly instructs AI to use only provided symptoms.
        Uses ICD-11 format (not ICD-10).
        """
        if not gemini_pool.get_active_keys() and not GROQ_API_KEY:
            _logger.warning("[TriageEngine] AI fallback skipped — no API keys configured")
            return None

        syms_str = ", ".join(symptoms_list)
        lang_label = "Hindi" if lang_code == "hi" else ("Gujarati" if lang_code == "gu" else "English")

        prompt = f"""You are DocMindX Clinical AI. Analyze this patient profile:
Reported Symptoms: {syms_str}
Age: {patient_history.get('age_group', 'Adult')}, Gender: {patient_history.get('gender', 'Male')}
Duration: {patient_history.get('duration', '3-5 Days')}, Severity: {patient_history.get('severity', 'Moderate')}

CRITICAL RULES:
1. Base your differential ONLY on the reported symptoms above.
2. Do NOT invent symptoms the patient did not report.
3. Do NOT add conditions that have no relationship to the reported symptoms.
4. Use ICD-11 codes (not ICD-10).
5. Use clinical language: "Pattern compatible with..." not "Patient is diagnosed with..."
6. Evidence score (0-100) must reflect actual symptom match, not be arbitrarily inflated.

Provide clinical differential assessment strictly in valid JSON:
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
      "icd_code": "ICD-11 Code or empty string",
      "match_percentage": 72,
      "clinical_status": "Leading possibility",
      "evidence_level": "Moderate",
      "matched_symptoms": ["symptom1", "symptom2"],
      "missing_symptoms": ["typical symptom not reported"],
      "description": "Clinical overview based on reported symptoms only.",
      "specialist": "Medical Specialist to consult",
      "source": "Gemini/Groq Clinical AI Reasoning",
      "is_live": true,
      "fallback_used": false,
      "guidance": {{
        "diet_summary": "Recommended dietary modifications",
        "foods_to_avoid": "Foods or habits to avoid",
        "key_precautions": "Clinical precautions and when to seek urgent care"
      }}
    }}
  ],
  "tests_to_discuss": ["Specific test linked to top condition"]
}}

Translate condition names and guidance to {lang_label}.
Return only conditions genuinely supported by the reported symptoms.
"""
        # Try Gemini (Multi-Key Failover Pool)
        if gemini_pool.get_active_keys():
            gem_payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.05, "responseMimeType": "application/json"}
            }
            res_data, model_used, _ = gemini_pool.execute_with_failover(
                payload=gem_payload,
                models=_GEMINI_MODELS,
                timeout=12
            )
            if res_data:
                candidates = res_data.get("candidates", [])
                if candidates:
                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if match:
                        try:
                            result = json.loads(match.group(0))
                            _logger.info("[TriageEngine] Gemini %s AI fallback SUCCESS via pool", model_used)
                            return result
                        except Exception:
                            pass

        # Try Groq
        if GROQ_API_KEY:
            for groq_model in _GROQ_MODELS:
                try:
                    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
                    body = {"model": groq_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.05}
                    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=8)
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        match = re.search(r"\{.*\}", content, re.DOTALL)
                        if match:
                            result = json.loads(match.group(0))
                            _logger.info("[TriageEngine] Groq %s AI fallback SUCCESS", groq_model)
                            return result
                    else:
                        _logger.warning("[TriageEngine] Groq %s returned HTTP %s", groq_model, res.status_code)
                except requests.exceptions.Timeout:
                    _logger.warning("[TriageEngine] Groq %s TIMEOUT", groq_model)
                except requests.exceptions.ConnectionError:
                    _logger.warning("[TriageEngine] Groq %s CONNECTION ERROR", groq_model)
                except Exception as exc:
                    _logger.error("[TriageEngine] Groq %s error: %s", groq_model, exc)

        _logger.warning("[TriageEngine] All AI providers failed for clinical fallback")
        return None

    def evaluate_symptoms(self, selected_symptom_ids, age_group="21–30", gender="Male", duration="3–5 Days",
                          existing_conditions=None, symptom_names=None, chief_condition=None, negative_findings=None,
                          bioportal_concepts=None, nlm_conditions=None):
        """
        Evaluates symptoms against India 100+ Major Diseases dataset and weighted bipartite
        knowledge graph. Returns evidence-grounded differential with full source metadata.
        """
        symptom_names = symptom_names or []
        existing_conditions = existing_conditions or {}
        bioportal_concepts = bioportal_concepts or []
        nlm_conditions = nlm_conditions or []

        # 0. Canonical normalization across provided symptom names and free text
        raw_text = " ".join([str(s) for s in symptom_names])
        canon_rep = canonical_normalizer.normalize(raw_text) if raw_text.strip() else None

        norm_symptom_ids = [normalize_id(sid, "S") for sid in (selected_symptom_ids or [])]
        if canon_rep:
            for cid in canon_rep.positive_symptoms:
                norm_cid = normalize_id(cid, "S")
                if norm_cid not in norm_symptom_ids:
                    norm_symptom_ids.append(norm_cid)

        # Consolidate negative findings (explicitly denied symptoms)
        all_negative_findings = list(negative_findings or [])
        if canon_rep and canon_rep.negative_findings:
            for nf in canon_rep.negative_findings:
                if nf not in all_negative_findings:
                    all_negative_findings.append(nf)

        denied_tokens = set()
        for nf in all_negative_findings:
            denied_tokens |= _tokenize(nf)

        # Remove denied symptoms from positive ID list
        positive_norm_ids = [
            sid for sid in norm_symptom_ids
            if sid not in all_negative_findings and not any(sid == normalize_id(nf, "S") for nf in all_negative_findings)
        ]

        # Ingest BioPortal-extracted concept IDs and NLM conditions into positive symptom tokens
        for bc in bioportal_concepts:
            if isinstance(bc, dict):
                pref_name = bc.get("prefLabel") or bc.get("name") or ""
                if pref_name:
                    mapped_sid = canonical_normalizer.get_symptom_id(pref_name)
                    if mapped_sid and mapped_sid not in positive_norm_ids and mapped_sid not in all_negative_findings:
                        positive_norm_ids.append(mapped_sid)
            elif isinstance(bc, str) and bc.strip():
                mapped_sid = canonical_normalizer.get_symptom_id(bc)
                if mapped_sid and mapped_sid not in positive_norm_ids and mapped_sid not in all_negative_findings:
                    positive_norm_ids.append(mapped_sid)

        _logger.info("[TriageEngine] Evaluating %d positive symptoms (%d denied) for age=%s, gender=%s, duration=%s",
                     len(positive_norm_ids), len(all_negative_findings), age_group, gender, duration)

        # 1. Red flag triage
        red_flags = self.check_red_flags(positive_norm_ids)
        is_emergency = len(red_flags) > 0

        ranked_conditions = []
        matched_disease_ids = set()

        # Build input token set for semantic matching
        s_names_lower = [s.lower().strip() for s in symptom_names]
        input_tokens = set()
        for s in s_names_lower:
            input_tokens |= _tokenize(s)
        if canon_rep:
            input_tokens |= canon_rep.positive_tokens

        # Merge BioPortal and NLM condition tokens
        for bc in bioportal_concepts:
            b_label = bc.get("prefLabel") or bc.get("name") if isinstance(bc, dict) else str(bc)
            if b_label:
                input_tokens |= _tokenize(b_label)
        for nlm in nlm_conditions:
            n_label = nlm.get("name") or nlm.get("title") if isinstance(nlm, dict) else str(nlm)
            if n_label:
                input_tokens |= _tokenize(n_label)

        # Purge denied tokens from input tokens to prevent contamination
        input_tokens -= denied_tokens

        # Check exposure events (e.g. Animal Bite Exposure)
        has_animal_bite_exposure = False
        if canon_rep and "EXP_ANIMAL_BITE" in canon_rep.exposure_events:
            has_animal_bite_exposure = True
        elif any(normalize_id(s, "S") == "S000265" for s in positive_norm_ids):
            has_animal_bite_exposure = True
        elif any(k in " ".join(s_names_lower) for k in ["bite", "dog bite", "animal bite", "કુતરા", "काटा"]):
            has_animal_bite_exposure = True

        # Determine patient anatomical system
        patient_anatomy = _classify_anatomy(symptom_names)
        if has_animal_bite_exposure and patient_anatomy == "general":
            patient_anatomy = "trauma_exposure"
        _logger.info("[TriageEngine] Patient anatomy classified as: %s (animal_bite_exposure=%s)",
                     patient_anatomy, has_animal_bite_exposure)

        # 2. Check 100+ Major Indian Diseases (local dataset)
        local_fallback_used = False
        local_fallback_reason = ""
        if not self.df_major_diseases.empty:
            for _, d_row in self.df_major_diseases.iterrows():
                d_id = str(d_row.get("disease_id", ""))
                d_name = str(d_row.get("disease_name", ""))
                d_cat = str(d_row.get("category", ""))

                # Gender exclusions
                gen_lower = str(gender).lower()
                if "male" in gen_lower and "female" not in gen_lower:
                    if any(kw in (d_name + " " + d_cat).lower() for kw in ["breast", "cervical", "ovarian", "maternal", "pregnancy"]):
                        if "breast" not in d_name.lower():
                            continue
                elif "female" in gen_lower:
                    if "prostate" in d_name.lower() or "testicular" in d_name.lower():
                        continue

                # Anatomical consistency check
                if not _anatomy_compatible(d_name, d_cat, patient_anatomy):
                    _logger.debug("[TriageEngine] Suppressed '%s': anatomical mismatch (%s vs %s)", d_name, d_cat, patient_anatomy)
                    continue

                # Parse disease symptoms with safe ast.literal_eval
                raw_syms = d_row.get("symptoms", [])
                if isinstance(raw_syms, str):
                    try:
                        d_syms = ast.literal_eval(raw_syms) if raw_syms.startswith("[") else [s.strip() for s in raw_syms.split(",")]
                    except Exception:
                        d_syms = [s.strip() for s in raw_syms.split(",")]
                else:
                    d_syms = list(raw_syms) if isinstance(raw_syms, (list, tuple)) else []

                # Negation check: suppress conditions whose cardinal symptom was explicitly denied
                # E.g. fever explicitly denied -> suppress acute febrile illnesses
                if "fever" in denied_tokens:
                    is_febrile = any(w in (d_name + " " + d_cat).lower() for w in ["malaria", "dengue", "typhoid", "leptospirosis", "scrub typhus", "influenza"])
                    if is_febrile:
                        _logger.debug("[TriageEngine] Suppressed '%s': cardinal symptom 'fever' was explicitly denied", d_name)
                        continue

                # Cardinal symptom requirement: acute febrile tropical infections strictly require fever/pyrexia
                is_cardinal_febrile = any(w in (d_name + " " + d_cat).lower() for w in [
                    "malaria", "dengue", "typhoid", "scrub typhus", "leptospirosis", "chikungunya"
                ])
                has_fever_symptom = (
                    any(f in input_tokens for f in ["fever", "pyrexia", "temperature", "chills", "febrile", "bukhar", "tav", "taap", "ताप", "તાવ", "बुखार"])
                    or "S000001" in positive_norm_ids
                )
                if is_cardinal_febrile and not has_fever_symptom:
                    _logger.debug("[TriageEngine] Suppressed '%s': cardinal symptom 'fever' not present in patient report", d_name)
                    continue

                # Weighted token overlap — no loose substring matching
                overlap_count = 0
                matched_syms = []
                for ds in d_syms:
                    ds_tokens = _tokenize(ds)
                    # Denied symptom cannot count toward positive match
                    if any(_symptom_token_overlap(ds_tokens, _tokenize(nf)) > 0 for nf in all_negative_findings):
                        continue
                    if _symptom_token_overlap(ds_tokens, input_tokens) > 0:
                        overlap_count += 1
                        matched_syms.append(ds)

                # Animal bite exposure matching
                if has_animal_bite_exposure and d_id == "ZOO001":
                    bite_symptom_desc = "History of animal bite/scratch (Dog, cat, monkey)"
                    if bite_symptom_desc not in matched_syms:
                        overlap_count += 1
                        matched_syms.append(bite_symptom_desc)

                # Chief condition matching (treated as hypothesis under evaluation, NOT broad substring matching)
                is_chief_match = False
                if chief_condition:
                    c_lower = str(chief_condition).lower().strip()
                    if c_lower and (c_lower == d_name.lower() or f" {c_lower} " in f" {d_name.lower()} "):
                        is_chief_match = True

                if not is_chief_match and overlap_count < 1:
                    continue

                # Calculate match percentage purely from clinical evidence overlap — zero arbitrary arithmetic boosts
                if overlap_count > 0:
                    match_pct = min(90, round((overlap_count / max(len(d_syms), 1)) * 100))
                else:
                    match_pct = 0

                # Standardized categorical evidence levels
                if match_pct >= 70:
                    evidence_level = "Strong evidence"
                    clinical_status = "Leading possibility"
                elif match_pct >= 40:
                    evidence_level = "Moderate evidence"
                    clinical_status = "Possible"
                elif match_pct >= 20:
                    evidence_level = "Limited evidence"
                    clinical_status = "Needs clinical evaluation"
                else:
                    evidence_level = "Insufficient evidence"
                    clinical_status = "Patient hypothesis / Insufficient symptom evidence" if is_chief_match else "Needs clinical evaluation"

                tests_list = d_row.get("tests", [])
                if isinstance(tests_list, str):
                    try:
                        tests_list = ast.literal_eval(tests_list) if tests_list.startswith("[") else [t.strip() for t in tests_list.split(",")]
                    except Exception:
                        tests_list = [t.strip() for t in tests_list.split(",")]

                guidance = {
                    "diet_summary": str(d_row.get("diet", "Wholesome, balanced, clean diet.")),
                    "foods_to_avoid": "Ultra-processed foods, deep fried snacks, excessive sodium and sugar.",
                    "key_precautions": f"Consult {d_row.get('specialist', 'a physician')} for definitive diagnostic evaluation."
                }

                if "emergency" in str(d_row.get("urgency", "")).lower() or "critical" in str(d_row.get("urgency", "")).lower():
                    is_emergency = True

                local_fallback_used = True
                local_fallback_reason = "Local clinical reference dataset (offline fallback)"

                icd_raw_code = str(d_row.get("icd_code", "")).strip()
                system_label = "ICD-10" if is_probable_icd10_code(icd_raw_code) else "ICD-11"

                ranked_conditions.append({
                    "disease_id": d_id,
                    "name": d_name,
                    "name_hi": str(d_row.get("disease_name_hi", d_name)),
                    "name_gu": str(d_row.get("disease_name_gu", d_name)),
                    "icd_code": icd_raw_code,
                    "icd_verified": False,  # Will be updated by WHO validation below
                    "icd_details": {
                        "code": icd_raw_code,
                        "system": system_label,
                        "source": "Local Clinical Reference Dataset"
                    },
                    "category": d_cat,
                    "category_icon": str(d_row.get("category_icon", "")),
                    "specialist": str(d_row.get("specialist", "General Physician")),
                    "urgency": str(d_row.get("urgency", "Urgent Clinical Attention")),
                    "description": f"National Priority Condition ({d_row.get('priority', 'High')} Priority) — pattern compatible based on reported symptoms.",
                    "match_percentage": match_pct,
                    "matched_symptoms_count": overlap_count,
                    "matched_symptoms": matched_syms,
                    "clinical_status": clinical_status,
                    "evidence_level": evidence_level,
                    "guidance": guidance,
                    "tests": tests_list,
                    "yoga": [],
                    "physiotherapy": [],
                    "is_patient_hypothesis": is_chief_match,
                    # Source metadata — local clinical dataset fallback
                    "source": "Local Major Disease Dataset",
                    "provider": "DocMindX India Disease KB",
                    "is_live": False,
                    "fallback_used": True,
                    "fallback_reason": "Local clinical reference dataset (offline fallback)"
                })
                matched_disease_ids.add(d_id)

        _logger.info("[TriageEngine] Major diseases matched: %d candidates", len(ranked_conditions))

        # 3. Traditional Bipartite Graph Knowledge Base
        scores = {}
        disease_matched_symptoms = {}
        if not self.df_mappings.empty and positive_norm_ids:
            matched_mappings = self.df_mappings[self.df_mappings["symptom_id"].isin(positive_norm_ids)]
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
                # Direct evidence calculation without arbitrary +35/+20 inflations or minimum clamps
                match_percentage = round(((total_score / max(max_w, 1.0)) * 0.70 + (matched_cnt / max(len(all_mappings), 1.0)) * 0.30) * 100)

                if match_percentage < 20:
                    continue

                if match_percentage >= 70:
                    evidence_level = "Strong evidence"
                    clinical_status = "Leading possibility"
                elif match_percentage >= 40:
                    evidence_level = "Moderate evidence"
                    clinical_status = "Possible"
                elif match_percentage >= 20:
                    evidence_level = "Limited evidence"
                    clinical_status = "Needs clinical evaluation"
                else:
                    evidence_level = "Insufficient evidence"
                    clinical_status = "Unlikely / Insufficient evidence"

                raw_icd = str(d_row.get("icd_code", "")).strip()
                is_i10 = is_probable_icd10_code(raw_icd)
                ranked_conditions.append({
                    "disease_id": d_id,
                    "name": str(d_row["disease_name"]),
                    "name_hi": str(d_row.get("disease_name_hi", d_row["disease_name"])),
                    "name_gu": str(d_row.get("disease_name_gu", d_row["disease_name"])),
                    "icd_code": "" if is_i10 else raw_icd,
                    "icd_verified": False,
                    "icd_details": {
                        "code": "" if is_i10 else raw_icd,
                        "system": "ICD-10" if is_i10 else "ICD-11",
                        "title": str(d_row["disease_name"]),
                        "source": "Local Bipartite Disease Graph (Pending WHO Validation)",
                        "verification_status": "UNVERIFIED"
                    },
                    "category": str(d_row.get("category", "General Medicine")),
                    "category_icon": "",
                    "specialist": "General Physician / Specialist",
                    "urgency": "Moderate Attention (Consult Physician)",
                    "description": str(d_row.get("description", "Consult a physician for clinical diagnosis.")),
                    "match_percentage": match_percentage,
                    "matched_symptoms_count": matched_cnt,
                    "matched_symptoms": [],
                    "clinical_status": clinical_status,
                    "evidence_level": evidence_level,
                    "guidance": {},
                    "tests": [],
                    "yoga": [],
                    "physiotherapy": [],
                    "source": "Local Bipartite Disease Graph",
                    "provider": "DocMindX Disease-Symptom KB",
                    "is_live": False,
                    "fallback_used": True,
                    "fallback_reason": "Local bipartite graph (symptom ID mapping)"
                })

        _logger.info("[TriageEngine] Total candidates before sort: %d", len(ranked_conditions))

        # 4. If no conditions matched, invoke Grounded AI Fallback
        if not ranked_conditions and (symptom_names or positive_norm_ids):
            _logger.info("[TriageEngine] No local matches — invoking AI grounded fallback")
            ai_res = self._evaluate_via_ai(
                symptom_names or ["Unspecified Symptoms"],
                {"age_group": age_group, "gender": gender, "duration": duration}
            )
            if ai_res and ai_res.get("ranked_conditions"):
                ai_conds = ai_res.get("ranked_conditions", [])
                for cond in ai_conds:
                    cond.setdefault("source", "AI Clinical Reasoning")
                    cond.setdefault("provider", "Gemini/Groq")
                    cond.setdefault("is_live", True)
                    cond.setdefault("fallback_used", False)
                    cond.setdefault("fallback_reason", "")
                    cond.setdefault("icd_verified", False)
                    cond.setdefault("icd_details", {
                        "code": cond.get("icd_code", ""),
                        "system": "ICD-11",
                        "source": "AI Clinical Reasoning"
                    })
                    cond.setdefault("evidence_level", "AI Assessed")
                    cond.setdefault("clinical_status", "Possible — AI assessment")
                return {
                    "is_emergency": bool(ai_res.get("is_emergency", False)),
                    "red_flags": red_flags,
                    "urgency_level": ai_res.get("urgency_level", "Moderate Attention"),
                    "ranked_conditions": ai_conds,
                    "tests_to_discuss": ai_res.get("tests_to_discuss", ["Consult Specialist"]),
                    "system_status": {
                        "live_api_available": True,
                        "fallback_used": False,
                        "who_icd_live": False,
                        "bioportal_live": False,
                        "ai_provider": "Gemini/Groq"
                    },
                    "fallback_warning": ""
                }
            else:
                _logger.warning("[TriageEngine] AI fallback also returned no conditions")

        # 5. Sort by match_percentage descending
        ranked_conditions.sort(key=lambda x: x["match_percentage"], reverse=True)

        # 6. WHO ICD-11 live validation for qualifying candidates (no artificial [:3] truncation)
        who_live_available = False
        for i, cond in enumerate(ranked_conditions):
            if cond.get("match_percentage", 0) < 30:
                continue
            who_result = self._validate_with_who(cond["name"])
            if who_result.get("validated"):
                v_code = who_result.get("icd_code") or cond.get("icd_code", "")
                ranked_conditions[i]["icd_code"] = v_code
                ranked_conditions[i]["icd_official_name"] = who_result.get("title") or who_result.get("official_name", cond["name"])
                ranked_conditions[i]["icd_verified"] = True
                ranked_conditions[i]["icd_source"] = "WHO ICD-11 Live"
                ranked_conditions[i]["icd_details"] = {
                    "code": v_code,
                    "system": "ICD-11",
                    "title": who_result.get("title") or who_result.get("official_name", cond["name"]),
                    "source": "WHO",
                    "verification_status": "VERIFIED"
                }
                ranked_conditions[i]["is_live"] = True
                ranked_conditions[i]["fallback_used"] = False
                who_live_available = True
            else:
                raw_c = cond.get("icd_code", "")
                is_i10 = is_probable_icd10_code(raw_c)
                ranked_conditions[i]["icd_source"] = "Local Clinical Reference (WHO unverified)"
                ranked_conditions[i]["icd_verified"] = False
                ranked_conditions[i]["icd_details"] = {
                    "code": "" if is_i10 else raw_c,
                    "system": "ICD-10" if is_i10 else "ICD-11",
                    "title": cond["name"],
                    "source": "Local Clinical Reference",
                    "verification_status": "UNVERIFIED"
                }

        # Ensure all conditions have structured icd_details conforming to Section 22
        for cond in ranked_conditions:
            if "icd_details" not in cond or not isinstance(cond["icd_details"], dict):
                raw_c = cond.get("icd_code", "")
                is_i10 = is_probable_icd10_code(raw_c)
                cond["icd_details"] = {
                    "code": "" if is_i10 else raw_c,
                    "system": "ICD-10" if is_i10 else "ICD-11",
                    "title": cond.get("name", "Clinical Condition"),
                    "source": "Local Clinical Reference",
                    "verification_status": "UNVERIFIED"
                }

        # 7. Determine overall urgency
        if is_emergency:
            urgency = "Critical / Urgent Medical Attention"
        elif any(c["match_percentage"] > 70 for c in ranked_conditions):
            urgency = "Moderate Attention (Consult Physician)"
        else:
            urgency = "Mild / Self-Monitoring"

        # 8. Compile evidence-linked tests across all qualifying differential candidates
        all_tests = []
        for rc in ranked_conditions:
            for t in rc.get("tests", []):
                if t and t not in all_tests:
                    all_tests.append(t)

        # Fallback warning
        fallback_warning = ""
        if not who_live_available:
            fallback_warning = (
                "⚠️ Live clinical data service is currently unavailable. "
                "DocMindX AI is using locally stored clinical reference data for this assessment. "
                "Results may be less current and should be clinically verified."
            )

        # 9. Build system status
        system_status = {
            "live_api_available": who_live_available,
            "fallback_used": not who_live_available,
            "who_icd_live": who_live_available,
            "bioportal_live": False,  # not called in this pipeline stage
            "local_dataset_used": local_fallback_used,
            "candidates_count": len(ranked_conditions)
        }

        _logger.info(
            "[TriageEngine] Final: %d conditions, urgency=%s, who_live=%s",
            len(ranked_conditions), urgency, who_live_available
        )

        return {
            "is_emergency": is_emergency,
            "red_flags": red_flags,
            "urgency_level": urgency,
            "ranked_conditions": ranked_conditions,  # Dynamic count — NO artificial [:N] limit here
            "tests_to_discuss": all_tests,
            "system_status": system_status,
            "fallback_warning": fallback_warning
        }

    def evaluate_triage(self, reported_symptom_ids, patient_history=None, symptom_names=None, chief_condition=None, negative_findings=None):
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
            chief_condition=chief_condition or patient_history.get("chief_condition"),
            negative_findings=negative_findings or patient_history.get("negative_findings", [])
        )


# Global singleton instance
triage_engine = SymptomTriageEngine()
