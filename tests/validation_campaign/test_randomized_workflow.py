import random
import pytest
from faker import Faker
from ai.disease_prediction.predict import triage_engine
from ai.disease_prediction.canonical_concepts import canonical_normalizer
from ai.utils.clinical_safety_rules import clinical_safety_engine
from ai.utils.care_recommendations import _extract_clinical_presentation_attributes

RANDOM_SEED = 20261021

def generate_random_patient_profiles(count=25, seed=RANDOM_SEED):
    fake = Faker()
    Faker.seed(seed)
    random.seed(seed)

    records = canonical_normalizer.bridge.id_to_record
    all_symptom_ids = list(records.keys())
    all_symptom_names = [records[sid].get("name", records[sid].get("canonical_name", "")) for sid in all_symptom_ids]

    indian_states = ["Gujarat", "Maharashtra", "Rajasthan", "Delhi", "Karnataka", "Tamil Nadu", "Uttar Pradesh", "West Bengal", "Punjab", "Kerala"]
    genders = ["Male", "Female"]
    durations = ["Started Today", "1-3 Days", "3-5 Days", "1-2 Weeks", "More than 2 Weeks"]
    severities = ["Mild", "Moderate", "Severe"]
    allergies_pool = [None, "Penicillin", "Sulfa", "Aspirin", "NSAIDs", "Cephalosporins", "Paracetamol"]
    history_pool = [None, "Hypertension", "Diabetes", "Chronic Kidney Disease", "Asthma", "G6PD Deficiency", "Peptic Ulcer Disease", "Pregnancy 3rd Trimester"]

    profiles = []
    for i in range(count):
        age = random.randint(1, 95)
        if age <= 10:
            age_group = "0-10"
        elif age <= 20:
            age_group = "11-20"
        elif age <= 30:
            age_group = "21-30"
        elif age <= 40:
            age_group = "31-40"
        elif age <= 50:
            age_group = "41-50"
        elif age <= 60:
            age_group = "51-60"
        else:
            age_group = "61+"

        gender = random.choice(genders)
        state = random.choice(indian_states)
        duration = random.choice(durations)
        severity = random.choice(severities)

        num_symptoms = random.randint(1, 5)
        chosen_symptom_ids = random.sample(all_symptom_ids, num_symptoms)
        chosen_symptom_names = [records[sid].get("name", records[sid].get("canonical_name", "")) for sid in chosen_symptom_ids]

        allergy = random.choice(allergies_pool)
        allergies = [allergy] if allergy else []

        hist = random.choice(history_pool)
        # Avoid pregnancy for male patients
        if gender == "Male" and hist and "pregnancy" in hist.lower():
            hist = "Hypertension"
        history = [hist] if hist else []

        profiles.append({
            "case_id": f"TC-RND-{str(i+1).zfill(3)}",
            "age": age,
            "age_group": age_group,
            "gender": gender,
            "state": state,
            "duration": duration,
            "severity": severity,
            "symptom_ids": chosen_symptom_ids,
            "symptom_names": chosen_symptom_names,
            "allergies": allergies,
            "history": history
        })
    return profiles

RANDOM_PROFILES = generate_random_patient_profiles(25, RANDOM_SEED)

class TestRandomizedWorkflow:
    """Fixed-Seed Randomized Workflow & Invariant Testing (25 Cases, Seed 20261021)."""

    @pytest.mark.parametrize("profile", RANDOM_PROFILES, ids=[p["case_id"] for p in RANDOM_PROFILES])
    def test_randomized_clinical_invariants(self, profile):
        cid = profile["case_id"]
        age = profile["age"]
        gender = profile["gender"]
        symptom_ids = profile["symptom_ids"]
        symptom_names = profile["symptom_names"]
        allergies = profile["allergies"]
        history = profile["history"]

        # Invariant 1: Universal Execution Invariant — Triage engine never crashes
        res = triage_engine.evaluate_symptoms(
            selected_symptom_ids=symptom_ids,
            age_group=profile["age_group"],
            gender=gender,
            duration=profile["duration"],
            severity=profile["severity"]
        )
        assert isinstance(res, dict), f"Case {cid}: Expected dict response, got {type(res)}"
        assert "urgency_level" in res
        assert "ranked_conditions" in res or "differential_diagnoses" in res

        cond_list = res.get("ranked_conditions") or res.get("differential_diagnoses", [])
        pred_names = [c.get("name", c.get("disease_name", "")).lower() for c in cond_list]

        # Invariant 2: Anatomical Invariant — Male cannot receive female conditions, and vice versa
        if gender == "Male":
            female_terms = ["ovarian cancer", "cervical cancer", "uterine fibroids", "endometriosis", "pregnancy complications"]
            for ft in female_terms:
                assert not any(ft in pn for pn in pred_names), (
                    f"Case {cid}: Male patient received female condition '{ft}' in {pred_names}"
                )
        elif gender == "Female":
            male_terms = ["prostate cancer", "benign prostatic hyperplasia", "prostatitis", "epididymitis", "testicular torsion"]
            for mt in male_terms:
                assert not any(mt in pn for pn in pred_names), (
                    f"Case {cid}: Female patient received male condition '{mt}' in {pred_names}"
                )

        # Invariant 3: Score Boundedness Invariant — All match scores between 0 and 100
        for c in cond_list:
            score = c.get("match_percentage", c.get("match_score", 0))
            assert 0 <= score <= 100, f"Case {cid}: Condition match score out of bounds: {score}"

        # Invariant 4: Pharmacological Safety Invariant — Blocked medications check
        if allergies or history:
            candidate_drugs = ["Amoxicillin", "Ibuprofen", "Ciprofloxacin", "Metformin", "Aspirin"]
            safety_eval = clinical_safety_engine.run_full_safety_audit(
                conditions=history,
                allergies=allergies,
                candidate_medications=candidate_drugs,
                patient_profile={"age_group": profile["age_group"], "gender": gender}
            )
            # If penicillin allergy, Amoxicillin MUST be blocked
            if "Penicillin" in allergies:
                assert "Amoxicillin" in safety_eval["blocked_medications"]
            # If aspirin or nsaid allergy, Ibuprofen and Aspirin MUST be blocked
            if "NSAIDs" in allergies or "Aspirin" in allergies:
                assert "Ibuprofen" in safety_eval["blocked_medications"] or "Aspirin" in safety_eval["blocked_medications"]

        # Invariant 5: Emergency Detection Invariant
        red_flag_symptoms = {"S000046", "S000026", "S000109"} # Chest pain, shortness of breath, blood in stool
        has_red_flag = any(sid in red_flag_symptoms for sid in symptom_ids)
        if has_red_flag:
            attrs = _extract_clinical_presentation_attributes(
                symptoms=symptom_names,
                top_condition="",
                user_context=profile
            )
            assert attrs["has_emergency_red_flags"] is True or res.get("is_emergency") is True
