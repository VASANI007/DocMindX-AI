"""
DocMindX AI - Clinical Test Manifest (300 Comprehensive Test Cases)
Canonical Symptom IDs verified against datasets/symptoms/symptoms_master.csv:
S000001: Fever
S000002: High Fever (above 103°F/39.4°C)
S000003: Chills
S000005: Fatigue
S000006: Weakness
S000009: Loss of Appetite
S000011: Generalized Body Ache
S000023: Dry Cough / Cough
S000024: Productive Cough
S000026: Shortness of Breath
S000032: Sore Throat
S000035: Runny Nose
S000046: Chest Pain
S000047: Chest Pain Radiating
S000061: Headache
S000064: Dizziness
S000079: Sensitivity to Light (Photophobia)
S000086: Nausea
S000087: Vomiting
S000089: Diarrhea
S000092: Abdominal Pain
S000102: Stomach Cramps
S000109: Skin Rash
S000131: Joint Pain
S000133: Muscle Pain
S000135: Back Pain
S000210: Blurred Vision
S000212: Eye Pain
S000213: Eye Redness
S000226: Frequent Urination
S000237: Painful Urination (Burning)
S000238: Blood in Urine
S000239: Difficulty Urinating
"""

# ==============================================================================
# CATEGORY A: DEMOGRAPHICS (40 Cases)
# ==============================================================================
DEMOGRAPHICS_TEST_CASES = [
    {"id": "TC-DEM-001", "name": "Neonate 0 days", "input": {"age": 0, "gender": "Male", "state": "Maharashtra", "height": 50, "weight": 3.2, "blood_group": "O+"}, "valid": True, "expected_age_group": "0-10"},
    {"id": "TC-DEM-002", "name": "Infant 1 year", "input": {"age": 1, "gender": "Female", "state": "Gujarat", "height": 75, "weight": 9.5, "blood_group": "A+"}, "valid": True, "expected_age_group": "0-10"},
    {"id": "TC-DEM-003", "name": "Child 10 years upper bound pediatric tier", "input": {"age": 10, "gender": "Male", "state": "Delhi", "height": 138, "weight": 32, "blood_group": "B+"}, "valid": True, "expected_age_group": "0-10"},
    {"id": "TC-DEM-004", "name": "Adolescent 11 years tier transition", "input": {"age": 11, "gender": "Female", "state": "Karnataka", "height": 142, "weight": 36, "blood_group": "AB+"}, "valid": True, "expected_age_group": "11-20"},
    {"id": "TC-DEM-005", "name": "Adolescent 17 years boundary", "input": {"age": 17, "gender": "Male", "state": "Tamil Nadu", "height": 170, "weight": 60, "blood_group": "O-"}, "valid": True, "expected_age_group": "11-20"},
    {"id": "TC-DEM-006", "name": "Young adult 18 years legal age", "input": {"age": 18, "gender": "Female", "state": "Kerala", "height": 162, "weight": 52, "blood_group": "A-"}, "valid": True, "expected_age_group": "11-20"},
    {"id": "TC-DEM-007", "name": "Adult 21 years tier start", "input": {"age": 21, "gender": "Male", "state": "Rajasthan", "height": 175, "weight": 70, "blood_group": "B-"}, "valid": True, "expected_age_group": "21-30"},
    {"id": "TC-DEM-008", "name": "Adult 30 years tier end", "input": {"age": 30, "gender": "Female", "state": "Punjab", "height": 165, "weight": 58, "blood_group": "AB-"}, "valid": True, "expected_age_group": "21-30"},
    {"id": "TC-DEM-009", "name": "Adult 31 years tier start", "input": {"age": 31, "gender": "Other", "state": "West Bengal", "height": 168, "weight": 64, "blood_group": "O+"}, "valid": True, "expected_age_group": "31-40"},
    {"id": "TC-DEM-010", "name": "Adult 40 years tier end", "input": {"age": 40, "gender": "Male", "state": "Uttar Pradesh", "height": 172, "weight": 78, "blood_group": "A+"}, "valid": True, "expected_age_group": "31-40"},

    {"id": "TC-DEM-011", "name": "Adult 41 years tier start", "input": {"age": 41, "gender": "Female", "state": "Madhya Pradesh", "height": 158, "weight": 62, "blood_group": "B+"}, "valid": True, "expected_age_group": "41-50"},
    {"id": "TC-DEM-012", "name": "Adult 50 years tier end", "input": {"age": 50, "gender": "Male", "state": "Andhra Pradesh", "height": 169, "weight": 74, "blood_group": "AB+"}, "valid": True, "expected_age_group": "41-50"},
    {"id": "TC-DEM-013", "name": "Senior 51 years tier start", "input": {"age": 51, "gender": "Female", "state": "Telangana", "height": 155, "weight": 66, "blood_group": "O+"}, "valid": True, "expected_age_group": "51-60"},
    {"id": "TC-DEM-014", "name": "Senior 60 years tier end", "input": {"age": 60, "gender": "Male", "state": "Bihar", "height": 165, "weight": 68, "blood_group": "A+"}, "valid": True, "expected_age_group": "51-60"},
    {"id": "TC-DEM-015", "name": "Elderly 61 years tier start", "input": {"age": 61, "gender": "Female", "state": "Odisha", "height": 150, "weight": 55, "blood_group": "B+"}, "valid": True, "expected_age_group": "61+"},
    {"id": "TC-DEM-016", "name": "Elderly 75 years active senior", "input": {"age": 75, "gender": "Male", "state": "Assam", "height": 160, "weight": 62, "blood_group": "AB+"}, "valid": True, "expected_age_group": "61+"},
    {"id": "TC-DEM-017", "name": "Elderly 90 years nonagenarian", "input": {"age": 90, "gender": "Female", "state": "Himachal Pradesh", "height": 148, "weight": 48, "blood_group": "O-"}, "valid": True, "expected_age_group": "61+"},
    {"id": "TC-DEM-018", "name": "Centenarian 100 years", "input": {"age": 100, "gender": "Male", "state": "Goa", "height": 158, "weight": 50, "blood_group": "A-"}, "valid": True, "expected_age_group": "61+"},
    {"id": "TC-DEM-019", "name": "Supercentenarian 115 years upper boundary", "input": {"age": 115, "gender": "Female", "state": "Uttarakhand", "height": 145, "weight": 42, "blood_group": "B-"}, "valid": True, "expected_age_group": "61+"},
    {"id": "TC-DEM-020", "name": "Max allowed age 125 years", "input": {"age": 125, "gender": "Male", "state": "Jammu and Kashmir", "height": 160, "weight": 45, "blood_group": "O+"}, "valid": True, "expected_age_group": "61+"},

    {"id": "TC-DEM-021", "name": "Negative age rejection", "input": {"age": -5, "gender": "Male", "state": "Gujarat"}, "valid": False, "error_field": "age"},
    {"id": "TC-DEM-022", "name": "Unrealistic extreme age 130", "input": {"age": 130, "gender": "Female", "state": "Maharashtra"}, "valid": False, "error_field": "age"},
    {"id": "TC-DEM-023", "name": "None age missing rejection", "input": {"age": None, "gender": "Male", "state": "Delhi"}, "valid": False, "error_field": "age"},
    {"id": "TC-DEM-024", "name": "String non-numeric age rejection", "input": {"age": "twenty-five", "gender": "Female", "state": "Kerala"}, "valid": False, "error_field": "age"},
    {"id": "TC-DEM-025", "name": "Empty gender rejection", "input": {"age": 30, "gender": "", "state": "Punjab"}, "valid": False, "error_field": "gender"},
    {"id": "TC-DEM-026", "name": "Invalid gender term rejection", "input": {"age": 30, "gender": "Alien", "state": "Punjab"}, "valid": False, "error_field": "gender"},
    {"id": "TC-DEM-027", "name": "Empty state rejection", "input": {"age": 30, "gender": "Male", "state": ""}, "valid": False, "error_field": "state"},
    {"id": "TC-DEM-028", "name": "Whitespace only state rejection", "input": {"age": 30, "gender": "Female", "state": "   "}, "valid": False, "error_field": "state"},

    {"id": "TC-DEM-029", "name": "Extreme height low boundary 20cm", "input": {"age": 0, "gender": "Male", "state": "Delhi", "height": 20, "weight": 1.5}, "valid": True},
    {"id": "TC-DEM-030", "name": "Extreme height high boundary 250cm", "input": {"age": 25, "gender": "Male", "state": "Haryana", "height": 250, "weight": 110}, "valid": True},
    {"id": "TC-DEM-031", "name": "Invalid negative height rejection", "input": {"age": 25, "gender": "Male", "state": "Haryana", "height": -170}, "valid": False, "error_field": "height"},
    {"id": "TC-DEM-032", "name": "Unrealistic extreme height 350cm rejection", "input": {"age": 25, "gender": "Male", "state": "Haryana", "height": 350}, "valid": False, "error_field": "height"},
    {"id": "TC-DEM-033", "name": "Extreme weight low boundary 1.0kg", "input": {"age": 0, "gender": "Female", "state": "Goa", "weight": 1.0}, "valid": True},
    {"id": "TC-DEM-034", "name": "Extreme weight high boundary 350kg", "input": {"age": 45, "gender": "Male", "state": "Maharashtra", "weight": 350.0}, "valid": True},
    {"id": "TC-DEM-035", "name": "Invalid zero weight rejection", "input": {"age": 45, "gender": "Male", "state": "Maharashtra", "weight": 0}, "valid": False, "error_field": "weight"},
    {"id": "TC-DEM-036", "name": "Unrealistic extreme weight 600kg rejection", "input": {"age": 45, "gender": "Male", "state": "Maharashtra", "weight": 600}, "valid": False, "error_field": "weight"},
    {"id": "TC-DEM-037", "name": "Valid Bombay Blood Group or rare notation", "input": {"age": 35, "gender": "Female", "state": "Gujarat", "blood_group": "O+"}, "valid": True},
    {"id": "TC-DEM-038", "name": "Invalid blood group symbol rejection", "input": {"age": 35, "gender": "Female", "state": "Gujarat", "blood_group": "C+"}, "valid": False, "error_field": "blood_group"},
    {"id": "TC-DEM-039", "name": "Unicode state name accepted (ગુજરાત)", "input": {"age": 28, "gender": "Male", "state": "ગુજરાત", "height": 172, "weight": 68}, "valid": True},
    {"id": "TC-DEM-040", "name": "XSS / injection in state sanitized or validated", "input": {"age": 28, "gender": "Male", "state": "<script>alert('xss')</script>"}, "valid": True, "sanitized": True}
]

