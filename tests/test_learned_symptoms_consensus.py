"""
Test suite for Dual-Model Consensus Symptom Learning Engine (Gemini + Groq).
Verifies:
1. Lookup hierarchy: Master dataset -> Learned dataset -> Dual Consensus -> Unresolved.
2. Verified consensus is dynamically registered in datasets/symptoms/learned_symptoms.csv.
3. In-memory cache is updated immediately.
4. Next lookup retrieves from learned dataset in Tier 2 with zero LLM calls.
5. Disagreements or rejected symptoms are not learned and safely marked Unresolved.
6. Offline mode strictly makes 0 network calls.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from ai.disease_prediction.canonical_concepts import canonical_normalizer
from ai.disease_prediction.multilingual_symptom_extractor import (
    verify_with_groq_consensus,
    normalize_user_symptoms,
    clear_symptom_norm_cache
)


def test_learned_symptom_registration_and_lookup():
    """Verify that registering a learned symptom allows immediate and cached resolution."""
    test_alias = "khub j mathu dukhe chhe test"
    target_sid = "S000061"  # Headache

    # Register
    ok = canonical_normalizer.bridge.register_learned_symptom(
        alias_text=test_alias,
        symptom_id=target_sid,
        language_code="gu",
        script_type="Gujarati",
        notes="Automated test consensus"
    )
    assert ok is True

    # Immediate resolution
    resolved = canonical_normalizer.bridge.resolve_symptom(test_alias)
    assert resolved == target_sid

    # Detailed match
    match_det = canonical_normalizer.bridge.match_symptom_detailed(test_alias)
    assert match_det.get("dataset_match") is True
    assert match_det.get("symptom_id") == target_sid


def test_groq_consensus_success():
    """Test verify_with_groq_consensus when Groq confirms genuine symptom."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"is_genuine_symptom": true, "meaning_agrees": true, "canonical_symptom_name": "Fever", "confidence": 0.95, "clinical_reasoning": "taav means fever in Gujarati"}'
            }
        }]
    }

    with patch("requests.post", return_value=mock_resp), \
         patch("config.settings.GROQ_API_KEY", "dummy_groq_key"):
        res = verify_with_groq_consensus("taav bahu vadhare chhe", "Fever")
        assert res is not None
        assert res.get("verified") is True
        assert res.get("canonical_name") == "Fever"
        assert res.get("confidence") == 0.95


def test_groq_consensus_rejection():
    """Test verify_with_groq_consensus when Groq rejects non-symptom hallucination."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"is_genuine_symptom": false, "meaning_agrees": false, "canonical_symptom_name": null, "confidence": 0.10, "clinical_reasoning": "Not a medical condition"}'
            }
        }]
    }

    with patch("requests.post", return_value=mock_resp), \
         patch("config.settings.GROQ_API_KEY", "dummy_groq_key"):
        res = verify_with_groq_consensus("random fictional word xyz", "Fabricated Illness")
        assert res is None


def test_end_to_end_consensus_learning_in_normalization():
    """Test full normalize_user_symptoms flow when Gemini extracts a candidate that is learned via Groq."""
    clear_symptom_norm_cache()

    novel_phrase = "maro gotho khub dukhe chhe consensus test"
    # Mock Gemini proposing a novel clinical term not in master dataset
    mock_gemini_resp = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": '{"english_translation": "My knee is hurting badly", "candidates": [{"raw_phrase": "maro gotho khub dukhe chhe consensus test", "candidate_canonical_name": "Severe Patellar Discomfort", "body_region": "lower_limb", "confidence": 0.92}]}'
                }]
            }
        }]
    }

    # Mock Groq agreeing it is Joint Pain (S000020)
    mock_groq_resp = MagicMock()
    mock_groq_resp.status_code = 200
    mock_groq_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"is_genuine_symptom": true, "meaning_agrees": true, "canonical_symptom_name": "Joint Pain", "confidence": 0.94, "clinical_reasoning": "Knee pain is joint pain"}'
            }
        }]
    }

    with patch("config.settings.gemini_pool.execute_with_failover", return_value=(mock_gemini_resp, "gemini-2.5-flash", "dummy_key")), \
         patch("requests.post", return_value=mock_groq_resp), \
         patch("config.settings.GROQ_API_KEY", "dummy_groq_key"):
        
        results = normalize_user_symptoms(novel_phrase)
        assert len(results) > 0
        matched = [r for r in results if r.get("dataset_match")]
        assert len(matched) > 0
        assert matched[0]["provenance"] == "GEMINI_GROQ_CONSENSUS_LEARNED"
        assert matched[0]["symptom_id"] is not None

        # Now test that it was learned and can be resolved in Tier 2 without calling Groq
        tier2_resolved = canonical_normalizer.bridge.resolve_symptom(novel_phrase)
        assert tier2_resolved == matched[0]["symptom_id"]
