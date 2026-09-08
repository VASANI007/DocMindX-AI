"""
DocMindX AI — Capacity & Workforce Analytics Model
Evaluates facility bed pressure, occupancy dynamics, and staffing gaps against official IPHS 2022 benchmarks.
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ai.supply_chain.models.model_registry import model_registry

logger = logging.getLogger("CapacityModel")

class CapacityModel:
    def __init__(self):
        self.workspace_root = WORKSPACE_ROOT
        self.processed_dir = os.path.join(self.workspace_root, "data", "processed", "command_center")
        self.output_dir = os.path.join(self.workspace_root, "data", "models", "command_center", "capacity_forecasting")
        os.makedirs(self.output_dir, exist_ok=True)

    def evaluate_capacity_health(self) -> Dict[str, Any]:
        """Calculates state and facility-level bed capacity, gaps, and workforce ratios."""
        fac_path = os.path.join(self.processed_dir, "facility_master.parquet")
        iphs_path = os.path.join(self.processed_dir, "iphs_benchmarks.parquet")
        beds_path = os.path.join(self.processed_dir, "bed_capacity.parquet")

        if not os.path.exists(fac_path) or not os.path.exists(iphs_path):
            return {"status": "DATA_NOT_READY"}

        fac_df = pd.read_parquet(fac_path)
        iphs_df = pd.read_parquet(iphs_path)
        beds_df = pd.read_parquet(beds_path) if os.path.exists(beds_path) else pd.DataFrame()

        # Merge with IPHS norms
        merged = fac_df.merge(iphs_df[["facility_type", "norm_beds_min", "norm_beds_max", "norm_doctors", "norm_nurses"]], on="facility_type", how="left")

        # Dynamic calculated metrics
        merged["bed_compliance_ratio"] = merged["bed_capacity"] / merged["norm_beds_min"].clip(lower=1)
        merged["doctor_gap"] = merged["norm_doctors"] - merged["doctors_observed"]
        merged["nurse_gap"] = merged["norm_nurses"] - merged["nurses_observed"]

        total_beds = int(merged["bed_capacity"].sum())
        avg_bed_compliance = round(float(merged["bed_compliance_ratio"].mean() * 100), 2)
        total_facilities = len(merged)

        results = {
            "total_monitored_facilities": total_facilities,
            "total_national_beds": total_beds,
            "average_bed_compliance_pct": avg_bed_compliance,
            "facilities_meeting_bed_norms": int((merged["bed_compliance_ratio"] >= 1.0).sum()),
            "states_covered": int(merged["state"].nunique()),
            "districts_covered": int(merged["district"].nunique())
        }

        meta_file = os.path.join(self.output_dir, "capacity_metrics.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Register in Model Registry
        model_registry.register_model(
            model_name="ai_capacity_analyzer",
            version="2.0.0",
            task="CAPACITY_BENCHMARKING",
            target="bed_and_staff_compliance",
            algorithm="IPHS_2022_Normative_Engine",
            metrics={"bed_compliance_pct": avg_bed_compliance},
            feature_schema=["bed_capacity", "doctors_observed", "nurses_observed", "norm_beds_min", "norm_doctors", "norm_nurses"],
            artifact_path=meta_file,
            status="VALIDATED",
            training_metadata=results
        )

        return results

capacity_model = CapacityModel()

if __name__ == "__main__":
    capacity_model.evaluate_capacity_health()