# ==============================================================================
# CATEGORY B: SYMPTOM EXTRACTION (80 Cases)
# ==============================================================================
SYMPTOM_TEST_CASES = [
    # Single Core Symptoms (1-15)
    {"id": "TC-SYM-001", "text": "I have a high fever", "expected_ids": ["S000001"]},
    {"id": "TC-SYM-002", "text": "Continuous severe cough", "expected_ids": ["S000023"]},
    {"id": "TC-SYM-003", "text": "Sharp chest pain on the left side", "expected_ids": ["S000046"]},
    {"id": "TC-SYM-004", "text": "Extreme fatigue and exhaustion", "expected_ids": ["S000005"]},
    {"id": "TC-SYM-005", "text": "Terrible headache since morning", "expected_ids": ["S000061"]},
    {"id": "TC-SYM-006", "text": "Nausea after every meal", "expected_ids": ["S000086"]},
    {"id": "TC-SYM-007", "text": "Persistent vomiting", "expected_ids": ["S000087"]},
    {"id": "TC-SYM-008", "text": "Severe watery diarrhea", "expected_ids": ["S000089"]},
    {"id": "TC-SYM-009", "text": "Shortness of breath walking upstairs", "expected_ids": ["S000026"]},
    {"id": "TC-SYM-010", "text": "Joint pain in both knees", "expected_ids": ["S000131"]},
    {"id": "TC-SYM-011", "text": "Itchy red skin rash across arms", "expected_ids": ["S000109"]},
    {"id": "TC-SYM-012", "text": "Painful burning sensation during urination", "expected_ids": ["S000237"]},
    {"id": "TC-SYM-013", "text": "Frequent urination waking me at night", "expected_ids": ["S000226"]},
    {"id": "TC-SYM-014", "text": "Difficulty urinating with weak stream", "expected_ids": ["S000239"]},
    {"id": "TC-SYM-015", "text": "Blood in urine", "expected_ids": ["S000238"]},

    # Ocular, ENT & Abdominal (16-25)
    {"id": "TC-SYM-016", "text": "Severe eye pain and sensitivity to light", "expected_ids": ["S000212"]},
    {"id": "TC-SYM-017", "text": "Both eyes are very red and irritated", "expected_ids": ["S000213"]},
    {"id": "TC-SYM-018", "text": "Sudden blurred vision in my right eye", "expected_ids": ["S000210"]},
    {"id": "TC-SYM-019", "text": "Loss of appetite completely", "expected_ids": ["S000009"]},
    {"id": "TC-SYM-020", "text": "Sore throat and pain while swallowing", "expected_ids": ["S000032"]},
    {"id": "TC-SYM-021", "text": "Runny nose and sneezing", "expected_ids": ["S000035"]},
    {"id": "TC-SYM-022", "text": "Severe abdominal pain around belly button", "expected_ids": ["S000092"]},
    {"id": "TC-SYM-023", "text": "Dizziness and feeling lightheaded", "expected_ids": ["S000064"]},
    {"id": "TC-SYM-024", "text": "Muscle ache and generalized stiffness", "expected_ids": ["S000133"]},
    {"id": "TC-SYM-025", "text": "Severe chills and shaking rigors", "expected_ids": ["S000003"]},

    # Multi-Symptom Compound Clinical Scenarios (26-40)
    {"id": "TC-SYM-026", "text": "Patient presents with high fever, chills, and muscle aches for 3 days", "expected_ids": ["S000002", "S000003"]},
    {"id": "TC-SYM-027", "text": "Dry cough, shortness of breath, and chest tightness", "expected_ids": ["S000023", "S000026", "S000029"]},
    {"id": "TC-SYM-028", "text": "Nausea, projectile vomiting, and abdominal pain", "expected_ids": ["S000086", "S000087", "S000092"]},
    {"id": "TC-SYM-029", "text": "Severe headache, neck stiffness, and high fever", "expected_ids": ["S000061"]},
    {"id": "TC-SYM-030", "text": "Fatigue, loss of appetite, and significant weakness", "expected_ids": ["S000005", "S000009"]},
    {"id": "TC-SYM-031", "text": "Frequent urination, burning dysuria, and lower abdominal pain", "expected_ids": ["S000226", "S000237", "S000092"]},
    {"id": "TC-SYM-032", "text": "Red eyes, watery eye discharge, and blurred vision", "expected_ids": ["S000213", "S000210"]},
    {"id": "TC-SYM-033", "text": "Sore throat, runny nose, sneezing, and low grade fever", "expected_ids": ["S000032", "S000035", "S000001"]},
    {"id": "TC-SYM-034", "text": "Dizziness, lightheadedness, and cold sweats", "expected_ids": ["S000064"]},
    {"id": "TC-SYM-035", "text": "Swollen joints, morning stiffness, and chronic joint pain", "expected_ids": ["S000131"]},
    {"id": "TC-SYM-036", "text": "Chest pain radiating to left shoulder and shortness of breath", "expected_ids": ["S000046", "S000026"]},
    {"id": "TC-SYM-037", "text": "High fever, skin rash with petechiae, and joint pain", "expected_ids": ["S000109", "S000131"]},
    {"id": "TC-SYM-038", "text": "Difficulty breathing, wheezing, and productive cough", "expected_ids": ["S000026", "S000024"]},
    {"id": "TC-SYM-039", "text": "Burning urination and gross hematuria", "expected_ids": ["S000237", "S000238"]},
    {"id": "TC-SYM-040", "text": "Splitting headache, eye pain, and nausea", "expected_ids": ["S000061", "S000212", "S000086"]},

    # Colloquial & Vernacular English (41-55)
    {"id": "TC-SYM-041", "text": "My tummy hurts really bad", "expected_ids": ["S000092"]},
    {"id": "TC-SYM-042", "text": "I have been throwing up all night", "expected_ids": ["S000087"]},
    {"id": "TC-SYM-043", "text": "I am feeling totally wiped out and drained", "expected_ids": ["S000005"]},
    {"id": "TC-SYM-044", "text": "Splitting headache pounding behind my temples", "expected_ids": ["S000061"]},
    {"id": "TC-SYM-045", "text": "My belly feels crampy and loose motions", "expected_ids": ["S000092", "S000089"]},
    {"id": "TC-SYM-046", "text": "I have got the runs and tummy cramps", "expected_ids": ["S000089", "S000092"]},
    {"id": "TC-SYM-047", "text": "It burns like fire whenever I pee", "expected_ids": ["S000237"]},
    {"id": "TC-SYM-048", "text": "I need to pass water every 20 minutes", "expected_ids": ["S000226"]},
    {"id": "TC-SYM-049", "text": "I can hardly catch my breath", "expected_ids": ["S000026"]},
    {"id": "TC-SYM-050", "text": "My throat is scratchy and raw", "expected_ids": ["S000032"]},
    {"id": "TC-SYM-051", "text": "Head feels like it will explode", "expected_ids": ["S000061"]},
    {"id": "TC-SYM-052", "text": "I feel like barfing all the time", "expected_ids": ["S000086"]},
    {"id": "TC-SYM-053", "text": "Whole body is burning up hot", "expected_ids": ["S000001"]},
    {"id": "TC-SYM-054", "text": "I am shaking uncontrollably with shivering", "expected_ids": ["S000003"]},
    {"id": "TC-SYM-055", "text": "My eye looks bloodshot red", "expected_ids": ["S000213"]},

    # Complex Negations & Adversatives (56-70)
    {"id": "TC-SYM-056", "text": "I have a fever, but no cough at all", "expected_ids": ["S000001"], "negated_ids": ["S000023"]},
    {"id": "TC-SYM-057", "text": "Severe headache, but no vomiting and no nausea", "expected_ids": ["S000061"], "negated_ids": ["S000087", "S000086"]},
    {"id": "TC-SYM-058", "text": "Chest pain, but definitely not experiencing any shortness of breath", "expected_ids": ["S000046"], "negated_ids": ["S000026"]},
    {"id": "TC-SYM-059", "text": "Shortness of breath, without any chest pain", "expected_ids": ["S000026"], "negated_ids": ["S000046"]},
    {"id": "TC-SYM-060", "text": "Abdominal pain present, but denies diarrhea", "expected_ids": ["S000092"], "negated_ids": ["S000089"]},
    {"id": "TC-SYM-061", "text": "Patient has nausea, but has not vomited", "expected_ids": ["S000086"], "negated_ids": ["S000087"]},
    {"id": "TC-SYM-062", "text": "High temperature, no rash, no joint pain", "expected_ids": ["S000001"], "negated_ids": ["S000109", "S000131"]},
    {"id": "TC-SYM-063", "text": "Dry cough for 4 days, denies fever and denies chills", "expected_ids": ["S000023"], "negated_ids": ["S000001", "S000003"]},
    {"id": "TC-SYM-064", "text": "Burning urination, but no blood in urine", "expected_ids": ["S000237"], "negated_ids": ["S000238"]},
    {"id": "TC-SYM-065", "text": "I have body aches, however no headache and no fever", "expected_ids": ["S000011"], "negated_ids": ["S000061", "S000001"]},
    {"id": "TC-SYM-066", "text": "Eye is red, but there is no pain or blurred vision", "expected_ids": ["S000213"], "negated_ids": ["S000212", "S000210"]},
    {"id": "TC-SYM-067", "text": "Sore throat, but no runny nose", "expected_ids": ["S000032"], "negated_ids": ["S000035"]},
    {"id": "TC-SYM-068", "text": "Severe fatigue, but no loss of appetite", "expected_ids": ["S000005"], "negated_ids": ["S000009"]},
    {"id": "TC-SYM-069", "text": "Dizziness reported, but denies fainting or chest pain", "expected_ids": ["S000064"], "negated_ids": ["S000046"]},
    {"id": "TC-SYM-070", "text": "Cough present, negative for hemoptysis, negative for fever", "expected_ids": ["S000023"], "negated_ids": ["S000001"]},

    # Spelling Variations & Conversational Noise (71-80)
    {"id": "TC-SYM-071", "text": "I have bad hedache and fevr", "expected_ids": ["S000061", "S000001"]},
    {"id": "TC-SYM-072", "text": "Constant caugh and running nose", "expected_ids": ["S000023", "S000035"]},
    {"id": "TC-SYM-073", "text": "I ate spicy street food yesterday at lunch and today I have stomach pain and loose stools", "expected_ids": ["S000092", "S000089"]},
    {"id": "TC-SYM-074", "text": "Doctor please help, my mother has severe chest pain and breathlessness", "expected_ids": ["S000046", "S000026"]},
    {"id": "TC-SYM-075", "text": "Woke up this morning feeling nauseous and dizzy", "expected_ids": ["S000086"]},
    {"id": "TC-SYM-076", "text": "Joints are hurting and body ache all over", "expected_ids": ["S000011"]},
    {"id": "TC-SYM-077", "text": "I have been coughing continuously for the last 3 days with yellowish phlegm", "expected_ids": ["S000023"]},
    {"id": "TC-SYM-078", "text": "No symptoms at all, I feel completely fine and healthy", "expected_ids": [], "negated_ids": []},
    {"id": "TC-SYM-079", "text": "Just routine checkup, no fever, no pain", "expected_ids": [], "negated_ids": ["S000001"]},
    {"id": "TC-SYM-080", "text": "Terrible shivering rigors followed by 103F temperature", "expected_ids": ["S000003"]}
]

