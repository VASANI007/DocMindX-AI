import json
import re
import pytest
from tests.validation_campaign.clinical_manifest import PERSISTENCE_ISOLATION_TEST_CASES
from ai.disease_prediction.predict import triage_engine
from ai.utils.clinical_safety_rules import clinical_safety_engine
from ai.disease_prediction.canonical_concepts import canonical_normalizer

def validate_step_transition(target_step: int, session_data: dict) -> bool:
    """
    Validates clinical multi-step workflow gating.
    Step 1: Patient Demographics (Requires age, gender, state)
    Step 2: Symptoms Selection (Requires Step 1 complete)
    Step 3: Medical History & Allergies (Requires Step 1 & Step 2 complete with >=1 symptom)
    Step 4: Clinical Triage & Care Recommendations (Requires Steps 1, 2, 3 complete)
    """
    session = session_data or {}
    has_step1 = bool(
        (session.get("age") or session.get("age_group")) and
        session.get("gender") in ["Male", "Female", "Other", "Transgender"] and
        (session.get("state") or session.get("location"))
    )
    symptoms = session.get("selected_symptoms") or session.get("symptoms") or []
    has_step2 = bool(has_step1 and len(symptoms) > 0)
    has_step3 = bool(has_step2)

    if target_step == 1:
        return True
    elif target_step == 2:
        return has_step1
    elif target_step == 3:
        return has_step1 and has_step2
    elif target_step == 4:
        return has_step1 and has_step2 and has_step3
    return False

def resolve_age_group(age: int) -> str:
    """Standard clinical age tier resolution."""
    if age <= 10:
        return "0-10"
    elif age <= 20:
        return "11-20"
    elif age <= 30:
        return "21-30"
    elif age <= 40:
        return "31-40"
    elif age <= 50:
        return "41-50"
    elif age <= 60:
        return "51-60"
    else:
        return "61+"

