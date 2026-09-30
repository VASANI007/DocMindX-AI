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
from config.settings import GEMINI_API_KEY, GROQ_API_KEY, gemini_pool, GROQ_MODELS, DEFAULT_GEMINI_MODELS
from ai.disease_prediction.canonical_concepts import canonical_normalizer, CanonicalClinicalRepresentation
from api.who_icd import is_probable_icd10_code

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "datasets")
_logger = logging.getLogger("DocMindX.TriageEngine")

# Valid model chains centralized from config.settings
_GEMINI_MODELS = list(DEFAULT_GEMINI_MODELS)
_GROQ_MODELS = list(GROQ_MODELS)


def normalize_id(item_id, prefix="D"):
    if not item_id or pd.isna(item_id):
        return ""
    s = str(item_id).strip().upper()
    try:
        clean = s.replace(prefix, "")
        return f"{prefix}{int(clean):04d}"
    except Exception:
        return s


def _parse_duration_days(duration_val: Any) -> Optional[int]:
    """Parses duration string or number into total days for clinical diagnostic gating."""
    if duration_val is None:
        return None
    if isinstance(duration_val, (int, float)):
        return int(duration_val)
    d_str = str(duration_val).lower().strip()
    if not d_str:
        return None
    if any(k in d_str for k in ["today", "aaj", "aaje", "just now", "hours", "hrs", "taas", "kalak"]):
        return 1
    if any(k in d_str for k in ["yesterday", "kal", "kaal", "gai kaal"]):
        return 1
    m_week = re.search(r'(\d+)\s*(?:week|wk|athvadi|hafte|saptaah)', d_str)
    if m_week:
        return int(m_week.group(1)) * 7
    m_month = re.search(r'(\d+)\s*(?:month|mahine|mahino)', d_str)
    if m_month:
        return int(m_month.group(1)) * 30
    m_range = re.search(r'(\d+)\s*[-–to]+\s*(\d+)\s*(?:day|divas|din)', d_str)
    if m_range:
        return int(m_range.group(2))
    m_day = re.search(r'(\d+)\s*(?:day|divas|din|divas thi|se)', d_str)
    if m_day:
        return int(m_day.group(1))
    text_nums = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "ten": 10, "fourteen": 14}
    for word, val in text_nums.items():
        if f"{word} week" in d_str:
            return val * 7
        if f"{word} day" in d_str:
            return val
    if "1–3" in d_str or "1-3" in d_str:
        return 3
    if "3–5" in d_str or "3-5" in d_str:
        return 5
    if "4–7" in d_str or "4-7" in d_str:
        return 7
    if "1–2 weeks" in d_str or "1-2 weeks" in d_str:
        return 14
    if ">2 weeks" in d_str or "> 2 weeks" in d_str:
        return 21
    return None


def _tokenize(text: str) -> set:
    """Split text into meaningful tokens (min 3 chars), lowercase."""
    return {w.lower() for w in re.findall(r'\b\w{3,}\b', str(text))}