# ==============================================================================
# CATEGORY C: MULTILINGUAL CLINICAL UNDERSTANDING (50 Cases)
# ==============================================================================
MULTILINGUAL_TEST_CASES = [
    # Hindi Devanagari (1-15)
    {"id": "TC-ML-001", "lang": "hi", "text": "मुझे दो दिन से बहुत तेज बुखार और सूखी खांसी है", "expected_ids": ["S000001", "S000023"]},
    {"id": "TC-ML-002", "lang": "hi", "text": "छाती में तेज दर्द और सांस लेने में तकलीफ हो रही है", "expected_ids": ["S000046", "S000026"]},
    {"id": "TC-ML-003", "lang": "hi", "text": "सिरदर्द है लेकिन बुखार नहीं है", "expected_ids": ["S000061"], "negated_ids": ["S000001"]},
    {"id": "TC-ML-004", "lang": "hi", "text": "पेशाब में जलन और बार-बार पेशाब आना", "expected_ids": ["S000237", "S000226"]},
    {"id": "TC-ML-005", "lang": "hi", "text": "गले में खराश और बदन दर्द है", "expected_ids": ["S000032", "S000011"]},
    {"id": "TC-ML-006", "lang": "hi", "text": "उल्टी और दस्त हो रहे हैं", "expected_ids": ["S000087", "S000089"]},
    {"id": "TC-ML-007", "lang": "hi", "text": "पेट में बहुत तेज मरोड़ और दर्द है", "expected_ids": ["S000092"]},
    {"id": "TC-ML-008", "lang": "hi", "text": "बहुत ज्यादा कमजोरी और थकान महसूस हो रही है", "expected_ids": ["S000005"]},
    {"id": "TC-ML-009", "lang": "hi", "text": "चक्कर आ रहे हैं और जी मिचला रहा है", "expected_ids": ["S000064", "S000086"]},
    {"id": "TC-ML-010", "lang": "hi", "text": "जोड़ों में असहनीय दर्द और सूजन है", "expected_ids": ["S000131"]},
    {"id": "TC-ML-011", "lang": "hi", "text": "आंखें लाल हो गई हैं और उनमें दर्द है", "expected_ids": ["S000213", "S000212"]},
    {"id": "TC-ML-012", "lang": "hi", "text": "पेशाब में खून आ रहा है", "expected_ids": ["S000238"]},
    {"id": "TC-ML-013", "lang": "hi", "text": "खांसी है परंतु सीने में दर्द नहीं है", "expected_ids": ["S000023"], "negated_ids": ["S000046"]},
    {"id": "TC-ML-014", "lang": "hi", "text": "भूख बिल्कुल नहीं लग रही है और वजन कम हो गया है", "expected_ids": ["S000009"]},
    {"id": "TC-ML-015", "lang": "hi", "text": "तेज ठंड लगकर कंपकंपी के साथ बुखार आया", "expected_ids": ["S000003", "S000001"]},

    # Gujarati Script (16-30)
    {"id": "TC-ML-016", "lang": "gu", "text": "મને ત્રણ દિવસથી તાવ અને માથાનો દુખાવો છે", "expected_ids": ["S000001", "S000061"]},
    {"id": "TC-ML-017", "lang": "gu", "text": "છાતીમાં દુખાવો થાય છે અને શ્વાસ લેવામાં તકલીફ છે", "expected_ids": ["S000046", "S000026"]},
    {"id": "TC-ML-018", "lang": "gu", "text": "તાવ નથી પણ પેટમાં દુખાવો થાય છે", "expected_ids": ["S000092"], "negated_ids": ["S000001"]},
    {"id": "TC-ML-019", "lang": "gu", "text": "પેશાબ કરતી વખતે બળતરા થાય છે અને વારંવાર પેશાબ જવું પડે છે", "expected_ids": ["S000237", "S000226"]},
    {"id": "TC-ML-020", "lang": "gu", "text": "ઉલટી અને ઝાડા થઈ ગયા છે", "expected_ids": ["S000087", "S000089"]},
    {"id": "TC-ML-021", "lang": "gu", "text": "ગળામાં દુખાવો અને સૂકી ઉધરસ છે", "expected_ids": ["S000032", "S000023"]},
    {"id": "TC-ML-022", "lang": "gu", "text": "શરીરમાં ખૂબ જ થાક અને અશક્તિ લાગે છે", "expected_ids": ["S000005"]},
    {"id": "TC-ML-023", "lang": "gu", "text": "ચક્કર આવે છે અને જીવ ગભરાય છે", "expected_ids": ["S000064", "S000086"]},
    {"id": "TC-ML-024", "lang": "gu", "text": "ઢીંચણમાં અને સાંધામાં દુખાવો થાય છે", "expected_ids": ["S000131"]},
    {"id": "TC-ML-025", "lang": "gu", "text": "આંખો લાલ થઈ ગઈ છે", "expected_ids": ["S000213"]},
    {"id": "TC-ML-026", "lang": "gu", "text": "પેશાબમાં લોહી દેખાય છે", "expected_ids": ["S000238"]},
    {"id": "TC-ML-027", "lang": "gu", "text": "ઉધરસ છે પણ તાવ નથી", "expected_ids": ["S000023"], "negated_ids": ["S000001"]},
    {"id": "TC-ML-028", "lang": "gu", "text": "ધ્રુજારી સાથે સખત ટાઢ વાય છે", "expected_ids": ["S000003"]},
    {"id": "TC-ML-029", "lang": "gu", "text": "આખું શરીર દુખે છે અને કળતર થાય છે", "expected_ids": ["S000011"]},
    {"id": "TC-ML-030", "lang": "gu", "text": "ભૂખ નથી લાગતી", "expected_ids": ["S000009"]},

    # Hinglish - Roman Hindi (31-40)
    {"id": "TC-ML-031", "lang": "en", "text": "Mujhe 2 din se tez bukhar aur khansi hai", "expected_ids": ["S000001", "S000023"]},
    {"id": "TC-ML-032", "lang": "en", "text": "Chhati me dard hai aur saans lene me takleef ho rahi hai", "expected_ids": ["S000046", "S000026"]},
    {"id": "TC-ML-033", "lang": "en", "text": "Bukhar nahi hai lekin sar dard bahut zyada hai", "expected_ids": ["S000061"], "negated_ids": ["S000001"]},
    {"id": "TC-ML-034", "lang": "en", "text": "Peshab me jalan ho rahi hai aur baar baar jana padta hai", "expected_ids": ["S000237", "S000226"]},
    {"id": "TC-ML-035", "lang": "en", "text": "Pet dard aur ulti dast ho rahe hain", "expected_ids": ["S000092", "S000087", "S000089"]},
    {"id": "TC-ML-036", "lang": "en", "text": "Gale me dard aur badan dard hai", "expected_ids": ["S000032", "S000011"]},
    {"id": "TC-ML-037", "lang": "en", "text": "Chakkar aa raha hai aur ulti jaisa lag raha hai", "expected_ids": ["S000064", "S000086"]},
    {"id": "TC-ML-038", "lang": "en", "text": "Jodo me dard aur sujan hai", "expected_ids": ["S000131"]},
    {"id": "TC-ML-039", "lang": "en", "text": "Khansi hai par chhati me dard bilkul nahi hai", "expected_ids": ["S000023"], "negated_ids": ["S000046"]},
    {"id": "TC-ML-040", "lang": "en", "text": "Thand lag ke kampkampi aur bukhar aa gaya", "expected_ids": ["S000003", "S000001"]},

    # Gujlish - Roman Gujarati (41-45)
    {"id": "TC-ML-041", "lang": "en", "text": "Mane 3 divas thi taav ane mathano dukhavo chhe", "expected_ids": ["S000001", "S000061"]},
    {"id": "TC-ML-042", "lang": "en", "text": "Chhati ma dukhe chhe ane shwas leva ma taklif chhe", "expected_ids": ["S000046", "S000026"]},
    {"id": "TC-ML-043", "lang": "en", "text": "Taav nathi pan pet ma dukhavo thay chhe", "expected_ids": ["S000092"], "negated_ids": ["S000001"]},
    {"id": "TC-ML-044", "lang": "en", "text": "Peshab ma balatra thay chhe", "expected_ids": ["S000237"]},
    {"id": "TC-ML-045", "lang": "en", "text": "Ulti ane jhada thai gaya chhe", "expected_ids": ["S000087", "S000089"]},

    # Code-Mixed Sentences (46-50)
    {"id": "TC-ML-046", "lang": "en", "text": "Doctor, mujhe mild fever hai and severe body ache ho raha hai since yesterday", "expected_ids": ["S000001", "S000011"]},
    {"id": "TC-ML-047", "lang": "en", "text": "Patient has dry cough and gale me kharash", "expected_ids": ["S000023", "S000032"]},
    {"id": "TC-ML-048", "lang": "en", "text": "I feel extreme fatigue aur sar dard bahut tez hai", "expected_ids": ["S000005", "S000061"]},
    {"id": "TC-ML-049", "lang": "en", "text": "Chest pain ho raha hai and shortness of breath without any fever", "expected_ids": ["S000046", "S000026"], "negated_ids": ["S000001"]},
    {"id": "TC-ML-050", "lang": "en", "text": "Burning sensation while peeing and baar baar peshab aana", "expected_ids": ["S000237", "S000226"]}
]

