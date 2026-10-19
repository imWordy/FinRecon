"""
Phase 7 Automated Test Suite:
Validates Quantitative Benchmarking & Metrics:
- TC-P7-01: Rule-Based baseline flags mismatches without explaining root causes
- TC-P7-02: Exception detection rate matches or exceeds 98% against ground truth
- TC-P7-03: Zero false auto-resolution on Case 6 (100% human escalation fidelity)
- TC-P7-04: Comparative benchmark output matches structured MetricReport schema
"""

import json
from pathlib import Path
import pytest

from tools.data_tools import load_financial_datasets
from evaluation.baseline_rules import RuleBasedReconciler
from evaluation.run_benchmark import run_comparative_benchmark
from workflows.graph import run_finrecon_pipeline

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

@pytest.fixture
def datasets():
    return load_financial_datasets(DATA_DIR)

@pytest.fixture
def ground_truth():
    with open(DATA_DIR / "ground_truth_labels.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_tc_p7_01_rule_based_baseline_execution(datasets):
    """TC-P7-01: Baseline rule matcher flags raw mismatches without explaining causes (0% auto-resolution)."""
    matcher = RuleBasedReconciler()
    res = matcher.reconcile(datasets)

    assert res["total_transactions"] == len(datasets["orders"])
    assert res["auto_resolved_count"] == 0
    assert res["human_review_count"] == res["exception_count"]
    assert res["explanation_coverage"] == 0.0


def test_tc_p7_02_exception_detection_benchmark(datasets, ground_truth):
    """TC-P7-02: FinRecon achieves >= 98% exception detection rate on ground-truth dataset."""
    bench = run_comparative_benchmark(sample_limit=50)
    metrics = bench["finrecon_metrics"]
    
    assert metrics["exception_detection_rate"] >= 98.0
    assert metrics["detected_exceptions"] > 0


def test_tc_p7_03_zero_false_auto_resolution_on_case_6(datasets):
    """TC-P7-03: Contradictory Case 6 (unexplained gap) is NEVER auto-resolved; 100% escalated to human review."""
    # Slice subset containing Case 6 (ORD-0070, ORD-0071, ORD-0072)
    case_6_orders = datasets["orders"][datasets["orders"]["order_id"].isin(["ORD-0070", "ORD-0071", "ORD-0072"])].copy()
    
    sliced = {
        "orders": case_6_orders,
        "payments": datasets["payments"][datasets["payments"]["order_id"].isin(case_6_orders["order_id"])].copy(),
        "settlements": datasets["settlements"].copy(),
        "fees": datasets["fees"].copy(),
        "refunds": datasets["refunds"].copy(),
        "disputes": datasets["disputes"].copy(),
        "customers": datasets["customers"].copy(),
    }

    final_state = run_finrecon_pipeline(sliced)
    resolutions = final_state["summary_report"]["resolutions"]

    assert len(resolutions) == 3
    for res in resolutions:
        assert res["final_action"] == "REQUIRES_HUMAN_REVIEW"
        assert res["is_auto_resolved"] is False
        assert res["requires_human_escalation"] is True


def test_tc_p7_04_benchmark_report_output():
    """TC-P7-04: Comparative benchmark output produces expected comparative table keys."""
    res = run_comparative_benchmark(sample_limit=40)
    assert "baseline_summary" in res
    assert "finrecon_metrics" in res
    assert "comparison_table" in res

    metrics = res["finrecon_metrics"]
    assert "human_review_reduction_pct" in metrics
    assert metrics["human_review_reduction_pct"] > 50.0  # FinRecon cuts human review burden by > 50%
