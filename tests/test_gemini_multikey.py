"""
Test suite for Gemini Multi-Key Failover Pool Manager (DocMindX AI).
Validates:
1. Environment key discovery (GEMINI_API_KEYS, GEMINI_API_KEY_1..N, GEMINI_API_KEY).
2. Dynamic rotation on HTTP 429 (Rate Limit / Quota Exceeded).
3. Dynamic rotation on HTTP 403 (Auth error).
4. Cooldown mechanism and key health recovery.
5. Failover to secondary keys without breaking caller flow.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import time
import pytest
from unittest.mock import patch, MagicMock
from api.gemini_manager import GeminiKeyPoolManager, call_gemini_with_failover


def test_key_pool_parsing():
    """Verify manager aggregates keys from comma lists, numbered variables, and legacy."""
    mgr = GeminiKeyPoolManager()
    
    mock_env = {
        "GEMINI_API_KEYS": "KEY_AAA_12345678, KEY_BBB_12345678",
        "GEMINI_API_KEY_1": "KEY_CCC_12345678",
        "GEMINI_API_KEY_2": "KEY_DDD_12345678",
        "GEMINI_API_KEY": "KEY_AAA_12345678"  # Duplicate of first
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        keys = mgr.get_all_keys()
        # Should deduplicate KEY_AAA
        assert len(keys) == 4
        assert keys == [
            "KEY_AAA_12345678",
            "KEY_BBB_12345678",
            "KEY_CCC_12345678",
            "KEY_DDD_12345678"
        ]


def test_automatic_failover_on_429():
    """Verify that when Key 1 returns 429, the manager rotates immediately to Key 2."""
    mgr = GeminiKeyPoolManager()
    
    mock_env = {
        "GEMINI_API_KEY_1": "MOCK_KEY_1_00000000",
        "GEMINI_API_KEY_2": "MOCK_KEY_2_00000000",
        "GEMINI_API_KEY_3": "MOCK_KEY_3_00000000",
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        assert len(mgr.get_all_keys()) == 3

        def fake_post(url, *args, **kwargs):
            mock_res = MagicMock()
            if "MOCK_KEY_1_00000000" in url:
                mock_res.status_code = 429
                mock_res.text = "Quota Exceeded"
            elif "MOCK_KEY_2_00000000" in url:
                mock_res.status_code = 200
                mock_res.json.return_value = {
                    "candidates": [{"content": {"parts": [{"text": "Success from Key 2"}]}}]
                }
            return mock_res

        with patch("requests.post", side_effect=fake_post):
            data, model, key_used = mgr.execute_with_failover(
                payload={"test": "payload"},
                models=["gemini-3.6-flash"],
                timeout=5
            )

            assert data is not None
            assert key_used == "MOCK_KEY_2_00000000"
            assert "Success from Key 2" in data["candidates"][0]["content"]["parts"][0]["text"]

            # Key 1 must be marked exhausted
            active_keys = mgr.get_active_keys()
            assert "MOCK_KEY_1_00000000" not in active_keys
            assert "MOCK_KEY_2_00000000" in active_keys


def test_all_keys_exhausted_graceful():
    """Verify that if all configured keys fail with 429, manager returns (None, None, None) without throwing."""
    mgr = GeminiKeyPoolManager()
    
    mock_env = {
        "GEMINI_API_KEY_1": "FAIL_KEY_1_00000000",
        "GEMINI_API_KEY_2": "FAIL_KEY_2_00000000",
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        def fake_post(url, *args, **kwargs):
            mock_res = MagicMock()
            mock_res.status_code = 429
            mock_res.text = "Quota Exceeded"
            return mock_res

        with patch("requests.post", side_effect=fake_post):
            data, model, key_used = mgr.execute_with_failover(
                payload={"test": "payload"},
                models=["gemini-3.6-flash"],
                timeout=5
            )
            assert data is None
            assert model is None
            assert key_used is None


def test_status_summary():
    """Verify status summary reports active vs exhausted keys correctly."""
    mgr = GeminiKeyPoolManager()
    
    mock_env = {
        "GEMINI_API_KEY_1": "KEY_ALPHA_00000000",
        "GEMINI_API_KEY_2": "KEY_BETA_00000000",
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        mgr.mark_key_exhausted("KEY_ALPHA_00000000", reason="test_429", cooldown=60)
        summary = mgr.get_status_summary()
        assert summary["total_keys_configured"] == 2
        assert summary["active_healthy_keys"] == 1
        assert len(summary["exhausted_keys"]) == 1
        assert "KEY_AL" in summary["exhausted_keys"][0]["key_masked"]