# ==============================================================================
# CATEGORY D: MEDICAL HISTORY, ALLERGIES & CONTRAINDICATIONS (40 Cases)
# ==============================================================================
HISTORY_TEST_CASES = [
    {"id": "TC-HIST-001", "conditions": ["Hypertension"], "meds": ["Amlodipine 5mg"], "allergies": [], "contraindicated_check": "Avoid decongestants like pseudoephedrine"},
    {"id": "TC-HIST-002", "conditions": ["Type 2 Diabetes"], "meds": ["Metformin 500mg"], "allergies": [], "contraindicated_check": "Avoid sugar syrups, cautious steroids"},
    {"id": "TC-HIST-003", "conditions": ["Bronchial Asthma"], "meds": ["Salbutamol Inhaler"], "allergies": [], "contraindicated_check": "NSAIDs / Non-selective beta blockers contraindicated"},
    {"id": "TC-HIST-004", "conditions": ["Chronic Kidney Disease"], "meds": ["Torsemide"], "allergies": [], "contraindicated_check": "NSAIDs contraindicated, dosage adjustments needed"},
    {"id": "TC-HIST-005", "conditions": ["Peptic Ulcer Disease"], "meds": ["Pantoprazole 40mg"], "allergies": [], "contraindicated_check": "Aspirin & NSAIDs contraindicated due to GI bleed"},
    {"id": "TC-HIST-006", "conditions": ["Liver Cirrhosis"], "meds": ["Spironolactone"], "allergies": [], "contraindicated_check": "High-dose paracetamol contraindicated"},
    {"id": "TC-HIST-007", "conditions": ["Epilepsy"], "meds": ["Levetiracetam 500mg"], "allergies": [], "contraindicated_check": "Tramadol & fluoroquinolones lower seizure threshold"},
    {"id": "TC-HIST-008", "conditions": ["Coronary Artery Disease"], "meds": ["Aspirin 75mg", "Atorvastatin 20mg"], "allergies": [], "contraindicated_check": "Selective COX-2 inhibitors caution"},
    {"id": "TC-HIST-009", "conditions": ["Hypothyroidism"], "meds": ["Levothyroxine 50mcg"], "allergies": [], "contraindicated_check": "Calcium / Iron supplements spaced 4 hours"},
    {"id": "TC-HIST-010", "conditions": ["Gout"], "meds": ["Allopurinol 100mg"], "allergies": [], "contraindicated_check": "Thiazide diuretics contraindicated"},

    {"id": "TC-HIST-011", "conditions": [], "meds": [], "allergies": ["Penicillin"], "disallowed_drugs": ["Amoxicillin", "Ampicillin", "Augmentin"]},
    {"id": "TC-HIST-012", "conditions": [], "meds": [], "allergies": ["Sulfa drugs", "Sulfonamides"], "disallowed_drugs": ["Co-trimoxazole", "Sulfamethoxazole"]},
    {"id": "TC-HIST-013", "conditions": [], "meds": [], "allergies": ["Aspirin", "NSAIDs"], "disallowed_drugs": ["Aspirin", "Ibuprofen", "Diclofenac", "Naproxen"]},
    {"id": "TC-HIST-014", "conditions": [], "meds": [], "allergies": ["Cephalosporins"], "disallowed_drugs": ["Cefixime", "Ceftriaxone", "Cephalexin"]},
    {"id": "TC-HIST-015", "conditions": [], "meds": [], "allergies": ["Fluoroquinolones", "Ciprofloxacin"], "disallowed_drugs": ["Ciprofloxacin", "Levofloxacin", "Ofloxacin"]},
    {"id": "TC-HIST-016", "conditions": [], "meds": [], "allergies": ["Macrolides"], "disallowed_drugs": ["Azithromycin", "Clarithromycin", "Erythromycin"]},
    {"id": "TC-HIST-017", "conditions": [], "meds": [], "allergies": ["Codeine"], "disallowed_drugs": ["Codeine syrup", "Co-codamol"]},
    {"id": "TC-HIST-018", "conditions": [], "meds": [], "allergies": ["Paracetamol"], "disallowed_drugs": ["Paracetamol", "Acetaminophen"]},
    {"id": "TC-HIST-019", "conditions": [], "meds": [], "allergies": ["Metronidazole"], "disallowed_drugs": ["Metronidazole", "Flagyl"]},
    {"id": "TC-HIST-020", "conditions": [], "meds": [], "allergies": ["Multiple Drug Allergy (Penicillin, Sulfa)"], "disallowed_drugs": ["Amoxicillin", "Co-trimoxazole"]},

    {"id": "TC-HIST-021", "conditions": ["Afib"], "meds": ["Warfarin 5mg"], "allergies": [], "interaction_risk": "Warfarin + NSAIDs increases major hemorrhage risk"},
    {"id": "TC-HIST-022", "conditions": ["Hypertension"], "meds": ["Lisinopril 10mg"], "allergies": [], "interaction_risk": "ACE inhibitors + Potassium sparing diuretics hyperkalemia"},
    {"id": "TC-HIST-023", "conditions": ["Heart Failure"], "meds": ["Digoxin 0.25mg"], "allergies": [], "interaction_risk": "Digoxin + Clarithromycin increases digoxin toxicity"},
    {"id": "TC-HIST-024", "conditions": ["Depression"], "meds": ["Sertraline 50mg"], "allergies": [], "interaction_risk": "SSRI + Tramadol increases serotonin syndrome risk"},
    {"id": "TC-HIST-025", "conditions": ["CAD"], "meds": ["Clopidogrel 75mg"], "allergies": [], "interaction_risk": "Clopidogrel + Omeprazole reduces antiplatelet efficacy"},
    {"id": "TC-HIST-026", "conditions": ["Diabetes"], "meds": ["Glimepiride 2mg"], "allergies": [], "interaction_risk": "Sulfonylurea + Fluconazole increases severe hypoglycemia"},
    {"id": "TC-HIST-027", "conditions": ["BPH"], "meds": ["Tamsulosin 0.4mg"], "allergies": [], "interaction_risk": "Alpha blockers + PDE5 inhibitors severe orthostatic hypotension"},
    {"id": "TC-HIST-028", "conditions": ["Dyslipidemia"], "meds": ["Simvastatin 40mg"], "allergies": [], "interaction_risk": "Simvastatin + Erythromycin increases rhabdomyolysis risk"},
    {"id": "TC-HIST-029", "conditions": ["Transplant"], "meds": ["Tacrolimus 1mg"], "allergies": [], "interaction_risk": "Tacrolimus + Azole antifungals increases nephrotoxicity"},
    {"id": "TC-HIST-030", "conditions": ["Osteoporosis"], "meds": ["Alendronate 70mg"], "allergies": [], "interaction_risk": "Bisphosphonates + NSAIDs increases severe esophageal ulceration"},

    {"id": "TC-HIST-031", "conditions": ["Pregnancy 1st Trimester"], "meds": ["Folic Acid 5mg"], "allergies": [], "pregnancy_contraindicated": ["Methotrexate", "Warfarin", "ACE inhibitors", "Statins"]},
    {"id": "TC-HIST-032", "conditions": ["Pregnancy 3rd Trimester"], "meds": ["Iron"], "allergies": [], "pregnancy_contraindicated": ["NSAIDs (premature closure of ductus arteriosus)"]},
    {"id": "TC-HIST-033", "conditions": ["Lactation / Breastfeeding"], "meds": ["Prenatal vitamins"], "allergies": [], "lactation_cautious": ["Amiodarone", "Codeine", "Tetracyclines"]},
    {"id": "TC-HIST-034", "conditions": ["End-stage Renal Disease (ESRD)"], "meds": ["Sevelamer"], "allergies": [], "renal_contraindicated": ["Metformin", "Aminoglycosides", "NSAIDs"]},
    {"id": "TC-HIST-035", "conditions": ["Severe Acute Hepatitis"], "meds": [], "allergies": [], "hepatic_contraindicated": ["High-dose Acetaminophen", "Isoniazid", "Ketoconazole"]},
    {"id": "TC-HIST-036", "conditions": ["G6PD Deficiency"], "meds": [], "allergies": [], "hemolysis_risk": ["Dapsone", "Primaquine", "Rasburicase", "Nitrofurantoin"]},
    {"id": "TC-HIST-037", "conditions": ["Myasthenia Gravis"], "meds": ["Pyridostigmine"], "allergies": [], "contraindicated": ["Aminoglycosides", "Telithromycin", "Fluoroquinolones"]},
    {"id": "TC-HIST-038", "conditions": ["Narrow-angle Glaucoma"], "meds": ["Latanoprost"], "allergies": [], "contraindicated": ["Anticholinergics", "First gen antihistamines"]},
    {"id": "TC-HIST-039", "conditions": ["Severe Bleeding Diathesis (Hemophilia)"], "meds": ["Factor VIII"], "allergies": [], "contraindicated": ["Anticoagulants", "Antiplatelets", "NSAIDs"]},
    {"id": "TC-HIST-040", "conditions": ["Active Tuberculosis on ATT"], "meds": ["Rifampicin", "Isoniazid", "Pyrazinamide", "Ethambutol"], "allergies": [], "caution": "Extensive CYP3A4 induction by Rifampicin"}
]

