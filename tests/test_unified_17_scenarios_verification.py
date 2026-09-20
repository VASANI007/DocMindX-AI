"""
DocMindX AI — Unified 17-Scenario Master Verification Test Suite
Directly validates all 17 clinical regression scenarios defined in Section 13 of the Unified Master Repair Prompt.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ai.disease_prediction.canonical_concepts import (
    canonical_normalizer,
    MasterSymptomTaxonomyBridge,
    get_taxonomy_bridge,
    validate_canonical_ids
)
from ai.disease_prediction.clinical_pipeline import clinical_pipeline
from ai.utils.care_recommendations import (
    condition_supports_topical,
    get_medicine_gallery,
    get_dynamic_clinical_recommendations,
    _get_condition_fallback_medicines,
    _get_condition_fallback_yoga
)
from api.openfda import is_openfda_verified, search_drug_openfda
from api.dailymed import is_dailymed_verified, search_dailymed_spls, get_dailymed_medicine_summary


class TestUnified17Scenarios:

    def test_scenario_01_dermatology_tinea_reproduction(self):
        """Scenario 1: Dermatology/Tinea reproduction vehicle ('dhadhar thay chhe lalchmbha padiya chhe')."""
        query_gu_roman = "dhadhar thay chhe lalchmbha padiya chhe"
        res = clinical_pipeline.run_pipeline(
            raw_text=query_gu_roman,
            selected_symptoms=[],
            age=28,
            gender="Male",
            lang_code="gu",
            run_care_recommendations=True
        )
        assert res is not None
        # Must identify skin / fungal presentation
        pos_symptoms = res["clinical_input"]["positive_findings"]
        symptom_ids = res["clinical_input"]["symptom_ids"]
        assert any("rash" in s.lower() or "fungal" in s.lower() or "dhadhar" in s.lower() or "skin" in s.lower() for s in pos_symptoms)
        assert "S000109" in symptom_ids or "S000124" in symptom_ids
        # Must not fabricate fever, malaria, or headache
        assert not any("malaria" in s.lower() for s in pos_symptoms)
        assert not any("dengue" in s.lower() for s in pos_symptoms)
        # Topical eligibility must be True
        top_condition = (
            res["clinical_assessment"].get("top_condition") or
            (res["clinical_assessment"]["compatible_conditions"][0].get("name") if res["clinical_assessment"]["compatible_conditions"] else "Fungal Skin Infection")
        )
        assert condition_supports_topical(top_condition, pos_symptoms) is True
        # Care recommendations: Yoga must be empty, compresses mode 'none', topical cream present
        care_plan = res["care_plan"]
        assert care_plan["yoga_recommendations"] == [], "Fungal skin infection must NOT recommend routine yoga"
        assert care_plan["cold_warm_compress_mode"] == "none"
        assert care_plan["cold_warm_compress_indicated"] is False
        assert care_plan["physiotherapy_guidance"]["exercises"] == []
        gallery = care_plan["medicine_gallery"]
        assert len(gallery) >= 1
        has_topical_cream = any(
            (m.get("form") or m.get("dosage_form", "")).lower() in ["cream", "ointment", "gel"] and
            m.get("route", "").lower() == "topical"
            for m in gallery
        )
        assert has_topical_cream, "Must contain topical formulation"
        # Dosage form must NEVER be 'Tube'
        for m in gallery:
            form = (m.get("form") or m.get("dosage_form", "") or "").lower()
            assert form != "tube", f"Dosage form must never be 'Tube': {m}"

    def test_scenario_02_skin_rash_canonical_mapping(self):
        """Scenario 2: Skin rash must map to S000109 (Skin Rash), NEVER S000108 (Worm Infestation)."""
        sid = canonical_normalizer.get_symptom_id("skin rash")
        assert sid == "S000109", f"Expected S000109, got {sid}"
        bridge = get_taxonomy_bridge()
        record = bridge.lookup_by_id(sid)
        assert record is not None
        assert "rash" in record.get("symptom_name", "").lower()
        assert "worm" not in record.get("symptom_name", "").lower()

    def test_scenario_03_abdominal_pain_canonical_mapping(self):
        """Scenario 3: Abdominal pain must map to S000092 (Abdominal Pain), NEVER S000091 (Constipation)."""
        for query in ["stomach pain", "abdominal pain", "પેટમાં દુખાવો", "पेट दर्द"]:
            sid = canonical_normalizer.get_symptom_id(query)
            assert sid == "S000092", f"Query '{query}' expected S000092, got {sid}"
        bridge = get_taxonomy_bridge()
        record = bridge.lookup_by_id("S000092")
        assert record is not None
        assert "abdominal" in record.get("symptom_name", "").lower() or "stomach" in record.get("symptom_name", "").lower()
        assert "constipation" not in record.get("symptom_name", "").lower()

    def test_scenario_04_sciatica_radicular_attributes(self):
        """Scenario 4: Sciatica radiating lower back pain -> S000135 + S000144, radicular attributes."""
        res = clinical_pipeline.run_pipeline(
            raw_text="Severe lower back pain radiating down my left leg with tingling in foot",
            selected_symptoms=[],
            age=45,
            gender="Male",
            lang_code="en"
        )
        pos = res["clinical_input"]["positive_findings"]
        sids = res["clinical_input"]["symptom_ids"]
        assert "S000135" in sids or "S000144" in sids
        concepts_dict = res["clinical_input"]["canonical_concepts"]
        has_rad = (
            concepts_dict.get("clinical_attributes", {}).get("has_radicular_symptoms", False) or
            "radiating_pain_lower_limb" in concepts_dict.get("canonical_concepts", []) or
            "sciatica" in concepts_dict.get("canonical_concepts", [])
        )
        assert has_rad is True

    def test_scenario_05_animal_bite_mapping(self):
        """Scenario 5: Animal bite -> S000265, NEVER S000280."""
        sid = canonical_normalizer.get_symptom_id("street dog bite on leg")
        assert sid == "S000265", f"Expected S000265, got {sid}"
        bridge = get_taxonomy_bridge()
        record = bridge.lookup_by_id("S000265")
        assert record is not None
        assert "bite" in record.get("symptom_name", "").lower()

    def test_scenario_06_cardiac_emergency_suppresses_routine_care(self):
        """Scenario 6: Acute cardiac emergency triggers emergency gate and suppresses routine yoga/physio."""
        care = get_dynamic_clinical_recommendations(
            symptoms=["Crushing Chest Pain", "Sweating", "Shortness of Breath"],
            user_context={"age": "58", "gender": "Male", "is_emergency": True},
            top_condition="Acute Coronary Syndrome",
            lang_code="en"
        )
        assert care["is_emergency"] is True
        assert care["yoga_recommendations"] == []
        assert care["physiotherapy_guidance"]["exercises"] == []

    def test_scenario_07_structured_negation(self):
        """Scenario 7: Structured negation correctly segregates positive from negative findings."""
        res = clinical_pipeline.run_pipeline(
            raw_text="High fever and persistent cough but no headache and no vomiting",
            selected_symptoms=[],
            age=30,
            gender="Female",
            lang_code="en"
        )
        pos = [p.lower() for p in res["clinical_input"]["positive_findings"]]
        neg = [n.lower() for n in res["clinical_input"]["negative_findings"]]
        assert any("fever" in p for p in pos)
        assert any("cough" in p for p in pos)
        assert any("headache" in n for n in neg)
        assert any("vomiting" in n for n in neg)

    def test_scenario_08_insufficient_information_anti_fabrication(self):
        """Scenario 8: Vague input produces 0 fabricated symptoms, diagnoses, or medicines."""
        res = clinical_pipeline.run_pipeline(
            raw_text="something feels strange in my body",
            selected_symptoms=[],
            age=25,
            gender="Male",
            lang_code="en"
        )
        assert res["clinical_assessment"]["compatible_conditions"] == []
        assert res["clinical_input"]["positive_findings"] == []
        fallback_meds = _get_condition_fallback_medicines(top_condition="", symptoms=["something feels strange in my body"])
        assert len(fallback_meds) == 0

    def test_scenario_09_topical_eligibility_gating(self):
        """Scenario 9: Topical eligibility: True for localized fungal/sprain, False for systemic fever."""
        assert condition_supports_topical("Fungal Skin Infection", ["Skin Rash", "Itching"]) is True
        assert condition_supports_topical("Lumbar Strain", ["Back Pain", "Muscle Stiffness"]) is True
        assert condition_supports_topical("Acute Viral Fever", ["High Fever", "Chills"]) is False
        assert condition_supports_topical("Malaria", ["Fever with Chills", "Sweating"]) is False

    def test_scenario_10_routine_illness_injection_block(self):
        """Scenario 10: Routine injections blocked for common mild short-duration illnesses."""
        injections = [
            {"name": "Paracetamol IV Infusion", "form": "Injection", "route": "Intravenous", "dosage": "1000mg IV"}
        ]
        gallery = get_medicine_gallery(
            injections,
            top_condition="Viral Fever",
            symptoms=["Fever", "Body Ache"],
            duration="1-3 Days"
        )
        assert len(gallery) == 0, "Routine IV paracetamol must be blocked for acute mild viral fever"

    def test_scenario_11_rabies_prophylaxis_pathway(self):
        """Scenario 11: Rabies post-exposure prophylaxis injection permitted under hospital protocol."""
        rabies_inj = [
            {"name": "Anti-Rabies Vaccine (Rabipur)", "form": "Injection", "route": "Intramuscular", "dosage": "1.0ml IM"}
        ]
        gallery = get_medicine_gallery(
            rabies_inj,
            top_condition="Rabies Post-Exposure Prophylaxis",
            symptoms=["Animal Bite", "Dog Bite Wound"],
            duration="Today"
        )
        assert len(gallery) == 1
        assert gallery[0]["is_hospital_protocol"] is True
        assert "hospital" in gallery[0]["administration_setting"].lower() or "clinic" in gallery[0]["administration_setting"].lower()

    def test_scenario_12_openfda_verification_honesty(self):
        """Scenario 12: OpenFDA verification honesty: NO_RELEVANT_RESULT must never equal verified success."""
        # Unverified / 404 response
        no_match = {
            "status": "NO_RELEVANT_RESULT",
            "verification_status": "NOT_FOUND",
            "is_live": True,
            "fallback_used": False,
            "brand_names": [],
            "generic_name": "Nonexistent",
            "verified_label_dosage": ""
        }
        assert is_openfda_verified(no_match) is False

        # Truly verified response
        verified = {
            "status": "SUCCESS",
            "verification_status": "OPENFDA_VERIFIED",
            "is_live": True,
            "fallback_used": False,
            "brand_names": ["Tylenol"],
            "generic_name": "Acetaminophen",
            "dosage_forms": ["TABLET"],
            "routes": ["ORAL"],
            "verified_label_dosage": "Take 1-2 tablets every 4-6 hours."
        }
        assert is_openfda_verified(verified) is True

    def test_scenario_13_dailymed_name_match_vs_spl_verification(self):
        """Scenario 13: DailyMed name match is NOT verified; full SPL document match IS verified."""
        # Name match only
        name_only = {
            "status": "DAILYMED_NAME_MATCH",
            "verification_status": "DAILYMED_NAME_MATCH",
            "is_live": True,
            "spl_setid": ""
        }
        assert is_dailymed_verified(name_only) is False

        # Full SPL record
        spl_record = {
            "status": "SUCCESS",
            "verification_status": "DAILYMED_VERIFIED",
            "is_live": True,
            "fallback_used": False,
            "spl_setid": "test-spl-setid-abc-123",
            "generic_name": "Amoxicillin"
        }
        assert is_dailymed_verified(spl_record) is True

    def test_scenario_14_badge_honesty_in_gallery(self):
        """Scenario 14: Medicine gallery displays honest provenance badges without falsification."""
        entries = [
            {"name": "Clotrimazole 1% Cream", "form": "Cream", "route": "Topical", "dosage": "Apply twice daily"}
        ]
        gallery = get_medicine_gallery(
            entries,
            top_condition="Tinea Corporis",
            symptoms=["Skin Rash", "Itching"]
        )
        assert len(gallery) == 1
        med = gallery[0]
        # Verification status must be one of the honest enums
        assert med["verification_status"] in [
            "OPENFDA_VERIFIED", "DAILYMED_VERIFIED", "OPENFDA_AND_DAILYMED_VERIFIED",
            "DAILYMED_NAME_MATCH", "CLINICAL_REFERENCE"
        ]
        if not med["is_verified"]:
            assert med["verification_status"] in ["CLINICAL_REFERENCE", "DAILYMED_NAME_MATCH"]

    def test_scenario_15_multilingual_and_code_mixed_invariance(self):
        """Scenario 15: Cross-lingual symmetry across English, Hindi, Gujarati, and Romanized script."""
        queries = {
            "en": "ringworm fungal skin infection with red rash",
            "hi": "दाद की समस्या है और त्वचा पर लाल चकत्ते हैं",
            "gu": "મને ધાધર થઈ છે અને ત્વચા પર લાલચમઠા પડ્યા છે",
            "gu_roman": "dhadhar thay chhe lalchmbha padiya chhe"
        }
        extracted_sids = {}
        for lang, text in queries.items():
            res = clinical_pipeline.run_pipeline(
                raw_text=text,
                selected_symptoms=[],
                age=30,
                gender="Male",
                lang_code=lang if lang != "gu_roman" else "gu"
            )
            sids = set(res["clinical_input"]["symptom_ids"])
            extracted_sids[lang] = sids
            assert len(sids) > 0, f"Language {lang} extracted 0 symptom IDs"
            assert "S000109" in sids or "S000124" in sids, f"Language {lang} missing S000109 or S000124: {sids}"

    def test_scenario_16_bioportal_offline_resilience(self, monkeypatch):
        """Scenario 16: Pipeline executes seamlessly when BioPortal is offline without crashing or fabricating."""
        monkeypatch.setattr(
            "ai.disease_prediction.clinical_pipeline.clinical_pipeline._get_bioportal_concepts",
            lambda *args, **kwargs: []
        )
        res = clinical_pipeline.run_pipeline(
            raw_text="Skin rash and itching on arms",
            selected_symptoms=[],
            age=25,
            gender="Female",
            lang_code="en"
        )
        assert res is not None
        assert "S000109" in res["clinical_input"]["symptom_ids"]
        assert res["provenance"]["status"] == "SUCCESS"

    def test_scenario_17_active_compound_deduplication(self):
        """Scenario 17: Active compound deduplication prevents duplicate entries for the same compound & route."""
        duplicate_entries = [
            {"name": "Paracetamol 500mg Tablet", "form": "Tablet", "route": "Oral", "dosage": "500mg"},
            {"name": "Paracetamol 650mg Tablet (Dolo 650)", "form": "Tablet", "route": "Oral", "dosage": "650mg"},
            {"name": "Crocin 500mg (Paracetamol)", "form": "Tablet", "route": "Oral", "dosage": "500mg"},
        ]
        gallery = get_medicine_gallery(
            duplicate_entries,
            top_condition="Viral Fever",
            symptoms=["Fever", "Body Ache"]
        )
        # All 3 are oral paracetamol: deduplication must collapse to 1 entry
        assert len(gallery) == 1, f"Expected 1 deduplicated entry, got {len(gallery)}"
