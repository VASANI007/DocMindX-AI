"""
DocMindX AI — NFHS-5 (National Family Health Survey 5) District Ingestor
Ingests official NFHS-5 district demographic and health indicators (2019-21).
"""
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any
from ai.supply_chain.data_quality import data_quality_engine, PROVENANCE_OBSERVED

logger = logging.getLogger("NFHSIngestor")

class NFHSIngestor:
    def __init__(self):
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.raw_path = os.path.join(workspace, "datasets", "data", "datafile.csv")
        self.processed_dir = os.path.join(workspace, "data", "processed", "command_center")
        os.makedirs(self.processed_dir, exist_ok=True)

    def ingest(self) -> Dict[str, Any]:
        """Ingests NFHS-5 district indicators."""
        if not os.path.exists(self.raw_path):
            logger.error(f"NFHS-5 file not found at {self.raw_path}")
            return {"status": "FILE_NOT_FOUND"}

        try:
            df = pd.read_csv(self.raw_path)
        except Exception:
            df = pd.read_csv(self.raw_path, encoding="latin1")

        # Normalize state and district
        state_col = "State/UT" if "State/UT" in df.columns else df.columns[1]
        dist_col = "District Names" if "District Names" in df.columns else df.columns[0]

        df["canonical_state"] = df[state_col].apply(data_quality_engine.normalize_state_name)
        df["canonical_district"] = df[dist_col].apply(data_quality_engine.normalize_district_name)
        df["geo_key"] = df.apply(lambda r: data_quality_engine.build_geo_key(r["canonical_state"], r["canonical_district"]), axis=1)

        # Ensure numeric columns are cleaned
        skip_cols = [state_col, dist_col, "canonical_state", "canonical_district", "geo_key"]
        for col in df.columns:
            if col not in skip_cols:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.strip(), errors="coerce").fillna(0)

        df["source"] = "MoHFW / IIPS — National Family Health Survey (NFHS-5) 2019-21"
        df["provenance"] = PROVENANCE_OBSERVED
        df["ingestion_timestamp"] = datetime.now().isoformat()

        out_path = os.path.join(self.processed_dir, "nfhs5_district_indicators.parquet")
        df.to_parquet(out_path, index=False)

        quality = data_quality_engine.evaluate_dataset_quality(df, "NFHS5_District_Health")
        logger.info(f"NFHS-5 data processed: {len(df)} districts saved to {out_path}")

        return {
            "status": "SUCCESS",
            "districts_covered": len(df),
            "states_covered": df["canonical_state"].nunique(),
            "indicator_features": len(df.columns) - len(skip_cols),
            "output_path": out_path,
            "quality": quality,
            "provenance": PROVENANCE_OBSERVED
        }

nfhs_ingestor = NFHSIngestor()
