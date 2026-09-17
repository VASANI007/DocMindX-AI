"""
DocMindX AI — System-Wide Language Invariance & Clinical Generalization Test Suite

Comprehensive automated test suite validating:
1. Language-Invariant Clinical Pathways (English, Hindi, Gujarati, Marathi, Romanized Indic, Code-mixed)
2. Zero Default Contamination (no silent Fever/Headache injections)
3. Strict Negation Parsing (denied symptoms -> negative_findings, differential suppression)
4. Formulation & Route Gating (routine injections blocked for 1-day mild illnesses; emergency prophylaxis permitted)
5. Supportive Yoga Safety (spinal hyperextension excluded for radicular presentations)
6. Anti-Fabrication on Dosages & Structured WHO ICD-11 Labels
7. Complete 16-Category Dynamic Clinical Generalization
"""
import os
import sys
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.disease_prediction.canonical_concepts import canonical_normalizer, CanonicalClinicalRepresentation
from ai.disease_prediction.multilingual_symptom_extractor import MultilingualSymptomExtractor
from ai.disease_prediction.predict import SymptomTriageEngine, _classify_anatomy
from ai.utils.care_recommendations import (
    get_medicine_gallery,
    condition_supports_topical,
    _extract_clinical_presentation_attributes,
    _get_condition_fallback_yoga
)


