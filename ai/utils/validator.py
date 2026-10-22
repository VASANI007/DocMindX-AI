"""
DocMindX AI — Clinical Demographics, Symptoms & Workflow Transition Validator
Enforces:
1. Strict required demographics validation (Age group, Biological gender, State/Location).
2. Optional field normalization and boundary sanitization (Height, Weight, Blood Group).
3. Symptom selection validation and canonical consistency.
4. Step transition gating preventing illegal advancement without required fields.
5. Patient context isolation and anti-leakage guards.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import re

from ai.utils.seasonal_context import INDIAN_STATES

# Allowed Blood Groups
VALID_BLOOD_GROUPS = {
    "", "none", "unknown", "a+", "a-", "b+", "b-", "ab+", "ab-", "o+", "o-"
}

# Standard Age Group Keys recognized by DocMindX AI
VALID_AGE_KEYS = {
    "0_1", "2_5", "6_12", "13_17", "18_20", "21_25", "26_30", "31_35",
    "36_40", "41_45", "46_50", "51_55", "56_60", "61_65", "66_70", "71_75",
    "76_80", "80_plus", "adult", "geriatric", "pediatric", "child", "adolescent", "infant"
}

# Standard Biological Gender Keys
VALID_GENDER_KEYS = {"male", "female", "other", "non-binary", "unspecified"}


@dataclass
class ValidationResult:
    """Structured result returned by clinical validation gates."""
    is_valid: bool
    missing_fields: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    sanitized_context: Dict[str, Any] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return self.is_valid

    @property
    def sanitized(self) -> Dict[str, Any]:
        return self.sanitized_context

    def __getitem__(self, item):
        if item == "valid":
            return self.is_valid
        if item == "is_valid":
            return self.is_valid
        if item == "missing_fields":
            return self.missing_fields
        if item == "errors":
            return self.errors
        if item in ("sanitized", "sanitized_context"):
            return self.sanitized_context
        return getattr(self, item)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "valid": self.is_valid,
            "missing_fields": list(self.missing_fields),
            "errors": list(self.errors),
            "sanitized_context": dict(self.sanitized_context),
            "sanitized": dict(self.sanitized_context)
        }


def validate_demographics(user_context: Optional[Dict[str, Any]] = None, **kwargs) -> ValidationResult:
    """
    Validates Step 1 demographics.
    Supports either dictionary context or explicit keyword arguments:
    age, gender, state, height, weight, blood_group.
    """
    ctx = {}
    if user_context and isinstance(user_context, dict):
        ctx.update(user_context)
    if kwargs:
        ctx.update(kwargs)

    if not ctx:
        return ValidationResult(
            is_valid=False,
            missing_fields=["Age Group", "Biological Gender", "State / Location"],
            errors=["User context dictionary is missing or empty."],
            sanitized_context={}
        )

    missing = []
    errors = []
    sanitized = dict(ctx)

    # 1. Age (Required) & Age Group Mapping
    raw_age = ctx.get("age")
    age_key = str(ctx.get("age_key", "")).strip().lower()

    if raw_age is None and (not age_key or age_key in ["select", "none", "null", ""]):
        missing.append("Age Group")
        errors.append("Required field 'age' is missing.")
    elif raw_age is not None:
        try:
            # Handle float or int representation
            if isinstance(raw_age, str):
                raw_age_clean = raw_age.strip()
                if not raw_age_clean or raw_age_clean.lower() in ["select", "none", "null"]:
                    missing.append("Age Group")
                    errors.append("Required field 'age' is missing.")
                    numeric_age = None
                else:
                    numeric_age = float(raw_age_clean)
            elif isinstance(raw_age, (int, float)):
                numeric_age = float(raw_age)
            else:
                errors.append("Age must be numeric.")
                numeric_age = None

            if numeric_age is not None:
                if numeric_age < 0:
                    errors.append("Age cannot be negative.")
                elif numeric_age > 125:
                    errors.append(f"Age {numeric_age} exceeds maximum physiological bound (125).")
                else:
                    sanitized["age"] = int(numeric_age) if numeric_age.is_integer() else numeric_age
                    if numeric_age <= 10:
                        sanitized["age_group"] = "0-10"
                    elif numeric_age <= 20:
                        sanitized["age_group"] = "11-20"
                    elif numeric_age <= 30:
                        sanitized["age_group"] = "21-30"
                    elif numeric_age <= 40:
                        sanitized["age_group"] = "31-40"
                    elif numeric_age <= 50:
                        sanitized["age_group"] = "41-50"
                    elif numeric_age <= 60:
                        sanitized["age_group"] = "51-60"
                    else:
                        sanitized["age_group"] = "61+"
        except ValueError:
            errors.append(f"Age '{raw_age}' is not a valid number.")
    elif age_key:
        sanitized["age_key"] = age_key
        sanitized["age"] = age_key.replace("_", "-").capitalize()
        sanitized["age_group"] = age_key

    # 2. Biological Gender (Required)
    gen_val = str(ctx.get("gender") or ctx.get("gender_key") or "").strip()
    valid_genders = {"male", "female", "other", "non-binary"}
    if not gen_val or gen_val.lower() in ["select", "none", "null", ""]:
        missing.append("Biological Gender")
        errors.append("Required field 'gender' is missing.")
    elif gen_val.lower() not in valid_genders and gen_val.lower() not in ["m", "f"]:
        errors.append(f"Invalid gender '{gen_val}'. Expected Male, Female, or Other.")
    else:
        g_lower = gen_val.lower()
        if g_lower in ["male", "m"]:
            sanitized["gender"] = "Male"
            sanitized["gender_key"] = "male"
        elif g_lower in ["female", "f"]:
            sanitized["gender"] = "Female"
            sanitized["gender_key"] = "female"
        else:
            sanitized["gender"] = "Other"
            sanitized["gender_key"] = "other"

    # 3. State / Location (Required)
    raw_state = str(ctx.get("state") or ctx.get("location") or "").strip()
    if not raw_state or raw_state.lower() in ["-- select state --", "select", "none", "null", ""]:
        missing.append("State / Location")
        errors.append("Required field 'state' is missing.")
    else:
        # Sanitize HTML / XSS tags
        clean_state = re.sub(r"<[^>]*>", "", raw_state).strip()
        if not clean_state:
            clean_state = "India"
        sanitized["state"] = clean_state
        sanitized["location"] = clean_state

    # 4. Optional Height (cm)
    raw_h = ctx.get("height")
    if raw_h is not None and str(raw_h).strip() and str(raw_h).strip().lower() not in ["none", "null", ""]:
        try:
            h_val = float(str(raw_h).replace("cm", "").strip())
            if 20.0 <= h_val <= 300.0:
                sanitized["height"] = f"{int(h_val) if h_val.is_integer() else h_val} cm"
                sanitized["height_cm"] = h_val
            else:
                errors.append(f"Height value {h_val} cm is outside realistic physiological range (20 - 300 cm).")
        except ValueError:
            errors.append(f"Height '{raw_h}' is non-numeric.")
    else:
        sanitized["height"] = "None"

    # 5. Optional Weight (kg)
    raw_w = ctx.get("weight")
    if raw_w is not None and str(raw_w).strip() and str(raw_w).strip().lower() not in ["none", "null", ""]:
        try:
            w_val = float(str(raw_w).replace("kg", "").strip())
            if 1.0 <= w_val <= 500.0:
                sanitized["weight"] = f"{int(w_val) if w_val.is_integer() else w_val} kg"
                sanitized["weight_kg"] = w_val
            else:
                errors.append(f"Weight value {w_val} kg is outside realistic physiological range (1 - 500 kg).")
        except ValueError:
            errors.append(f"Weight '{raw_w}' is non-numeric.")
    else:
        sanitized["weight"] = "None"

    # 6. Optional Blood Group
    raw_bg = ctx.get("blood_group")
    if raw_bg is not None and str(raw_bg).strip() and str(raw_bg).strip().lower() not in ["none", "null", ""]:
        clean_bg = str(raw_bg).strip().upper()
        if clean_bg.lower() in VALID_BLOOD_GROUPS:
            sanitized["blood_group"] = clean_bg if clean_bg.lower() not in ["none", "unknown", ""] else "None"
        else:
            errors.append(f"Invalid blood group '{raw_bg}'. Must be one of A+, A-, B+, B-, AB+, AB-, O+, O-, or Unknown.")
    else:
        sanitized["blood_group"] = "None"

    is_valid = (len(missing) == 0 and len(errors) == 0)
    return ValidationResult(
        is_valid=is_valid,
        missing_fields=missing,
        errors=errors,
        sanitized_context=sanitized
    )


def validate_symptoms_selection(
    selected_symptoms: Optional[List[str]],
    detected_chief_condition: Optional[Any] = None
) -> Tuple[bool, List[str]]:
    """
    Validates that at least one symptom or chief condition is provided.
    Returns (is_valid, list_of_cleaned_symptoms).
    """
    cleaned = []
    if selected_symptoms:
        for s in selected_symptoms:
            s_str = str(s).strip()
            if s_str and s_str.lower() not in ["none", "null"] and s_str not in cleaned:
                cleaned.append(s_str)

    if not cleaned and detected_chief_condition:
        if isinstance(detected_chief_condition, dict):
            c_name = detected_chief_condition.get("disease_name") or detected_chief_condition.get("name")
            if c_name:
                cleaned.append(str(c_name).strip())
        elif isinstance(detected_chief_condition, str) and detected_chief_condition.strip():
            cleaned.append(detected_chief_condition.strip())

    return (len(cleaned) > 0, cleaned)


def validate_step_progression(
    current_step: int,
    target_step: int,
    user_context: Dict[str, Any],
    selected_symptoms: List[str]
) -> ValidationResult:
    """
    Validates if transition between assessment steps is authorized.
    Step 1 -> Step 2 requires valid demographics and >= 1 symptom.
    Step 2 -> Step 3 requires >= 1 symptom.
    Step 3 -> Step 4 requires valid demographics and symptoms.
    """
    # Moving backwards is always permitted
    if target_step <= current_step:
        return ValidationResult(is_valid=True)

    # Moving forwards requires prior step preconditions:
    demo_res = validate_demographics(user_context)
    has_syms, cleaned_syms = validate_symptoms_selection(selected_symptoms)

    missing = list(demo_res.missing_fields)
    errors = list(demo_res.errors)

    if not has_syms:
        missing.append("Clinical Symptoms")

    if missing or errors:
        return ValidationResult(
            is_valid=False,
            missing_fields=missing,
            errors=errors,
            sanitized_context=demo_res.sanitized_context
        )

    return ValidationResult(is_valid=True, sanitized_context=demo_res.sanitized_context)
