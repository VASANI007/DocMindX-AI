"""
DocMindX AI — Gemini Multi-API-Key Failover & Pool Management Engine.

Provides seamless, dynamic failover across multiple Google Gemini API keys:
- Loads 4-5+ Gemini API keys from .env via GEMINI_API_KEYS list or GEMINI_API_KEY_1..N
- Tracks key exhaustion / rate-limiting (HTTP 429 Quota Exceeded / HTTP 403 Forbidden)
- Automatically shifts to the next active key without interrupting clinical inference
- Provides transparent failover to Groq / local intelligence when all keys are exhausted
"""

import os
import re
import time
import json
import logging
import threading
from typing import List, Dict, Any, Optional, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

_logger = logging.getLogger("DocMindX.GeminiManager")

# Default model chain in priority order (fastest high-availability models first)
DEFAULT_GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]
COOLDOWN_SECONDS = 180  # 3-minute cooldown for rate-limited (429) keys


class GeminiKeyPoolManager:
    """
    Thread-safe manager for multiple Gemini API keys.
    Maintains active key list, health state, permanent denial state, and automatic rotation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._exhausted_keys: Dict[str, float] = {}  # key -> timestamp when cooldown ends
        self._permanently_disabled_keys: Dict[str, str] = {}  # key -> reason/error
        self._current_index = 0

    def get_all_keys(self) -> List[str]:
        """
        Loads and aggregates all Gemini API keys from environment variables:
        1. Comma/newline/semicolon-separated list: GEMINI_API_KEYS
        2. Numbered variables: GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
        3. Legacy single variable: GEMINI_API_KEY
        Returns deduplicated, non-empty list maintaining preference order.
        """
        keys: List[str] = []
        seen = set()

        def _add_key(k: str):
            if not k:
                return
            clean = k.strip().strip('"').strip("'").strip()
            if clean and len(clean) > 8 and clean not in seen:
                seen.add(clean)
                keys.append(clean)

        # 1. Check GEMINI_API_KEYS (list format: comma, semicolon, or newline separated)
        env_keys_list = os.getenv("GEMINI_API_KEYS", "")
        if env_keys_list:
            for part in re.split(r"[,;\n\s]+", env_keys_list):
                _add_key(part)

        # 2. Check numbered keys: GEMINI_API_KEY_1 to GEMINI_API_KEY_20
        for i in range(1, 21):
            num_key = os.getenv(f"GEMINI_API_KEY_{i}", "")
            if num_key:
                _add_key(num_key)

        # 3. Check legacy GEMINI_API_KEY
        legacy_key = os.getenv("GEMINI_API_KEY", "")
        if legacy_key:
            _add_key(legacy_key)

        return keys

    def get_active_keys(self) -> List[str]:
        """
        Returns keys that are currently healthy (not permanently disabled and cooldown has expired).
        If all healthy keys are on cooldown, returns them sorted by earliest cooldown expiry.
        """
        all_keys = self.get_all_keys()
        if not all_keys:
            return []

        now = time.time()
        with self._lock:
            # Clean up expired cooldowns
            self._exhausted_keys = {
                k: exp for k, exp in self._exhausted_keys.items() if exp > now
            }

            # Filter out permanently disabled keys completely
            non_disabled = [k for k in all_keys if k not in self._permanently_disabled_keys]
            if not non_disabled:
                _logger.error("[GeminiManager] All %d configured Gemini keys are permanently disabled.", len(all_keys))
                return []

            healthy = [k for k in non_disabled if k not in self._exhausted_keys]
            if healthy:
                return healthy

            # If all non-disabled keys are exhausted, sort by cooldown expiry (earliest first)
            _logger.warning("[GeminiManager] All %d active Gemini keys are on temporary cooldown. Trying earliest expiring key.", len(non_disabled))
            return sorted(non_disabled, key=lambda k: self._exhausted_keys.get(k, 0))

    def mark_key_exhausted(self, key: str, reason: str = "quota_exceeded", cooldown: float = COOLDOWN_SECONDS):
        """Marks a key as temporarily exhausted for the cooldown duration (transient 429)."""
        with self._lock:
            now = time.time()
            self._exhausted_keys[key] = now + cooldown
            masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
            _logger.warning(
                "[GeminiManager] Key %s marked temporarily exhausted (%s) for %ds. Cooldown ends at %.0f",
                masked, reason, cooldown, self._exhausted_keys[key]
            )

    def mark_key_permanently_disabled(self, key: str, reason: str = "auth_denied"):
        """Marks a key as permanently disabled for this process lifetime (403 denied / invalid project)."""
        with self._lock:
            self._permanently_disabled_keys[key] = reason
            if key in self._exhausted_keys:
                del self._exhausted_keys[key]
            masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
            _logger.error(
                "[GeminiManager] KEY PERMANENTLY DISABLED (%s): %s. Key has been retired from active rotation.",
                masked, reason
            )

    def mark_key_success(self, key: str):
        """Clears any exhaustion record for a successfully working key."""
        with self._lock:
            if key in self._exhausted_keys:
                del self._exhausted_keys[key]

    def get_primary_key(self) -> str:
        """Returns the primary active key, or empty string if none configured."""
        active = self.get_active_keys()
        return active[0] if active else ""

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns diagnostic status of the key pool."""
        all_keys = self.get_all_keys()
        now = time.time()
        with self._lock:
            active = [k for k in all_keys if k not in self._permanently_disabled_keys and self._exhausted_keys.get(k, 0) <= now]
            exhausted = [
                {
                    "key_masked": k[:6] + "..." + k[-4:] if len(k) > 10 else "***",
                    "cooldown_remaining_sec": round(self._exhausted_keys[k] - now, 1)
                }
                for k in all_keys if k not in self._permanently_disabled_keys and self._exhausted_keys.get(k, 0) > now
            ]
            disabled = [
                {
                    "key_masked": k[:6] + "..." + k[-4:] if len(k) > 10 else "***",
                    "reason": reason
                }
                for k, reason in self._permanently_disabled_keys.items()
            ]
        return {
            "total_keys_configured": len(all_keys),
            "active_healthy_keys": len(active),
            "exhausted_keys": exhausted,
            "permanently_disabled_keys": disabled
        }

    def execute_with_failover(
        self,
        payload: Dict[str, Any],
        models: Optional[List[str]] = None,
        timeout: int = 12
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
        """
        Executes a Gemini API request with automatic multi-key failover.
        - Rate limits (429) put the key on short cooldown and shift to next key.
        - Permanent auth errors (403/401/400 project denied) permanently disable the key.
        - Returns: (response_json, model_used, key_used) or (None, None, None) on complete exhaustion.
        """
        keys = self.get_active_keys()
        if not keys:
            _logger.error("[GeminiManager] No active Gemini API keys available in pool.")
            return None, None, None

        models_to_try = models or DEFAULT_GEMINI_MODELS
        last_error = ""

        for key_idx, key in enumerate(keys):
            masked_key = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
            headers = {"Content-Type": "application/json"}

            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                try:
                    res = requests.post(url, headers=headers, json=payload, timeout=timeout)
                    if res.status_code == 200:
                        self.mark_key_success(key)
                        _logger.info("[GeminiManager] SUCCESS with key %d/%d (%s) on model %s", key_idx + 1, len(keys), masked_key, model)
                        return res.json(), model, key

                    elif res.status_code == 429:
                        # Rate limit / Quota Exceeded -> Mark key on temporary cooldown and shift to next key immediately
                        last_error = f"HTTP 429 Quota Exceeded on {masked_key}"
                        _logger.warning("[GeminiManager] Key %d/%d (%s) hit 429 Quota Exceeded. Shifting to next key...", key_idx + 1, len(keys), masked_key)
                        self.mark_key_exhausted(key, reason="quota_exceeded", cooldown=COOLDOWN_SECONDS)
                        break  # Break out of models loop to immediately try the NEXT KEY

                    elif res.status_code in (400, 401, 403):
                        res_text = res.text.lower()
                        is_permanent = any(w in res_text for w in [
                            "denied access", "contact support", "permission_denied", "api_key_invalid",
                            "consumer_suspended", "billing_disabled", "project has been denied"
                        ]) or res.status_code in (401, 403)

                        if is_permanent:
                            last_error = f"HTTP {res.status_code} Permanent Auth Error on {masked_key}: {res.text[:120]}"
                            self.mark_key_permanently_disabled(key, reason=f"HTTP {res.status_code}: {res.text[:100]}")
                        else:
                            last_error = f"HTTP {res.status_code} on {masked_key}: {res.text[:120]}"
                            self.mark_key_exhausted(key, reason=f"HTTP_{res.status_code}", cooldown=600)
                        break  # Break out of models loop to immediately try NEXT KEY

                    elif res.status_code in (404, 503):
                        # Model unavailable/503 on this specific model -> Try next model in chain
                        _logger.debug("[GeminiManager] Model %s returned HTTP %d with key %s, trying next model...", model, res.status_code, masked_key)
                        continue

                    else:
                        _logger.warning("[GeminiManager] Key %s model %s returned HTTP %d: %s", masked_key, model, res.status_code, res.text[:120])
                        continue

                except requests.exceptions.Timeout:
                    _logger.warning("[GeminiManager] Timeout (%ds) on key %s model %s", timeout, masked_key, model)
                    continue
                except Exception as e:
                    _logger.warning("[GeminiManager] Request exception on key %s: %s", masked_key, e)
                    continue

        _logger.error("[GeminiManager] All %d Gemini keys exhausted or failed. Last error: %s", len(keys), last_error)
        return None, None, None


# Global singleton instance
gemini_pool = GeminiKeyPoolManager()


def get_gemini_api_keys() -> List[str]:
    """Convenience getter for all configured Gemini keys in pool."""
    return gemini_pool.get_all_keys()


def get_active_gemini_key() -> str:
    """Returns currently active primary key."""
    return gemini_pool.get_primary_key()


def call_gemini_with_failover(
    prompt: str,
    models: Optional[List[str]] = None,
    json_mode: bool = False,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2500,
    timeout: int = 12
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    High-level convenience function for text generation across the Gemini key pool.
    Returns: (text_output, model_used, key_used) or (None, None, None) if all keys failed.
    """
    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    data, model, key = gemini_pool.execute_with_failover(payload, models=models, timeout=timeout)
    if data:
        try:
            candidates = data.get("candidates", [])
            if candidates:
                text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return text_out, model, key
        except Exception as e:
            _logger.error("[GeminiManager] Error parsing candidate text: %s", e)
    return None, None, None
