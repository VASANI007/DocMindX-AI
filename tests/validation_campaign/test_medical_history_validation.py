import pytest
import re
from ai.utils.clinical_safety_rules import clinical_safety_engine
from tests.validation_campaign.clinical_manifest import HISTORY_TEST_CASES

class TestMedicalHistoryValidation:
    """Category D: Medical History, Allergies & Contraindications Test Suite (40 Cases)."""

    @classmethod
    def setup_class(cls):
        cls.engine = clinical_safety_engine

    @pytest.mark.parametrize("case", HISTORY_TEST_CASES, ids=[c["id"] for c in HISTORY_TEST_CASES])
    def test_medical_history_case(self, case):
        cid = case["id"]
        conditions = case.get("conditions", [])
        meds = case.get("meds", [])
        allergies = case.get("allergies", [])

        # Group 1: TC-HIST-001 to 010 (Pre-existing Condition Contraindications)
        if "contraindicated_check" in case:
            # Check condition-specific contraindication evaluation
            eval_res = self.engine.evaluate_condition_contraindications(conditions, candidate_medication_names=[])
            alerts = " ".join(eval_res.get("guidance_alerts", []))
            assert len(eval_res.get("guidance_alerts", [])) > 0, (
                f"Case {cid} ({conditions}): Expected contraindication guidance alerts, got none."
            )

        # Group 2: TC-HIST-011 to 020 (Drug Allergies & Immunological Cross-Reactivity)
        elif "disallowed_drugs" in case:
            disallowed = case["disallowed_drugs"]
            for drug in disallowed:
                allergy_eval = self.engine.evaluate_allergies(allergies, [drug])
                assert not allergy_eval["is_safe"], (
                    f"Case {cid}: Drug '{drug}' was not flagged as unsafe for patient allergic to {allergies}."
                )
                assert drug in allergy_eval["blocked_medications"], (
                    f"Case {cid}: Drug '{drug}' not in blocked medications list: {allergy_eval['blocked_medications']}."
                )

        # Group 3: TC-HIST-021 to 030 (Drug-Drug Interactions)
        elif "interaction_risk" in case:
            # Map interacting candidate drug for the DDI assessment
            interaction_candidates = {
                "TC-HIST-021": ["Ibuprofen 400mg", "Aspirin"],
                "TC-HIST-022": ["Spironolactone 25mg"],
                "TC-HIST-023": ["Clarithromycin 500mg"],
                "TC-HIST-024": ["Tramadol 50mg"],
                "TC-HIST-025": ["Omeprazole 20mg"],
                "TC-HIST-026": ["Fluconazole 150mg"],
                "TC-HIST-027": ["Sildenafil 50mg"],
                "TC-HIST-028": ["Erythromycin 250mg"],
                "TC-HIST-029": ["Fluconazole 200mg"],
                "TC-HIST-030": ["Ibuprofen 400mg", "Diclofenac"]
            }
            cand_meds = interaction_candidates.get(cid, [])
            ddi_eval = self.engine.evaluate_drug_drug_interactions(meds, candidate_medication_names=cand_meds)
            assert ddi_eval["has_interactions"], (
                f"Case {cid}: Expected DDI risk for ongoing meds {meds} with proposed {cand_meds}, but none was identified."
            )
            interactions = ddi_eval["interactions"]
            assert len(interactions) > 0

        # Group 4: TC-HIST-031 to 040 (Special Populations, Organ Failure, Enzymopathies)
        else:
            spec_eval = self.engine.evaluate_special_populations(conditions, candidate_medication_names=[])
            assert spec_eval["has_special_population_alerts"], (
                f"Case {cid} ({conditions}): Expected special population safety alert, got none."
            )
            alerts = spec_eval["alerts"]
            assert len(alerts) > 0, f"Case {cid}: Alerts list was empty."
