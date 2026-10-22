import pytest
from ai.disease_prediction.multilingual_symptom_extractor import MultilingualSymptomExtractor
from tests.validation_campaign.clinical_manifest import MULTILINGUAL_TEST_CASES

class TestMultilingualValidation:
    @classmethod
    def setup_class(cls):
        cls.extractor = MultilingualSymptomExtractor()

    @pytest.mark.parametrize("case", MULTILINGUAL_TEST_CASES, ids=[c["id"] for c in MULTILINGUAL_TEST_CASES])
    def test_multilingual_extraction_case(self, case):
        text = case["text"]
        lang = case.get("lang", "en")
        expected_ids = set(case.get("expected_ids", []))
        negated_ids = set(case.get("negated_ids", []))

        # Test offline canonical multilingual extraction deterministically
        result = self.extractor.extract_symptoms_and_medicines(text, user_lang=lang, offline=True)

        detected = result.get("detected_symptoms", [])
        detected_ids = set(result.get("symptom_ids", []))
        for d in detected:
            if "symptom_id" in d:
                detected_ids.add(d["symptom_id"])

        # Check expected IDs are present
        for exp in expected_ids:
            assert exp in detected_ids, (
                f"Case {case['id']} ('{text}') [lang={lang}] failed: expected symptom ID '{exp}' "
                f"not found in detected: {detected_ids}"
            )

        # Check negated IDs are NOT present
        for neg in negated_ids:
            assert neg not in detected_ids, (
                f"Case {case['id']} ('{text}') [lang={lang}] failed negation check: negated symptom ID '{neg}' "
                f"was erroneously emitted in detected: {detected_ids}"
            )
