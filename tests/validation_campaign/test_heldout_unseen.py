"""
DocMindX AI — Stage 3: Held-Out Unseen Validation Suite (100 Novel Clinical Cases)
Strictly independent evaluation suite never used in training, tuning or initial defect repair.
Spans:
1. Rare & Complex Multi-Symptom Presentations (25 cases: TC-HLD-001 to 025)
2. Novel Code-Mixed Indic Clinical Narratives (25 cases: TC-HLD-026 to 050)
3. Complex Multi-Morbid History, Drug Allergy & Interaction Cross-Checks (25 cases: TC-HLD-051 to 075)
4. Distractor Idioms, Mixed Negation & Edge Demographics (25 cases: TC-HLD-076 to 100)
"""
import pytest
from ai.disease_prediction.predict import triage_engine
from ai.disease_prediction.multilingual_symptom_extractor import symptom_extractor
from ai.disease_prediction.canonical_concepts import canonical_normalizer
from ai.utils.clinical_safety_rules import clinical_safety_engine
from ai.utils.care_recommendations import _extract_clinical_presentation_attributes

HELDOUT_UNSEEN_TEST_CASES = [
    # -------------------------------------------------------------------------
    # PART 1: RARE & COMPLEX MULTI-SYMPTOM PRESENTATIONS (25 Cases)
    # -------------------------------------------------------------------------
    {"id": "TC-HLD-001", "name": "Thyrotoxic Crisis / Storm", "symptoms": ["palpitations", "sweating", "fever", "tremors", "fatigue"], "patient": {"age_group": "31-40", "gender": "Female", "duration": "1-3 Days", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-002", "name": "Acute Pancreatitis Presentation", "symptoms": ["abdominal pain", "vomiting", "nausea", "fever"], "patient": {"age_group": "41-50", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-003", "name": "Severe Dengue with Hemorrhagic Manifestations", "symptoms": ["high fever", "joint pain", "vomiting blood", "skin rash"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "3-5 Days", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-004", "name": "Acute Peritonitis / Ruptured Viscus", "symptoms": ["severe abdominal pain", "abdominal distension", "vomiting", "fever"], "patient": {"age_group": "51-60", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-005", "name": "Aortic Dissection Presentation", "symptoms": ["tearing chest pain", "shortness of breath", "sweating", "dizziness"], "patient": {"age_group": "61+", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-006", "name": "Severe Acute Asthma Attack", "symptoms": ["wheezing", "shortness of breath", "cough", "chest tightness"], "patient": {"age_group": "11-20", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-007", "name": "Infective Endocarditis", "symptoms": ["prolonged fever", "chills", "fatigue", "joint pain", "chest pain"], "patient": {"age_group": "41-50", "gender": "Male", "duration": "More than 2 Weeks", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-008", "name": "Acute Bacterial Pyelonephritis", "symptoms": ["flank pain", "high fever", "chills", "painful urination"], "patient": {"age_group": "31-40", "gender": "Female", "duration": "1-3 Days", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-009", "name": "Acute Gout Flare", "symptoms": ["severe joint pain", "swelling", "redness in foot"], "patient": {"age_group": "51-60", "gender": "Male", "duration": "Started Today", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-010", "name": "Chronic Kidney Disease Uremic Pruritus", "symptoms": ["itching", "fatigue", "nausea", "loss of appetite"], "patient": {"age_group": "61+", "gender": "Female", "duration": "More than 2 Weeks", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-011", "name": "Temporal Arteritis", "symptoms": ["temporal headache", "blurred vision", "jaw pain"], "patient": {"age_group": "61+", "gender": "Female", "duration": "1-2 Weeks", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-012", "name": "Spontaneous Pneumothorax", "symptoms": ["sudden chest pain", "shortness of breath", "cough"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-013", "name": "Acute Angle-Closure Glaucoma", "symptoms": ["severe eye pain", "headache", "blurred vision", "nausea"], "patient": {"age_group": "61+", "gender": "Female", "duration": "Started Today", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-014", "name": "Guillain-Barre Syndrome Prodrome", "symptoms": ["ascending weakness", "tingling", "numbness", "muscle weakness"], "patient": {"age_group": "31-40", "gender": "Male", "duration": "3-5 Days", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-015", "name": "Hyperosmolar Hyperglycemic State", "symptoms": ["extreme thirst", "frequent urination", "confusion", "fatigue"], "patient": {"age_group": "61+", "gender": "Male", "duration": "1-2 Weeks", "severity": "Severe"}, "expected_emergency": True},
    {"id": "TC-HLD-016", "name": "Early Shingles / Herpes Zoster", "symptoms": ["burning pain", "skin rash", "tingling sensation"], "patient": {"age_group": "51-60", "gender": "Female", "duration": "1-3 Days", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-017", "name": "Celiac Disease Presentation", "symptoms": ["chronic diarrhea", "abdominal bloating", "fatigue", "weight loss"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "More than 2 Weeks", "severity": "Mild"}, "expected_emergency": False},
    {"id": "TC-HLD-018", "name": "Rheumatoid Arthritis Early Phase", "symptoms": ["morning stiffness", "bilateral joint pain", "swelling in fingers"], "patient": {"age_group": "41-50", "gender": "Female", "duration": "More than 2 Weeks", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-019", "name": "Benign Paroxysmal Positional Vertigo (BPPV)", "symptoms": ["spinning dizziness", "nausea", "loss of balance"], "patient": {"age_group": "51-60", "gender": "Female", "duration": "1-3 Days", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-020", "name": "Iron Deficiency Anemia Fatigue", "symptoms": ["extreme fatigue", "pale skin", "dizziness", "shortness of breath on exertion"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "More than 2 Weeks", "severity": "Mild"}, "expected_emergency": False},
    {"id": "TC-HLD-021", "name": "Systemic Lupus Erythematosus Flare", "symptoms": ["malar rash", "joint pain", "fever", "fatigue"], "patient": {"age_group": "21-30", "gender": "Female", "duration": "1-2 Weeks", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-022", "name": "Psoriatic Arthritis", "symptoms": ["skin rash", "flaking skin", "joint pain", "finger swelling"], "patient": {"age_group": "31-40", "gender": "Male", "duration": "More than 2 Weeks", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-023", "name": "Ulcerative Colitis Exacerbation", "symptoms": ["bloody diarrhea", "abdominal cramps", "fever", "weight loss"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-2 Weeks", "severity": "Moderate"}, "expected_emergency": False},
    {"id": "TC-HLD-024", "name": "Primary Hypothyroidism", "symptoms": ["cold intolerance", "weight gain", "dry skin", "constipation", "fatigue"], "patient": {"age_group": "31-40", "gender": "Female", "duration": "More than 2 Weeks", "severity": "Mild"}, "expected_emergency": False},
    {"id": "TC-HLD-025", "name": "Secondary Syphilis Exanthem", "symptoms": ["palmar rash", "fever", "sore throat", "generalized lymphadenopathy"], "patient": {"age_group": "21-30", "gender": "Male", "duration": "1-2 Weeks", "severity": "Moderate"}, "expected_emergency": False},

    # -------------------------------------------------------------------------
    # PART 2: NOVEL CODE-MIXED INDIC CLINICAL NARRATIVES (25 Cases)
    # -------------------------------------------------------------------------
    {"id": "TC-HLD-026", "text": "मुझे अचानक severe chest pain और breathing problem शुरू हुई है", "lang": "hi-en", "expected_concept": "S000046"},
    {"id": "TC-HLD-027", "text": "મારા પિતાજીને કાલથી high fever અને violent shivering થાય છે", "lang": "gu-en", "expected_concept": "S000001"},
    {"id": "TC-HLD-028", "text": "bahut zyada dizziness aur spinning sensation ho raha hai", "lang": "hinglish", "expected_concept": "S000064"},
    {"id": "TC-HLD-029", "text": "pet ma severe cramps che ane 4 var loose motions thaya", "lang": "gujlish", "expected_concept": "S000089"},
    {"id": "TC-HLD-030", "text": "subah se throat bohot scratchy hai aur swallowing me pain ho raha hai", "lang": "hinglish", "expected_concept": "S000032"},
    {"id": "TC-HLD-031", "text": "બે દિવસથી skin par red itching rash દેખાય છે", "lang": "gu-en", "expected_concept": "S000109"},
    {"id": "TC-HLD-032", "text": "sir me severe throbbing headache hai jo light se badh jata hai", "lang": "hinglish", "expected_concept": "S000061"},
    {"id": "TC-HLD-033", "text": "walking karta knee joint ma असह્ય pain થાય છે", "lang": "gujlish", "expected_concept": "S000131"},
    {"id": "TC-HLD-034", "text": "peshab karti vakhat burning sensation ane extreme pain che", "lang": "gujlish", "expected_concept": "S000237"},
    {"id": "TC-HLD-035", "text": "pure body me severe muscular ache hai aur thakan lagti hai", "lang": "hinglish", "expected_concept": "S000011"},
    {"id": "TC-HLD-036", "text": "रात को continuous dry cough आता है जिससे नींद नहीं आती", "lang": "hi-en", "expected_concept": "S000023"},
    {"id": "TC-HLD-037", "text": "ekdam blurry vision thai gayu che ane dizziness lage che", "lang": "gujlish", "expected_concept": "S000210"},
    {"id": "TC-HLD-038", "text": "खाना देखकर severe nausea aur vomiting sensation hota hai", "lang": "hi-en", "expected_concept": "S000086"},
    {"id": "TC-HLD-039", "text": "પેશાબ વારંવાર જવું પડે છે increased urination frequency che", "lang": "gu-en", "expected_concept": "S000226"},
    {"id": "TC-HLD-040", "text": "chest me uncomfortable tightness aur heavy pressure lag raha hai", "lang": "hinglish", "expected_concept": "S000046"},
    {"id": "TC-HLD-041", "text": "kan ma severe pain che ane ear discharge aave che", "lang": "gujlish", "expected_concept": "S000170"},
    {"id": "TC-HLD-042", "text": "ankle ma twisting pachhi severe swelling ane tenderness aavi gayi", "lang": "gujlish", "expected_concept": "S000052"},
    {"id": "TC-HLD-043", "text": "running nose aur constant sneezing band nahi ho rahi", "lang": "hinglish", "expected_concept": "S000035"},
    {"id": "TC-HLD-044", "text": "eyes bilkul red thai gayi che ane severe watery discharge che", "lang": "gujlish", "expected_concept": "S000213"},
    {"id": "TC-HLD-045", "text": "पीठ के निचले हिस्से में sharp lower back pain radiate ho raha hai", "lang": "hi-en", "expected_concept": "S000135"},
    {"id": "TC-HLD-046", "text": "subah se continuous pelvic pain aur pedu me dard ho raha hai", "lang": "hinglish", "expected_concept": "S000188"},
    {"id": "TC-HLD-047", "text": "pait ma bohot acidity aur heartburn sensation hota hai khana khane ke baad", "lang": "hinglish", "expected_concept": "S000095"},
    {"id": "TC-HLD-048", "text": "chhati ma palpitations ane heart racing feel thay che", "lang": "gujlish", "expected_concept": "S000048"},
    {"id": "TC-HLD-049", "text": "kuch dino se severe loss of appetite hai kuch khane ka man nahi karta", "lang": "hinglish", "expected_concept": "S000009"},
    {"id": "TC-HLD-050", "text": "stomach ma gas ane continuous bloating sensation thi hairan chu", "lang": "gujlish", "expected_concept": "S000094"},

    # -------------------------------------------------------------------------
    # PART 3: COMPLEX MULTI-MORBID HISTORY, DRUG ALLERGY & DDIs (25 Cases)
    # -------------------------------------------------------------------------
    {"id": "TC-HLD-051", "patient": {"history": ["G6PD Deficiency"], "allergies": []}, "drug": "Primaquine", "expected_safe": False},
    {"id": "TC-HLD-052", "patient": {"history": ["Myasthenia Gravis"], "allergies": []}, "drug": "Gentamicin", "expected_safe": False},
    {"id": "TC-HLD-053", "patient": {"history": ["Acute Viral Hepatitis"], "allergies": []}, "drug": "Paracetamol 1000mg", "expected_safe": False},
    {"id": "TC-HLD-054", "patient": {"history": ["End-Stage Renal Disease (ESRD)"], "allergies": []}, "drug": "Metformin", "expected_safe": False},
    {"id": "TC-HLD-055", "patient": {"history": ["Narrow-Angle Glaucoma"], "allergies": []}, "drug": "Atropine", "expected_safe": False},
    {"id": "TC-HLD-056", "patient": {"history": ["Severe Peptic Ulcer Disease"], "allergies": []}, "drug": "Ketorolac", "expected_safe": False},
    {"id": "TC-HLD-057", "patient": {"history": ["Severe Bronchial Asthma"], "allergies": []}, "drug": "Propranolol", "expected_safe": False},
    {"id": "TC-HLD-058", "patient": {"history": ["Active Pulmonary Tuberculosis on ATT"], "allergies": []}, "drug": "Rifampicin", "expected_safe": False},
    {"id": "TC-HLD-059", "patient": {"history": ["Hemophilia A"], "allergies": []}, "drug": "Warfarin", "expected_safe": False},
    {"id": "TC-HLD-060", "patient": {"history": ["Heart Failure (HFrEF)"], "allergies": []}, "drug": "Verapamil", "expected_safe": False},
    {"id": "TC-HLD-061", "patient": {"history": [], "allergies": ["Penicillin"]}, "drug": "Ampicillin", "expected_safe": False},
    {"id": "TC-HLD-062", "patient": {"history": [], "allergies": ["Sulfa Drugs"]}, "drug": "Sulfamethoxazole", "expected_safe": False},
    {"id": "TC-HLD-063", "patient": {"history": [], "allergies": ["Aspirin"]}, "drug": "Naproxen", "expected_safe": False},
    {"id": "TC-HLD-064", "patient": {"history": [], "allergies": ["Cephalosporins"]}, "drug": "Cephalexin", "expected_safe": False},
    {"id": "TC-HLD-065", "patient": {"history": [], "allergies": ["Macrolides"]}, "drug": "Azithromycin", "expected_safe": False},
    {"id": "TC-HLD-066", "patient": {"current_meds": ["Warfarin"], "history": []}, "drug": "Aspirin", "expected_safe": False},
    {"id": "TC-HLD-067", "patient": {"current_meds": ["Lisinopril"], "history": []}, "drug": "Spironolactone", "expected_safe": False},
    {"id": "TC-HLD-068", "patient": {"current_meds": ["Simvastatin"], "history": []}, "drug": "Clarithromycin", "expected_safe": False},
    {"id": "TC-HLD-069", "patient": {"current_meds": ["Glimepiride"], "history": []}, "drug": "Fluconazole", "expected_safe": False},
    {"id": "TC-HLD-070", "patient": {"current_meds": ["Tamsulosin"], "history": []}, "drug": "Sildenafil", "expected_safe": False},
    {"id": "TC-HLD-071", "patient": {"age_group": "0-10", "gender": "Male", "history": []}, "drug": "Aspirin 325mg", "expected_safe": False},
    {"id": "TC-HLD-072", "patient": {"age_group": "0-10", "gender": "Female", "history": []}, "drug": "Ciprofloxacin", "expected_safe": False},
    {"id": "TC-HLD-073", "patient": {"age_group": "61+", "gender": "Male", "history": []}, "drug": "Diazepam", "expected_safe": False},
    {"id": "TC-HLD-074", "patient": {"age_group": "21-30", "gender": "Female", "pregnancy": True, "history": ["Pregnancy 1st Trimester"]}, "drug": "Methotrexate", "expected_safe": False},
    {"id": "TC-HLD-075", "patient": {"age_group": "21-30", "gender": "Female", "pregnancy": True, "history": ["Pregnancy 3rd Trimester"]}, "drug": "Diclofenac", "expected_safe": False},

    # -------------------------------------------------------------------------
    # PART 4: DISTRACTOR IDIOMS, MIXED NEGATION & EDGE PROFILES (25 Cases)
    # -------------------------------------------------------------------------
    {"id": "TC-HLD-076", "text": "छाती में कोई दर्द नहीं है, केवल सूखी खांसी है", "expected_positive": "S000023", "expected_negative": "S000046"},
    {"id": "TC-HLD-077", "text": "તાવ નથી પણ ખૂબ જ માથું દુખે છે", "expected_positive": "S000061", "expected_negative": "S000001"},
    {"id": "TC-HLD-078", "text": "no nausea or vomiting, only severe watery diarrhea", "expected_positive": "S000089", "expected_negative": "S000086"},
    {"id": "TC-HLD-079", "text": "heart does not hurt, but my legs feel very heavy and swollen", "expected_positive": "S000052", "expected_negative": "S000046"},
    {"id": "TC-HLD-080", "text": "I feel butterfly in my stomach when nervous, but my actual complaint is sore throat", "expected_positive": "S000032"},
    {"id": "TC-HLD-081", "text": "I got cold feet before the presentation, but my health issue is a runny nose", "expected_positive": "S000035"},
    {"id": "TC-HLD-082", "text": "mera dimaag kharab ho raha hai exam se, par gale me dard hai", "expected_positive": "S000032"},
    {"id": "TC-HLD-083", "text": "dil toot gaya breakup me, par pet me jalan hai", "expected_positive": "S000095"},
    {"id": "TC-HLD-084", "text": "no shortness of breath or fever, only localized mild skin rash", "expected_positive": "S000109", "expected_negative": "S000026"},
    {"id": "TC-HLD-085", "text": "sar me koi dard nahi hai, siraf kamar me dard hai", "expected_positive": "S000135", "expected_negative": "S000061"},
    {"id": "TC-HLD-086", "text": "કાનમાં દુખાવો નથી પરંતુ આંખો લાલ થઈ ગઈ છે", "expected_positive": "S000213", "expected_negative": "S000167"},
    {"id": "TC-HLD-087", "text": "neither fever nor chills, only painful urination", "expected_positive": "S000237", "expected_negative": "S000001"},
    {"id": "TC-HLD-088", "text": "bhookh bilkul nahi lag rahi aur energy down hai", "expected_positive": "S000009"}, # Inherent loss negation
    {"id": "TC-HLD-089", "text": "ભૂખ નથી લાગતી અને કમજોરી લાગે છે", "expected_positive": "S000009"}, # Inherent loss negation
    {"id": "TC-HLD-090", "text": "no loss of smell, but severe nasal congestion and runny nose", "expected_positive": "S000035"},
    {"id": "TC-HLD-091", "patient": {"age": 1, "age_group": "0-10", "gender": "Female"}, "symptoms": ["S000001"], "assert_pediatric_filter": True},
    {"id": "TC-HLD-092", "patient": {"age": 98, "age_group": "61+", "gender": "Male"}, "symptoms": ["S000005"], "assert_geriatric_filter": True},
    {"id": "TC-HLD-093", "patient": {"age": 25, "gender": "Male"}, "symptoms": ["S000092"], "disallowed_conditions": ["ovarian cyst", "cervical cancer"]},
    {"id": "TC-HLD-094", "patient": {"age": 55, "gender": "Female"}, "symptoms": ["S000239"], "disallowed_conditions": ["prostatitis", "prostate enlargement"]},
    {"id": "TC-HLD-095", "text": "It is not a heart problem, just a muscle sprain in my shoulder", "expected_positive": "S000133", "expected_negative": "S000046"},
    {"id": "TC-HLD-096", "text": "I do not have dengue or malaria, but I have a persistent low fever", "expected_positive": "S000001"},
    {"id": "TC-HLD-097", "text": "chest is totally clear without cough, but throat feels very dry", "expected_positive": "S000032", "expected_negative": "S000023"},
    {"id": "TC-HLD-098", "text": "no diarrhea, but severe painful constipation for three days", "expected_positive": "S000091", "expected_negative": "S000089"},
    {"id": "TC-HLD-099", "patient": {"age": 28, "gender": "Female", "pregnancy": True}, "symptoms": ["S000001"], "disallowed_drugs": ["Warfarin", "Methotrexate"]},
    {"id": "TC-HLD-100", "patient": {"age": 72, "gender": "Male", "history": ["ESRD"]}, "symptoms": ["S000131"], "disallowed_drugs": ["Metformin", "Ibuprofen"]}
]

class TestHeldOutUnseen:
    """Stage 3: Held-Out Unseen Test Suite (100 Unique Test Cases)."""

    @pytest.mark.parametrize("case", HELDOUT_UNSEEN_TEST_CASES, ids=[c["id"] for c in HELDOUT_UNSEEN_TEST_CASES])
    def test_heldout_case(self, case):
        cid = case["id"]

        # Part 1: TC-HLD-001 to 025 (Rare / Complex Multi-Symptom Presentations)
        if "TC-HLD-001" <= cid <= "TC-HLD-025":
            symptoms = case.get("symptoms", [])
            cname = case.get("name", "")
            patient = case.get("patient", {})
            expected_emergency = case.get("expected_emergency")

            attrs = _extract_clinical_presentation_attributes(
                symptoms=symptoms,
                top_condition=cname,
                user_context=patient
            )
            if expected_emergency is True:
                assert attrs["has_emergency_red_flags"] is True, (
                    f"Case {cid} ({cname}): Expected emergency=True, got False."
                )
            elif expected_emergency is False:
                assert attrs["has_emergency_red_flags"] is False, (
                    f"Case {cid} ({cname}): Expected emergency=False, got True."
                )

        # Part 2: TC-HLD-026 to 050 (Novel Code-Mixed Indic Narratives)
        elif "TC-HLD-026" <= cid <= "TC-HLD-050":
            text = case["text"]
            exp_concept = case["expected_concept"]
            rep = canonical_normalizer.normalize(text)
            extracted = symptom_extractor.extract_symptoms_and_medicines(text, offline=True)
            found_ids = set(rep.positive_symptoms) | set(extracted.get("symptom_ids", []))
            for d in extracted.get("detected_symptoms", []):
                if "symptom_id" in d:
                    found_ids.add(d["symptom_id"])
            assert exp_concept in found_ids, (
                f"Case {cid} ('{text}'): Expected canonical concept '{exp_concept}', found {found_ids}."
            )

        # Part 3: TC-HLD-051 to 075 (Complex Multi-Morbid History, Drug Allergy & DDIs)
        elif "TC-HLD-051" <= cid <= "TC-HLD-075":
            p = case.get("patient", {})
            drug = case["drug"]
            expected_safe = case["expected_safe"]
            eval_res = clinical_safety_engine.run_full_safety_audit(
                conditions=p.get("history", []),
                current_medications=p.get("current_meds", []),
                allergies=p.get("allergies", []),
                candidate_medications=[drug],
                patient_profile=p
            )
            drug_clean = drug.split()[0].strip()
            is_blocked = (not eval_res["is_safe"]) or (drug in eval_res["blocked_medications"]) or any(drug_clean.lower() in b.lower() for b in eval_res["blocked_medications"])
            if expected_safe is False:
                assert is_blocked is True, (
                    f"Case {cid}: Expected drug '{drug}' to be contraindicated/blocked, but safety engine marked safe."
                )
            else:
                assert is_blocked is False, (
                    f"Case {cid}: Expected drug '{drug}' to be safe, but got blocked: {eval_res['blocked_medications']}."
                )

        # Part 4: TC-HLD-076 to 100 (Distractor Idioms, Mixed Negation & Edge Demographics)
        elif "TC-HLD-076" <= cid <= "TC-HLD-100":
            # Text based negation/distractor assertions
            if "text" in case:
                text = case["text"]
                rep = canonical_normalizer.normalize(text)
                extracted = symptom_extractor.extract_symptoms_and_medicines(text, offline=True)
                found_pos = set(rep.positive_symptoms) | set(extracted.get("symptom_ids", []))
                for d in extracted.get("detected_symptoms", []):
                    if "symptom_id" in d:
                        found_pos.add(d["symptom_id"])

                if "expected_positive" in case:
                    exp_pos = case["expected_positive"]
                    assert exp_pos in found_pos, (
                        f"Case {cid} ('{text}'): Expected positive concept '{exp_pos}', found {found_pos}."
                    )
                if "expected_negative" in case:
                    exp_neg = case["expected_negative"]
                    assert exp_neg not in found_pos, (
                        f"Case {cid} ('{text}'): Denied symptom '{exp_neg}' falsely detected as positive in {found_pos}."
                    )

            # Demographic / Anatomical / Drug safety checks
            elif "disallowed_conditions" in case:
                p = case["patient"]
                disallowed = [c.lower() for c in case["disallowed_conditions"]]
                res = triage_engine.evaluate_symptoms(case["symptoms"], gender=p["gender"])
                conds = [c.get("name", "").lower() for c in (res.get("ranked_conditions") or [])]
                for dis in disallowed:
                    assert not any(dis in c for c in conds), (
                        f"Case {cid}: Gender {p['gender']} received disallowed condition '{dis}' in {conds}"
                    )

            elif "disallowed_drugs" in case:
                p = case["patient"]
                disallowed_drugs = case["disallowed_drugs"]
                for d in disallowed_drugs:
                    eval_res = clinical_safety_engine.run_full_safety_audit(
                        conditions=p.get("history", []),
                        candidate_medications=[d],
                        patient_profile=p
                    )
                    assert not eval_res["is_safe"] or d in eval_res["blocked_medications"] or len(eval_res["blocked_medications"]) > 0

            elif case.get("assert_pediatric_filter"):
                p = case["patient"]
                eval_res = clinical_safety_engine.run_full_safety_audit(
                    candidate_medications=["Aspirin"],
                    patient_profile=p
                )
                assert not eval_res["is_safe"] or "Aspirin" in eval_res["blocked_medications"]

            elif case.get("assert_geriatric_filter"):
                p = case["patient"]
                eval_res = clinical_safety_engine.run_full_safety_audit(
                    candidate_medications=["Diazepam"],
                    patient_profile=p
                )
                assert not eval_res["is_safe"] or "Diazepam" in eval_res["blocked_medications"]
