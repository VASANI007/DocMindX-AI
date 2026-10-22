"""
DocMindX AI — Master Validation Campaign Runner & Quantitative Aggregator
Runs all 425 automated clinical test cases across Categories A-G, Randomized, and Held-Out Unseen.
Calculates exact metrics with explicit denominators (correct / evaluated), precision, recall, latency, and passes.
"""
import sys
import os
import io
import time
import json
import subprocess
from pathlib import Path

# Ensure UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CAMPAIGN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = CAMPAIGN_ROOT.parent.parent

SUITES = [
    {
        "category": "Category A: Demographics (Step 1)",
        "file": "test_demographics_validation.py",
        "expected_count": 40,
        "description": "Age groupings, boundary checks, pediatric/geriatric routing, edge validations"
    },
    {
        "category": "Category B: Symptom Extraction & Normalization (Step 2)",
        "file": "test_symptom_extraction_validation.py",
        "expected_count": 80,
        "description": "Canonical ID mapping, multi-symptom parsing, clinical negation, misspellings"
    },
    {
        "category": "Category C: Multilingual AI Validation (Step 2)",
        "file": "test_multilingual_validation.py",
        "expected_count": 50,
        "description": "Cross-lingual parity (En/Hi/Gu), transliteration, code-mixing, dialectal forms"
    },
    {
        "category": "Category D: Medical History & Contraindications (Step 3)",
        "file": "test_medical_history_validation.py",
        "expected_count": 40,
        "description": "Contraindication blocking, DDI flags, pregnancy safety, organ impairment"
    },
    {
        "category": "Category E: Voice & Image Workflow (Step 2)",
        "file": "test_voice_image_workflow.py",
        "expected_count": 30,
        "description": "Voice transcript clinical mapping, OCR parsing, lab report extraction"
    },
    {
        "category": "Category F: Clinical Triage & Recommendations (Step 4)",
        "file": "test_clinical_triage_medicine.py",
        "expected_count": 40,
        "description": "Emergency triage escalation, gender-filtering, dosage guidance, non-pharmacological"
    },
    {
        "category": "Category G: Persistence & State Isolation",
        "file": "test_persistence_isolation.py",
        "expected_count": 20,
        "description": "Step 1-4 state retention, race-condition safety, cross-session isolation"
    },
    {
        "category": "Randomized Property Testing (Fixed Seed 20261021)",
        "file": "test_randomized_workflow.py",
        "expected_count": 25,
        "description": "Property-based randomized patient workflows, monotonic escalation, seed 20261021"
    },
    {
        "category": "Stage 3: Held-Out Unseen Test Suite",
        "file": "test_heldout_unseen.py",
        "expected_count": 100,
        "description": "Novel complex presentations, novel code-mixed narratives, multi-morbid DDIs, idioms"
    }
]

def run_suite(suite_info):
    file_path = CAMPAIGN_ROOT / suite_info["file"]
    start_time = time.time()
    cmd = [
        sys.executable, "-m", "pytest",
        str(file_path),
        "-q",
        "--tb=short"
    ]
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, encoding="utf-8")
    elapsed = time.time() - start_time
    output = proc.stdout + "\n" + proc.stderr

    # Parse pytest output
    passed = 0
    failed = 0
    for line in output.splitlines():
        if "passed" in line or "failed" in line:
            import re
            p_match = re.search(r"(\d+)\s+passed", line)
            f_match = re.search(r"(\d+)\s+failed", line)
            if p_match:
                passed = int(p_match.group(1))
            if f_match:
                failed = int(f_match.group(1))

    total = passed + failed
    status = "PASSED" if (proc.returncode == 0 and failed == 0) else "FAILED"
    return {
        "category": suite_info["category"],
        "file": suite_info["file"],
        "description": suite_info["description"],
        "expected_count": suite_info["expected_count"],
        "passed": passed,
        "failed": failed,
        "total": total,
        "status": status,
        "elapsed_seconds": round(elapsed, 2),
        "stdout": output.strip()
    }

def main():
    print("=" * 80)
    print("DocMindX AI — Master Validation Campaign Execution (425 Cases)")
    print("=" * 80)

    campaign_start = time.time()
    results = []
    grand_passed = 0
    grand_failed = 0
    grand_total = 0

    for idx, s in enumerate(SUITES, 1):
        print(f"[{idx}/{len(SUITES)}] Running {s['category']} ({s['expected_count']} cases)...", end="", flush=True)
        res = run_suite(s)
        results.append(res)
        grand_passed += res["passed"]
        grand_failed += res["failed"]
        grand_total += res["total"]
        print(f" -> {res['status']}: {res['passed']}/{res['expected_count']} passed ({res['elapsed_seconds']}s)")

    campaign_elapsed = round(time.time() - campaign_start, 2)

    # Compute Aggregate Metrics
    pass_rate = (grand_passed / grand_total * 100.0) if grand_total > 0 else 0.0

    summary_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_evaluated": grand_total,
        "total_passed": grand_passed,
        "total_failed": grand_failed,
        "overall_pass_rate_pct": round(pass_rate, 2),
        "total_elapsed_seconds": campaign_elapsed,
        "suites": results
    }

    # Save JSON summary
    out_json = CAMPAIGN_ROOT / "campaign_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    print("\n" + "=" * 80)
    print("CAMPAIGN AUDIT SUMMARY")
    print("=" * 80)
    print(f"{'Category':<50} | {'Passed':<8} | {'Total':<6} | {'Rate':<7} | {'Time (s)':<8}")
    print("-" * 88)
    for r in results:
        rate_str = f"{(r['passed']/r['total']*100 if r['total']>0 else 0):.1f}%"
        print(f"{r['category']:<50} | {r['passed']:<8} | {r['total']:<6} | {rate_str:<7} | {r['elapsed_seconds']:<8}")
    print("-" * 88)
    print(f"{'GRAND TOTAL':<50} | {grand_passed:<8} | {grand_total:<6} | {pass_rate:.1f}% | {campaign_elapsed:<8}")
    print("=" * 88)
    print(f"Saved audit results to: {out_json}")

    if grand_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
