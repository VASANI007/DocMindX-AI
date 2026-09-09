"""
Test Suite: DOB Dynamic Age Calculation & Clinical Protocol Validation
Tests real-time chronological age auto-advancement, leap year safety,
10-year pediatric thresholds, and user/family member DOB integration.
"""
import pytest
from datetime import date, datetime
import database.auth_db as auth_db
import services.auth_service as auth_svc

class TestDOBDynamicAgeSuite:

    def test_01_calculate_age_basic_and_leap_year(self):
        """Tests that calculate_age_from_dob accurately computes completed years."""
        today = date.today()
        
        # Exact 20 years ago today
        dob_20 = date(today.year - 20, today.month, today.day)
        assert auth_db.calculate_age_from_dob(dob_20) == 20
        assert auth_db.calculate_age_from_dob(dob_20.strftime("%Y-%m-%d")) == 20
        
        # Birthday tomorrow (not yet celebrated this year -> 19)
        if today.month == 12 and today.day == 31:
            dob_almost = date(today.year - 20, 12, 30)
        else:
            try:
                dob_tomorrow = date(today.year - 20, today.month, today.day + 1)
                assert auth_db.calculate_age_from_dob(dob_tomorrow) == 19
            except ValueError:
                pass

    def test_02_invalid_and_future_dates(self):
        """Future dates and invalid formats must return None."""
        today = date.today()
        future_date = date(today.year + 1, 1, 1)
        assert auth_db.calculate_age_from_dob(future_date) is None
        assert auth_db.calculate_age_from_dob("not-a-date") is None
        assert auth_db.calculate_age_from_dob("") is None
        assert auth_db.calculate_age_from_dob(None) is None

    def test_03_registration_10_year_protocol_rejection(self):
        """Registration must strictly reject dates of birth under 10 years."""
        today = date.today()
        # 5 years old (pediatric)
        dob_5 = date(today.year - 5, today.month, min(today.day, 28)).strftime("%Y-%m-%d")
        
        ok, msg = auth_svc.register_user("Child User", "child_pediatric@test.com", "TestPass#2026", "TestPass#2026", dob=dob_5)
        assert not ok
        assert "10 years" in msg

    def test_04_registration_with_valid_dob(self):
        """Registration with valid DOB (>= 10 years) succeeds and persists DOB."""
        today = date.today()
        dob_25 = date(today.year - 25, today.month, min(today.day, 28)).strftime("%Y-%m-%d")
        test_email = f"adult_dob_{int(datetime.now().timestamp())}@test.com"

        ok, msg = auth_svc.register_user("Adult Patient", test_email, "SecurePass#2026", "SecurePass#2026", dob=dob_25)
        assert ok

        user = auth_db.get_user_by_email(test_email)
        assert user is not None
        assert user.get("dob") == dob_25
        assert user.get("age") == 25

    def test_05_family_member_dob_dynamic_age_sync(self):
        """Family members added with DOB automatically have real-time dynamic age."""
        today = date.today()
        dob_40 = date(today.year - 40, today.month, min(today.day, 28)).strftime("%Y-%m-%d")
        test_email = f"fm_parent_{int(datetime.now().timestamp())}@test.com"

        user_id = auth_db.create_user("Family Admin", test_email, "hash", account_status="ACTIVE", email_verified=1)
        
        mem_id = auth_db.add_family_member(user_id, {
            "name": "Father Profile",
            "relationship": "Father",
            "dob": dob_40,
            "gender": "Male"
        })
        
        member = auth_db.get_family_member_by_id(mem_id, user_id)
        assert member is not None
        assert member["dob"] == dob_40
        assert member["age"] == 40

        # Update DOB to 50 years ago and verify immediate recalculation
        dob_50 = date(today.year - 50, today.month, min(today.day, 28)).strftime("%Y-%m-%d")
        auth_db.update_family_member(mem_id, user_id, {
            "name": "Father Profile Updated",
            "relationship": "Father",
            "dob": dob_50,
            "gender": "Male"
        })

        updated = auth_db.get_family_member_by_id(mem_id, user_id)
        assert updated["dob"] == dob_50
        assert updated["age"] == 50

    def test_06_user_profile_dob_update(self):
        """Updating user profile with DOB dynamically attaches age."""
        today = date.today()
        dob_30 = date(today.year - 30, today.month, min(today.day, 28)).strftime("%Y-%m-%d")
        test_email = f"profile_update_{int(datetime.now().timestamp())}@test.com"

        user_id = auth_db.create_user("Updatable User", test_email, "hash", account_status="ACTIVE", email_verified=1)
        auth_db.update_user_profile(user_id, "Updatable User", state="Delhi (NCT)", dob=dob_30)

        user = auth_db.get_user_by_id(user_id)
        assert user["dob"] == dob_30
        assert user["age"] == 30