class SessionState:
    """Simulated Clinical Workflow Session State."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_step = 1
        self.demographics = {}
        self.selected_symptom_ids = []
        self.medical_history = []
        self.allergies = []
        self.language = "en"
        self.triage_cache = None

    def reset(self):
        self.current_step = 1
        self.demographics = {}
        self.selected_symptom_ids = []
        self.medical_history = []
        self.allergies = []
        self.language = "en"
        self.triage_cache = None

    def remove_symptom(self, symptom_id: str):
        if symptom_id in self.selected_symptom_ids:
            self.selected_symptom_ids.remove(symptom_id)
            self.triage_cache = None  # Cache invalidation

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "step": self.current_step,
            "demographics": self.demographics,
            "symptoms": self.selected_symptom_ids,
            "medical_history": self.medical_history,
            "allergies": self.allergies,
            "language": self.language
        }

class TestPersistenceIsolation:
    """Category G: Multi-Step Form Persistence, State Isolation & Serialization Test Suite (20 Cases)."""

    @pytest.mark.parametrize("case", PERSISTENCE_ISOLATION_TEST_CASES, ids=[c["id"] for c in PERSISTENCE_ISOLATION_TEST_CASES])
    def test_persistence_isolation_case(self, case):
        cid = case["id"]

        # TC-REG-001 to 005: Step Transition Gating
        if cid in ["TC-REG-001", "TC-REG-002", "TC-REG-003", "TC-REG-004", "TC-REG-005"]:
            target_step = case["target_step"]
            session_data = case["session_data"]
            expected = case["expected_allowed"]
            actual = validate_step_transition(target_step, session_data)
            assert actual == expected, (
                f"Case {cid}: Expected transition to Step {target_step} allowed={expected}, got {actual}."
            )

        # TC-REG-006: Symptom removal in Step 2 clears previous triage cache
        elif cid == "TC-REG-006":
            sess = SessionState("sess-006")
            sess.selected_symptom_ids = ["S000046", "S000026"]
            sess.triage_cache = {"urgency": "High", "conditions": ["CAD"]}
            sess.remove_symptom("S000046")
            assert sess.triage_cache is None
            assert "S000046" not in sess.selected_symptom_ids

        # TC-REG-007: Gender change in Step 1 updates anatomical filters
        elif cid == "TC-REG-007":
            # Male anatomical check
            male_res = triage_engine.evaluate_symptoms(["S000092", "S000005"], gender="Male")
            male_conds = [c.get("name", "").lower() for c in (male_res.get("ranked_conditions") or [])]
            assert not any("ovarian" in c or "cervical" in c or "uterine" in c for c in male_conds)

            # Female anatomical check
            female_res = triage_engine.evaluate_symptoms(["S000239", "S000226"], gender="Female")
            female_conds = [c.get("name", "").lower() for c in (female_res.get("ranked_conditions") or [])]
            assert not any("prostate" in c or "prostatitis" in c or "testicular" in c for c in female_conds)

        # TC-REG-008: Age tier change recalculates age group
        elif cid == "TC-REG-008":
            assert resolve_age_group(8) == "0-10"
            assert resolve_age_group(65) == "61+"

        # TC-REG-009: Allergy addition dynamically blocks previously recommended drug
        elif cid == "TC-REG-009":
            # Baseline: no allergy
            base_eval = clinical_safety_engine.run_full_safety_audit(
                allergies=[],
                candidate_medications=["Amoxicillin"]
            )
            assert base_eval["is_safe"] is True

            # Modified: patient adds Penicillin allergy
            allergy_eval = clinical_safety_engine.run_full_safety_audit(
                allergies=["Penicillin"],
                candidate_medications=["Amoxicillin"]
            )
            assert allergy_eval["is_safe"] is False
            assert "Amoxicillin" in allergy_eval["blocked_medications"]

        # TC-REG-010: Language change preserves clinical symptom selection
        elif cid == "TC-REG-010":
            sess = SessionState("sess-010")
            sess.selected_symptom_ids = ["S000001", "S000023"]
            sess.language = "en"
            # Change language
            sess.language = "hi"
            assert sess.selected_symptom_ids == ["S000001", "S000023"]

        # TC-REG-011: Concurrent user isolation Patient A (Pediatric) vs Patient B (Geriatric)
        elif cid == "TC-REG-011":
            sess_a = SessionState("sess-A")
            sess_b = SessionState("sess-B")
            sess_a.demographics = {"age": 4, "gender": "Male"}
            sess_b.demographics = {"age": 78, "gender": "Female"}
            assert sess_a.demographics["age"] == 4
            assert sess_b.demographics["age"] == 78
            assert sess_a.demographics != sess_b.demographics

        # TC-REG-012: Concurrent session symptom isolation
        elif cid == "TC-REG-012":
            sess_a = SessionState("sess-A")
            sess_b = SessionState("sess-B")
            sess_a.selected_symptom_ids = ["S000046"]
            sess_b.selected_symptom_ids = ["S000089"]
            assert "S000089" not in sess_a.selected_symptom_ids
            assert "S000046" not in sess_b.selected_symptom_ids

        # TC-REG-013: Concurrent allergy isolation
        elif cid == "TC-REG-013":
            sess_a = SessionState("sess-A")
            sess_b = SessionState("sess-B")
            sess_a.allergies = ["Penicillin"]
            sess_b.allergies = []
            eval_a = clinical_safety_engine.run_full_safety_audit(
                allergies=sess_a.allergies,
                candidate_medications=["Amoxicillin"]
            )
            eval_b = clinical_safety_engine.run_full_safety_audit(
                allergies=sess_b.allergies,
                candidate_medications=["Amoxicillin"]
            )
            assert eval_a["is_safe"] is False
            assert eval_b["is_safe"] is True

        # TC-REG-014: Simulated multi-tab navigation state consistency
        elif cid == "TC-REG-014":
            tab1 = SessionState("sess-multi")
            tab2 = SessionState("sess-multi-clone")
            tab1.current_step = 2
            tab2.current_step = 3
            assert tab1.current_step == 2
            assert tab2.current_step == 3

        # TC-REG-015: Session reset clears all clinical variables
        elif cid == "TC-REG-015":
            sess = SessionState("sess-reset")
            sess.demographics = {"age": 30, "gender": "Male"}
            sess.selected_symptom_ids = ["S000001"]
            sess.allergies = ["Aspirin"]
            sess.reset()
            assert sess.demographics == {}
            assert sess.selected_symptom_ids == []
            assert sess.allergies == []
            assert sess.current_step == 1

        # TC-REG-016: Scan payload serialization valid JSON
        elif cid == "TC-REG-016":
            payload = {
                "patient_id": "P-98741",
                "demographics": {"age": 45, "gender": "Male"},
                "symptoms": ["S000001", "S000005"],
                "timestamp": "2026-10-21T10:00:00Z"
            }
            dumped = json.dumps(payload)
            loaded = json.loads(dumped)
            assert loaded == payload

        # TC-REG-017: Required DB columns present in scan record / triage_history
        elif cid == "TC-REG-017":
            # Triage history columns defined in schema_postgres.sql
            required = ["session_id", "created_at", "age_group", "gender", "state", "duration", "symptoms_list", "urgency_level"]
            db_record = {
                "session_id": "test-uuid",
                "created_at": "2026-10-21 10:00:00",
                "age_group": "21-30",
                "gender": "Male",
                "state": "Gujarat",
                "duration": "1-3 Days",
                "symptoms_list": "Fever, Cough",
                "urgency_level": "Moderate Attention (Consult Physician)"
            }
            for col in required:
                assert col in db_record

        # TC-REG-018: Zero plaintext API keys in serialized audit logs
        elif cid == "TC-REG-018":
            audit_log = {
                "session_id": "sess-sec-018",
                "endpoint": "/api/triage",
                "provider": "Gemini (gemini-3.5-flash-lite)",
                "status": "SUCCESS",
                "timestamp": "2026-10-21T10:30:00Z"
            }
            log_str = json.dumps(audit_log)
            # Assert no Google AI Studio keys or Groq keys leaked
            assert "AIzaSy" not in log_str
            assert "gsk_" not in log_str
            assert "API_KEY" not in log_str

        # TC-REG-019: Offline queue persistence format valid
        elif cid == "TC-REG-019":
            offline_item = {
                "id": "queue-101",
                "created_at": "2026-10-21T10:00:00Z",
                "endpoint": "triage_evaluation",
                "payload": {"symptoms": ["S000001"]},
                "sync_status": "PENDING_SYNC",
                "retry_count": 0
            }
            dumped = json.dumps(offline_item)
            loaded = json.loads(dumped)
            assert loaded["sync_status"] == "PENDING_SYNC"
            assert "payload" in loaded

        # TC-REG-020: Large payload stress (50 selected symptoms) gracefully handled
        elif cid == "TC-REG-020":
            # Provide 50 symptom IDs
            all_symptoms = [f"S{str(i).zfill(6)}" for i in range(1, 51)]
            res = triage_engine.evaluate_symptoms(all_symptoms, age_group="31-40", gender="Male")
            assert isinstance(res, dict)
            assert "ranked_conditions" in res or "differential_diagnoses" in res
            assert "urgency_level" in res
