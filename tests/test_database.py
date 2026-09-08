"""
    DocMindX AI - Database Test Suite
"""
import unittest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.insert_data import log_triage_session, log_report_analysis, get_db_connection
from database.backup import create_database_backup, list_backups

class TestDatabase(unittest.TestCase):
    
    def test_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_log_triage_session(self):
        sample = {
            "session_id": "test_session_123",
            "age": "Adult",
            "gender": "Male",
            "symptoms": ["Fever", "Headache"],
            "urgency_level": "NORMAL"
        }
        res_id = log_triage_session(sample)
        self.assertIsInstance(res_id, int)
        self.assertGreater(res_id, 0)

    def test_database_backup(self):
        bk = create_database_backup()
        self.assertTrue(os.path.exists(bk))
        bks = list_backups()
        self.assertGreater(len(bks), 0)

if __name__ == "__main__":
    unittest.main()
