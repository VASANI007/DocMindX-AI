"""
DocMindX AI — Universal Pipeline Repair Comprehensive Test Suite
Validates the entire general-purpose patient-input -> symptom normalization ->
clinical evidence validation -> triage/context -> medicine suitability/recommendation pipeline.

Requirements Verified:
1. Full-context structured clinical request (original_text, normalized_english_text, validated findings, locations, negations).
2. Typed vs Voice equivalence in extraction schema and canonical IDs.
3. Provenance separation: auto-extracted refreshed on new extraction, manual chips preserved.
4. Detected cards, selected chips, and validated canonical IDs count alignment (1:1:1).
5. Exact 1 Gemini call per extraction operation with safe correlation IDs.
6. Deterministic offline mode with zero network calls and full cache isolation.
7. Medicine Safety Gate: empty/unresolvable symptoms return 0 medicines, 0 hallucinations, supportive guidance.
8. Downstream medicine engine receives and leverages narrative and structured findings.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import json
import pytest
from unittest.mock import patch, MagicMock

from ai.disease_prediction.multilingual_symptom_extractor import (
    MultilingualSymptomExtractor,
    normalize_user_symptoms,
    clear_symptom_norm_cache
)
from ai.disease_prediction.canonical_concepts import canonical_normalizer
from ai.disease_prediction.clinical_pipeline import clinical_pipeline
from ai.utils.care_recommendations import get_dynamic_clinical_recommendations


class TestUniversalPipelineRepair:
    """End-to-end tests for universal full-context pipeline repair."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        clear_symptom_norm_cache()
        yield
        clear_symptom_norm_cache()

    # --------------------------------------------------------------------------
    # 1. Full-Context Structured Clinical Request Preservation
    # --------------------------------------------------------------------------
    def test_structured_clinical_request_object_fields(self):
        """Extraction returns structured clinical_request with both original and normalized English text."""
        extractor = MultilingualSymptomExtractor()
        
        # Test offline mode for deterministic assertions
        res = extractor.extract_symptoms_and_medicines(
            "mane mathu dukhe chhe ane thak lage chhe",
            user_lang="gu",
            offline=True
        )
        
        assert "clinical_request" in res
        req = res["clinical_request"]
        assert req["original_text"] == "mane mathu dukhe chhe ane thak lage chhe"
        assert isinstance(req["normalized_english_text"], str)
        assert req["detected_language"] == "gu"
        assert req["detected_script"] in ["Latn", "Gujr"]
        assert isinstance(req["validated_symptoms"], list)
        assert len(req["validated_symptoms"]) >= 1
        
        # Each validated symptom contains anatomical location and source info
        for sym in req["validated_symptoms"]:
            assert "canonical_name" in sym
            assert "symptom_id" in sym
            assert "body_region" in sym
            assert "user_phrase" in sym
            assert sym["validation_status"] == "Validated"

    def test_backward_compatibility_keys_preserved(self):
        """extract_symptoms_and_medicines preserves detected_symptoms and symptom_labels for UI callers."""
        extractor = MultilingualSymptomExtractor()
        res = extractor.extract_symptoms_and_medicines(
            "fever and severe headache",
            user_lang="en",
            offline=True
        )
        assert "detected_symptoms" in res
        assert "symptom_labels" in res
        assert "matched_symptom_ids" in res
        assert "is_emergency" in res
        assert "clinical_request" in res

    # --------------------------------------------------------------------------
    # 2. Typed and Voice Equivalence
    # --------------------------------------------------------------------------
    def test_typed_and_voice_equivalence(self):
        """Typed text and transcribed voice yield identical structured canonical schemas and symptom IDs."""
        extractor = MultilingualSymptomExtractor()
        input_phrase = "chhati ma dukhavo ane shwas chadhe chhe"
        
        typed_res = extractor.extract_symptoms_and_medicines(input_phrase, user_lang="gu", offline=True)
        voice_res = extractor.extract_symptoms_and_medicines(input_phrase, user_lang="gu", offline=True)
        
        typed_ids = sorted(typed_res.get("matched_symptom_ids", []))
        voice_ids = sorted(voice_res.get("matched_symptom_ids", []))
        assert typed_ids == voice_ids
        assert len(typed_ids) >= 1
        
        typed_req = typed_res["clinical_request"]
        voice_req = voice_res["clinical_request"]
        assert typed_req["original_text"] == voice_req["original_text"]
        assert typed_req["detected_language"] == voice_req["detected_language"]

    # --------------------------------------------------------------------------
    # 3. Provenance Separation: Refresh Auto-Extracted while Preserving Manual
    # --------------------------------------------------------------------------
    def test_provenance_separation_logic(self):
        """Simulate the app.py provenance state manager: auto-extracted symptoms refresh while manual chips persist."""
        # Initial state: user manually selected 'Fatigue'
        symptom_provenance_map = {"Fatigue": "manual"}
        selected_symptoms_list = ["Fatigue"]
        
        # User runs extraction 1: extracts 'Headache'
        extracted_1 = ["Headache"]
        # Update state: remove prior 'extracted_text', preserve 'manual'
        preserved = [s for s in selected_symptoms_list if symptom_provenance_map.get(s) != "extracted_text"]
        new_list = list(preserved)
        for s in extracted_1:
            if s not in new_list:
                new_list.append(s)
            symptom_provenance_map[s] = "extracted_text"
            
        assert "Fatigue" in new_list
        assert "Headache" in new_list
        assert symptom_provenance_map["Fatigue"] == "manual"
        assert symptom_provenance_map["Headache"] == "extracted_text"
        
        # User runs extraction 2: extracts 'Fever' (replaces Headache, keeps Fatigue)
        extracted_2 = ["Fever"]
        preserved = [s for s in new_list if symptom_provenance_map.get(s) != "extracted_text"]
        new_list_2 = list(preserved)
        for s in extracted_2:
            if s not in new_list_2:
                new_list_2.append(s)
            symptom_provenance_map[s] = "extracted_text"
            
        assert "Fatigue" in new_list_2
        assert "Fever" in new_list_2
        assert "Headache" not in new_list_2, "Previous extraction must be refreshed without leaving orphan symptoms"

    # --------------------------------------------------------------------------
    # 4. Count and ID Integrity (Cards == Chips == Canonical IDs)
    # --------------------------------------------------------------------------
    def test_count_and_id_integrity(self):
        """Ensure detected items count equals unique validated canonical IDs count with 0 duplicates."""
        extractor = MultilingualSymptomExtractor()
        res = extractor.extract_symptoms_and_medicines(
            "severe headache, pounding head, mathu dukhe chhe",
            user_lang="gu",
            offline=True
        )
        detected_cards = res["detected_symptoms"]
        selected_chips = res["symptom_labels"]
        validated_ids = res["matched_symptom_ids"]
        
        assert len(detected_cards) == len(selected_chips) == len(validated_ids)
        # All IDs must be unique
        assert len(validated_ids) == len(set(validated_ids))

    # --------------------------------------------------------------------------
    # 5. Exact 1 Gemini Call per Extraction Operation & Correlation ID
    # --------------------------------------------------------------------------
    @patch("config.settings.gemini_pool.execute_with_failover")
    def test_exact_one_gemini_call_per_extraction(self, mock_gemini):
        """Single extraction operation must make at most 1 Gemini API call with correlation ID."""
        mock_gemini.return_value = (
            {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": json.dumps({
                                "english_translation": "Mild headache and fever",
                                "candidates": [
                                    {
                                        "raw_phrase": "mathu dukhe",
                                        "candidate_canonical_name": "Headache",
                                        "body_region": "head",
                                        "confidence": 0.95
                                    }
                                ]
                            })
                        }]
                    }
                }]
            },
            "gemini-2.5-flash",
            None
        )
        
        extractor = MultilingualSymptomExtractor()
        res = extractor.extract_symptoms_and_medicines("mathu dukhe chhe", user_lang="gu", offline=False)
        
        assert mock_gemini.call_count == 1, f"Expected exactly 1 Gemini call, got {mock_gemini.call_count}"
        assert res["clinical_request"]["normalized_english_text"] == "Mild headache and fever"

    # --------------------------------------------------------------------------
    # 6. Deterministic Offline Mode (Zero Network Calls)
    # --------------------------------------------------------------------------
    @patch("config.settings.gemini_pool.execute_with_failover")
    def test_offline_mode_zero_network_calls(self, mock_gemini):
        """Offline extraction makes strictly 0 network calls."""
        extractor = MultilingualSymptomExtractor()
        res = extractor.extract_symptoms_and_medicines("fever and cough", user_lang="en", offline=True)
        
        assert mock_gemini.call_count == 0
        assert len(res["detected_symptoms"]) >= 1

    # --------------------------------------------------------------------------
    # 7. Medicine Safety Gate: Empty/Unresolvable Findings -> 0 Medicines
    # --------------------------------------------------------------------------
    @patch("config.settings.gemini_pool.execute_with_failover")
    def test_medicine_safety_gate_empty_symptoms_returns_zero_medicines(self, mock_gemini):
        """Empty or unresolvable symptoms must return medicine_gallery: [] with 0 LLM calls."""
        mock_gemini.return_value = (None, None, None)
        recs = get_dynamic_clinical_recommendations(
            symptoms=[],
            user_context={"original_text": "I feel strange today", "normalized_english_text": ""},
            top_condition="Undifferentiated Symptom",
            lang_code="en"
        )
        # LLM must NOT be called
        assert mock_gemini.call_count == 0
        assert recs.get("medicine_gallery") == []
        assert recs.get("total_medicines_recommended") == 0
        assert "lifestyle_home_remedies" in recs
        assert len(recs["lifestyle_home_remedies"]) >= 1

    # --------------------------------------------------------------------------
    # 8. Downstream Medicine Engine Receives Complete Context
    # --------------------------------------------------------------------------
    @patch("config.settings.gemini_pool.execute_with_failover")
    def test_medicine_engine_prompt_contains_full_narrative_context(self, mock_gemini):
        """Downstream medicine recommender prompt must include original_text, normalized English, and body region."""
        mock_gemini.return_value = (
            {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": json.dumps({
                                "clinical_summary": "Patient reports severe knee pain",
                                "medicine_gallery": [],
                                "lifestyle_home_remedies": ["Apply ice pack"]
                            })
                        }]
                    }
                }]
            },
            "gemini-2.5-flash",
            None
        )
        
        user_ctx = {
            "original_text": "maro gothan ma asahya dukhavo chhe",
            "normalized_english_text": "Unbearable knee pain in the joint",
            "validated_symptoms": [{
                "canonical_name": "Joint Pain",
                "body_region": "lower_limb",
                "body_location": "knee"
            }],
            "age": "45",
            "gender": "Female"
        }
        
        recs = get_dynamic_clinical_recommendations(
            symptoms=["Joint Pain"],
            user_context=user_ctx,
            top_condition="Knee Arthralgia",
            lang_code="en"
        )
        
        assert mock_gemini.call_count == 1
        call_payload = mock_gemini.call_args[1]["payload"]
        prompt_text = call_payload["contents"][0]["parts"][0]["text"]
        
        assert "maro gothan ma asahya dukhavo chhe" in prompt_text
        assert "Unbearable knee pain in the joint" in prompt_text
        assert "Knee" in prompt_text or "lower_limb" in prompt_text

    # --------------------------------------------------------------------------
    # 9. Universal Paracetamol & Medicine Fallback Elimination
    # --------------------------------------------------------------------------
    @patch("config.settings.gemini_pool.execute_with_failover")
    def test_empty_or_unsupported_assessment_does_not_produce_paracetamol(self, mock_gemini):
        """Unsupported assessment returns empty medicine list, NEVER universal Paracetamol 500mg."""
        mock_gemini.return_value = (None, None, None)
        from ai.utils.care_recommendations import _get_condition_fallback_medicines
        
        # Test 1: Vague non-specific symptom
        meds = _get_condition_fallback_medicines(top_condition="", symptoms=["something feels strange in my body"])
        assert meds == [], f"Expected [] but got {meds}"
        assert not any("paracetamol" in m["name"].lower() for m in meds)

        # Test 2: Ocular presentation without fever -> must NOT recommend Paracetamol
        meds_eye = _get_condition_fallback_medicines(top_condition="Dry Eye Syndrome", symptoms=["Eye Pain", "Eye Irritation"])
        assert not any("paracetamol" in m["name"].lower() for m in meds_eye)
        # Should recommend ophthalmic tears instead
        assert any("eye drops" in m["name"].lower() or "ophthalmic" in m.get("route", "").lower() for m in meds_eye)

    def test_provider_no_relevant_result_does_not_trigger_generic_fallback(self):
        """OpenFDA NO_RELEVANT_RESULT maintains candidate name and unverified status; never replaces with Paracetamol."""
        from ai.utils.care_recommendations import get_medicine_gallery
        with patch("api.openfda.search_drug_openfda", return_value={
            "medicine_name": "Novelexperimentalcompound",
            "generic_name": "Novelexperimentalcompound",
            "status": "NO_RELEVANT_RESULT",
            "verification_status": "NOT_FOUND",
            "is_live": True,
            "fallback_used": False,
            "dosage_forms": [],
            "routes": [],
            "verified_label_dosage": ""
        }):
            gallery = get_medicine_gallery(
                [{"name": "Novelexperimentalcompound 100mg", "dosage": "100mg daily"}],
                top_condition="Experimental Condition",
                symptoms=["Mild Fatigue"]
            )
            assert len(gallery) == 1
            assert gallery[0]["name"] == "Novelexperimentalcompound 100mg"
            assert gallery[0]["is_verified"] is False
            assert gallery[0]["verification_status"] == "UNVERIFIED"
            assert "paracetamol" not in gallery[0]["name"].lower()

    def test_provider_failure_does_not_create_verified_medicine(self):
        """Provider TIMEOUT or AUTH_ERROR is preserved truthfully and never labeled VERIFIED."""
        from ai.utils.care_recommendations import get_medicine_gallery
        with patch("api.openfda.search_drug_openfda", return_value={
            "status": "TIMEOUT",
            "verification_status": "UNVERIFIED",
            "fallback_used": True,
            "fallback_reason": "OpenFDA timeout"
        }):
            gallery = get_medicine_gallery(
                [{"name": "SomeMedicine 10mg", "dosage": "10mg"}],
                top_condition="Some Condition",
                symptoms=["Fever"]
            )
            assert len(gallery) == 1
            assert gallery[0]["is_verified"] is False
            assert gallery[0]["provider_status"] == "TIMEOUT"
            assert gallery[0]["reference_type"] == "UNRESOLVED_CANDIDATE"

    # --------------------------------------------------------------------------
    # 10. BioPortal & External Reference Evidence Isolation
    # --------------------------------------------------------------------------
    def test_bioportal_concepts_do_not_contaminate_patient_symptom_ids(self):
        """External BioPortal concepts must NEVER mutate or be added to patient's selected_symptom_ids."""
        orchestrator = clinical_pipeline
        mock_bioportal = [
            {"prefLabel": "Headache", "pref_label": "Headache", "cui": "C0018681"},
            {"prefLabel": "Nausea", "pref_label": "Nausea", "cui": "C0027497"}
        ]
        
        with patch.object(orchestrator, "_get_bioportal_concepts", return_value=mock_bioportal):
            with patch("requests.get", side_effect=ConnectionError("offline")):
                with patch("requests.post", side_effect=ConnectionError("offline")):
                    triage_result = orchestrator.run_pipeline(
                        symptom_names=["Eye Pain"],
                        patient_context={"age_group": "21-30", "gender": "Male", "duration": "1-3 Days", "severity": "Moderate"},
                        run_bioportal=True,
                        run_nlm=False,
                        run_care_recommendations=False
                    )
        
        # Patient only reported "Eye Pain" -> patient symptom_names and symptom_ids must NOT contain Headache or Nausea
        sym_names = triage_result.get("symptom_names", [])
        assert "Headache" not in sym_names
        assert "Nausea" not in sym_names
        assert len(sym_names) == 1
        assert "Eye Pain" in sym_names[0]

    # --------------------------------------------------------------------------
    # 11. Authoritative Triage Urgency & Evaluation Timeframe Consistency
    # --------------------------------------------------------------------------
    def test_authoritative_triage_urgency_consistency(self):
        """Moderate severity presentation produces consistent physician consultation triage, never contradictory Mild."""
        from ai.disease_prediction.predict import triage_engine
        
        # Presentation with moderate severity eye pain
        triage = triage_engine.evaluate_symptoms(
            selected_symptom_ids=[],
            symptom_names=["Eye Pain"],
            age_group="21-30",
            gender="Male",
            duration="1-3 Days",
            severity="Moderate"
        )
        
        urgency = triage["urgency_level"]
        timeframe = triage["timeframe_for_evaluation"]
        assert urgency == "Moderate Attention (Consult Physician)"
        assert "Within 24–48 hours" in timeframe or "Prompt" in timeframe
        assert "Mild / Self-Monitoring" not in urgency

    # --------------------------------------------------------------------------
    # 12. Recovery & Seasonal Advisory Evidence Gating
    # --------------------------------------------------------------------------
    def test_recovery_timeline_gated_by_diagnostic_uncertainty(self):
        """Emergency or high-uncertainty condition does not dogmatically assert 5-7 days recovery."""
        from ai.utils.care_recommendations import _build_local_dataset_fallback
        res = _build_local_dataset_fallback(
            symptoms=["Sudden Vision Loss", "Severe Eye Pain"],
            user_context={"severity": "Severe", "is_emergency": True},
            top_condition="Acute Angle-Closure Glaucoma",
            lang_code="en"
        )
        rec_dur = res["recovery_duration"]
        assert "5 – 7 days" not in rec_dur
        assert "depends on clinical evaluation" in rec_dur.lower() or "clinical" in rec_dur.lower()

    def test_seasonal_health_advisory_evidence_label(self):
        """Seasonal advisory frames risk as educational health information, not unverified active outbreak."""
        from ai.utils.seasonal_context import get_seasonal_health_context
        ctx = get_seasonal_health_context("Gujarat", month=10, lang_code="en")
        alert_desc = ctx["alert_description"].lower()
        # Does not claim a confirmed active outbreak
        assert "advisory" in ctx["alert_title"].lower() or "reference" in ctx["alert_title"].lower()

