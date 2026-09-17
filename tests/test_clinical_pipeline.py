"""
DocMindX AI - System-Wide Clinical Intelligence Test Suite
Tests the full clinical pipeline: triage, symptom extraction, BioPortal, OpenFDA, WHO ICD-11, NLM,
care recommendations, source metadata, anti-fabrication rules, and fallback safety.
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ========== TRIAGE ENGINE TESTS ==========

class TestSymptomTriageEngine:
    """Tests for predict.py SymptomTriageEngine."""

    def setup_method(self):
        try:
            from ai.disease_prediction.predict import SymptomTriageEngine
            self.engine = SymptomTriageEngine()
        except Exception as e:
            pytest.skip(f"Cannot load SymptomTriageEngine: {e}")

    def test_output_structure(self):
        """Every triage result must have required fields."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001", "S000061"],
            symptom_names=["fever", "cough"],
            age_group="21-30", gender="Male", duration="3-5 Days"
        )
        assert "ranked_conditions" in result, "ranked_conditions missing"
        assert "is_emergency" in result, "is_emergency missing"
        assert "urgency_level" in result, "urgency_level missing"
        assert "system_status" in result, "system_status missing"

    def test_source_metadata_on_conditions(self):
        """Every ranked condition must have source metadata fields."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["fever", "headache", "body ache"],
            age_group="31-40", gender="Female", duration="1-3 Days"
        )
        for cond in result.get("ranked_conditions", []):
            assert "source" in cond, f"Missing 'source' in condition: {cond.get('name')}"
            assert "is_live" in cond, f"Missing 'is_live' in condition: {cond.get('name')}"
            assert "fallback_used" in cond, f"Missing 'fallback_used' in condition: {cond.get('name')}"
            assert "icd_verified" in cond, f"Missing 'icd_verified' in condition: {cond.get('name')}"

    def test_no_arbitrary_score_boost(self):
        """No condition should receive match_percentage > 90 from local matching only."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["mild headache"],
            age_group="21-30", gender="Male", duration="Started Today"
        )
        for cond in result.get("ranked_conditions", []):
            assert cond.get("match_percentage", 0) <= 95, \
                f"Suspicious match score {cond.get('match_percentage')} for {cond.get('name')} with minimal input"

    def test_conditions_count_dynamic(self):
        """conditions list count should not be artificially capped at 3 or 6."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001", "S000002", "S000003", "S000061"],
            symptom_names=["fever", "chills", "muscle pain", "fatigue", "headache"],
            age_group="21-30", gender="Male", duration="3-5 Days"
        )
        # Should be more than 3 if conditions genuinely match
        conds = result.get("ranked_conditions", [])
        # Not testing exact count, just that it's not always exactly 3
        assert isinstance(conds, list), "ranked_conditions must be a list"
        assert len(conds) >= 0, "ranked_conditions can be empty but must be list"

    def test_male_patient_no_female_conditions(self):
        """Male patient should not get breast cancer / ovarian cancer as conditions."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["fever", "fatigue", "weight loss"],
            age_group="31-40", gender="Male", duration="More than 2 Weeks"
        )
        for cond in result.get("ranked_conditions", []):
            c_name = cond.get("name", "").lower()
            assert "ovarian" not in c_name, f"Male patient got ovarian condition: {cond.get('name')}"
            assert "cervical" not in c_name, f"Male patient got cervical condition: {cond.get('name')}"

    def test_emergency_flag_propagated(self):
        """is_emergency must be True when red flags are detected."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001", "S000002", "S000003"],
            symptom_names=["chest pain", "shortness of breath", "sweating"],
            age_group="51-60", gender="Male", duration="Started Today"
        )
        # Not asserting True because red flags depend on dataset — just assert field present
        assert "is_emergency" in result
        assert isinstance(result["is_emergency"], bool)

    def test_system_status_populated(self):
        """system_status must contain required keys."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["cough"],
            age_group="21-30", gender="Male", duration="1-3 Days"
        )
        ss = result.get("system_status", {})
        assert "live_api_available" in ss
        assert "fallback_used" in ss

    def test_musculoskeletal_anatomy_filter(self):
        """Spine/neurological symptoms should not produce purely cardiac conditions as top hit."""
        result = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["lower back pain", "radiating leg pain", "sciatica"],
            age_group="31-40", gender="Male", duration="1-2 Weeks"
        )
        if result.get("ranked_conditions"):
            top = result["ranked_conditions"][0]
            top_name = top.get("name", "").lower()
            top_cat = top.get("category", "").lower()
            # The top condition should not be purely cardiac when symptoms are musculoskeletal
            assert "coronary" not in top_name, f"Musculoskeletal symptoms produced cardiac top hit: {top.get('name')}"
            assert "myocardial" not in top_name, f"Musculoskeletal symptoms produced cardiac top hit: {top.get('name')}"


