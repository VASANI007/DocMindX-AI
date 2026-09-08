"""
    Universal Medical Document Verifier & Classification Engine
Detects whether an uploaded document / OCR stream is an authentic medical document
or a non-medical document (e.g. college letters, assignments, invoices, general certificates).
"""
import re

# Comprehensive list of non-medical indicators across academia, business, software, law, etc.
NON_MEDICAL_INDICATORS = [
    r"\bcollege\b", r"\buniversity\b", r"\binstitute\b", r"\bsemester\b", r"\bcurriculum\b",
    r"\bassignment\b", r"\bhomework\b", r"\bbonafide\b", r"\bmarksheet\b", r"\bstudent\b",
    r"\binternship\b", r"\bpermission letter\b", r"\bconfirmation letter\b", r"\bhardware store\b",
    r"\bproject training\b", r"\bpython development\b", r"\bdjango\b", r"\bsoftware\b",
    r"\binvoice\b", r"\bbill to\b", r"\btax invoice\b", r"\breceipt\b", r"\bsalary slip\b",
    r"\bresume\b", r"\bcurriculum vitae\b", r"\blegal notice\b", r"\bagreement\b", r"\bcontract\b",
    r"\bboarding pass\b", r"\bticket\b", r"\be-commerce\b", r"\bshipping address\b"
]

# Clinical laboratory / pathology indicators
LAB_INDICATORS = [
    r"\bhemoglobin\b", r"\bhaemoglobin\b", r"\bhb\b", r"\bwbc\b", r"\bleukocyte\b",
    r"\bplatelet\b", r"\bplt\b", r"\bglucose\b", r"\bsugar\b", r"\bfbs\b", r"\bppbs\b",
    r"\bhba1c\b", r"\bcreatinine\b", r"\bbilirubin\b", r"\bsgpt\b", r"\balt\b", r"\bsgot\b",
    r"\bast\b", r"\bcholesterol\b", r"\btriglyceride\b", r"\btsh\b", r"\bthyroid\b",
    r"\bvitamin d\b", r"\bvitamin b12\b", r"\bcbc\b", r"\blft\b", r"\bkft\b", r"\brft\b",
    r"\blipid profile\b", r"\bpathology\b", r"\bhematology\b", r"\bbiochemistry\b",
    r"\breference interval\b", r"\breference range\b", r"\bbiological reference\b",
    r"\bg/dl\b", r"\bmg/dl\b", r"\bcells/mcl\b", r"\bcells/cumm\b", r"\bu/l\b", r"\bng/ml\b", r"\bpg/ml\b"
]

# Prescription indicators
PRESCRIPTION_INDICATORS = [
    r"\brx\b", r"\btab\b", r"\btablet\b", r"\bcap\b", r"\bcapsule\b", r"\bsyr\b", r"\bsyrup\b",
    r"\binj\b", r"\binjection\b", r"\bdrops\b", r"\bointment\b", r"\binhaler\b", r"\bsuspension\b",
    r"\b1-0-1\b", r"\b1-1-1\b", r"\b1-0-0\b", r"\b0-0-1\b", r"\bbd\b", r"\bod\b", r"\btds\b",
    r"\bqid\b", r"\bsos\b", r"\bafter food\b", r"\bbefore food\b", r"\bempty stomach\b",
    r"\bmg\b", r"\bmcg\b", r"\bdosage\b", r"\bdoctor\b", r"\bdr\.\b", r"\bclinic\b", r"\bphysician\b"
]

# Radiology / Imaging indicators
RADIOLOGY_INDICATORS = [
    r"\bx-ray\b", r"\bxray\b", r"\bchest radiograph\b", r"\bradiology\b", r"\bct scan\b",
    r"\bcomputed tomography\b", r"\bhrct\b", r"\bmri\b", r"\bmagnetic resonance\b",
    r"\bultrasound\b", r"\busg\b", r"\bsonography\b", r"\bmammography\b", r"\bpet-ct\b",
    r"\bimpression\b", r"\bfindings\b", r"\bconsolidation\b", r"\bpleural effusion\b",
    r"\bcardiomegaly\b", r"\bfracture\b", r"\bground glass\b", r"\bggo\b", r"\bopacit\w*\b",
    r"\binfarct\b", r"\bischemi\w*\b", r"\bhemorrhage\b", r"\bhematoma\b", r"\bherniation\b",
    r"\bdegenerative\b", r"\bspondylosis\b", r"\bcalculus\b", r"\bcalculi\b", r"\blesion\b",
    r"\bhyperintensity\b", r"\bhypointensity\b", r"\battenuation\b", r"\bparenchyma\b"
]

def verify_medical_document(text: str, expected_type: str = "any") -> dict:
    """
    Evaluates whether raw text corresponds to a genuine medical document of the specified type.
    expected_type: 'lab', 'prescription', 'radiology', or 'any'
    
    Returns:
        dict: {
            "is_valid": bool,
            "detected_type": str ('lab', 'prescription', 'radiology', 'general_medical', 'non_medical', 'empty'),
            "confidence": float,
            "reasons": list[str]
        }
    """
    if not text or not text.strip() or len(text.strip()) < 8:
        return {
            "is_valid": False,
            "detected_type": "empty",
            "confidence": 1.0,
            "reasons": ["Empty or insufficient text provided."]
        }

    text_lower = text.lower()

    # Count matching non-medical indicators
    non_med_matches = [ind for ind in NON_MEDICAL_INDICATORS if re.search(ind, text_lower)]
    
    # Count matching medical domain indicators
    lab_matches = [ind for ind in LAB_INDICATORS if re.search(ind, text_lower)]
    presc_matches = [ind for ind in PRESCRIPTION_INDICATORS if re.search(ind, text_lower)]
    rad_matches = [ind for ind in RADIOLOGY_INDICATORS if re.search(ind, text_lower)]
    
    total_medical_matches = len(lab_matches) + len(presc_matches) + len(rad_matches)

    # If non-medical context is prominent and there is virtually no medical terminology
    if len(non_med_matches) >= 2 and total_medical_matches <= 1:
        return {
            "is_valid": False,
            "detected_type": "non_medical",
            "confidence": 0.95,
            "reasons": ["Document contains non-medical content (e.g. academic letter, invoice, assignment, general text) with no genuine clinical data."]
        }

    # Determine highest matching clinical domain
    score_map = {
        "lab": len(lab_matches),
        "prescription": len(presc_matches),
        "radiology": len(rad_matches)
    }
    
    best_type = max(score_map, key=score_map.get)
    max_score = score_map[best_type]

    if max_score == 0:
        return {
            "is_valid": False,
            "detected_type": "non_medical",
            "confidence": 0.90,
            "reasons": ["No recognized medical diagnostic parameters, medications, or radiological findings detected."]
        }

    # If expected_type is specified, verify match
    if expected_type in ["lab", "prescription", "radiology"]:
        type_score = score_map.get(expected_type, 0)
        if type_score == 0 and len(non_med_matches) > 0:
            return {
                "is_valid": False,
                "detected_type": best_type if max_score > 0 else "non_medical",
                "confidence": 0.85,
                "reasons": [f"Document does not contain authentic {expected_type.capitalize()} data."]
            }
        return {
            "is_valid": True,
            "detected_type": expected_type,
            "confidence": min(0.99, 0.5 + (max(type_score, 1) * 0.1)),
            "reasons": [f"Valid {expected_type} indicators verified."]
        }

    return {
        "is_valid": True,
        "detected_type": best_type,
        "confidence": min(0.99, 0.5 + (max_score * 0.1)),
        "reasons": [f"Valid {best_type} indicators verified."]
    }
