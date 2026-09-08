"""
Unit Tests for DocMindX AI — BigQuery National-Scale Telemetry & Sync Engine
Verifies defensive local-first fallback, mock synchronization, and trend query generation.
Must pass 100% offline with zero cloud credentials.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ai.supply_chain.bigquery_sync import bigquery_sync, BigQuerySync

class TestBigQuerySync(unittest.TestCase):
    def setUp(self):
        # Create an unconfigured instance to test pure local fallback
        self.offline_sync = BigQuerySync(project_id="")

    def test_offline_fallback_push_facility_snapshot(self):
        """Verify push_facility_snapshot safely returns LOCAL_NO_OP without credentials."""
        res = self.offline_sync.push_facility_snapshot()
        self.assertEqual(res["status"], "LOCAL_NO_OP")
        self.assertEqual(res["rows_synced"], 0)

    def test_offline_fallback_push_demand_forecast(self):
        """Verify push_demand_forecast safely returns LOCAL_NO_OP without credentials."""
        dummy_forecast = [{"facility_id": "F001", "burn": 120.0}]
        res = self.offline_sync.push_demand_forecast(dummy_forecast)
        self.assertEqual(res["status"], "LOCAL_NO_OP")
        self.assertEqual(res["rows_synced"], 0)

    def test_query_national_trend_local_fallback(self):
        """Verify query_national_trend computes multi-day trend locally when BigQuery is unconfigured."""
        res = self.offline_sync.query_national_trend(days=14, state="Maharashtra")
        self.assertEqual(res["status"], "LOCAL_PARQUET_FALLBACK")
        self.assertEqual(len(res["data"]), 14)
        first_day = res["data"][0]
        self.assertIn("snapshot_date", first_day)
        self.assertIn("total_medicine_burn", first_day)
        self.assertIn("avg_attendance_pct", first_day)
        self.assertGreater(first_day["total_active_beds"], 0)

    def test_mocked_bigquery_online_push(self):
        """Verify push works when BigQuery client is mocked."""
        mock_client = MagicMock()
        mock_job = MagicMock()
        mock_job.result.return_value = None
        mock_client.load_table_from_dataframe.return_value = mock_job

        online_sync = BigQuerySync(project_id="test-DocMindX-proj", dataset_id="command_center")
        online_sync.client = mock_client

        dummy_forecast = [{"facility_id": "F001", "medicine_id": "MED_PCM_500", "forecast": 150}]
        res = online_sync.push_demand_forecast(dummy_forecast)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["rows_synced"], 1)

if __name__ == "__main__":
    unittest.main()
