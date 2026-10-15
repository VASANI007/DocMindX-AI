"""
    DocMindX AI - Global Clinical and Application Constants
"""

# Supported Languages (Strict 3-Language Architecture: English, Hindi, Gujarati)
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "flag": ""},
    "hi": {"name": "Hindi", "native": "हिन्दी", "flag": ""},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "flag": ""}
}

# Age Demographic Groups
AGE_GROUPS = [
    "Infant (0–1 yr)",
    "Toddler / Child (2–12 yrs)",
    "Adolescent / Teen (13–18 yrs)",
    "Adult (19–59 yrs)",
    "Senior Citizen (60+ yrs)"
]

# Gender Categories
GENDER_OPTIONS = ["Female", "Male", "Other / Prefer not to say"]

# Blood Pressure Classification Categories (AHA / ACC Standards)
BP_STATUS_OPTIONS = [
    "No / Normal (< 120/80 mmHg)",
    "Elevated (120–129/< 80 mmHg)",
    "High BP - Stage 1 (130–139/80–89 mmHg)",
    "High BP - Stage 2 (≥ 140/≥ 90 mmHg)",
    "Low BP (Hypotension < 90/60 mmHg)"
]

# Diabetes Status
DIABETES_STATUS_OPTIONS = [
    "No / Non-Diabetic",
    "Prediabetic (HbA1c 5.7–6.4%)",
    "Type 2 Diabetes Mellitus",
    "Type 1 Diabetes Mellitus",
    "Gestational Diabetes"
]

# Healthcare Facility Search Categories
HEALTHCARE_CATEGORIES = {
    "Hospital": ["hospital", "general_hospital"],
    "Clinic": ["clinic", "doctors", "health_post"],
    "Pharmacy": ["pharmacy", "chemist"],
    "Diagnostic Lab": ["laboratory", "diagnostic_centre"]
}

# Clinical Triage Risk Levels
RISK_LEVEL_LOW = "LOW"
RISK_LEVEL_MEDIUM = "MEDIUM"
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_EMERGENCY = "EMERGENCY"

# Emergency Helpline Contacts (India)
EMERGENCY_CONTACTS = {
    "National Emergency Number": "112",
    "Ambulance Services": "108",
    "Medical Helpline": "104",
    "Women Helpline": "1091",
    "Mental Health Support (Tele-MANAS)": "14416"
}
