"""
    DocMindX AI - SQLite Database Backup & Recovery Utility
"""
import os
import shutil
import datetime

DB_DIR = os.path.dirname(__file__)
MAIN_DB = os.path.join(DB_DIR, "DocMindX.db")
BACKUP_DIR = os.path.join(DB_DIR, "backups")

def create_database_backup() -> str:
    """Creates a timestamped snapshot of the SQLite database."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(MAIN_DB):
        return "Main database not found"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"DocMindX_backup_{timestamp}.db")
    shutil.copy2(MAIN_DB, backup_file)
    return backup_file

def list_backups() -> list:
    """Returns all available database backup files."""
    if not os.path.exists(BACKUP_DIR):
        return []
    return [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
