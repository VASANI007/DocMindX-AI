"""
DocMindX AI — Anti-Hardcoding Repository Audit Test Suite
Ensures that NO production code contains disease-specific hardcoded branching
(such as if 'sciatica' in ..., if disease == 'Sciatica', or disease-name-based
exercise/dosage/injection/topical decisions).

Distinguishes production decision logic from legitimate data mappings, test fixtures,
and UI translation strings.
"""
import os
import re
import pytest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTION_DIRS = [
    os.path.join(WORKSPACE_ROOT, "ai"),
    os.path.join(WORKSPACE_ROOT, "api"),
    os.path.join(WORKSPACE_ROOT, "config"),
]
PRODUCTION_FILES = [
    os.path.join(WORKSPACE_ROOT, "app.py")
]


def _get_production_py_files():
    py_files = list(PRODUCTION_FILES)
    for pdir in PRODUCTION_DIRS:
        for root, dirs, files in os.walk(pdir):
            if "__pycache__" in root or ".pytest_cache" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))
    return py_files


class TestAntiHardcodingAudit:
    """Automated AST/regex audit enforcing disease-agnostic clinical architecture."""

    def test_no_direct_sciatica_conditional_in_production(self):
        """
        No production code should ever have `if 'sciatica'` or `if disease == 'Sciatica'`
        as a clinical decision trigger.
        """
        forbidden_patterns = [
            re.compile(r'if\s+["\']sciatica["\']\s+in', re.IGNORECASE),
            re.compile(r'if\s+.*\b(disease|condition)\b\s*==\s*["\']sciatica["\']', re.IGNORECASE),
            re.compile(r'elif\s+["\']sciatica["\']\s+in', re.IGNORECASE),
            re.compile(r'elif\s+.*\b(disease|condition)\b\s*==\s*["\']sciatica["\']', re.IGNORECASE),
            re.compile(r'is_sciatica\s*=', re.IGNORECASE),
        ]

        violations = []
        for file_path in _get_production_py_files():
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for pattern in forbidden_patterns:
                matches = pattern.findall(content)
                if matches:
                    rel_path = os.path.relpath(file_path, WORKSPACE_ROOT)
                    violations.append(f"{rel_path}: matched pattern '{pattern.pattern}'")

        assert len(violations) == 0, f"Found prohibited disease-name hardcoding in production:\n" + "\n".join(violations)

    def test_no_disease_specific_yoga_decision_branches(self):
        """
        Yoga / exercise selection must NOT use disease-name conditionals like
        if cond == 'Asthma' or if 'gerd' in cond_lower.
        It must evaluate clinical attributes (spinal_extension, movement_type, target_body_region).
        """
        care_rec_path = os.path.join(WORKSPACE_ROOT, "ai", "utils", "care_recommendations.py")
        with open(care_rec_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        # Prohibited: disease-specific if-branches in yoga engine
        bad_patterns = [
            "if is_sciatica:",
            "elif is_sciatica:",
            "elif any(r in cond_lower or r in sym_lower for r in [\"asthma\"",
            "elif any(d in cond_lower or d in sym_lower for d in [\"acidity\"",
        ]
        for pat in bad_patterns:
            assert pat not in code, f"Found disease-specific yoga branch in care_recommendations.py: '{pat}'"

    def test_no_disease_specific_topical_block_branches(self):
        """
        condition_supports_topical must not check individual disease names like 'malaria' or 'dengue'.
        It must evaluate clinical presentation attributes (is_systemic_presentation vs is_localized_superficial).
        """
        care_rec_path = os.path.join(WORKSPACE_ROOT, "ai", "utils", "care_recommendations.py")
        with open(care_rec_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        func_match = re.search(r'def condition_supports_topical\([^)]*\)[^:]*:.*?(?=\ndef\s|\Z)', code, re.DOTALL)
        assert func_match is not None, "condition_supports_topical function not found"
        func_body = func_match.group(0)

        # Ensure no disease names are hardcoded in the topical check
        for dis in ["malaria", "dengue", "typhoid", "sciatica", "covid", "pneumonia"]:
            assert f'"{dis}"' not in func_body.lower() and f"'{dis}'" not in func_body.lower(), \
                f"condition_supports_topical contains hardcoded disease name: '{dis}'"

    def test_no_static_slices_in_ui_render_layer(self):
        """
        app.py must not contain artificial result-count capping slices.
        """
        app_path = os.path.join(WORKSPACE_ROOT, "app.py")
        with open(app_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        prohibited_slices = [
            'conditions_list = t_res.get("ranked_conditions", [])[:3]',
            'for rc in ranked_conds[:3]:',
            'for y in yoga[:3]:',
            'for y in ins["yoga"][:4]',
            'for l in lifestyle[:3]:',
            'for l in ins["lifestyle"][:3]',
            'for p in prec[:2]:',
            'for p in ins["precautions"][:3]',
            'for m in medicines[:5]:',
            'for f in findings[:6]:',
        ]
        for s in prohibited_slices:
            assert s not in code, f"Found artificial slice in app.py: '{s}'"

    def test_no_sciatica_in_attribute_extractor(self):
        """
        _extract_clinical_presentation_attributes must evaluate symptom/concept evidence
        and NOT include the condition name 'sciatica'.
        """
        care_rec_path = os.path.join(WORKSPACE_ROOT, "ai", "utils", "care_recommendations.py")
        with open(care_rec_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        func_match = re.search(r'def _extract_clinical_presentation_attributes\([^)]*\)[^:]*:.*?(?=\ndef\s|\Z)', code, re.DOTALL)
        assert func_match is not None, "_extract_clinical_presentation_attributes function not found"
        func_body = func_match.group(0)

        assert '"sciatica"' not in func_body.lower() and "'sciatica'" not in func_body.lower(), \
            "_extract_clinical_presentation_attributes contains disease-name keyword 'sciatica'"

    def test_no_arbitrary_chief_condition_score_boost(self):
        """
        predict.py must NOT contain arbitrary score inflations like `+ 20` or `max(match_pct, 60)`.
        """
        predict_path = os.path.join(WORKSPACE_ROOT, "ai", "disease_prediction", "predict.py")
        with open(predict_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        assert "+ 20" not in code, "Found arbitrary '+ 20' score boost in predict.py"
        assert "max(match_pct, 60)" not in code, "Found arbitrary 'max(match_pct, 60)' score boost in predict.py"

    def test_no_clinical_truncation_of_who_validation(self):
        """
        WHO ICD-11 validation must NOT be capped at [:3] in clinical_pipeline.py or predict.py.
        """
        for rel_path in ["ai/disease_prediction/predict.py", "ai/disease_prediction/clinical_pipeline.py"]:
            full_path = os.path.join(WORKSPACE_ROOT, rel_path)
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            assert "conditions[:3]" not in code, f"Found conditions[:3] cap in {rel_path}"
            assert "ranked_conditions[:3]" not in code, f"Found ranked_conditions[:3] cap in {rel_path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
