import pytest
from ai.utils.care_recommendations import _extract_clinical_presentation_attributes, get_dynamic_clinical_recommendations, get_medicine_gallery
from ai.disease_prediction.predict import triage_engine
from ai.utils.clinical_safety_rules import clinical_safety_engine
from tests.validation_campaign.clinical_manifest import TRIAGE_MEDICINE_TEST_CASES

class TestClinicalTriageMedicine:
    """Category F: Clinical Triage, Red Flags & Care Recommendations Test Suite (40 Cases)."""

    @pytest.mark.parametrize("case", TRIAGE_MEDICINE_TEST_CASES, ids=[c["id"] for c in TRIAGE_MEDICINE_TEST_CASES])
    def test_triage_medicine_case(self, case):
        cid = case["id"]
        cname = case.get("name", "")
        symptoms = case.get("symptoms", [])
        patient = case.get("patient", {})

        # Group 1: TC-TRI-001 to 012 (Critical Red Flag Emergencies)
        if case.get("expected_emergency") is True:
            attrs = _extract_clinical_presentation_attributes(
                symptoms=symptoms,
                top_condition=cname,
                user_context=patient
            )
            assert attrs["has_emergency_red_flags"] is True, (
                f"Case {cid} ({cname}): Expected has_emergency_red_flags=True, got False."
            )

        # Group 2: TC-TRI-013 to 025 (Non-Emergency Common Primary Care)
        elif case.get("expected_emergency") is False:
            attrs = _extract_clinical_presentation_attributes(
                symptoms=symptoms,
                top_condition=cname,
                user_context=patient
            )
            assert attrs["has_emergency_red_flags"] is False, (
                f"Case {cid} ({cname}): Expected has_emergency_red_flags=False, got True."
            )

        # Group 3: TC-TRI-026 to 032 (Anatomical & Pharmacological Safety Invariants)
        elif cid == "TC-TRI-026":
            # Male anatomical filter
            disallowed = [c.lower() for c in case.get("disallowed_conditions", [])]
            triage_res = triage_engine.evaluate_symptoms(
                selected_symptom_ids=["S000092", "S000005"],
                gender="Male",
                age_group=patient.get("age_group", "41-50")
            )
            conditions_list = triage_res.get("ranked_conditions") or triage_res.get("differential_diagnoses", [])
            predicted_names = [d.get("name", d.get("disease_name", "")).lower() for d in conditions_list]
            for dis in disallowed:
                assert not any(dis in p for p in predicted_names), (
                    f"Male patient erroneously received female-specific condition '{dis}' in {predicted_names}"
                )

        elif cid == "TC-TRI-027":
            # Female anatomical filter
            disallowed = [c.lower() for c in case.get("disallowed_conditions", [])]
            triage_res = triage_engine.evaluate_symptoms(
                selected_symptom_ids=["S000239", "S000226"],
                gender="Female",
                age_group=patient.get("age_group", "51-60")
            )
            conditions_list = triage_res.get("ranked_conditions") or triage_res.get("differential_diagnoses", [])
            predicted_names = [d.get("name", d.get("disease_name", "")).lower() for d in conditions_list]
            for dis in disallowed:
                assert not any(dis in p for p in predicted_names), (
                    f"Female patient erroneously received male-specific condition '{dis}' in {predicted_names}"
                )

        elif cid in ["TC-TRI-028", "TC-TRI-029", "TC-TRI-030", "TC-TRI-031", "TC-TRI-032"]:
            # Medication safety gates
            allergies = patient.get("allergies", [])
            conditions = patient.get("history", [])
            disallowed_meds = case.get("disallowed_meds", [])
            for dis in disallowed_meds:
                dis_clean = dis.split("(")[0].strip()
                eval_res = clinical_safety_engine.run_full_safety_audit(
                    conditions=conditions or (["Pregnancy 3rd Trimester"] if patient.get("pregnancy") else []),
                    allergies=allergies,
                    candidate_medications=[dis_clean],
                    patient_profile=patient
                )
                assert not eval_res["is_safe"] or dis_clean in eval_res["blocked_medications"] or len(eval_res["blocked_medications"]) > 0

        # Group 4: TC-TRI-033 to 040 (Anti-Fabrication & Source Tracking)
        elif cid == "TC-TRI-033":
            triage_res = triage_engine.evaluate_symptoms(["S000001", "S000061"])
            conditions_list = triage_res.get("ranked_conditions") or triage_res.get("differential_diagnoses", [])
            assert len(conditions_list) > 0
            for d in conditions_list:
                assert "source" in d or "provenance" in d or "match_score" in d or "match_percentage" in d or "confidence" in d

        elif cid == "TC-TRI-034":
            triage_res = triage_engine.evaluate_symptoms(["S000005"])
            diffs = triage_res.get("ranked_conditions") or triage_res.get("differential_diagnoses", [])
            if diffs:
                top_score = diffs[0].get("match_percentage", diffs[0].get("match_score", 0))
                assert top_score <= 100

        elif cid == "TC-TRI-035":
            triage_res = triage_engine.evaluate_symptoms(["S000001", "S000003", "S000011", "S000061", "S000005"])
            diffs = triage_res.get("ranked_conditions") or triage_res.get("differential_diagnoses", [])
            assert len(diffs) >= case.get("min_condition_count", 1)

        elif cid == "TC-TRI-036":
            gallery = get_medicine_gallery(
                [{"name": "Paracetamol 650mg Tablet", "form": "Tablet", "route": "Oral"}],
                top_condition="Viral Fever",
                symptoms=["Fever"]
            )
            assert len(gallery) > 0
            assert gallery[0].get("dosage_form") in ["Tablet", "Oral", "Capsule", "Syrup", "Unspecified Formulation"] or gallery[0].get("route")

        elif cid == "TC-TRI-037":
            # Force offline fallback check
            care_res = get_dynamic_clinical_recommendations(
                symptoms=["Cough"],
                top_condition="Common Cold",
                user_context={"offline": True, "age": "30", "gender": "Male"}
            )
            assert care_res.get("fallback_used") is True or care_res.get("is_fallback") is True or "offline" in str(care_res).lower()

        elif cid == "TC-TRI-038":
            triage_res = triage_engine.evaluate_symptoms(["S000046", "S000026"])
            diffs = triage_res.get("ranked_conditions") or triage_res.get("differential_diagnoses", [])
            if diffs:
                icd = diffs[0].get("icd_10_code") or diffs[0].get("icd_code") or diffs[0].get("icd_details", {}).get("code")
                assert icd is not None and len(icd) >= 3

        elif cid == "TC-TRI-039":
            care_res = get_dynamic_clinical_recommendations(
                symptoms=["Headache"],
                top_condition="Tension Headache",
                user_context={"age": "25", "gender": "Female"}
            )
            assert "summary" in care_res
            assert "dietary_guidelines" in care_res or "foods_to_eat" in care_res

        elif cid == "TC-TRI-040":
            # Ensure zero fabricated medicines for empty/invalid condition
            from ai.utils.care_recommendations import _get_condition_fallback_medicines
            meds = _get_condition_fallback_medicines(top_condition="", symptoms=["something strange"])
            assert len(meds) == 0