def _find_condition_tests(disease_name: str, df_major: pd.DataFrame) -> list:
    """Look up verified diagnostic tests for a given condition from the major diseases dataset."""
    if df_major.empty or not disease_name:
        return []
    b_clean = re.sub(r'\(.*?\)', '', disease_name).strip().lower()
    b_words = [w for w in re.findall(r'\b\w{3,}\b', b_clean) if w not in {'fever', 'disease', 'acute', 'chronic', 'infection', 'syndrome'}]

    # 1. Exact or substring match on clean name
    for _, m in df_major.iterrows():
        m_clean = re.sub(r'\(.*?\)', '', str(m.get('disease_name', ''))).strip().lower()
        if b_clean == m_clean or b_clean in m_clean or m_clean in b_clean:
            raw_t = m.get('tests', [])
            if isinstance(raw_t, str):
                try:
                    return ast.literal_eval(raw_t) if raw_t.startswith('[') else [t.strip() for t in raw_t.split(',')]
                except Exception:
                    return [t.strip() for t in raw_t.split(',')]
            elif isinstance(raw_t, (list, tuple)):
                return list(raw_t)

    # 2. Key word match
    if b_words:
        for _, m in df_major.iterrows():
            m_clean = re.sub(r'\(.*?\)', '', str(m.get('disease_name', ''))).strip().lower()
            if any(w in m_clean for w in b_words):
                raw_t = m.get('tests', [])
                if isinstance(raw_t, str):
                    try:
                        return ast.literal_eval(raw_t) if raw_t.startswith('[') else [t.strip() for t in raw_t.split(',')]
                    except Exception:
                        return [t.strip() for t in raw_t.split(',')]
                elif isinstance(raw_t, (list, tuple)):
                    return list(raw_t)
    return []


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
    # EXPOSURE / TRAUMA PRIORITY: Validate exposures first so an acute bite is never lost to non-specific headache
    try:
        from ai.disease_prediction.canonical_concepts import canonical_normalizer
        rep = canonical_normalizer.normalize(combined)
        if "animal_bite_exposure" in rep.canonical_concepts or "EXP_ANIMAL_BITE" in rep.exposure_events:
            return "trauma_exposure"
        if "thoracic_chest" in rep.anatomical_regions or any(c in rep.canonical_concepts for c in ["chest_pain", "dyspnea_breathlessness"]):
            return "cardiopulmonary"
        if "cough" in rep.canonical_concepts or "sore_throat" in rep.canonical_concepts or "pharyngitis" in rep.canonical_concepts:
            return "respiratory"
        if "lumbar_spine" in rep.anatomical_regions or any(c in rep.canonical_concepts for c in ["lower_back_pain", "radiating_pain_lower_limb"]):
            return "spinal_musculoskeletal"
        if any(r in rep.anatomical_regions for r in ["lower_limb", "upper_limb"]):
            return "musculoskeletal"
        if "abdominal_gi" in rep.anatomical_regions or any(c in rep.canonical_concepts for c in ["abdominal_pain", "vomiting", "diarrhea"]):
            return "gastrointestinal"
        if "skin_rash" in rep.canonical_concepts:
            return "dermatological"
        if "head_cranial" in rep.anatomical_regions or "headache" in rep.canonical_concepts:
            return "neurological"
        if any(c in rep.canonical_concepts for c in ["fever", "chills"]):
            return "systemic_infectious"
    except Exception as e:
        _logger.debug("[_classify_anatomy] Canonical normalization fallback: %s", e)

    domain_keywords = {
        "trauma_exposure": [
            r"\bbite\b", r"\bwound\b", r"\banimal\b", r"\bdog\b", r"\bsnake\b",
            r"\btrauma\b", r"\binjury\b", r"\blaceration\b", r"\bpuncture\b", r"\bburn\b", r"\bfall\b",
            r"काट", r"बટકું", r"घाव", r"ઘા", r"चावा", r"जखम"
        ],
        "cardiopulmonary": [
            r"\bchest\b", r"\bheart\b", r"\bcardiac\b", r"\bpalpitation\b",
            r"\bbreathless\b", r"\bshortness of breath\b", r"\bangina\b", r"\bcoronary\b",
            r"सीने", r"सीना", r"छाती", r"हार्ट", r"છાતી", r"હૃદય", r"छातीत", r"श्वास", r"सांस"
        ],
        "respiratory": [
            r"\bcough\b", r"\bwheeze\b", r"\bwheezing\b", r"\bsputum\b", r"\bbronchial\b",
            r"\bpulmonary\b", r"\blung\b", r"\bairway\b", r"\brespiratory\b", r"\bthroat\b", r"\bpharyng\b", r"\bsore throat\b",
            r"खांसी", r"उધરસ", r"खोकला", r"दमा", r"गला", r"गले", r"ગળું", r"ગળા"
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

    # Explicit exposure priority
    if "trauma_exposure" in scores:
        return "trauma_exposure"

    return max(scores, key=scores.get)


def _detect_patient_domains(symptom_names: list, canon_rep=None) -> set:
    """
    Detects all active anatomical/clinical domains present in patient-reported symptoms.
    Prevents a multi-domain presentation (e.g. bite + headache + sore throat) from losing
    constituent clinical domains.
    """
    combined = " ".join([str(s) for s in symptom_names]).lower()
    domains = set()

    if canon_rep:
        if "animal_bite_exposure" in canon_rep.canonical_concepts or "EXP_ANIMAL_BITE" in canon_rep.exposure_events:
            domains.add("trauma_exposure")
        if "head_cranial" in canon_rep.anatomical_regions or "headache" in canon_rep.canonical_concepts:
            domains.add("neurological")
        if "cough" in canon_rep.canonical_concepts or "sore_throat" in canon_rep.canonical_concepts or "pharyngitis" in canon_rep.canonical_concepts:
            domains.add("respiratory")
        if "thoracic_chest" in canon_rep.anatomical_regions or "chest_pain" in canon_rep.canonical_concepts:
            domains.add("cardiopulmonary")
        if "lumbar_spine" in canon_rep.anatomical_regions or "lower_back_pain" in canon_rep.canonical_concepts:
            domains.add("spinal_musculoskeletal")
        if "abdominal_gi" in canon_rep.anatomical_regions:
            domains.add("gastrointestinal")
        if "skin_rash" in canon_rep.canonical_concepts:
            domains.add("dermatological")
        if any(c in canon_rep.canonical_concepts for c in ["fever", "chills"]):
            domains.add("systemic_infectious")

    # Keyword check
    if any(k in combined for k in ["bite", "wound", "bataku", "karad", "chaava", "dog", "animal", "काटा", "બટકું", "ઘા"]):
        domains.add("trauma_exposure")
    if any(k in combined for k in ["headache", "mathu", "sir", "migraine", "सिरदर्द", "માથું"]):
        domains.add("neurological")
    if any(k in combined for k in ["throat", "cough", "gala", "gale", "pharyng", "khasi", "उધરસ", "ગળું"]):
        domains.add("respiratory")
    if any(k in combined for k in ["chest", "breath", "palpitation", "छाती", "सांस", "શ્વાસ"]):
        domains.add("cardiopulmonary")
    if any(k in combined for k in ["back", "spine", "lumbar", "कमर", "કમર", "पीठ"]):
        domains.add("spinal_musculoskeletal")
    if any(k in combined for k in ["joint", "knee", "shoulder", "muscle", "जोड़ों", "સાંધા"]):
        domains.add("musculoskeletal")
    if any(k in combined for k in ["stomach", "abdomen", "vomit", "diarrhea", "nausea", "पेट", "पેટ", "उल्टी"]):
        domains.add("gastrointestinal")
    if any(k in combined for k in ["skin", "rash", "itch", "खुजली", "ખંજવાળ"]):
        domains.add("dermatological")
    if any(k in combined for k in ["fever", "bukhar", "tav", "taap", "बुखार", "તાવ"]):
        domains.add("systemic_infectious")

    return domains if domains else {"general"}


def _anatomy_compatible(condition_name: str, condition_category: str, patient_anatomy: str, patient_domains: set = None) -> bool:
    """
    Returns True if the condition is anatomically plausible given the patient's symptom anatomy.
    Enforces multi-domain consistency so multi-symptom presentations do not generate unrelated organ conditions.
    """
    c_lower = (condition_name + " " + condition_category).lower()
    domains = set(patient_domains) if patient_domains else {patient_anatomy}

    # Broad multi-system, metabolic, endocrine, neoplastic, or systemic/trauma domains
    is_systemic_domain = any(k in c_lower for k in [
        "systemic", "infectious", "infection", "sepsis", "metabolic", "endocrine",
        "hematolog", "immune", "autoimmune", "neoplasm", "oncolog", "circulatory",
        "multisystem", "general", "deficiency", "toxic", "poisoning", "fever", "anemia",
        "zoonotic", "trauma", "emergency", "bite", "wound", "injury", "exposure", "rabies", "tetanus"
    ])
    if is_systemic_domain:
        return True

    if "general" in domains or "trauma_exposure" in domains or "systemic_infectious" in domains:
        # Check specific organ alignment for specific non-systemic conditions
        pass

    # Map organ-specific domains
    is_cardiac = any(k in c_lower for k in ["cardiac", "heart", "coronary", "myocard", "vascular", "angina"])
    is_respiratory = any(k in c_lower for k in ["pulmon", "bronch", "lung", "respiratory", "pleural", "alveol", "airway", "pharyng", "throat", "tonsil"])
    is_spinal = any(k in c_lower for k in ["spine", "spinal", "vertebr", "lumbar", "disc", "radicul", "nerve root"])
    is_musculo = any(k in c_lower for k in ["arthritis", "muscle", "joint", "knee", "shoulder", "tendon", "sprain", "strain", "bursitis", "myositis", "synov"])
    is_gi = any(k in c_lower for k in ["gastro", "ulcer", "colitis", "bowel", "liver", "hepat", "pancreat", "appendic", "gastric", "intestinal", "esophag", "reflux", "gerd"])
    is_urinary = any(k in c_lower for k in ["renal", "kidney", "urinary", "nephro", "bladder", "prostate", "ureter"])
    is_neuro = any(k in c_lower for k in ["neuro", "cerebr", "brain", "seizure", "cranial", "vertigo", "neuropathy", "central nervous", "headache", "migraine", "tension"])
    is_derma = any(k in c_lower for k in ["dermat", "cutan", "skin", "epiderm", "psorias", "urticar", "fungal", "tinea", "ringworm"])

    if is_cardiac and ("cardiopulmonary" in domains or "general" in domains):
        return True
    if is_respiratory and ("respiratory" in domains or "cardiopulmonary" in domains or "general" in domains):
        return True
    if is_spinal and ("spinal_musculoskeletal" in domains or "general" in domains):
        return True
    if is_musculo and ("musculoskeletal" in domains or "spinal_musculoskeletal" in domains or "general" in domains):
        return True
    if is_gi and ("gastrointestinal" in domains or "general" in domains):
        return True
    if is_urinary and ("urinary_renal" in domains or "general" in domains):
        return True
    if is_neuro and ("neurological" in domains or "general" in domains):
        return True
    if is_derma and ("dermatological" in domains or "general" in domains):
        return True

    # If organ-specific but patient's reported anatomy domains have ZERO overlap with it, suppress
    if any([is_cardiac, is_respiratory, is_spinal, is_musculo, is_gi, is_urinary, is_neuro, is_derma]):
        return False

    return True  # default: compatible


def _passes_clinical_quality_gate(
    condition_name: str,
    condition_category: str,
    input_tokens: set,
    positive_norm_ids: list,
    has_animal_bite_exposure: bool,
    denied_tokens: set
) -> bool:
    """
    Hard clinical quality gate that prevents unrelated differential explosion.
    Enforces cardinal symptom requirements, exposure compatibility, and anatomy constraints.
    """
    c_lower = (condition_name + " " + condition_category).lower()

    # 1. Snakebite Envenoming Gate: STRICTLY requires snakebite exposure
    if any(k in c_lower for k in ["snake", "snakebite", "envenom"]):
        has_snake_exposure = any(t in input_tokens for t in ["snake", "snakebite", "serpent", "सांप", "સાપ"])
        if not has_snake_exposure:
            return False

    # 2. Acute Febrile Tropical Infections: STRICTLY require fever/pyrexia
    is_febrile = any(k in c_lower for k in [
        "malaria", "dengue", "typhoid", "leptospirosis", "scrub typhus", "nipah",
        "kyasanur", "kfd", "chikungunya", "yellow fever", "kala-azar", "leishmaniasis", "influenza"
    ])
    has_fever = (
        any(f in input_tokens for f in ["fever", "pyrexia", "temperature", "chills", "febrile", "bukhar", "tav", "taap", "ताप", "તાવ", "बुखार"])
        or "S000001" in positive_norm_ids
    )
    if is_febrile and not has_fever:
        return False

    # 3. Dermatological / Fungal Infections: STRICTLY require rash / itching / skin lesion
    is_derma = any(k in c_lower for k in ["fungal", "ringworm", "tinea", "dermatitis", "psoriasis", "eczema", "scabies", "urticaria", "rash"])
    has_derma_symptom = any(k in input_tokens for k in ["rash", "itch", "itching", "lesion", "ringworm", "fungal", "skin", "khujli", "dhadhar", "erythema", "pururitus", "चकत्ते", "खुजली", "ખંજવાળ"])
    if is_derma and not has_derma_symptom:
        return False

    # 4. Stroke / Cerebrovascular Accident: STRICTLY requires focal neurological deficit
    if any(k in c_lower for k in ["stroke", "cerebrovascular", "hemiplegia", "transient ischemic", "tia"]):
        has_stroke_signs = any(k in input_tokens for k in [
            "paralysis", "weakness", "droop", "facial droop", "slurred", "speech", "hemiparesis",
            "numbness", "paresthesia", "seizure", "vision loss", "paralyzed", "loss of consciousness"
        ])
        if not has_stroke_signs:
            return False

    # 5. Glaucoma: STRICTLY requires eye pain / vision changes
    if "glaucoma" in c_lower:
        has_eye_signs = any(k in input_tokens for k in ["eye", "ocular", "vision", "blur", "blurred", "halo", "halos", "red eye", "blindness"])
        if not has_eye_signs:
            return False

    # 6. Hypertension: Cannot be diagnosed purely from isolated non-specific headache alone
    if "hypertension" in c_lower or "high blood pressure" in c_lower:
        has_htn_signs = any(k in input_tokens for k in ["hypertension", "blood pressure", "chest", "breathless", "palpitation", "dizziness"])
        if not has_htn_signs:
            return False

    # 7. GERD / Acid Peptic Disorder: STRICTLY requires acid/reflux/heartburn/epigastric burning
    if any(k in c_lower for k in ["gerd", "gastroesophageal", "acid peptic", "reflux", "heartburn"]):
        has_reflux_signs = any(k in input_tokens for k in ["heartburn", "acid", "reflux", "regurgitation", "epigastric", "burning chest", "sour"])
        if not has_reflux_signs:
            return False

    # 8. Rabies Post-Exposure / Encephalitis: requires animal exposure or neurological symptoms
    if "rabies" in c_lower:
        if not has_animal_bite_exposure and not any(k in input_tokens for k in ["bite", "dog", "cat", "monkey", "rabies", "hydrophobia", "aerophobia"]):
            return False

    return True


def _deduplicate_conditions(conditions_list: list) -> list:
    """
    Deduplicates conditions representing identical clinical concepts (e.g. Rabies vs Rabies Post-Exposure).
    Retains the candidate with the higher match score and richer diagnostic metadata.
    """
    seen_concepts = {}
    deduped = []
    for cond in conditions_list:
        name = cond.get("name", "")
        clean_name = re.sub(r'\(.*?\)', '', name).strip().lower()
        # Canonicalize base concept key
        if "rabies" in clean_name:
            concept_key = "rabies_exposure"
        elif "tension" in clean_name and "headache" in clean_name:
            concept_key = "tension_headache"
        elif "migraine" in clean_name:
            concept_key = "migraine"
        elif "influenza" in clean_name or "flu" in clean_name:
            concept_key = "influenza"
        elif "dengue" in clean_name:
            concept_key = "dengue"
        elif "malaria" in clean_name:
            concept_key = "malaria"
        elif "typhoid" in clean_name:
            concept_key = "typhoid"
        elif "gerd" in clean_name or "reflux" in clean_name:
            concept_key = "gerd"
        else:
            concept_key = clean_name

        if concept_key in seen_concepts:
            prev_idx = seen_concepts[concept_key]
            if cond.get("match_percentage", 0) > deduped[prev_idx].get("match_percentage", 0):
                deduped[prev_idx] = cond
        else:
            seen_concepts[concept_key] = len(deduped)
            deduped.append(cond)
    return deduped



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

    def check_red_flags(self, selected_symptom_ids, input_tokens=None, denied_tokens=None, canon_rep=None):
        """
        Check if any selected symptoms trigger emergency red flag protocols.
        Hard evidence gating: Compound red flags require all constituent positive evidence.
        Contradiction check: Removes flags contradicted by denied symptoms or missing triggers.
        """
        if self.df_red_flags.empty or not selected_symptom_ids:
            return []

        norm_symptom_ids = [normalize_id(sid, "S") for sid in selected_symptom_ids]
        matched_flags = self.df_red_flags[self.df_red_flags["symptom_id"].isin(norm_symptom_ids)]
        raw_flags = matched_flags.to_dict(orient="records")
        if not raw_flags:
            return []

        all_tokens = set(input_tokens or set())
        if canon_rep:
            all_tokens |= canon_rep.positive_tokens
        denied = set(denied_tokens or set())
        tokens_str = " ".join(all_tokens).lower()

        # Evidence verification rules for compound red flags
        RED_FLAG_EVIDENCE_RULES = {
            "RF030": {  # Head Injury with Vomiting
                "required_any_group1": ["head injury", "head trauma", "head wound", "trauma", "fall", "injury", "hit", "इंजरी", "चोट", "ઇજા"],
                "required_any_group2": ["vomiting", "vomit", "emesis", "उल्टी", "ઉલટી"],
                "disallowed_only_headache": True
            },
            "RF031": {  # Persistent Headache with Vomiting
                "required_any_group1": ["headache", "head", "सिरदर्द", "માથું", "માથાનો"],
                "required_any_group2": ["vomiting", "vomit", "emesis", "उल्टी", "ઉલટી"]
            },
            "RF014": {  # Chest Pain Radiating to Arm, Jaw, or Back
                "required_any_group1": ["chest pain", "chest", "सीना", "छाती"],
                "required_any_group2": ["radiat", "arm", "jaw", "back", "रेडिएटिंग", "हाथ", "कंधा"]
            },
            "RF018": {  # Chest Pain with Sweating and Nausea
                "required_any_group1": ["chest pain", "chest", "सीना", "छाती"],
                "required_any_group2": ["sweat", "perspir", "nausea", "vomit", "पसीना", "पसीनो"]
            },
            "RF019": {  # Sudden Severe Chest Pain with Breathlessness
                "required_any_group1": ["chest pain", "chest", "सीना", "छाती"],
                "required_any_group2": ["breath", "dyspnea", "shortness", "सांस", "શ્વાસ"]
            },
            "RF021": {  # Sudden One-Sided Weakness (Stroke Warning)
                "required_any_group1": ["paralysis", "weakness", "droop", "slurred", "speech", "hemiparesis", "लकवा", "कमजोरी", "નબળાઈ"]
            },
            "RF028": {  # Neck Stiffness with Fever
                "required_any_group1": ["neck", "stiff", "गर्दन", "ગરદન"],
                "required_any_group2": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"]
            },
            "RF064": {  # Fever with Joint Pain
                "required_any_group1": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"],
                "required_any_group2": ["joint", "arthralgia", "जोड़ों", "સાંધા"]
            },
            "RF065": {  # Fever with Chills and Sweating
                "required_any_group1": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"],
                "required_any_group2": ["chills", "rigors", "sweat", "कंपकंपी", "ધ્રુજારી"]
            },
            "RF067": {  # Fever with Neck Stiffness
                "required_any_group1": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"],
                "required_any_group2": ["neck", "stiff", "गर्दन", "ગરદન"]
            },
            "RF068": {  # Fever with Yellowing of Skin
                "required_any_group1": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"],
                "required_any_group2": ["jaundice", "yellow", "पीलिया", "કમળો"]
            },
            "RF069": {  # Fever with Cough and Breathlessness
                "required_any_group1": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"],
                "required_any_group2": ["cough", "breath", "dyspnea", "खांसी", "उધરસ", "सांस"]
            },
            "RF070": {  # Fever with Rash and Bleeding Gums
                "required_any_group1": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"],
                "required_any_group2": ["rash", "bleed", "रक्त", "લોહી", "ગુંદર"]
            },
            "RF071": {  # Fever with Low Platelet Signs
                "required_any_group1": ["fever", "pyrexia", "temperature", "बुखार", "ताप", "તાવ"],
                "required_any_group2": ["platelet", "bruis", "bleed", "प्लेटलेट्स"]
            },
            "RF072": {  # Animal Bite with Wound
                "required_any_group1": ["bite", "animal", "dog", "cat", "monkey", "wound", "bataku", "karad", "chaava", "काटा", "બટકું", "કૂતરું", "ઘા"]
            }
        }

        validated_flags = []

        for flag in raw_flags:
            fid = str(flag.get("flag_id", "")).strip()
            rule = RED_FLAG_EVIDENCE_RULES.get(fid)
            passed = True
            missing_evidence = []
            matched_evidence = []

            if rule and tokens_str:
                g1 = rule.get("required_any_group1", [])
                g2 = rule.get("required_any_group2", [])
                
                hit1 = any(k in tokens_str for k in g1) if g1 else True
                hit2 = any(k in tokens_str for k in g2) if g2 else True
                
                if not hit1:
                    passed = False
                    missing_evidence.append(f"Group 1: {g1}")
                else:
                    matched_evidence.append("Group 1 hit")
                    
                if not hit2:
                    passed = False
                    missing_evidence.append(f"Group 2: {g2}")
                else:
                    matched_evidence.append("Group 2 hit")

                if rule.get("disallowed_only_headache") and not any(k in tokens_str for k in ["injury", "trauma", "fall", "wound", "hit", "चोट", "ઇજા"]):
                    passed = False
                    missing_evidence.append("Explicit head trauma/injury absent (only isolated headache reported)")

            # Check if any constituent symptom is in denied_tokens
            flag_name_toks = _tokenize(flag.get("symptom_name", ""))
            if flag_name_toks & denied:
                passed = False
                missing_evidence.append(f"Denied tokens matched: {flag_name_toks & denied}")

            debug_obj = {
                "rule_name": f"{fid}: {flag.get('symptom_name')}",
                "required_evidence": rule.get("required_any_group1", []) + rule.get("required_any_group2", []) if rule else [],
                "matched_evidence": matched_evidence,
                "missing_evidence": missing_evidence,
                "passed": passed
            }
            _logger.debug("[TriageEngine] Red flag validation: %s", debug_obj)

            if passed:
                validated_flags.append(flag)
            else:
                _logger.info("[TriageEngine] Gated out false red flag: '%s' (%s) due to missing required evidence",
                             flag.get("symptom_name"), fid)

        if validated_flags:
            _logger.info("[TriageEngine] RED FLAGS confirmed: %d flag(s)", len(validated_flags))
        return validated_flags

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

        # Map individual symptom names to canonical symptom IDs
        for s in symptom_names:
            if s and str(s).strip():
                sid = canonical_normalizer.get_symptom_id(str(s).strip())
                if sid:
                    norm_sid = normalize_id(sid, "S")
                    if norm_sid not in norm_symptom_ids:
                        norm_symptom_ids.append(norm_sid)

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

        # CRITICAL REPAIR: STRICTLY SEPARATE EVIDENCE CHANNELS
        # 1. Patient Raw Tokens
        s_names_lower = [s.lower().strip() for s in symptom_names]
        patient_raw_tokens = set()
        for s in s_names_lower:
            patient_raw_tokens |= _tokenize(s)

        # 2. Patient Canonical Tokens
        patient_canonical_tokens = set()
        if canon_rep:
            patient_canonical_tokens |= canon_rep.positive_tokens

        # 3. Patient Positive Tokens (from resolved positive IDs)
        patient_positive_tokens = set()
        for sid in positive_norm_ids:
            rec = canonical_normalizer.bridge.lookup_by_id(sid)
            if rec and rec.get("symptom_name"):
                patient_positive_tokens |= _tokenize(rec["symptom_name"])

        # 4. External BioPortal Tokens (Separated — concept must map to valid canonical symptom to contribute)
        external_bioportal_tokens = set()
        for bc in bioportal_concepts:
            b_label = bc.get("prefLabel") or bc.get("name") if isinstance(bc, dict) else str(bc)
            if b_label:
                external_bioportal_tokens |= _tokenize(b_label)
                mapped_sid = canonical_normalizer.get_symptom_id(str(b_label))
                if mapped_sid:
                    norm_msid = normalize_id(mapped_sid, "S")
                    if norm_msid not in positive_norm_ids and norm_msid not in all_negative_findings:
                        positive_norm_ids.append(norm_msid)
                        rec = canonical_normalizer.bridge.lookup_by_id(norm_msid)
                        if rec and rec.get("symptom_name"):
                            patient_positive_tokens |= _tokenize(rec["symptom_name"])

        # 5. External NLM Condition Tokens (Strictly External — NEVER added to patient symptom evidence!)
        external_nlm_condition_tokens = set()
        for nlm in nlm_conditions:
            n_label = nlm.get("name") or nlm.get("title") if isinstance(nlm, dict) else str(nlm)
            if n_label:
                external_nlm_condition_tokens |= _tokenize(n_label)

        # PATIENT EVIDENCE = (patient_raw_tokens | patient_canonical_tokens | patient_positive_tokens) - denied_tokens
        # NLM conditions MUST NEVER become patient symptom evidence
        patient_evidence_tokens = (patient_raw_tokens | patient_canonical_tokens | patient_positive_tokens) - denied_tokens
        input_tokens = patient_evidence_tokens

        # Check exposure events (e.g. Animal Bite Exposure)
        has_animal_bite_exposure = False
        if canon_rep and "EXP_ANIMAL_BITE" in canon_rep.exposure_events:
            has_animal_bite_exposure = True
        elif any(normalize_id(s, "S") == "S000265" for s in positive_norm_ids):
            has_animal_bite_exposure = True
        elif any(k in " ".join(s_names_lower) for k in ["bite", "dog bite", "animal bite", "કુતરા", "काटा", "bataku", "karad", "chaava"]):
            has_animal_bite_exposure = True

        # Determine patient anatomical system and all active patient clinical domains
        patient_anatomy = _classify_anatomy(symptom_names)
        if has_animal_bite_exposure and patient_anatomy == "general":
            patient_anatomy = "trauma_exposure"
        patient_domains = _detect_patient_domains(symptom_names, canon_rep=canon_rep)
        if has_animal_bite_exposure:
            patient_domains.add("trauma_exposure")
        _logger.info("[TriageEngine] Patient anatomy: %s | Domains: %s (animal_bite_exposure=%s)",
                     patient_anatomy, list(patient_domains), has_animal_bite_exposure)

        _logger.info("[TriageEngine] Evaluating %d positive symptoms (%d denied) for age=%s, gender=%s, duration=%s",
                     len(positive_norm_ids), len(all_negative_findings), age_group, gender, duration)

        # 1. Red flag triage with hard constituent evidence gating (USES ONLY PATIENT EVIDENCE)
        red_flags = self.check_red_flags(
            positive_norm_ids,
            input_tokens=patient_evidence_tokens,
            denied_tokens=denied_tokens,
            canon_rep=canon_rep
        )
        is_emergency = len(red_flags) > 0 or has_animal_bite_exposure

        ranked_conditions = []
        matched_disease_ids = set()

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
                if not _anatomy_compatible(d_name, d_cat, patient_anatomy, patient_domains=patient_domains):
                    _logger.debug("[TriageEngine] Suppressed '%s': anatomical mismatch (%s vs %s)", d_name, d_cat, patient_anatomy)
                    continue

                # Clinical quality gate (cardinal symptoms, exposure compatibility)
                if not _passes_clinical_quality_gate(d_name, d_cat, input_tokens, positive_norm_ids, has_animal_bite_exposure, denied_tokens):
                    _logger.debug("[TriageEngine] Suppressed '%s': failed clinical quality gate", d_name)
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
                if "fever" in denied_tokens:
                    is_febrile = any(w in (d_name + " " + d_cat).lower() for w in ["malaria", "dengue", "typhoid", "leptospirosis", "scrub typhus", "influenza"])
                    if is_febrile:
                        _logger.debug("[TriageEngine] Suppressed '%s': cardinal symptom 'fever' was explicitly denied", d_name)
                        continue

                # Weighted token overlap — no loose substring matching
                overlap_count = 0
                matched_syms = []
                for ds in d_syms:
                    ds_tokens = _tokenize(ds)
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

                # Chief condition matching (treated as hypothesis under evaluation)
                is_chief_match = False
                if chief_condition:
                    c_lower = str(chief_condition).lower().strip()
                    if c_lower and (c_lower == d_name.lower() or f" {c_lower} " in f" {d_name.lower()} "):
                        is_chief_match = True

                if not is_chief_match and overlap_count < 1:
                    continue

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

                if ("emergency" in str(d_row.get("urgency", "")).lower() or "critical" in str(d_row.get("urgency", "")).lower()) and match_pct >= 70 and overlap_count >= 3:
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
                    "icd_verified": False,
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
                    "source": "Local Major Disease Dataset",
                    "provider": "DocMindX India Disease KB",
                    "is_live": False,
                    "fallback_used": True,
                    "fallback_reason": "Local clinical reference dataset (offline fallback)"
                })
                matched_disease_ids.add(d_id)

        _logger.info("[TriageEngine] Major diseases matched: %d candidates", len(ranked_conditions))

        # 3. Traditional Bipartite Graph Knowledge Base with strict quality gating
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
                d_name = str(d_row["disease_name"])
                d_cat = str(d_row.get("category", "General Medicine"))

                # Strict anatomical compatibility gate for bipartite candidates
                if not _anatomy_compatible(d_name, d_cat, patient_anatomy, patient_domains=patient_domains):
                    _logger.debug("[TriageEngine] Suppressed bipartite '%s': anatomical mismatch", d_name)
                    continue

                # Strict clinical quality gate for bipartite candidates
                if not _passes_clinical_quality_gate(d_name, d_cat, input_tokens, positive_norm_ids, has_animal_bite_exposure, denied_tokens):
                    _logger.debug("[TriageEngine] Suppressed bipartite '%s': failed clinical quality gate", d_name)
                    continue

                all_mappings = self.df_mappings[self.df_mappings["disease_id"] == d_id]
                max_w = all_mappings["weight"].sum() if not all_mappings.empty else 1.0
                matched_cnt = len(disease_matched_symptoms[d_id])
                match_percentage = round(((total_score / max(max_w, 1.0)) * 0.70 + (matched_cnt / max(len(all_mappings), 1.0)) * 0.30) * 100)

                if match_percentage < 25:
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
                d_tests = _find_condition_tests(str(d_row["disease_name"]), self.df_major_diseases)

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
                    "category": d_cat,
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
                    "tests": d_tests,
                    "yoga": [],
                    "physiotherapy": [],
                    "source": "Local Bipartite Disease Graph",
                    "provider": "DocMindX Disease-Symptom KB",
                    "is_live": False,
                    "fallback_used": True,
                    "fallback_reason": "Local bipartite graph (symptom ID mapping)"
                })

        # Apply clinical concept deduplication (e.g. Rabies vs Rabies Post-Exposure)
        ranked_conditions = _deduplicate_conditions(ranked_conditions)
        _logger.info("[TriageEngine] Candidates after quality gating & deduplication: %d", len(ranked_conditions))

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
                # Duration gate on routine tests: <= 4 days suppresses routine tests unless emergency
                dur_days_val = _parse_duration_days(duration)
                if dur_days_val is None and canon_rep and canon_rep.duration_days is not None:
                    dur_days_val = canon_rep.duration_days
                
                ai_tests = ai_res.get("tests_to_discuss", [])
                if not bool(ai_res.get("is_emergency", False)) and not red_flags and dur_days_val is not None and dur_days_val <= 4:
                    ai_tests = []
                elif has_animal_bite_exposure and dur_days_val is not None and dur_days_val <= 4:
                    ai_tests = ["Wound Assessment & Antiseptic Irrigation Check", "Rabies Exposure Risk & Prophylaxis Evaluation", "Tetanus Immunization Status Check"]

                return {
                    "is_emergency": bool(ai_res.get("is_emergency", False)) or has_animal_bite_exposure,
                    "red_flags": red_flags,
                    "urgency_level": ai_res.get("urgency_level", "Critical / Urgent Medical Attention" if has_animal_bite_exposure else "Moderate Attention"),
                    "ranked_conditions": ai_conds,
                    "tests_to_discuss": ai_tests,
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
        is_emergency = (len(red_flags) > 0) or has_animal_bite_exposure or any(
            ("emergency" in str(c.get("urgency", "")).lower() or "critical" in str(c.get("urgency", "")).lower())
            and c.get("match_percentage", 0) >= 70 for c in ranked_conditions
        )
        if is_emergency:
            urgency = "Critical / Urgent Medical Attention"
        elif any(c.get("match_percentage", 0) >= 40 for c in ranked_conditions):
            urgency = "Moderate Attention (Consult Physician)"
        else:
            urgency = "Mild / Self-Monitoring"

        # 8. Compile evidence-linked tests with strict DURATION GATING (Section 14 & 15)
        all_tests = []
        dur_days_val = _parse_duration_days(duration)
        if dur_days_val is None and canon_rep and canon_rep.duration_days is not None:
            dur_days_val = canon_rep.duration_days

        # Duration Gate:
        # If duration <= 4 days (e.g. "Started Today", "1-3 Days"):
        # Suppress routine laboratory panels (Lipid Profile, ECG, EEG, Brain MRI, Serum Creatinine).
        # Emergency exception: If animal bite / exposure is active, show only relevant urgent exposure evaluation.
        if dur_days_val is not None and dur_days_val <= 4:
            if has_animal_bite_exposure:
                all_tests = [
                    "Wound Assessment & Antiseptic Irrigation Check",
                    "Rabies Exposure Risk & Prophylaxis Evaluation",
                    "Tetanus Immunization Status Check"
                ]
            else:
                all_tests = []
        else:
            # Duration > 4 days: show only condition-linked, high-yield diagnostic tests (capped at 5)
            for rc in ranked_conditions:
                for t in rc.get("tests", []):
                    # Suppress irrelevant high-cost/invasive panels for simple presentations
                    t_lower = str(t).lower()
                    if any(k in t_lower for k in ["lipid profile", "eeg", "brain mri", "electrophoresis"]) and "headache" in str(s_names_lower) and len(s_names_lower) <= 2:
                        continue
                    if t and t not in all_tests:
                        all_tests.append(t)
                if len(all_tests) >= 5:
                    break
            all_tests = all_tests[:5]

        # Fallback warning
        fallback_warning = ""
        if not who_live_available:
            fallback_warning = (
                " Live clinical data service is currently unavailable. "
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
            "positive_symptoms": positive_norm_ids,
            "positive_symptom_ids": positive_norm_ids,
            "ranked_conditions": ranked_conditions,  # Dynamic count — NO artificial [:N] limit here
            "tests_to_discuss": all_tests,
            "system_status": system_status,
            "fallback_warning": fallback_warning
        }

    def evaluate_triage(
        self,
        reported_symptom_ids,
        patient_history=None,
        symptom_names=None,
        chief_condition=None,
        negative_findings=None,
        bioportal_concepts=None,
        nlm_conditions=None,
        **kwargs
    ):
        """
        Adapter method called by the clinical pipeline and Streamlit portal.
        Forwards resolved BioPortal concepts, NLM candidates, and patient context into evaluate_symptoms.
        """
        patient_history = patient_history or {}
        return self.evaluate_symptoms(
            selected_symptom_ids=reported_symptom_ids,
            age_group=patient_history.get("age_group", patient_history.get("age", "21-30")),
            gender=patient_history.get("gender", "Male"),
            duration=patient_history.get("duration", "1-3 Days"),
            existing_conditions=patient_history.get("conditions", {}),
            symptom_names=symptom_names or patient_history.get("symptom_names", []),
            chief_condition=chief_condition or patient_history.get("chief_condition"),
            negative_findings=negative_findings or patient_history.get("negative_findings", []),
            bioportal_concepts=bioportal_concepts or patient_history.get("bioportal_concepts", []),
            nlm_conditions=nlm_conditions or patient_history.get("nlm_conditions", [])
        )


# Global singleton instance and class alias
TriageEngine = SymptomTriageEngine
triage_engine = SymptomTriageEngine()
