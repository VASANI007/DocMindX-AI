"""
DocMindX AI — Comprehensive Dosage Form & Route Verification Suite
Verifies that all 16 dosage forms (Tablet, Capsule, Syrup, Suspension, Sachet,
Gel, Cream, Ointment, Spray, Patch, Eye Drops, Ear Drops, Nasal, Inhaler,
Suppository, Injection) are accurately handled with generalized route gating.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.utils.care_recommendations import get_medicine_gallery, condition_supports_topical


class TestDosageForms:
    """Verifies all 16 clinical dosage forms and their route suitability."""

    @pytest.fixture(autouse=True)
    def mock_dependencies(self, monkeypatch):
        monkeypatch.setattr(
            "ai.utils.care_recommendations.search_drug_openfda",
            lambda c: {"is_live": True, "source": "OpenFDA Mock"}
        )
        monkeypatch.setattr(
            "api.openfda.search_drug_openfda",
            lambda c: {"is_live": True, "source": "OpenFDA Mock"}
        )
        monkeypatch.setattr(
            "ai.utils.care_recommendations.resolve_image",
            lambda source_type, identifier, url=None: ("/mock/img.png", False)
        )
        monkeypatch.setattr(
            "ai.utils.care_recommendations.search_dailymed_drugnames",
            lambda c: [{"drug_name": c, "is_live": True}]
        )
        monkeypatch.setattr(
            "api.dailymed.search_dailymed_drugnames",
            lambda c: [{"drug_name": c, "is_live": True}]
        )

    def test_all_16_dosage_forms_processed_accurately(self):
        forms_catalog = [
            {"name": "Paracetamol 500mg Tablet", "form": "Tablet", "route": "Oral"},
            {"name": "Omeprazole 20mg Capsule", "form": "Capsule", "route": "Oral"},
            {"name": "Promethazine 5mg/5ml Syrup", "form": "Syrup", "route": "Oral"},
            {"name": "Amoxicillin 250mg Suspension", "form": "Suspension", "route": "Oral"},
            {"name": "Oral Rehydration Salts Sachet", "form": "Sachet", "route": "Oral"},
            {"name": "Diclofenac 1.16% Gel", "form": "Gel", "route": "Topical"},
            {"name": "Hydrocortisone 1% Cream", "form": "Cream", "route": "Topical"},
            {"name": "Mupirocin 2% Ointment", "form": "Ointment", "route": "Topical"},
            {"name": "Lidocaine 10% Topical Spray", "form": "Spray", "route": "Topical"},
            {"name": "Fentanyl 25mcg/hr Patch", "form": "Patch", "route": "Transdermal"},
            {"name": "Ciprofloxacin 0.3% Eye Drops", "form": "Eye Drops", "route": "Ophthalmic"},
            {"name": "Ofloxacin 0.3% Ear Drops", "form": "Ear Drops", "route": "Otic"},
            {"name": "Fluticasone 50mcg Nasal Spray", "form": "Nasal Spray", "route": "Nasal"},
            {"name": "Salbutamol 100mcg Inhaler", "form": "Inhaler", "route": "Inhalation"},
            {"name": "Bisacodyl 10mg Suppository", "form": "Suppository", "route": "Rectal"},
            {"name": "Paracetamol 1000mg IV Injection", "form": "Injection", "route": "Intravenous"}
        ]

        # Process in localized context where topical & cutaneous formulations are permitted
        gallery = get_medicine_gallery(
            forms_catalog,
            max_items=None,
            top_condition="Multisite Musculoskeletal & Dermatological Strain",
            symptoms=["Localized Joint Sprain", "Skin Abrasion", "Muscle Pain"]
        )

        assert len(gallery) == 16, f"Expected all 16 dosage forms to be processed, got {len(gallery)}"

        routes_observed = {m["route"].lower() for m in gallery}
        assert "oral" in routes_observed
        assert "topical" in routes_observed
        assert "injectable" in routes_observed or "intravenous" in routes_observed
        assert "ophthalmic" in routes_observed
        assert "otic" in routes_observed
        assert "inhalation" in routes_observed
        assert "rectal" in routes_observed

    def test_topical_forms_filtered_out_for_purely_systemic_febrile_illness(self):
        forms = [
            {"name": "Paracetamol 650mg Tablet", "form": "Tablet", "route": "Oral"},
            {"name": "Diclofenac 1.16% Gel", "form": "Gel", "route": "Topical"},
            {"name": "Ketoprofen 2.5% Gel", "form": "Gel", "route": "Topical"}
        ]
        gallery = get_medicine_gallery(
            forms,
            max_items=None,
            top_condition="Acute Viral Infection",
            symptoms=["High Fever", "Chills", "Generalized Sweating"]
        )
        names = [m["name"].lower() for m in gallery]
        assert any("paracetamol" in n for n in names)
        assert not any("gel" in n for n in names), "Topical pain gels must be filtered out for pure systemic febrile illness"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
