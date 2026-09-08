"""
    DocMindX AI - Patient-Friendly Medicine Explainer
Generates dosage guidelines, food interactions, and precautions in user's preferred language.
"""
def explain_medication(medicine_data: dict, user_lang: str = "en") -> dict:
    """
    Translates raw pharmacology data into structured, easy-to-understand patient advice (No emojis).
    """
    med_name = medicine_data.get("medicine_name", "Medicine")
    generic = medicine_data.get("generic_name", "Active Formulation")
    indication = medicine_data.get("primary_indication", "Symptomatic relief")
    dosage = medicine_data.get("standard_dosage", "As directed by your physician.")
    warnings = medicine_data.get("warnings", "Do not exceed stated dose. Consult doctor.")
    timing = medicine_data.get("timing_advice", "Take with plenty of water after meals.")

    if user_lang == "hi":
        return {
            "title": f"{med_name} (जेनेरिक: {generic})",
            "purpose": f"**उपयोग:** {indication}",
            "timing_and_dosage": f"**खुराक और समय:** {dosage} • {timing}",
            "precautions": f"**सावधानियां:** {warnings}",
            "food_advice": "तेल-मसालेदार भोजन कम करें और पर्याप्त पानी पिएं।"
        }
    elif user_lang == "gu":
        return {
            "title": f"{med_name} (જેનેરિક: {generic})",
            "purpose": f"**ઉપયોગ:** {indication}",
            "timing_and_dosage": f"**ડોઝ અને સમય:** {dosage} • {timing}",
            "precautions": f"**સાવચેતી:** {warnings}",
            "food_advice": "તળેલું અને મસાલેદાર ભોજન ટાળો અને પૂરતું પાણી પીવો."
        }
    else:
        return {
            "title": f"{med_name} (Generic: {generic})",
            "purpose": f"**Primary Indication:** {indication}",
            "timing_and_dosage": f"**Dosage & Timing:** {dosage} • {timing}",
            "precautions": f"**Precautions:** {warnings}",
            "food_advice": "Avoid heavy/oily meals and ensure optimal hydration."
        }
