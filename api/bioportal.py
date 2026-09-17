"""
    NCBO BioPortal API Client - Biomedical Ontology & Clinical Concept Mapping
Provides:
1. Medical Concept Search (ICD-10, SNOMED-CT, MeSH, LOINC, RxNorm, HPO)
2. Clinical Text Annotator (Extracts clinical concepts from raw text / reports)
3. Ontology definitions and synonym expansion
"""
import requests
import os
import sys
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_logger = logger  # Alias for consistency with DocMindX.TriageEngine logger convention

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import BIOPORTAL_API_KEY

BASE_URL = "https://data.bioontology.org"

# Stateful Circuit Breaker Pattern for BioPortal
_last_bioportal_failure_timestamp: float = 0.0
_BIOPORTAL_CIRCUIT_BREAKER_BACKOFF: float = 60.0  # 60 seconds backoff on timeout/auth failure

# High-frequency clinical ontology knowledgebase for instant offline lookup & zero-latency fallback
OFFLINE_CLINICAL_ONTOLOGIES = {
    "asthma": [
        {
            "pref_label": "Bronchial Asthma",
            "concept_id": "http://snomed.info/id/195967001",
            "ontology": "SNOMED-CT",
            "cui": "C0004096",
            "definition": "Chronic inflammatory disorder of the airways characterized by bronchial hyperresponsiveness and reversible airflow obstruction.",
            "synonyms": ["Asthma", "Hyperreactive Airway Disease", "Bronchial Spasm"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Asthma",
            "concept_id": "http://purl.bioontology.org/ontology/MESH/D001249",
            "ontology": "MeSH",
            "cui": "C0004096",
            "definition": "A form of bronchial disorder characterized by recurrent attacks of paroxysmal dyspnea.",
            "synonyms": ["Bronchial Asthma", "Asthmatic Attack"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "fever": [
        {
            "pref_label": "Fever (Pyrexia)",
            "concept_id": "http://snomed.info/id/386661006",
            "ontology": "SNOMED-CT",
            "cui": "C0015967",
            "definition": "Elevation of body temperature above normal circadian range resulting from cytokine-mediated thermoregulatory set-point elevation.",
            "synonyms": ["Pyrexia", "Elevated Body Temperature", "Febrile State"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "cough": [
        {
            "pref_label": "Cough",
            "concept_id": "http://snomed.info/id/49727002",
            "ontology": "SNOMED-CT",
            "cui": "C0010200",
            "definition": "Sudden, repetitive, spasmodic contraction of the thoracic cavity resulting in violent release of air from the lungs.",
            "synonyms": ["Coughing", "Tussis", "Dry or Productive Cough"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "chest pain": [
        {
            "pref_label": "Chest Pain",
            "concept_id": "http://snomed.info/id/29857009",
            "ontology": "SNOMED-CT",
            "cui": "C0008031",
            "definition": "Pain or discomfort in the chest region requiring prompt cardiopulmonary risk stratification.",
            "synonyms": ["Precordial Pain", "Thoracalgia", "Chest Discomfort"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "headache": [
        {
            "pref_label": "Headache",
            "concept_id": "http://snomed.info/id/25064002",
            "ontology": "SNOMED-CT",
            "cui": "C0018681",
            "definition": "Pain in the head, scalp, or neck arising from traction or irritation of pain-sensitive intracranial and extracranial structures.",
            "synonyms": ["Cephalalgia", "Cranial Pain", "Head Pain"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "dengue": [
        {
            "pref_label": "Dengue Fever",
            "concept_id": "http://snomed.info/id/38362002",
            "ontology": "SNOMED-CT",
            "cui": "C0011311",
            "definition": "Acute mosquito-borne viral infection caused by Dengue virus flaviviruses characterized by biphasic fever, myalgia, and thrombocytopenia.",
            "synonyms": ["Breakbone Fever", "Dengue Virus Infection", "Classical Dengue"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "malaria": [
        {
            "pref_label": "Malaria",
            "concept_id": "http://snomed.info/id/61462000",
            "ontology": "SNOMED-CT",
            "cui": "C0024530",
            "definition": "Protozoan infectious disease transmitted by Anopheles mosquitoes caused by Plasmodium species.",
            "synonyms": ["Plasmodium Infection", "Paludism", "Febrile Splenomegaly"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "back pain": [
        {
            "pref_label": "Low Back Pain",
            "concept_id": "http://snomed.info/id/279039007",
            "ontology": "SNOMED-CT",
            "cui": "C0024031",
            "definition": "Pain, muscle tension, or stiffness localized below the costal margin and above the inferior gluteal folds.",
            "synonyms": ["Lumbago", "Lumbar Spine Pain", "Lower Backache"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "hypertension": [
        {
            "pref_label": "Essential (primary) hypertension",
            "concept_id": "http://snomed.info/id/59621000",
            "ontology": "SNOMED-CT",
            "cui": "C0020538",
            "definition": "Persistently high systemic arterial blood pressure (systolic >= 140 mmHg or diastolic >= 90 mmHg) without secondary cause.",
            "synonyms": ["High Blood Pressure", "Systemic Arterial Hypertension", "Primary Hypertension"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Hypertension",
            "concept_id": "http://purl.bioontology.org/ontology/MESH/D006973",
            "ontology": "MeSH",
            "cui": "C0020538",
            "definition": "Pathological elevation of systemic arterial blood pressure requiring pharmacological and lifestyle intervention.",
            "synonyms": ["Blood Pressure, High", "Arterial Hypertension"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Systolic and Diastolic Blood Pressure panel",
            "concept_id": "http://purl.bioontology.org/ontology/LNC/85354-9",
            "ontology": "LOINC",
            "cui": "C0871470",
            "definition": "Standardized clinical laboratory and physiological panel for measuring systolic and diastolic blood pressure.",
            "synonyms": ["BP Panel", "Blood Pressure Measurement"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "diabetes": [
        {
            "pref_label": "Type 2 Diabetes Mellitus",
            "concept_id": "http://snomed.info/id/44054006",
            "ontology": "SNOMED-CT",
            "cui": "C0011860",
            "definition": "Metabolic disorder characterized by chronic hyperglycemia resulting from defects in insulin secretion and insulin resistance.",
            "synonyms": ["Non-insulin-dependent diabetes", "T2DM", "Adult-onset diabetes"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Glucose [Mass/volume] in Blood",
            "concept_id": "http://purl.bioontology.org/ontology/LNC/2345-7",
            "ontology": "LOINC",
            "cui": "C0373639",
            "definition": "Quantitative laboratory test for measuring fasting and postprandial serum glucose levels.",
            "synonyms": ["Fasting Blood Sugar", "Blood Glucose Level", "FBS"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Hemoglobin A1c / Total Hemoglobin in Blood",
            "concept_id": "http://purl.bioontology.org/ontology/LNC/4548-4",
            "ontology": "LOINC",
            "cui": "C0474680",
            "definition": "Diagnostic glycemic marker reflecting average 3-month blood glucose control.",
            "synonyms": ["HbA1c", "Glycated Hemoglobin", "Glycohemoglobin"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "metformin": [
        {
            "pref_label": "Metformin hydrochloride 500 MG Oral Tablet",
            "concept_id": "http://purl.bioontology.org/ontology/RXNORM/860975",
            "ontology": "RxNorm",
            "cui": "C0978482",
            "definition": "Biguanide antihyperglycemic agent that decreases hepatic glucose production and improves insulin sensitivity.",
            "synonyms": ["Glucophage", "Metformin HCl", "Biguanide Oral Antidiabetic"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Metformin",
            "concept_id": "http://purl.bioontology.org/ontology/MESH/D008687",
            "ontology": "MeSH",
            "cui": "C0025598",
            "definition": "A first-line oral antidiabetic drug in the biguanide class prescribed for type 2 diabetes management.",
            "synonyms": ["Dimethyldiguanide", "Glucophage 500"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "creatinine": [
        {
            "pref_label": "Creatinine [Mass/volume] in Serum or Plasma",
            "concept_id": "http://purl.bioontology.org/ontology/LNC/2160-0",
            "ontology": "LOINC",
            "cui": "C0201990",
            "definition": "Critical kidney function marker reflecting glomerular filtration and muscle catabolism rate.",
            "synonyms": ["Serum Creatinine", "Cr Level", "Kidney Function Test"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Creatinine measurement",
            "concept_id": "http://snomed.info/id/70901006",
            "ontology": "SNOMED-CT",
            "cui": "C0201990",
            "definition": "Diagnostic laboratory assessment evaluating renal clearance and tubular secretion.",
            "synonyms": ["Blood Creatinine Test", "Renal Function Marker"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "paracetamol": [
        {
            "pref_label": "Acetaminophen 500 MG Oral Tablet",
            "concept_id": "http://purl.bioontology.org/ontology/RXNORM/198440",
            "ontology": "RxNorm",
            "cui": "C0000970",
            "definition": "Widely used antipyretic and analgesic agent indicated for mild-to-moderate pain and fever reduction.",
            "synonyms": ["Paracetamol", "Dolo 500", "Crocin 500", "Acetaminophen"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Acetaminophen",
            "concept_id": "http://purl.bioontology.org/ontology/MESH/D000082",
            "ontology": "MeSH",
            "cui": "C0000970",
            "definition": "Anilide derivative analgesic used to relieve pain and reduce elevated body temperature.",
            "synonyms": ["APAP", "Paracetamol Tablet", "N-acetyl-p-aminophenol"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "pneumonia": [
        {
            "pref_label": "Pneumonia",
            "concept_id": "http://snomed.info/id/233604007",
            "ontology": "SNOMED-CT",
            "cui": "C0032285",
            "definition": "Acute inflammatory condition of the lung parenchyma primarily affecting the alveoli, usually caused by infection.",
            "synonyms": ["Lung Infection", "Pulmonary Consolidation", "Pneumonitis"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Chest X-Ray Single View (PA)",
            "concept_id": "http://purl.bioontology.org/ontology/LNC/36572-6",
            "ontology": "LOINC",
            "cui": "C0882319",
            "definition": "Radiological imaging examination to identify pulmonary infiltrates and consolidation.",
            "synonyms": ["CXR", "Chest Radiograph", "Pulmonary X-Ray"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ],
    "hemoglobin": [
        {
            "pref_label": "Hemoglobin [Mass/volume] in Blood",
            "concept_id": "http://purl.bioontology.org/ontology/LNC/718-7",
            "ontology": "LOINC",
            "cui": "C0019046",
            "definition": "Standard complete blood count parameter measuring oxygen-carrying protein capacity in erythrocytes.",
            "synonyms": ["Hb Level", "Hgb", "Blood Hemoglobin Concentration"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        },
        {
            "pref_label": "Iron deficiency anemia",
            "concept_id": "http://snomed.info/id/87522002",
            "ontology": "SNOMED-CT",
            "cui": "C0162316",
            "definition": "Microcytic hypochromic anemia caused by insufficient total body iron reserves.",
            "synonyms": ["IDA", "Microcytic Anemia", "Low Hemoglobin State"],
            "fallback": True,
            "failure_type": "offline_knowledgebase"
        }
    ]
}

def get_headers():
    return {
        "Authorization": f"apikey token={BIOPORTAL_API_KEY}",
        "Accept": "application/json"
    }

def search_bioportal_concept(query, ontologies=None, page_size=5):
    """
    Searches NCBO BioPortal for medical concepts, synonyms, and ICD/SNOMED codes.
    With automatic offline clinical knowledgebase fallback.
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to search_bioportal_concept.")
        return []

    q_clean = query.strip().lower()

    # 1. Attempt live BioPortal NCBO API search (Circuit Breaker Protected)
    global _last_bioportal_failure_timestamp
    now = time.time()
    circuit_open = (now - _last_bioportal_failure_timestamp) < _BIOPORTAL_CIRCUIT_BREAKER_BACKOFF

    if BIOPORTAL_API_KEY and not circuit_open:
        try:
            url = f"{BASE_URL}/search"
            params = {
                "q": query.strip(),
                "pagesize": page_size,
                "display_context": "false"
            }
            if ontologies:
                params["ontologies"] = ",".join(ontologies) if isinstance(ontologies, list) else ontologies

            # Fast adaptive timeout (1.5s connect, 3.0s read) to prevent pipeline hangs
            res = requests.get(url, headers=get_headers(), params=params, timeout=(1.5, 3.0))
            if res.status_code == 200:
                data = res.json()
                collection = data.get("collection", [])
                results = []
                
                for item in collection:
                    pref_label = item.get("prefLabel", "")
                    concept_id = item.get("@id", "")
                    ontology_link = item.get("links", {}).get("ontology", "")
                    ontology_name = ontology_link.split("/")[-1] if ontology_link else "Medical Ontology"
                    synonyms = item.get("synonym", [])
                    cui = item.get("cui", [])
                    definition = item.get("definition", [""])[0] if isinstance(item.get("definition"), list) and item.get("definition") else ""
                    
                    results.append({
                        "pref_label": pref_label,
                        "prefLabel": pref_label,
                        "concept_id": concept_id,
                        "id": concept_id,
                        "ontology": ontology_name,
                        "synonyms": synonyms[:4] if isinstance(synonyms, list) else [],
                        "cui": cui[0] if cui and isinstance(cui, list) else "",
                        "definition": definition,
                        "is_live": True,
                        "fallback_used": False,
                        "fallback_reason": ""
                    })
                if results:
                    return results
            elif res.status_code in (401, 403):
                _last_bioportal_failure_timestamp = time.time()
                _logger.warning("[BioPortal] Authentication error HTTP %d. Tripping circuit breaker for 60s.", res.status_code)
            else:
                _logger.warning("[BioPortal] API returned status code %d", res.status_code)
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            _last_bioportal_failure_timestamp = time.time()
            _logger.warning("[BioPortal] Network timeout/handshake error (%s). Tripping circuit breaker for 60s.", e)
        except Exception as e:
            _logger.warning("[BioPortal] Live search exception: %s", e)
    elif circuit_open:
        remaining = round(_BIOPORTAL_CIRCUIT_BREAKER_BACKOFF - (now - _last_bioportal_failure_timestamp), 1)
        _logger.debug("[BioPortal] Circuit breaker active (backing off for %.1fs). Resolving via local clinical ontology.", remaining)

    # 2. Seamless local ontology fallback
    for key, items in OFFLINE_CLINICAL_ONTOLOGIES.items():
        if key in q_clean or any(word in q_clean for word in key.split()):
            _logger.info("[BioPortal] LOCAL FALLBACK matched '%s' for query: '%s'", key, query)
            enriched = []
            for it in items:
                failure_type = it.get("failure_type")
                enriched.append({
                    **it,
                    "prefLabel": it.get("pref_label", ""),
                    "id": it.get("concept_id", ""),
                    "is_live": False,
                    "fallback_used": True,
                    "fallback_reason": failure_type or "BioPortal API unavailable"
                })
            return enriched

    # 3. No fabricated SNOMED IDs or generic cards; return empty list with failure tracking
    logger.warning(f"No concept found for query '{query}' in live API or offline knowledgebase.")
    return []

def annotate_clinical_text(text):
    """
    Uses BioPortal Annotator endpoint to extract recognized biomedical entities,
    diseases, medications, and anatomy from raw prescription/report notes.
    """
    if not text or not text.strip() or len(text.strip()) < 4:
        logger.warning("Text too short or empty for clinical annotation.")
        return []

    if not BIOPORTAL_API_KEY:
        logger.error("BIOPORTAL_API_KEY not configured for text annotation.")
        return []

    try:
        url = f"{BASE_URL}/annotator"
        params = {
            "text": text[:1000],
            "longest_only": "true",
            "exclude_numbers": "true"
        }
        res = requests.get(url, headers=get_headers(), params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            annotations = []
            for ann in data[:10]:
                annotated_class = ann.get("annotatedClass", {})
                pref_label = annotated_class.get("prefLabel", "")
                ont_link = annotated_class.get("links", {}).get("ontology", "")
                ont_acronym = ont_link.split("/")[-1] if ont_link else "Biomedical Ontology"
                spans = []
                for match in ann.get("annotations", []):
                    spans.append({
                        "from": match.get("from"),
                        "to": match.get("to"),
                        "text": match.get("text")
                    })
                    
                annotations.append({
                    "concept": pref_label or (spans[0]["text"] if spans else "Medical Concept"),
                    "matched_text": spans[0]["text"] if spans else "",
                    "ontology": ont_acronym,
                    "concept_id": annotated_class.get("@id", ""),
                    "fallback": False,
                    "failure_type": None
                })
            return annotations
        else:
            logger.error(f"BioPortal Annotator API returned status code {res.status_code}")
    except Exception as e:
        logger.error(f"BioPortal Annotator exception: {e}", exc_info=True)

    return []
