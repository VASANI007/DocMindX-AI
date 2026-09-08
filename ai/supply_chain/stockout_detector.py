"""
DocMindX AI — Early Warning Stockout & Health Resource Risk Detector
Scans public health network for imminent stock exhaustion, capacity bottlenecks, and outbreak signals.
All alerts derived from official data and deterministic operational risk engine.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ai.supply_chain.phc_data_engine import data_engine, NLEM_FORMULARY
from ai.supply_chain.data_quality import PROVENANCE_DERIVED, PROVENANCE_OBSERVED, PROVENANCE_OPERATIONAL_RULE
from ai.supply_chain.models.train_stockout_model import stockout_risk_engine

logger = logging.getLogger("StockoutDetector")

class StockoutDetector:
    def __init__(self):
        pass

    def scan_network_alerts(self, state: str = "All India", district: str = "All Districts",
                            scenario_key: str = "baseline") -> Dict[str, Any]:
        """
        Scans all monitored facilities and generates prioritized early warning alerts using operational rules.
        """
        facilities = data_engine.get_facilities(state=state, district=district, scenario_key=scenario_key)
        
        critical_alerts = []
        warning_alerts = []

        for fac in facilities:
            fac_id = fac["id"]
            fac_name = fac["name"]
            st = fac["state"]
            dist = fac["district"]

            # 1. Medicine Stockout Check via Operational Risk Engine
            for med_id, inv in fac["inventory"].items():
                days_left = inv["days_remaining"]
                stock = inv["stock"]
                burn = inv["adjusted_daily_burn"]

                risk_eval = stockout_risk_engine.evaluate_operational_risk(
                    days_of_inventory=days_left,
                    reorder_lead_time_days=7.0,
                    outbreak_signal_severity=1 if scenario_key != "baseline" else 0
                )

                if risk_eval["risk_level"] == "CRITICAL":
                    critical_alerts.append({
                        "facility_id": fac_id,
                        "facility_name": fac_name,
                        "state": st,
                        "district": dist,
                        "type": "MEDICINE_STOCKOUT",
                        "severity": "CRITICAL",
                        "indicator": f"Critical Shortage: {inv['name']}",
                        "medicine_id": med_id,
                        "medicine_name": inv["name"],
                        "observed_value": f"{stock} {inv['unit']} ({days_left} days remaining)",
                        "threshold": "Minimum 3.0 days emergency buffer",
                        "risk_level": "CRITICAL",
                        "data_date": datetime.now().strftime("%Y-%m-%d"),
                        "source": "Operational Risk Rule Engine",
                        "provenance": PROVENANCE_OPERATIONAL_RULE,
                        "recommended_action": f"Recommend cross-district redistribution request for {inv['name']}."
                    })
                elif risk_eval["risk_level"] == "HIGH":
                    warning_alerts.append({
                        "facility_id": fac_id,
                        "facility_name": fac_name,
                        "state": st,
                        "district": dist,
                        "type": "MEDICINE_WARNING",
                        "severity": "WARNING",
                        "indicator": f"Low Stock Warning: {inv['name']}",
                        "medicine_id": med_id,
                        "medicine_name": inv["name"],
                        "observed_value": f"{stock} {inv['unit']} ({days_left} days remaining)",
                        "threshold": "7.0 days reorder threshold",
                        "risk_level": "HIGH",
                        "data_date": datetime.now().strftime("%Y-%m-%d"),
                        "source": "Operational Risk Rule Engine",
                        "provenance": PROVENANCE_OPERATIONAL_RULE,
                        "recommended_action": f"Queue replenishment batch in next routine procurement cycle."
                    })

            # 2. Capacity & Workforce Alerts
            if fac["type"] == "DH" and fac["bed_capacity"] < 100:
                warning_alerts.append({
                    "facility_id": fac_id,
                    "facility_name": fac_name,
                    "state": st,
                    "district": dist,
                    "type": "BED_CAPACITY",
                    "severity": "WARNING",
                    "indicator": "Bed Capacity Below IPHS Standard",
                    "observed_value": f"{fac['bed_capacity']} Beds",
                    "threshold": "IPHS DH Norm: 100-500 Beds",
                    "risk_level": "MODERATE",
                    "data_date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "Rajya Sabha Beds / IPHS 2022 Norms",
                    "provenance": PROVENANCE_DERIVED,
                    "recommended_action": "Infrastructure augmentation planning under NHM/EAP grants."
                })

            # 3. Personnel Attendance & Workforce Check via Attendance Engine
            from ai.supply_chain.attendance_engine import attendance_engine
            att_record = attendance_engine.compute_daily_attendance(fac, scenario_key=scenario_key)
            att_pct = att_record["attendance_pct"]
            if att_record["status"] == "CRITICAL":
                critical_alerts.append({
                    "facility_id": fac_id,
                    "facility_name": fac_name,
                    "state": st,
                    "district": dist,
                    "type": "STAFF_ATTENDANCE",
                    "severity": "CRITICAL",
                    "indicator": f"Critical Staff Deficit ({att_pct}%)",
                    "observed_value": f"{att_record['present_total']} / {att_record['sanctioned_total']} Staff Present ({att_pct}%)",
                    "threshold": "Minimum 60.0% operational attendance norm",
                    "risk_level": "CRITICAL",
                    "data_date": att_record["date"],
                    "source": "Attendance & Workforce Telemetry Engine",
                    "provenance": att_record["provenance"],
                    "recommended_action": f"Immediate deployment of mobile medical team or doctor rotation to {fac_name}."
                })
            elif att_record["status"] == "WARNING":
                warning_alerts.append({
                    "facility_id": fac_id,
                    "facility_name": fac_name,
                    "state": st,
                    "district": dist,
                    "type": "STAFF_ATTENDANCE",
                    "severity": "WARNING",
                    "indicator": f"Staff Attendance Warning ({att_pct}%)",
                    "observed_value": f"{att_record['present_total']} / {att_record['sanctioned_total']} Staff Present ({att_pct}%)",
                    "threshold": "Standard 75.0% staff presence norm",
                    "risk_level": "HIGH",
                    "data_date": att_record["date"],
                    "source": "Attendance & Workforce Telemetry Engine",
                    "provenance": att_record["provenance"],
                    "recommended_action": f"Review staff leave roaster and arrange local coverage across {dist} district cluster."
                })

        total_facs = len(facilities)
        supply_health = max(50.0, round(100.0 - ((len(critical_alerts) * 2.0 + len(warning_alerts) * 0.5) / max(1, total_facs) * 100), 1))
        supply_health = min(99.0, supply_health)

        return {
            "total_monitored_facilities": total_facs,
            "supply_health_pct": supply_health,
            "total_critical_count": len(critical_alerts),
            "total_warning_count": len(warning_alerts),
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "alerts": critical_alerts + warning_alerts,
            "scan_timestamp": datetime.now().isoformat()
        }

stockout_detector = StockoutDetector()
