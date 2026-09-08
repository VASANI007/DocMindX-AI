"""
    DocMindX AI - Medicine Entity Detector from Clinical Text & Prescriptions
"""
import re
from ai.medicine_ai.medicine_search import medicine_search_engine

COMMON_DRUG_PATTERNS = [
    r"\b(paracetamol|dolo|crocin|calpol|combiflam|ibuprofen|meftal|aspirin)\b",
    r"\b(pantoprazole|pan 40|pan-d|omeprazole|rabeprazole|gelusil|digene|eno)\b",
    r"\b(ondansetron|ondem|emeset|vomistop|domperidone)\b",
    r"\b(cetirizine|cetzine|okacet|levocetirizine|allegra|fexofenadine|benadryl|ascoril)\b",
    r"\b(amoxicillin|augmentin|azithromycin|azithral|ciprofloxacin|ofloxacin|cefixime)\b",
    r"\b(metformin|glycomet|glimepiride|teneligliptin|insulin)\b",
    r"\b(amlodipine|telmisartan|telma|losartan|atenolol|metoprolol)\b",
    r"\b(atorvastatin|atorva|rosuvastatin|rosuvas)\b",
    r"\b(electral|ors|sporlac|becosules|limcee|zinc|shelcal|calcium)\b"
]

class MedicineDetector:
    """Detects pharmaceutical entities from free text and OCR extracts."""
def detect_medicines(self, text: str) -> list:
        if not text or not isinstance(text, str):
            return []
            
        found_names = set()
        text_lower = text.lower()

        for pat in COMMON_DRUG_PATTERNS:
            matches = re.findall(pat, text_lower)
            for m in matches:
                found_names.add(m.capitalize())

        # Enrich detected entities with master database
        results = []
        for name in found_names:
            matched_records = medicine_search_engine.search_medicine(name, limit=1)
            if matched_records:
                results.append(matched_records[0])
            else:
                results.append({"medicine_name": name, "generic_name": name, "primary_indication": "Symptomatic treatment"})

        return results

medicine_detector = MedicineDetector()
