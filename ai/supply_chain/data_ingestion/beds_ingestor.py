"""
DocMindX AI — Official Hospital Beds Ingestor (Rajya Sabha / Health Dynamics Layer)
Ingests:
- RS_Session_266_AU_911_C_to_D_iii.csv (State/UT-wise beds in PHC, CHC, SDH, DH, Medical College as of 31-03-2023)
- RS_Session_267_AU_287_A_to_B.csv (Central Government Tertiary Hospitals)
"""
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any
from ai.supply_chain.data_quality import data_quality_engine, PROVENANCE_OBSERVED

logger = logging.getLogger("BedsIngestor")

class BedsIngestor:
    def __init__(self):
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.rs266_path = os.path.join(workspace, "datasets", "data", "RS_Session_266_AU_911_C_to_D_iii.csv")
        self.rs267_path = os.path.join(workspace, "datasets", "data", "RS_Session_267_AU_287_A_to_B.csv")
        self.processed_dir = os.path.join(workspace, "data", "processed", "command_center")
        os.makedirs(self.processed_dir, exist_ok=True)

    def ingest(self) -> Dict[str, Any]:
        """Ingests Rajya Sabha official bed data by facility level and state/UT."""
        if not os.path.exists(self.rs266_path):
            logger.error(f"RS266 bed file not found at {self.rs266_path}")
            return {"status": "FILE_NOT_FOUND"}

        try:
            df = pd.read_csv(self.rs266_path)
        except Exception as e:
            df = pd.read_csv(self.rs266_path, encoding="latin1")

        # Standardize columns
        rename_map = {
            "State/UT": "raw_state",
            "PHC": "phc_beds",
            "CHC": "chc_beds",
            "SUB DISTRICT/ SUB DIVISIONAL HOSPITAL": "sdh_beds",
            "DISTRICT HOSPITAL": "dh_beds",
            "MEDICAL COLLEGE": "medical_college_beds",
            "Total No. of Beds": "total_beds"
        }
        df = df.rename(columns=rename_map)

        # Convert numeric columns
        num_cols = ["phc_beds", "chc_beds", "sdh_beds", "dh_beds", "medical_college_beds", "total_beds"]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0).astype(int)

        # Drop summary/total rows
        df = df[~df["raw_state"].astype(str).str.upper().str.contains("TOTAL|ALL INDIA|INDIA", na=False)]

        df["canonical_state"] = df["raw_state"].apply(data_quality_engine.normalize_state_name)
        df["source"] = "Government of India / Rajya Sabha Unstarred Question AU_911"
        df["source_period"] = "As on 31-03-2023"
        df["provenance"] = PROVENANCE_OBSERVED
        df["ingestion_timestamp"] = datetime.now().isoformat()

        out_path = os.path.join(self.processed_dir, "bed_capacity.parquet")
        df.to_parquet(out_path, index=False)

        quality = data_quality_engine.evaluate_dataset_quality(df, "Rajya_Sabha_Bed_Capacity")
        logger.info(f"Beds data processed: {len(df)} States/UTs saved to {out_path}")

        return {
            "status": "SUCCESS",
            "states_covered": len(df),
            "total_national_beds": int(df["total_beds"].sum()),
            "phc_beds_national": int(df["phc_beds"].sum()),
            "chc_beds_national": int(df["chc_beds"].sum()),
            "dh_beds_national": int(df["dh_beds"].sum()),
            "medical_college_beds_national": int(df["medical_college_beds"].sum()),
            "output_path": out_path,
            "quality": quality,
            "provenance": PROVENANCE_OBSERVED
        }

beds_ingestor = BedsIngestor()
