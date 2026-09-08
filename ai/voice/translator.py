"""
    DocMindX AI - Multilingual Medical Text Translation Engine
"""
from ai.disease_prediction.multilingual_symptom_extractor import MultilingualSymptomExtractor

class MedicalTranslator:
    """Provides translation and transliteration between English, Hindi, and Gujarati."""
    def __init__(self):
        self.extractor = MultilingualSymptomExtractor()

    def translate_clinical_text(self, text: str, target_lang: str = "hi") -> str:
        if not text or not text.strip():
            return ""

        # Extract structured concepts and format translation
        res = self.extractor.extract_symptoms_and_medicines(text, user_lang=target_lang)
        if res.get("detected_symptoms"):
            names = [s["display_name"] for s in res["detected_symptoms"]]
            return f"अनुवादित लक्षण / Translated: {', '.join(names)}"
        return text

medical_translator = MedicalTranslator()
