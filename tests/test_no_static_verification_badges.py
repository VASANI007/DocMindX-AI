"""
DocMindX AI — Anti-Fabrication & Static Badge Elimination Audit Test Suite
Ensures that:
1. Zero static "DOCMINDX VERIFIED" strings exist in UI rendering logic.
2. Zero fabricated "Standard Formulation" strings exist in prescription or medicine rendering.
3. Verification badges are strictly derived dynamically from real API evidence provenance.
"""
import os
import re
import pytest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_no_static_docmindx_verified_in_codebase():
    """Verifies that no static 'DOCMINDX VERIFIED' badge string is hardcoded in rendering files."""
    audit_files = [
        os.path.join(WORKSPACE_ROOT, "app.py"),
        os.path.join(WORKSPACE_ROOT, "components", "diagnostic_results_view.py"),
        os.path.join(WORKSPACE_ROOT, "ai", "utils", "care_recommendations.py"),
        os.path.join(WORKSPACE_ROOT, "api", "openfda.py"),
        os.path.join(WORKSPACE_ROOT, "api", "dailymed.py"),
    ]

    violations = []
    for fpath in audit_files:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "DOCMINDX VERIFIED" in content:
                violations.append(f"{os.path.relpath(fpath, WORKSPACE_ROOT)} contains static 'DOCMINDX VERIFIED'")

    assert len(violations) == 0, f"Prohibited static verification badge found:\n" + "\n".join(violations)


def test_no_fabricated_standard_formulation():
    """Verifies that no fabricated 'Standard Formulation' string exists in components or API clients."""
    audit_files = [
        os.path.join(WORKSPACE_ROOT, "app.py"),
        os.path.join(WORKSPACE_ROOT, "components", "diagnostic_results_view.py"),
        os.path.join(WORKSPACE_ROOT, "api", "openfda.py"),
        os.path.join(WORKSPACE_ROOT, "api", "dailymed.py"),
    ]

    violations = []
    for fpath in audit_files:
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "Standard Formulation" in content:
                violations.append(f"{os.path.relpath(fpath, WORKSPACE_ROOT)} contains fabricated 'Standard Formulation'")

    assert len(violations) == 0, f"Prohibited 'Standard Formulation' found:\n" + "\n".join(violations)


def test_dynamic_verification_status_derivation(monkeypatch):
    """Verifies that get_medicine_gallery yields truthful dynamic verification status."""
    from ai.utils.care_recommendations import get_medicine_gallery

    # Case 1: Unverified / API returns no results
    monkeypatch.setattr("api.openfda.search_drug_openfda", lambda c: None)
    monkeypatch.setattr("api.dailymed.search_dailymed_drugnames", lambda c: [])

    unverified_entries = [
        {"name": "NonexistentMedicationXYZ", "form": "Syrup", "dosage": "10ml"}
    ]
    gallery_unver = get_medicine_gallery(
        unverified_entries,
        top_condition="General Malaise",
        symptoms=["Fatigue"]
    )
    assert len(gallery_unver) >= 1
    med_unver = gallery_unver[0]
    assert med_unver["verification_status"] in ["CLINICAL_REFERENCE", "UNVERIFIED"]
    assert "DOCMINDX VERIFIED" != med_unver["verification_status"]
    assert "OPENFDA_VERIFIED" != med_unver["verification_status"]

    # Case 2: Verified live API
    monkeypatch.setattr("api.openfda.search_drug_openfda", lambda c: {
        "is_live": True,
        "status": "SUCCESS",
        "brand_name": "Tylenol",
        "generic_name": "Acetaminophen"
    })
    gallery_ver = get_medicine_gallery(
        [{"name": "Paracetamol 500mg", "form": "Tablet", "dosage": "1 Tab"}],
        top_condition="Fever",
        symptoms=["Fever"]
    )
    assert len(gallery_ver) >= 1
    med_ver = gallery_ver[0]
    assert med_ver["verification_status"] == "OPENFDA_VERIFIED"
    assert "DOCMINDX VERIFIED" != med_ver["verification_status"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
