"""
DocMindX AI — Medication Formulation & Provenance Verification Test Suite
Verifies:
1. Strict separation of candidate dosage vs verified label dosage.
2. Injection formulation gating (hospital/clinic administration only, never self-administered).
3. Topical/Gel formulation gating (localized superficial only; blocked for open bites or pure systemic fever).
4. Emergency gate suppression of routine yoga and exercises.
"""
import os
import sys
import pytest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_ROOT)

from ai.utils.care_recommendations import (
    get_medicine_gallery,
    condition_supports_topical,
    get_dynamic_clinical_recommendations,
    _get_condition_fallback_medicines,
    _get_condition_fallback_yoga
)


class TestMedicationProvenance:

    def test_medication_provenance_schema(self, monkeypatch):
        """Verifies that all entries in medicine gallery carry explicit provenance fields."""
        monkeypatch.setattr(
            "api.openfda.search_drug_openfda",
            lambda c: {
                "is_live": True,
                "status": "SUCCESS",
                "brand_name": "Tylenol",
                "generic_name": "Acetaminophen",
                "verified_label_dosage": "Take 1-2 tablets every 4-6 hours. Do not exceed 4000mg daily.",
                "verified_strength": "500 mg",
                "verified_route": "Oral",
                "verified_form": "Tablet"
            }
        )

        entries = [
            {
                "name": "Paracetamol 500mg Tablet",
                "dosage": "1 Tablet thrice daily",
                "form": "Tablet",
                "route": "Oral",
                "type": "OTC"
            }
        ]

        gallery = get_medicine_gallery(
            entries,
            top_condition="Viral Fever",
            symptoms=["Fever", "Body Ache"]
        )

        assert len(gallery) == 1
        med = gallery[0]

        # Verify provenance fields
        assert "candidate_medication" in med
        assert med["candidate_dosage"] == "1 Tablet thrice daily"
        assert med["verified_label_dosage"] == "Take 1-2 tablets every 4-6 hours. Do not exceed 4000mg daily."
        assert med["verified_strength"] == "500 mg"
        assert med["verified_route"] == "Oral"
        assert med["verified_form"] == "Tablet"
        assert med["verification_status"] == "OPENFDA_VERIFIED"
        assert med["provider"] == "OpenFDA"
        assert med["is_live"] is True
        assert med["is_hospital_protocol"] is False

    def test_injection_formulation_gating(self):
        """Verifies that injections are hospital/clinic protocol and never self-administered."""
        # 1. Routine injection for mild cold should be blocked
        routine_inj = [
            {"name": "Paracetamol IV Infusion", "form": "Injection", "route": "Intravenous", "dosage": "1000mg IV"}
        ]
        gallery_mild = get_medicine_gallery(
            routine_inj,
            top_condition="Common Cold",
            symptoms=["Runny Nose", "Sneezing"],
            duration="1-3 Days"
        )
        assert len(gallery_mild) == 0, "Routine injection must be blocked for acute mild common cold"

        # 2. Emergency rabies vaccine must be permitted but tagged as hospital protocol
        rabies_inj = [
            {"name": "Anti-Rabies Vaccine (Rabipur)", "form": "Injection", "route": "Intramuscular", "dosage": "1.0ml IM"}
        ]
        gallery_rabies = get_medicine_gallery(
            rabies_inj,
            top_condition="Rabies Post-Exposure Prophylaxis",
            symptoms=["Dog Bite with Wound", "Animal Bite"],
            duration="Today"
        )
        assert len(gallery_rabies) == 1
        inj_med = gallery_rabies[0]
        assert inj_med["is_hospital_protocol"] is True
        assert "hospital" in inj_med["administration_setting"].lower() or "clinic" in inj_med["administration_setting"].lower()

    def test_topical_gel_gating(self):
        """Verifies that gel is only supported for localized superficial presentations and blocked for bite wounds."""
        # Localized back strain -> Topical gel supported
        assert condition_supports_topical("Lumbar Strain", ["Back Pain", "Muscle Stiffness"]) is True

        # Pure systemic febrile illness -> Topical gel blocked
        assert condition_supports_topical("Acute Viral Fever", ["High Fever", "Chills"]) is False

        # Open dog bite wound -> Analgesic topical gel blocked
        assert condition_supports_topical("Animal Bite Exposure", ["Dog Bite with Wound", "Bleeding Wound"]) is False

    def test_emergency_gate_suppresses_routine_exercises(self):
        """Verifies that emergency gate suppresses routine yoga and physiotherapy."""
        care_res = get_dynamic_clinical_recommendations(
            symptoms=["Sudden Crushing Chest Pain", "Sweating", "Shortness of Breath"],
            user_context={
                "age": "55",
                "gender": "Male",
                "severity": "Severe",
                "duration": "Started 1 Hour Ago",
                "is_emergency": True
            },
            top_condition="Acute Coronary Syndrome",
            lang_code="en"
        )

        assert care_res["is_emergency"] is True
        assert care_res["yoga_recommendations"] == [], "Emergency gate MUST set yoga_recommendations to empty list"
        assert care_res["physiotherapy_guidance"]["exercises"] == [], "Emergency gate MUST set physiotherapy exercises to empty list"
        assert "EMERGENCY" in care_res["summary"].upper()

    def test_unknown_input_does_not_fabricate_medicines(self):
        """Verifies that unknown or unresolvable symptom input produces 0 fallback medicines."""
        meds = _get_condition_fallback_medicines(
            top_condition="",
            symptoms=["something feels strange in my body"],
            lang_code="en"
        )
        assert len(meds) == 0, f"Expected 0 fabricated medicines for unknown input, got {len(meds)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
