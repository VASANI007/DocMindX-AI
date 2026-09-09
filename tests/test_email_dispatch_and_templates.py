import sys
import os
import unittest
import re

# Ensure workspace root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services import email_service

class TestEmailServiceTemplates(unittest.TestCase):
    def test_otp_html_template_elements(self):
        otp = "185139"
        # Test digit box generation
        boxes = email_service.render_otp_digit_boxes(otp)
        for digit in otp:
            self.assertIn(f">{digit}</span>", boxes)

        # Test base template
        html = email_service.get_base_html_template(
            title="National Administrator Console Key",
            hero_title="National Administrator Console Key",
            hero_subtitle="Authorized Personnel Only &bull; Valid 10m",
            body_content=f"<div style='text-align:center;'>{boxes}</div>"
        )
        # Check branding
        self.assertIn("DocMindX", html)
        self.assertIn("CLINICAL AI HEALTHCARE SYSTEM", html)
        self.assertIn("Your Health Data", html)
        self.assertIn("Our Priority", html)
        self.assertIn("icon.png", html)
        # Check trust badges and compliance
        self.assertIn("HIPAA &amp; WHO Compliant", html)
        self.assertIn("Clinical AI", html)
        # Ensure zero Unicode emoji (uses email-safe glyphs/HTML entities instead)
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        self.assertFalse(emoji_pattern.search(html), "HTML template must not contain raw Unicode emojis!")

    def test_login_success_dispatch(self):
        res = email_service.send_login_success_notice(
            email="testuser@example.com",
            full_name="Daksh Vasani"
        )
        self.assertIsInstance(res, bool)
        if "testuser@example.com" in email_service.DEV_EMAIL_INBOX:
            msg = email_service.DEV_EMAIL_INBOX["testuser@example.com"]
            self.assertIn("Successful Account Login", msg["subject"])
            self.assertIn("Daksh Vasani", msg["html"])

    def test_login_failed_dispatch(self):
        res = email_service.send_login_failed_alert(
            email="testuser@example.com",
            full_name="Daksh Vasani",
            reason="Invalid credentials entered"
        )
        self.assertIsInstance(res, bool)
        if "testuser@example.com" in email_service.DEV_EMAIL_INBOX:
            msg = email_service.DEV_EMAIL_INBOX["testuser@example.com"]
            self.assertIn("Unsuccessful Login Attempt", msg["subject"])
            self.assertIn("Invalid credentials entered", msg["html"])

    def test_support_ticket_to_admin_and_user(self):
        ticket_id = "TKT-A92B1C"
        user_email = "clinician@hospital.org"
        issue_desc = "Unable to process batch prescriptions on module 2."
        
        # Test admin dispatch
        res_admin = email_service.send_support_ticket_to_admin(
            user_email=user_email,
            issue_text=issue_desc,
            ticket_id=ticket_id,
            user_name="Dr. Sharma"
        )
        self.assertIsInstance(res_admin, bool)
        if email_service.ADMIN_EMAIL in email_service.DEV_EMAIL_INBOX:
            msg_admin = email_service.DEV_EMAIL_INBOX[email_service.ADMIN_EMAIL]
            self.assertIn(ticket_id, msg_admin["subject"])
            self.assertIn(user_email, msg_admin["html"])
            self.assertIn(issue_desc, msg_admin["html"])

        # Test user confirmation with 24-hour promise
        res_user = email_service.send_support_ticket_confirmation_to_user(
            user_email=user_email,
            issue_text=issue_desc,
            ticket_id=ticket_id,
            user_name="Dr. Sharma"
        )
        self.assertIsInstance(res_user, bool)
        if user_email in email_service.DEV_EMAIL_INBOX:
            msg_user = email_service.DEV_EMAIL_INBOX[user_email]
            self.assertIn(ticket_id, msg_user["subject"])
            self.assertIn("24 hours", msg_user["html"])
            self.assertIn("Dr. Sharma", msg_user["html"])

    def test_admin_login_otp_dispatch(self):
        admin_email = "docmindxai@gmail.com"
        otp = "984217"
        res = email_service.send_admin_login_otp(email=admin_email, otp=otp)
        self.assertTrue(res)
        self.assertIn(admin_email, email_service.DEV_EMAIL_INBOX)
        msg = email_service.DEV_EMAIL_INBOX[admin_email]
        self.assertIn("ADMIN PANEL", msg["subject"])
        self.assertIn("ADMIN CONSOLE KEY", msg["html"])
        for digit in otp:
            self.assertIn(f">{digit}</span>", msg["html"])
        # Ensure zero raw emojis
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]", flags=re.UNICODE)
        self.assertFalse(emoji_pattern.search(msg["html"]))

if __name__ == "__main__":
    unittest.main()
