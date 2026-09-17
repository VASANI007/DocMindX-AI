"""
    DocMindX AI - Global API-First Clinical Pipeline Orchestrator
Implements the end-to-end clinical reasoning pipeline with per-provider state tracking.

Pipeline stages:
1. Symptom extraction & normalization
2. BioPortal concept resolution (live)
3. NLM condition discovery (live)
4. WHO ICD-11 validation (live)
5. Anatomical consistency scoring
6. Candidate scoring from local datasets
7. Red flag safety gate
8. Source metadata assembly
9. Fallback warning generation

Every stage tracks: provider, status, is_live, fallback_used, failure_type, latency.
"""
import logging
import time
from typing import List, Dict, Any, Optional

_logger = logging.getLogger("DocMindX.TriageEngine.Pipeline")


class ProviderStatus:
    """Tracks the live/fallback state of a single API provider."""
    def __init__(self, name: str):
        self.name = name
        self.attempted = False
        self.success = False
        self.is_live = False
        self.fallback_used = False
        self.failure_type: Optional[str] = None
        self.fallback_reason: str = ""
        self.latency_ms: float = 0.0

    def record_success(self, latency_ms: float = 0.0):
        self.attempted = True
        self.success = True
        self.is_live = True
        self.fallback_used = False
        self.failure_type = None
        self.fallback_reason = ""
        self.latency_ms = latency_ms

    def record_failure(self, failure_type: str, fallback_reason: str = "", latency_ms: float = 0.0):
        self.attempted = True
        self.success = False
        self.is_live = False
        self.fallback_used = True
        self.failure_type = failure_type
        self.fallback_reason = fallback_reason or failure_type
        self.latency_ms = latency_ms

    def record_skipped(self, reason: str = "not attempted"):
        self.attempted = False
        self.success = False
        self.is_live = False
        self.fallback_used = False
        self.failure_type = "skipped"
        self.fallback_reason = reason

    def to_dict(self) -> dict:
        return {
            "provider": self.name,
            "attempted": self.attempted,
            "success": self.success,
            "is_live": self.is_live,
            "fallback_used": self.fallback_used,
            "failure_type": self.failure_type,
            "fallback_reason": self.fallback_reason,
            "latency_ms": round(self.latency_ms, 1)
        }


