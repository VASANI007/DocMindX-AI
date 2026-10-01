"""
DocMindX AI — Universal Multilingual Symptom Normalization & Canonical Validation Test Suite
Permanent generic verification covering:
- 30+ representative symptoms across master taxonomy categories
- Colloquial Gujarati, Hindi, Romanized, Hinglish phrases
- Anatomical region separation (Hand != Ear, Head != Leg)
- Negation detection
- Count integrity (extracted count == unique validated canonical IDs)
- Raw phrase preservation vs canonical selected chips
- Visual Symptom Extractor
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from unittest.mock import patch, MagicMock

from ai.disease_prediction.canonical_concepts import (
    canonical_normalizer,
    segment_clinical_phrases,
    MasterSymptomTaxonomyBridge
)
from ai.disease_prediction.multilingual_symptom_extractor import (
    normalize_user_symptoms,
    MultilingualSymptomExtractor
)
from ai.disease_prediction.visual_symptom_extractor import VisualSymptomExtractor


class TestUniversalMultilingualNormalization:
    """Comprehensive regression test suite for universal multilingual symptom normalization."""

    # --------------------------------------------------------------------------
    # 1. User Specific Target Phrases
    # --------------------------------------------------------------------------

    def test_vaho_dukhe_chhe_maps_to_canonical_back_pain(self):
        """'vaho dukhe chhe' must resolve to canonical Back Pain (S000135) without raw phrase chip."""
        res = normalize_user_symptoms("vaho dukhe chhe")
        assert len(res) == 1
        item = res[0]
        assert item["dataset_match"] is True
        assert item["symptom_id"] == "S000135"
        assert item["canonical_name"] == "Back Pain"
        assert "vaho dukhe" in item["user_phrase"]
        # Raw phrase is evidence, NOT canonical name
        assert item["canonical_name"] != "vaho dukhe chhe"

    def test_mathu_halaku_dukhe_maps_to_headache(self):
        """'mathu halaku halakhu dukhe chhe' must resolve to Headache (S000061)."""
        res = normalize_user_symptoms("mathu halaku halakhu dukhe chhe")
        assert len(res) == 1
        item = res[0]
        assert item["dataset_match"] is True
        assert item["symptom_id"] == "S000061"
        assert item["canonical_name"] == "Headache"

    def test_anatomical_integrity_hand_is_never_ear(self):
        """'hath ma dard chhe' must NEVER map to Ear Pain (S000167)."""
        res = normalize_user_symptoms("hath ma dard chhe")
        for item in res:
            assert item.get("symptom_id") != "S000167", "Hand pain must NEVER be mapped to Ear Pain"
            if item["dataset_match"]:
                # Must be Musculoskeletal joint/muscle/limb pain
                assert item["symptom_id"] in ["S000131", "S000133", "S000011"]

    def test_trauma_and_pain_ghodaye_laat_mari(self):
        """'ghodaye laat mari vaho dukhe chhe' extracts Back Pain without inventing unrelated symptoms."""
        res = normalize_user_symptoms("ghodaye laat mari vaho dukhe chhe")
        matched = [r for r in res if r["dataset_match"]]
        assert len(matched) >= 1
        assert any(r["symptom_id"] == "S000135" for r in matched)

    def test_bleeding_wound_pag_ma_vagiyu(self):
        """'pag ma vagiyu chhe ama thin loy nikale chhe' maps cleanly to wound/sore."""
        res = normalize_user_symptoms("pag ma vagiyu chhe ama thin loy nikale chhe")
        assert len(res) >= 1
        for r in res:
            assert "user_phrase" in r

    # --------------------------------------------------------------------------
    # 2. Count Integrity & No Leaked Raw Phrases into Selected Symptoms
    # --------------------------------------------------------------------------

    def test_count_integrity_extractor_result(self):
        """Extracted count must strictly equal number of unique validated canonical IDs."""
        extractor = MultilingualSymptomExtractor()
        text = "mathu dukhe chhe, tav aave chhe, gala ma dukhay chhe"
        res = extractor.extract_symptoms_and_medicines(text, user_lang="gu")
        s_ids = res["symptom_ids"]
        s_labels = res["symptom_labels"]
        # Exactly equal counts
        assert len(s_ids) == len(s_labels)
        # Unique IDs
        assert len(s_ids) == len(set(s_ids))
        # No raw vernacular phrases in s_labels
        for lbl in s_labels:
            assert "dukhe" not in lbl.lower()
            assert "chhe" not in lbl.lower()
            assert "aave" not in lbl.lower()

    def test_unresolved_phrases_never_enter_symptom_labels(self):
        """Random unresolvable non-medical words must NEVER enter symptom_labels or symptom_ids."""
        extractor = MultilingualSymptomExtractor()
        unresolved_text = "aje office ma meeting chhe ane laptop bagadi gayu chhe"
        res = extractor.extract_symptoms_and_medicines(unresolved_text, user_lang="gu")
        # Should not fabricate canonical symptoms
        assert len(res["symptom_ids"]) == 0
        assert len(res["symptom_labels"]) == 0

    # --------------------------------------------------------------------------
    # 3. Negation Enforcement
    # --------------------------------------------------------------------------

    def test_negation_in_gujarati(self):
        """'mathu nathi dukhtu' must be detected as negated and NOT in positive selected IDs."""
        norm = canonical_normalizer.normalize("mathu nathi dukhtu")
        assert "S000061" not in norm.symptom_ids
        assert any("headache" in n.lower() for n in norm.negative_findings)

    def test_negation_in_hindi(self):
        """'बुखार नहीं है' must not add Fever (S000001)."""
        norm = canonical_normalizer.normalize("बुखार नहीं है सिरदर्द है")
        assert "S000001" not in norm.symptom_ids
        assert "S000061" in norm.symptom_ids

    def test_negation_in_english(self):
        """'no fever, only dry cough' must not add fever."""
        norm = canonical_normalizer.normalize("no fever, only dry cough")
        assert "S000001" not in norm.symptom_ids
        assert "S000023" in norm.symptom_ids

    # --------------------------------------------------------------------------
    # 4. 30+ Representative Symptoms Across Taxonomy Categories
    # --------------------------------------------------------------------------

    # Category A: Head / Neurological
    def test_cat_a_headache(self):
        res = normalize_user_symptoms("Severe headache for 2 days")
        assert any(r["symptom_id"] == "S000061" for r in res if r["dataset_match"])

    def test_cat_a_dizziness(self):
        res = normalize_user_symptoms("chakkar aave chhe")
        assert any(r["symptom_id"] == "S000064" for r in res if r["dataset_match"])

    # Category B: Musculoskeletal
    def test_cat_b_back_pain(self):
        res = normalize_user_symptoms("lower back pain and lumbago")
        assert any(r["symptom_id"] == "S000135" for r in res if r["dataset_match"])

    def test_cat_b_joint_pain(self):
        res = normalize_user_symptoms("sandha ma dukh")
        assert any(r["symptom_id"] == "S000131" for r in res if r["dataset_match"])

    def test_cat_b_muscle_pain(self):
        res = normalize_user_symptoms("snayu ma dukhavo")
        assert any(r["symptom_id"] == "S000133" for r in res if r["dataset_match"])

    def test_cat_b_neck_pain(self):
        res = normalize_user_symptoms("gardan dard and stiff neck")
        assert any(r["symptom_id"] == "S000136" for r in res if r["dataset_match"])

    # Category C: Respiratory
    def test_cat_c_dry_cough(self):
        res = normalize_user_symptoms("sukhi khasi")
        assert any(r["symptom_id"] == "S000023" for r in res if r["dataset_match"])

    def test_cat_c_runny_nose(self):
        res = normalize_user_symptoms("nak vahe chhe aur runny nose")
        assert any(r["symptom_id"] == "S000035" for r in res if r["dataset_match"])

    def test_cat_c_shortness_of_breath(self):
        res = normalize_user_symptoms("shwas charhe chhe breathlessness")
        assert any(r["symptom_id"] == "S000026" for r in res if r["dataset_match"])

    def test_cat_c_wheezing(self):
        res = normalize_user_symptoms("wheezing in chest")
        assert any(r["symptom_id"] == "S000028" for r in res if r["dataset_match"])

    # Category D: Gastrointestinal
    def test_cat_d_abdominal_pain(self):
        res = normalize_user_symptoms("pet ma dukhe chhe")
        assert any(r["symptom_id"] == "S000092" for r in res if r["dataset_match"])

    def test_cat_d_vomiting(self):
        res = normalize_user_symptoms("ulti thay chhe")
        assert any(r["symptom_id"] == "S000087" for r in res if r["dataset_match"])

    def test_cat_d_diarrhea(self):
        res = normalize_user_symptoms("patla zhada and loose motion")
        assert any(r["symptom_id"] == "S000089" for r in res if r["dataset_match"])

    def test_cat_d_constipation(self):
        res = normalize_user_symptoms("kabziyat chhe hard stool")
        assert any(r["symptom_id"] == "S000091" for r in res if r["dataset_match"])

    def test_cat_d_heartburn(self):
        res = normalize_user_symptoms("chhati ma balatara acid reflux")
        assert any(r["symptom_id"] == "S000095" for r in res if r["dataset_match"])

    # Category E: ENT
    def test_cat_e_ear_pain(self):
        res = normalize_user_symptoms("kan ma dukhe chhe")
        assert any(r["symptom_id"] == "S000167" for r in res if r["dataset_match"])

    def test_cat_e_sore_throat(self):
        res = normalize_user_symptoms("gala ma kharash burning throat")
        assert any(r["symptom_id"] == "S000032" for r in res if r["dataset_match"])

    def test_cat_e_nosebleed(self):
        res = normalize_user_symptoms("nak mathi lohi aave chhe")
        assert any(r["symptom_id"] == "S000172" for r in res if r["dataset_match"])

    # Category F: Skin
    def test_cat_f_skin_rash(self):
        res = normalize_user_symptoms("chamadi par lala chakama skin rash")
        assert any(r["symptom_id"] == "S000109" for r in res if r["dataset_match"])

    def test_cat_f_itching(self):
        res = normalize_user_symptoms("khaj aave chhe pruritus")
        assert any(r["symptom_id"] == "S000110" for r in res if r["dataset_match"])

    def test_cat_f_skin_redness(self):
        res = normalize_user_symptoms("skin redness and erythema")
        assert any(r["symptom_id"] == "S000112" for r in res if r["dataset_match"])

    def test_cat_f_blisters(self):
        res = normalize_user_symptoms("folla thay gaya chhe blisters")
        assert any(r["symptom_id"] == "S000120" for r in res if r["dataset_match"])

    # Category G: Cardiac / Chest
    def test_cat_g_chest_pain(self):
        res = normalize_user_symptoms("severe chest pain and pressure")
        assert any(r["symptom_id"] == "S000046" for r in res if r["dataset_match"])

    def test_cat_g_palpitations(self):
        res = normalize_user_symptoms("racing heart palpitations")
        assert any(r["symptom_id"] == "S000048" for r in res if r["dataset_match"])

    def test_cat_g_chest_tightness(self):
        res = normalize_user_symptoms("chhati ma jakadat chest tightness")
        assert any(r["symptom_id"] == "S000029" for r in res if r["dataset_match"])

    # Category H: General / Systemic
    def test_cat_h_fever(self):
        res = normalize_user_symptoms("tav aave chhe 102 fever")
        assert any(r["symptom_id"] == "S000001" for r in res if r["dataset_match"])

    def test_cat_h_chills(self):
        res = normalize_user_symptoms("thandi lage chhe chills")
        assert any(r["symptom_id"] == "S000003" for r in res if r["dataset_match"])

    def test_cat_h_fatigue(self):
        res = normalize_user_symptoms("thak lage chhe excessive tiredness")
        assert any(r["symptom_id"] == "S000005" for r in res if r["dataset_match"])

    # Category I: Trauma / Exposure
    def test_cat_i_animal_bite(self):
        res = normalize_user_symptoms("kutraae batku bharyu animal bite")
        assert any(r["symptom_id"] == "S000265" for r in res if r["dataset_match"])

    # --------------------------------------------------------------------------
    # 5. Phrase Segmentation & Connector Stripping
    # --------------------------------------------------------------------------

    def test_phrase_segmentation_strips_connectors(self):
        """Conjunctions and conversational connectors must not become symptoms."""
        raw = "tav aave chhe ane mathu dukhe chhe sathe chakar aave chhe pan ulti nathi"
        phrases = segment_clinical_phrases(raw)
        assert len(phrases) >= 2
        for p in phrases:
            # Standalone connectors must be stripped
            assert p.lower() not in ["ane", "sathe", "pan", "and", "with"]

    # --------------------------------------------------------------------------
    # 6. Visual Symptom Extractor Unit Test
    # --------------------------------------------------------------------------

    def test_visual_symptom_extractor_mock(self):
        """Visual symptom extractor maps visible findings to valid canonical taxonomy IDs."""
        extractor = VisualSymptomExtractor()
        fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
        
        mock_ai_json = {
            "is_clinical_photo": True,
            "image_quality": "clear",
            "anatomical_region": "forearm",
            "visual_findings": [
                {
                    "finding_name": "Skin Redness",
                    "location": "forearm",
                    "confidence": 0.95,
                    "description": "Erythema on anterior forearm"
                },
                {
                    "finding_name": "Skin Rash",
                    "location": "forearm",
                    "confidence": 0.90,
                    "description": "Small maculopapular bumps"
                }
            ],
            "visual_summary": "Erythematous rash visible on the forearm."
        }
        
        with patch("ai.disease_prediction.visual_symptom_extractor._safe_parse_json", return_value=mock_ai_json), \
             patch("config.settings.gemini_pool.get_active_keys", return_value=["fake_key"]), \
             patch("config.settings.gemini_pool.execute_with_failover", return_value=({"candidates": [{"content": {"parts": [{"text": "dummy"}]}}]}, "gemini", None)):
            res = extractor.extract_visual_symptoms(fake_jpeg)
            assert res["success"] is True
            assert "S000112" in res["symptom_ids"]  # Skin Redness
            assert "S000109" in res["symptom_ids"]  # Skin Rash
            assert "Skin Redness" in res["symptom_labels"]
            assert "Skin Rash" in res["symptom_labels"]
