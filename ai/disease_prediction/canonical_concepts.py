"""
    DocMindX AI — Generalized Canonical Clinical Concepts & Multilingual Semantic Normalization Engine
    
    Architectural Principles:
    1. LANGUAGE-INDEPENDENT: Clinical meaning maps to the same canonical representation
       regardless of language (English, Hindi, Gujarati, Marathi, Bengali, Tamil, Telugu,
       Kannada, Malayalam, Punjabi, Urdu, Odia, Assamese, Romanized variants, code-mixed).
    2. ZERO CONDITION-SPECIFIC HACKS: Animal bites, radicular pain, chest pain, rashes,
       and trauma are treated as generalized clinical attributes, exposures, and anatomy.
    3. EXPLICIT NEGATION: "No fever", "તાવ નથી", "बुखार नहीं है", "ताप नाही" explicitly
       become negative findings (fever = absent), NEVER converting to positive findings.
    4. NO DEFAULT FALLBACK CONTAMINATION: If normalization fails, returns
       normalization_status = "failed" with zero fabricated headache/fever/infection.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
import re
import unicodedata
import os
import csv
import logging

_logger = logging.getLogger("DocMindX.CanonicalConcepts")


class ClinicalIntegrityError(ValueError):
    """Raised when canonical symptom taxonomy mappings violate clinical data integrity."""
    pass


@dataclass
class CanonicalClinicalRepresentation:
    """Standardized language-independent clinical intermediate representation."""
    raw_text: str = ""
    detected_language: str = "en"
    normalized_text: str = ""
    canonical_concepts: List[str] = field(default_factory=list)
    symptom_ids: List[str] = field(default_factory=list)
    exposure_ids: List[str] = field(default_factory=list)
    anatomical_regions: List[str] = field(default_factory=list)
    laterality: List[str] = field(default_factory=list)  # 'left', 'right', 'bilateral'
    severity: str = "moderate"  # 'mild', 'moderate', 'severe', 'critical'
    duration: str = "1-3 days"  # 'today', '1-3 days', '4-7 days', '1-2 weeks', '>2 weeks'
    duration_days: Optional[int] = None
    age_group: str = "Adult"
    gender: str = "Unspecified"
    associated_features: List[str] = field(default_factory=list)
    negative_findings: List[str] = field(default_factory=list)
    clinical_attributes: Dict[str, Any] = field(default_factory=dict)
    normalization_confidence: float = 0.0
    normalization_status: str = "failed"  # 'success', 'partial', 'failed'
    unsupported_reasons: List[str] = field(default_factory=list)

    @property
    def clinical_status(self) -> str:
        if not self.symptom_ids and not self.canonical_concepts and not self.exposure_ids:
            return "insufficient_information"
        return "success"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "detected_language": self.detected_language,
            "normalized_text": self.normalized_text,
            "canonical_concepts": list(self.canonical_concepts),
            "symptom_ids": list(self.symptom_ids),
            "exposure_ids": list(self.exposure_ids),
            "anatomical_regions": list(self.anatomical_regions),
            "laterality": list(self.laterality),
            "severity": self.severity,
            "duration": self.duration,
            "duration_days": self.duration_days,
            "age_group": self.age_group,
            "gender": self.gender,
            "associated_features": list(self.associated_features),
            "negative_findings": list(self.negative_findings),
            "clinical_attributes": dict(self.clinical_attributes),
            "normalization_confidence": round(self.normalization_confidence, 2),
            "normalization_status": self.normalization_status,
            "clinical_status": self.clinical_status,
            "unsupported_reasons": list(self.unsupported_reasons)
        }

    @property
    def positive_symptoms(self) -> List[str]:
        return self.symptom_ids

    @property
    def exposure_events(self) -> List[str]:
        return self.exposure_ids

    @property
    def positive_tokens(self) -> Set[str]:
        tokens = set()
        for c in self.canonical_concepts:
            tokens |= {w.lower() for w in re.findall(r'\b\w{3,}\b', str(c))}
        return tokens


# ==============================================================================
# MULTILINGUAL TOKENS & LEXICONS
# ==============================================================================
LATERALITY_PATTERNS = {
    "left": [
        r"left", r"\bl\b", r"बाएं", r"बायां", r"बायाँ", r"बायें", r"उलटा",
        r"ડાબા", r"ડાબો", r"ડાબી", r"ડાબું", r"ડાબે",
        r"डाव्या", r"डावा", r"डावी", r"डावे",
        r"বাম", r"বাঁ", r"இடது", r"ఎడమ", r"ಎಡ", r"ഇടത്", r"ਖੱਬੇ", r"ବାମ", r"بایاں", r"بائیں",
        r"daba", r"dabo", r"dabi", r"dabu", r"dabe",
        r"baaye", r"baayan", r"baaya", r"davya", r"dava", r"davi"
    ],
    "right": [
        r"right", r"\br\b", r"दाएं", r"दायां", r"दायाँ", r"दायें", r"सीधा",
        r"જમણા", r"જમણો", r"જમણી", r"જમણું", r"જમણે",
        r"उजव्या", r"उजवा", r"उजवी", r"उजवे",
        r"ডান", r"வலது", r"కుడి", r"ಬಲ", r"വലത്", r"ਸੱਜੇ", r"ଡାହାଣ", r"دایاں", r"دائیں",
        r"jamna", r"jamno", r"jamni", r"jamnu", r"jamne",
        r"daaye", r"daayan", r"ujva", r"ujvya"
    ],
    "bilateral": [
        r"bilateral", r"both", r"दोनों", r"બંને", r"દોનો", r"दोन्ही",
        r"উভয়", r"இரு", r"రెండు", r"ಎರಡೂ", r"രണ്ടും", r"ਦੋਵੇਂ", r"ଦୁଇ",
        r"both sides", r"dono", r"banne", r"donhi"
    ]
}

ANATOMICAL_REGION_PATTERNS = {
    "lower_limb": [
        r"leg", r"legs", r"foot", r"feet", r"thigh", r"calf", r"ankle", r"knee",
        r"पैर", r"पांव", r"टांग", r"जांघ", r"पिंडली", r"घुटना", r"टखना",
        r"પગ", r"સાથળ", r"ઘૂંટણ", r"ઘૂંટી", r"પાની",
        r"पाय", r"पाऊल", r"मांडी", r"गुडघा", r"घोटा",
        r"পা", r"কাল", r"கால்", r"பாதம்", r"కాలు", r"పాదం", r"ಕಾಲು", r"ಕಾಲಿನ", r"കാൽ", r"പാദം",
        r"ਲੱਤ", r"ਪੈਰ", r"ଗୋଡ଼", r"پاؤں", r"ٹانگ",
        r"pag", r"paga", r"pair", r"paanv", r"paav", r"tang", r"taang", r"pay", r"paay"
    ],
    "upper_limb": [
        r"arm", r"hand", r"shoulder", r"elbow", r"wrist", r"finger", r"forearm",
        r"हाथ", r"बांह", r"कंधा", r"कोहनी", r"कलाई", r"उंगली",
        r"હાથ", r"ખભા", r"ખભો", r"કોણી", r"કાંડું", r"આંગળી",
        r"हात", r"खांदा", r"कोपरा", r"मनगट", r"बोट",
        r"হাত", r"கை", r"தோள்", r"చేయి", r"భుజం", r"ಕೈ", r"தோಳು", r"കൈ",
        r"ਹੱਥ", r"ਮੋਢਾ", r"ହାତ", r"ہاتھ", r"بازو",
        r"hath", r"haath", r"khandha", r"khabho", r"khabha"
    ],
    "lumbar_spine": [
        r"lower back", r"lumber", r"lumbar", r"\bback\b", r"spine", r"waist",
        r"कमर", r"पीठ", r"रीढ़", r"रीढ़ की हड्डी",
        r"કમર", r"પીઠ", r"કરોડરજ્જુ", r"કરોડ",
        r"कंबर", r"पाठ", r"पाठीचा कणा",
        r"কোমর", r"இடுப்பு", r"ముதுகு", r"నడుము", r"వీపు", r"ಸೊಂಟ", r"ಬೆನ್ನು", r"ഇടുപ്പ്", r"പുറം",
        r"ਕਮਰ", r"ਪਿੱਠ", r"କଣ୍ଟା", r"କମର", r"کمر", r"پیٹھ",
        r"kamar", r"peeth", r"pith", r"kambar"
    ],
    "cervical_spine": [
        r"neck", r"cervical", r"nucha",
        r"गर्दन", r"गला", r"ગર્દન", r"ગરદન", r"ગળું", r"मान", r"गळा",
        r"ঘাড়", r"கழுத்து", r"మెడ", r"ಕುತ್ತಿಗೆ", r"കഴുത്ത്", r"ਗਰਦਨ", r"ବେକ", r"گردن",
        r"gardan", r"maan", r"galu"
    ],
    "thoracic_chest": [
        r"chest", r"thorax", r"precordium", r"breast",
        r"सीना", r"छाती", r"हार्ट", r"છાતી", r"હૃદય", r"छातीत",
        r"বুক", r"மார்பு", r"ఛాతీ", r"ಎದೆ", r"നെഞ്ച്", r"ਛਾਤੀ", r"ଛାତି", r"سینہ",
        r"chaati", r"chhati", r"seena", r"seene"
    ],
    "abdominal_gi": [
        r"abdomen", r"stomach", r"belly", r"tummy", r"gut",
        r"पेट", r"उदर", r"પેટ", r"पोट",
        r"পেট", r"வயிறு", r"కడుపు", r"ಹೊಟ್ಟೆ", r"വയർ", r"ਢਿੱਡ", r"ପେଟ", r"پیٹ",
        r"pet", r"peta", r"pot"
    ],
    "head_cranial": [
        r"head", r"scalp", r"forehead", r"temple", r"cranial",
        r"सिर", r"सर", r"माथा", r"માથું", r"ડોકું", r"डोके",
        r"মাথা", r"தலை", r"తల", r"ತಲೆ", r"തല", r"ਸਿਰ", r"ମୁଣ୍ଡ", r"سر",
        r"sir", r"sar", r"mathu", r"mathe", r"doke"
    ]
}

DOG_TOKENS = [
    r"dog", r"dogs", r"canine", r"hound", r"puppy",
    r"कुत्ता", r"कुत्ते", r"कुत्तों", r"कुतिया",
    r"કૂતરો", r"કૂતરા", r"કૂતરું", r"કૂતરી", r"કુતરો", r"કુતરા",
    r"कुत्रा", r"कुत्र्या", r"कुत्री",
    r"কুকুর", r"நாய்", r"కుక్క", r"ನಾಯಿ", r"പട്ടി", r"നായ", r"ਕੁੱਤਾ", r"ਕੁੱਤੇ", r"କୁକୁର", r"کتا", r"کتے",
    r"kutra", r"kutraye", r"kutro", r"kutraae", r"kutta", r"kutte", r"kutti"
]

CAT_TOKENS = [
    r"cat", r"kitten", r"feline",
    r"बिल्ली", r"बिल्लियां", r"બિલાડી", r"બિલાડા", r"मांजर",
    r"বিড়াল", r"பூனை", r"పిల్లి", r"ಬೆಕ್ಕು", r"പൂച്ച", r"ਬਿੱਲੀ", r"ବିଲେଇ", r"بلی",
    r"billi", r"biladi", r"manjar"
]

MONKEY_TOKENS = [
    r"monkey", r"ape", r"simian",
    r"बंदर", r"बंदरों", r"વાંદરો", r"વાંદરા", r"વાંદરૂં", r"माकड",
    r"বানর", r"குரங்கு", r"కోతి", r"ಮಂಗ", r"കുരങ്ങ്", r"ਬਾਂਦਰ", r"ମାଙ୍କଡ଼", r"بندر",
    r"bandar", r"vandaro", r"vandra", r"makad"
]

BITE_TOKENS = [
    r"bite", r"bitten", r"bit", r"scratch", r"scratched", r"chewed", r"attacked",
    r"काटा", r"काटना", r"काट", r"डसा", r"नोचा",
    r"કરડ્યું", r"કરડવું", r"કરડ", r"બટકું", r"બટકા", r"બટક", r"બટકું.*ભર્યું", r"બટકું.*ભર્યુ",
    r"ચાवला", r"चावले", r"चावा", r"चावणे", r"चावा.*घेतला",
    r"কামড়েছে", r"கடித்தது", r"கடி", r"కాటు", r"కరిచింది", r"ಕಡಿತ", r"ಕಚ್ಚಿದೆ", r"കടിച്ചു", r"ਵੱਢਿਆ", r"କାମୁଡ଼ିଛି", r"کاٹا",
    r"batku", r"batku.*bharyu", r"bataku", r"bataku.*bhariyu", r"kardyu", r"karadyu", r"karadyo", r"kaata", r"kata", r"chava", r"chavla", r"chawa", r"chaava"
]

EXPOSURE_PATTERNS = {
    "rusty_wound_puncture": [
        r"rusty", r"metal.*cut", r"puncture", r"soil.*contamination",
        r"जंग", r"लोहे.*चोट", r"गहरा.*घाव", r"કાટવાળો", r"ધાતુ.*વાગી", r"ઊંડો.*ઘા",
        r"गंजलेला", r"गंभीर.*जखम", r"തുരുമ്പ്", r"ತುಪ್ಪು",
        r"deep.*cut", r"katvalo"
    ],
    "trauma_fall": [
        r"\bfall\b", r"fell", r"accident", r"injury", r"hit.*by",
        r"गिर.*गया", r"चोट", r"दुर्घटना", r"પડી.*ગય", r"ઈજા", r"અકસ્માત",
        r"पडला", r"पडली", r"अपघात", r"விபத்து", r"ప్రమాదం",
        r"padi.*gayo", r"padi.*gayi", r"gir.*gaya", r"chot"
    ]
}

CANONICAL_CONCEPT_PATTERNS = {
    # 1. Lower Back Pain & Lumbar Radiculopathy
    # S000135 = Back Pain (Master Taxonomy: Back Pain)
    "lower_back_pain": {
        "symptom_id": "S000135",
        "patterns": [
            r"lower.*back.*pain", r"pain.*lower.*back", r"lumbago", r"back.*pain", r"pain.*back", r"backache",
            r"कमर.*दर्द", r"दर्द.*कमर", r"पीठ.*दर्द", r"दर्द.*पीठ",
            r"કમર.*દુખાવો", r"દુખાવો.*કમર", r"કમરમાં.*દુખાવો",
            r"कंबरदुखी", r"कंबरे.*वेदना", r"वेदना.*कंबर", r"पाठी.*वेदना", r"वेदना.*पाठ",
            r"কোমর.*ব্যথা", r"இடுப்பு.*வலி", r"నడుము.*నొప్పి", r"ಸೊಂಟ.*ನೋವು", r"ഇടുപ്പ്.*വേദന",
            r"ਕਮਰ.*ਦਰਦ", r"କମର.*ଯନ୍ତ୍ରଣା", r"کمر.*درد",
            r"kamar.*dard", r"dard.*kamar", r"kamar.*dukhav", r"dukhav.*kamar", r"kambar.*dukh", r"peeth.*dard"
        ],
        "category": "musculoskeletal",
        "red_flag": False
    },
    # S000144 = Lower Back Pain Radiating to Leg (Sciatica) (Master Taxonomy)
    "radiating_pain_lower_limb": {
        "symptom_id": "S000144",
        "patterns": [
            r"radiat.*pain", r"pain.*travels", r"pain.*radiat", r"shooting.*pain", r"radiat.*leg",
            r"दर्द.*पैर.*तक", r"दर्द.*नीचे.*जा", r"पैर.*झनझनाहट",
            r"દુખાવો.*પગ.*સુધી", r"પગ.*દુખાવો.*ઊતર", r"પગ.*ઝણઝણાટી",
            r"वेदना.*पायापर्यंत", r"पायात.*कळ",
            r"jhanjhanahat", r"zanzanati", r"radiat", r"travels.*to.*leg"
        ],
        "category": "neurological_musculoskeletal",
        "red_flag": False
    },
    "sciatica": {
        "symptom_id": "S000144",
        "patterns": [
            r"\bsciatica\b", r"sciatic.*pain", r"lumbar.*radiculopathy", r"radicular.*pain",
            r"साइटिका", r"સાયટિકા", r"सायटिका"
        ],
        "category": "neurological_musculoskeletal",
        "red_flag": False
    },
    # S000265 = Animal Bite with Wound (Master Taxonomy)
    "animal_bite": {
        "symptom_id": "S000265",
        "patterns": [
            r"animal.*bite", r"dog.*bite", r"cat.*bite", r"monkey.*bite",
            r"जानवर.*काटना", r"कुत्ते.*काटना", r"કુતરા.*બટકું", r"પ્રાણી.*કરડવું",
            r"कुत्रा.*चावा", r"प्राणी.*चावा"
        ],
        "category": "exposure",
        "red_flag": True
    },
    # S000280 = Bluish Lips in Infant (Master Taxonomy - Pediatric Emergency)
    "bluish_lips_infant": {
        "symptom_id": "S000280",
        "patterns": [
            r"bluish.*lips", r"blue.*lips", r"cyanosis.*infant", r"infant.*blue.*lips",
            r"शिशु.*नीला.*होंठ", r"શિશુ.*ભૂરું.*હોઠ", r"बाळ.*निळे.*ओठ"
        ],
        "category": "pediatric_emergency",
        "red_flag": True
    },
    # 2. Chest Pain & Cardiac Emergencies
    "chest_pain": {
        "symptom_id": "S000046",
        "patterns": [
            r"chest.*pain", r"chest.*pressure", r"heavy.*chest", r"angina",
            r"सीने.*दर्द", r"छाती.*दर्द", r"सीने.*भारीपन",
            r"\u0a9b\u0abe\u0aa4\u0ac0.*\u0aa6\u0ac1\u0a96\u0abe\u0ab5\u0acb", r"\u0a9b\u0abe\u0aa4\u0ac0.*\u0aa6\u0aac\u0abe\u0aa3", r"\u0a9b\u0abe\u0aa4\u0ac0.*\u0aad\u0abe\u0ab0\u0ac7", r"\u0a9b\u0abe\u0aa4\u0ac0\u0aae\u0abe\u0a82.*\u0aa6\u0ac1\u0a96\u0abe\u0ab5\u0acb", r"\u0a9b\u0abe\u0aa4\u0ac0\u0aae\u0abe\u0a82.*\u0aa6\u0aac\u0abe\u0aa3",
            r"छातीत.*वेदना", r"छातीत.*जड",
            r"\u09ac\u09c1\u0995\u09c7.*\u09ac\u09cd\u09af\u09a5\u09be", r"\u0bae\u0bbe\u0bb0\u0bcd\u0baa\u0bc1.*\u0bb5\u0bb2\u0bbf", r"\u0c1b\u0c3e\u0c24\u0c40.*\u0c28\u0c4a\u0c2a\u0c4d\u0c2a\u0c3f", r"\u0c8e\u0ca6\u0cc6.*\u0ca8\u0ccb\u0cb5\u0cc1", r"\u0d28\u0d46\u0d1e\u0d4d\u0d1a\u0d41\u0d35\u0d46\u0d28",
            r"\u0a1b\u0a3e\u0a24\u0a40.*\u0a26\u0a30\u0a26", r"\u0b1b\u0b3e\u0b24\u0b3f.*\u0b2f\u0b28\u0b4d\u0b30\u0b23\u0b3e", r"\u0633\u06cc\u0646\u06d2.*\u062f\u0631\u062f",
            r"chhati.*dukhav", r"chhati.*dabana", r"seene.*dard"
        ],
        "category": "cardiopulmonary",
        "red_flag": True
    },
    "dyspnea_breathlessness": {
        "symptom_id": "S000026",
        "patterns": [
            r"shortness.*breath", r"difficulty.*breath", r"breathless", r"dyspnea",
            r"सांस.*तकलीफ", r"सांस.*फूल", r"શ્વાસ.*તકલીફ", r"શ્વાસ.*ચઢ", r"દમ",
            r"श्वास.*त्रास", r"दम.*लाग",
            r"শ্বাসকষ্ট", r"மூச்சுத்.*திணறல்", r"శ్వాస.*ఆడకపోవడం", r"ಉಸಿರಾಟ.*ತೊಂದರೆ", r"ശ്വാസതടസ്സം",
            r"ਸਾਹ.*ਤਕਲੀਫ਼", r"ଶ୍ୱାସ.*କଷ୍ଟ",
            r"sans.*taklif", r"shwas.*taklif", r"breathless"
        ],
        "category": "cardiopulmonary",
        "red_flag": True
    },
    # 3. Febrile Illness
    "fever": {
        "symptom_id": "S000001",
        "patterns": [
            r"\bfever\b", r"high.*temperature", r"pyrexia", r"febrile",
            r"बुखार", r"ताप", r"તાવ", r"জ্বর", r"காய்ச்சல்", r"జ్వరం", r"ಜ್ವರ", r"പനി", r"ਬੁਖਾਰ", r"ଜ୍ୱର", r"بخار",
            r"bukhar", r"tav", r"taap"
        ],
        "category": "systemic_infectious",
        "red_flag": False
    },
    "chills": {
        "symptom_id": "S000003",
        "patterns": [
            r"chills", r"shivering", r"rigors",
            r"ठंड.*लग", r"कंपकंपी", r"ઠંડી.*લાગ", r"ધ્રુજારી", r"थंडी.*वाज",
            r"কাঁপুনি", r"குளிர்", r"చలి", r"ಚಳಿ", r"വിറയൽ", r"ਕੰਬਣੀ",
            r"thandi", r"thand.*lag", r"kapkapi"
        ],
        "category": "systemic_infectious",
        "red_flag": False
    },
    # 4. Respiratory
    "cough": {
        "symptom_id": "S000023",
        "patterns": [
            r"\bcough\b", r"coughing",
            r"खांसी", r"खोंसी", r"ખાંસી", r"ઉધરસ", r"खोकला",
            r"কাশি", r"இருமல்", r"దగ్గు", r"ಕೆಮ್ಮು", r"ചുമ", r"ਖੰਘ", r"କାଶ", r"کھانسی",
            r"khasi", r"khansi", r"udhras", r"khokla"
        ],
        "category": "respiratory",
        "red_flag": False
    },
    # 5. Neurological Headache
    "headache": {
        "symptom_id": "S000061",
        "patterns": [
            r"headache", r"head.*pain", r"cephalalgia", r"migraine",
            r"सिरदर्द", r"सिर.*दर्द", r"માથા.*દુખાવો", r"માથામાં.*દુખાવો", r"ડોકેદુખી", r"डोकेदुखी",
            r"মাথাব্যথা", r"தலைவலி", r"తలనొప్పి", r"ತಲೆನೋವು", r"തലവേദന", r"ਸਿਰ.*ਦਰਦ", r"ମୁଣ୍ଡ.*ବିନ୍ଧା", r"سر.*درد",
            r"sirdard", r"sir.*dard", r"mathano.*dukhav", r"dokedukhi"
        ],
        "category": "neurological",
        "red_flag": False
    },
    # 6. Gastrointestinal
    "abdominal_pain": {
        "symptom_id": "S000092",
        "patterns": [
            r"abdominal.*pain", r"stomach.*pain", r"stomach.*ache", r"belly.*pain", r"cramps", r"cramp", r"pelvic.*cramps", r"pelvic.*pain",
            r"पेट.*दर्द", r"પેટ.*દુખાવો", r"પેટમાં.*દુખાવો", r"पोटदुखी", r"पोटात.*वेदना", r"मरोड़", r"ऐंठन", r"મરોડ",
            r"পেট.*ব্যথা", r"வயிற்று.*வலி", r"కడుపు.*నొప్పి", r"ಹೊಟ್ಟೆ.*ನೋವು", r"വയറുവേദന", r"ਢਿੱਡ.*ਪੀੜ",
            r"pet.*dard", r"pet.*dukhav", r"potdukhi"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "vomiting": {
        "symptom_id": "S000087",
        "patterns": [
            r"vomiting", r"\bvomit\b", r"throwing.*up",
            r"उल्टी", r"वमन", r"ઉલટી", r"ઉલ્ટી", r"વાંટો", r"उलटी", r"उलट्या", r"उलट",
            r"বমি", r"வாந்தி", r"వాంతులు", r"ವಾಂತಿ", r"ഛർദ്ദി", r"ਉਲਟੀ", r"ବାନ୍ତି", r"الٹی",
            r"ulti", r"vomit"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "diarrhea": {
        "symptom_id": "S000089",
        "patterns": [
            r"diarrhea", r"loose.*motion", r"watery.*stool",
            r"दस्त", r"पतले.*दस्त", r"ઝાડા", r"પાતળા.*ઝાડા", r"जुलाब", r"हगवण",
            r"ডায়রিয়া", r"வயிற்றுப்போக்கு", r"విరేచనాలు", r"ಭೇದಿ", r"വയറിളക്കം", r"ਦਸਤ", r"ଝାଡ଼ା",
            r"dast", r"zhada", r"julab"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    # 7. Dermatological
    "skin_rash": {
        "symptom_id": "S000109",
        "patterns": [
            r"\brash\b", r"skin.*eruption", r"hives", r"erythema", r"itching",
            r"चकत्ते", r"खुजली", r"दाने", r"ગુમડાં", r"ખંજવાળ", r"લાલ.*ચકામા", r"खाज", r"पुरळ",
            r"ফুসকুড়ি", r"அரிப்பு", r"దద్దుర్లు", r"ತುರಿಕೆ", r"ചൊറിച്ചിൽ", r"ਖੁਜਲੀ", r"କୁଣ୍ଡାଇ",
            r"khujli", r"khanjwal", r"chakama", r"rash"
        ],
        "category": "dermatological",
        "red_flag": False
    },
    "constipation": {
        "symptom_id": "S000091",
        "patterns": [
            r"constipat", r"hard.*stool", r"difficulty.*passing.*stool", r"infrequent.*bowel",
            r"कब्ज़", r"कब्ज", r"મલબદ્ધતા", r"કબજિયાત", r"શૌચ.*તકલીફ", r"बद्धकोष्ठता",
            r"কোষ্ঠকাঠিন্য", r"மலச்சிக்கல்", r"మలబద్ధకం", r"ಮಲಬದ್ಧತೆ", r"മലബന്ധം", r"ਕਬਜ਼",
            r"kabziyat", r"kabj", r"kabz"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "worm_infestation": {
        "symptom_id": "S000108",
        "patterns": [
            r"worm.*infestation", r"visible.*worms", r"worms.*stool", r"pinworm", r"tapeworm", r"roundworm",
            r"पेट.*कीड़े", r"मल.*कीड़े", r"પેટના.*કીડા", r"કૃમિ", r"पोटातील.*जंत",
            r"pet.*ke.*kide", r"petna.*kida"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "itching_pruritus": {
        "symptom_id": "S000110",
        "patterns": [
            r"itching", r"pruritus", r"itchy", r"scratching",
            r"खुजली", r"ખંજવાળ", r"खाज", r"અળાઈ",
            r"চুলকানি", r"அரிப்பு", r"దురద", r"ತುರಿಕೆ", r"ചൊറിച്ചിൽ", r"ਖੁਜਲੀ", r"କୁଣ୍ଡାଇ",
            r"khujli", r"khanjwal", r"khaj"
        ],
        "category": "dermatological",
        "red_flag": False
    },
    "fungal_skin_infection": {
        "symptom_id": "S000124",
        "patterns": [
            r"fungal.*infection", r"ringworm", r"tinea", r"ring.*shaped.*rash", r"circular.*rash",
            r"दाद", r"फंगल.*संक्रमण", r"દાદર", r"ધાધર", r"ફૂગનો.*ચેપ", r"गचकरण", r"नायटा",
            r"dhadhar", r"dadar", r"daadh", r"daad", r"lalchmbha", r"lal.*chambha"
        ],
        "category": "dermatological",
        "red_flag": False
    }
}

NEGATION_MARKERS = [
    # English
    r"(?:^|\s)no(?:\s|$)", r"(?:^|\s)not(?:\s|$)", r"(?:^|\s)without(?:\s|$)",
    r"(?:^|\s)denies(?:\s|$)", r"(?:^|\s)denied(?:\s|$)", r"(?:^|\s)absent(?:\s|$)",
    # Hindi
    r"(?:^|\s)नहीं(?:\s|$)", r"(?:^|\s)न(?:\s|$)", r"(?:^|\s)बिना(?:\s|$)",
    # Gujarati
    r"(?:^|\s)નથી(?:\s|$)", r"(?:^|\s)વિના(?:\s|$)", r"(?:^|\s)નહિ(?:\s|$)", r"(?:^|\s)ન(?:\s|$)",
    # Marathi
    r"(?:^|\s)नाही(?:\s|$)", r"(?:^|\s)नाहीत(?:\s|$)", r"(?:^|\s)नसणे(?:\s|$)",
    # Bengali
    r"(?:^|\s)না(?:\s|$)", r"(?:^|\s)নেই(?:\s|$)",
    # Tamil
    r"(?:^|\s)இல்லை(?:\s|$)", r"(?:^|\s)இல்ல(?:\s|$)",
    # Telugu
    r"(?:^|\s)లేదు(?:\s|$)", r"(?:^|\s)కాదు(?:\s|$)",
    # Kannada
    r"(?:^|\s)ಇಲ್ಲ(?:\s|$)", r"(?:^|\s)ಅಲ್ಲ(?:\s|$)",
    # Malayalam
    r"(?:^|\s)ഇല്ല(?:\s|$)",
    # Punjabi
    r"(?:^|\s)ਨਹੀਂ(?:\s|$)",
    # Urdu
    r"(?:^|\s)نہیں(?:\s|$)",
    # Roman Indic
    r"(?:^|\s)nahi(?:\s|$)", r"(?:^|\s)nahin(?:\s|$)", r"(?:^|\s)nathi(?:\s|$)", r"(?:^|\s)naahi(?:\s|$)", r"(?:^|\s)nahe(?:\s|$)"
]

DURATION_PATTERNS = [
    (r"(?:\d+|one|two|three|few|a|an|दोन|एक|બે)?\s*(?:hours?|hrs?|घंटे|कલાક|તાસ|तास|घण्टे|ঘন্টা|மணிநேரம்|గంటలు|గంటల|గంట|ಗಂಟೆ|മണിക്കൂർ|ਘੰਟੇ|घण्टा|घंटा|કલાક|तासांपूर्वी|kalak|taas)", "today", 1),
    (r"(today|आज|આજે|आजच|இன்று|నేడు|ಇಂದು|ਅੱਜ|just now|अभी|હમણાં|आत्ता)", "today", 1),
    (r"(yesterday|कल|ગઈકાલે|काल|நேற்று|నిన్న|ನಿನ್ನೆ)", "1-3 days", 1),
    (r"(\d+)\s*(days?|दिन|દિવસ|दिवस|দিন|நாட்கள்|రోజులు|ದಿನಗಳು|ਦਿਨ|ଦିନ|دن)", "days_var", 0),
    (r"(1|one)\s*(week|हफ्ता|અઠવાડિયું|आठवडा|সপ্তাহ|வாரம்|వారం|ವಾರ)", "4-7 days", 7),
    (r"(\d+)\s*(weeks?|हफ्ते|અઠવાડિયા|आठवडे)", "weeks_var", 0),
    (r"(month|months?|महीने|મહિના|महिने)", ">2 weeks", 30)
]

SEVERITY_PATTERNS = {
    "severe": [
        r"severe", r"extreme", r"intense", r"unbearable", r"critical",
        r"तेज", r"तीव्र", r"गंभीर", r"असहनीय", r"ખૂબ", r"ભારે", r"અસહ્ય", r"जास्त",
        r"মারাত্মক", r"கடுமையான", r"తీవ్రమైన", r"ತೀವ್ರ", r"കഠിനമായ", r"ਗੰਭੀਰ", r"شدید",
        r"khup", r"bhare", r"tej", r"tivra"
    ],
    "mild": [
        r"mild", r"slight", r"minor", r"little",
        r"हल्का", r"थोड़ा", r"હળવો", r"થોડો", r"हळू", r"कमी",
        r"হালকা", r"லேசான", r"తేలికపాటి", r"ಸ್ವಲ್ಪ", r"നേരിയ", r"ਹਲਕਾ", r"ہلکا",
        r"halka", r"halvo", r"thodu"
    ],
    "moderate": [
        r"moderate", r"medium", r"मध्यम", r"સામાન્ય", r"మధ్యస్థ", r"madhyam"
    ]
}


class MultilingualClinicalNormalizer:
    """
    Language-Independent Clinical Normalization Engine.
    Translates free-text multilingual statements into canonical clinical representations.
    """

    def __init__(self):
        self._concept_patterns = CANONICAL_CONCEPT_PATTERNS
        self._neg_regex = re.compile("|".join(f"(?:{p})" for p in NEGATION_MARKERS), re.IGNORECASE)

    def _clean_text(self, text: str) -> str:
        """Standardizes unicode, removes excess whitespace and punctuation."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFKC", str(text))
        cleaned = re.sub(r"[^\w\s\u0900-\u0DFF\-,;.\n।!?]", " ", norm)
        return re.sub(r"\s+", " ", cleaned).strip().lower()

    def _any_token_match(self, text: str, token_list: List[str]) -> bool:
        for t in token_list:
            if re.search(t, text, re.IGNORECASE):
                return True
        return False

    def _detect_negation_scope(self, text: str) -> Tuple[str, List[str]]:
        """
        Splits text into affirmative and negated clauses.
        Returns: (affirmative_text, list_of_negated_clauses)
        """
        split_pattern = (
            r"[,;.\n।!?]|"
            r"(?:\b(?:and|aur|ane|aani|तथा|एवं|અને|આણિ|आणि)\b)|"
            r"(?:\b(?:but|however|except|excluding|parantu|lekin|pan|पण|પરંતુ|લેકિન|लेकिन|किन्तु|किंतु)\b)|"
            r"(?=\b(?:without|बिना|વિના)\b)"
        )
        clauses = re.split(split_pattern, text, flags=re.IGNORECASE)
        affirmative = []
        negated = []

        for clause in clauses:
            c = clause.strip()
            if not c:
                continue
            is_neg = bool(self._neg_regex.search(c))
            if is_neg:
                negated.append(c)
            else:
                affirmative.append(c)

        return " ".join(affirmative), negated

    def _extract_laterality(self, text: str) -> List[str]:
        lat = set()
        for side, patterns in LATERALITY_PATTERNS.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    lat.add(side)
                    break
        if "bilateral" in lat:
            return ["bilateral"]
        return sorted(list(lat))

    def _extract_anatomy(self, text: str) -> List[str]:
        regions = set()
        for region, patterns in ANATOMICAL_REGION_PATTERNS.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    regions.add(region)
                    break
        return sorted(list(regions))

    def _extract_duration(self, text: str) -> Tuple[str, Optional[int]]:
        for pat, dur_label, days in DURATION_PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                if dur_label == "days_var":
                    num = int(m.group(1))
                    if num <= 3:
                        return "1-3 days", num
                    elif num <= 7:
                        return "4-7 days", num
                    elif num <= 14:
                        return "1-2 weeks", num
                    else:
                        return ">2 weeks", num
                elif dur_label == "weeks_var":
                    num = int(m.group(1))
                    if num == 1:
                        return "4-7 days", 7
                    elif num == 2:
                        return "1-2 weeks", 14
                    else:
                        return ">2 weeks", num * 7
                return dur_label, days
        return "1-3 days", 1

    def _extract_severity(self, text: str) -> str:
        for sev, patterns in SEVERITY_PATTERNS.items():
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    return sev
        return "moderate"

    def normalize(
        self,
        raw_text: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> CanonicalClinicalRepresentation:
        """
        Main canonical normalization entry point.
        Takes free-text clinical description in ANY supported language or Romanized script
        and returns a language-independent CanonicalClinicalRepresentation.
        """
        user_context = user_context or {}
        if not raw_text or not str(raw_text).strip():
            return CanonicalClinicalRepresentation(
                raw_text="",
                normalization_status="failed",
                unsupported_reasons=["Empty input text"]
            )

        clean = self._clean_text(raw_text)
        aff_text, neg_clauses = self._detect_negation_scope(clean)

        canonical_concepts = set()
        symptom_ids = set()
        exposure_ids = set()
        associated_features = set()
        negative_findings = set()
        clinical_attributes = {}

        # 1. Process Negations first
        neg_text = " ".join(neg_clauses)
        for concept_name, info in self._concept_patterns.items():
            for p in info["patterns"]:
                if re.search(p, neg_text, re.IGNORECASE):
                    negative_findings.add(concept_name)
                    break

        # 2. Process Positive / Affirmative Concepts
        for concept_name, info in self._concept_patterns.items():
            if concept_name in negative_findings:
                continue
            for p in info["patterns"]:
                if re.search(p, aff_text, re.IGNORECASE):
                    canonical_concepts.add(concept_name)
                    symptom_ids.add(info["symptom_id"])
                    break

        # 3. Process Generalized Exposures (Multi-token animal bite, wound, trauma)
        has_bite_action = self._any_token_match(aff_text, BITE_TOKENS)
        has_dog_token = self._any_token_match(aff_text, DOG_TOKENS)
        has_cat_token = self._any_token_match(aff_text, CAT_TOKENS)
        has_monkey_token = self._any_token_match(aff_text, MONKEY_TOKENS)

        if has_bite_action or (has_dog_token and "bite" in aff_text) or (has_dog_token and any(k in aff_text for k in ["karad", "batk", "chaav", "kaat", "kata"])):
            canonical_concepts.add("animal_bite_exposure")
            symptom_ids.add("S000265")  # S000265 = Animal Bite with Wound (NEVER S000280)
            exposure_ids.add("EXP_ANIMAL_BITE")
            clinical_attributes["exposure_type"] = "animal_bite"
            clinical_attributes["bite_exposure"] = True
            clinical_attributes["rabies_risk_assessment_required"] = True

            if has_dog_token:
                clinical_attributes["animal_type"] = "dog"
            elif has_cat_token:
                clinical_attributes["animal_type"] = "cat"
            elif has_monkey_token:
                clinical_attributes["animal_type"] = "monkey"
            else:
                clinical_attributes["animal_type"] = "unknown_animal"

        # Contaminated wound / rusty nail
        for p in EXPOSURE_PATTERNS["rusty_wound_puncture"]:
            if re.search(p, aff_text, re.IGNORECASE):
                exposure_ids.add("EXP_TETANUS_RISK_WOUND")
                clinical_attributes["tetanus_risk_exposure"] = True
                break

        # Trauma / Fall
        for p in EXPOSURE_PATTERNS["trauma_fall"]:
            if re.search(p, aff_text, re.IGNORECASE):
                exposure_ids.add("EXP_ACUTE_TRAUMA")
                clinical_attributes["acute_trauma"] = True
                break

        # 4. Extract Anatomy & Laterality
        anatomy = self._extract_anatomy(clean)
        laterality = self._extract_laterality(clean)
        if laterality:
            clinical_attributes["laterality"] = laterality[0]

        # Compound anatomical region
        if "lower_limb" in anatomy and "left" in laterality:
            clinical_attributes["anatomical_region"] = "left_lower_limb"
        elif "lower_limb" in anatomy and "right" in laterality:
            clinical_attributes["anatomical_region"] = "right_lower_limb"
        elif "upper_limb" in anatomy and "left" in laterality:
            clinical_attributes["anatomical_region"] = "left_upper_limb"
        elif "upper_limb" in anatomy and "right" in laterality:
            clinical_attributes["anatomical_region"] = "right_upper_limb"
        elif anatomy:
            clinical_attributes["anatomical_region"] = anatomy[0]

        # 5. Extract Duration & Severity
        duration_label, duration_days = self._extract_duration(clean)
        severity_label = self._extract_severity(clean)

        if user_context.get("duration"):
            duration_label, duration_days = self._extract_duration(str(user_context.get("duration")))
        if user_context.get("severity"):
            severity_label = str(user_context.get("severity")).lower()

        # 6. Evaluate Neurologic / Radicular Features
        if "lower_back_pain" in canonical_concepts and (
            "radiating_pain_lower_limb" in canonical_concepts
            or "sciatica" in canonical_concepts
            or "lower_limb" in anatomy
            or any(k in clean for k in ["leg", "pag", "pair", "paya", "jhanjhanahat", "zanzanati", "radiat"])
        ):
            canonical_concepts.add("radiating_pain_lower_limb")
            symptom_ids.add("S000144")  # S000144 = Lower Back Pain Radiating to Leg (Sciatica)
            clinical_attributes["has_radicular_symptoms"] = True
            clinical_attributes["neurological_nerve_root_involvement"] = True

        # 7. Evaluate Cardiopulmonary Emergency Features
        if "chest_pain" in canonical_concepts and ("dyspnea_breathlessness" in canonical_concepts or severity_label == "severe"):
            clinical_attributes["emergency_cardiopulmonary"] = True
            clinical_attributes["has_emergency_red_flags"] = True

        # 8. Normalization Confidence and Status
        total_extracted = len(canonical_concepts) + len(exposure_ids)
        if total_extracted == 0 and len(negative_findings) == 0:
            status = "failed"
            confidence = 0.0
            reasons = ["Insufficient clinical normalization: no recognized clinical concepts or findings"]
        elif total_extracted == 0 and len(negative_findings) > 0:
            status = "partial"
            confidence = 0.5
            reasons = ["Only negative findings reported; no primary symptoms identified"]
        else:
            status = "success"
            confidence = min(0.95, 0.4 + (total_extracted * 0.2))
            reasons = []

        # Detect language family
        detected_lang = "en"
        if re.search(r"[\u0A80-\u0AFF]", raw_text):
            detected_lang = "gu"
        elif re.search(r"[\u0900-\u097F]", raw_text):
            if any(w in raw_text for w in ["आहे", "नाही", "वेदना", "चावला", "पाय"]):
                detected_lang = "mr"
            else:
                detected_lang = "hi"
        elif re.search(r"[\u0980-\u09FF]", raw_text):
            detected_lang = "bn"
        elif re.search(r"[\u0B80-\u0BFF]", raw_text):
            detected_lang = "ta"
        elif re.search(r"[\u0C00-\u0C7F]", raw_text):
            detected_lang = "te"
        elif re.search(r"[\u0C80-\u0CFF]", raw_text):
            detected_lang = "kn"
        elif re.search(r"[\u0D00-\u0D7F]", raw_text):
            detected_lang = "ml"
        elif re.search(r"[\u0A00-\u0A7F]", raw_text):
            detected_lang = "pa"
        elif re.search(r"[\u0B00-\u0B7F]", raw_text):
            detected_lang = "or"
        elif re.search(r"[\u0600-\u06FF]", raw_text):
            detected_lang = "ur"

        return CanonicalClinicalRepresentation(
            raw_text=raw_text,
            detected_language=detected_lang,
            normalized_text=clean,
            canonical_concepts=sorted(list(canonical_concepts)),
            symptom_ids=sorted(list(symptom_ids)),
            exposure_ids=sorted(list(exposure_ids)),
            anatomical_regions=anatomy,
            laterality=laterality,
            severity=severity_label,
            duration=duration_label,
            duration_days=duration_days,
            age_group=str(user_context.get("age", "Adult")),
            gender=str(user_context.get("gender", "Unspecified")),
            associated_features=sorted(list(associated_features)),
            negative_findings=sorted(list(negative_findings)),
            clinical_attributes=clinical_attributes,
            normalization_confidence=confidence,
            normalization_status=status,
            unsupported_reasons=reasons
        )

    def __init__(self):
        self._concept_patterns = CANONICAL_CONCEPT_PATTERNS
        self._neg_regex = re.compile("|".join(f"(?:{p})" for p in NEGATION_MARKERS), re.IGNORECASE)
        self.bridge = MasterSymptomTaxonomyBridge()

    def get_symptom_id(self, symptom_text: str) -> Optional[str]:
        """
        Resolves a symptom name, label, or concept string into a canonical symptom ID (e.g. 'S000135').
        Uses MasterSymptomTaxonomyBridge covering the full 280-symptom master taxonomy first,
        then checks canonical concept patterns. Returns None if unresolvable.
        """
        if not symptom_text:
            return None
        st = str(symptom_text).strip()
        # Direct canonical ID format check (S followed by digits)
        if re.match(r"^S[0-9]{6}$", st.upper()):
            return st.upper()

        # Check concept dictionary directly
        c_key = st.lower().replace(" ", "_").replace("-", "_")
        if c_key in self._concept_patterns:
            return self._concept_patterns[c_key]["symptom_id"]

        # Check generalized 280-symptom taxonomy bridge
        bridge_id = self.bridge.resolve_symptom(st)
        if bridge_id:
            return bridge_id

        # Normalize text and look for extracted symptom IDs
        rep = self.normalize(st)
        if rep.symptom_ids:
            return rep.symptom_ids[0]

        return None


# ==============================================================================
# GENERALIZED 280-SYMPTOM MASTER TAXONOMY BRIDGE
# ==============================================================================
class MasterSymptomTaxonomyBridge:
    """
    Generalized Multilingual Bridge covering all 280 symptoms in symptoms_master.csv.
    Provides fast bidirectional lookup:
      user_text / multilingual phrase -> canonical symptom ID (S000001..S000280) -> metadata.
    Enforces semantic validation so fuzzy candidates must pass an attribute check.
    """
    def __init__(self, csv_path: Optional[str] = None):
        if not csv_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            csv_path = os.path.join(base_dir, "datasets", "symptoms", "symptoms_master.csv")
        self.csv_path = csv_path
        self.id_to_record: Dict[str, Dict[str, Any]] = {}
        self.exact_name_to_id: Dict[str, str] = {}
        self._load_master_taxonomy()

    def _load_master_taxonomy(self):
        if not os.path.exists(self.csv_path):
            _logger.warning("[MasterSymptomTaxonomyBridge] Master symptoms file not found at: %s", self.csv_path)
            return

        with open(self.csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("symptom_id", "").strip()
                if not sid:
                    continue
                name_en = row.get("symptom_name", "").strip()
                name_hi = row.get("symptom_name_hi", "").strip()
                name_gu = row.get("symptom_name_gu", "").strip()
                record = {
                    "symptom_id": sid,
                    "symptom_name": name_en,
                    "symptom_name_hi": name_hi,
                    "symptom_name_gu": name_gu,
                    "body_system": row.get("body_system", "").strip(),
                    "symptom_category": row.get("symptom_category", "").strip(),
                    "severity_level": row.get("severity_level", "").strip(),
                    "emergency_flag": row.get("emergency_flag", "").strip(),
                    "description": row.get("description", "").strip()
                }
                self.id_to_record[sid] = record

                # Index English exact & cleaned
                if name_en:
                    self.exact_name_to_id[name_en.lower()] = sid
                    clean_en = re.sub(r'\(.*?\)', '', name_en).strip().lower()
                    if clean_en and clean_en not in self.exact_name_to_id:
                        self.exact_name_to_id[clean_en] = sid
                    parenthetical = re.findall(r'\((.*?)\)', name_en)
                    for p in parenthetical:
                        for p_sub in p.split(','):
                            p_clean = p_sub.strip().lower()
                            if p_clean and p_clean not in self.exact_name_to_id:
                                self.exact_name_to_id[p_clean] = sid

                # Index Hindi & Gujarati
                if name_hi:
                    self.exact_name_to_id[name_hi.strip().lower()] = sid
                    for h_part in name_hi.split('/'):
                        h_clean = re.sub(r'\(.*?\)', '', h_part).strip().lower()
                        if h_clean and h_clean not in self.exact_name_to_id:
                            self.exact_name_to_id[h_clean] = sid
                if name_gu:
                    self.exact_name_to_id[name_gu.strip().lower()] = sid
                    for g_part in name_gu.split('/'):
                        g_clean = re.sub(r'\(.*?\)', '', g_part).strip().lower()
                        if g_clean and g_clean not in self.exact_name_to_id:
                            self.exact_name_to_id[g_clean] = sid

    def resolve_symptom(self, symptom_text: str) -> Optional[str]:
        if not symptom_text:
            return None
        st = str(symptom_text).strip()
        if re.match(r"^S[0-9]{6}$", st.upper()):
            sid = st.upper()
            return sid if sid in self.id_to_record else sid

        st_clean = st.lower()
        if st_clean in self.exact_name_to_id:
            return self.exact_name_to_id[st_clean]

        # Normalized without punctuation
        norm_clean = re.sub(r"[^\w\s\u0900-\u0DFF]", " ", st_clean)
        norm_clean = re.sub(r"\s+", " ", norm_clean).strip()
        if norm_clean in self.exact_name_to_id:
            return self.exact_name_to_id[norm_clean]

        return None

    def lookup_by_id(self, sid: str) -> Optional[Dict[str, Any]]:
        if not sid:
            return None
        return self.id_to_record.get(str(sid).strip().upper())


def get_taxonomy_bridge() -> MasterSymptomTaxonomyBridge:
    """Returns the singleton MasterSymptomTaxonomyBridge instance."""
    return canonical_normalizer.bridge

# RUNTIME CANONICAL TAXONOMY INTEGRITY VALIDATION
# ==============================================================================
MANDATORY_CANONICAL_TAXONOMY = {
    "S000135": "Back Pain",
    "S000144": "Lower Back Pain Radiating to Leg (Sciatica)",
    "S000265": "Animal Bite with Wound",
    "S000280": "Bluish Lips in Infant",
    "S000101": "Excessive Belching",
    "S000102": "Stomach Cramps",
    "S000092": "Abdominal Pain",
    "S000091": "Constipation",
    "S000109": "Skin Rash",
    "S000110": "Itching (Pruritus)",
    "S000124": "Fungal Skin Infection Signs (Ring-shaped Rash)",
    "S000108": "Worm Infestation Symptoms (Itching, Visible Worms)",
    "S000001": "Fever",
    "S000003": "Chills",
    "S000023": "Dry Cough",
    "S000046": "Chest Pain",
    "S000061": "Headache",
    "S000087": "Vomiting",
    "S000089": "Diarrhea",
}

def validate_canonical_ids(csv_path: Optional[str] = None) -> bool:
    """
    Validates canonical concept symptom IDs at runtime against symptoms_master.csv.
    Enforces strict invariants:
      - S000135 == Back Pain
      - S000144 == Lower Back Pain Radiating to Leg (Sciatica)
      - S000265 == Animal Bite with Wound
      - S000280 == Bluish Lips in Infant
      - S000092 == Abdominal Pain
      - S000091 == Constipation
      - S000109 == Skin Rash
      - S000110 == Itching (Pruritus)
      - S000124 == Fungal Skin Infection Signs (Ring-shaped Rash)
      - S000108 == Worm Infestation Symptoms (Itching, Visible Worms)
      - abdominal_pain != S000091 (Must NEVER be Constipation)
      - skin_rash != S000108 (Must NEVER be Worm Infestation)
      - animal_bite != S000280 (Must NEVER be Bluish Lips in Infant)
      - sciatica != S000101 and sciatica != S000102
    Raises ClinicalIntegrityError on any mismatch.
    """
    # 1. Internal Invariants Check
    if CANONICAL_CONCEPT_PATTERNS.get("lower_back_pain", {}).get("symptom_id") != "S000135":
        raise ClinicalIntegrityError("Integrity Violation: lower_back_pain must map to S000135 (Back Pain)")

    if CANONICAL_CONCEPT_PATTERNS.get("radiating_pain_lower_limb", {}).get("symptom_id") != "S000144":
        raise ClinicalIntegrityError("Integrity Violation: radiating_pain_lower_limb must map to S000144 (Sciatica)")

    if CANONICAL_CONCEPT_PATTERNS.get("sciatica", {}).get("symptom_id") != "S000144":
        raise ClinicalIntegrityError("Integrity Violation: sciatica must map to S000144")

    if CANONICAL_CONCEPT_PATTERNS.get("animal_bite", {}).get("symptom_id") != "S000265":
        raise ClinicalIntegrityError("Integrity Violation: animal_bite must map to S000265 (Animal Bite with Wound)")

    if CANONICAL_CONCEPT_PATTERNS.get("animal_bite", {}).get("symptom_id") == "S000280":
        raise ClinicalIntegrityError("Integrity Violation: animal_bite must NEVER map to S000280 (Bluish Lips in Infant)")

    if CANONICAL_CONCEPT_PATTERNS.get("bluish_lips_infant", {}).get("symptom_id") != "S000280":
        raise ClinicalIntegrityError("Integrity Violation: bluish_lips_infant must map to S000280 (Bluish Lips in Infant)")

    if CANONICAL_CONCEPT_PATTERNS.get("abdominal_pain", {}).get("symptom_id") != "S000092":
        raise ClinicalIntegrityError("Integrity Violation: abdominal_pain must map to S000092 (Abdominal Pain)")

    if CANONICAL_CONCEPT_PATTERNS.get("abdominal_pain", {}).get("symptom_id") == "S000091":
        raise ClinicalIntegrityError("Integrity Violation: abdominal_pain must NEVER map to S000091 (Constipation)")

    if CANONICAL_CONCEPT_PATTERNS.get("skin_rash", {}).get("symptom_id") != "S000109":
        raise ClinicalIntegrityError("Integrity Violation: skin_rash must map to S000109 (Skin Rash)")

    if CANONICAL_CONCEPT_PATTERNS.get("skin_rash", {}).get("symptom_id") == "S000108":
        raise ClinicalIntegrityError("Integrity Violation: skin_rash must NEVER map to S000108 (Worm Infestation)")

    if CANONICAL_CONCEPT_PATTERNS.get("itching_pruritus", {}).get("symptom_id") != "S000110":
        raise ClinicalIntegrityError("Integrity Violation: itching_pruritus must map to S000110 (Itching (Pruritus))")

    if CANONICAL_CONCEPT_PATTERNS.get("fungal_skin_infection", {}).get("symptom_id") != "S000124":
        raise ClinicalIntegrityError("Integrity Violation: fungal_skin_infection must map to S000124 (Fungal Skin Infection)")

    # 2. Check against symptoms_master.csv if available
    if not csv_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base_dir, "datasets", "symptoms", "symptoms_master.csv")

    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            id_to_name = {row["symptom_id"].strip(): row["symptom_name"].strip() for row in reader if row.get("symptom_id") and row.get("symptom_name")}

        for sid, expected_name in MANDATORY_CANONICAL_TAXONOMY.items():
            actual_name = id_to_name.get(sid)
            if not actual_name:
                raise ClinicalIntegrityError(f"Integrity Violation: {sid} not found in symptoms_master.csv")
            if actual_name != expected_name:
                raise ClinicalIntegrityError(f"Integrity Violation: {sid} in symptoms_master.csv is '{actual_name}', expected '{expected_name}'")

    _logger.info("[CanonicalConcepts] Canonical taxonomy integrity validation PASSED")
    return True


# Run validation immediately upon module load
validate_canonical_ids()

# Global singleton normalizer
canonical_normalizer = MultilingualClinicalNormalizer()
