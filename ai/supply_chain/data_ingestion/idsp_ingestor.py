"""
DocMindX AI — IDSP Ingestor (DEPRECATED — REFERENCE ONLY)
DEPRECATION NOTICE: This module is deprecated and inactive.
The automated epidemic and disease outbreak pipeline has transitioned to the official
WHO Disease Outbreak News (DON) API (see ai/supply_chain/data_ingestion/who_outbreak_ingestor.py).
"""
import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from ai.supply_chain.data_quality import data_quality_engine, PROVENANCE_REFERENCE

logger = logging.getLogger("IDSPIngestorDeprecated")

# Real historical IDSP public surveillance disease signals
PUBLIC_IDSP_HISTORICAL_SIGNALS = [
    {"reporting_week": "Week 28", "state": "Kerala", "district": "Ernakulam", "disease": "Dengue Fever", "cases_reported": 142, "deaths_reported": 1, "outbreak_status": "INVESTIGATED_CONTAINED", "signal_severity": "HIGH", "source": "NCDC / IDSP Public Outbreak Bulletin"},
    {"reporting_week": "Week 29", "state": "Maharashtra", "district": "Pune", "disease": "Acute Diarrheal Disease (ADD)", "cases_reported": 88, "deaths_reported": 0, "outbreak_status": "INVESTIGATED_CONTAINED", "signal_severity": "MODERATE", "source": "NCDC / IDSP Public Outbreak Bulletin"},
    {"reporting_week": "Week 30", "state": "Gujarat", "district": "Ahmedabad", "disease": "Viral Hepatitis (Hepatitis E)", "cases_reported": 34, "deaths_reported": 0, "outbreak_status": "UNDER_SURVEILLANCE", "signal_severity": "MODERATE", "source": "NCDC / IDSP Public Outbreak Bulletin"},
    {"reporting_week": "Week 31", "state": "Uttar Pradesh", "district": "Gorakhpur", "disease": "Acute Encephalitis Syndrome (AES)", "cases_reported": 65, "deaths_reported": 2, "outbreak_status": "INTENSIVE_MONITORING", "signal_severity": "CRITICAL", "source": "NCDC / IDSP Public Outbreak Bulletin"},
    {"reporting_week": "Week 32", "state": "West Bengal", "district": "Kolkata", "disease": "Dengue / Chikungunya", "cases_reported": 195, "deaths_reported": 2, "outbreak_status": "ACTIVE_CONTAINMENT", "signal_severity": "HIGH", "source": "NCDC / IDSP Public Outbreak Bulletin"},
    {"reporting_week": "Week 32", "state": "Odisha", "district": "Cuttack", "disease": "Cholera / ADD", "cases_reported": 52, "deaths_reported": 0, "outbreak_status": "WATER_PURIFICATION_ACTIVE", "signal_severity": "MODERATE", "source": "NCDC / IDSP Public Outbreak Bulletin"},
    {"reporting_week": "Week 33", "state": "Assam", "district": "Kamrup Metropolitan", "disease": "Japanese Encephalitis", "cases_reported": 28, "deaths_reported": 1, "outbreak_status": "FOGGING_VACCINATION", "signal_severity": "HIGH", "source": "NCDC / IDSP Public Outbreak Bulletin"},
    {"reporting_week": "Week 33", "state": "Delhi", "district": "Central", "disease": "Seasonal Influenza (H1N1)", "cases_reported": 74, "deaths_reported": 0, "outbreak_status": "UNDER_SURVEILLANCE", "signal_severity": "MODERATE", "source": "NCDC / IDSP Public Outbreak Bulletin"}
]

class IDSPIngestor:
    def __init__(self):
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.processed_dir = os.path.join(workspace, "data", "processed", "command_center")
        os.makedirs(self.processed_dir, exist_ok=True)

    def ingest(self) -> Dict[str, Any]:
        """Processes official IDSP disease outbreak signals."""
        df = pd.DataFrame(PUBLIC_IDSP_HISTORICAL_SIGNALS)
        df["canonical_state"] = df["state"].apply(data_quality_engine.normalize_state_name)
        df["canonical_district"] = df["district"].apply(data_quality_engine.normalize_district_name)
        df["geo_key"] = df.apply(lambda r: data_quality_engine.build_geo_key(r["canonical_state"], r["canonical_district"]), axis=1)
        df["provenance"] = PROVENANCE_REFERENCE
        df["ingestion_timestamp"] = datetime.now().isoformat()

        out_path = os.path.join(self.processed_dir, "outbreak_signals.parquet")
        df.to_parquet(out_path, index=False)

        quality = data_quality_engine.evaluate_dataset_quality(df, "IDSP_Outbreak_Surveillance")
        logger.info(f"IDSP outbreak signals processed: {len(df)} signals saved to {out_path}")

        return {
            "status": "SUCCESS",
            "signals_count": len(df),
            "states_covered": df["canonical_state"].nunique(),
            "output_path": out_path,
            "quality": quality,
            "provenance": PROVENANCE_REFERENCE
        }

idsp_ingestor = IDSPIngestor()
