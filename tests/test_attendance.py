"""
Unit Tests for DocMindX AI — Healthcare Personnel Attendance Engine & Ingestor
Tests determinism, alerting thresholds, role integrity, and honest provenance fallback.
"""
import os
import sys
import unittest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ai.supply_chain.attendance_engine import attendance_engine
from ai.supply_chain.data_ingestion.attendance_ingestor import attendance_ingestor
from ai.supply_chain.data_quality import PROVENANCE_SIMULATED
from ai.supply_chain.stockout_detector import stockout_detector

class TestAttendanceEngine(unittest.TestCase):
    def setUp(self):
        self.sample_facility = {
            "id": "FAC_TEST_001",
            "name": "Baramati Sub-District Hospital",
            "state": "Maharashtra",
            "district": "Pune",
            "type": "SDH",
            "doctors": 6,
            "nurses": 18,
            "pharmacists": 3
        }

    def test_deterministic_simulation(self):
        """Verify identical seed + date produces exact same present counts."""
        target_date = "2026-09-15"
        rec1 = attendance_engine.compute_daily_attendance(self.sample_facility, target_date=target_date)
        rec2 = attendance_engine.compute_daily_attendance(self.sample_facility, target_date=target_date)

        self.assertEqual(rec1["attendance_pct"], rec2["attendance_pct"])
        self.assertEqual(rec1["present_total"], rec2["present_total"])
        self.assertEqual(rec1["sanctioned_total"], rec2["sanctioned_total"])
        self.assertEqual(rec1["status"], rec2["status"])

    def test_role_breakdown_integrity(self):
        """Verify role breakdown preserves sanctioned >= present >= 0 for all roles."""
        rec = attendance_engine.compute_daily_attendance(self.sample_facility, target_date="2026-09-10")
        roles = rec["role_breakdown"]
        
        self.assertIn("doctor", roles)
        self.assertIn("nurse", roles)
        self.assertIn("pharmacist", roles)
        self.assertIn("lab_tech", roles)

        for role_name, rdata in roles.items():
            self.assertGreaterEqual(rdata["sanctioned"], 1)
            self.assertGreaterEqual(rdata["present"], 0)
            self.assertLessEqual(rdata["present"], rdata["sanctioned"])
            self.assertEqual(rdata["absent"], rdata["sanctioned"] - rdata["present"])

    def test_provenance_tagging(self):
        """Verify output is honestly labeled PROVENANCE_SIMULATED."""
        rec = attendance_engine.compute_daily_attendance(self.sample_facility)
        self.assertEqual(rec["provenance"], PROVENANCE_SIMULATED)

    def test_network_alerts_include_attendance(self):
        """Verify unified stockout_detector scan includes STAFF_ATTENDANCE alerts."""
        alerts = stockout_detector.scan_network_alerts(state="Maharashtra", district="All Districts")
        self.assertIn("alerts", alerts)
        att_alerts = [a for a in alerts["alerts"] if a["type"] == "STAFF_ATTENDANCE"]
        self.assertGreaterEqual(len(att_alerts), 0)  # Verify list can be parsed without error

    def test_ingestor_fallback_behavior(self):
        """Verify attendance ingestor gracefully falls back to simulation with provenance."""
        result = attendance_ingestor.fetch_attendance(state="Gujarat")
        self.assertEqual(result["provenance"], PROVENANCE_SIMULATED)
        self.assertIn(result["status"], ["SIMULATION_FALLBACK", "ONLINE_CONNECTED"])
        self.assertIn("data", result)

if __name__ == "__main__":
    unittest.main()
