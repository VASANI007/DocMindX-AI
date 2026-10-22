import pytest
from ai.disease_prediction.multilingual_symptom_extractor import MultilingualSymptomExtractor
from tests.validation_campaign.clinical_manifest import VOICE_IMAGE_TEST_CASES

class TestVoiceImageWorkflow:
    """Category E: Voice & Image (OCR) Workflow Integration Test Suite (30 Cases)."""

    @classmethod
    def setup_class(cls):
        cls.extractor = MultilingualSymptomExtractor()

    @pytest.mark.parametrize("case", VOICE_IMAGE_TEST_CASES, ids=[c["id"] for c in VOICE_IMAGE_TEST_CASES])
    def test_voice_image_case(self, case):
        cid = case["id"]
        ctype = case.get("type", "voice")
        text = case.get("transcript") if ctype == "voice" else case.get("report_text")
        expected_ids = set(case.get("expected_ids", []))
        negated_ids = set(case.get("negated_ids", []))

        # Detect or default language
        lang = "gu" if "mane" in text.lower() or "divas" in text.lower() else ("hi" if "dard" in text.lower() and "pet" in text.lower() else "en")

        result = self.extractor.extract_symptoms_and_medicines(text, user_lang=lang, offline=True)

        detected = result.get("detected_symptoms", [])
        detected_ids = set(result.get("symptom_ids", []))
        for d in detected:
            if "symptom_id" in d:
                detected_ids.add(d["symptom_id"])

        for exp in expected_ids:
            assert exp in detected_ids, (
                f"Case {cid} ({ctype}) failed: expected symptom ID '{exp}' "
                f"not found in detected: {detected_ids}. Input: '{text}'"
            )

        for neg in negated_ids:
            assert neg not in detected_ids, (
                f"Case {cid} ({ctype}) failed negation check: negated symptom ID '{neg}' "
                f"erroneously emitted in detected: {detected_ids}. Input: '{text}'"
            )
