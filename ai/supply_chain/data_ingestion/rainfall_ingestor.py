"""
DocMindX AI — IMD (India Meteorological Department) Rainfall & Seasonality Ingestor
Ingests official subdivision historical rainfall data to calculate monsoon & environmental features.
"""
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any
from ai.supply_chain.data_quality import data_quality_engine, PROVENANCE_OBSERVED

logger = logging.getLogger("RainfallIngestor")

# Mapping IMD Subdivisions to States
SUBDIVISION_TO_STATE = {
    "ANDAMAN & NICOBAR ISLANDS": "Andaman and Nicobar Islands",
    "ARUNACHAL PRADESH": "Arunachal Pradesh",
    "ASSAM & MEGHALAYA": "Assam",
    "NAGA MANI MIZO TRIPURA": "Tripura",
    "SUB HIMALAYAN WEST BENGAL & SIKKIM": "West Bengal",
    "GANGETIC WEST BENGAL": "West Bengal",
    "ORISSA": "Odisha",
    "JHARKHAND": "Jharkhand",
    "BIHAR": "Bihar",
    "EAST UTTAR PRADESH": "Uttar Pradesh",
    "WEST UTTAR PRADESH": "Uttar Pradesh",
    "UTTARAKHAND": "Uttarakhand",
    "HARYANA DELHI & CHANDIGARH": "Haryana",
    "PUNJAB": "Punjab",
    "HIMACHAL PRADESH": "Himachal Pradesh",
    "JAMMU & KASHMIR": "Jammu and Kashmir",
    "WEST RAJASTHAN": "Rajasthan",
    "EAST RAJASTHAN": "Rajasthan",
    "WEST MADHYA PRADESH": "Madhya Pradesh",
    "EAST MADHYA PRADESH": "Madhya Pradesh",
    "GUJARAT REGION": "Gujarat",
    "SAURASHTRA & KUTCH": "Gujarat",
    "KONKAN & GOA": "Maharashtra",
    "MADHYA MAHARASHTRA": "Maharashtra",
    "MATATHWADA": "Maharashtra",
    "VIDARBHA": "Maharashtra",
    "CHHATTISGARH": "Chhattisgarh",
    "COASTAL ANDHRA PRADESH": "Andhra Pradesh",
    "TELANGANA": "Telangana",
    "RAYALSEEMA": "Andhra Pradesh",
    "TAMIL NADU": "Tamil Nadu",
    "COASTAL KARNATAKA": "Karnataka",
    "NORTH INTERIOR KARNATAKA": "Karnataka",
    "SOUTH INTERIOR KARNATAKA": "Karnataka",
    "KERALA": "Kerala",
    "LAKSHADWEEP": "Lakshadweep"
}

class RainfallIngestor:
    def __init__(self):
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.raw_path = os.path.join(workspace, "datasets", "data", "Sub_Division_IMD_2017.csv")
        self.processed_dir = os.path.join(workspace, "data", "processed", "command_center")
        os.makedirs(self.processed_dir, exist_ok=True)

    def ingest(self) -> Dict[str, Any]:
        """Ingests IMD subdivision monthly rainfall datasets."""
        if not os.path.exists(self.raw_path):
            logger.error(f"IMD rainfall file not found at {self.raw_path}")
            return {"status": "FILE_NOT_FOUND"}

        try:
            df = pd.read_csv(self.raw_path)
        except Exception:
            df = pd.read_csv(self.raw_path, encoding="latin1")

        df["canonical_state"] = df["SUBDIVISION"].map(SUBDIVISION_TO_STATE).fillna(df["SUBDIVISION"].apply(data_quality_engine.normalize_state_name))

        # Calculate 30-year climatological monthly averages (1981-2017)
        modern_df = df[df["YEAR"] >= 1980]
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        
        state_rain = modern_df.groupby("canonical_state")[months + ["ANNUAL", "JJAS"]].mean().reset_index()
        state_rain["source"] = "India Meteorological Department (IMD) / Hydromet Subdivision Series"
        state_rain["provenance"] = PROVENANCE_OBSERVED
        state_rain["ingestion_timestamp"] = datetime.now().isoformat()

        out_path = os.path.join(self.processed_dir, "rainfall_features.parquet")
        state_rain.to_parquet(out_path, index=False)

        quality = data_quality_engine.evaluate_dataset_quality(state_rain, "IMD_Historical_Rainfall")
        logger.info(f"Rainfall data processed: {len(state_rain)} state climates saved to {out_path}")

        return {
            "status": "SUCCESS",
            "states_covered": len(state_rain),
            "output_path": out_path,
            "quality": quality,
            "provenance": PROVENANCE_OBSERVED
        }

rainfall_ingestor = RainfallIngestor()
