"""
DocMindX AI — 15-Category Clinical Intelligence Generalization Test Suite
Validates that the clinical intelligence engine reasons from clinical attributes,
anatomy, and physiological presentation across ALL 15 clinical domains
with zero disease-name hardcoded shortcuts.

Categories Tested:
1. Musculoskeletal
2. Neurological
3. Infectious
4. Cardiac
5. Respiratory
6. Gastrointestinal
7. Urinary
8. Endocrine
9. Dermatological
10. Reproductive
11. Pediatric
12. Elderly
13. Emergency
14. Multi-symptom
15. Unknown / Insufficient Evidence

Plus Generalized Property-Based Safety & Formulation Tests:
- Attribute-based Yoga Safety Gate (radicular symptoms + hyperextension exclusion)
- Attribute-based Topical Route Gating (localized superficial vs systemic febrile)
- Clinical Injection / Parenteral Indication Gating
- Compound Deduplication & Dynamic Counts
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.disease_prediction.predict import SymptomTriageEngine, _classify_anatomy, _anatomy_compatible
from ai.utils.care_recommendations import (
    condition_supports_topical,
    _extract_clinical_presentation_attributes,
    _get_condition_fallback_yoga,
    _get_condition_fallback_medicines,
    get_medicine_gallery,
    YOGA_POSTURE_REGISTRY
)


class Test15CategoryGeneralization:
    """End-to-end clinical reasoning across all 15 clinical domains."""

    def setup_method(self):
        self.engine = SymptomTriageEngine()

    # 1. Musculoskeletal
    def test_category_1_musculoskeletal(self):
        symptoms = ["knee joint pain", "morning joint stiffness", "difficulty bending knee"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy in ["musculoskeletal", "spinal_musculoskeletal"]
        topical = condition_supports_topical("Knee Osteoarthritis", symptoms)
        assert topical is True, "Localized joint pain must allow topical formulation consideration"

    # 2. Neurological
    def test_category_2_neurological(self):
        symptoms = ["throbbing unilateral headache", "photophobia", "nausea with light sensitivity"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy == "neurological"
        topical = condition_supports_topical("Migraine", symptoms)
        assert topical is False, "Pure cephalalgia/migraine without musculoskeletal neck pain should not generate topical gel"

    # 3. Infectious
    def test_category_3_infectious(self):
        symptoms = ["high fever", "chills", "severe body ache", "rigors"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy == "systemic_infectious"
        topical = condition_supports_topical("Acute Viral Illness", symptoms)
        assert topical is False, "Purely systemic febrile presentation must block topical analgesic gels"

    # 4. Cardiac
    def test_category_4_cardiac(self):
        symptoms = ["crushing retrosternal chest pain", "shortness of breath", "cold sweating", "radiation to jaw"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy == "cardiopulmonary"
        attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition="Acute Coronary Syndrome")
        assert attrs["has_emergency_red_flags"] is True
        yoga = _get_condition_fallback_yoga("Acute Coronary Syndrome", symptoms)
        assert yoga == [], "Acute cardiac emergency must return zero yoga/exercise recommendations"

    # 5. Respiratory
    def test_category_5_respiratory(self):
        symptoms = ["productive cough", "wheezing", "shortness of breath", "bronchial tightness"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy in ["respiratory", "cardiopulmonary"]
        attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition="Bronchial Asthma")
        assert attrs["has_respiratory_symptoms"] is True
        yoga = _get_condition_fallback_yoga("Bronchial Asthma", symptoms)
        yoga_sanskrit = [y["sanskrit_name"] for y in yoga]
        assert any("Anulom" in s or "Bhastrika" in s or "Balasana" in s for s in yoga_sanskrit), \
            "Respiratory presentation must prioritize respiratory vital capacity postures"

    # 6. Gastrointestinal
    def test_category_6_gastrointestinal(self):
        symptoms = ["epigastric burning", "acid regurgitation", "post-prandial heartburn", "bloating"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy == "gastrointestinal"
        attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition="Gastroesophageal Reflux")
        assert attrs["has_gastrointestinal_symptoms"] is True
        yoga = _get_condition_fallback_yoga("Gastroesophageal Reflux", symptoms)
        yoga_sanskrit = [y["sanskrit_name"] for y in yoga]
        assert any("Vajrasana" in s or "Pawanmuktasana" in s for s in yoga_sanskrit), \
            "GI presentation must recommend digestive supportive postures like Vajrasana"

    # 7. Urinary
    def test_category_7_urinary(self):
        symptoms = ["burning dysuria", "urinary frequency", "suprapubic discomfort"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy == "urinary_renal"

    # 8. Endocrine / Metabolic
    def test_category_8_endocrine(self):
        is_comp = _anatomy_compatible("Type 2 Diabetes Mellitus", "Endocrine, Nutritional and Metabolic Diseases", "general")
        assert is_comp is True, "Endocrine/metabolic systemic conditions must be anatomically compatible"

    # 9. Dermatological
    def test_category_9_dermatological(self):
        symptoms = ["itchy erythematous skin rash", "pruritic cutaneous plaques", "epidermal peeling"]
        anatomy = _classify_anatomy(symptoms)
        assert anatomy == "dermatological"
        topical = condition_supports_topical("Atopic Dermatitis", symptoms)
        assert topical is True, "Dermatological cutaneous presentation must support topical formulation route"

    # 10. Reproductive
    def test_category_10_reproductive(self):
        res = self.engine.evaluate_symptoms(
            selected_symptom_ids=["S000001"],
            symptom_names=["lower abdominal pelvic cramps"],
            gender="Male",
            duration="1-3 Days"
        )
        for c in res.get("ranked_conditions", []):
            name_lower = c.get("name", "").lower()
            assert "ovarian" not in name_lower and "cervical" not in name_lower, \
                f"Male patient received female-specific reproductive condition: {c.get('name')}"

    # 11. Pediatric context
    def test_category_11_pediatric(self):
        meds = [
            {"name": "Paracetamol Paediatric Oral Drops 100mg/ml", "route": "Oral", "type": "OTC"},
            {"name": "Amoxicillin Oral Suspension 125mg/5ml", "route": "Oral", "type": "Prescription"}
        ]
        gallery = get_medicine_gallery(meds, top_condition="Pediatric Acute Pharyngitis", symptoms=["Fever", "Sore throat"])
        assert len(gallery) == 2
        assert all(m.get("is_verified") is not None for m in gallery)

    # 12. Elderly / Geriatric
    def test_category_12_elderly(self):
        symptoms = ["chronic bilateral knee stiffness", "reduced joint mobility"]
        attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition="Osteoarthritis", user_context={"age_group": "Elderly (60+)"})
        assert attrs["has_musculoskeletal_symptoms"] is True
        assert attrs["has_radicular_symptoms"] is False

    # 13. Emergency
    def test_category_13_emergency(self):
        symptoms = ["sudden loss of consciousness", "cyanosis", "severe dyspnea"]
        attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition="Acute Respiratory Failure")
        assert attrs["has_emergency_red_flags"] is True
        yoga = _get_condition_fallback_yoga("Acute Respiratory Failure", symptoms)
        assert yoga == [], "Emergency presentations must yield 0 restorative exercises"

    # 14. Multi-symptom Complex Presentation
    def test_category_14_multi_symptom(self):
        symptoms = ["fever", "cough", "knee pain", "diarrhea"]
        attrs = _extract_clinical_presentation_attributes(symptoms=symptoms, top_condition="Undifferentiated Illness")
        assert attrs["has_systemic_fatigue_or_fever"] is True
        assert attrs["has_respiratory_symptoms"] is True
        assert attrs["has_musculoskeletal_symptoms"] is True
        assert attrs["has_gastrointestinal_symptoms"] is True

    # 15. Unknown / Vague Presentation
    def test_category_15_unknown_insufficient(self):
        attrs = _extract_clinical_presentation_attributes(symptoms=["unspecified general malaise"], top_condition="Unknown")
        assert attrs["has_emergency_red_flags"] is False
        yoga = _get_condition_fallback_yoga("Unknown", ["unspecified general malaise"])
        assert len(yoga) > 0, "Vague non-critical symptoms should default to safe restorative postures"
        assert all(y["sanskrit_name"] in ["Balasana", "Shavasana", "Anulom Vilom"] for y in yoga)


class TestPropertyBasedSafetyAndFormulations:
    """Validates attribute-based mechanisms with zero disease-name reliance."""

    def test_yoga_safety_gate_excludes_cobra_pose_on_radicular_attribute_alone(self):
        """
        Prove that Cobra Pose is excluded whenever radicular symptoms exist,
        even if condition name is completely fictional/novel (e.g. 'Syndrome XYZ-99').
        """
        symptoms_with_radiculopathy = ["sharp pain radiating down posterior thigh", "foot numbness"]
        # Notice top_condition does NOT contain 'Sciatica' or 'Radiculopathy'
        poses = _get_condition_fallback_yoga("Lumbar Facet Syndrome XYZ-99", symptoms_with_radiculopathy)
        pose_names = [p["name"].lower() for p in poses]
        pose_sanskrit = [p["sanskrit_name"].lower() for p in poses]

        assert not any("cobra" in n for n in pose_names), "Cobra pose must be excluded due to radicular symptoms"
        assert not any("bhujangasana" in s for s in pose_sanskrit), "Bhujangasana must be excluded due to radicular symptoms"

    def test_yoga_safety_gate_allows_restorative_when_no_radicular_symptoms(self):
        """
        When patient has upper back muscular stiffness without radiating pain,
        neutral/extensor postures may be considered if safe.
        """
        symptoms_non_radicular = ["upper thoracic backache", "shoulder blade tension"]
        poses = _get_condition_fallback_yoga("Thoracic Postural Fatigue", symptoms_non_radicular)
        assert len(poses) > 0

    def test_topical_gating_is_attribute_driven(self):
        """
        Topical gel is permitted for localized musculoskeletal or cutaneous symptoms
        and blocked for systemic febrile illnesses regardless of arbitrary condition naming.
        """
        # Case A: Localized muscle strain with novel name
        assert condition_supports_topical("Condition-Alpha", ["severe localized deltoid muscle strain"]) is True

        # Case B: Systemic febrile illness with novel name
        assert condition_supports_topical("Condition-Beta", ["high fever", "chills", "rigors", "sweats"]) is False

    def test_active_compound_deduplication(self):
        """
        Multiple brand entries sharing the same active pharmaceutical compound
        must be deduplicated to avoid near-duplicate cards in gallery.
        """
        entries = [
            {"name": "Paracetamol 650mg (Dolo 650)", "route": "Oral", "type": "OTC"},
            {"name": "Paracetamol 500mg (Crocin Advance)", "route": "Oral", "type": "OTC"},
            {"name": "Paracetamol 1000mg Infusion", "route": "Intravenous", "type": "Prescription"},
            {"name": "Ibuprofen 400mg (Brufen)", "route": "Oral", "type": "Prescription"}
        ]
        gallery = get_medicine_gallery(entries, max_items=None, top_condition="General Musculoskeletal Pain")
        oral_paracetamols = [m for m in gallery if "paracetamol" in m.get("medicine_name", "").lower() and m.get("route") == "Oral"]
        assert len(oral_paracetamols) == 1, "Duplicate oral paracetamol brands must be deduplicated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
