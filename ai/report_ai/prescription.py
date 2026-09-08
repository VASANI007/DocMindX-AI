"""
    Prescription Parsing and Explanation Engine
Extracts medicine names, instructions, dosage, and maps to safety guidance.
"""
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from api.openfda import search_drug_openfda
from ai.report_ai.medical_verifier import verify_medical_document

class PrescriptionAnalyzer:
    def __init__(self):
        pass

    def parse_prescription_text(self, text: str) -> dict:
        """
        Parses prescription text line-by-line looking for medication lines, dosage frequencies, and advice.
        """
        doc_eval = verify_medical_document(text, expected_type="prescription")
        if not doc_eval["is_valid"]:
            return {
                "is_valid_prescription": False,
                "total_medicines_identified": 0,
                "medicines": [],
                "general_doctor_instructions": [],
                "summary": "The uploaded document does not appear to be a valid doctor prescription. No prescribed medications were detected."
            }

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        medicines = []
        instructions = []

        # Common medicine keywords / forms
        med_keywords = ["tab", "tablet", "cap", "capsule", "syr", "syrup", "inj", "injection", "ointment", "drops", "mg", "ml"]

        for line in lines:
            # Clean leading numbering (e.g. "1.", "1)", "- ")
            cleaned_line = re.sub(r'^\s*[\d\.\-\)\*]+\s*', '', line).strip()
            line_lower = cleaned_line.lower()

            # Check if line looks like a medicine line
            is_med = any(re.search(r'\b' + re.escape(kw) + r'\b', line_lower) for kw in med_keywords)
            
            # Extract frequency if present (e.g. 1-0-1, once daily, TDS, BD, OD, SOS)
            frequency = "As directed by physician"
            freq_match = re.search(r'\b(1-0-1|1-1-1|1-0-0|0-0-1|0-1-0|bd|od|tds|qid|sos|twice daily|once daily|three times daily)\b', line_lower)
            if freq_match:
                frequency = freq_match.group(1).upper()

            # Use word boundaries so 'ac' does not match inside 'Paracetamol' or 'Diclofenac'
            timing = "After food"
            if re.search(r'\b(before food|empty stomach|empty-stomach|ac|a\.c\.)\b', line_lower):
                timing = "Before food (Empty stomach)"
            elif re.search(r'\b(after food|after-food|pc|p\.c\.)\b', line_lower):
                timing = "After food"

            # Clean medicine candidate name (strip forms like Tablet, Tab, Syrup, Syr, etc.)
            clean_name = re.sub(r'^(tablet|tab|capsule|cap|syrup|syr|injection|inj|ointment|oint|drops|drop|gel|cream|rx|dr\.)\s*', '', cleaned_line, flags=re.IGNORECASE).strip()
            # Remove dosage numbers like 500mg, 10mg and trailing dosage codes
            drug_name_candidate = re.split(r'(\d+\s*(?:mg|ml|mcg|gm)|\b1-0-1\b|\b1-1-1\b|\b1-0-0\b|\b0-0-1\b|\bod\b|\bbd\b|\btds\b)', clean_name, flags=re.IGNORECASE)[0].strip()

            if len(drug_name_candidate) >= 3 and is_med:
                # Query OpenFDA / Knowledge cache
                drug_info = search_drug_openfda(drug_name_candidate)
                medicines.append({
                    "raw_line": line,
                    "extracted_name": drug_name_candidate,
                    "frequency": frequency,
                    "timing": timing,
                    "info": drug_info
                })
            elif not is_med and len(line) > 5:
                instructions.append(line)

        return {
            "total_medicines_identified": len(medicines),
            "medicines": medicines,
            "general_doctor_instructions": instructions if medicines else []
        }