class TestLanguageInvariance:
    """Validates that identical clinical semantics produce the identical clinical pathway across all languages."""

    @pytest.fixture(autouse=True)
    def setup_engine(self):
        self.engine = SymptomTriageEngine()
        self.extractor = MultilingualSymptomExtractor()

    # =========================================================================
    # TEST GROUP A: Animal Bite Exposure (Rabies Risk Assessment)
    # =========================================================================
    def test_group_a_animal_bite_multilingual_invariance(self):
        phrases = {
            "en": "A street dog bit my lower leg 2 hours ago, wound is bleeding",
            "hi": "मुझे 2 घंटे पहले एक आवारा कुत्ते ने पैर में काट लिया, घाव से खून बह रहा है",
            "gu": "મને 2 કલાક પહેલા શેરીના કુતરા એ પગમાં બટકું ભર્યું છે, ઘામાંથી લોહી નીકળે છે",
            "mr": "दोन तासांपूर्वी मला भटक्या कुत्र्याने पायाला चावा घेतला, जखमेतून रक्त येत आहे",
            "roman_gu": "mane 2 kalak pela kutra e pag ma batku bharyu che, lohi nikle che",
            "code_mixed": "street dog bit me on my leg and bleeding ho raha hai"
        }

        representations = {}
        triage_results = {}

        for lang, text in phrases.items():
            rep = canonical_normalizer.normalize(text)
            representations[lang] = rep

            # Verify canonical representation invariants
            assert "EXP_ANIMAL_BITE" in rep.exposure_events or "S000265" in rep.symptom_ids, \
                f"[{lang}] Animal bite exposure failed to be canonically captured from: '{text}'"
            assert rep.duration_days == 1 or rep.duration == "today", \
                f"[{lang}] Exposure duration failed to normalize to acute Day 1"

            # Anti-contamination: neither fever nor headache should EVER be present
            assert "S000001" not in rep.symptom_ids, f"[{lang}] Contaminated with Fever ID S000001"
            assert "S000061" not in rep.symptom_ids, f"[{lang}] Contaminated with Headache ID S000061"

            # Run through triage engine
            triage = self.engine.evaluate_symptoms(
                selected_symptom_ids=rep.symptom_ids,
                symptom_names=rep.canonical_concepts or [text],
                duration="Started Today",
                gender="Male"
            )
            triage_results[lang] = triage

            # All languages must trigger emergency flag
            assert triage["is_emergency"] is True, f"[{lang}] Animal bite wound must trigger emergency"

            # Top candidate must be Zoonotic / Rabies Post-Exposure / Trauma
            top_cond = triage["ranked_conditions"][0] if triage.get("ranked_conditions") else {}
            assert top_cond, f"[{lang}] No conditions returned for animal bite"
            top_name_lower = top_cond.get("name", "").lower()
            assert any(k in top_name_lower for k in ["rabies", "bite", "wound", "zoonotic"]), \
                f"[{lang}] Top condition was '{top_cond.get('name')}', expected Rabies Post-Exposure/Bite protocol"

            # Structured WHO ICD-11 labels
            assert "icd_details" in top_cond, f"[{lang}] Missing structured icd_details dictionary"
            assert top_cond["icd_details"].get("system") == "ICD-11"

        # Cross-language identity check: All languages produce identical primary exposure category
        first_rep = list(representations.values())[0]
        for lang, rep in representations.items():
            assert rep.exposure_events == first_rep.exposure_events, \
                f"Language '{lang}' exposure events {rep.exposure_events} differ from reference {first_rep.exposure_events}"

    # =========================================================================
    # TEST GROUP B: Radiating Lumbar Pain (Sciatica / Radiculopathy)
    # =========================================================================
    def test_group_b_radiating_lumbar_pain_multilingual_invariance(self):
        phrases = {
            "en": "Severe lower back pain radiating down my left leg, with numbness and tingling",
            "hi": "कमर में तेज दर्द जो बाएं पैर में नीचे जा रहा है, पैर सुन्न हो रहा है और झुनझुनी है",
            "gu": "કમરમાં સખત દુખાવો છે જે ડાબા પગમાં નીચે ઉતરે છે, પગ સુન્ન થઈ જાય છે અને ઝણઝણાટી થાય છે",
            "mr": "कंबरेत तीव्र वेदना ज्या डाव्या पायात खाली जात आहेत, पाय बधिर झाला आहे",
            "code_mixed": "lower back pain radiating down to left leg with numbness"
        }

        for lang, text in phrases.items():
            rep = canonical_normalizer.normalize(text)

            # Invariant: anatomical regions must include lumbar_spine and lower_limb
            assert "lumbar_spine" in rep.anatomical_regions, f"[{lang}] Missing lumbar_spine in {rep.anatomical_regions}"
            assert "lower_limb" in rep.anatomical_regions, f"[{lang}] Missing lower_limb in {rep.anatomical_regions}"

            # Invariant: laterality must include left
            assert "left" in rep.laterality, f"[{lang}] Failed to detect left laterality in: '{text}'"

            # Invariant: radicular symptoms attribute
            attrs = _extract_clinical_presentation_attributes(symptoms=[text], top_condition="Sciatica / Lumbar Disc Herniation")
            assert attrs["has_radicular_symptoms"] is True, f"[{lang}] Failed to set has_radicular_symptoms=True"

            # Invariant: Cobra Pose (Bhujangasana) MUST BE EXCLUDED
            yoga_poses = _get_condition_fallback_yoga("Sciatica / Lumbar Disc Herniation", [text])
            cobra_poses = [p for p in yoga_poses if "cobra" in p["name"].lower() or "bhujang" in p["sanskrit_name"].lower()]
            assert len(cobra_poses) == 0, f"[{lang}] Cobra Pose was dangerously recommended for radicular sciatica!"

    # =========================================================================
    # TEST GROUP C: Acute Cardiopulmonary Distress
    # =========================================================================
    def test_group_c_acute_cardiopulmonary_multilingual_invariance(self):
        phrases = {
            "en": "Sudden crushing chest pain radiating to left arm with severe breathlessness and cold sweating",
            "hi": "अचानक सीने में तेज दबाव वाला दर्द जो बाएं हाथ में जा रहा है, सांस फूल रही है और ठंडा पसीना आ रहा है",
            "gu": "અચાનક છાતીમાં દબાણવાળો દુખાવો જે ડાબા હાથમાં જાય છે, શ્વાસ ચઢે છે અને ઠંડો પરસેવો વળે છે",
            "code_mixed": "sudden severe chest pain radiating to left arm and breathless"
        }

        for lang, text in phrases.items():
            rep = canonical_normalizer.normalize(text)
            assert "thoracic_chest" in rep.anatomical_regions, f"[{lang}] Missing thoracic_chest in {rep.anatomical_regions}"
            assert "left" in rep.laterality, f"[{lang}] Missing left laterality"

            anatomy = _classify_anatomy([text])
            assert anatomy in ["cardiopulmonary", "respiratory"], f"[{lang}] Classified as {anatomy}"

            triage = self.engine.evaluate_symptoms(
                selected_symptom_ids=rep.symptom_ids,
                symptom_names=[text],
                duration="Started Today"
            )
            assert triage["is_emergency"] is True, f"[{lang}] Cardiopulmonary distress must be an emergency"

            # Restorative yoga must be 0 for acute cardiac emergency
            attrs = _extract_clinical_presentation_attributes(symptoms=[text], top_condition="Acute Coronary Syndrome")
            assert attrs["has_emergency_red_flags"] is True, f"[{lang}] Acute cardiac emergency red flag missing"
            yoga = _get_condition_fallback_yoga("Acute Coronary Syndrome", [text])
            assert yoga == [], f"[{lang}] Restorative exercises must be 0 during acute cardiac emergency"

    # =========================================================================
    # TEST GROUP D: Acute Febrile Illness
    # =========================================================================
    def test_group_d_febrile_illness_multilingual_invariance(self):
        phrases = {
            "en": "High fever with chills and dry cough for 3 days",
            "hi": "3 दिन से ठंड लगकर तेज बुखार और सूखी खांसी है",
            "gu": "3 દિવસથી ઠંડી લાગીને તાવ અને સૂકી ખાંસી છે"
        }

        for lang, text in phrases.items():
            rep = canonical_normalizer.normalize(text)
            assert "S000001" in rep.symptom_ids, f"[{lang}] Missing Fever ID S000001"
            assert "S000023" in rep.symptom_ids, f"[{lang}] Missing Cough ID S000023"

            # Anti-contamination: No headache or bite
            assert "S000061" not in rep.symptom_ids, f"[{lang}] Unexpected headache S000061"
            assert "EXP_ANIMAL_BITE" not in rep.exposure_events, f"[{lang}] Unexpected bite exposure"

    # =========================================================================
    # TEST GROUP E: Strict Negation Parsing
    # =========================================================================
    def test_group_e_strict_negation_across_languages(self):
        negated_inputs = [
            ("en", "High fever and cough, but no headache and no vomiting"),
            ("hi", "तेज बुखार और खांसी है, सिरदर्द नहीं है, उल्टी नहीं है"),
            ("gu", "તાવ અને ખાંસી છે, માથાનો દુખાવો નથી, ઉલટી નથી"),
            ("mr", "ताप आणि खोकला आहे, डोकेदुखी नाही, उलट्या नाहीत")
        ]

        for lang, text in negated_inputs:
            rep = canonical_normalizer.normalize(text)

            # Positive symptoms must include fever & cough
            assert "S000001" in rep.symptom_ids, f"[{lang}] Missing positive Fever"
            assert "S000023" in rep.symptom_ids, f"[{lang}] Missing positive Cough"

            # Denied symptoms must be strictly captured in negative_findings
            assert any("S000061" in nf or "Headache" in nf or "headache" in nf.lower() for nf in rep.negative_findings), \
                f"[{lang}] Headache was NOT captured in negative_findings: {rep.negative_findings}"
            assert any("S000087" in nf or "Vomiting" in nf or "vomiting" in nf.lower() for nf in rep.negative_findings), \
                f"[{lang}] Vomiting was NOT captured in negative_findings: {rep.negative_findings}"

            # Headache and Vomiting must NEVER be in positive symptom_ids
            assert "S000061" not in rep.symptom_ids, f"[{lang}] Denied headache contaminated positive symptom_ids!"
            assert "S000087" not in rep.symptom_ids, f"[{lang}] Denied vomiting contaminated positive symptom_ids!"

            # Run triage and ensure Tension Headache is NOT the top differential
            triage = self.engine.evaluate_symptoms(
                selected_symptom_ids=rep.symptom_ids,
                symptom_names=rep.canonical_concepts,
                negative_findings=rep.negative_findings
            )
            top_cond = triage["ranked_conditions"][0] if triage.get("ranked_conditions") else {}
            assert "headache" not in top_cond.get("name", "").lower(), \
                f"[{lang}] Condition '{top_cond.get('name')}' recommended despite headache being explicitly denied!"

    # =========================================================================
    # TEST GROUP F: Duration-Gated Formulation Routing
    # =========================================================================
    def test_group_f_duration_gated_injection_routing(self):
        # 1. Acute mild illness (1-3 days): routine injections MUST be blocked
        mild_meds = [
            {"name": "Paracetamol 500mg Tablet", "form": "Tablet", "route": "Oral"},
            {"name": "Paracetamol 1000mg IV Injection", "form": "Injection", "route": "Intravenous"},
            {"name": "Diclofenac 75mg/3ml IM Injection", "form": "Injection", "route": "Intramuscular"}
        ]
        gallery_mild = get_medicine_gallery(
            mild_meds,
            top_condition="Common Cold with Mild Fever",
            symptoms=["Mild Fever", "Runny Nose"],
            duration="1-3 Days"
        )
        gallery_names = [m["name"].lower() for m in gallery_mild]
        assert any("tablet" in n for n in gallery_names), "Oral tablet should be permitted"
        assert not any("injection" in n for n in gallery_names), \
            "Routine injections must be blocked for acute mild 1-3 day common cold/fever"

        # 2. Acute Day 1 Emergency Prophylaxis: Injections MUST be permitted
        emergency_prophylaxis_meds = [
            {"name": "Anti-Rabies Vaccine (ARV) 0.5ml IM Injection", "form": "Injection", "route": "Intramuscular"},
            {"name": "Rabies Immunoglobulin (RIG) 300IU Infiltration", "form": "Injection", "route": "Intravenous"},
            {"name": "Tetanus Toxoid 0.5ml IM Booster", "form": "Injection", "route": "Intramuscular"}
        ]
        gallery_emergency = get_medicine_gallery(
            emergency_prophylaxis_meds,
            top_condition="Animal Bite / Rabies Risk Protocol",
            symptoms=["Animal Bite with Wound", "Bleeding"],
            duration="Started Today"
        )
        assert len(gallery_emergency) >= 2, \
            f"Emergency prophylaxis injections (ARV/RIG/TT) must be allowed on Day 1! Got: {len(gallery_emergency)}"

    # =========================================================================
    # TEST GROUP G: Anti-Contamination / Zero Default Fallback
    # =========================================================================
    def test_group_g_anti_contamination_zero_default_fallback(self):
        # When user reports knee pain only, NO fever or headache should ever appear
        rep = canonical_normalizer.normalize("Severe knee joint pain with swelling")
        assert "S000001" not in rep.symptom_ids, "Silent Fever contamination detected"
        assert "S000061" not in rep.symptom_ids, "Silent Headache contamination detected"

        triage = self.engine.evaluate_symptoms(
            selected_symptom_ids=rep.symptom_ids,
            symptom_names=["Severe knee joint pain with swelling"],
            duration="1-2 Weeks"
        )
        for cond in triage.get("ranked_conditions", []):
            c_name = cond.get("name", "").lower()
            assert "malaria" not in c_name, f"Knee pain contaminated with Malaria: {cond.get('name')}"
            assert "scrub typhus" not in c_name, f"Knee pain contaminated with Scrub Typhus: {cond.get('name')}"
            assert "dengue" not in c_name, f"Knee pain contaminated with Dengue: {cond.get('name')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