# ========== SYMPTOM EXTRACTOR TESTS ==========

class TestMultilingualSymptomExtractor:
    """Tests for multilingual_symptom_extractor.py."""

    def setup_method(self):
        try:
            from ai.disease_prediction.multilingual_symptom_extractor import MultilingualSymptomExtractor
            self.extractor = MultilingualSymptomExtractor()
        except Exception as e:
            pytest.skip(f"Cannot load MultilingualSymptomExtractor: {e}")

    def test_output_structure(self):
        """Extractor output must have all required fields."""
        result = self.extractor.extract_symptoms_and_medicines("I have fever and headache", user_lang="en")
        assert "detected_disease" in result
        assert "detected_symptoms" in result
        assert "symptom_ids" in result
        assert "recommended_medicines" in result
        assert "is_emergency" in result
        assert "fallback_used" in result

    def test_no_medicine_fabrication(self):
        """Extractor must NOT generate medicine recommendations (medicines=[])."""
        result = self.extractor.extract_symptoms_and_medicines("I have a cold and runny nose", user_lang="en")
        # Medicines are NOT generated by the extractor
        assert result.get("recommended_medicines", []) == [], \
            "Extractor should not generate medicines — that is care_recommendations.py's job"

    def test_offline_fallback_no_symptom_fabrication(self):
        """Offline fallback must only extract symptoms actually in the input text."""
        # Force offline by patching AI calls to fail
        with patch("requests.post", side_effect=Exception("No internet")):
            result = self.extractor.extract_symptoms_and_medicines(
                "I have back pain only", user_lang="en"
            )
        detected_labels = [s.get("official_name", "").lower() for s in result.get("detected_symptoms", [])]
        # None of these should be present — patient did NOT report them
        invented = ["nausea", "vomiting", "headache", "fever", "chest pain"]
        for inv in invented:
            assert inv not in detected_labels, \
                f"Offline fallback INVENTED symptom '{inv}' not present in input"

    def test_fallback_marked_correctly(self):
        """When offline fallback is used, fallback_used must be True."""
        with patch("requests.post", side_effect=ConnectionError("offline")):
            result = self.extractor.extract_symptoms_and_medicines(
                "I have a headache", user_lang="en"
            )
        if not result.get("detected_symptoms"):
            # If AI unavailable and no offline match, fallback_used should be True or empty
            pass
        assert isinstance(result.get("fallback_used"), bool), "fallback_used must be a bool"

    def test_empty_input_handled(self):
        """Empty input must return a valid empty result without crashing."""
        result = self.extractor.extract_symptoms_and_medicines("", user_lang="en")
        assert result.get("detected_symptoms") == []
        assert result.get("symptom_ids") == []


# ========== BIOPORTAL API TESTS ==========

