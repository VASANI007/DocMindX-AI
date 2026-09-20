"""
DocMindX AI — Canonical Symptom ID Integrity & Multilingual Normalization Suite
Mandatory data-integrity test ensuring:
1. Exact mapping against datasets/symptoms/symptoms_master.csv
2. S000135 == Back Pain
3. S000144 == Lower Back Pain Radiating to Leg (Sciatica)
4. S000265 == Animal Bite with Wound
5. S000280 == Bluish Lips in Infant
6. Negative assertions: Animal bite != S000280; Sciatica != S000101 / S000102
7. Language invariance: English, Hindi, Gujarati, Marathi, Roman variants
"""
import os
import sys
import csv
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.disease_prediction.canonical_concepts import (
    canonical_normalizer,
    validate_canonical_ids,
    ClinicalIntegrityError,
    CANONICAL_CONCEPT_PATTERNS
)


class TestCanonicalIdIntegrity:
    """Rigorous verification of canonical IDs against the master clinical taxonomy."""

    def test_symptoms_master_csv_invariants(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(root, "datasets", "symptoms", "symptoms_master.csv")
        assert os.path.exists(csv_path), f"symptoms_master.csv not found at {csv_path}"

        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            id_map = {row["symptom_id"].strip(): row["symptom_name"].strip() for row in reader if row.get("symptom_id")}

        # Mandatory canonical taxonomy checks
        assert id_map.get("S000135") == "Back Pain", f"S000135 was {id_map.get('S000135')}"
        assert id_map.get("S000144") == "Lower Back Pain Radiating to Leg (Sciatica)", f"S000144 was {id_map.get('S000144')}"
        assert id_map.get("S000265") == "Animal Bite with Wound", f"S000265 was {id_map.get('S000265')}"
        assert id_map.get("S000280") == "Bluish Lips in Infant", f"S000280 was {id_map.get('S000280')}"
        assert id_map.get("S000101") == "Excessive Belching", f"S000101 was {id_map.get('S000101')}"
        assert id_map.get("S000102") == "Stomach Cramps", f"S000102 was {id_map.get('S000102')}"

    def test_canonical_concept_patterns_mappings(self):
        # lower_back_pain must map to S000135
        assert CANONICAL_CONCEPT_PATTERNS["lower_back_pain"]["symptom_id"] == "S000135"

        # radiating_pain_lower_limb & sciatica must map to S000144
        assert CANONICAL_CONCEPT_PATTERNS["radiating_pain_lower_limb"]["symptom_id"] == "S000144"
        assert CANONICAL_CONCEPT_PATTERNS["sciatica"]["symptom_id"] == "S000144"

        # animal_bite must map to S000265
        assert CANONICAL_CONCEPT_PATTERNS["animal_bite"]["symptom_id"] == "S000265"

        # bluish_lips_infant must map to S000280
        assert CANONICAL_CONCEPT_PATTERNS["bluish_lips_infant"]["symptom_id"] == "S000280"

        # Hard negative integrity assertions
        assert CANONICAL_CONCEPT_PATTERNS["animal_bite"]["symptom_id"] != "S000280"
        assert CANONICAL_CONCEPT_PATTERNS["lower_back_pain"]["symptom_id"] != "S000101"
        assert CANONICAL_CONCEPT_PATTERNS["radiating_pain_lower_limb"]["symptom_id"] != "S000102"
        assert CANONICAL_CONCEPT_PATTERNS["sciatica"]["symptom_id"] != "S000101"
        assert CANONICAL_CONCEPT_PATTERNS["sciatica"]["symptom_id"] != "S000102"

    def test_runtime_validation_passes(self):
        assert validate_canonical_ids() is True

    @pytest.mark.parametrize("input_text, lang", [
        ("A street dog bit my lower leg 2 hours ago.", "en"),
        ("मुझे 2 घंटे पहले एक आवारा कुत्ते ने पैर में काट लिया।", "hi"),
        ("મને 2 કલાક પહેલા શેરીના કુતરાએ પગમાં બટકું ભર્યું.", "gu"),
        ("दोन तासांपूर्वी मला भटक्या कुत्र्याने पायाला चावा घेतला.", "mr"),
        ("mane 2 kalak pela kutra e pag ma batku bharyu", "gu_roman"),
        ("kutraye pag ma bataku bhariyu", "gu_roman"),
        ("dog ne pag ma karadyo", "gu_roman"),
    ])
    def test_animal_bite_multilingual_regression(self, input_text, lang):
        rep = canonical_normalizer.normalize(input_text)
        assert rep.clinical_attributes.get("bite_exposure") is True, f"[{lang}] bite_exposure not True"
        assert "EXP_ANIMAL_BITE" in rep.exposure_ids, f"[{lang}] EXP_ANIMAL_BITE missing"
        assert "S000265" in rep.symptom_ids, f"[{lang}] S000265 (Animal Bite with Wound) missing"

        # Hard negative checks: Animal bite must NEVER be S000280 (Bluish Lips in Infant)
        assert "S000280" not in rep.symptom_ids, f"[{lang}] S000280 (Bluish Lips) falsely assigned to animal bite!"

        # Animal bite must NOT fabricate systemic infections
        assert "S000001" not in rep.symptom_ids, f"[{lang}] S000001 (Fever) falsely introduced!"
        assert "S000061" not in rep.symptom_ids, f"[{lang}] S000061 (Headache) falsely introduced!"

    @pytest.mark.parametrize("input_text, lang", [
        ("Severe lower back pain radiating down my left leg.", "en"),
        ("कमर से दर्द बाएं पैर तक जाता है", "hi"),
        ("ડાબા પગ સુધી કમરનો દુખાવો જાય છે", "gu"),
        ("lower back pain left leg ma jaye che", "gu_roman"),
    ])
    def test_sciatica_multilingual_regression(self, input_text, lang):
        rep = canonical_normalizer.normalize(input_text)
        assert "lower_back_pain" in rep.canonical_concepts, f"[{lang}] lower_back_pain missing"
        assert "radiating_pain_lower_limb" in rep.canonical_concepts or "sciatica" in rep.canonical_concepts, f"[{lang}] radicular concept missing"
        assert "S000135" in rep.symptom_ids, f"[{lang}] S000135 (Back Pain) missing"
        assert "S000144" in rep.symptom_ids, f"[{lang}] S000144 (Sciatica) missing"

        # Hard negative checks: Sciatica must NEVER be S000101 (Belching) or S000102 (Cramps)
        assert "S000101" not in rep.symptom_ids, f"[{lang}] S000101 (Belching) falsely assigned to sciatica!"
        assert "S000102" not in rep.symptom_ids, f"[{lang}] S000102 (Cramps) falsely assigned to sciatica!"

        # Must not fabricate fever or headache
        assert "S000001" not in rep.symptom_ids, f"[{lang}] S000001 (Fever) falsely introduced!"
        assert "S000061" not in rep.symptom_ids, f"[{lang}] S000061 (Headache) falsely introduced!"

    @pytest.mark.parametrize("input_text, lang", [
        ("Severe stomach pain and cramps for 2 days", "en"),
        ("मुझे पेट में तेज़ दर्द हो रहा है", "hi"),
        ("મને પેટમાં સખત દુખાવો થાય છે", "gu"),
        ("pet ma dukhava thay che", "gu_roman"),
        ("stomach pain and belly ache", "en"),
    ])
    def test_abdominal_pain_regression(self, input_text, lang):
        rep = canonical_normalizer.normalize(input_text)
        assert "abdominal_pain" in rep.canonical_concepts, f"[{lang}] abdominal_pain concept missing"
        assert "S000092" in rep.symptom_ids, f"[{lang}] S000092 (Abdominal Pain) missing"
        # Hard negative check: Abdominal pain must NEVER be S000091 (Constipation)
        assert "S000091" not in rep.symptom_ids, f"[{lang}] S000091 (Constipation) falsely assigned to stomach pain!"

    @pytest.mark.parametrize("input_text, lang", [
        ("I have a red skin rash on my chest", "en"),
        ("त्वचा पर लाल चकत्ते और दाने हैं", "hi"),
        ("ત્વચા પર લાલ ચકામા પડ્યા છે", "gu"),
        ("skin rash and redness", "en"),
        ("chakama padi gaya che", "gu_roman"),
    ])
    def test_skin_rash_regression(self, input_text, lang):
        rep = canonical_normalizer.normalize(input_text)
        assert "skin_rash" in rep.canonical_concepts, f"[{lang}] skin_rash concept missing"
        assert "S000109" in rep.symptom_ids, f"[{lang}] S000109 (Skin Rash) missing"
        # Hard negative check: Skin rash must NEVER be S000108 (Worm Infestation)
        assert "S000108" not in rep.symptom_ids, f"[{lang}] S000108 (Worm Infestation) falsely assigned to skin rash!"

    @pytest.mark.parametrize("input_text, lang", [
        ("धाधर है लाल चकत्ते हैं", "hi"),
        ("મને ધાધર થઈ છે અને લાલચમઠા પડ્યા છે", "gu"),
        ("dhadhar thay chhe lalchmbha padiya chhe", "gu_roman"),
        ("ringworm fungal infection with round rash", "en"),
    ])
    def test_dermatology_tinea_regression(self, input_text, lang):
        rep = canonical_normalizer.normalize(input_text)
        assert "fungal_skin_infection" in rep.canonical_concepts or "skin_rash" in rep.canonical_concepts, f"[{lang}] skin/fungal concept missing"
        assert any(sid in rep.symptom_ids for sid in ["S000124", "S000109"]), f"[{lang}] Expected S000124 or S000109, got {rep.symptom_ids}"
        # Hard negative checks: No worm infestation, no fabricated malaria/fever
        assert "S000108" not in rep.symptom_ids, f"[{lang}] Worm Infestation falsely assigned!"
        assert "S000001" not in rep.symptom_ids, f"[{lang}] Fever falsely fabricated!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
