"""
DocMindX AI — Dedicated Supabase PostgreSQL Database Test Suite
Tests:
- PostgreSQL database configuration & connection pool layer (config.database)
- Live database health check probe & zero credential exposure
- Dialect translation & cursor wrapper
- Supabase schema tables validation
- Public database interfaces in database.auth_db, database.create_tables, database.insert_data
- Backup creation and safety
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from config.database import (
    get_db_connection,
    get_db_cursor,
    check_database_health,
    get_database_engine_name,
    PostgresCursorWrapper
)
import database.auth_db as auth_db
import database.create_tables as create_tables
import database.insert_data as insert_data
from database.backup import create_database_backup, list_backups


def test_database_health_check_supabase():
    """Validates that Supabase PostgreSQL health check returns CONNECTED without leaking credentials."""
    health = check_database_health()
    assert health["status"] == "CONNECTED"
    assert health["healthy"] is True
    assert health["engine"] == "PostgreSQL (Supabase)"
    assert "latency_ms" in health
    assert "password" not in str(health).lower()
    assert "user:" not in str(health).lower()


def test_database_engine_name():
    """Validates engine name reporting is strictly PostgreSQL (Supabase)."""
    engine = get_database_engine_name()
    assert engine == "PostgreSQL (Supabase)"


def test_backup_utility():
    """Validates database snapshot backup creation and file listing."""
    backup_file = create_database_backup()
    assert os.path.exists(backup_file)
    backups = list_backups()
    assert len(backups) > 0
    assert any(b.endswith(".db") for b in backups)


def test_postgres_cursor_wrapper_sql_translation():
    """Validates PostgreSQL cursor wrapper SQL translation and parameter handling."""
    mock_cursor = MagicMock()
    wrapper = PostgresCursorWrapper(mock_cursor)

    # 1. Translate ? to %s
    sql_in = "SELECT * FROM users WHERE email = ? AND role = ?"
    sql_out, is_insert = wrapper._prepare_sql(sql_in)
    assert "%s" in sql_out
    assert "?" not in sql_out
    assert is_insert is False

    # 2. Translate COLLATE NOCASE
    sql_collate = "SELECT * FROM users WHERE email = ? COLLATE NOCASE"
    sql_out, _ = wrapper._prepare_sql(sql_collate)
    assert "COLLATE NOCASE" not in sql_out

    # 3. Add RETURNING id for INSERT
    sql_insert = "INSERT INTO users (full_name, email) VALUES (?, ?)"
    sql_out, is_insert = wrapper._prepare_sql(sql_insert)
    assert is_insert is True
    assert "RETURNING id" in sql_out


def test_schema_postgres_ddl_validity():
    """Validates that schema_postgres.sql exists and contains all required tables."""
    schema_path = os.path.join(WORKSPACE_ROOT, "database", "schema_postgres.sql")
    assert os.path.exists(schema_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read()

    required_tables = [
        "users",
        "family_members",
        "medical_conditions",
        "medications",
        "medical_scans",
        "otp_verifications",
        "security_audit_logs",
        "medicine_cache",
        "triage_history",
        "report_analysis_history",
        "command_center_sources",
        "command_center_facilities",
        "command_center_inventory",
        "command_center_demand",
        "command_center_alerts",
        "command_center_predictions",
        "command_center_transfers",
        "command_center_model_runs"
    ]
    for tbl in required_tables:
        assert f"CREATE TABLE IF NOT EXISTS {tbl}" in content, f"Missing table: {tbl}"


def test_medicine_caching_and_retrieval():
    """Validates medicine cache read/write interfaces in Supabase PostgreSQL."""
    create_tables.cache_medicine(
        medicine_name="TestAzithromycin_101",
        generic_name="Azithromycin",
        active_ingredients="Azithromycin 500mg",
        manufacturer="Test Pharma",
        purpose="Antibacterial",
        warnings="Prescription only"
    )
    cached = create_tables.get_cached_medicine("TestAzithromycin_101")
    assert cached is not None
    assert cached["generic_name"] == "Azithromycin"
    assert cached["manufacturer"] == "Test Pharma"


def test_triage_logging_and_report_history():
    """Validates clinical triage and report analysis persistence in Supabase PostgreSQL."""
    triage_id = insert_data.log_triage_session({
        "session_id": "test_pg_session_1",
        "age": 30,
        "gender": "Female",
        "state": "Gujarat",
        "district": "Surat",
        "duration": "1-2 days",
        "symptoms": ["cough", "mild fever"],
        "ranked_conditions": [{"name": "Acute Bronchitis", "probability": 0.82}],
        "is_emergency": False
    })
    assert triage_id is not None and triage_id > 0

    recent_triage = insert_data.get_recent_triage_history(limit=5)
    assert len(recent_triage) > 0
    assert any(t.get("session_id") == "test_pg_session_1" for t in recent_triage)

    report_id = insert_data.log_report_analysis(
        report_name="Test CBC Panel PG",
        report_type="Lab Report",
        extracted_text="Hemoglobin 14.2 g/dL",
        summary="Normal CBC",
        findings=[{"test": "Hemoglobin", "value": "14.2"}],
        abnormal_count=0
    )
    assert report_id is not None and report_id > 0

    recent_reports = insert_data.get_recent_report_history(limit=5)
    assert len(recent_reports) > 0


def test_auth_crud_roundtrip():
    """Validates authentication user creation, retrieval, status update, and audit logging in Supabase."""
    test_email = "db_pg_user_test@docmindx.ai"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
    conn.commit()
    conn.close()

    user_id = auth_db.create_user(
        full_name="PostgreSQL Test User",
        email=test_email,
        password_hash="$2b$12$eTestPasswordHashForDbVerificationOnly000",
        account_status="ACTIVE",
        email_verified=1,
        dob="1995-06-15"
    )
    assert user_id > 0

    user = auth_db.get_user_by_email(test_email)
    assert user is not None
    assert user["id"] == user_id
    assert user["full_name"] == "PostgreSQL Test User"
    assert user["age"] is not None

    auth_db.log_security_event("TEST_PG_AUDIT", email=test_email, user_id=user_id, details="Audit log probe")
    kpis = auth_db.admin_get_kpis()
    assert kpis["total_users"] > 0
    assert len(kpis["recent_activity"]) > 0

    # Cleanup
    auth_db.admin_delete_user(user_id, permanent=True)
