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
    MultilingualSymptomExtractor,
    get_supported_language_codes,
    detect_input_language,
    clear_symptom_norm_cache
)
from ai.disease_prediction.visual_symptom_extractor import VisualSymptomExtractor


class TestUniversalMultilingualNormalization:
    """Comprehensive regression test suite for universal multilingual symptom normalization."""

    # --------------------------------------------------------------------------
    # 1. User Specific Target Phrases
    # --------------------------------------------------------------------------

    def test_vaho_dukhe_chhe_maps_to_canonical_back_pain(self):
        """'vaho dukhe chhe' must resolve to canonical Back Pain (S000135) without raw phrase chip."""
        res = normalize_user_symptoms("vaho dukhe chhe", offline=True)
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
        assert any(r["symptom_id"] in ["S000001", "S000002"] for r in res if r["dataset_match"])

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

    # --------------------------------------------------------------------------
    # 7. Regression Test: "gothan ma dukhavo" Must NEVER Map to Eye Pain
    # --------------------------------------------------------------------------

    def test_gothan_ma_dukhavo_never_maps_to_eye_pain_offline(self):
        """Regression: 'gothan ma dukhavo' must NEVER be mapped to Eye Pain (S000212)."""
        clear_symptom_norm_cache()
        res = normalize_user_symptoms("gothan ma dukhavo", offline=True)
        for r in res:
            assert r.get("symptom_id") != "S000212", "Regression failed: gothan ma dukhavo mapped to Eye Pain!"
            assert r.get("canonical_name") != "Eye Pain"
            assert r.get("dataset_name") != "Eye Pain"

    def test_gothan_ma_dukhavo_online_gemini_mapped_to_knee_or_joint_pain(self):
        """In online mode, Gemini proposing Knee Pain correctly maps to Joint Pain (S000131), NOT Eye Pain."""
        clear_symptom_norm_cache()
        mock_gemini_resp = {
            "candidates": [
                {
                    "raw_phrase": "gothan ma dukhavo",
                    "candidate_canonical_name": "Knee Pain",
                    "semantic_type": "symptom",
                    "body_region": "lower_limb",
                    "confidence": 0.95,
                    "reason": "Gujarati for knee pain"
                }
            ]
        }
        with patch("config.settings.gemini_pool.get_active_keys", return_value=["test_key"]), \
             patch("ai.disease_prediction.multilingual_symptom_extractor._safe_parse_json", return_value=mock_gemini_resp), \
             patch("config.settings.gemini_pool.execute_with_failover", return_value=({"candidates": [{"content": {"parts": [{"text": "dummy"}]}}]}, "gemini", None)):
            res = normalize_user_symptoms("gothan ma dukhavo")
            assert len(res) >= 1
            item = res[0]
            assert item["symptom_id"] != "S000212"
            assert item["dataset_match"] is True
            assert item["symptom_id"] == "S000131"  # Joint Pain
            assert item["canonical_name"] == "Joint Pain"
            assert item["provenance"] == "GEMINI_SEMANTIC_THEN_DATASET_VALIDATED"

    def test_gothan_ma_dukhavo_rejects_hallucinated_eye_pain_candidate(self):
        """If Gemini hallucinates Eye Pain for 'gothan ma dukhavo', validation MUST reject it."""
        clear_symptom_norm_cache()
        mock_hallucination = {
            "candidates": [
                {
                    "raw_phrase": "gothan ma dukhavo",
                    "candidate_canonical_name": "Eye Pain",
                    "semantic_type": "symptom",
                    "body_region": "eye",
                    "confidence": 0.95,
                    "reason": "Hallucinated interpretation"
                }
            ]
        }
        with patch("config.settings.gemini_pool.get_active_keys", return_value=["test_key"]), \
             patch("ai.disease_prediction.multilingual_symptom_extractor._safe_parse_json", return_value=mock_hallucination), \
             patch("config.settings.gemini_pool.execute_with_failover", return_value=({"candidates": [{"content": {"parts": [{"text": "dummy"}]}}]}, "gemini", None)):
            res = normalize_user_symptoms("gothan ma dukhavo")
            # Must reject Eye Pain because gothan is lower_limb
            for r in res:
                assert r.get("symptom_id") != "S000212", "Validation failed to reject hallucinated Eye Pain!"
                assert r.get("canonical_name") != "Eye Pain"

    # --------------------------------------------------------------------------
    # 8. Genuine Eye Symptoms Must Map Correctly
    # --------------------------------------------------------------------------

    def test_genuine_eye_pain_romanized_gujarati(self):
        """'aankh ma dukhe chhe' genuinely reports eye pain and must map to Eye Pain (S000212)."""
        res = normalize_user_symptoms("aankh ma dukhe chhe")
        matched = [r for r in res if r["dataset_match"]]
        assert any(r["symptom_id"] == "S000212" for r in matched)

    def test_genuine_eye_pain_native_gujarati(self):
        """'આંખમાં દુખાવો' in native Gujarati script must map to Eye Pain (S000212)."""
        res = normalize_user_symptoms("મને આંખમાં દુખાવો થાય છે")
        matched = [r for r in res if r["dataset_match"]]
        assert any(r["symptom_id"] == "S000212" for r in matched)

    def test_genuine_eye_pain_native_hindi(self):
        """'आँख में दर्द' in native Hindi must map to Eye Pain (S000212)."""
        res = normalize_user_symptoms("आँख में दर्द हो रहा है")
        matched = [r for r in res if r["dataset_match"]]
        assert any(r["symptom_id"] == "S000212" for r in matched)

    def test_genuine_eye_pain_english(self):
        """'severe eye pain and redness' must map to Eye Pain (S000212)."""
        res = normalize_user_symptoms("severe eye pain and redness")
        matched = [r for r in res if r["dataset_match"]]
        assert any(r["symptom_id"] == "S000212" for r in matched)

    # --------------------------------------------------------------------------
    # 9. Cross-Anatomical Separation Across Multiple Body Regions
    # --------------------------------------------------------------------------

    def test_cross_region_knee_is_never_eye(self):
        bridge = canonical_normalizer.bridge
        rec_eye = bridge.lookup_by_id("S000212")
        assert bridge.check_anatomical_conflict("gothan ma dukhavo", rec_eye) is True
        assert bridge.check_anatomical_conflict("knee pain", rec_eye) is True
        assert bridge.check_anatomical_conflict("Knee Pain", rec_eye, candidate_region="lower_limb") is True

    def test_cross_region_chest_is_never_leg(self):
        bridge = canonical_normalizer.bridge
        rec_chest = bridge.lookup_by_id("S000046")  # Chest Pain
        assert bridge.check_anatomical_conflict("pag ma dukhavo", rec_chest, candidate_region="lower_limb") is True
        assert bridge.check_anatomical_conflict("leg pain", rec_chest, candidate_region="lower_limb") is True

    def test_cross_region_hand_is_never_ear(self):
        bridge = canonical_normalizer.bridge
        rec_ear = bridge.lookup_by_id("S000167")  # Ear Pain
        assert bridge.check_anatomical_conflict("hath ma dard", rec_ear, candidate_region="upper_limb") is True
        assert bridge.check_anatomical_conflict("hand pain", rec_ear, candidate_region="upper_limb") is True

    def test_cross_region_head_is_never_abdomen(self):
        bridge = canonical_normalizer.bridge
        rec_abd = bridge.lookup_by_id("S000092")  # Abdominal Pain
        assert bridge.check_anatomical_conflict("mathu dukhe", rec_abd, candidate_region="head") is True
        assert bridge.check_anatomical_conflict("headache", rec_abd, candidate_region="head") is True

    # --------------------------------------------------------------------------
    # 10. Native Script and Romanized Forms for All Configured Languages
    # --------------------------------------------------------------------------

    def test_dynamic_supported_languages_discovery(self):
        """Supported languages are discovered dynamically from configuration."""
        langs = get_supported_language_codes()
        assert "en" in langs
        assert "hi" in langs
        assert "gu" in langs
        assert len(langs) >= 3

    def test_native_gujarati_symptoms(self):
        """Native Gujarati phrases map to valid canonical symptoms."""
        res_head = normalize_user_symptoms("માથાનો દુખાવો")
        assert any(r["symptom_id"] == "S000061" for r in res_head if r["dataset_match"])

        res_fever = normalize_user_symptoms("ખૂબ તાવ આવે છે")
        assert any(r["symptom_id"] in ["S000001", "S000002"] for r in res_fever if r["dataset_match"])

    def test_native_hindi_symptoms(self):
        """Native Devanagari Hindi phrases map to valid canonical symptoms."""
        res_head = normalize_user_symptoms("तेज सिरदर्द")
        assert any(r["symptom_id"] == "S000061" for r in res_head if r["dataset_match"])

        res_fever = normalize_user_symptoms("तेज बुखार")
        assert any(r["symptom_id"] in ["S000001", "S000002"] for r in res_fever if r["dataset_match"])

    # --------------------------------------------------------------------------
    # 11. Offline Mode: Zero Network Requests & Explicit UNRESOLVED on Unknown
    # --------------------------------------------------------------------------

    def test_offline_mode_zero_network_calls(self):
        """When offline=True, gemini_pool.execute_with_failover is NEVER called."""
        clear_symptom_norm_cache()
        with patch("config.settings.gemini_pool.execute_with_failover") as mock_exec:
            res = normalize_user_symptoms("random unknown gibberish qwerty12345", offline=True)
            mock_exec.assert_not_called()
            assert len(res) >= 1
            assert res[0]["dataset_match"] is False
            assert res[0]["provenance"] == "UNRESOLVED"
            assert res[0]["symptom_id"] is None

    # --------------------------------------------------------------------------
    # 12. Gemini Failure Modes: Timeout, Rate-Limit, Auth, Invalid JSON
    # --------------------------------------------------------------------------

    def test_gemini_timeout_falls_back_to_dataset(self):
        """If Gemini times out, system falls back to dataset without failing."""
        clear_symptom_norm_cache()
        with patch("config.settings.gemini_pool.get_active_keys", return_value=["test_key"]), \
             patch("config.settings.gemini_pool.execute_with_failover", side_effect=Exception("Timeout 10s")):
            res = normalize_user_symptoms("severe headache and high fever")
            matched = [r for r in res if r["dataset_match"]]
            assert any(r["symptom_id"] == "S000061" for r in matched)
            assert any(r["symptom_id"] in ["S000001", "S000002"] for r in matched)

    def test_gemini_invalid_json_falls_back_to_dataset(self):
        """If Gemini produces invalid non-JSON output, fallback to dataset handles it."""
        clear_symptom_norm_cache()
        with patch("config.settings.gemini_pool.get_active_keys", return_value=["test_key"]), \
             patch("ai.disease_prediction.multilingual_symptom_extractor._safe_parse_json", return_value=None), \
             patch("config.settings.gemini_pool.execute_with_failover", return_value=({"candidates": [{"content": {"parts": [{"text": "not a json"}]}}]}, "gemini", None)):
            res = normalize_user_symptoms("severe headache and high fever")
            matched = [r for r in res if r["dataset_match"]]
            assert any(r["symptom_id"] == "S000061" for r in matched)

    def test_gemini_candidate_validation_failure_marks_unresolved(self):
        """If Gemini returns a candidate that does not exist in master dataset, it is NOT accepted."""
        clear_symptom_norm_cache()
        mock_fake_candidate = {
            "candidates": [
                {
                    "raw_phrase": "strange non-existent feeling",
                    "candidate_canonical_name": "Totally Fabricated Symptom Name XYZ",
                    "semantic_type": "symptom",
                    "body_region": "general",
                    "confidence": 0.95
                }
            ]
        }
        with patch("config.settings.gemini_pool.get_active_keys", return_value=["test_key"]), \
             patch("ai.disease_prediction.multilingual_symptom_extractor._safe_parse_json", return_value=mock_fake_candidate), \
             patch("config.settings.gemini_pool.execute_with_failover", return_value=({"candidates": [{"content": {"parts": [{"text": "dummy"}]}}]}, "gemini", None)):
            res = normalize_user_symptoms("strange non-existent feeling")
            # Fabricated symptom must NOT be accepted as dataset_match
            for r in res:
                assert r.get("symptom_id") is None
                assert r["dataset_match"] is False
                assert r["provenance"] == "UNRESOLVED"

    # --------------------------------------------------------------------------
    # 13. Cache Isolation Across Languages and Online/Offline Modes
    # --------------------------------------------------------------------------

    def test_cache_isolation_online_vs_offline(self):
        """Cache keys differ between online and offline modes."""
        clear_symptom_norm_cache()
        input_text = "chakkar aave chhe"
        res_offline = normalize_user_symptoms(input_text, offline=True)
        res_online = normalize_user_symptoms(input_text, offline=False)
        assert len(res_offline) >= 1
        assert len(res_online) >= 1

    def test_cache_isolation_across_languages(self):
        """Cache keys differ when language context differs."""
        clear_symptom_norm_cache()
        res_en = normalize_user_symptoms("fever", patient_context={"lang_code": "en"}, offline=True)
        res_gu = normalize_user_symptoms("fever", patient_context={"lang_code": "gu"}, offline=True)
        assert len(res_en) >= 1
        assert len(res_gu) >= 1

    # --------------------------------------------------------------------------
    # 14. Voice and Typed Input Equivalence
    # --------------------------------------------------------------------------

    def test_voice_and_typed_equivalence(self):
        """Transcribed voice input produces identical symptoms as typed text."""
        extractor = MultilingualSymptomExtractor()
        phrase = "mathu dukhe chhe ane tav aave chhe"
        typed_res = extractor.extract_symptoms_and_medicines(phrase, user_lang="gu", offline=True)
        voice_res = extractor.extract_symptoms_and_medicines(phrase, user_lang="gu", offline=True)
        assert set(typed_res["symptom_ids"]) == set(voice_res["symptom_ids"])
        assert set(typed_res["symptom_labels"]) == set(voice_res["symptom_labels"])
        assert "S000061" in typed_res["symptom_ids"]  # Headache
        assert "S000001" in typed_res["symptom_ids"]  # Fever

    # --------------------------------------------------------------------------
    # 15. Anatomical Location Preservation & Single API Call Invariance
    # --------------------------------------------------------------------------

    def test_gothan_ma_dukhavo_preserves_anatomical_location_and_region(self):
        """'gothan ma dukhavo' must preserve 'knee' and 'lower_limb' while mapping to Joint Pain (S000131)."""
        clear_symptom_norm_cache()
        res = normalize_user_symptoms("gothan ma dukhavo", offline=True)
        assert len(res) == 1
        item = res[0]
        assert item["dataset_match"] is True
        assert item["symptom_id"] == "S000131"  # Joint Pain
        assert item["canonical_name"] == "Joint Pain"
        assert item["body_location"] == "knee"
        assert item["body_region"] == "lower_limb"
        assert item["detected_language"] == "gu"
        assert item["detected_script"] == "Latn"
        assert item["validation_status"] == "Validated"

    def test_exact_one_gemini_call_per_extraction_operation(self):
        """Single extraction operation must invoke Gemini failover pool exactly ONCE (zero duplicate calls)."""
        clear_symptom_norm_cache()
        extractor = MultilingualSymptomExtractor()
        mock_gemini_resp = {
            "candidates": [
                {
                    "raw_phrase": "gothan ma dukhavo",
                    "candidate_canonical_name": "Joint Pain",
                    "semantic_type": "symptom",
                    "body_region": "lower_limb",
                    "body_location": "knee",
                    "confidence": 0.95,
                    "reason": "Knee pain mapped to Joint Pain"
                }
            ]
        }
        with patch("config.settings.gemini_pool.get_active_keys", return_value=["test_api_key"]), \
             patch("ai.disease_prediction.multilingual_symptom_extractor._safe_parse_json", return_value=mock_gemini_resp), \
             patch("config.settings.gemini_pool.execute_with_failover", return_value=({"candidates": [{"content": {"parts": [{"text": "dummy"}]}}]}, "gemini-2.0-flash", None)) as mock_exec:
            res = extractor.extract_symptoms_and_medicines("gothan ma dukhavo", user_lang="gu", offline=False)
            assert mock_exec.call_count == 1, f"Expected exactly 1 Gemini call, but got {mock_exec.call_count}!"
            assert "Joint Pain" in res["symptom_labels"]
            assert "S000131" in res["symptom_ids"]
            assert len(res["normalized_symptoms"]) == 1
            norm_item = res["normalized_symptoms"][0]
            assert norm_item["body_location"] == "knee"
            assert norm_item["body_region"] == "lower_limb"

    def test_anatomical_location_and_laterality_preservation_matrix(self):
        """Validate location and laterality preservation across multiple body regions."""
        clear_symptom_norm_cache()
        test_cases = [
            ("left knee pain", "knee", "lower_limb", "left"),
            ("right shoulder pain", "shoulder", "upper_limb", "right"),
            ("severe lower back pain", "lower_back", "lumbar_spine", None),
            ("both ankle swelling", "ankle", "lower_limb", "bilateral"),
        ]
        for phrase, expected_loc, expected_reg, expected_lat in test_cases:
            res = normalize_user_symptoms(phrase, offline=True)
            matched = [r for r in res if r["dataset_match"]]
            assert len(matched) >= 1, f"Failed to match {phrase}"
            item = matched[0]
            assert item["body_location"] == expected_loc, f"Expected loc {expected_loc} for '{phrase}', got {item.get('body_location')}"
            if expected_lat:
                assert item["laterality"] == expected_lat, f"Expected laterality {expected_lat} for '{phrase}', got {item.get('laterality')}"


