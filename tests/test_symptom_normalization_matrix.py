"""
DocMindX AI — System-Wide Multilingual Symptom Normalization, Dataset Matching & WHO Warning Test Matrix
Covers Test Cases A through U as required in the system specification.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from unittest.mock import patch, MagicMock
from ai.disease_prediction.canonical_concepts import canonical_normalizer
from ai.disease_prediction.multilingual_symptom_extractor import normalize_user_symptoms, MultilingualSymptomExtractor
from ai.disease_prediction.predict import SymptomTriageEngine, _parse_duration_days
from ai.disease_prediction.clinical_pipeline import ClinicalPipelineOrchestrator, ProviderStatus
from api.who_icd import search_who_icd11_structured, validate_icd11_condition


class TestSymptomNormalizationMatrix:
    """Test Suite covering Cases A through U."""

    def setup_method(self):
        import api.who_icd as who_icd
        who_icd._circuit_open_until = 0

    # A. English: "fever for 2 days"
    def test_case_a_english(self):
        norm = canonical_normalizer.normalize("fever for 2 days")
        assert "S000001" in norm.symptom_ids
        assert norm.duration_days == 2

    # B. Gujarati: "2 divas thi tav aave chhe"
    def test_case_b_gujarati(self):
        norm = canonical_normalizer.normalize("2 divas thi tav aave chhe")
        assert "S000001" in norm.symptom_ids
        assert norm.duration_days == 2

    # C. Roman Gujarati: "2 divas thi tav ave chhe"
    def test_case_c_roman_gujarati(self):
        norm = canonical_normalizer.normalize("2 divas thi tav ave chhe")
        assert "S000001" in norm.symptom_ids
        assert norm.duration_days == 2

    # D. Hindi: "दो दिन से बुखार है"
    def test_case_d_hindi(self):
        norm = canonical_normalizer.normalize("दो दिन से बुखार है")
        assert "S000001" in norm.symptom_ids
        assert norm.duration_days == 2

    # E. Mixed language: "2 divas se tav ave chhe aur gala burning chhe"
    def test_case_e_mixed_language(self):
        norm = canonical_normalizer.normalize("2 divas se tav ave chhe aur gala burning chhe")
        assert "S000001" in norm.symptom_ids
        assert norm.duration_days == 2

    # F. Multiple symptoms: "tav, galu bale chhe, pag ma dukhe chhe, chakar ave chhe"
    def test_case_f_multiple_symptoms(self):
        res = normalize_user_symptoms("tav, galu bale chhe, pag ma dukhe chhe, chakar ave chhe")
        assert len(res) >= 2
        # Check that individual symptoms are structured
        matched = [r for r in res if r["dataset_match"]]
        assert len(matched) >= 1
        # Internal S-IDs must exist in backend object but user phrases are preserved
        for r in res:
            assert "user_phrase" in r
            assert "normalized_english" in r
            assert "dataset_match" in r
            assert "match_status" in r

    # G. Spelling variation: "taav ave che"
    def test_case_g_spelling_variation(self):
        norm = canonical_normalizer.normalize("taav ave che")
        assert "S000001" in norm.symptom_ids

    # H. Unmatched phrase: "aje ajeeb lage chhe"
    def test_case_h_unmatched_phrase(self):
        det = canonical_normalizer.bridge.match_symptom_detailed("aje ajeeb lage chhe")
        assert det["dataset_match"] is False
        assert det["match_type"] == "UNMATCHED"
        assert det["match_status"] == "Not Matched"

    # I. Ambiguous symptom: "pag ma dukhe chhe"
    def test_case_i_ambiguous_symptom(self):
        # Must not fabricate sciatica (S000144) without back pain evidence
        norm = canonical_normalizer.normalize("pag ma dukhe chhe")
        assert "S000144" not in norm.symptom_ids

    # J. WHO API 200 + relevant match
    def test_case_j_who_200_match(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "destinationEntities": [
                {"id": "http://id.who.int/icd/entity/123", "title": "Hypertension", "theCode": "BA00", "chapter": "11"}
            ]
        }
        with patch("api.who_icd.get_who_access_token", return_value="fake_token"), \
             patch("requests.get", return_value=mock_response):
            res = search_who_icd11_structured("Hypertension")
            assert res["status"] == "SUCCESS"
            assert res["is_live"] is True
            assert res["fallback_used"] is False
            assert len(res["results"]) > 0

    # K. WHO API 200 + no relevant match
    def test_case_k_who_200_no_match(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"destinationEntities": []}
        with patch("api.who_icd.get_who_access_token", return_value="fake_token"), \
             patch("requests.get", return_value=mock_response):
            res = search_who_icd11_structured("NonExistentDisease12345XYZ")
            assert res["status"] == "NO_RELEVANT_RESULT"
            assert res["is_live"] is True
            assert res["fallback_used"] is False
            assert len(res["results"]) == 0

    # L. WHO timeout
    def test_case_l_who_timeout(self):
        import requests
        import api.who_icd as who_icd
        who_icd._circuit_open_until = 0
        with patch("api.who_icd.get_who_access_token", return_value="fake_token"), \
             patch("requests.get", side_effect=requests.exceptions.Timeout()):
            res = search_who_icd11_structured("Hypertension")
            assert res["status"] == "TIMEOUT"
            assert res["is_live"] is False
            assert res["fallback_used"] is True

    # M. WHO authentication failure
    def test_case_m_who_auth_failure(self):
        import api.who_icd as who_icd
        who_icd._circuit_open_until = 0
        mock_response = MagicMock()
        mock_response.status_code = 401
        with patch("api.who_icd.get_who_access_token", return_value="fake_token"), \
             patch("requests.get", return_value=mock_response):
            res = search_who_icd11_structured("Hypertension")
            assert res["status"] == "AUTH_ERROR"
            assert res["is_live"] is False
            assert res["fallback_used"] is True

    # N. Gemini unavailable
    def test_case_n_gemini_unavailable(self):
        extractor = MultilingualSymptomExtractor()
        with patch("config.settings.gemini_pool.get_active_keys", return_value=[]), \
             patch("config.settings.GROQ_API_KEY", ""):
            res = extractor.extract_symptoms_and_medicines("2 divas thi tav aave chhe", user_lang="gu")
            assert "S000001" in res["symptom_ids"]

    # O. Dataset match success
    def test_case_o_dataset_match_success(self):
        det = canonical_normalizer.bridge.match_symptom_detailed("Fever")
        assert det["dataset_match"] is True
        assert det["dataset_name"] == "Fever"
        assert det["symptom_id"] == "S000001"
        assert det["match_status"] == "Matched"

    # P. Dataset match failure
    def test_case_p_dataset_match_failure(self):
        det = canonical_normalizer.bridge.match_symptom_detailed("Unusual Random Feeling XYZ")
        assert det["dataset_match"] is False
        assert det["dataset_name"] is None
        assert det["match_status"] == "Not Matched"

    # Q. Duration 1 day -> No routine tests
    def test_case_q_duration_1_day(self):
        engine = SymptomTriageEngine()
        res = engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["Fever"],
            duration="1 day"
        )
        assert res["tests_to_discuss"] == []

    # R. Duration 3 days -> No routine tests
    def test_case_r_duration_3_days(self):
        engine = SymptomTriageEngine()
        res = engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["Fever"],
            duration="3 days"
        )
        assert res["tests_to_discuss"] == []

    # S. Duration 4 days -> No routine tests
    def test_case_s_duration_4_days(self):
        engine = SymptomTriageEngine()
        res = engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["Fever"],
            duration="4 days"
        )
        assert res["tests_to_discuss"] == []

    # T. Duration 5 days -> Routine tests allowed
    def test_case_t_duration_5_days(self):
        engine = SymptomTriageEngine()
        res = engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["Fever"],
            duration="5 days"
        )
        assert isinstance(res["tests_to_discuss"], list)
        assert len(res["tests_to_discuss"]) > 0

    # U. Duration 14 days -> Routine tests allowed
    def test_case_u_duration_14_days(self):
        engine = SymptomTriageEngine()
        res = engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["Fever"],
            duration="14 days"
        )
        assert isinstance(res["tests_to_discuss"], list)
        assert len(res["tests_to_discuss"]) > 0

    # Emergency Override Test
    def test_emergency_override_duration_gate(self):
        engine = SymptomTriageEngine()
        # S000046 = Chest Pain (cardiac emergency/red flag candidate)
        res = engine.evaluate_symptoms(
            selected_symptom_ids=["S000046"],
            symptom_names=["Severe Chest Pain"],
            duration="1 day"
        )
        # Even with 1 day, if emergency red flag is active or condition is emergency, tests can appear
        assert res["urgency_level"] != "Mild / Self-Monitoring"
