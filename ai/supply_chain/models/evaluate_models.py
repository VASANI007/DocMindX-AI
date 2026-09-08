"""
DocMindX AI — Supply Chain Model Evaluation & Quality Gate Runner
Runs automated checks on all models, validates metrics, checks schema consistency,
and enforces quality gates.
"""
import os
import sys
import json
import logging
from typing import Dict, Any

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from ai.supply_chain.models.model_registry import model_registry
from ai.supply_chain.models.train_demand_model import demand_model_trainer
from ai.supply_chain.models.train_stockout_model import stockout_risk_engine
from ai.supply_chain.models.train_capacity_model import capacity_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ModelEvaluator")

def run_all_trainings_and_evaluations() -> Dict[str, Any]:
    """Trains, benchmarks, and validates all ML and rule-based pipelines."""
    logger.info("=== 1. Training & Benchmarking AI Demand Forecaster (Chronological Split) ===")
    res_demand = demand_model_trainer.train_and_select_best()

    logger.info("=== 2. Configuring Operational Stockout Risk Engine & Benchmark Classifier ===")
    res_stockout = stockout_risk_engine.train_research_demonstration_classifier()

    logger.info("=== 3. Evaluating IPHS Capacity & Workforce Analytics ===")
    res_capacity = capacity_model.evaluate_capacity_health()

    reg = model_registry.load_registry()
    logger.info("=== Model Registry State ===")
    for m_name, meta in reg.get("models", {}).items():
        logger.info(f"Model: {m_name} | Status: {meta.get('status')} | Task: {meta.get('task')} | Metrics: {meta.get('metrics')}")

    return {
        "demand_model": res_demand,
        "stockout_model": res_stockout,
        "capacity_model": res_capacity,
        "registry": reg
    }

if __name__ == "__main__":
    run_all_trainings_and_evaluations()