class ClinicalPipelineOrchestrator:
    """
    Global API-First Clinical Pipeline.
    Orchestrates multi-provider clinical intelligence for any disease category.

    Usage:
        orchestrator = ClinicalPipelineOrchestrator()
        result = orchestrator.run_pipeline(
            symptom_names=["lower back pain", "pain radiating to left leg"],
            patient_context={"age_group": "31-40", "gender": "Male", "duration": "1-3 Days", "severity": "Moderate"}
        )
    """

    def __init__(self):
        self.providers = {
            "WHO_ICD": ProviderStatus("WHO ICD-11"),
            "BioPortal": ProviderStatus("BioPortal NCBO"),
            "NLM": ProviderStatus("NLM Clinical Tables"),
            "OpenFDA": ProviderStatus("OpenFDA"),
            "DailyMed": ProviderStatus("DailyMed NIH"),
            "Gemini": ProviderStatus("Google Gemini"),
            "Groq": ProviderStatus("Groq LLM"),
        }

    def _get_bioportal_concepts(self, symptom_names: List[str]) -> List[dict]:
        """Resolves clinical concepts via BioPortal for the reported symptoms."""
        concepts = []
        try:
            from api.bioportal import search_bioportal_concept
            t0 = time.time()
            for sym in symptom_names[:5]:  # Limit API calls — resolve primary symptoms
                results = search_bioportal_concept(sym, page_size=2)
                if results:
                    first = results[0]
                    if first.get("is_live"):
                        self.providers["BioPortal"].record_success(latency_ms=(time.time() - t0) * 1000)
                    concepts.extend(results)
            if not self.providers["BioPortal"].success and not self.providers["BioPortal"].attempted:
                self.providers["BioPortal"].record_failure("empty_response", "No BioPortal results for any symptom")
            _logger.info("[Pipeline] BioPortal: %d concept(s) resolved", len(concepts))
        except Exception as exc:
            self.providers["BioPortal"].record_failure("error", str(exc))
            _logger.error("[Pipeline] BioPortal resolution error: %s", exc)
        return concepts

    def _get_nlm_conditions(self, symptom_names: List[str]) -> List[str]:
        """Discovers candidate conditions via NLM Clinical Tables."""
        conditions = []
        try:
            from api.nlm_clinical import search_nlm_conditions
            t0 = time.time()
            # Use first 2 key symptoms for NLM search
            for sym in symptom_names[:2]:
                results = search_nlm_conditions(sym, max_list=8)
                for c in results:
                    if c and c not in conditions:
                        conditions.append(c)
            if conditions:
                self.providers["NLM"].record_success(latency_ms=(time.time() - t0) * 1000)
            else:
                self.providers["NLM"].record_failure("empty_response", "NLM returned no conditions")
            _logger.info("[Pipeline] NLM: %d condition(s) discovered", len(conditions))
        except Exception as exc:
            self.providers["NLM"].record_failure("error", str(exc))
            _logger.error("[Pipeline] NLM error: %s", exc)
        return conditions

    def _validate_top_conditions_who(self, conditions: List[dict]) -> List[dict]:
        """Validates top candidate conditions against WHO ICD-11."""
        try:
            from api.who_icd import validate_icd11_condition
            t0 = time.time()
            any_validated = False
            for i, cond in enumerate(conditions):
                c_name = cond.get("name", "")
                result = validate_icd11_condition(c_name)
                conditions[i]["icd_validation"] = result
                is_ver = bool(result.get("validated") or result.get("verification_status") == "VERIFIED")
                if is_ver:
                    conditions[i]["icd_code"] = result.get("code") or result.get("icd_code")
                    conditions[i]["icd_verified"] = True
                    conditions[i]["icd_source"] = "WHO ICD-11 Live"
                    conditions[i]["icd_system"] = "ICD-11"
                    any_validated = True
                else:
                    conditions[i]["icd_verified"] = False
                    conditions[i]["icd_source"] = "Clinical Reference"
                    conditions[i]["icd_system"] = "ICD-11"
                    if not conditions[i].get("icd_code"):
                        conditions[i]["icd_code"] = result.get("code") or cond.get("icd_code", "Unspecified")

            if any_validated:
                self.providers["WHO_ICD"].record_success(latency_ms=(time.time() - t0) * 1000)
            else:
                self.providers["WHO_ICD"].record_failure("no_validation", "WHO returned no validated entities")
        except Exception as exc:
            self.providers["WHO_ICD"].record_failure("error", str(exc))
            _logger.error("[Pipeline] WHO ICD-11 validation error: %s", exc)
        return conditions

    def _build_system_status(self) -> dict:
        """Assembles the per-provider system status dict."""
        any_live = any(p.is_live for p in self.providers.values())
        any_fallback = any(p.fallback_used for p in self.providers.values())

        return {
            "live_api_available": any_live,
            "fallback_used": any_fallback,
            "providers": {name: p.to_dict() for name, p in self.providers.items()}
        }

    def _build_fallback_warning(self) -> str:
        """Returns a user-facing warning when fallback sources are in use."""
        failed = [p for p in self.providers.values() if p.fallback_used and p.attempted]
        if not failed:
            return ""

        provider_names = ", ".join(p.name for p in failed)
        return (
            f"⚠️ Some live clinical data services are currently unavailable ({provider_names}). "
            "DocMindX AI is using locally stored clinical reference data for parts of this assessment. "
            "Results may be less current and should be clinically verified with a qualified healthcare professional."
        )

    def run_pipeline(
        self,
        symptom_names: Optional[List[str]] = None,
        patient_context: Optional[Dict[str, Any]] = None,
        chief_condition: Optional[str] = None,
        selected_symptom_ids: Optional[List[str]] = None,
        negative_findings: Optional[List[str]] = None,
        input_text: Optional[str] = None,
        run_bioportal: bool = True,
        run_nlm: bool = True,
        run_care_recommendations: bool = False
    ) -> dict:
        """
        Runs the full production API-first clinical intelligence pipeline.

        Flow:
        1. Canonical normalization (multilingual & voice/text inputs)
        2. Positive/negative finding extraction & strict negation enforcement
        3. Live BioPortal evidence retrieval with provenance tracking
        4. Live NLM condition discovery
        5. Core clinical compatibility triage engine
        6. Emergency & red-flag gating
        7. WHO ICD-11 live validation
        8. Dynamic care recommendations & medication formulation verification (optional)
        9. Structured clinical data object conforming to Section 57
        """
        t_start = time.time()
        patient_context = dict(patient_context or {})
        symptom_names = [str(s).strip() for s in (symptom_names or []) if str(s).strip()]
        selected_symptom_ids = [str(sid).strip() for sid in (selected_symptom_ids or []) if str(sid).strip()]
        negative_findings = [str(n).strip() for n in (negative_findings or []) if str(n).strip()]

        # Reset provider states for this run
        for p in self.providers.values():
            p.attempted = False
            p.success = False
            p.is_live = False
            p.fallback_used = False

        from ai.disease_prediction.canonical_concepts import canonical_normalizer

        canonical_rep = None
        # Stage 1: Free-text / Voice Transcript Canonical Normalization
        if input_text and str(input_text).strip():
            canonical_rep = canonical_normalizer.normalize(str(input_text).strip())

            # Check for unresolvable input ("something feels strange in my body")
            if canonical_rep.clinical_status == "insufficient_information" and not symptom_names and not selected_symptom_ids:
                _logger.info("[Pipeline] Input produced insufficient clinical information — returning safe prompt")
                return {
                    "clinical_status": "insufficient_information",
                    "normalization_status": "failed",
                    "is_emergency": False,
                    "urgency_level": "Insufficient Information (Please Describe Symptoms)",
                    "ranked_conditions": [],
                    "red_flags": [],
                    "positive_findings": [],
                    "negative_findings": [],
                    "symptom_names": [],
                    "symptom_ids": [],
                    "tests_to_discuss": [],
                    "system_status": self._build_system_status(),
                    "fallback_warning": "",
                    "message": "Insufficient clinical information to determine a differential pattern. Please describe your symptoms in more detail."
                }

            # Merge canonical findings
            for c in canonical_rep.canonical_concepts:
                c_lbl = c.replace("_", " ").title()
                if c_lbl not in symptom_names:
                    symptom_names.append(c_lbl)

            for sid in canonical_rep.symptom_ids:
                if sid not in selected_symptom_ids:
                    selected_symptom_ids.append(sid)

            for neg in canonical_rep.negative_findings:
                if neg not in negative_findings:
                    negative_findings.append(neg)

            if canonical_rep.duration and not patient_context.get("duration"):
                patient_context["duration"] = canonical_rep.duration
            if canonical_rep.severity and not patient_context.get("severity"):
                patient_context["severity"] = canonical_rep.severity

        # Check symptom names for negation phrases (e.g. "no fever", "not having headache")
        cleaned_symptoms = []
        for s in symptom_names:
            sub_norm = canonical_normalizer.normalize(s)
            if sub_norm.negative_findings:
                for neg in sub_norm.negative_findings:
                    if neg not in negative_findings:
                        negative_findings.append(neg)
            if sub_norm.symptom_ids and not sub_norm.negative_findings:
                for sid in sub_norm.symptom_ids:
                    if sid not in selected_symptom_ids:
                        selected_symptom_ids.append(sid)
                cleaned_symptoms.append(s)
            elif not sub_norm.negative_findings:
                cleaned_symptoms.append(s)
        symptom_names = cleaned_symptoms

        # Strict negation enforcement: remove any negated concept/ID from positive findings
        neg_set = {n.lower().strip() for n in negative_findings}
        symptom_names = [s for s in symptom_names if s.lower().strip() not in neg_set and not any(n in s.lower() for n in neg_set if len(n) > 3)]
        selected_symptom_ids = [sid for sid in selected_symptom_ids if sid not in negative_findings and sid not in neg_set]

        # Resolve any missing symptom IDs for symptom names
        for s in symptom_names:
            sid = canonical_normalizer.get_symptom_id(s)
            if sid and sid not in selected_symptom_ids and sid not in negative_findings:
                selected_symptom_ids.append(sid)

        # Stage 2: BioPortal concept resolution (contextual — non-blocking)
        bioportal_concepts = []
        if run_bioportal and symptom_names:
            bioportal_concepts = self._get_bioportal_concepts(symptom_names)
        else:
            self.providers["BioPortal"].record_skipped("BioPortal skipped")

        # Stage 3: NLM condition discovery (contextual — non-blocking)
        nlm_conditions = []
        if run_nlm and symptom_names:
            nlm_conditions = self._get_nlm_conditions(symptom_names)
        else:
            self.providers["NLM"].record_skipped("NLM skipped")

        # Stage 4: Core triage engine (Compatibility, Anatomy, Red Flags)
        try:
            from ai.disease_prediction.predict import triage_engine
            patient_context["symptom_names"] = symptom_names
            patient_context["chief_condition"] = chief_condition
            patient_context["negative_findings"] = negative_findings

            if hasattr(triage_engine, "evaluate_triage"):
                triage_result = triage_engine.evaluate_triage(
                    reported_symptom_ids=selected_symptom_ids,
                    patient_history=patient_context,
                    symptom_names=symptom_names,
                    chief_condition=chief_condition,
                    negative_findings=negative_findings
                )
            else:
                triage_result = triage_engine.evaluate_symptoms(
                    selected_symptom_ids=selected_symptom_ids,
                    age_group=patient_context.get("age", patient_context.get("age_group", "21-30")),
                    gender=patient_context.get("gender", "Male"),
                    duration=patient_context.get("duration", "1-3 Days"),
                    existing_conditions=patient_context.get("conditions", {}),
                    symptom_names=symptom_names,
                    chief_condition=chief_condition,
                    negative_findings=negative_findings
                )
        except Exception as exc:
            _logger.error("[Pipeline] Core triage engine error: %s", exc)
            triage_result = {
                "is_emergency": False,
                "red_flags": [],
                "urgency_level": "Moderate Attention (Consult Physician)",
                "ranked_conditions": [],
                "tests_to_discuss": []
            }

        # Stage 5: WHO ICD-11 validation for top conditions
        ranked = triage_result.get("ranked_conditions", [])
        if ranked:
            ranked = self._validate_top_conditions_who(ranked)
            triage_result["ranked_conditions"] = ranked

        # Stage 6: Dynamic care recommendations (if requested)
        if run_care_recommendations:
            try:
                from ai.utils.care_recommendations import get_dynamic_clinical_recommendations
                top_name = ranked[0].get("name", "Acute Illness") if ranked else "Acute Illness"
                care_res = get_dynamic_clinical_recommendations(
                    symptoms=symptom_names,
                    user_context=patient_context,
                    top_condition=top_name,
                    lang_code=patient_context.get("lang_code", "en")
                )
                triage_result["care_recommendations"] = care_res
            except Exception as c_exc:
                _logger.error("[Pipeline] Care recommendations error: %s", c_exc)

        # Stage 7: Assemble system status, provenance and warnings
        system_status = self._build_system_status()
        fallback_warning = self._build_fallback_warning()

        triage_result["clinical_status"] = "success"
        triage_result["normalization_status"] = "complete" if canonical_rep else "partial"
        triage_result["positive_findings"] = symptom_names
        triage_result["negative_findings"] = negative_findings
        triage_result["symptom_names"] = symptom_names
        triage_result["symptom_ids"] = selected_symptom_ids
        triage_result["system_status"] = system_status
        triage_result["fallback_warning"] = fallback_warning
        triage_result["pipeline_context"] = {
            "bioportal_concepts": bioportal_concepts,
            "nlm_conditions": nlm_conditions,
            "elapsed_ms": round((time.time() - t_start) * 1000, 1),
            "canonical_representation": canonical_rep.to_dict() if canonical_rep else None
        }

        _logger.info(
            "[Pipeline] Run completed in %.1fms: %d conditions, %d red flags, emergency=%s",
            (time.time() - t_start) * 1000,
            len(ranked),
            len(triage_result.get("red_flags", [])),
            triage_result.get("is_emergency", False)
        )

        return triage_result


# Global singleton
clinical_pipeline = ClinicalPipelineOrchestrator()
