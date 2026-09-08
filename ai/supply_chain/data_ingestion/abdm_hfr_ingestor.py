"""
DocMindX AI — ABDM (Ayushman Bharat Digital Mission) / HFR Ingestor
Ingests official ABDM Facility & Healthcare Professionals taxonomy registry.
"""
import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from ai.supply_chain.data_quality import data_quality_engine, PROVENANCE_OBSERVED

logger = logging.getLogger("ABDMHFRIngestor")

class ABDMHFRIngestor:
    def __init__(self):
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.prod_path = os.path.join(workspace, "datasets", "data", "Master_Data_Production_1_5c34b971ee.xlsx")
        self.sandbox_path = os.path.join(workspace, "datasets", "data", "Master_Data_Sandbox_69b717ca39.xlsx")
        self.processed_dir = os.path.join(workspace, "data", "processed", "command_center")
        os.makedirs(self.processed_dir, exist_ok=True)

    def ingest(self) -> Dict[str, Any]:
        """Ingests official ABDM Facility & Workforce taxonomy layers."""
        path_to_use = self.prod_path if os.path.exists(self.prod_path) else self.sandbox_path
        if not os.path.exists(path_to_use):
            logger.warning(f"ABDM taxonomy file not found at {path_to_use}")
            return {"status": "FILE_NOT_FOUND"}

        try:
            xl = pd.ExcelFile(path_to_use)
            specialities = xl.parse("Doctor Specialities").dropna() if "Doctor Specialities" in xl.sheet_names else pd.DataFrame()
            fac_types = xl.parse("Facility Type").dropna() if "Facility Type" in xl.sheet_names else pd.DataFrame()
            nurse_cats = xl.parse("Nurse Categories").dropna() if "Nurse Categories" in xl.sheet_names else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error reading ABDM Excel: {e}")
            return {"status": "READ_ERROR", "error": str(e)}

        out_path = os.path.join(self.processed_dir, "abdm_taxonomy.parquet")
        combined_meta = {
            "specialities_count": len(specialities),
            "facility_types_count": len(fac_types),
            "nurse_categories_count": len(nurse_cats),
            "source": "National Health Authority (NHA) / ABDM Master Data Registry",
            "provenance": PROVENANCE_OBSERVED,
            "ingestion_timestamp": datetime.now().isoformat()
        }

        # Save summary
        summary_df = pd.DataFrame([combined_meta])
        summary_df.to_parquet(out_path, index=False)

        return {
            "status": "SUCCESS",
            "specialities": len(specialities),
            "facility_types": len(fac_types),
            "output_path": out_path,
            "provenance": PROVENANCE_OBSERVED
        }

abdm_hfr_ingestor = ABDMHFRIngestor()
