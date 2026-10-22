"""
Validation Suite: Category A - Demographics & Profile Edge Cases (40 Cases)
Tests TC-DEM-001 through TC-DEM-040 using clinical_manifest.py and ai.utils.validator
"""
import pytest
from ai.utils.validator import validate_demographics
from tests.validation_campaign.clinical_manifest import DEMOGRAPHICS_TEST_CASES

class TestDemographicsValidation:
    """Automated test execution for Demographics edge cases."""

    @pytest.mark.parametrize("case", DEMOGRAPHICS_TEST_CASES, ids=[c["id"] for c in DEMOGRAPHICS_TEST_CASES])
    def test_demographics_case(self, case):
        inp = case["input"]
        result = validate_demographics(
            age=inp.get("age"),
            gender=inp.get("gender"),
            state=inp.get("state"),
            height=inp.get("height"),
            weight=inp.get("weight"),
            blood_group=inp.get("blood_group")
        )

        expected_valid = case["valid"]
        assert result["valid"] == expected_valid, (
            f"Case {case['id']} ({case['name']}) expected valid={expected_valid}, "
            f"got valid={result['valid']} with errors: {result['errors']}"
        )

        if expected_valid:
            if "expected_age_group" in case:
                assert result["sanitized"]["age_group"] == case["expected_age_group"], (
                    f"Case {case['id']} expected age_group {case['expected_age_group']}, "
                    f"got {result['sanitized']['age_group']}"
                )
            if case.get("sanitized"):
                # Ensure dangerous tags stripped or escaped
                assert "<script>" not in result["sanitized"]["state"]
        else:
            if "error_field" in case:
                err_str = " ".join(result["errors"]).lower()
                target_field = case["error_field"].lower()
                assert target_field in err_str or target_field.replace("_", " ") in err_str, (
                    f"Case {case['id']} expected error on '{case['error_field']}', "
                    f"got errors: {result['errors']}"
                )
