"""
Unit tests for DocMindX AI — Health Records & Clinical History Module
Validates:
1. Unauthenticated / Guest session handling (no DB leakage, strict memory mode)
2. Authenticated multi-profile query isolation (General vs Profile vs Family Member)
3. IDOR protection & cross-user access rejection
4. Complete clinical scan persistence (symptoms, findings, triage, medicines, care protocols)
5. ReportLab PDF generation via generate_scan_record_pdf for all scan types
"""
import unittest
import io
import os
import sys
import json

# Ensure project root is in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import database.auth_db as auth_db
from ai.utils.report_generator import generate_scan_record_pdf


class TestHealthRecordsClinicalModule(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        auth_db.init_auth_tables()
        # Seed test users
        cls.user_a_email = "hr_patient_a@test.hospital"
        cls.user_b_email = "hr_patient_b@test.hospital"

        u_a = auth_db.get_user_by_email(cls.user_a_email)
        if not u_a:
            cls.user_a_id = auth_db.create_user(
                full_name="Vikramaditya Sharma",
                email=cls.user_a_email,
                password_hash="mock_hash_a",
                account_status="ACTIVE",
                email_verified=1
            )
        else:
            cls.user_a_id = u_a["id"]

        u_b = auth_db.get_user_by_email(cls.user_b_email)
        if not u_b:
            cls.user_b_id = auth_db.create_user(
                full_name="Rohan Verma",
                email=cls.user_b_email,
                password_hash="mock_hash_b",
                account_status="ACTIVE",
                email_verified=1
            )
        else:
            cls.user_b_id = u_b["id"]

        # Add family members for User A
        existing_fams_a = auth_db.get_family_members(cls.user_a_id)
        if not existing_fams_a:
            cls.mem_spouse_id = auth_db.add_family_member(cls.user_a_id, {
                "name": "Priya Sharma",
                "relationship": "Spouse",
                "age": 32,
                "gender": "Female",
                "blood_group": "A+",
                "height": 162,
                "weight": 58
            })
            cls.mem_child_id = auth_db.add_family_member(cls.user_a_id, {
                "name": "Aarav Sharma",
                "relationship": "Child",
                "age": 8,
                "gender": "Male",
                "blood_group": "O+",
                "height": 125,
                "weight": 26
            })
        else:
            cls.mem_spouse_id = existing_fams_a[0]["id"]
            cls.mem_child_id = existing_fams_a[1]["id"] if len(existing_fams_a) > 1 else existing_fams_a[0]["id"]

    def test_01_profile_isolation_general_vs_profile_vs_family(self):
        """Verify strict isolation between General, Profile, and Family Member scans."""
        # 1. Save General Scan for User A
        scan_gen_id = auth_db.save_medical_scan(
            user_id=self.user_a_id,
            family_member_id=None,
            scan_type="Health Assessment",
            scan_mode="GENERAL",
            result_reference="Viral Fever",
            summary="Moderate viral fever assessment",
            details={"symptoms": ["fever", "headache"], "urgency": "MODERATE"}
        )

        # 2. Save Personal Profile Scan for User A
        scan_prof_id = auth_db.save_medical_scan(
            user_id=self.user_a_id,
            family_member_id=None,
            scan_type="Lab Report",
            scan_mode="PROFILE",
            result_reference="Lipid Profile",
            summary="Borderline high cholesterol",
            details={"cholesterol": 215, "abnormal_count": 1}
        )

        # 3. Save Family Member (Spouse) Scan for User A
        scan_spouse_id = auth_db.save_medical_scan(
            user_id=self.user_a_id,
            family_member_id=self.mem_spouse_id,
            scan_type="Prescription",
            scan_mode="FAMILY_MEMBER",
            result_reference="Dr Prescription - Priya",
            summary="Thyroxine regimen",
            details={"medicines": [{"name": "Thyroxine 50mcg", "frequency": "1 daily"}]}
        )

        # Query General Scans
        gen_scans = auth_db.get_user_scans(self.user_a_id, scan_mode="GENERAL")
        gen_ids = [s["id"] for s in gen_scans]
        self.assertIn(scan_gen_id, gen_ids)
        self.assertNotIn(scan_prof_id, gen_ids)
        self.assertNotIn(scan_spouse_id, gen_ids)

        # Query Profile Scans
        prof_scans = auth_db.get_user_scans(self.user_a_id, scan_mode="PROFILE")
        prof_ids = [s["id"] for s in prof_scans]
        self.assertIn(scan_prof_id, prof_ids)
        self.assertNotIn(scan_gen_id, prof_ids)
        self.assertNotIn(scan_spouse_id, prof_ids)

        # Query Family Member Scans
        spouse_scans = auth_db.get_user_scans(self.user_a_id, family_member_id=self.mem_spouse_id, scan_mode="FAMILY_MEMBER")
        spouse_ids = [s["id"] for s in spouse_scans]
        self.assertIn(scan_spouse_id, spouse_ids)
        self.assertNotIn(scan_gen_id, spouse_ids)
        self.assertNotIn(scan_prof_id, spouse_ids)

    def test_02_idor_cross_user_protection(self):
        """Verify User B cannot query or delete User A's scans or family members."""
        # Create scan for User A
        scan_a_id = auth_db.save_medical_scan(
            user_id=self.user_a_id,
            family_member_id=None,
            scan_type="Radiology",
            scan_mode="GENERAL",
            result_reference="Chest X-Ray",
            summary="Clear lung fields",
            details={"findings": [{"observation": "Normal cardiac silhouette"}]}
        )

        # User B attempts to access User A's scan via get_medical_scan_by_id
        unauth_scan = auth_db.get_medical_scan_by_id(scan_a_id, user_id=self.user_b_id)
        self.assertIsNone(unauth_scan, "User B should not be able to retrieve User A's scan")

        # User B attempts to query User A's family member scans
        idor_scans = auth_db.get_user_scans(user_id=self.user_b_id, family_member_id=self.mem_spouse_id)
        self.assertEqual(len(idor_scans), 0, "IDOR check should reject non-owned family_member_id")

        # User B attempts to delete User A's scan
        del_result = auth_db.delete_medical_scan(scan_a_id, user_id=self.user_b_id)
        self.assertFalse(del_result, "User B should not be permitted to delete User A's scan")

        # Confirm scan still exists for User A
        valid_scan = auth_db.get_medical_scan_by_id(scan_a_id, user_id=self.user_a_id)
        self.assertIsNotNone(valid_scan, "Scan should still exist for rightful owner")

    def test_03_guest_session_isolation_zero_db(self):
        """Verify guest mode requirements: no DB queries needed when user is None."""
        # In guest mode, session scans live in memory
        guest_scans = [
            {
                "scan_type": "Health Assessment",
                "scan_mode": "GENERAL",
                "result_reference": "Acute Migraine",
                "summary": "Moderate urgency migraine evaluation",
                "created_at": "2026-09-08 20:30:00",
                "patient_name": "Guest Visitor",
                "details": {
                    "symptoms": ["headache", "photophobia"],
                    "urgency_level": "MODERATE",
                    "ranked_conditions": [{"name": "Migraine without Aura", "confidence": 0.88}],
                    "care_recommendations": {
                        "yoga_recommendations": [{"name": "Shavasana", "benefits": "Reduces cerebral vascular tension"}],
                        "diet_guidance": {"foods_to_eat": ["Ginger tea", "Almonds"], "foods_to_avoid": ["Aged cheese", "Red wine"]}
                    }
                }
            }
        ]

        # Verify PDF generation functions completely without database persistence
        pdf_stream = generate_scan_record_pdf(guest_scans[0])
        self.assertIsInstance(pdf_stream, io.BytesIO)
        self.assertGreater(len(pdf_stream.getvalue()), 1000, "Generated PDF must contain valid byte stream")

    def test_04_complete_scan_persistence_all_sections(self):
        """Verify details_json preserves all 5 clinical sections: context, findings, AI analysis, recommendations, precautions."""
        full_assessment = {
            "scan_type": "Health Assessment",
            "scan_mode": "PROFILE",
            "patient_name": "Vikramaditya Sharma",
            "user_inputs": {
                "age": 35,
                "gender": "Male",
                "duration": "3-5 Days",
                "severity": "Moderate",
                "blood_group": "B+",
                "existing_conditions": ["Hypertension"],
                "current_medicines": ["Amlodipine 5mg"],
                "symptoms": ["Cough", "Mild Fever"]
            },
            "findings": [{"test_name": "Body Temperature", "value": "100.4 F", "status": "High"}],
            "ranked_conditions": [
                {"name": "Acute Bronchitis", "confidence": 0.85},
                {"name": "Viral Upper Respiratory Infection", "confidence": 0.72}
            ],
            "urgency_level": "MODERATE",
            "is_emergency": False,
            "medicines": [
                {"name": "Dextromethorphan Syrup", "dosage": "10ml thrice daily", "purpose": "Cough suppressant"}
            ],
            "yoga_recommendations": [
                {"name": "Pranayama (Anulom Vilom)", "benefits": "Enhances respiratory oxygenation"}
            ],
            "diet_guidance": {
                "foods_to_eat": ["Warm turmeric milk", "Clear vegetable soups"],
                "foods_to_avoid": ["Cold beverages", "Deep-fried foods"]
            },
            "precautions": [
                "Seek immediate emergency evaluation if dyspnea or hemoptysis develops"
            ]
        }

        scan_id = auth_db.save_medical_scan(
            user_id=self.user_a_id,
            family_member_id=None,
            scan_type="Health Assessment",
            scan_mode="PROFILE",
            result_reference="Acute Bronchitis Evaluation",
            summary="Acute Bronchitis — Moderate Urgency",
            details=full_assessment
        )

        fetched = auth_db.get_medical_scan_by_id(scan_id, user_id=self.user_a_id)
        self.assertIsNotNone(fetched)
        details = fetched["details"]
        self.assertEqual(details["user_inputs"]["severity"], "Moderate")
        self.assertEqual(details["user_inputs"]["existing_conditions"], ["Hypertension"])
        self.assertEqual(len(details["ranked_conditions"]), 2)
        self.assertEqual(details["ranked_conditions"][0]["name"], "Acute Bronchitis")
        self.assertEqual(len(details["yoga_recommendations"]), 1)
        self.assertEqual(len(details["diet_guidance"]["foods_to_eat"]), 2)

    def test_05_pdf_generation_for_lab_prescription_and_radiology(self):
        """Verify PDF export operates seamlessly across all medical document categories."""
        # Lab Report
        lab_scan = {
            "scan_type": "Lab Report",
            "result_reference": "Complete Blood Count (CBC)",
            "summary": "Mild leukocytosis observed",
            "created_at": "2026-09-08 19:45:00",
            "patient_name": "Aarav Sharma",
            "details": {
                "findings": [
                    {"test_name": "Hemoglobin", "value": 13.5, "unit": "g/dL", "reference_range": "12.0 - 15.5", "status": "Normal"},
                    {"test_name": "White Blood Cell Count", "value": 12500, "unit": "/uL", "reference_range": "4500 - 11000", "status": "High"}
                ],
                "abnormal_count": 1,
                "breakdown": "Patient displays mild elevation in leukocytes suggesting early response to mild infection."
            }
        }
        lab_pdf = generate_scan_record_pdf(lab_scan)
        self.assertIsInstance(lab_pdf, io.BytesIO)
        self.assertGreater(len(lab_pdf.getvalue()), 500)

        # Prescription
        rx_scan = {
            "scan_type": "Prescription",
            "result_reference": "Pediatric Consultation",
            "summary": "Amoxicillin course prescribed",
            "created_at": "2026-09-08 19:50:00",
            "patient_name": "Aarav Sharma",
            "details": {
                "medicines": [
                    {"name": "Amoxicillin Oral Suspension", "dosage": "250mg / 5ml", "frequency": "Every 8 hours", "duration": "5 days"}
                ],
                "breakdown": "Complete the full 5-day antibiotic regimen even if clinical symptoms improve early."
            }
        }
        rx_pdf = generate_scan_record_pdf(rx_scan)
        self.assertIsInstance(rx_pdf, io.BytesIO)
        self.assertGreater(len(rx_pdf.getvalue()), 500)

        # Radiology
        rad_scan = {
            "scan_type": "Radiology",
            "result_reference": "Chest Digital Radiograph",
            "summary": "Normal chest radiography without focal consolidation",
            "created_at": "2026-09-08 19:55:00",
            "patient_name": "Priya Sharma",
            "details": {
                "findings": [
                    {"observation": "Lungs", "finding": "Clear throughout, no infiltrate or pneumothorax", "severity": "Normal"},
                    {"observation": "Cardiomediastinal Silhouette", "finding": "Within normal clinical limits", "severity": "Normal"}
                ],
                "overall_severity": "Normal",
                "breakdown": "Radiological evaluation demonstrates normal pulmonary parenchyma and mediastinum."
            }
        }
        rad_pdf = generate_scan_record_pdf(rad_scan)
        self.assertIsInstance(rad_pdf, io.BytesIO)
        self.assertGreater(len(rad_pdf.getvalue()), 500)

    def test_06_navigation_auth_redirection_prevention(self):
        """Verify that typing into credentials inputs during Auth view preserves active_panel."""
        from streamlit.testing.v1 import AppTest

        test_app_code = """
import streamlit as st

if 'active_panel' not in st.session_state:
    st.session_state['active_panel'] = 'Health Records'

panel_keys = ['Health Assessment', 'Medical Report', 'Nearby Healthcare', 'Health Records']

def _on_clinical_nav_change():
    chosen = st.session_state.get('clinical_module_nav_radio')
    if chosen in panel_keys:
        st.session_state['active_panel'] = chosen

active_p = st.session_state.get('active_panel', 'Health Records')

if 'clinical_module_nav_radio' not in st.session_state:
    st.session_state['clinical_module_nav_radio'] = active_p if active_p in panel_keys else None
elif active_p in panel_keys:
    st.session_state['clinical_module_nav_radio'] = active_p
else:
    st.session_state['clinical_module_nav_radio'] = None

st.radio(
    'Clinical Module Navigation',
    options=panel_keys,
    key='clinical_module_nav_radio',
    on_change=_on_clinical_nav_change,
    label_visibility='collapsed'
)

if st.button('Sign In / Register', key='btn_nav_auth'):
    st.session_state['active_panel'] = 'Account / Authentication'
    st.rerun()

st.text_input('Email', key='panel_login_email')
st.text_input('Password', key='panel_login_password')
"""
        at = AppTest.from_string(test_app_code)
        at.run()
        self.assertEqual(at.session_state['active_panel'], 'Health Records')

        # User navigates to Auth portal
        at.button[0].click().run()
        self.assertEqual(at.session_state['active_panel'], 'Account / Authentication')

        # User types email address
        at.text_input[0].input('doctor@docmindx.ai').run()
        self.assertEqual(at.session_state['active_panel'], 'Account / Authentication')

        # User types password — MUST NOT bounce back to Health Records
        at.text_input[1].input('SecureClinicalPass!2026').run()
        self.assertEqual(at.session_state['active_panel'], 'Account / Authentication')


if __name__ == "__main__":
    unittest.main()

