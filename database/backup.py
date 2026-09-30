"""
DocMindX AI — Database Backup & Archive Utility (Supabase PostgreSQL)
"""
import os
import json
import datetime
from config.database import get_db_connection

DB_DIR = os.path.dirname(__file__)
BACKUP_DIR = os.path.join(DB_DIR, "backups")

def create_database_backup() -> str:
    """Creates a timestamped snapshot of core Supabase PostgreSQL records."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"supabase_backup_{timestamp}.json")

    snapshot = {}
    tables = [
        "users", "family_members", "medical_conditions", "medications",
        "medical_scans", "otp_verifications", "security_audit_logs",
        "medicine_cache", "triage_history", "report_analysis_history"
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for tbl in tables:
            try:
                cursor.execute(f'SELECT * FROM "{tbl}"')
                rows = cursor.fetchall()
                snapshot[tbl] = [dict(r) for r in rows]
            except Exception:
                snapshot[tbl] = []
        conn.close()

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, default=str)
        return backup_file
    except Exception as e:
        return f"Backup error: {e}"

def list_backups() -> list:
    """Returns all available database backup files."""
    if not os.path.exists(BACKUP_DIR):
        return []
    return [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".db") or f.endswith(".json")]