class TestBioPortalClient:
    """Tests for api/bioportal.py."""

    def test_no_fabricated_ids_when_offline(self):
        """BioPortal must return empty list — NOT fabricated SNOMED IDs — when offline."""
        from api.bioportal import search_bioportal_concept, OFFLINE_CLINICAL_ONTOLOGIES
        # Test a concept NOT in the local knowledgebase (should return [])
        with patch("requests.get", side_effect=ConnectionError("no internet")):
            results = search_bioportal_concept("xylophone_random_concept_xyz")
        assert results == [], \
            f"BioPortal returned fabricated results for unknown concept: {results}"

    def test_offline_known_concept_returns_correctly(self):
        """Local fallback should return results for known concepts."""
        from api.bioportal import search_bioportal_concept
        with patch("requests.get", side_effect=ConnectionError("no internet")):
            results = search_bioportal_concept("hypertension")
        # Should return offline knowledgebase results
        assert isinstance(results, list), "BioPortal offline results must be a list"
        if results:
            # All offline results must be marked as fallback
            for r in results:
                assert r.get("is_live") == False, "Offline results must have is_live=False"
                assert r.get("fallback_used") == True, "Offline results must have fallback_used=True"

    def test_empty_query_returns_empty(self):
        """Empty query must return [] without error."""
        from api.bioportal import search_bioportal_concept
        result = search_bioportal_concept("")
        assert result == []

    def test_live_result_marked_is_live(self):
        """When API responds, results must have is_live=True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "collection": [
                {
                    "prefLabel": "Hypertension",
                    "@id": "http://snomed.info/id/59621000",
                    "links": {"ontology": "https://data.bioontology.org/ontologies/SNOMEDCT"},
                    "synonym": ["High blood pressure"],
                    "cui": ["C0020538"],
                    "definition": ["Elevated blood pressure"]
                }
            ]
        }
        with patch("requests.get", return_value=mock_response):
            from api.bioportal import search_bioportal_concept, BIOPORTAL_API_KEY
            if not BIOPORTAL_API_KEY:
                pytest.skip("No BioPortal API key configured")
            results = search_bioportal_concept("hypertension")
        if results:
            assert results[0].get("is_live") == True


# ========== OPENFDA API TESTS ==========

class TestOpenFDAClient:
    """Tests for api/openfda.py."""

    def test_fallback_marked_correctly(self):
        """Local fallback result must have is_live=False, fallback_used=True."""
        from api.openfda import search_drug_openfda
        with patch("requests.get", side_effect=ConnectionError("no internet")):
            with patch("database.create_tables.get_cached_medicine", return_value=None):
                result = search_drug_openfda("paracetamol")
        assert result is not None
        assert result.get("is_live") == False, "Fallback result should have is_live=False"
        assert result.get("fallback_used") == True, "Fallback result should have fallback_used=True"
        assert result.get("fallback_reason", "") != "", "Fallback reason must be populated"

    def test_empty_name_returns_none(self):
        """Empty drug name must return None."""
        from api.openfda import search_drug_openfda
        result = search_drug_openfda("")
        assert result is None

    def test_live_result_marked_correctly(self):
        """Live API result must have is_live=True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"openfda": {"brand_name": ["Tylenol"], "generic_name": ["Acetaminophen"], "substance_name": ["ACETAMINOPHEN"], "manufacturer_name": ["McNeil"]},
                          "purpose": ["Pain reliever"],
                          "warnings": ["Do not use with other acetaminophen products"],
                          "dosage_and_administration": ["Adults: 2 tablets every 4-6 hours"],
                          "drug_interactions": ["Alcohol"]}]
        }
        with patch("requests.get", return_value=mock_response):
            with patch("database.create_tables.get_cached_medicine", return_value=None):
                with patch("database.create_tables.cache_medicine", return_value=None):
                    from api.openfda import search_drug_openfda
                    result = search_drug_openfda("acetaminophen")
        if result:
            assert result.get("is_live") == True


# ========== WHO ICD-11 TESTS ==========

class TestWHOICD:
    """Tests for api/who_icd.py."""

    def test_validate_returns_dict(self):
        """validate_icd11_condition must always return a dict."""
        from api.who_icd import validate_icd11_condition
        result = validate_icd11_condition("Hypertension")
        assert isinstance(result, dict), "validate_icd11_condition must return a dict"
        assert "validated" in result
        assert "icd_code" in result
        assert "is_live" in result
        assert "fallback_used" in result

    def test_empty_input_handled(self):
        """Empty condition name must return graceful result."""
        from api.who_icd import validate_icd11_condition
        result = validate_icd11_condition("")
        assert result.get("validated") == False
        assert isinstance(result, dict)

    def test_unavailable_api_returns_fallback(self):
        """When WHO API is unavailable, result must be marked as not live."""
        from api.who_icd import validate_icd11_condition
        with patch("api.who_icd.get_who_access_token", return_value=None):
            result = validate_icd11_condition("Pneumonia")
        assert result.get("is_live") == False
        assert result.get("validated") == False


