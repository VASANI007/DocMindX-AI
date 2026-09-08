"""
    DocMindX AI - Seasonal & Geographical Health Intelligence Engine
Tracks Indian climatic seasons, monsoon vector-borne surges, winter respiratory risks,
and summer heat waves across Indian States & Union Territories.
Integrates with india_geographic_master.csv and clinical epidemiological surveillance protocols.
"""
import os
import datetime
from typing import Dict, Any, List

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "datasets")
GEO_CSV_PATH = os.path.join(DATASETS_DIR, "india_geographic_master.csv")

# Standard Indian States & Union Territories (28 States + 8 UTs)
INDIAN_STATES = [
    "-- Select State --",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi (NCT)",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry"
]

def get_current_indian_season(month: int = None) -> Dict[str, Any]:
    """
    Returns Indian meteorological season based on month (1-12).
    """
    if month is None:
        month = datetime.datetime.now().month

    # Indian Meteorological Department (IMD) standard seasons
    if month in [6, 7, 8, 9]:
        return {
            "season_id": "monsoon",
            "en": "Monsoon / Rainy Season",
            "hi": "मानसून / वर्षा ऋतु",
            "gu": "ચોમાસું / વરસાદી ઋતુ",
            "is_vector_borne": True,
            "is_waterborne": True,
            "is_heat": False,
            "is_respiratory": False,
            "key_diseases": [
                "Dengue Fever", "Malaria (P. vivax & P. falciparum)", 
                "Chikungunya", "Typhoid Fever", "Acute Viral Gastroenteritis", 
                "Viral Hepatitis A/E", "Leptospirosis"
            ]
        }
    elif month in [10, 11]:
        return {
            "season_id": "post_monsoon",
            "en": "Post-Monsoon / Autumn",
            "hi": "शरद ऋतु (मानसून उपरांत)",
            "gu": "શરદ ઋતુ / પાનખર",
            "is_vector_borne": True,
            "is_waterborne": False,
            "is_heat": False,
            "is_respiratory": True,
            "key_diseases": [
                "Dengue Fever Peak", "Seasonal Viral Fevers", 
                "Allergic Rhinitis", "Bronchial Asthma Flare-ups", "Viral Conjunctivitis"
            ]
        }
    elif month in [12, 1, 2]:
        return {
            "season_id": "winter",
            "en": "Winter / Cold Season",
            "hi": "शीत ऋतु (सर्दी का मौसम)",
            "gu": "શિયાળો / ઠંડીની ઋતુ",
            "is_vector_borne": False,
            "is_waterborne": False,
            "is_heat": False,
            "is_respiratory": True,
            "key_diseases": [
                "Seasonal Influenza (H1N1/H3N2)", "Acute Bronchitis & Pneumonia", 
                "Smog/AQI Induced Asthma Exacerbation", "Common Cold / Rhinovirus", 
                "Arthritis & Joint Stiffness Flare-up"
            ]
        }
    else:  # 3, 4, 5
        return {
            "season_id": "summer",
            "en": "Summer / Pre-Monsoon Heat",
            "hi": "ग्रीष्म ऋतु (गर्मी व लू का मौसम)",
            "gu": "ઉનાળો / ગરમીની ઋતુ",
            "is_vector_borne": False,
            "is_waterborne": True,
            "is_heat": True,
            "is_respiratory": False,
            "key_diseases": [
                "Heat Exhaustion & Hyperthermia", "Sunstroke / Dehydration", 
                "Acute Gastroenteritis & Food Poisoning", "Typhoid", 
                "Chickenpox & Heat Rashes", "Renal Calculi / Kidney Stones"
            ]
        }