# ==============================================================================
# CATEGORY E: VOICE & IMAGE WORKFLOW (30 Cases)
# ==============================================================================
VOICE_IMAGE_TEST_CASES = [
    # Voice Transcripts with Conversational Noise, Fillers & Dialectal Pauses (1-15)
    {"id": "TC-VI-001", "type": "voice", "transcript": "uh hello doctor um I have had this really bad fever and uh cough for two days", "expected_ids": ["S000001", "S000023"]},
    {"id": "TC-VI-002", "type": "voice", "transcript": "so basically um I woke up with chest pain and like shortness of breath", "expected_ids": ["S000046", "S000026"]},
    {"id": "TC-VI-003", "type": "voice", "transcript": "uh severe headache you know and feeling like vomiting", "expected_ids": ["S000061", "S000086"]},
    {"id": "TC-VI-004", "type": "voice", "transcript": "yeah doctor pet me dard hai bahut tez and loose motions ho rahe hain", "expected_ids": ["S000092", "S000089"]},
    {"id": "TC-VI-005", "type": "voice", "transcript": "umm mane tran divas thi mathano dukhavo chhe ane taav aave chhe", "expected_ids": ["S000061", "S000001"]},
    {"id": "TC-VI-006", "type": "voice", "transcript": "uh throat hurts when swallowing and running nose", "expected_ids": ["S000032", "S000035"]},
    {"id": "TC-VI-007", "type": "voice", "transcript": "like I am sweating and having cold chills rigors", "expected_ids": ["S000003"]},
    {"id": "TC-VI-008", "type": "voice", "transcript": "burning while passing urine you know burning micturition", "expected_ids": ["S000237"]},
    {"id": "TC-VI-009", "type": "voice", "transcript": "feeling completely exhausted fatigue and no appetite at all", "expected_ids": ["S000005", "S000009"]},
    {"id": "TC-VI-010", "type": "voice", "transcript": "my eyes are very red and irritated since yesterday", "expected_ids": ["S000213"]},
    {"id": "TC-VI-011", "type": "voice", "transcript": "doctor I feel very dizzy like room is spinning around", "expected_ids": ["S000064"]},
    {"id": "TC-VI-012", "type": "voice", "transcript": "uh joints are aching especially both knees and morning stiffness", "expected_ids": ["S000131"]},
    {"id": "TC-VI-013", "type": "voice", "transcript": "red itchy rash spreading all over my chest and back", "expected_ids": ["S000109"]},
    {"id": "TC-VI-014", "type": "voice", "transcript": "uh I have fever but you know no cough and definitely no chest pain", "expected_ids": ["S000001"], "negated_ids": ["S000023", "S000046"]},
    {"id": "TC-VI-015", "type": "voice", "transcript": "just general weakness and body pain all over", "expected_ids": ["S000005", "S000011"]},

    # OCR Lab Report & Clinical Findings Text (16-30)
    {"id": "TC-VI-016", "type": "ocr", "report_text": "LAB REPORT: Hb: 8.2 g/dL (Low), Platelets: 65,000/mcL (Thrombocytopenia), TLC: 14,200/mcL (Leukocytosis). Patient reports high fever and petechial rash.", "expected_ids": ["S000001", "S000109"]},
    {"id": "TC-VI-017", "type": "ocr", "report_text": "URINE ROUTINE: Pus cells: 35-40/HPF, RBCs: 15-20/HPF (Microscopic Hematuria), Bacteria: Plentiful. Patient complains of burning dysuria and increased frequency.", "expected_ids": ["S000237", "S000226", "S000238"]},
    {"id": "TC-VI-018", "type": "ocr", "report_text": "CHEST X-RAY PA VIEW: Right lower lobe consolidation consistent with bacterial lobar pneumonia. Symptoms: Productive cough, dyspnea, and high-grade fever.", "expected_ids": ["S000023", "S000026", "S000001"]},
    {"id": "TC-VI-019", "type": "ocr", "report_text": "ECG REPORT: ST-segment elevation in leads II, III, aVF. Diagnosis: Inferior wall STEMI. Patient experienced crushing substernal chest pain and diaphoresis.", "expected_ids": ["S000046"]},
    {"id": "TC-VI-020", "type": "ocr", "report_text": "BIOCHEMISTRY REPORT: Fasting Blood Glucose: 280 mg/dL, HbA1c: 11.2%. Patient notes polydipsia, polyuria (frequent urination), and unexplained fatigue.", "expected_ids": ["S000226", "S000005"]},
    {"id": "TC-VI-021", "type": "ocr", "report_text": "LIVER FUNCTION TEST: Total Bilirubin: 5.4 mg/dL (Elevated), ALT: 450 U/L, AST: 380 U/L. Clinical presentation: Jaundice, nausea, fatigue, and right upper quadrant pain.", "expected_ids": ["S000086", "S000005", "S000092"]},
    {"id": "TC-VI-022", "type": "ocr", "report_text": "KIDNEY FUNCTION TEST: Serum Creatinine: 4.8 mg/dL, Blood Urea: 110 mg/dL. Symptoms: Oliguria (difficulty urinating), generalized edema, and fatigue.", "expected_ids": ["S000239", "S000005"]},
    {"id": "TC-VI-023", "type": "ocr", "report_text": "OPHTHALMOLOGY EXAM: Conjunctival injection bilateral, purulent discharge. Symptoms: Eye redness, eye pain, and blurred vision.", "expected_ids": ["S000213", "S000212", "S000210"]},
    {"id": "TC-VI-024", "type": "ocr", "report_text": "GASTROENTEROLOGY NOTES: Endoscopy confirms acute gastric ulceration. Clinical: Epigastric abdominal pain, nausea, and coffee-ground vomiting.", "expected_ids": ["S000092", "S000086", "S000087"]},
    {"id": "TC-VI-025", "type": "ocr", "report_text": "NEUROLOGY EVALUATION: Sudden onset left hemiparesis and facial droop. Symptoms: Severe sudden headache and dizziness.", "expected_ids": ["S000061", "S000064"]},
    {"id": "TC-VI-026", "type": "ocr", "report_text": "PEDIATRIC CLINICAL NOTE: Child age 4. Low grade fever, barky cough, inspiratory stridor, and runny nose.", "expected_ids": ["S000001", "S000023", "S000035"]},
    {"id": "TC-VI-027", "type": "ocr", "report_text": "ENT EXAMINATION: Hyperemic pharynx, tonsillar exudates present. Patient symptoms: Severe sore throat and difficulty swallowing.", "expected_ids": ["S000032"]},
    {"id": "TC-VI-028", "type": "ocr", "report_text": "DERMATOLOGY CONSULT: Diffuse maculopapular erythematous skin rash with pruritus and mild fever.", "expected_ids": ["S000109", "S000001"]},
    {"id": "TC-VI-029", "type": "ocr", "report_text": "RHEUMATOLOGY WORKUP: Positive Anti-CCP, RF 120 IU/mL. Symptoms: Symmetrical joint pain, joint swelling, and early morning stiffness.", "expected_ids": ["S000131"]},
    {"id": "TC-VI-030", "type": "ocr", "report_text": "INFECTIOUS DISEASE PANEL: Dengue NS1 Antigen Positive. Clinical triad: High fever, eye pain, severe muscle and joint pain.", "expected_ids": ["S000001", "S000212", "S000133", "S000131"]}
]

