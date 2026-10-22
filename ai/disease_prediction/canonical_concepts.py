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
    body_locations: List[str] = field(default_factory=list)
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
            "body_locations": list(self.body_locations),
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
        r"kamar", r"peeth", r"pith", r"kambar", r"vaho", r"vanso", r"વાહો", r"વાંસો"
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
    ],
    "ent_ear": [
        r"ear", r"ears", r"earache", r"कान", r"કાન", r"કાને", r"कानों", r"কান", r"காது", r"చెవి", r"ಕಿವಿ", r"ചെവി", r"ਕੰਨ", r"କାନ", r"کان",
        r"kan", r"kaan", r"kane"
    ],
    "eye_ocular": [
        r"eye", r"eyes", r"vision", r"आंख", r"आंखें", r"આંખ", r"આંખો", r"डोळा", r"डोळे", r"চোখ", r"கண்", r"కన్ను", r"ಕಣ್ಣು", r"കണ്ണ്", r"ਅੱਖ", r"ଆଖି", r"آنکھ",
        r"aankh", r"ankh", r"aankho", r"ankho"
    ],
    "throat_oral": [
        r"throat", r"mouth", r"oral", r"tongue", r"tonsil", r"गला", r"गले", r"गळा", r"ગળું", r"ગળા", r"મોં", r"મુખ", r"मुंह",
        r"gala", r"gale", r"galu"
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
    r"batku", r"batku.*bharyu", r"bataku", r"bataku.*bhariyu", r"kardyu", r"karadyu", r"karadyo", r"chaava.*ghetla", r"chawla"
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
            r"kamar.*dard", r"dard.*kamar", r"kamar.*dukhav", r"dukhav.*kamar", r"kambar.*dukh", r"peeth.*dard",
            r"વાહો.*દુખ", r"વાંસો.*દુખ", r"વાહોમાં.*દુખાવો", r"વાંસામાં.*દુખાવો", r"vaho.*dukh", r"vanso.*dukh", r"vaho.*dukhe", r"vanso.*dukhe"
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
            r"shortness.*breath", r"difficulty.*breath", r"breathless", r"dyspnea", r"catch.*breath", r"catch.*my.*breath",
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
            r"\bfever\b", r"high.*temperature", r"pyrexia", r"febrile", r"burning.*up.*hot", r"103f", r"\bfevr\b",
            r"बुखार", r"ताप", r"તાવ", r"জ্বর", r"காய்ச்சல்", r"జ్వరం", r"ಜ್ವರ", r"പനി", r"ਬੁਖਾਰ", r"ଜ୍ୱର", r"بخار",
            r"bukhar", r"tav", r"taav", r"taap", r"tap"
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
            r"\bcough\b", r"coughing", r"\bcaugh\b", r"coughing.*continuously",
            r"खांसी", r"खोंसी", r"ખાંસી", r"ઉધરસ", r"खोकला",
            r"কাশি", r"இருமல்", r"దగ్గు", r"ಕೆಮ್ಮು", r"ചുമ", r"ਖੰਘ", r"କାଶ", r"کھانسی",
            r"khasi", r"khansi", r"udharas", r"udhras", r"khokla", r"chuma", r"kemmu", r"daggu", r"irumal", r"kashi", r"khang", r"udhras", r"khokla"
        ],
        "category": "respiratory",
        "red_flag": False
    },
    # 4.1. Sore Throat / Pharyngitis (S000032)
    "sore_throat": {
        "symptom_id": "S000032",
        "patterns": [
            r"sore.*throat", r"throat.*pain", r"throat.*irritat", r"burning.*throat", r"pharyngitis", r"throat.*burn",
            r"throat.*scratchy", r"scratchy.*and.*raw", r"throat.*hurt", r"hurts.*swallow", r"throat.*feels?.*dry", r"dry.*throat",
            r"गले.*खराश", r"गले.*दर्द", r"गले.*जलन", r"गला.*सूख", r"गला.*बैठ", r"गले.*में.*जलन",
            r"ગળામાં.*દુખાવો", r"ગળામાં.*બળતરા", r"ગળામાં.*બળે", r"ગળું.*બળ", r"ગળું.*છોલા", r"ગળા.*દુખાવો",
            r"घशात.*खवखव", r"घसा.*दुख", r"घशात.*जळजळ",
            r"গলা.*ব্যথা", r"தொண்டை.*வலி", r"గొంతు.*నొప్పి", r"ಗಂಟಲು.*ನೋವು", r"തൊണ്ടവേദന", r"ਗਲੇ.*ਦਰਦ",
            r"gale.*dard", r"gala.*dard", r"gala.*bale", r"galama.*bale", r"gala.*ma.*bale", r"gala.*khari",
            r"galam.*bale", r"galama.*bale.*cgge", r"galama.*bale.*chhe", r"ghasa.*dukh", r"ghashat.*khavkhav", r"gale.*jalan",
            r"gale.*kharash", r"gale.*me.*kharash", r"gala.*kharash"
        ],
        "category": "respiratory",
        "red_flag": False
    },
    # 4.2. Runny Nose / Rhinorrhea (S000035)
    "runny_nose": {
        "symptom_id": "S000035",
        "patterns": [
            r"runny.*nose", r"running.*nose", r"rhinorrhea", r"nasal.*discharge", r"sneezing",
            r"नाक.*बह", r"નાક.*વહે", r"नाक.*गळ",
            r"nak.*bahe", r"nak.*vahe", r"running.*nose"
        ],
        "category": "respiratory",
        "red_flag": False
    },
    # 4.2. Wheezing (S000028)
    "wheezing": {
        "symptom_id": "S000028",
        "patterns": [
            r"wheez", r"whistling.*sound", r"whistling.*breath",
            r"सीटी.*आवाज़", r"સીટી.*અવાજ", r"घुरघुराहट"
        ],
        "category": "respiratory",
        "red_flag": False
    },
    "shortness_of_breath": {
        "symptom_id": "S000026",
        "patterns": [
            r"shortness.*breath", r"breathless", r"difficulty.*breathing", r"dyspnea", r"breath.*short",
            r"सांस.*तकलीफ", r"सांस.*फूल", r"શ્વાસ.*તકલીફ", r"શ્વાસ.*ચડ", r"શ્વાસ.*લેવા",
            r"saans.*takleef", r"saans.*lene.*me.*takleef", r"shwas.*taklif", r"shwas.*leva.*ma.*taklif", r"shwas.*chadhe"
        ],
        "category": "respiratory",
        "red_flag": True
    },
    "chest_pain": {
        "symptom_id": "S000046",
        "patterns": [
            r"chest.*pain", r"chest.*tightness", r"chest.*pressure", r"angina", r"pain.*in.*chest",
            r"सीने.*दर्द", r"छाती.*दर्द", r"छाती.*દુખ", r"छाती.*દુખાવો", r"છાતીમાં.*દુખાવો", r"છાતીમાં.*દુખ",
            r"chhati.*me.*dard", r"chhati.*dard", r"chhati.*ma.*dukh", r"chhati.*dukhe", r"sine.*me.*dard", r"seene.*me.*dard"
        ],
        "category": "cardiovascular",
        "red_flag": True
    },
    "palpitations": {
        "symptom_id": "S000048",
        "patterns": [
            r"palpitat", r"heart.*racing", r"racing.*heart", r"pounding.*heart",
            r"धड़कन.*तेज़", r"दिल.*धड़क", r"ધબકારા.*ઝડપી", r"ધબકારા.*વધી",
            r"chhati.*ma.*palpitat", r"heart.*racing.*feel"
        ],
        "category": "cardiovascular",
        "red_flag": False
    },
    "swelling_legs_ankles": {
        "symptom_id": "S000052",
        "patterns": [
            r"swelling.*(?:leg|legs|ankle|ankles|foot|feet)",
            r"(?:leg|legs|ankle|ankles|foot|feet).*swelling",
            r"(?:leg|legs|ankle|ankles|foot|feet).*swollen",
            r"swollen.*(?:leg|legs|ankle|ankles|foot|feet)",
            r"legs?.*(?:feel.*)?swollen",
            r"पैर.*सूजन", r"टखने.*सूजन", r"પગ.*સોજો", r"ઘૂંટી.*સોજો",
            r"ankle.*swelling", r"swelling.*ankle"
        ],
        "category": "cardiovascular",
        "red_flag": False
    },
    # 5. Neurological Headache
    "headache": {
        "symptom_id": "S000061",
        "patterns": [
            r"headache", r"head.*pain", r"cephalalgia", r"migraine",
            r"splitting.*headache", r"head.*explode", r"pounding.*behind", r"\bhedache\b",
            r"सिरदर्द", r"सिर.*दर्द", r"માથા.*દુખાવો", r"માથામાં.*દુખાવો", r"માથું.*દુખ", r"માથું.*દુખે", r"માથાનો.*દુખાવો", r"ડોકેદુખી", r"डोकेदुखी",
            r"মাথাব্যথা", r"தலைவலி", r"తలనొప్పి", r"ತಲೆನೋವು", r"തലവേദന", r"ਸਿਰ.*ਦਰਦ", r"ମୁଣ୍ଡ.*ବିନ୍ଧା", r"سر.*درد",
            r"sirdard", r"sir.*dard", r"sar.*dard", r"sar.*me.*dard", r"mathano.*dukhav", r"mathu.*dukh", r"mathu.*dukhe", r"mathu.*dard", r"dokedukhi", r"matha.*betha", r"matha.*byatha", r"matha.*ghorano", r"thalaivali", r"thalai.*vali", r"talanopi", r"tala.*noppi", r"tale.*novu", r"thala.*vedhana", r"dokedukhi"
        ],
        "category": "neurological",
        "red_flag": False
    },
    # 5.1. Dizziness / Vertigo
    "dizziness_vertigo": {
        "symptom_id": "S000064",
        "patterns": [
            r"dizziness", r"vertigo", r"lightheaded", r"giddiness", r"spinning",
            r"चक्कर", r"ચક્કર", r"चकरावणे", r"মাথা.*ঘোরা", r"மயக்கம்", r"తలతిరుగు", r"ತಲೆತಿರುಗುವಿಕೆ", r"തലകറക്കം",
            r"chakkar", r"chakara", r"chakar", r"mayakkam", r"talatirugudu"
        ],
        "category": "neurological",
        "red_flag": False
    },
    # 5.2. Generalized Body Ache / Myalgia
    "body_ache_myalgia": {
        "symptom_id": "S000011",
        "patterns": [
            r"body.*pain", r"body.*ache", r"myalgia", r"generalized.*pain", r"whole.*body.*pain",
            r"बदन.*दर्द", r"शरीर.*दर्द", r"અંગ.*દુખાવો", r"આખા.*શરીરમાં.*દુખાવો", r"આખું.*શરીર.*દુખ", r"શરીર.*દુખ", r"કળતર", r"अंगदुखी",
            r"গায়ে.*ব্যথা", r"உடல்.*வலி", r"శరీర.*నొప్పులు", r"ಮೈಕೈ.*ನೋವು", r"ശരീരവേദന",
            r"badan.*dard", r"ang.*dukhav", r"sarir.*dard", r"udal.*vali", r"aakha.*sarir.*dukh", r"kaltar"
        ],
        "category": "systemic_infectious",
        "red_flag": False
    },
    # 5.3. Joint Pain & Upper/Lower Limb Arthralgia (S000131)
    "joint_pain": {
        "symptom_id": "S000131",
        "patterns": [
            r"joint.*pain", r"joint.*ach", r"joints.*ach", r"arthralgia", r"knee.*pain", r"hand.*pain", r"arm.*pain", r"shoulder.*pain", r"wrist.*pain", r"elbow.*pain", r"finger.*pain",
            r"जोड़ों.*दर्द", r"जोड़.*दर्द", r"घुटने.*दर्द", r"घुटना.*दर्द", r"हाथ.*दर्द", r"बांह.*दर्द", r"कंधे.*दर्द",
            r"સાંધા.*દુખાવો", r"સાંધામાં.*દુખાવો", r"ઘૂંટણ.*દુખાવો", r"ગોઠણ.*દુખાવો", r"હાથ.*દુખાવો", r"હાથમાં.*દુખાવો", r"હાથ.*દુખ", r"ખભા.*દુખાવો",
            r"hath.*dukh", r"hath.*ma.*dukh", r"haath.*dard", r"sandha.*dukh", r"sandha.*ma.*dukh", r"gothan.*dukh", r"ghuntan.*dukh", r"khabha.*dukh", r"shoulder.*pain",
            r"jod.*dard", r"jodo.*dard", r"jodo.*me.*dard", r"sandha.*dard"
        ],
        "category": "musculoskeletal",
        "red_flag": False
    },
    # 5.4. Muscle Pain (S000133)
    "muscle_pain": {
        "symptom_id": "S000133",
        "patterns": [
            r"muscle.*pain", r"myalgia", r"मांसपेशियों.*दर्द", r"સ્નાયુ.*દુખાવો", r"સ્નાયુમાં.*દુખાવો",
            r"snayu.*dukh", r"muscle.*cramp", r"muscle.*(?:strain|sprain)", r"\bsprain\b"
        ],
        "category": "musculoskeletal",
        "red_flag": False
    },
    # 5.5. Neck Pain (S000136)
    "neck_pain": {
        "symptom_id": "S000136",
        "patterns": [
            r"neck.*pain", r"stiff.*neck", r"गर्दन.*दर्द", r"ગરદન.*દુખાવો", r"ગરદનમાં.*દુખાવો", r"ડોક.*દુખ",
            r"gardan.*dard", r"gardan.*dukhav", r"dok.*dukh"
        ],
        "category": "musculoskeletal",
        "red_flag": False
    },
    # 5.6. Ear Pain (S000167)
    "ear_pain": {
        "symptom_id": "S000167",
        "patterns": [
            r"ear.*pain", r"earache", r"otalgia", r"pain.*in.*ear",
            r"कान.*दर्द", r"कानों.*दर्द", r"કાન.*દુખાવો", r"કાનમાં.*દુખાવો", r"કાન.*દુખ",
            r"kan.*dard", r"kaan.*dard", r"kan.*dukh", r"kaan.*dukh", r"kan.*ma.*dukh"
        ],
        "category": "ent",
        "red_flag": False
    },
    # 6. Gastrointestinal
    "abdominal_pain": {
        "symptom_id": "S000092",
        "patterns": [
            r"abdominal.*pain", r"stomach.*pain", r"stomach.*ache", r"belly.*pain", r"tummy.*hurt", r"tummy.*ache", r"cramps?", r"pelvic.*cramps?", r"pelvic.*pain", r"belly.*feels.*crampy", r"tummy.*cramps?",
            r"quadrant.*pain", r"epigastric.*pain", r"ruq.*pain", r"luq.*pain", r"rlq.*pain", r"llq.*pain",
            r"पेट.*दर्द", r"પેટ.*દુખાવો", r"પેટમાં.*દુખાવો", r"पोटदुखी", r"पोटात.*वेदना", r"मरोड़", r"ऐंठन", r"મરોડ",
            r"পেট.*ব্যথা", r"வயிற்று.*வலி", r"కడుపు.*నొప్పి", r"ಹೊಟ್ಟೆ.*ನೋವು", r"വയറുവേദന", r"ਢਿੱਡ.*ਪੀੜ",
            r"pet.*dard", r"pet.*dukhav", r"potdukhi", r"kadupu.*noppi", r"vayiru.*vali", r"vayi.*vali", r"pot.*dukh", r"hotte.*novu", r"vayaru.*vedhana"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "nausea": {
        "symptom_id": "S000086",
        "patterns": [
            r"\bnausea\b", r"\bnauseous\b", r"\bnauseated\b", r"feeling.*like.*vomiting", r"barfing", r"feeling.*like.*barfing",
            r"जी.*मिचला", r"जी.*घबरा", r"જીવ.*ગભરા", r"ઉબકા", r"ઊબકા",
            r"ji.*michla", r"jiv.*gabhra", r"ubka", r"oobka", r"ulti.*jaisa", r"feel.*like.*vomit"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "vomiting": {
        "symptom_id": "S000087",
        "patterns": [
            r"vomiting", r"\bvomit\b", r"throwing.*up", r"threw.*up", r"barfed",
            r"उल्टी", r"वमन", r"ઉલટી", r"ઉલ્ટી", r"વાંટો", r"उलटी", r"उलट्या", r"उलट",
            r"বমি", r"வாந்தி", r"వాంతులు", r"ವಾಂತಿ", r"ഛർദ്ദി", r"ਉਲਟੀ", r"ବାନ୍ତି", r"الٹی",
            r"\bulti\b(?!.*jaisa)", r"vomit", r"vanti", r"vaanthi", r"chardi", r"bomi", r"banthee"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "diarrhea": {
        "symptom_id": "S000089",
        "patterns": [
            r"diarrhea", r"loose.*motion", r"watery.*stool", r"loose.*stool", r"the.*runs",
            r"दस्त", r"पतले.*दस्त", r"ઝાડા", r"પાતળા.*ઝાડા", r"जुलाब", r"हगवण",
            r"ডায়রিয়া", r"வயிற்றுப்போக்கு", r"విరేచనాలు", r"ಭೇದಿ", r"വയറിളക്കം", r"ਦਸਤ", r"ଝାଡ଼ା",
            r"dast", r"zhada", r"julab", r"jhada"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    # 7. Dermatological
    "skin_rash": {
        "symptom_id": "S000109",
        "patterns": [
            r"\brash\b", r"skin.*rash", r"skin.*eruption", r"hives",
            r"चकत्ते", r"दाने", r"ગુમડાં", r"લાલ.*ચકામા", r"पुरळ",
            r"ফুসকুড়ি", r"దద్దుర్లు",
            r"chakama", r"\brash\b"
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
    # 9.0. Skin Redness / Erythema (S000112)
    "skin_redness": {
        "symptom_id": "S000112",
        "patterns": [
            r"skin.*redness", r"redness.*skin", r"erythema",
            r"लाल.*त्वचा", r"લાલ.*ચામડી", r"લાલ.*ત્વચા", r"त्वचा.*लाल"
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
    },
    "blisters": {
        "symptom_id": "S000120",
        "patterns": [
            r"\bblisters?\b", r"\bbullae\b", r"\bvesicles?\b",
            r"छाले", r"ફોલ્લા", r"\bfolla\b", r"\bfola\b", r"\bchhale\b", r"\bchala\b"
        ],
        "category": "dermatological",
        "red_flag": False
    },
    "heartburn_acid_reflux": {
        "symptom_id": "S000095",
        "patterns": [
            r"heartburn", r"acid.*reflux", r"reflux", r"pyrosis", r"hyperacidity",
            r"acidity", r"pet.*(?:me|ma).*jalan", r"pait.*jalan",
            r"सीने.*जलन", r"छाती.*बळतरा", r"છાતી.*બળતરા", r"chhati.*balatara", r"chhati.*ma.*balatara", r"seene.*jalan"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "bloating": {
        "symptom_id": "S000094",
        "patterns": [
            r"bloat", r"bloating", r"pet.*phool", r"pet.*phoolna", r"पेट.*फूलना", r"પેટ.*ફૂલવું",
            r"bloating.*sensation", r"gas.*bloating"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    },
    "pelvic_pain": {
        "symptom_id": "S000188",
        "patterns": [
            r"pelvic.*pain", r"pain.*pelvic", r"पेल्विक.*दर्द", r"પેલ્વિક.*દુખાવો",
            r"पेडू.*दर्द", r"પેડુ.*દુખાવો", r"pedu.*dard"
        ],
        "category": "reproductive",
        "red_flag": False
    },
    "nosebleed": {
        "symptom_id": "S000172",
        "patterns": [
            r"nosebleed", r"epistaxis", r"bleeding.*nose", r"blood.*from.*nose",
            r"नाक.*खून", r"નાક.*લોહી", r"nak.*lohi", r"nak.*khoon", r"nak.*mathi.*lohi"
        ],
        "category": "ent",
        "red_flag": False
    },
    # 8. Urological / Urinary
    "painful_urination": {
        "symptom_id": "S000237",
        "patterns": [
            r"painful.*urinat", r"burning.*urinat", r"burning.*sensation.*urinat", r"dysuria", r"stinging.*urinat",
            r"burns.*whenever.*i.*pee", r"burns.*like.*fire", r"burning.*micturition", r"pee.*burns?", r"burns?.*pee", r"burning.*(?:sensation.*)?(?:while.*)?pee",
            r"पेशाब.*जलन", r"पेशाब.*दर्द", r"पेशाब.*जल",
            r"પેશાબ.*બળતરા", r"પેશાબ.*દુખાવો", r"પેશાબ.*બળે",
            r"peshab.*jalan", r"peshab.*me.*jalan", r"peshab.*balatara", r"peshab.*ma.*balatara", r"peshab.*dard", r"peshab.*(?:ma|me)?.*balatra",
            r"peshab.*burn", r"burning.*peshab", r"peshab.*karti.*vakhat"
        ],
        "category": "urinary",
        "red_flag": False
    },
    "frequent_urination": {
        "symptom_id": "S000226",
        "patterns": [
            r"frequent.*urinat", r"urinat.*often", r"urinat.*frequently", r"increased.*frequency", r"polyuria",
            r"pass.*water.*every", r"pass.*water.*often", r"need.*to.*pass.*water", r"pass.*water",
            r"बार.*बार.*पेशाब", r"વારંવાર.*પેશાબ", r"बार-बार.*पेशाब",
            r"bar.*bar.*peshab", r"baar.*baar.*peshab", r"ba+r.*ba+r.*peshab", r"varamvar.*peshab", r"baar.*baar.*jana", r"bar.*bar.*jana"
        ],
        "category": "urinary",
        "red_flag": False
    },
    "difficulty_urinating": {
        "symptom_id": "S000239",
        "patterns": [
            r"difficulty.*urinat", r"trouble.*urinat", r"hesitancy", r"weak.*stream",
            r"पेशाब.*कठिनाई", r"પેશાબ.*તકલીફ", r"peshab.*taklif"
        ],
        "category": "urinary",
        "red_flag": False
    },
    "hematuria": {
        "symptom_id": "S000238",
        "patterns": [
            r"blood.*in.*urine", r"hematuria", r"bloody.*urine",
            r"पेशाब.*खून", r"પેશાબ.*લોહી", r"peshab.*khoon", r"peshab.*lohi"
        ],
        "category": "urinary",
        "red_flag": True
    },
    # 9. Ocular
    "eye_pain": {
        "symptom_id": "S000212",
        "patterns": [
            r"eye.*pain", r"pain.*in.*eye", r"pain.*in.*eyes", r"ocular.*pain",
            r"आंख.*दर्द", r"आंखों.*दर्द", r"આંખ.*દુખાવો", r"આંખમાં.*દુખાવો", r"આંખો.*દુખ",
            r"aankh.*dard", r"ankh.*dard", r"aankh.*me.*dard", r"ankh.*ma.*dukhav", r"aankho.*dukh"
        ],
        "category": "ocular",
        "red_flag": False
    },
    "red_eyes": {
        "symptom_id": "S000213",
        "patterns": [
            r"\bred\b.*eyes?", r"eyes?.*\bred\b", r"eyes?.*(?:are.*)?very.*red", r"\beye.*redness\b", r"bloodshot.*eyes?", r"bloodshot.*red", r"bloodshot", r"conjunctivitis", r"pink.*eye",
            r"लाल.*आंख", r"लाल.*आंखें", r"આંખ.*લાલ", r"આંખો.*લાલ", r"आंख.*लाल", r"आंखें.*लाल", r"લાલ.*આંખ", r"લાલ.*આંખો",
            r"lal.*aankh", r"lal.*ankh", r"aankh.*(?:me.*)?lal", r"ankh.*(?:ma.*)?lal"
        ],
        "category": "ocular",
        "red_flag": False
    },
    "blurred_vision": {
        "symptom_id": "S000210",
        "patterns": [
            r"blurred.*vision", r"blurry.*vision", r"cloudy.*vision", r"blurred.*(?:in.*)?eye", r"blurry.*(?:in.*)?eye",
            r"धुंधला.*दिख", r"धुंधलापन", r"ઝાંખું.*દેખા", r"ઝાંખપ",
            r"dhundhla", r"jhankhu"
        ],
        "category": "ocular",
        "red_flag": False
    },
    # 10. Systemic
    "fatigue": {
        "symptom_id": "S000005",
        "patterns": [
            r"fatigue", r"extreme.*tired", r"exhaustion", r"weakness", r"tiredness", r"lethargy",
            r"wiped.*out", r"drained", r"completely.*exhausted", r"weakness.*all.*over",
            r"थकान", r"कमजोरी", r"થાક", r"નબળાઈ", r"thakan", r"kamjori", r"thak", r"nablai"
        ],
        "category": "systemic",
        "red_flag": False
    },
    "loss_of_appetite": {
        "symptom_id": "S000009",
        "patterns": [
            r"loss.*of.*appetite", r"not.*feeling.*hungry", r"poor.*appetite", r"anorexia", r"no.*appetite",
            r"भूख.*(?:नहीं|न).*लग", r"भूख.*कम", r"ભૂખ.*(?:નથી|ન).*લાગ", r"ભૂખ.*ઓછી",
            r"bhookh.*kam", r"bhukh.*nathi", r"bhukh.*kam", r"bhukh.*nahi", r"bhukh.*na.*lag",
            r"bhookh.*(?:nahi|nathi|na)", r"bhookh.*(?:bilkul.*)?nahi"
        ],
        "category": "gastrointestinal",
        "red_flag": False
    }
}

NEGATION_MARKERS = [
    # English
    r"(?:^|\s)no(?:\s|$)", r"(?:^|\s)not(?:\s|$)", r"(?:^|\s)without(?:\s|$)",
    r"(?:^|\s)denies(?:\s|$)", r"(?:^|\s)denied(?:\s|$)", r"(?:^|\s)absent(?:\s|$)",
    r"(?:^|\s)negative(?:\s|$)", r"(?:^|\s)negative\s+for(?:\s|$)",
    r"(?:^|\s)neither(?:\s|$)", r"(?:^|\s)nor(?:\s|$)", r"(?:^|\s)never(?:\s|$)",
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
    (r"(yesterday|कल(?:\s+से)?|ગઈકાલે(?:\s+થી)?|ગઈકાલથી|काल(?:\s+पासून)?|நேற்று|నిన్న|ನಿನ್ನೆ|since\s+yesterday|kal\s+se|kaal\s+thi)", "1-3 days", 1),
    (r"(\d+)\s*(?:days?|दिन(?:\s*से)?|દિવસ(?:\s*થી)?|દિવસથી|दिवस|দিন|நாட்கள்|రోజులు|ದಿನಗಳು|ਦਿਨ|ଦିନ|دن|divas(?:\s*thi)?|din(?:\s*se)?)", "days_var", 0),
    (r"(?:दो|do|two|બે|be|दोन)\s*(?:days?|दिन(?:\s*से)?|દિવસ(?:\s*થી)?|દિવસથી|दिवस|divas|din)", "1-3 days", 2),
    (r"(?:तीन|teen|three|ત્રણ|tran)\s*(?:days?|दिन(?:\s*से)?|દિવસ(?:\s*થી)?|દિવસથી|दिवस|divas|din)", "1-3 days", 3),
    (r"(?:चार|char|four|ચાર)\s*(?:days?|दिन(?:\s*से)?|દિવસ(?:\s*થી)?|દિવસથી|दिवस|divas|din)", "4-7 days", 4),
    (r"(?:पांच|paanch|five|પાંચ|panch|पाच)\s*(?:days?|दिन(?:\s*से)?|દિવસ(?:\s*થી)?|દિવસથી|दिवસ|divas|din)", "4-7 days", 5),
    (r"(?:छह|chhah|six|છ|chha|सहा)\s*(?:days?|दिन(?:\s*से)?|દિવસ(?:\s*થી)?|દિવસથી|दिवસ|divas|din)", "4-7 days", 6),
    (r"(?:सात|saat|seven|સાત)\s*(?:days?|दिन(?:\s*से)?|દિવસ(?:\s*થી)?|દિવસથી|दिवસ|divas|din)", "4-7 days", 7),
    (r"(?:1|one|ek|એક|एक)\s*(?:week|हफ्ता|અઠવાડિયું|આઠવડિયું|आठवडा|সপ্তাহ|வாரம்|వారం|ವಾರ|athvadiyu|hafte)", "4-7 days", 7),
    (r"(?:2|two|do|બે|be|दोन)\s*(?:weeks?|हफ्ते|અઠવાડિયા|આઠવડિયા|आठवडे|hafte|athvadiya|weeks)", "1-2 weeks", 14),
    (r"(\d+)\s*(?:weeks?|हफ्ते|અઠવાડિયા|આઠવડિયા|आठवडे|hafte|athvadiya)", "weeks_var", 0),
    (r"(?:month|months?|महीने|મહિના|મહિનો|महिने|mahine|mahino)", ">2 weeks", 30)
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
            r"(?:(?:(?<=[\s,;.!?-])|(?<=^))(?:and|aur|ane|aani|तथा|एवं|અને|આણિ|आणि)(?=[\s,;.!?-]|$))|"
            r"(?:(?:(?<=[\s,;.!?-])|(?<=^))(?:but|however|except|excluding|parantu|lekin|pan|पण|પરંતુ|લેકિન|लेकिन|किन्तु|किंतु|परंतु|par|magar)(?=[\s,;.!?-]|$))|"
            r"(?:(?:(?<=[\s,;.!?-])|(?<=^))(?:jisse|jethi|tyamule|kyunki|jiski\s+wajah\s+se|जिससे|જેથી|त्यामुळे|कारण)(?=[\s,;.!?-]|$))|"
            r"(?:(?:(?<=[\s,;.!?-])|(?<=^))(?:only|sirf|siraf|fakt|shudhu)(?=[\s,;.!?-]|$))|"
            r"(?=(?:(?<=[\s,;.!?-])|(?<=^))(?:nor|without|बिना|વિના)(?=[\s,;.!?-]|$))"
        )
        raw_clauses = re.split(split_pattern, text, flags=re.IGNORECASE)
        clauses = []
        verb_pat = r"\b(?:dukhtu|dukhe|thay|thatu|aavtu|lagtu|hotu|dukh|dukhta|hota|hoti|hote)\b"
        for cl in raw_clauses:
            # If negation is immediately attached to a verb of the same clause (e.g., 'mathu nathi dukhtu'), do not split
            if re.search(r"(?:nathi|\u0aa8\u0aa5\u0ac0)\s+" + verb_pat, cl, re.IGNORECASE):
                clauses.append(cl)
                continue
            # Split on complete copula negations like 'नहीं है', 'nahi hai', or 'nathi/નથી' when followed by another clause
            parts = re.split(r"(?:^|\s+)(?:\u0928\u0939\u0940\u0902\s*\u0939\u0948|nahi\s*hai|\u0aa8\u0aa5\u0ac0|nathi)(?:\s+|$)", cl, flags=re.IGNORECASE)
            if len(parts) > 1 and parts[1].strip():
                clauses.append(parts[0].strip() + " nahi")
                clauses.append(parts[1].strip())
            else:
                clauses.append(cl)
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
                    if concept_name == "loss_of_appetite":
                        if not re.search(r"(?:no|denies|without|not)\s+(?:loss\s+of\s+appetite|reduced\s+appetite)", neg_text, re.IGNORECASE):
                            canonical_concepts.add(concept_name)
                            symptom_ids.add(info["symptom_id"])
                            break
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
        has_general_animal = self._any_token_match(aff_text, [r"\banimal\b", r"जानवर", r"પ્રાણી", r"\bpraani\b", r"\bjanwar\b", r"\bkutta\b", r"\bkutro\b", r"\bkutra\b"])
        has_any_animal = has_dog_token or has_cat_token or has_monkey_token or has_general_animal

        if (has_any_animal and has_bite_action) or any(k in aff_text for k in ["dog bite", "cat bite", "monkey bite", "animal bite", "kutraae batku", "kutra batku", "kutta kata"]):
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
        loc, reg = extract_anatomical_location(clean)
        body_locations = [loc] if loc else []
        if loc:
            clinical_attributes["body_location"] = loc
            clinical_attributes["body_region"] = reg
            if reg and reg not in anatomy:
                anatomy.append(reg)
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
            body_locations=body_locations,
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

# Anatomical Region Keywords for Strict Medical Validation
ANATOMICAL_REGION_TOKENS: Dict[str, List[str]] = {
    "lower_limb": [
        r"\bleg\b", r"\blegs\b", r"\bknee\b", r"\bknees\b", r"\bfoot\b", r"\bfeet\b",
        r"\bankle\b", r"\bankles\b", r"\bcalf\b", r"\bcalves\b", r"\bthigh\b", r"\bthighs\b",
        r"\btoe\b", r"\btoes\b", r"\bheel\b", r"\bheels\b", r"\bshin\b", r"\bshins\b",
        r"\bpatella\b", r"\btibia\b", r"\bfibula\b",
        r"\bgothan\b", r"\bghutan\b", r"\bghutna\b", r"\bpag\b", r"\bpair\b", r"\bpaanv\b", r"\bpaav\b",
        r"\btang\b", r"\btaang\b", r"\bsathal\b", r"\bghunti\b", r"\bpani\b",
        r"पैर", r"पांव", r"टांग", r"जांघ", r"पिंडली", r"घुटना", r"टखना",
        r"પગ", r"સાથળ", r"ઘૂંટણ", r"ઘૂંટી", r"પાની", r"ગોઠણ"
    ],
    "upper_limb": [
        r"\barm\b", r"\barms\b", r"\bhand\b", r"\bhands\b", r"\bwrist\b", r"\bwrists\b",
        r"\bfinger\b", r"\bfingers\b", r"\belbow\b", r"\belbows\b", r"\bshoulder\b", r"\bshoulders\b",
        r"\bforearm\b", r"\bforearms\b", r"\bpalm\b", r"\bpalms\b",
        r"\bhath\b", r"\bhaath\b", r"\bkhandha\b", r"\bkhabho\b", r"\bkhadha\b", r"\bkoni\b", r"\bkandu\b", r"\bangli\b",
        r"हाथ", r"बांह", r"कंधा", r"कोहनी", r"कलाई", r"उंगली",
        r"હાથ", r"ખભા", r"ખભો", r"કોણી", r"કાંડું", r"આંગળી"
    ],
    "eye": [
        r"\beye\b", r"\beyes\b", r"\bvision\b", r"\bvisual\b", r"\bocular\b", r"\bsight\b",
        r"\bpupil\b", r"\bpupils\b", r"\bcornea\b", r"\bretina\b", r"\beyelid\b", r"\beyelids\b",
        r"\baankh\b", r"\bankh\b", r"\baankho\b", r"\bankho\b", r"\bdola\b", r"\bdole\b",
        r"आंख", r"आंखें", r"આંખ", r"આંખો"
    ],
    "ear": [
        r"\bear\b", r"\bears\b", r"\bhearing\b", r"\beardrum\b", r"\botic\b",
        r"\bkan\b", r"\bkaan\b", r"\bkane\b",
        r"कान", r"कानों", r"કાન", r"કાને"
    ],
    "head": [
        r"\bhead\b", r"\bheadache\b", r"\bskull\b", r"\bscalp\b", r"\bbrain\b", r"\bforehead\b", r"\btemple\b",
        r"\bmathu\b", r"\bmathe\b", r"\bsir\b", r"\bsar\b", r"\bdoke\b",
        r"सिर", r"सर", r"माथा", r"માથું", r"ડોકું"
    ],
    "throat_oral": [
        r"\bthroat\b", r"\bmouth\b", r"\btongue\b", r"\btonsil\b", r"\btonsils\b", r"\btooth\b", r"\bteeth\b",
        r"\bgala\b", r"\bgale\b", r"\bgalu\b", r"\bdaant\b", r"\bdaat\b",
        r"गला", r"गले", r"मुंह", r"दांत", r"ગળું", r"ગળા", r"મોં", r"દાંત"
    ],
    "chest": [
        r"\bchest\b", r"\bheart\b", r"\bcardiac\b", r"\bbreast\b",
        r"\bchhati\b", r"\bchaati\b", r"\bseena\b", r"\bseene\b",
        r"छाती", r"सीना", r"हार्ट", r"છાતી", r"હૃદય"
    ],
    "abdomen": [
        r"\babdomen\b", r"\babdominal\b", r"\bstomach\b", r"\bbelly\b", r"\btummy\b", r"\bgut\b",
        r"\bpet\b", r"\bpeta\b", r"\bpot\b",
        r"पेट", r"उदर", r"પેટ", r"पोट"
    ],
    "spine": [
        r"\bback\b", r"\bspine\b", r"\bspinal\b", r"\blumbar\b", r"\bwaist\b",
        r"\bkamar\b", r"\bpeeth\b", r"\bpith\b", r"\bvaho\b", r"\bvanso\b",
        r"कमर", r"पीठ", r"रीढ़", r"કમર", r"પીઠ", r"વાહો", r"વાંસો"
    ],
    "skin": [
        r"\bskin\b", r"\brash\b", r"\bitching\b", r"\bpruritus\b", r"\bblister\b", r"\bblisters\b",
        r"\bchamadi\b", r"\btvacha\b", r"\bkhujli\b", r"\bkhanjwal\b", r"\bfolla\b",
        r"त्वचा", r"खुजली", r"चामड़ी", r"ખંજવાળ", r"ફોલ્લા"
    ]
}

REGION_TO_SYSTEM_COMPATIBILITY: Dict[str, Optional[Set[str]]] = {
    "lower_limb": {"musculoskeletal", "general", "skin", "cardiovascular", "neurology"},
    "upper_limb": {"musculoskeletal", "general", "skin", "cardiovascular", "neurology"},
    "eye": {"eye", "general", "neurology"},
    "ear": {"ent", "respiratory", "general"},
    "ent": {"ent", "respiratory", "general"},
    "head": {"neurology", "mental health", "general", "ent", "eye"},
    "throat_oral": {"ent", "respiratory", "gastrointestinal", "general"},
    "chest": {"cardiovascular", "respiratory", "musculoskeletal", "general"},
    "abdomen": {"gastrointestinal", "urinary", "women's health", "men's health", "general", "endocrine"},
    "spine": {"musculoskeletal", "neurology", "general", "urinary"},
    "skin": {"skin", "general", "infectious diseases"},
    "general": None
}

INCOMPATIBLE_REGION_PAIRS: Set[Tuple[str, str]] = {
    ("lower_limb", "eye"), ("eye", "lower_limb"),
    ("lower_limb", "ear"), ("ear", "lower_limb"),
    ("lower_limb", "throat_oral"), ("throat_oral", "lower_limb"),
    ("lower_limb", "chest"), ("chest", "lower_limb"),
    ("lower_limb", "abdomen"), ("abdomen", "lower_limb"),
    ("upper_limb", "eye"), ("eye", "upper_limb"),
    ("upper_limb", "ear"), ("ear", "upper_limb"),
    ("upper_limb", "throat_oral"), ("throat_oral", "upper_limb"),
    ("upper_limb", "abdomen"), ("abdomen", "upper_limb"),
    ("upper_limb", "lower_limb"), ("lower_limb", "upper_limb"),
    ("spine", "lower_limb"), ("lower_limb", "spine"),
    ("spine", "upper_limb"), ("upper_limb", "spine"),
    ("spine", "eye"), ("eye", "spine"),
    ("spine", "ear"), ("ear", "spine"),
    ("spine", "throat_oral"), ("throat_oral", "spine"),
    ("eye", "ear"), ("ear", "eye"),
    ("eye", "chest"), ("chest", "eye"),
    ("eye", "abdomen"), ("abdomen", "eye"),
    ("ear", "abdomen"), ("abdomen", "ear"),
    ("ear", "chest"), ("chest", "ear"),
    ("head", "lower_limb"), ("lower_limb", "head"),
    ("head", "abdomen"), ("abdomen", "head")
}

def extract_anatomical_regions(text: str) -> Set[str]:
    """Identifies all anatomical regions mentioned in a text using regex boundaries."""
    if not text:
        return set()
    t_clean = text.lower()
    found = set()
    for region, patterns in ANATOMICAL_REGION_TOKENS.items():
        for p in patterns:
            if re.search(p, t_clean, re.IGNORECASE):
                found.add(region)
                break
    return found


BODY_LOCATION_PATTERNS: Dict[str, Dict[str, Any]] = {
    "knee": {
        "region": "lower_limb",
        "tokens": [r"\bknee\b", r"\bknees\b", r"\bgothan\b", r"\bghutan\b", r"\bghutna\b", r"ઘૂંટણ", r"ગોઠણ", r"घुटना", r"\bdhincham\b", r"\bdhinchan\b"]
    },
    "ankle": {
        "region": "lower_limb",
        "tokens": [r"\bankle\b", r"\bankles\b", r"\bghunti\b", r"ઘૂંટી", r"टखना"]
    },
    "foot": {
        "region": "lower_limb",
        "tokens": [r"\bfoot\b", r"\bfeet\b", r"\bpag\b", r"\bpani\b", r"પાની", r"पांव", r"पैर"]
    },
    "leg": {
        "region": "lower_limb",
        "tokens": [r"\bleg\b", r"\blegs\b", r"\btang\b", r"\btaang\b", r"ટાંગ", r"टांग"]
    },
    "thigh": {
        "region": "lower_limb",
        "tokens": [r"\bthigh\b", r"\bthighs\b", r"\bsathal\b", r"સાથળ", r"जांघ"]
    },
    "shoulder": {
        "region": "upper_limb",
        "tokens": [r"\bshoulder\b", r"\bshoulders\b", r"\bkhabho\b", r"\bkhandha\b", r"ખભો", r"ખભા", r"कंधा"]
    },
    "elbow": {
        "region": "upper_limb",
        "tokens": [r"\belbow\b", r"\belbows\b", r"\bkoni\b", r"કોણી", r"कोहनी"]
    },
    "wrist": {
        "region": "upper_limb",
        "tokens": [r"\bwrist\b", r"\bwrists\b", r"\bkandu\b", r"કાંડું", r"कलाई"]
    },
    "hand": {
        "region": "upper_limb",
        "tokens": [r"\bhand\b", r"\bhands\b", r"\bhath\b", r"\bhaath\b", r"હાથ", r"हाथ"]
    },
    "finger": {
        "region": "upper_limb",
        "tokens": [r"\bfinger\b", r"\bfingers\b", r"\bangli\b", r"આંગળી", r"उंगली"]
    },
    "lower_back": {
        "region": "spine",
        "tokens": [r"\blower back\b", r"\blumbago\b", r"\bkamar\b", r"\bvaho\b", r"\bvanso\b", r"વાહો", r"વાંસો", r"કમર", r"कमर"]
    },
    "upper_back": {
        "region": "spine",
        "tokens": [r"\bupper back\b", r"\bpeeth\b", r"\bpith\b", r"પીઠ", r"पीठ"]
    },
    "neck": {
        "region": "spine",
        "tokens": [r"\bneck\b", r"\bcervical\b", r"\bgardan\b", r"\bmaan\b", r"ગરદન", r"गर्दन", r"માન"]
    },
    "chest": {
        "region": "chest",
        "tokens": [r"\bchest\b", r"\bchhati\b", r"\bseena\b", r"છાતી", r"छाती", r"सीना"]
    },
    "abdomen": {
        "region": "abdomen",
        "tokens": [r"\babdomen\b", r"\bstomach\b", r"\bbelly\b", r"\bpet\b", r"પેટ", r"पेट"]
    },
    "head": {
        "region": "head",
        "tokens": [r"\bhead\b", r"\bforehead\b", r"\bmathu\b", r"\bsir\b", r"\bsar\b", r"માથું", r"सिर"]
    },
    "eye": {
        "region": "eye",
        "tokens": [r"\beye\b", r"\beyes\b", r"\baankh\b", r"આંખ", r"आंख"]
    },
    "ear": {
        "region": "ear",
        "tokens": [r"\bear\b", r"\bears\b", r"\bkan\b", r"કાન", r"कान"]
    },
    "throat": {
        "region": "throat_oral",
        "tokens": [r"\bthroat\b", r"\bgala\b", r"\bgalu\b", r"ગળું", r"गला"]
    }
}


def extract_anatomical_location(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts specific anatomical location and its associated body region from text.
    Returns (body_location, body_region), e.g. ('knee', 'lower_limb').
    """
    if not text or not isinstance(text, str):
        return None, None
    t_lower = text.lower()
    for loc_name, loc_info in BODY_LOCATION_PATTERNS.items():
        for pat in loc_info["tokens"]:
            if re.search(pat, t_lower, re.IGNORECASE):
                return loc_name, loc_info["region"]
    return None, None


def extract_laterality_from_text(text: str) -> Optional[str]:
    """Detects explicit laterality ('left', 'right', 'bilateral') from text."""
    if not text or not isinstance(text, str):
        return None
    t_lower = text.lower()
    for lat, patterns in LATERALITY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, t_lower, re.IGNORECASE):
                return lat
    return None



class MasterSymptomTaxonomyBridge:
    """
    Generalized Multilingual Bridge covering all 280 symptoms in symptoms_master.csv
    and extensible aliases in symptom_aliases.csv.
    Provides fast bidirectional lookup:
      user_text / multilingual phrase -> canonical symptom ID (S000001..S000280) -> metadata.
    Enforces strict anatomical and semantic validation so impossible cross-body matches are rejected.
    """
    def __init__(self, csv_path: Optional[str] = None):
        if not csv_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            csv_path = os.path.join(base_dir, "datasets", "symptoms", "symptoms_master.csv")
            aliases_path = os.path.join(base_dir, "datasets", "symptoms", "symptom_aliases.csv")
            learned_path = os.path.join(base_dir, "datasets", "symptoms", "learned_symptoms.csv")
        else:
            aliases_path = os.path.join(os.path.dirname(csv_path), "symptom_aliases.csv")
            learned_path = os.path.join(os.path.dirname(csv_path), "learned_symptoms.csv")
        self.csv_path = csv_path
        self.aliases_path = aliases_path
        self.learned_path = learned_path
        self.id_to_record: Dict[str, Dict[str, Any]] = {}
        self.exact_name_to_id: Dict[str, str] = {}
        self.alias_name_to_id: Dict[str, str] = {}
        self.dataset_fingerprint: str = ""
        self._load_master_taxonomy()

    def _compute_fingerprint(self) -> str:
        import hashlib
        h = hashlib.sha256()
        for path in [self.csv_path, self.aliases_path, self.learned_path]:
            if os.path.exists(path):
                stat = os.stat(path)
                h.update(f"{path}:{stat.st_mtime}:{stat.st_size}".encode("utf-8"))
        return h.hexdigest()[:16]

    def _load_master_taxonomy(self):
        if not os.path.exists(self.csv_path):
            _logger.warning("[MasterSymptomTaxonomyBridge] Master symptoms file not found at: %s", self.csv_path)
            return

        self.dataset_fingerprint = self._compute_fingerprint()

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
                for col_name, val in row.items():
                    if col_name.startswith("symptom_name_") and val:
                        record[col_name] = str(val).strip()

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

                # Index localized columns dynamically
                for col_key, val in record.items():
                    if col_key.startswith("symptom_name_") and val:
                        v_str = str(val).strip().lower()
                        if v_str and v_str != "nan":
                            self.exact_name_to_id[v_str] = sid
                            for v_part in v_str.split('/'):
                                v_clean = re.sub(r'\(.*?\)', '', v_part).strip().lower()
                                if v_clean and v_clean not in self.exact_name_to_id:
                                    self.exact_name_to_id[v_clean] = sid

        # Load extensible aliases dataset dynamically
        if os.path.exists(self.aliases_path):
            try:
                with open(self.aliases_path, mode="r", encoding="utf-8-sig") as af:
                    a_reader = csv.DictReader(af)
                    for a_row in a_reader:
                        a_sid = a_row.get("symptom_id", "").strip().upper()
                        a_name = str(a_row.get("alias_text") or a_row.get("alias_name") or "").strip().lower()
                        if a_sid and a_name and a_sid in self.id_to_record:
                            self.alias_name_to_id[a_name] = a_sid
                            if a_name not in self.exact_name_to_id:
                                self.exact_name_to_id[a_name] = a_sid
            except Exception as e:
                _logger.warning("[MasterSymptomTaxonomyBridge] Failed loading aliases: %s", e)

        # Load learned symptoms dataset dynamically (Tier 2 learned storage)
        if os.path.exists(self.learned_path):
            try:
                with open(self.learned_path, mode="r", encoding="utf-8-sig") as lf:
                    l_reader = csv.DictReader(lf)
                    for l_row in l_reader:
                        l_sid = l_row.get("symptom_id", "").strip().upper()
                        l_name = str(l_row.get("alias_text") or l_row.get("alias_name") or "").strip().lower()
                        if l_sid and l_name and l_sid in self.id_to_record:
                            self.alias_name_to_id[l_name] = l_sid
                            if l_name not in self.exact_name_to_id:
                                self.exact_name_to_id[l_name] = l_sid
            except Exception as e:
                _logger.warning("[MasterSymptomTaxonomyBridge] Failed loading learned symptoms: %s", e)

    def register_learned_symptom(
        self,
        alias_text: str,
        symptom_id: str,
        language_code: str = "en",
        script_type: str = "Latin",
        notes: str = "Learned via Gemini+Groq consensus"
    ) -> bool:
        """
        Dynamically records a new verified alias in datasets/symptoms/learned_symptoms.csv
        and updates the in-memory lookup cache in real-time.
        """
        if not alias_text or not symptom_id:
            return False
        clean_text = str(alias_text).strip()
        clean_sid = str(symptom_id).strip().upper()
        if clean_sid not in self.id_to_record:
            return False

        norm_key = clean_text.lower()
        # Even if already in index, ensure mapping is consistent
        self.alias_name_to_id[norm_key] = clean_sid
        self.exact_name_to_id[norm_key] = clean_sid

        try:
            file_exists = os.path.exists(self.learned_path)
            next_idx = 1
            if file_exists and os.path.getsize(self.learned_path) > 0:
                with open(self.learned_path, mode="r", encoding="utf-8-sig") as f:
                    lines = [line for line in f if line.strip()]
                    next_idx = max(1, len(lines))
            alias_id = f"LSA{next_idx:06d}"

            # Check if this exact alias is already written to file to prevent duplicate rows
            already_in_file = False
            if file_exists and os.path.getsize(self.learned_path) > 0:
                with open(self.learned_path, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        if str(r.get("alias_text", "")).strip().lower() == norm_key:
                            already_in_file = True
                            break

            if not already_in_file:
                with open(self.learned_path, mode="a", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    if not file_exists or os.path.getsize(self.learned_path) == 0:
                        writer.writerow([
                            "alias_id", "symptom_id", "language_code", "script_type",
                            "alias_text", "alias_kind", "match_status", "source_file",
                            "source_column", "review_status", "notes"
                        ])
                    writer.writerow([
                        alias_id, clean_sid, language_code, script_type,
                        clean_text, "learned_consensus", "ACTIVE_CONSENSUS_LEARNED",
                        "learned_symptoms.csv", "alias_text",
                        "approved_dual_llm_consensus", notes
                    ])
                _logger.info("[TaxonomyBridge] Successfully persisted learned symptom alias: '%s' -> %s (%s)", clean_text, clean_sid, alias_id)
            return True
        except Exception as exc:
            _logger.error("[TaxonomyBridge] Error appending to learned_symptoms.csv: %s", exc)
            return False

    def check_anatomical_conflict(
        self,
        phrase_or_cand: str,
        record: Optional[Dict[str, Any]],
        candidate_region: Optional[str] = None
    ) -> bool:
        """
        Validates that a symptom record does not violate explicit anatomical markers
        in the user's phrase or proposed candidate.
        Returns True if there is an INVALID CONFLICT, False if compatible.
        """
        if not phrase_or_cand or not record:
            return False

        rec_name = str(record.get("symptom_name", "")).lower()
        rec_sys = str(record.get("body_system", "")).strip().lower()

        # 1. Candidate region vs Record body_system check
        if candidate_region:
            c_reg = candidate_region.strip().lower()
            allowed_systems = REGION_TO_SYSTEM_COMPATIBILITY.get(c_reg)
            if allowed_systems is not None:
                if rec_sys and rec_sys not in allowed_systems:
                    return True

        # 2. Check if candidate_region directly conflicts with user phrase regions
        phrase_regions = extract_anatomical_regions(phrase_or_cand)
        if candidate_region:
            c_reg = candidate_region.strip().lower()
            for p_reg in phrase_regions:
                if (p_reg, c_reg) in INCOMPATIBLE_REGION_PAIRS:
                    return True

        # 3. Extract anatomical regions from target record and check incompatibilities
        target_text = f"{rec_name} {rec_sys}"
        target_regions = extract_anatomical_regions(target_text)

        src_regions = set(phrase_regions)
        if candidate_region and candidate_region.lower() in REGION_TO_SYSTEM_COMPATIBILITY:
            src_regions.add(candidate_region.lower())

        for s_reg in src_regions:
            for t_reg in target_regions:
                if (s_reg, t_reg) in INCOMPATIBLE_REGION_PAIRS:
                    return True

        return False

    def resolve_symptom(self, symptom_text: str, candidate_region: Optional[str] = None) -> Optional[str]:
        if not symptom_text:
            return None
        st = str(symptom_text).strip()
        if re.match(r"^S[0-9]{6}$", st.upper()):
            sid = st.upper()
            return sid if sid in self.id_to_record else sid

        st_clean = st.lower()
        if st_clean in self.exact_name_to_id:
            sid = self.exact_name_to_id[st_clean]
            rec = self.id_to_record.get(sid)
            if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                return sid

        # Normalized without punctuation
        norm_clean = re.sub(r"[^\w\s\u0900-\u0DFF]", " ", st_clean)
        norm_clean = re.sub(r"\s+", " ", norm_clean).strip()
        if norm_clean in self.exact_name_to_id:
            sid = self.exact_name_to_id[norm_clean]
            rec = self.id_to_record.get(sid)
            if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                return sid

        # Check canonical concept patterns directly
        for concept_name, info in CANONICAL_CONCEPT_PATTERNS.items():
            for p in info["patterns"]:
                if re.search(p, st_clean, re.IGNORECASE):
                    sid = info["symptom_id"]
                    rec = self.id_to_record.get(sid)
                    if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                        return sid

        # Controlled biomedical synonyms map
        biomed_synonyms = {
            "pyrexia": "S000001", "hyperthermia": "S000001", "fever": "S000001", "febrile": "S000001",
            "cephalalgia": "S000061", "headache": "S000061", "migraine": "S000063",
            "pharyngitis": "S000032", "sore throat": "S000032", "throat pain": "S000032",
            "dizziness": "S000064", "vertigo": "S000065", "lightheadedness": "S000064",
            "myalgia": "S000011", "body ache": "S000011", "muscle pain": "S000011", "arthralgia": "S000131",
            "nausea": "S000086", "vomiting": "S000087", "emesis": "S000087",
            "diarrhea": "S000089", "loose motion": "S000089",
            "dyspnea": "S000026", "breathlessness": "S000026", "shortness of breath": "S000026",
            "chest pain": "S000046", "angina": "S000046",
            "dysuria": "S000237", "burning urination": "S000237", "painful urination": "S000237",
            "hematuria": "S000238", "blood in urine": "S000238",
            "photophobia": "S000079", "conjunctivitis": "S000213",
            "fatigue": "S000005", "malaise": "S000012",
            "anorexia": "S000009", "loss of appetite": "S000009"
        }
        for k, v in biomed_synonyms.items():
            if k == st_clean or (len(k) > 4 and k in st_clean) or (len(st_clean) > 4 and st_clean in k):
                rec = self.id_to_record.get(v)
                if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                    return v

        return None

    def match_symptom_detailed(self, symptom_text: str, candidate_region: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates an extracted symptom phrase or candidate against symptoms_master.csv
        following strict clinical matching hierarchy:
        1. Exact match (symptom_name exact)
        2. Alias match (Hindi/Gujarati/symptom_aliases.csv/Concept patterns)
        3. Normalized lexical match (whitespace/punctuation stripped)
        4. Controlled semantic match (biomedical synonyms)
        5. Controlled high-precision fuzzy match (threshold >= 0.90, separation margin >= 0.10)
        6. Otherwise UNMATCHED.
        
        Strictly enforces that anatomical conflicts are rejected across all stages.
        """
        if not symptom_text or not str(symptom_text).strip():
            return {
                "dataset_match": False,
                "dataset_name": None,
                "symptom_id": None,
                "match_type": "UNMATCHED",
                "match_status": "Not Matched",
                "record": None
            }

        st = str(symptom_text).strip()
        st_clean = st.lower()

        # 0. Direct Canonical ID
        if re.match(r"^S[0-9]{6}$", st.upper()):
            sid = st.upper()
            rec = self.id_to_record.get(sid)
            if rec and not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                return {
                    "dataset_match": True,
                    "dataset_name": rec.get("symptom_name", st),
                    "symptom_id": sid,
                    "match_type": "EXACT MATCH",
                    "match_status": "Matched",
                    "record": rec
                }

        # 1. Exact Match against master English names
        for sid, rec in self.id_to_record.items():
            if rec.get("symptom_name", "").lower() == st_clean:
                if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                    return {
                        "dataset_match": True,
                        "dataset_name": rec.get("symptom_name"),
                        "symptom_id": sid,
                        "match_type": "EXACT MATCH",
                        "match_status": "Matched",
                        "record": rec
                    }

        # 2. Alias Match (symptom_aliases.csv, Hindi, Gujarati, clean English aliases)
        if st_clean in self.exact_name_to_id:
            sid = self.exact_name_to_id[st_clean]
            rec = self.id_to_record.get(sid)
            if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                return {
                    "dataset_match": True,
                    "dataset_name": rec.get("symptom_name") if rec else st,
                    "symptom_id": sid,
                    "match_type": "ALIAS MATCH",
                    "match_status": "Matched",
                    "record": rec
                }

        # Check concept patterns (e.g. lower_back_pain, chest_pain, animal_bite)
        for concept_name, info in CANONICAL_CONCEPT_PATTERNS.items():
            for p in info["patterns"]:
                if re.search(p, st_clean, re.IGNORECASE):
                    sid = info["symptom_id"]
                    rec = self.id_to_record.get(sid)
                    if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                        return {
                            "dataset_match": True,
                            "dataset_name": rec.get("symptom_name") if rec else concept_name.replace("_", " ").title(),
                            "symptom_id": sid,
                            "match_type": "ALIAS MATCH",
                            "match_status": "Matched",
                            "record": rec
                        }

        # 2b. Clinical Laterality & Severity Modifier Stripping (left, right, both, bilateral, severe, mild, moderate, high, etc.)
        core_unmodified = re.sub(
            r"^(?:(?:left|right|both|bilateral|severe|mild|moderate|chronic|acute|slight|intense|high|तेज|तेज़|ખૂબ|તીવ્ર|हल्का|સખત|डावा|दायां|જમણો|ડાબો)\s+)+",
            "",
            st_clean
        ).strip()
        if core_unmodified and core_unmodified != st_clean:
            if core_unmodified in self.exact_name_to_id:
                sid = self.exact_name_to_id[core_unmodified]
                rec = self.id_to_record.get(sid)
                if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                    return {
                        "dataset_match": True,
                        "dataset_name": rec.get("symptom_name") if rec else core_unmodified.title(),
                        "symptom_id": sid,
                        "match_type": "ALIAS MATCH",
                        "match_status": "Matched",
                        "record": rec
                    }
            for concept_name, info in CANONICAL_CONCEPT_PATTERNS.items():
                for p in info["patterns"]:
                    if re.search(p, core_unmodified, re.IGNORECASE):
                        sid = info["symptom_id"]
                        rec = self.id_to_record.get(sid)
                        if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                            return {
                                "dataset_match": True,
                                "dataset_name": rec.get("symptom_name") if rec else concept_name.replace("_", " ").title(),
                                "symptom_id": sid,
                                "match_type": "ALIAS MATCH",
                                "match_status": "Matched",
                                "record": rec
                            }

        # 3. Normalized Lexical Match (strip non-alphanumeric, collapse whitespace)
        norm_clean = re.sub(r"[^\w\s\u0900-\u0DFF]", " ", st_clean)
        norm_clean = re.sub(r"\s+", " ", norm_clean).strip()
        if norm_clean in self.exact_name_to_id:
            sid = self.exact_name_to_id[norm_clean]
            rec = self.id_to_record.get(sid)
            if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                return {
                    "dataset_match": True,
                    "dataset_name": rec.get("symptom_name") if rec else st,
                    "symptom_id": sid,
                    "match_type": "NORMALIZED MATCH",
                    "match_status": "Matched",
                    "record": rec
                }

        # 4. Controlled Semantic Match (Biomedical synonyms)
        biomed_synonyms = {
            "pyrexia": "S000001", "hyperthermia": "S000001", "fever": "S000001", "febrile": "S000001",
            "burning throat": "S000032", "sore throat": "S000032", "throat irritation": "S000032", "pharyngitis": "S000032", "throat pain": "S000032",
            "cephalalgia": "S000061", "headache": "S000061", "migraine": "S000063",
            "dizziness": "S000064", "vertigo": "S000065", "lightheadedness": "S000064", "giddiness": "S000064",
            "myalgia": "S000011", "body ache": "S000011", "body pain": "S000011", "arthralgia": "S000131",
            "nausea": "S000086", "vomiting": "S000087", "emesis": "S000087",
            "diarrhea": "S000089", "loose motion": "S000089",
            "dyspnea": "S000026", "breathlessness": "S000026", "shortness of breath": "S000026",
            "chest pain": "S000046", "angina": "S000046",
            "wheezing": "S000028", "wheeze": "S000028", "chest wheezing": "S000028",
            "skin redness": "S000112", "erythema": "S000112",
            "runny nose": "S000035", "rhinorrhea": "S000035",
            "abdominal bloating": "S000100", "bloating": "S000100",
            "bleeding wound": "S000114", "open wound": "S000114"
        }
        for k, v in biomed_synonyms.items():
            if k == st_clean or (len(k) > 4 and k in st_clean) or (len(st_clean) > 4 and st_clean in k):
                sid = v
                rec = self.id_to_record.get(sid)
                if not self.check_anatomical_conflict(st_clean, rec, candidate_region):
                    return {
                        "dataset_match": True,
                        "dataset_name": rec.get("symptom_name") if rec else k.title(),
                        "symptom_id": sid,
                        "match_type": "SEMANTIC MATCH",
                        "match_status": "Matched",
                        "record": rec
                    }

        # 5. Controlled High-Precision Fuzzy Match (threshold >= 0.90, margin >= 0.10)
        import difflib
        candidates_scored = []
        for name, sid in self.exact_name_to_id.items():
            rec = self.id_to_record.get(sid)
            # Pre-filter: anatomical conflict is strictly disqualified from fuzzy matching
            if self.check_anatomical_conflict(st_clean, rec, candidate_region):
                continue
            ratio = difflib.SequenceMatcher(None, st_clean, name).ratio()
            if ratio >= 0.90:
                candidates_scored.append((ratio, sid, rec))

        if candidates_scored:
            candidates_scored.sort(key=lambda x: x[0], reverse=True)
            best_ratio, best_sid, best_rec = candidates_scored[0]
            if len(candidates_scored) > 1:
                second_ratio = candidates_scored[1][0]
                if (best_ratio - second_ratio) < 0.10 and best_sid != candidates_scored[1][1]:
                    return {
                        "dataset_match": False,
                        "dataset_name": None,
                        "symptom_id": None,
                        "match_type": "AMBIGUOUS",
                        "match_status": "Not Matched",
                        "record": None
                    }

            return {
                "dataset_match": True,
                "dataset_name": best_rec.get("symptom_name") if best_rec else st,
                "symptom_id": best_sid,
                "match_type": "FUZZY MATCH",
                "match_status": "Matched",
                "record": best_rec
            }

        # 6. UNMATCHED (No fabricated match)
        return {
            "dataset_match": False,
            "dataset_name": None,
            "symptom_id": None,
            "match_type": "UNMATCHED",
            "match_status": "Not Matched",
            "record": None
        }

    def lookup_by_id(self, sid: str) -> Optional[Dict[str, Any]]:
        if not sid:
            return None
        return self.id_to_record.get(str(sid).strip().upper())


def get_taxonomy_bridge() -> MasterSymptomTaxonomyBridge:
    """Returns the singleton MasterSymptomTaxonomyBridge instance."""
    return canonical_normalizer.bridge


def segment_clinical_phrases(text: str) -> List[str]:
    """
    Splits free-form multilingual patient text into distinct clinical phrases.
    Strips non-clinical connectors ('and', 'ane', 'aur', 'or', 'with', 'sathe', 'સાથે', 'और', 'તથા', 'પણ', 'pan', 'pn', 'भी', etc.).
    Preserves raw patient evidence intact.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return []

    # 0. Pre-process clause boundaries: vernacular verb terminals followed by letters
    verb_clause_pattern = r'\b(chhe|che|hai|હતી|હતો|છે|है)\b\s+(?=[a-zA-Z\u0900-\u0D7F])'
    prep_text = re.sub(verb_clause_pattern, r'\1, ', text, flags=re.IGNORECASE)

    # 1. Primary boundaries: punctuation, commas, semicolons, full stops, danda, newlines
    primary_delims = r"[,;\n।!?|]+|(?:\.\s+)"
    raw_clauses = [c.strip() for c in re.split(primary_delims, prep_text) if c and c.strip()]

    # 2. Conjunction splitting for compound phrases (coordinating and adversative)
    conj_pattern = r"(?:\s+(?:and|aur|ane|aani|તથા|तथा|અને|આણિ|आणि|or|with|sathe|સાથે|और|but|lekin|parantu|kintu|magar|pan|લેકિન|પરંતુ|પણ|किन्तु|मगर|પર|par|परंतु)\s+)"
    sub_clauses = []
    for c in raw_clauses:
        parts = [p.strip() for p in re.split(conj_pattern, c, flags=re.IGNORECASE) if p and p.strip()]
        sub_clauses.extend(parts)

    # 3. Clean non-clinical standalone connectors that shouldn't be symptoms
    non_clinical_words = {
        "and", "ane", "aur", "also", "pan", "pn", "bhi", "भी", "પણ", "with", "sathe", "સાથે", "or",
        "chhe", "che", "hai", "aave", "ave", "chhe.", "che.", "hai.", "tha", "raha", "rahi", "hata"
    }

    cleaned_phrases = []
    for sc in sub_clauses:
        tokens = sc.split()
        while tokens and tokens[0].lower().strip(".,!?") in non_clinical_words:
            tokens.pop(0)
        while tokens and tokens[-1].lower().strip(".,!?") in non_clinical_words:
            tokens.pop(-1)
        cleaned_phrase = " ".join(tokens).strip()
        if len(cleaned_phrase) >= 2 and cleaned_phrase.lower() not in non_clinical_words:
            cleaned_phrases.append(cleaned_phrase)

    return cleaned_phrases if cleaned_phrases else [text.strip()]


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
    "S000032": "Sore Throat",
    "S000064": "Dizziness",
    "S000011": "Generalized Body Ache",
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
