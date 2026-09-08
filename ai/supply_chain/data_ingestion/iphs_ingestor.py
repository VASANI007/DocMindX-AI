"""
DocMindX AI — IPHS 2022 (Indian Public Health Standards) Reference Norms Ingestor
Structures facility hierarchy standards, minimum bed requirements, staffing norms, and service benchmarks.
"""
import os
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from ai.supply_chain.data_quality import data_quality_engine, PROVENANCE_REFERENCE

logger = logging.getLogger("IPHSIngestor")

# Official IPHS 2022 Benchmarks across facility types
IPHS_FACILITY_NORMS = [
    {
        "facility_type": "SHC/HWC",
        "name_full": "Sub Health Centre - Health and Wellness Centre",
        "level_of_care": "Primary",
        "norm_beds_min": 0,
        "norm_beds_max": 2,
        "norm_doctors": 0,
        "norm_nurses": 1, # CHO / ANM
        "norm_pharmacists": 0,
        "essential_drugs_count": 105,
        "essential_diagnostics_count": 14,
        "population_norm_plains": 5000,
        "population_norm_tribal": 3000
    },
    {
        "facility_type": "PHC",
        "name_full": "Primary Health Centre",
        "level_of_care": "Primary",
        "norm_beds_min": 6,
        "norm_beds_max": 10,
        "norm_doctors": 2, # 1 MO + 1 AYUSH
        "norm_nurses": 4,
        "norm_pharmacists": 1,
        "essential_drugs_count": 172,
        "essential_diagnostics_count": 63,
        "population_norm_plains": 30000,
        "population_norm_tribal": 20000
    },
    {
        "facility_type": "UPHC",
        "name_full": "Urban Primary Health Centre",
        "level_of_care": "Primary (Urban)",
        "norm_beds_min": 0,
        "norm_beds_max": 6,
        "norm_doctors": 2,
        "norm_nurses": 4,
        "norm_pharmacists": 1,
        "essential_drugs_count": 172,
        "essential_diagnostics_count": 63,
        "population_norm_plains": 50000,
        "population_norm_tribal": 50000
    },
    {
        "facility_type": "CHC",
        "name_full": "Community Health Centre",
        "level_of_care": "Secondary (First Referral Unit)",
        "norm_beds_min": 30,
        "norm_beds_max": 50,
        "norm_doctors": 7, # 4 specialists + 3 MOs
        "norm_nurses": 10,
        "norm_pharmacists": 2,
        "essential_drugs_count": 298,
        "essential_diagnostics_count": 99,
        "population_norm_plains": 120000,
        "population_norm_tribal": 80000
    },
    {
        "facility_type": "SDH",
        "name_full": "Sub-District / Sub-Divisional Hospital",
        "level_of_care": "Secondary",
        "norm_beds_min": 50,
        "norm_beds_max": 100,
        "norm_doctors": 18,
        "norm_nurses": 30,
        "norm_pharmacists": 4,
        "essential_drugs_count": 350,
        "essential_diagnostics_count": 120,
        "population_norm_plains": 250000,
        "population_norm_tribal": 250000
    },
    {
        "facility_type": "DH",
        "name_full": "District Hospital",
        "level_of_care": "Secondary / Tertiary Referral",
        "norm_beds_min": 100,
        "norm_beds_max": 500,
        "norm_doctors": 45,
        "norm_nurses": 90,
        "norm_pharmacists": 8,
        "essential_drugs_count": 450,
        "essential_diagnostics_count": 150,
        "population_norm_plains": 1000000,
        "population_norm_tribal": 1000000
    },
    {
        "facility_type": "Medical College",
        "name_full": "Tertiary Medical College & Hospital",
        "level_of_care": "Tertiary / Super-Speciality",
        "norm_beds_min": 500,
        "norm_beds_max": 2000,
        "norm_doctors": 150,
        "norm_nurses": 350,
        "norm_pharmacists": 20,
        "essential_drugs_count": 600,
        "essential_diagnostics_count": 250,
        "population_norm_plains": 3000000,
        "population_norm_tribal": 3000000
    }
]

class IPHSIngestor:
    def __init__(self):
        workspace = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.processed_dir = os.path.join(workspace, "data", "processed", "command_center")
        os.makedirs(self.processed_dir, exist_ok=True)

    def ingest(self) -> Dict[str, Any]:
        """Creates canonical IPHS 2022 standards dataset."""
        df = pd.DataFrame(IPHS_FACILITY_NORMS)
        df["standards_year"] = 2022
        df["source"] = "Ministry of Health & Family Welfare — Indian Public Health Standards (IPHS) 2022 Guidelines"
        df["provenance"] = PROVENANCE_REFERENCE
        df["ingestion_timestamp"] = datetime.now().isoformat()

        out_path = os.path.join(self.processed_dir, "iphs_benchmarks.parquet")
        df.to_parquet(out_path, index=False)

        quality = data_quality_engine.evaluate_dataset_quality(df, "IPHS_2022_Norms")
        logger.info(f"IPHS 2022 benchmarks processed: {len(df)} facility levels saved to {out_path}")

        return {
            "status": "SUCCESS",
            "facility_types_standardized": len(df),
            "output_path": out_path,
            "quality": quality,
            "provenance": PROVENANCE_REFERENCE
        }

iphs_ingestor = IPHSIngestor()