def get_seasonal_health_context(state: str, month: int = None, lang_code: str = "en") -> Dict[str, Any]:
    """
    Generates rich, state-specific seasonal risk telemetry and clinical advisory.
    """
    if month is None:
        month = datetime.datetime.now().month

    season_meta = get_current_indian_season(month)
    season_id = season_meta["season_id"]
    season_name = season_meta.get(lang_code, season_meta["en"])
    clean_state = (state or "Gujarat").strip()

    # Read regional climate notes from dataset if available
    regional_notes = ""
    if os.path.exists(GEO_CSV_PATH):
        try:
            import pandas as pd
            df_geo = pd.read_csv(GEO_CSV_PATH)
            matched = df_geo[df_geo["state"].str.lower() == clean_state.lower()]
            if not matched.empty:
                contexts = matched["season_context"].dropna().tolist()
                if contexts:
                    regional_notes = contexts[0]
        except Exception:
            pass

    # Build State-Specific Epidemiological Highlights
    is_gujarat = "gujarat" in clean_state.lower()
    is_maharashtra = "maharashtra" in clean_state.lower()
    is_delhi = "delhi" in clean_state.lower()
    is_north = any(k in clean_state.lower() for k in ["punjab", "haryana", "uttar pradesh", "bihar", "rajasthan"])
    is_south = any(k in clean_state.lower() for k in ["kerala", "tamil nadu", "karnataka", "andhra", "telangana"])
    is_hilly = any(k in clean_state.lower() for k in ["himachal", "uttarakhand", "jammu", "kashmir", "ladakh", "sikkim"])

    # Localized Alerts
    if season_id == "monsoon":
        if lang_code == "gu":
            alert_title = f"ચોમાસું રોગચાળો ચેતવણી — {clean_state}"
            alert_text = (
                f"{clean_state} માં હાલ ચોમાસાની ઋતુ સક્રિય છે. ભેજવાળા વાતાવરણ અને પાણી ભરાવાના કારણે "
                f"ડેન્ગ્યુ, મેલેરિયા, ટાઈફોઈડ, ચિકનગુનિયા અને વાયરલ ફીવરનો ફેલાવો ઝડપથી થાય છે. "
                f"તાવ સાથે શરીરમાં દુખાવો, માથાનો દુખાવો કે ઉલ્ટી હોય તો તુરંત સીબીસી/પ્લેટલેટ્સ ટેસ્ટ કરાવો."
            )
            checklist = [
                "ઘરની આસપાસ પાણી જમા ન થવા દો અને મચ્છરદાની/રીપેલન્ટનો ઉપયોગ કરો.",
                "હંમેશા ઉકાળેલું અથવા ફિલ્ટર કરેલું શુદ્ધ પાણી જ પીવો.",
                "તાવમાં જાતે એન્ટિબાયોટિક કે પેઇનકિલર ન લો; સાદું પેરાસિટામોલ અને વધુ પ્રવાહી લો."
            ]
        elif lang_code == "hi":
            alert_title = f"मानसून मौसमी रोग चेतावनी — {clean_state}"
            alert_text = (
                f"{clean_state} में वर्तमान में मानसून (बारिश का मौसम) सक्रिय है। जलभराव और मच्छरों के प्रजनन के कारण "
                f"डेंगू, मलेरिया, चिकनगुनिया, टाइफाइड और वायरल बुखार का संक्रमण चरम पर रहता है। "
                f"यदि बुखार के साथ सिरदर्द, जोड़ों में दर्द या कमजोरी है तो डॉक्टर से परामर्श लें और सीबीसी प्लेटलेट्स की जांच कराएं।"
            )
            checklist = [
                "घरों और गमलों के आसपास पानी जमा न होने दें, मच्छरदानी का प्रयोग करें।",
                "उबला हुआ या सुरक्षित फ़िल्टर पानी पिएं और बाहर के खुले खाद्य पदार्थों से बचें।",
                "तेज बुखार में माथे पर ठंडे पानी की पट्टी (Cold Sponging) रखें और ओआरएस/तरल पदार्थ लें।"
            ]
        else:
            alert_title = f"Active Monsoon Seasonal Risk Alert — {clean_state}"
            alert_text = (
                f"Monsoon rainy conditions are currently active in {clean_state}. High humidity and waterlogging "
                f"significantly amplify transmission of vector-borne and waterborne illnesses including Dengue, "
                f"Malaria, Chikungunya, Typhoid, and Acute Viral Fevers. Patients presenting with fever, severe body ache, "
                f"or nausea require prompt clinical evaluation and complete blood count (CBC) monitoring."
            )
            checklist = [
                "Eliminate stagnant water around living spaces and use insect repellents / bed nets.",
                "Consume boiled or purified drinking water to prevent enteric typhoid and gastroenteritis.",
                "Avoid unprescribed NSAIDs/painkillers during fever; prioritize hydration (ORS) and medical triage."
            ]

    elif season_id == "winter":
        if lang_code == "gu":
            alert_title = f"શિયાળુ શ્વસનતંત્ર આરોગ્ય એલર્ટ — {clean_state}"
            alert_text = f"{clean_state} માં ઠંડા પવનો અને તાપમાન ઘટવાને કારણે ઈન્ફ્લુએન્ઝા, શરદી, ન્યુમોનિયા અને અસ્થમાની તકલીફો વધે છે."
            checklist = ["ગરમ વસ્ત્રો પહેરો અને સવારે/રાત્રે ઠંડા પવનથી બચો.", "વરાળ (સ્ટીમ) લો અને ગરમ સૂપ/પાણી પીવો."]
        elif lang_code == "hi":
            alert_title = f"शीतकालीन श्वसन स्वास्थ्य चेतावनी — {clean_state}"
            alert_text = f"{clean_state} में गिरते तापमान और प्रदूषण/धुंध के कारण स्वाइन फ्लू (H1N1), निमोनिया, ब्रोंकाइटिस और अस्थमा का जोखिम बढ़ जाता है।"
            checklist = ["गर्म कपड़े पहनें और सुबह-शाम ठंडी हवा व स्मॉग से बचें।", "गुनगुने पानी का सेवन करें और भाप (Steam inhalation) लें।"]
        else:
            alert_title = f"Winter Respiratory Health Alert — {clean_state}"
            alert_text = f"Falling temperatures in {clean_state} heighten risk of Seasonal Influenza (H1N1/H3N2), Bronchitis, Asthma exacerbation, and Pneumonia."
            checklist = ["Dress warmly and minimize exposure to early morning smog / cold drafts.", "Maintain indoor ventilation and steam inhalation for congestion."]

    elif season_id == "summer":
        if lang_code == "gu":
            alert_title = f"ગ્રીષ્મ ઋતુ લૂ અને ડિહાઇડ્રેશન એલર્ટ — {clean_state}"
            alert_text = f"{clean_state} માં ભારે તાપમાનને કારણે લૂ (હીટસ્ટ્રોક), ડિહાઇડ્રેશન અને પેટના ચેપનો ખતરો રહે છે."
            checklist = ["દિવસ દરમિયાન 3-4 લિટર પાણી, લીંબુ પાણી કે છાશ પીવો.", "બપોરે 12 થી 4 સીધા તડકામાં જવાનું ટાળો."]
        elif lang_code == "hi":
            alert_title = f"ग्रीष्मकालीन लू व डिहाइड्रेशन अलर्ट — {clean_state}"
            alert_text = f"{clean_state} में अत्यधिक तापमान के कारण लू (Heat Stroke), निर्जलीकरण (Dehydration) और फूड पॉइजनिंग का खतरा अधिक रहता है।"
            checklist = ["दिन में 3-4 लीटर पानी, ओआरएस या छाछ का सेवन करें।", "दोपहर में धूप में निकलने से बचें और ढीले सूती कपड़े पहनें।"]
        else:
            alert_title = f"Summer Heatwave & Dehydration Advisory — {clean_state}"
            alert_text = f"Elevated ambient temperatures in {clean_state} elevate risks of Heat Exhaustion, Dehydration, Heatstroke, and Acute Food Poisoning."
            checklist = ["Stay well-hydrated with 3–4 liters of fluids (electrolytes/ORS, buttermilk).", "Avoid direct sun exposure during peak hours (12 PM – 4 PM)."]

    else:  # Post-monsoon
        if lang_code == "gu":
            alert_title = f"ચોમાસા પછીની ઋતુ એલર્ટ — {clean_state}"
            alert_text = f"{clean_state} માં ચોમાસા પછીના દિવસોમાં ડેન્ગ્યુ અને વાયરલ તાવની પીક રહે છે."
            checklist = ["મચ્છર કરડવાથી બચો.", "તાવ આવે તો પૂરતો આરામ કરો અને પ્રવાહી લો."]
        elif lang_code == "hi":
            alert_title = f"मानसून उपरांत मौसमी फ्लू चेतावनी — {clean_state}"
            alert_text = f"{clean_state} में वर्षा के बाद के हफ्तों में डेंगू का प्रकोप और मौसमी एलर्जी बढ़ती है।"
            checklist = ["मच्छरों से बचाव के उपाय जारी रखें।", "बुखार या जोड़ों के दर्द में तुरंत चिकित्सीय सलाह लें।"]
        else:
            alert_title = f"Post-Monsoon Transition Advisory — {clean_state}"
            alert_text = f"Transition period in {clean_state} frequently coincides with peak Dengue incidence and seasonal respiratory allergies."
            checklist = ["Maintain strict vector control around households.", "Monitor fever trajectory and seek early clinical consultation."]

    return {
        "season_id": season_id,
        "season_name": season_name,
        "state": clean_state,
        "month": month,
        "is_vector_borne_risk": season_meta["is_vector_borne"],
        "is_waterborne_risk": season_meta["is_waterborne"],
        "is_heat_risk": season_meta["is_heat"],
        "is_respiratory_risk": season_meta["is_respiratory"],
        "key_surging_diseases": season_meta["key_diseases"],
        "alert_title": alert_title,
        "alert_description": alert_text,
        "checklist": checklist,
        "regional_notes": regional_notes
    }