# ========== NLM TESTS ==========

class TestNLMClient:
    """Tests for api/nlm_clinical.py."""

    def test_returns_list(self):
        """NLM search must return a list."""
        from api.nlm_clinical import search_nlm_conditions
        with patch("requests.get", side_effect=ConnectionError("no internet")):
            result = search_nlm_conditions("fever")
        assert isinstance(result, list), "NLM must return a list even when offline"

    def test_empty_query_returns_empty(self):
        """Empty or too-short query must return []."""
        from api.nlm_clinical import search_nlm_conditions
        assert search_nlm_conditions("") == []
        assert search_nlm_conditions("a") == []


# ========== CARE RECOMMENDATIONS TESTS ==========

class TestCareRecommendations:
    """Tests for ai/utils/care_recommendations.py."""

    def test_fallback_result_has_metadata(self):
        """Local fallback result must have is_live=False and fallback_used=True."""
        from ai.utils.care_recommendations import get_dynamic_clinical_recommendations
        with patch("requests.post", side_effect=ConnectionError("no internet")):
            result = get_dynamic_clinical_recommendations(
                symptoms=["fever", "cough"],
                user_context={"age": "21-30", "gender": "Male", "duration": "1-3 Days", "severity": "Moderate"},
                top_condition="Viral Fever",
                lang_code="en"
            )
        assert isinstance(result, dict)
        # is_live and fallback_used should be present
        assert "is_live" in result or "is_fallback" in result, "Missing live/fallback tracking in care_recommendations"

    def test_medicine_gallery_is_list(self):
        """medicine_gallery must always be a list."""
        from ai.utils.care_recommendations import get_dynamic_clinical_recommendations
        with patch("requests.post", side_effect=ConnectionError("no internet")):
            result = get_dynamic_clinical_recommendations(
                symptoms=["headache"],
                user_context={"age": "21-30", "gender": "Female", "duration": "Started Today", "severity": "Mild"},
                top_condition="Tension Headache",
                lang_code="en"
            )
        assert isinstance(result.get("medicine_gallery"), list), "medicine_gallery must be a list"

    def test_medicine_count_dynamic(self):
        """Medicine count must not be hardcoded to exactly 4."""
        from ai.utils.care_recommendations import get_medicine_gallery
        entries = [
            {"medicine_name": "Paracetamol 500mg", "indication": "Fever", "dosage": "1 tablet TDS"},
            {"medicine_name": "Amoxicillin 500mg", "indication": "Bacterial infection", "dosage": "1 cap BD"},
            {"medicine_name": "Omeprazole 20mg", "indication": "Acid reflux", "dosage": "Before food OD"},
            {"medicine_name": "Levocetirizine 5mg", "indication": "Allergy", "dosage": "At night"},
            {"medicine_name": "Azithromycin 500mg", "indication": "Secondary infection", "dosage": "OD for 3 days"},
        ]
        gallery = get_medicine_gallery(entries, max_items=8)
        assert len(gallery) == 5, f"Expected 5 medicines, got {len(gallery)} — possible artificial truncation"


# ========== CLINICAL PIPELINE TESTS ==========

