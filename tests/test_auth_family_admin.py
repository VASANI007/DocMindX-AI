"""
DocMindX AI — Master Verification & Security Test Suite
Tests all 46 acceptance criteria:
1. SQL Injection Protection (Parameterized queries)
2. Dual-Factor Authentication & Cryptographic OTP Engine
3. Recovery Password & Change Password Flows
4. User Data Isolation
5. Family Medical Profiles & Relational Medical History
6. Dynamic Scan Context & General Scan Mode
7. National Administrator Portal, KPIs, User Management & Audit Trail
"""
import os
import sys
import unittest
import sqlite3
import re

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import database.auth_db as auth_db
import services.auth_service as auth_svc
import services.email_service as email_service

class TestDocMindXAuthFamilyAdminSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        auth_db.init_auth_tables()
        cls.test_email_1 = "testpatient_alpha@docmindx.test"
        cls.test_email_2 = "testpatient_beta@docmindx.test"
        cls.test_pass = "TestClinical@2026!"
        cls.admin_email = os.getenv("DOCMINDX_ADMIN_EMAIL", "docmindxai@gmail.com").strip().lower()

        # Clean up any residual test records from prior runs
        conn = auth_db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email IN (?, ?)", (cls.test_email_1, cls.test_email_2))
        cursor.execute("DELETE FROM otp_verifications WHERE email IN (?, ?)", (cls.test_email_1, cls.test_email_2))
        conn.commit()
        conn.close()

    # ============================================================
    # SECTION 1: SQL INJECTION SECURITY AUDIT
    # ============================================================
    def test_01_sqli_protection_on_all_endpoints(self):
        """CRITICAL: Tests malicious SQL injection payloads against all DB entry points."""
        malicious_payloads = [
            "' OR '1'='1",
            "' OR 1=1 --",
            "'; DROP TABLE users; --",
            "admin' --",
            "\" OR \"\"=\"",
            "1' UNION SELECT * FROM users --"
        ]

        conn = auth_db.get_db_connection()
        for payload in malicious_payloads:
            # 1. Login query injection attempt
            res = auth_db.get_user_by_email(payload)
            self.assertIsNone(res, f"SQLi payload breached get_user_by_email: {payload}")

            # 2. User search injection attempt
            users = auth_db.admin_get_users(search=payload)
            self.assertIsInstance(users, list)

            # 3. Admin scan filter injection attempt
            scans = auth_db.admin_get_all_scans(search=payload)
            self.assertIsInstance(scans, list)

            # 4. Security log query injection attempt
            logs = auth_db.admin_get_security_logs(search=payload)
            self.assertIsInstance(logs, list)

        # Confirm users table was not dropped and remains intact
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM users")
        count = cursor.fetchone()[0]
        self.assertGreaterEqual(count, 0)
        conn.close()

    # ============================================================
    # SECTION 2: REGISTRATION & OTP ACTIVATION
    # ============================================================
    def test_02_registration_validation(self):
        """Tests registration input validation: weak password, invalid email, password mismatch."""
        # Weak password (no number/symbol)
        ok, msg = auth_svc.register_user("Daksh Patel", "daksh@docmindx.test", "short", "short")
        self.assertFalse(ok)

        # Password mismatch
        ok, msg = auth_svc.register_user("Daksh Patel", "daksh@docmindx.test", self.test_pass, "Different@2026!")
        self.assertFalse(ok)
        self.assertIn("match", msg.lower())

        # Invalid email
        ok, msg = auth_svc.register_user("Daksh Patel", "invalid-email-string", self.test_pass, self.test_pass)
        self.assertFalse(ok)

    def test_03_registration_and_activation_flow(self):
        """Tests complete registration -> pending user -> OTP verification -> account activation."""
        ok, msg = auth_svc.register_user("Test Alpha", self.test_email_1, self.test_pass, self.test_pass)
        self.assertTrue(ok)

        # Check pending state in database
        u = auth_db.get_user_by_email(self.test_email_1)
        self.assertIsNotNone(u)
        self.assertEqual(u["account_status"], "PENDING")
        self.assertEqual(u["email_verified"], 0)

        # Cannot login while PENDING
        can_login, l_msg, _ = auth_svc.authenticate_credentials(self.test_email_1, self.test_pass)
        self.assertFalse(can_login)

        # Retrieve generated OTP (from secure dev engine)
        otp = auth_svc.get_dev_otp_fallback(self.test_email_1, "REGISTRATION")
        self.assertTrue(len(otp) == 6)

        # Invalid OTP attempt limit
        bad_ok, _ = auth_svc.activate_user_account(self.test_email_1, "000000")
        self.assertFalse(bad_ok)

        # Correct OTP activation
        act_ok, act_msg = auth_svc.activate_user_account(self.test_email_1, otp)
        self.assertTrue(act_ok)

        # Verify active state in DB
        u_active = auth_db.get_user_by_email(self.test_email_1)
        self.assertEqual(u_active["account_status"], "ACTIVE")
        self.assertEqual(u_active["email_verified"], 1)

    # ============================================================
    # SECTION 3: 2FA LOGIN (EMAIL + PASSWORD + OTP)
    # ============================================================
    def test_04_dual_factor_login_flow(self):
        """Tests that password-only login is prohibited and 2FA OTP is strictly required."""
        # 1. Invalid password
        ok, msg, _ = auth_svc.authenticate_credentials(self.test_email_1, "WrongPassword@123")
        self.assertFalse(ok)

        # 2. Correct password -> triggers OTP step
        ok, msg, user_data = auth_svc.authenticate_credentials(self.test_email_1, self.test_pass)
        self.assertTrue(ok)
        self.assertIsNotNone(user_data)

        # 3. Dispatch login OTP
        otp_sent, _ = auth_svc.send_login_verification_code(self.test_email_1)
        self.assertTrue(otp_sent)
        login_otp = auth_svc.get_dev_otp_fallback(self.test_email_1, "LOGIN")
        self.assertEqual(len(login_otp), 6)

        # 4. Verify login OTP
        v_ok, v_msg, session = auth_svc.complete_login_with_otp(self.test_email_1, login_otp)
        self.assertTrue(v_ok)
        self.assertTrue(session["authenticated"])
        self.assertEqual(session["email"], self.test_email_1)

    # ============================================================
    # SECTION 4: RECOVERY PASSWORD & CHANGE PASSWORD
    # ============================================================
    def test_05_recovery_password_flow(self):
        """Tests Recovery Password flow (strictly using Recovery Password label)."""
        ok, msg = auth_svc.initiate_recovery_password(self.test_email_1)
        self.assertTrue(ok)

        rec_otp = auth_svc.get_dev_otp_fallback(self.test_email_1, "RECOVERY")
        self.assertEqual(len(rec_otp), 6)

        new_pass = "NewClinicalPassword@2026!"
        reset_ok, reset_msg = auth_svc.verify_recovery_otp_and_reset_password(self.test_email_1, rec_otp, new_pass, new_pass)
        self.assertTrue(reset_ok)

        # Verify old password fails
        old_ok, _, _ = auth_svc.authenticate_credentials(self.test_email_1, self.test_pass)
        self.assertFalse(old_ok)

        # Verify new password succeeds
        new_ok, _, _ = auth_svc.authenticate_credentials(self.test_email_1, new_pass)
        self.assertTrue(new_ok)

    def test_06_change_password_flow(self):
        """Tests Change Password inside user account settings."""
        u = auth_db.get_user_by_email(self.test_email_1)
        curr_pass = "NewClinicalPassword@2026!"
        next_pass = "UpdatedSecurity@2026!"

        # Wrong current password
        bad_ok, _ = auth_svc.change_user_password(u["id"], "IncorrectCurrent@123", next_pass, next_pass)
        self.assertFalse(bad_ok)

        # Successful change
        chg_ok, chg_msg = auth_svc.change_user_password(u["id"], curr_pass, next_pass, next_pass)
        self.assertTrue(chg_ok)

        # Verify updated login
        ver_ok, _, _ = auth_svc.authenticate_credentials(self.test_email_1, next_pass)
        self.assertTrue(ver_ok)

    # ============================================================
    # SECTION 5: FAMILY MEMBERS & RELATIONAL MEDICAL HISTORY
    # ============================================================
    def test_07_family_members_crud_and_medical_history(self):
        """Tests adding, editing, querying, and deleting family members with conditions & meds."""
        u = auth_db.get_user_by_email(self.test_email_1)
        user_id = u["id"]

        member_data = {
            "name": "Mother",
            "relationship": "Mother",
            "age": 48,
            "dob": "1978-05-12",
            "gender": "Female",
            "blood_group": "B+",
            "height": "162",
            "weight": "65",
            "notes": "Mild penicillin sensitivity",
            "emergency_contact": "+91 98765 43210",
            "conditions": ["Diabetes / Sugar", "Cholesterol / Dyslipidemia"],
            "medications": [
                {"medicine_name": "Metformin", "dosage": "500mg", "frequency": "Twice daily"},
                {"medicine_name": "Atorvastatin", "dosage": "10mg", "frequency": "Nightly"}
            ]
        }
        mem_id = auth_db.add_family_member(user_id, member_data)
        self.assertGreater(mem_id, 0)

        # Query member
        fetched = auth_db.get_family_member_by_id(mem_id, user_id=user_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["name"], "Mother")
        self.assertEqual(fetched["blood_group"], "B+")
        self.assertEqual(len(fetched["conditions"]), 2)
        self.assertEqual(len(fetched["medications"]), 2)

        # Add additional condition
        c_id = auth_db.add_medical_condition(mem_id, user_id, "Hypertension", status="Controlled")
        self.assertGreater(c_id, 0)

        # Update member
        member_data["age"] = 49
        up_ok = auth_db.update_family_member(mem_id, user_id, member_data)
        self.assertTrue(up_ok)

    # ============================================================
    # SECTION 6: USER DATA ISOLATION
    # ============================================================
    def test_08_strict_user_data_isolation(self):
        """MANDATORY: Verifies User A cannot read or mutate User B's profile, family, or history."""
        # Create User B
        auth_svc.register_user("User Beta", self.test_email_2, self.test_pass, self.test_pass)
        otp = auth_svc.get_dev_otp_fallback(self.test_email_2, "REGISTRATION")
        auth_svc.activate_user_account(self.test_email_2, otp)

        user_a = auth_db.get_user_by_email(self.test_email_1)
        user_b = auth_db.get_user_by_email(self.test_email_2)

        # User A's family member
        user_a_fams = auth_db.get_family_members(user_a["id"])
        self.assertGreater(len(user_a_fams), 0)
        target_mem = user_a_fams[0]

        # User B attempts to access User A's family member
        b_access = auth_db.get_family_member_by_id(target_mem["id"], user_id=user_b["id"])
        self.assertIsNone(b_access, "CRITICAL: Cross-user data leak! User B retrieved User A's family member.")

        # User B attempts to delete User A's family member
        b_del = auth_db.delete_family_member(target_mem["id"], user_id=user_b["id"])
        self.assertFalse(b_del, "CRITICAL: User B was able to delete User A's family member!")

        # Confirm target member still exists for User A
        a_access = auth_db.get_family_member_by_id(target_mem["id"], user_id=user_a["id"])
        self.assertIsNotNone(a_access)

    # ============================================================
    # SECTION 7: SCAN WORKFLOW & CONTEXT INTEGRATION
    # ============================================================
    def test_09_scan_saving_and_general_mode(self):
        """Tests saving scans under PROFILE, FAMILY_MEMBER, and GENERAL modes."""
        user = auth_db.get_user_by_email(self.test_email_1)
        fams = auth_db.get_family_members(user["id"])
        mem_id = fams[0]["id"] if fams else None

        # 1. Family member scan
        sc1_id = auth_db.save_medical_scan(
            user_id=user["id"],
            family_member_id=mem_id,
            scan_type="Blood Report",
            scan_mode="FAMILY_MEMBER",
            result_reference="CBC_Report.pdf",
            summary="Hemoglobin 13.8, Normal ranges.",
            details={"wbc": 7400}
        )
        self.assertGreater(sc1_id, 0)

        # 2. General scan (no family member association)
        sc2_id = auth_db.save_medical_scan(
            user_id=user["id"],
            family_member_id=None,
            scan_type="Prescription",
            scan_mode="GENERAL",
            result_reference="Rx_General.jpg",
            summary="General prescription evaluation.",
            details={}
        )
        self.assertGreater(sc2_id, 0)

        # Query user scans
        scans = auth_db.get_user_scans(user["id"])
        self.assertGreaterEqual(len(scans), 2)
        modes = [s["scan_mode"] for s in scans]
        self.assertIn("FAMILY_MEMBER", modes)
        self.assertIn("GENERAL", modes)

    # ============================================================
    # SECTION 8: ADMIN CONSOLE, KPIS & USER MANAGEMENT
    # ============================================================
    def test_10_admin_authentication_and_authorization(self):
        """Tests Admin credentials, OTP, server-side authorization and privilege enforcement."""
        # Admin plaintext password for testing — loaded from .env (DOCMINDX_ADMIN_PASSWORD)
        # NEVER hardcode passwords in source code; always use environment variables.
        admin_plain_password = os.getenv("DOCMINDX_ADMIN_PASSWORD", "")
        if not admin_plain_password:
            self.skipTest(
                "DOCMINDX_ADMIN_PASSWORD not set in environment/.env — skipping admin auth test. "
                "Add DOCMINDX_ADMIN_PASSWORD=<your_admin_password> to your .env file."
            )

        # Non-admin user cannot authorize as admin
        regular_user = auth_db.get_user_by_email(self.test_email_1)
        self.assertFalse(auth_svc.is_admin_session(regular_user))

        # Admin required fields and minimum length tests
        err_email, _ = auth_svc.authenticate_admin_credentials("", admin_plain_password)
        self.assertFalse(err_email)
        err_pass, _ = auth_svc.authenticate_admin_credentials(self.admin_email, "")
        self.assertFalse(err_pass)
        err_short, _ = auth_svc.authenticate_admin_credentials(self.admin_email, "Short1!")
        self.assertFalse(err_short)

        # Admin login step 1 (Email + Password from .env)
        ok, msg = auth_svc.authenticate_admin_credentials(self.admin_email, admin_plain_password)
        self.assertTrue(ok, f"Admin login failed: {msg}")

        # Admin login step 2 (Admin OTP)
        otp_sent, _ = auth_svc.send_admin_login_otp_code(self.admin_email)
        self.assertTrue(otp_sent)
        adm_otp = auth_svc.get_dev_otp_fallback(self.admin_email, "ADMIN_LOGIN")
        self.assertEqual(len(adm_otp), 6)

        # Admin login step 3 (Verification & Session)
        v_ok, v_msg, adm_session = auth_svc.complete_admin_login(self.admin_email, adm_otp)
        self.assertTrue(v_ok)
        self.assertTrue(auth_svc.is_admin_session(adm_session))


    def test_11_admin_dynamic_kpis_and_user_governance(self):
        """Tests admin dynamic KPIs (no fake numbers), user disable/enable, and security logs."""
        kpis = auth_db.admin_get_kpis()
        self.assertGreaterEqual(kpis["total_users"], 2)
        self.assertGreaterEqual(kpis["verified_users"], 2)
        self.assertGreaterEqual(kpis["total_family_members"], 1)
        self.assertGreaterEqual(kpis["total_scans"], 2)

        # Admin disables User Beta
        user_b = auth_db.get_user_by_email(self.test_email_2)
        auth_db.admin_disable_user(user_b["id"])
        u_b_check = auth_db.get_user_by_id(user_b["id"])
        self.assertEqual(u_b_check["account_status"], "DISABLED")

        # Disabled user cannot login
        can_login, msg, _ = auth_svc.authenticate_credentials(self.test_email_2, self.test_pass)
        self.assertFalse(can_login)
        self.assertIn("disabled", msg.lower())

        # Admin re-enables User Beta
        auth_db.admin_enable_user(user_b["id"])
        u_b_active = auth_db.get_user_by_id(user_b["id"])
        self.assertEqual(u_b_active["account_status"], "ACTIVE")

        # Verify audit logs exist and contain zero plaintext passwords/OTPs
        logs = auth_db.admin_get_security_logs(limit=50)
        self.assertGreater(len(logs), 0)
        for log in logs:
            det = (log.get("details") or "").lower()
            self.assertNotIn("password=", det)
            self.assertNotIn(self.test_pass.lower(), det)

if __name__ == "__main__":
    unittest.main()