# ==============================================================================
# CATEGORY F: CLINICAL TRIAGE, RED FLAGS & CARE RECOMMENDATIONS (40 Cases)
# ==============================================================================
TRIAGE_MEDICINE_TEST_CASES = [
    # Critical Red Flag Emergency Conditions (1-12)
    {"id": "TC-TRI-001", "name": "Acute Coronary Syndrome", "symptoms": ["chest pain", "shortness of breath", "sweating"], "patient": {"age_group": "51-60", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-002", "name": "Anaphylaxis", "symptoms": ["shortness of breath", "skin rash", "dizziness"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-003", "name": "Acute Stroke", "symptoms": ["headache", "dizziness", "blurred vision"], "patient": {"age_group": "61+", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-004", "name": "Meningitis Triad", "symptoms": ["fever", "headache", "vomiting"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-3 Days", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-005", "name": "Severe Sepsis Alert", "symptoms": ["fever", "chills", "dizziness", "shortness of breath"], "patient": {"age_group": "61+", "gender": "Female", "duration": "1-3 Days", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-006", "name": "Acute Pulmonary Embolism", "symptoms": ["chest pain", "shortness of breath", "cough"], "patient": {"age_group": "41-50", "gender": "Female", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-007", "name": "Acute Gastrointestinal Hemorrhage", "symptoms": ["vomiting", "abdominal pain", "dizziness", "fatigue"], "patient": {"age_group": "51-60", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-008", "name": "Acute Respiratory Distress", "symptoms": ["shortness of breath", "cough", "fatigue"], "patient": {"age_group": "61+", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-009", "name": "Hypertensive Crisis Presentation", "symptoms": ["headache", "chest pain", "blurred vision"], "patient": {"age_group": "51-60", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-010", "name": "Acute Surgical Abdomen", "symptoms": ["abdominal pain", "vomiting", "fever"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-011", "name": "Severe Dehydration Shock", "symptoms": ["vomiting", "diarrhea", "dizziness", "fatigue"], "patient": {"age_group": "0-10", "gender": "Female", "duration": "1-3 Days", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},
    {"id": "TC-TRI-012", "name": "Gross Hematuria with Acute Retention", "symptoms": ["blood in urine", "difficulty urinating", "abdominal pain"], "patient": {"age_group": "61+", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True, "min_urgency": "High"},

    # Non-Emergency Common Primary Care Conditions (13-25)
    {"id": "TC-TRI-013", "name": "Common Cold / Viral URI", "symptoms": ["runny nose", "sore throat", "cough"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-3 Days", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-014", "name": "Tension Headache", "symptoms": ["headache"], "patient": {"age_group": "31-40", "gender": "Female", "duration": "Started Today", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-015", "name": "Mild Acute Gastroenteritis", "symptoms": ["nausea", "diarrhea", "abdominal pain"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-3 Days", "severity": "Moderate"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-016", "name": "Allergic Rhinitis", "symptoms": ["runny nose", "sneezing", "red eyes"], "patient": {"age_group": "11-20", "gender": "Female", "duration": "1-2 Weeks", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-017", "name": "Uncomplicated Cystitis / UTI", "symptoms": ["painful urination", "frequent urination"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "1-3 Days", "severity": "Moderate"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-018", "name": "Mild Viral Pharyngitis", "symptoms": ["sore throat", "fever"], "patient": {"age_group": "11-20", "gender": "Male", "duration": "1-3 Days", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-019", "name": "Localized Skin Contact Dermatitis", "symptoms": ["skin rash"], "patient": {"age_group": "31-40", "gender": "Male", "duration": "3-5 Days", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-020", "name": "Chronic Knee Osteoarthritis", "symptoms": ["joint pain"], "patient": {"age_group": "61+", "gender": "Female", "duration": "More than 2 Weeks", "severity": "Moderate"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-021", "name": "Acute Sinusitis", "symptoms": ["headache", "runny nose", "fever"], "patient": {"age_group": "31-40", "gender": "Male", "duration": "1-2 Weeks", "severity": "Moderate"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-022", "name": "Mild Viral Fever", "symptoms": ["fever", "body ache", "fatigue"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "1-3 Days", "severity": "Moderate"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-023", "name": "Conjunctivitis / Pink Eye", "symptoms": ["red eyes", "eye pain"], "patient": {"age_group": "11-20", "gender": "Male", "duration": "1-3 Days", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-024", "name": "Post-viral Asthenia", "symptoms": ["fatigue"], "patient": {"age_group": "31-40", "gender": "Female", "duration": "1-2 Weeks", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},
    {"id": "TC-TRI-025", "name": "Muscular Neck Strain", "symptoms": ["muscle ache", "headache"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "3-5 Days", "severity": "Mild"}, "expected_emergency": False, "max_urgency": "Moderate"},

    # Gender & Anatomical Filtering Invariants (26-32)
    {"id": "TC-TRI-026", "name": "Male anatomical filter", "symptoms": ["abdominal pain", "fatigue"], "patient": {"age_group": "41-50", "gender": "Male", "duration": "1-2 Weeks"}, "disallowed_conditions": ["ovarian cancer", "cervical cancer", "endometriosis", "pregnancy complications", "uterine fibroids"]},
    {"id": "TC-TRI-027", "name": "Female anatomical filter", "symptoms": ["difficulty urinating", "frequent urination"], "patient": {"age_group": "51-60", "gender": "Female", "duration": "1-3 Days"}, "disallowed_conditions": ["prostate cancer", "benign prostatic hyperplasia", "prostatitis", "epididymitis", "testicular torsion"]},
    {"id": "TC-TRI-028", "name": "Pediatric condition safety", "symptoms": ["fever", "cough"], "patient": {"age_group": "0-10", "gender": "Male", "duration": "1-3 Days"}, "disallowed_meds": ["Aspirin (Adult 325mg)", "Ciprofloxacin (fluoroquinolones avoid in pediatrics)"]},
    {"id": "TC-TRI-029", "name": "Geriatric medication safety", "symptoms": ["insomnia", "dizziness"], "patient": {"age_group": "61+", "gender": "Female", "duration": "1-2 Weeks"}, "disallowed_meds": ["High dose long-acting benzodiazepines (Beers criteria)"]},
    {"id": "TC-TRI-030", "name": "Pregnancy medication safety", "symptoms": ["headache", "fever"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "1-3 Days", "pregnancy": True}, "disallowed_meds": ["Ibuprofen (3rd trimester)", "Aspirin", "ACE Inhibitors"]},
    {"id": "TC-TRI-031", "name": "Penicillin allergy safety", "symptoms": ["sore throat", "fever"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "3-5 Days", "allergies": ["Penicillin"]}, "disallowed_meds": ["Amoxicillin", "Ampicillin", "Augmentin"]},
    {"id": "TC-TRI-032", "name": "Renal failure safety", "symptoms": ["joint pain", "fever"], "patient": {"age_group": "51-60", "gender": "Male", "duration": "3-5 Days", "history": ["Chronic Kidney Disease"]}, "disallowed_meds": ["Diclofenac", "Naproxen", "Ibuprofen"]},

    # Anti-Fabrication & Source Tracking Verification (33-40)
    {"id": "TC-TRI-033", "name": "No unvalidated conditions", "symptoms": ["fever", "headache"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-3 Days"}, "assert_has_source_metadata": True},
    {"id": "TC-TRI-034", "name": "Score sanity bound", "symptoms": ["fatigue"], "patient": {"age_group": "31-40", "gender": "Female", "duration": "Started Today"}, "max_match_score": 95},
    {"id": "TC-TRI-035", "name": "Dynamic condition count", "symptoms": ["fever", "chills", "muscle ache", "headache", "fatigue"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "3-5 Days"}, "min_condition_count": 1},
    {"id": "TC-TRI-036", "name": "Valid dosage formulation present", "symptoms": ["fever"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-3 Days"}, "assert_valid_dosage_form": True},
    {"id": "TC-TRI-037", "name": "Offline fallback transparency", "symptoms": ["cough"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-3 Days"}, "force_offline": True, "assert_fallback_flag": True},
    {"id": "TC-TRI-038", "name": "ICD code format validity", "symptoms": ["chest pain", "shortness of breath"], "patient": {"age_group": "51-60", "gender": "Male", "duration": "Started Today"}, "assert_icd_structure": True},
    {"id": "TC-TRI-039", "name": "Care recommendations structure", "symptoms": ["headache"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "Started Today"}, "assert_care_fields": ["immediate_actions", "lifestyle_recommendations", "when_to_see_doctor"]},
    {"id": "TC-TRI-040", "name": "Zero fabricated medicine names", "symptoms": ["fever", "cough"], "patient": {"age_group": "31-40", "gender": "Male", "duration": "1-3 Days"}, "assert_pharmacopeia_whitelist": True}
]

# ==============================================================================
# CATEGORY G: PERSISTENCE, CONCURRENCY & ISOLATION (20 Cases)
# ==============================================================================
PERSISTENCE_ISOLATION_TEST_CASES = [
    {"id": "TC-REG-001", "name": "Direct jump to Step 4 blocked without Demographics/Symptoms", "target_step": 4, "session_data": {}, "expected_allowed": False},
    {"id": "TC-REG-002", "name": "Direct jump to Step 3 blocked without Demographics", "target_step": 3, "session_data": {"symptoms": ["fever"]}, "expected_allowed": False},
    {"id": "TC-REG-003", "name": "Direct jump to Step 2 allowed when Step 1 valid", "target_step": 2, "session_data": {"age": 25, "gender": "Male", "state": "Gujarat"}, "expected_allowed": True},
    {"id": "TC-REG-004", "name": "Jump to Step 4 allowed when Steps 1, 2, 3 complete", "target_step": 4, "session_data": {"age": 25, "gender": "Male", "state": "Gujarat", "selected_symptoms": ["S000001"], "duration": "1-3 Days", "severity": "Moderate"}, "expected_allowed": True},
    {"id": "TC-REG-005", "name": "Bypass symptom selection to Step 4 blocked", "target_step": 4, "session_data": {"age": 25, "gender": "Male", "state": "Gujarat", "selected_symptoms": []}, "expected_allowed": False},

    {"id": "TC-REG-006", "name": "Symptom removal in Step 2 clears previous triage cache", "action": "remove_symptom", "initial_symptoms": ["chest pain", "shortness of breath"], "modified_symptoms": ["headache"], "assert_cache_invalidated": True},
    {"id": "TC-REG-007", "name": "Gender change in Step 1 updates anatomical filters", "action": "change_gender", "initial_gender": "Female", "modified_gender": "Male", "assert_filter_updated": True},
    {"id": "TC-REG-008", "name": "Age tier change in Step 1 recalculates age group", "action": "change_age", "initial_age": 8, "modified_age": 65, "expected_groups": ("0-10", "61+")},
    {"id": "TC-REG-009", "name": "Allergy addition dynamically blocks previously recommended drug", "action": "add_allergy", "symptoms": ["fever", "cough"], "allergy": "Penicillin", "blocked_drug": "Amoxicillin"},
    {"id": "TC-REG-010", "name": "Language change preserves clinical symptom selection", "action": "change_language", "initial_lang": "en", "new_lang": "hi", "symptoms": ["S000001", "S000023"]},

    {"id": "TC-REG-011", "name": "Concurrent user isolation Patient A (Pediatric) vs Patient B (Geriatric)", "user_a": {"age": 4, "gender": "Male"}, "user_b": {"age": 78, "gender": "Female"}, "assert_zero_leakage": True},
    {"id": "TC-REG-012", "name": "Concurrent session symptom isolation", "user_a_symptoms": ["S000046"], "user_b_symptoms": ["S000089"], "assert_zero_leakage": True},
    {"id": "TC-REG-013", "name": "Concurrent allergy isolation (User A allergic to Penicillin, User B not)", "user_a_allergy": ["Penicillin"], "user_b_allergy": [], "assert_zero_leakage": True},
    {"id": "TC-REG-014", "name": "Simulated multi-tab navigation state consistency", "action": "rapid_step_switch", "assert_no_state_corruption": True},
    {"id": "TC-REG-015", "name": "Session reset clears all clinical variables", "action": "reset_session", "assert_clean_slate": True},

    {"id": "TC-REG-016", "name": "Scan payload serialization valid JSON", "action": "serialize_scan", "assert_json_serializable": True},
    {"id": "TC-REG-017", "name": "Required DB columns present in scan record", "required_columns": ["patient_id", "symptoms", "ranked_conditions", "is_emergency", "created_at"]},
    {"id": "TC-REG-018", "name": "Zero plaintext API keys in serialized audit logs", "action": "inspect_log_payload", "assert_zero_credentials": True},
    {"id": "TC-REG-019", "name": "Offline queue persistence format valid", "action": "offline_queue_format", "assert_valid_offline_schema": True},
    {"id": "TC-REG-020", "name": "Large payload stress (50 selected symptoms) gracefully handled", "action": "large_symptom_payload", "symptom_count": 50, "assert_no_oom": True}
]
