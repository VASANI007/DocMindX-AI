"""
    DocMindX AI - General Utility and Formatting Helpers
"""
import re
import datetime
from typing import Any, Optional

def sanitize_text(text: str) -> str:
    """Removes unsafe characters and normalizes whitespace."""
    if not text or not isinstance(text, str):
        return ""
    # Strip HTML tags and normalize spaces
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()

def format_timestamp(dt: Optional[datetime.datetime] = None) -> str:
    """Returns standardized ISO-like datetime string."""
    dt = dt or datetime.datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def truncate_text(text: str, max_chars: int = 120, suffix: str = "...") -> str:
    """Truncates string to max characters without breaking words abruptly."""
    if not text or len(text) <= max_chars:
        return text or ""
    return text[:max_chars].rsplit(" ", 1)[0] + suffix

def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts value to float with fallback."""
    try:
        if val is None:
            return default
        # Remove commas or units
        cleaned = re.sub(r"[^\d.-]", "", str(val))
        return float(cleaned) if cleaned else default
    except Exception:
        return default

def calculate_bmi(weight_kg: float, height_cm: float) -> Optional[dict]:
    """Calculates BMI and health category."""
    if weight_kg <= 0 or height_cm <= 0:
        return None
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m * height_m)
    
    if bmi < 18.5:
        cat = "Underweight"
        color = "warning"
    elif 18.5 <= bmi < 24.9:
        cat = "Normal Weight"
        color = "success"
    elif 25.0 <= bmi < 29.9:
        cat = "Overweight"
        color = "warning"
    else:
        cat = "Obese"
        color = "critical"

    return {
        "bmi": round(bmi, 1),
        "category": cat,
        "status_color": color
    }
