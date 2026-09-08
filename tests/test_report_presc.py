import os
import sys
sys.path.insert(0, ".")

from ai.report_ai.blood_report import LabReportAnalyzer
from ai.report_ai.prescription import PrescriptionAnalyzer
from ai.report_ai.radiology import RadiologyReportAnalyzer

print("=========================================================")
print("  TESTING MEDICAL REPORT & PRESCRIPTION ANALYZER ENGINES")
print("=========================================================")

# 1. TEST BLOOD LAB REPORT
print("\n--- 1. Testing Blood Lab Report Analyzer ---")
sample_blood_report = """
PATIENT LAB REPORT:
Patient Name: Rajesh Kumar | Age: 42 | Gender: Male
TEST PARAMETERS:
Hemoglobin: 11.2 g/dL (Reference: 13.0 - 17.0 g/dL)
Total WBC Count: 12500 /mcL (Reference: 4000 - 11000 /mcL)
Platelet Count: 180000 /mcL (Reference: 150000 - 450000 /mcL)
Fasting Blood Sugar (Glucose): 145 mg/dL (Reference: 70 - 100 mg/dL)
Serum Creatinine: 1.1 mg/dL (Reference: 0.7 - 1.3 mg/dL)
Total Cholesterol: 240 mg/dL (Reference: < 200 mg/dL)
SGPT (ALT): 35 U/L (Reference: < 50 U/L)
"""

lab_analyzer = LabReportAnalyzer()
lab_res = lab_analyzer.parse_and_evaluate(sample_blood_report, age_group="Adult", gender="Male", lang="en")
print(f"Total Tests Detected: {lab_res.get('total_tests_detected')}")
print(f"Abnormal Parameters Count: {lab_res.get('abnormal_count')}")
print("Findings:")
for f in lab_res.get("findings", []):
    print(f"  • {f.get('test_name')}: {f.get('value')} {f.get('unit')} [{f.get('status')}] (Ref: {f.get('reference_range')})")

# 2. TEST PRESCRIPTION ANALYZER
print("\n--- 2. Testing Doctor Prescription Analyzer ---")
sample_prescription = """
Dr. Sharma Clinic
Rx:
1. Tab Paracetamol 650mg - 1-0-1 (After food) for 3 days
2. Cap Amoxicillin 500mg - 1-1-1 (After food) for 5 days
3. Tab Pantoprazole 40mg - 1-0-0 (Before food / Empty stomach) for 5 days
4. Syrup Benadryl 10ml - 0-0-1 at bedtime
Advice: Drink warm water and rest.
"""

presc_analyzer = PrescriptionAnalyzer()
presc_res = presc_analyzer.parse_prescription_text(sample_prescription)
print(f"Total Medicines Identified: {presc_res.get('total_medicines_identified')}")
print("Medicines Breakdown:")
for m in presc_res.get("medicines", []):
    print(f"  • Medicine: {m.get('extracted_name')} | Dosage: {m.get('frequency')} | Timing: {m.get('timing')}")

# 3. TEST RADIOLOGY / IMAGING ANALYZER
print("\n--- 3. Testing Radiology / Imaging Analyzer ---")
sample_xray = """
DEPARTMENT OF RADIODIGNOSTICS
CHEST X-RAY (PA VIEW):
Clinical History: 45 year old male with fever and cough for 5 days.
FINDINGS:
- Patchy consolidation seen in right lower lung zone suggestive of pneumonia.
- Cardiac silhouette is normal in size and contour.
- Bilateral costophrenic angles are clear.
- No pneumothorax or pleural effusion.
IMPRESSION: Right lower lobe pneumonia.
"""

rad_analyzer = RadiologyReportAnalyzer()
rad_res = rad_analyzer.analyze_imaging_report(sample_xray, user_lang="en")
print(f"Total Findings: {rad_res.get('total_findings')}")
print(f"Overall Severity: {rad_res.get('overall_severity')}")
print("Radiology Findings:")
for rf in rad_res.get("findings", []):
    print(f"  • {rf.get('finding_name')}: {rf.get('severity')} - {rf.get('explanation')}")

print("\n--- 4. Testing Non-Medical Document (Safety Verification) ---")
sample_non_medical = """
INVOICE # 48291
To: ABC Tech Solutions
Services: Website development and maintenance.
Total Due: $500.00
Payment due within 15 days.
"""
non_med_lab = lab_analyzer.parse_and_evaluate(sample_non_medical)
print(f"Non-medical lab valid: {non_med_lab.get('is_valid_medical_report', True)}")
non_med_presc = presc_analyzer.parse_prescription_text(sample_non_medical)
print(f"Non-medical prescription valid: {non_med_presc.get('is_valid_prescription', True)}")

print("\n================ ALL CHECKS FINISHED ================")
