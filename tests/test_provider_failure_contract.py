"""
DocMindX AI — Provider Failure Contract & Structured Status Test Suite
Verifies:
1. Standardized status contract across OpenFDA, DailyMed, and WHO ICD-11:
   - SUCCESS (HTTP 200 with data)
   - NO_RELEVANT_RESULT (HTTP 200 with empty result set)
   - RATE_LIMIT (HTTP 429)
   - AUTH_ERROR (HTTP 401 / 403)
   - TIMEOUT (requests.exceptions.Timeout)
   - NETWORK_ERROR (requests.exceptions.ConnectionError)
   - INVALID_RESPONSE (Corrupted JSON / Non-JSON response)
2. Graceful degradation: No fabricated badges, dosages, or synthetic clinical entities on failure.
3. WHO ICD-11 circuit breaker cooldown and fail-fast behavior.
4. WHO ICD-11 vs ICD-10 format validation (preventing mislabeling).
"""
import os
import sys
import pytest
import requests
from unittest.mock import MagicMock

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_ROOT)

import api.openfda as openfda
import api.dailymed as dailymed
import api.who_icd as who_icd


class TestOpenFDAFailureContract:

    @pytest.fixture(autouse=True)
    def bypass_cache(self, monkeypatch):
        """Ensure network tests test the API and failure contracts directly, bypassing local DB cache."""
        monkeypatch.setattr(openfda, "get_cached_medicine", lambda name: None)
        monkeypatch.setattr(openfda, "cache_medicine", lambda **kwargs: None)

    def test_openfda_success(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [{
                "openfda": {
                    "brand_name": ["Tylenol"],
                    "generic_name": ["Acetaminophen"],
                    "dosage_form": ["TABLET"],
                    "route": ["ORAL"],
                    "strength": ["500 mg"]
                },
                "dosage_and_administration": ["Take 1 tablet every 4-6 hours."]
            }]
        }
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = openfda.search_drug_openfda("acetaminophen")
        assert res["status"] == openfda.STATUS_SUCCESS
        assert res["is_live"] is True
        assert res["verification_status"] == "OPENFDA_VERIFIED"
        assert res["verified_label_dosage"] == "Take 1 tablet every 4-6 hours."
        assert "TABLET" in res["dosage_forms"]
        assert "ORAL" in res["routes"]

    def test_openfda_no_relevant_result(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.json.return_value = {"error": {"code": "NOT_FOUND", "message": "No matches found!"}}
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = openfda.search_drug_openfda("nonexistentdrug12345")
        assert res["status"] == openfda.STATUS_NO_RELEVANT_RESULT
        assert res["is_live"] is True
        assert res["verification_status"] == "NOT_FOUND"
        assert res["verified_label_dosage"] == ""

    def test_openfda_rate_limit(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = openfda.search_drug_openfda("ibuprofen")
        assert res["status"] == openfda.STATUS_RATE_LIMIT
        assert res["is_live"] is False
        assert res["verification_status"] == "CLINICAL_REFERENCE"
        assert res["verified_label_dosage"] == ""

    def test_openfda_auth_error(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = openfda.search_drug_openfda("ibuprofen")
        assert res["status"] == openfda.STATUS_AUTH_ERROR
        assert res["is_live"] is False
        assert res["verification_status"] == "CLINICAL_REFERENCE"

    def test_openfda_timeout(self, monkeypatch):
        def raise_timeout(*args, **kwargs):
            raise requests.exceptions.Timeout("Connection timed out after 5.0s")

        monkeypatch.setattr(requests, "get", raise_timeout)
        res = openfda.search_drug_openfda("aspirin")
        assert res["status"] == openfda.STATUS_TIMEOUT
        assert res["is_live"] is False
        assert res["verification_status"] == "CLINICAL_REFERENCE"
        assert res["verified_label_dosage"] == ""

    def test_openfda_network_error(self, monkeypatch):
        def raise_conn_err(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Failed to establish a new connection")

        monkeypatch.setattr(requests, "get", raise_conn_err)
        res = openfda.search_drug_openfda("aspirin")
        assert res["status"] == openfda.STATUS_NETWORK_ERROR
        assert res["is_live"] is False
        assert res["verification_status"] == "CLINICAL_REFERENCE"

    def test_openfda_invalid_json(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("Invalid JSON format")
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = openfda.search_drug_openfda("aspirin")
        assert res["status"] == openfda.STATUS_INVALID_RESPONSE
        assert res["is_live"] is False
        assert res["verification_status"] == "CLINICAL_REFERENCE"


class TestDailyMedFailureContract:

    def test_dailymed_success(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": [{
                "title": "Amoxicillin Capsule 500mg",
                "setid": "test-spl-setid-1234",
                "published_date": "Jan 01, 2024"
            }]
        }
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = dailymed.search_dailymed_spls("amoxicillin")
        assert res["status"] == dailymed.STATUS_SUCCESS
        assert res["is_live"] is True
        assert len(res["results"]) == 1
        assert res["results"][0]["setid"] == "test-spl-setid-1234"

    def test_dailymed_no_relevant_result(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": []}
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = dailymed.search_dailymed_spls("unknownsubstance999")
        assert res["status"] == dailymed.STATUS_NO_RELEVANT_RESULT
        assert res["is_live"] is True
        assert res["results"] == []

    def test_dailymed_rate_limit(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = dailymed.search_dailymed_spls("amoxicillin")
        assert res["status"] == dailymed.STATUS_RATE_LIMIT
        assert res["is_live"] is False

    def test_dailymed_timeout(self, monkeypatch):
        def raise_timeout(*args, **kwargs):
            raise requests.exceptions.Timeout("Read timed out")

        monkeypatch.setattr(requests, "get", raise_timeout)
        res = dailymed.search_dailymed_spls("amoxicillin")
        assert res["status"] == dailymed.STATUS_TIMEOUT
        assert res["is_live"] is False

    def test_dailymed_network_error(self, monkeypatch):
        def raise_conn_err(*args, **kwargs):
            raise requests.exceptions.ConnectionError("DNS lookup failed")

        monkeypatch.setattr(requests, "get", raise_conn_err)
        res = dailymed.search_dailymed_spls("amoxicillin")
        assert res["status"] == dailymed.STATUS_NETWORK_ERROR
        assert res["is_live"] is False

    def test_dailymed_invalid_json(self, monkeypatch):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("HTML received instead of JSON")
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = dailymed.search_dailymed_spls("amoxicillin")
        assert res["status"] == dailymed.STATUS_INVALID_RESPONSE
        assert res["is_live"] is False


class TestWHOICDFailureContract:

    def setup_method(self):
        # Reset state before each test
        who_icd._circuit_open_until = 0
        who_icd._cached_token = None
        who_icd._last_auth_failure_timestamp = 0

    def test_who_icd_success(self, monkeypatch):
        monkeypatch.setattr(who_icd, "get_who_access_token", lambda: "fake-jwt-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "destinationEntities": [{
                "theCode": "1A00",
                "title": "Cholera",
                "id": "http://id.who.int/icd/entity/1A00"
            }]
        }
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = who_icd.search_who_icd11_structured("cholera")
        assert res["status"] == who_icd.STATUS_SUCCESS
        assert res["is_live"] is True
        assert len(res["results"]) == 1
        rec = res["results"][0]
        assert rec["code"] == "1A00"
        assert rec["system"] == "ICD-11"

    def test_who_icd_rate_limit(self, monkeypatch):
        monkeypatch.setattr(who_icd, "get_who_access_token", lambda: "fake-jwt-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        monkeypatch.setattr(requests, "get", lambda *args, **kwargs: mock_resp)

        res = who_icd.search_who_icd11_structured("malaria")
        assert res["status"] == who_icd.STATUS_RATE_LIMIT
        assert res["is_live"] is False

    def test_who_icd_auth_error(self, monkeypatch):
        # Token failure triggers AUTH_ERROR
        monkeypatch.setattr(who_icd, "get_who_access_token", lambda: None)

        res = who_icd.search_who_icd11_structured("dengue")
        assert res["status"] == who_icd.STATUS_AUTH_ERROR
        assert res["is_live"] is False

    def test_who_icd_timeout_and_circuit_breaker(self, monkeypatch):
        monkeypatch.setattr(who_icd, "get_who_access_token", lambda: "fake-jwt-token")

        def raise_timeout(*args, **kwargs):
            raise requests.exceptions.Timeout("WHO Gateway Timeout")

        monkeypatch.setattr(requests, "get", raise_timeout)

        # First call encounters timeout and arms circuit breaker
        r1 = who_icd.search_who_icd11_structured("rabies")
        assert r1["status"] == who_icd.STATUS_TIMEOUT

        # Subsequent call fast-fails with CIRCUIT_OPEN without hitting network
        r2 = who_icd.search_who_icd11_structured("rabies")
        assert r2["status"] == who_icd.STATUS_CIRCUIT_OPEN
        assert r2["is_live"] is False

    def test_is_probable_icd10_code(self):
        """Verifies that ICD-10 format codes are correctly distinguished from ICD-11."""
        # ICD-10 codes (1 letter followed by 2 digits, optional decimal)
        assert who_icd.is_probable_icd10_code("A00") is True
        assert who_icd.is_probable_icd10_code("A00.0") is True
        assert who_icd.is_probable_icd10_code("B20") is True
        assert who_icd.is_probable_icd10_code("J45.9") is True
        assert who_icd.is_probable_icd10_code("M54.5") is True

        # ICD-11 codes (Start with a digit or have specific alphanumeric ICD-11 structures)
        assert who_icd.is_probable_icd10_code("1A00") is False
        assert who_icd.is_probable_icd10_code("1D20") is False
        assert who_icd.is_probable_icd10_code("CA40") is False
        assert who_icd.is_probable_icd10_code("") is False
        assert who_icd.is_probable_icd10_code("ICD-11") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
