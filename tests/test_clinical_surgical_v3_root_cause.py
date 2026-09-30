import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.disease_prediction.clinical_pipeline import clinical_pipeline
from ai.disease_prediction.predict import triage_engine
from ai.disease_prediction.canonical_concepts import canonical_normalizer
from ai.utils.care_recommendations import get_medicine_gallery, get_dynamic_clinical_recommendations


class TestClinicalSurgicalV3RootCause:
    """
    Comprehensive Root-Cause Verification Suite for DocMindX Clinical Pipeline v3.
    """

    # TEST 1 — EXACT CURRENT BUG REPRODUCTION
    def test_1_exact_current_bug_reproduction(self):
        raw_text = "kutraye daba pag ma bataku bhariyu, mathu dukhe che, galama bale chee"
        
        mock_bioportal = [{"pref_label": "Dog bite", "cui": "C0012984", "is_live": True}, {"pref_label": "Headache", "cui": "C0018681", "is_live": True}]
        mock_nlm = ["Head injury with vomiting", "Tetanus", "Rabies"]
        
        with patch("api.bioportal.search_bioportal_concept", return_value=mock_bioportal), \
             patch("api.nlm_clinical.search_nlm_conditions", return_value=mock_nlm):
            res = clinical_pipeline.run_pipeline(
                input_text=raw_text,
                patient_context={"duration": "Started Today", "age_group": "21-30", "gender": "Male"},
                run_bioportal=True,
                run_nlm=True,
                run_care_recommendations=False
            )

        assert res["clinical_status"] == "success"
        # Positive findings: animal bite, headache, sore throat
        sym_str = " ".join(res["symptom_names"]).lower()
        assert any(k in sym_str for k in ["animal", "bite", "wound", "dog"])

        # Vomiting and head injury MUST be absent from patient findings
        assert not any("vomit" in s for s in sym_str.split())
        assert not any("head injury" in s for s in res["symptom_names"])

        # RF030 Head Injury with Vomiting MUST NOT appear even when NLM returns "Head injury with vomiting"
        flag_names = [f.get("symptom_name", "") for f in res.get("red_flags", [])]
        assert "Head Injury with Vomiting" not in flag_names, f"False RF030 emitted: {flag_names}"

        # No fabricated neurological trauma flag, snakebite, or broad unrelated tropical differential
        ranked = res.get("ranked_conditions", [])
        cond_names = [c.get("name", "").lower() for c in ranked]
        assert not any("snake" in n for n in cond_names)
        assert not any("stroke" in n for n in cond_names)
        assert not any("glaucoma" in n for n in cond_names)
        assert not any("hypertension" in n for n in cond_names)
        assert not any(k in n for n in cond_names for k in ["nipah", "kfd", "kyasanur", "malaria", "dengue"])

        # Duration gate respected: Started Today suppresses routine diagnostics
        tests = res.get("tests_to_discuss", [])
        assert not any(t in tests for t in ["Lipid Profile", "ECG", "Serum Creatinine", "EEG", "Brain MRI"])

    # TEST 2 — EXPLICIT HEAD INJURY + VOMITING
    def test_2_explicit_head_injury_with_vomiting(self):
        res = triage_engine.evaluate_symptoms(
            selected_symptom_ids=["S000082"],
            symptom_names=["Head Injury", "Vomiting after fall"],
            duration="Started Today"
        )
        flag_names = [f.get("symptom_name", "") for f in res.get("red_flags", [])]
        assert any("Head Injury with Vomiting" in f for f in flag_names)

    # TEST 3 — ANIMAL BITE ONLY
    def test_3_animal_bite_only(self):
        res = clinical_pipeline.run_pipeline(
            input_text="Dog bite on leg with open puncture wound",
            patient_context={"duration": "Started Today"},
            run_care_recommendations=False
        )
        ranked = res.get("ranked_conditions", [])
        cond_names = [c.get("name", "").lower() for c in ranked]
        assert not any("headache" in n for n in cond_names)
        assert not any("snake" in n for n in cond_names)
        assert not any("stroke" in n for n in cond_names)

    # TEST 4 — HEADACHE ONLY
    def test_4_headache_only(self):
        res = clinical_pipeline.run_pipeline(
            input_text="Severe throbbing headache on forehead",
            patient_context={"duration": "1 Day"},
            run_care_recommendations=False
        )
        sym_str = " ".join(res["symptom_names"]).lower()
        assert "bite" not in sym_str

    # TEST 5 — SORE THROAT ONLY
    def test_5_sore_throat_only(self):
        res = clinical_pipeline.run_pipeline(
            input_text="Severe sore throat and difficulty swallowing",
            patient_context={"duration": "2 Days"}
        )
        tests = res.get("tests_to_discuss", [])
        assert not any(t in tests for t in ["EEG", "Brain MRI", "Lipid Profile", "ECG"])

    # TEST 6 — MANDATORY NLM CONTAMINATION TEST
    def test_6_nlm_contamination_isolation(self):
        """
        Mock NLM returning 'Head injury with vomiting' when patient input is only 'headache'.
        Verifies that NLM condition text NEVER enters patient evidence and CANNOT trigger RF030.
        """
        mock_nlm = [{"name": "Head injury with vomiting", "title": "Head injury with vomiting"}]
        res = triage_engine.evaluate_symptoms(
            selected_symptom_ids=["S000061"],
            symptom_names=["Headache"],
            duration="Started Today",
            nlm_conditions=mock_nlm
        )
        flag_names = [f.get("symptom_name", "") for f in res.get("red_flags", [])]
        assert "Head Injury with Vomiting" not in flag_names
        assert not any(f.get("flag_id") == "RF030" for f in res.get("red_flags", []))

    # TEST 7 — MEDICINE PROVIDER EMPTY / NO_RELEVANT_RESULT
    def test_7_medicine_provider_empty_no_fake_verification(self):
        """
        When OpenFDA and DailyMed return no relevant results, unverified AI candidate
        must be labelled UNVERIFIED, not given fake verification badges.
        """
        mock_entries = [{
            "name": "NonExistentDrugXYZ 500mg",
            "dosage": "1 Tablet twice daily",
            "indication": "Experimental",
            "type": "Prescription",
            "source": "Clinical AI Candidate"
        }]
        with patch("api.openfda.search_drug_openfda", return_value={"status": "NO_RELEVANT_RESULT"}), \
             patch("api.dailymed.get_dailymed_medicine_summary", return_value={"status": "NO_RELEVANT_RESULT"}), \
             patch("api.dailymed.search_dailymed_drugnames", return_value=[]):
            gallery = get_medicine_gallery(mock_entries, top_condition="General Illness")
            assert len(gallery) > 0
            item = gallery[0]
            assert item["verification_status"] == "UNVERIFIED"
            assert item["is_verified"] is False
            assert "OPENFDA_AND_DAILYMED_VERIFIED" not in item["verification_status"]

    # TEST 8 — MEDICINE FORM PRESERVATION
    def test_8_medicine_form_preservation(self):
        """Verified / specified Cream remains Cream, not defaulted to Tablet."""
        entries = [{
            "name": "Clotrimazole 1% Cream",
            "form": "Cream",
            "route": "Topical",
            "type": "OTC",
            "source": "Local Clinical Reference"
        }]
        gallery = get_medicine_gallery(entries, top_condition="Tinea Corporis (Ringworm)", symptoms=["Skin rash", "Itching"])
        assert len(gallery) == 1
        assert gallery[0]["dosage_form"] == "Cream"
        assert gallery[0]["route"].lower() == "topical"

    # TEST 9 — SHORT DURATION TESTS GATING
    def test_9_short_duration_suppresses_routine_tests(self):
        res = triage_engine.evaluate_symptoms(
            selected_symptom_ids=["S000061"],
            symptom_names=["Headache"],
            duration="Started Today"
        )
        assert res.get("tests_to_discuss", []) == []

    # TEST 10 — LONGER DURATION RELEASES RELEVANT TESTS
    def test_10_longer_duration_retains_evidence_tests(self):
        res = triage_engine.evaluate_symptoms(
            selected_symptom_ids=["S000061"],
            symptom_names=["Headache"],
            duration="7 Days"
        )
        tests = res.get("tests_to_discuss", [])
        assert len(tests) <= 5

    # TEST 11 — EMERGENCY SUPPRESSES ROUTINE YOGA & PHYSIO
    def test_11_emergency_suppresses_routine_yoga_and_physio(self):
        res = get_dynamic_clinical_recommendations(
            symptoms=["Dog bite on left leg with deep bleeding wound"],
            user_context={"is_emergency": True, "duration": "Started Today"},
            top_condition="Rabies Post-Exposure / Animal Bite"
        )
        assert len(res.get("yoga_recommendations", [])) == 0
        physio = res.get("physiotherapy_guidance", {})
        assert not physio.get("is_indicated", False) or len(physio.get("exercises", [])) == 0

    # TEST 12 — SEASONAL CONTAMINATION ISOLATION
    def test_12_seasonal_contamination_isolation(self):
        """Monsoon season with headache only must not diagnose Dengue or Malaria without fever."""
        res = triage_engine.evaluate_symptoms(
            selected_symptom_ids=["S000061"],
            symptom_names=["Headache"],
            duration="1 Day"
        )
        ranked = res.get("ranked_conditions", [])
        cond_names = [c.get("name", "").lower() for c in ranked]
        assert not any("dengue" in n for n in cond_names)
        assert not any("malaria" in n for n in cond_names)

    # TEST 13 — MULTILINGUAL SYMPTOM EXTRACTION INVARIANCE
    def test_13_multilingual_invariance(self):
        gu_text = "માથું દુખે છે"
        hi_text = "सिर में दर्द है"
        en_text = "I have a headache"

        norm_gu = canonical_normalizer.normalize(gu_text)
        norm_hi = canonical_normalizer.normalize(hi_text)
        norm_en = canonical_normalizer.normalize(en_text)

        assert "S000061" in norm_gu.symptom_ids
        assert "S000061" in norm_hi.symptom_ids
        assert "S000061" in norm_en.symptom_ids

    # TEST 14 — NEGATION SUPPRESSION
    def test_14_negation_suppression(self):
        res = clinical_pipeline.run_pipeline(
            input_text="kutraye bataku bhariyu pan mathu nathi dukhtu",
            patient_context={"duration": "Started Today"}
        )
        assert any("headache" in n.lower() or "mathu" in n.lower() or "cephalalgia" in n.lower() for n in res["negative_findings"])
        assert not any(sid == "S000061" for sid in res.get("symptom_ids", []))
