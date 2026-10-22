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
        med_keywords = ["tab", "tablet", "cap", "capsule", "syr", "syrup", "inj", "injection", "ointment", "drops", "mg", "ml", "mcg", "gel", "cream", "inhaler"]
        
        # Category headers to skip from being identified as medicines
        category_headers = [
            r'nerve support', r'nerve pain', r'pain & muscle', r'stomach protection',
            r'diagnostic recommendations', r'treatment plan', r'clinical assessment',
            r'investigations', r'advice', r'general instructions', r'chief complaint',
            r'diagnosis', r'provisional diagnosis', r'history of present illness'
        ]

        for line in lines:
            # 1. Clean markdown artifacts, orphan asterisks, bullets, numbering
            cleaned_line = re.sub(r'[*_~`#]', '', line).strip()
            cleaned_line = re.sub(r'^[•\-\*\d\.\)\s]+', '', cleaned_line).strip()
            if not cleaned_line:
                continue

            # Skip lines that are purely category headers (e.g. "Nerve Pain Modulator:")
            if any(re.match(rf'^{kw}\s*:?$', cleaned_line, re.IGNORECASE) for kw in category_headers):
                continue

            # Separate inline purpose / instructions (e.g. "Inj. Neurokind: Prescribed to support nerve repair")
            inline_purpose = ""
            if ":" in cleaned_line:
                parts = cleaned_line.split(":", 1)
                med_candidate_part = parts[0].strip()
                inline_purpose = parts[1].strip()
            else:
                med_candidate_part = cleaned_line

            # Extract parenthetical formulation if present (e.g. "Neurokind (Vitamin B12 / Mecobalamin)")
            generic_formulation = ""
            paren_match = re.search(r'\((.*?)\)', med_candidate_part)
            if paren_match:
                generic_formulation = paren_match.group(1).strip()
                med_candidate_part = re.sub(r'\(.*?\)', '', med_candidate_part).strip()

            line_lower = med_candidate_part.lower()

            # Check if line looks like a medicine line
            is_med = any(re.search(r'\b' + re.escape(kw) + r'\b', line_lower) for kw in med_keywords)
            
            # Extract frequency if present (e.g. 1-0-1, once daily, weekly, TDS, BD, OD, SOS)
            frequency = "As directed by physician"
            combined_context = (med_candidate_part + " " + inline_purpose).lower()
            if "weekly" in combined_context:
                frequency = "Once weekly"
            elif "once daily" in combined_context or "at night" in combined_context or "bedtime" in combined_context:
                frequency = "Once daily (Night)" if ("night" in combined_context or "bedtime" in combined_context) else "Once daily"
            elif "twice daily" in combined_context:
                frequency = "Twice daily (BD)"
            elif "three times daily" in combined_context:
                frequency = "Three times daily (TDS)"
            else:
                freq_match = re.search(r'\b(1-0-1|1-1-1|1-0-0|0-0-1|0-1-0|bd|od|tds|qid|sos)\b', combined_context)
                if freq_match:
                    frequency = freq_match.group(1).upper()

            # Use word boundaries for food timing
            timing = "After food"
            if re.search(r'\b(before food|empty stomach|empty-stomach|ac|a\.c\.)\b', combined_context):
                timing = "Before food (Empty stomach)"
            elif re.search(r'\b(after food|after-food|pc|p\.c\.)\b', combined_context):
                timing = "After food"

            # Clean medicine candidate name (strip forms like Tablet, Tab, Syrup, Syr, etc.)
            clean_name = re.sub(r'^(?:inj(?:ection)?|tab(?:let)?|cap(?:sule)?|syr(?:up)?|oint(?:ment)?|drops?|rx|dr)[\.\s:]+', '', med_candidate_part, flags=re.IGNORECASE).strip()
            # Remove dosage numbers like 500mg, 10mg and trailing dosage codes
            clean_name = re.split(r'(\d+\s*(?:mg|ml|mcg|gm)|\b1-0-1\b|\b1-1-1\b|\b1-0-0\b|\b0-0-1\b|\bod\b|\bbd\b|\btds\b)', clean_name, flags=re.IGNORECASE)[0].strip()
            clean_name = re.sub(r'\s+(?:tablet|capsule|injection|syrup)$', '', clean_name, flags=re.IGNORECASE).strip()
            clean_name = re.sub(r'[*_~`#]', '', clean_name).strip()

            if len(clean_name) >= 2 and is_med:
                # Query OpenFDA with clean brand name or generic active formulation
                drug_query = clean_name
                drug_info = search_drug_openfda(drug_query)
                if (not drug_info or drug_info.get("status") == "NO_RELEVANT_RESULT") and generic_formulation:
                    # Try querying first active salt in formulation
                    first_salt = generic_formulation.split("/")[0].strip().split("+")[0].strip()
                    if len(first_salt) >= 3:
                        alt_info = search_drug_openfda(first_salt)
                        if alt_info and alt_info.get("status") == "SUCCESS":
                            drug_info = alt_info

                # Ensure drug_info has clean, patient-friendly information
                if not drug_info or drug_info.get("status") == "NO_RELEVANT_RESULT":
                    drug_info = {
                        "medicine_name": clean_name,
                        "generic_name": generic_formulation or clean_name,
                        "purpose": inline_purpose if inline_purpose else "Prescribed for targeted clinical therapy",
                        "warnings": "Take strictly as directed by the prescribing physician. Follow scheduled food timings."
                    }
                else:
                    if not drug_info.get("purpose") and inline_purpose:
                        drug_info["purpose"] = inline_purpose
                    if not drug_info.get("generic_name") and generic_formulation:
                        drug_info["generic_name"] = generic_formulation
                    if "no official fda drug label found" in str(drug_info.get("warnings", "")).lower():
                        drug_info["warnings"] = "Take strictly as directed by the prescribing physician. Follow scheduled food timings."

                medicines.append({
                    "raw_line": line,
                    "extracted_name": clean_name,
                    "generic_name": generic_formulation or drug_info.get("generic_name", clean_name),
                    "frequency": frequency,
                    "timing": timing,
                    "purpose": inline_purpose or drug_info.get("purpose", "Prescribed for therapy"),
                    "info": drug_info
                })
            elif not is_med and len(cleaned_line) > 5:
                instructions.append(cleaned_line)

        return {
            "total_medicines_identified": len(medicines),
            "medicines": medicines,
            "general_doctor_instructions": instructions if medicines else []
        }
