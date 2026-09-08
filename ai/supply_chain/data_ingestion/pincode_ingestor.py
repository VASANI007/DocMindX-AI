"""
DocMindX AI — India Pincode Directory & Geographic Geocoding Ingestor
Ingests official postal geography dataset and aggregates canonical district & facility coordinates.
"""
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Tuple
from ai.supply_chain.data_quality import data_quality_engine, CANONICAL_STATES_AND_UTS, PROVENANCE_OBSERVED

logger = logging.getLogger("PincodeIngestor")

class PincodeIngestor:
    def __init__(self, raw_path: str = None):
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.raw_path = raw_path or os.path.join(workspace, "datasets", "data", "(pincode)5c2f62fe-5afa-4119-a499-fec9d604d5bd.csv")
        self.processed_dir = os.path.join(workspace, "data", "processed", "command_center")
        os.makedirs(self.processed_dir, exist_ok=True)

    def ingest(self) -> Dict[str, Any]:
        """Loads and processes the India Pincode Directory."""
        if not os.path.exists(self.raw_path):
            logger.error(f"Pincode file not found at {self.raw_path}")
            return {"status": "FILE_NOT_FOUND", "records": 0}

        logger.info(f"Ingesting India Pincode Directory from {self.raw_path}...")
        try:
            df = pd.read_csv(
                self.raw_path,
                usecols=["officename", "pincode", "district", "statename", "latitude", "longitude"],
                low_memory=False
            )
        except Exception as e:
            logger.error(f"Error reading pincode CSV: {e}")
            return {"status": "READ_ERROR", "error": str(e)}

        # Clean coordinates
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df = df.dropna(subset=["statename", "district", "latitude", "longitude"])
        # Filter valid India bounding box (approx lat 6-38, lon 68-98)
        df = df[(df["latitude"] >= 6.0) & (df["latitude"] <= 38.5) & (df["longitude"] >= 68.0) & (df["longitude"] <= 98.0)]

        # Normalize state and district
        df["canonical_state"] = df["statename"].apply(data_quality_engine.normalize_state_name)
        df["canonical_district"] = df["district"].apply(data_quality_engine.normalize_district_name)
        df["geo_key"] = df.apply(lambda r: data_quality_engine.build_geo_key(r["canonical_state"], r["canonical_district"]), axis=1)

        # Compute District centroids
        district_centroids = df.groupby(["canonical_state", "canonical_district", "geo_key"]).agg(
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
            pincode_count=("pincode", "nunique"),
            sample_pincode=("pincode", "first")
        ).reset_index()

        out_path = os.path.join(self.processed_dir, "geography_master.parquet")
        district_centroids.to_parquet(out_path, index=False)

        quality = data_quality_engine.evaluate_dataset_quality(district_centroids, "India_Pincode_Geography")
        logger.info(f"Pincode ingestion complete: {len(district_centroids)} canonical districts stored in {out_path}")

        return {
            "status": "SUCCESS",
            "total_pincodes_parsed": len(df),
            "canonical_districts": len(district_centroids),
            "canonical_states": district_centroids["canonical_state"].nunique(),
            "output_path": out_path,
            "quality": quality,
            "provenance": PROVENANCE_OBSERVED,
            "source_name": "Department of Posts, Govt of India / Pincode Directory"
        }

pincode_ingestor = PincodeIngestor()
