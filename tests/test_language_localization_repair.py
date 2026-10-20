"""
DocMindX AI — Universal Language Consistency & Care Localization Test Suite

Validates that:
1. When target language is English, NO Gujarati or Hindi script leaks into:
   - Medicine dosages ("૧ થી ૨ બુંદ" -> "1 to 2 drops")
   - Course durations ("૫ થી ૭ દિવસ" -> "5 to 7 days")
   - Supportive yoga names and tutorial URLs
   - Thermal compress guidance (title, instructions, duration, precautions)
   - Specialized hospital therapies and referrals
   - Food timings and clinical advisories
2. Switching languages dynamically through localize_care_recommendations completely localizes all fields.
3. Offline fallback sanitizers guarantee 100% pure script even when LLM APIs are unreachable.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.utils.care_recommendations import (
    localize_care_recommendations,
    contains_indic_script,
    sanitize_indic_text_to_pure_english,
    _enforce_target_language_consistency,
    get_dynamic_clinical_recommendations
)


def test_sanitize_indic_text_to_pure_english():
    # Dosages and numbers
    assert sanitize_indic_text_to_pure_english("૧ થી ૨ બુંદ") == "1 to 2 drops"
    assert sanitize_indic_text_to_pure_english("૫ થી ૭ દિવસ") == "5 to 7 days"
    assert sanitize_indic_text_to_pure_english("દિવસે ૨ થી ૩ વખત") == "2 to 3 times daily"
    assert sanitize_indic_text_to_pure_english("૫ થી ૧૦ મિનિટ માટે") == "for 5 to 10 minutes"
    
    # Combined duration and frequency
    combined = sanitize_indic_text_to_pure_english("દિવસે ૨ થી ૩ વખત, ૫ થી ૧૦ મિનિટ માટે")
    assert "2 to 3 times daily" in combined
    assert "5 to 10 minutes" in combined
    assert not contains_indic_script(combined)

    # Compress guidance
    c_title = sanitize_indic_text_to_pure_english("આંખ માટે ઠંડા પાણીની હળવી પટ્ટી (Cold Compress)")
    assert "Cold" in c_title or "Compress" in c_title
    assert not contains_indic_script(c_title)

    c_inst = sanitize_indic_text_to_pure_english("સ્વચ્છ કપડાને ઠંડા પાણીમાં પલાળીને બંધ આંખો પર હળવા હાથે મૂકો.")
    assert "cloth" in c_inst.lower() or "cold water" in c_inst.lower()
    assert not contains_indic_script(c_inst)

    c_caut = sanitize_indic_text_to_pure_english("આંખ પર વધુ પડતું દબાણ ન કરવું અને સ્વચ્છ કપડાનો જ ઉપયોગ કરવો.")
    assert not contains_indic_script(c_caut)

    # Specialized therapies
    spec_ref = sanitize_indic_text_to_pure_english("આંખના નિષ્ણાત (Ophthalmologist)")
    assert "Ophthalmologist" in spec_ref
    assert not contains_indic_script(spec_ref)

    spec_proc = sanitize_indic_text_to_pure_english("ઓપ્થાલમિક પ્રેશર મૂલ્યાંકન અને ગ્લુકોમા સ્ક્રીનીંગ")
    assert "Ophthalmic" in spec_proc or "Glaucoma" in spec_proc
    assert not contains_indic_script(spec_proc)


def test_localize_care_recommendations_exact_user_scenario():
    """
    Recreates the exact user scenario: A care recommendation generated in Gujarati
    is localized to English. All Gujarati fields must be converted to pure English.
    """
    gujarati_care_res = {
        "lang_code": "gu",
        "state": "Gujarat",
        "top_condition": "Glaucoma",
        "summary": "દર્દીને ગુજરાતમાં પાનખર ઋતુ દરમિયાન આંખમાં દુખાવો થયો છે.",
        "recovery_duration": "ડોક્ટરની સલાહ મુજબ સારવાર પર આધાર રાખે છે.",
        "hydration_advice": "શરીરને હાઇડ્રેટેડ રાખવા માટે દરરોજ 8 થી 10 ગ્લાસ પાણી પીવો.",
        "foods_to_eat": ["ગાજર અને પાલક (વિટામિન A સમૃદ્ધ ખોરાક)", "લીલા પાંદડાવાળા શાકભાજી"],
        "foods_to_avoid": ["વધુ પડતો તીખો અને તળેલો ખોરાક", "પ્રોસેસ્ડ ફૂડ"],
        "clinical_dos": ["આંખના ડૉક્ટરની નિયમિત સલાહ લો.", "સ્ક્રીન સમય મર્યાદિત કરો."],
        "clinical_donts": ["આંખોને વારંવાર ઘસશો નહીં.", "ડૉક્ટરની સલાહ વિના આંખના ટીપાં ન વાપરો."],
        "red_flags": ["દ્રષ્ટિમાં અચાનક ઘટાડો કે ઝાંખપ", "આંખમાં અસહ્ય દુખાવો અને લાલાશ"],
        "medicine_gallery": [
            {
                "name": "Carboxymethylcellulose 0.5% Eye Drops (Refresh Tears / Add Tears)",
                "indication": "આંખની શુષ્કતા, બળતરા અને ખેંચાણમાં રાહત આપે છે.",
                "dosage": "૧ થી ૨ બુંદ",
                "course_duration": "૫ થી ૭ દિવસ",
                "food_timing": "જમ્યા પછી",
                "time_of_day": "Morning & Night",
                "type": "OTC",
                "warnings": "ડ્રોપરની અણીને હાથ અડાડવો નહીં."
            }
        ],
        "yoga_recommendations": [
            {
                "name": "શાંતિ મુદ્રા અને પ્રાણાયામ (Anulom Vilom Pranayama)",
                "benefits": "માનસિક તણાવ ઘટાડે છે અને આંખના સ્નાયુઓને આરામ આપે છે.",
                "instructions": "સુખાસનમાં બેસીને ઊંડા શ્વાસ લો.",
                "youtube_url": "https://www.youtube.com/results?search_query=how+to+do+શાંતિ+મુદ્રા+અને+પ્રાણાયામ+yoga+tutorial"
            }
        ],
        "compress_guidance": {
            "mode": "cold_sponging",
            "title": "આંખ માટે ઠંડા પાણીની હળવી પટ્ટી (Cold Compress)",
            "instructions": "સ્વચ્છ કપડાને ઠંડા પાણીમાં પલાળીને બંધ આંખો પર હળવા હાથે મૂકો.",
            "duration": "દિવસે ૨ થી ૩ વખત, ૫ થી ૧૦ મિનિટ માટે",
            "duration_and_frequency": "દિવસે ૨ થી ૩ વખત, ૫ થી ૧૦ મિનિટ માટે",
            "cautions": "આંખ પર વધુ પડતું દબાણ ન કરવું અને સ્વચ્છ કપડાનો જ ઉપયોગ કરવો."
        },
        "specialized_therapies": {
            "is_indicated": True,
            "therapy_name": "ઓપ્થાલમિક પ્રેશર મૂલ્યાંકન અને ગ્લુકોમા સ્ક્રીનીંગ",
            "specialist_type": "આંખના નિષ્ણાત (Ophthalmologist)",
            "specialist_consult": "આંખના નિષ્ણાત (Ophthalmologist)",
            "overview": "આંખનું અંદરનું દબાણ (IOP) માપવા અને ઓપ્ટિક નર્વની તપાસ માટે વિશિષ્ટ ક્લિનિકલ મૂલ્યાંકન.",
            "patient_guidance": "હોસ્પિટલમાં તપાસ કરાવો.",
            "therapies": [
                {
                    "name": "ઓપ્થાલમિક પ્રેશર મૂલ્યાંકન અને ગ્લુકોમા સ્ક્રીનીંગ",
                    "category": "Tertiary Hospital Treatment",
                    "setting": "Specialized Hospital / Medical Center",
                    "description": "આંખનું અંદરનું દબાણ (IOP) માપવા અને ઓપ્ટિક નર્વની તપાસ માટે વિશિષ્ટ ક્લિનિકલ મૂલ્યાંકન."
                }
            ]
        }
    }

    localized = localize_care_recommendations(gujarati_care_res, "en")

    assert localized["lang_code"] == "en"

    # 1. Medicine Dosage & Duration MUST be pure English
    med = localized["medicine_gallery"][0]
    assert med["dosage"] == "1 to 2 drops", f"Dosage not English: {med['dosage']}"
    assert med["course_duration"] == "5 to 7 days", f"Duration not English: {med['course_duration']}"
    assert med["food_timing"] == "After Food"
    assert not contains_indic_script(med["dosage"])
    assert not contains_indic_script(med["course_duration"])

    # 2. Yoga routine name and YouTube tutorial link
    yoga = localized["yoga_recommendations"][0]
    assert "Anulom Vilom" in yoga["name"] or "Pranayama" in yoga["name"]
    assert not contains_indic_script(yoga["name"])
    assert not contains_indic_script(yoga["youtube_url"])

    # 3. Compress Guidance
    comp = localized["compress_guidance"]
    assert not contains_indic_script(comp["title"])
    assert not contains_indic_script(comp["instructions"])
    assert not contains_indic_script(comp["duration"])
    assert not contains_indic_script(comp["cautions"])
    assert any(phrase in comp["duration"].lower() for phrase in ["times a day", "daily", "2 to 3 times"])

    # 4. Specialized Therapies
    spec = localized["specialized_therapies"]
    assert "Ophthalmologist" in spec["specialist_type"]
    assert not contains_indic_script(spec["specialist_type"])
    assert not contains_indic_script(spec["therapy_name"])
    assert not contains_indic_script(spec["overview"])
    for th in spec["therapies"]:
        assert not contains_indic_script(th["name"])
        assert not contains_indic_script(th["description"])

    # 5. Global Script Verification
    assert not contains_indic_script(localized), "Residual Indic script found in localized English plan!"


def test_dynamic_clinical_recommendations_en_purity():
    """Validates that get_dynamic_clinical_recommendations for lang_code='en' produces zero Indic script."""
    user_context = {
        "age": "21 - 25 Years",
        "gender": "Male",
        "location": "Gujarat",
        "state": "Gujarat",
        "severity": "Moderate",
        "duration": "1 - 3 Days",
        "conditions": ["None"],
        "medications": "None",
        "allergies": "None",
        "family_history": "None"
    }
    recs = get_dynamic_clinical_recommendations(
        symptoms=["Eye Pain"],
        user_context=user_context,
        top_condition="Glaucoma",
        lang_code="en"
    )
    assert recs["lang_code"] == "en"
    assert not contains_indic_script(recs), "Indic script leaked into English dynamic recommendations!"