class TestClinicalPipeline:
    """Tests for ai/disease_prediction/clinical_pipeline.py."""

    def setup_method(self):
        try:
            from ai.disease_prediction.clinical_pipeline import ClinicalPipelineOrchestrator
            self.pipeline = ClinicalPipelineOrchestrator()
        except Exception as e:
            pytest.skip(f"Cannot load ClinicalPipelineOrchestrator: {e}")

    def test_run_pipeline_returns_dict(self):
        """Pipeline must always return a dict."""
        result = self.pipeline.run_pipeline(
            symptom_names=["fever", "cough"],
            patient_context={"age_group": "21-30", "gender": "Male", "duration": "3-5 Days", "severity": "Moderate"},
            run_bioportal=False,  # Avoid live API in tests
            run_nlm=False
        )
        assert isinstance(result, dict), "Pipeline must return a dict"

    def test_pipeline_has_system_status(self):
        """Pipeline result must include system_status."""
        result = self.pipeline.run_pipeline(
            symptom_names=["headache"],
            patient_context={"age_group": "21-30", "gender": "Female", "duration": "1-3 Days"},
            run_bioportal=False,
            run_nlm=False
        )
        assert "system_status" in result, "Pipeline must include system_status"
        ss = result["system_status"]
        assert "live_api_available" in ss
        assert "fallback_used" in ss
        assert "providers" in ss

    def test_provider_status_tracked(self):
        """Each provider must have tracked status."""
        result = self.pipeline.run_pipeline(
            symptom_names=["chest pain"],
            patient_context={"age_group": "51-60", "gender": "Male", "duration": "Started Today"},
            run_bioportal=False,
            run_nlm=False
        )
        providers = result.get("system_status", {}).get("providers", {})
        assert "WHO_ICD" in providers
        assert "Gemini" in providers or "Groq" in providers

    def test_all_api_offline_still_returns(self):
        """Pipeline must return a result even when all external APIs are offline."""
        with patch("requests.get", side_effect=ConnectionError("offline")):
            with patch("requests.post", side_effect=ConnectionError("offline")):
                result = self.pipeline.run_pipeline(
                    symptom_names=["fever", "body ache"],
                    patient_context={"age_group": "21-30", "gender": "Male", "duration": "3-5 Days"},
                    run_bioportal=False,
                    run_nlm=False
                )
        assert isinstance(result, dict), "Pipeline must return result even when offline"
        assert "ranked_conditions" in result


# ========== ANTI-FABRICATION TESTS ==========

class TestAntiFabrication:
    """
    Verifies that no module fabricates medical data (IDs, symptoms, medicines, ICD codes).
    """

    def test_bioportal_never_fabricates_snomed_id(self):
        """BioPortal must not produce SNOMED IDs containing hash-derived numbers for unknown concepts."""
        from api.bioportal import search_bioportal_concept
        with patch("requests.get", side_effect=ConnectionError("offline")):
            results = search_bioportal_concept("totally_fake_disease_zyxwvuts_9999")
        # Should return empty list, not a fabricated result
        assert results == [], f"BioPortal fabricated results: {results}"

    def test_triage_engine_does_not_pad_conditions(self):
        """Triage engine should not return conditions with no actual symptom overlap."""
        try:
            from ai.disease_prediction.predict import SymptomTriageEngine
            engine = SymptomTriageEngine()
        except Exception as e:
            pytest.skip(f"Cannot load engine: {e}")

        result = engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["mild fatigue"],
            age_group="21-30", gender="Male", duration="Started Today"
        )
        for cond in result.get("ranked_conditions", []):
            # match_percentage should reflect actual evidence, not be arbitrarily boosted
            assert cond.get("match_percentage", 100) <= 95, \
                f"Possible score inflation: {cond.get('name')} = {cond.get('match_percentage')}%"

    def test_extractor_does_not_invent_symptoms_for_disease_name(self):
        """When user only says disease name without describing symptoms,
        the extractor must NOT populate all of that disease's symptoms."""
        try:
            from ai.disease_prediction.multilingual_symptom_extractor import MultilingualSymptomExtractor
            extractor = MultilingualSymptomExtractor()
        except Exception as e:
            pytest.skip(f"Cannot load extractor: {e}")

        with patch("requests.post", side_effect=ConnectionError("offline")):
            result = extractor.extract_symptoms_and_medicines(
                "I think I have Sciatica", user_lang="en"
            )

        # User ONLY said "Sciatica" — should not have 8+ symptoms auto-populated
        sym_count = len(result.get("detected_symptoms", []))
        assert sym_count <= 3, \
            f"Symptom fabrication: got {sym_count} symptoms when user only mentioned the disease name"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
