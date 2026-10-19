"""
Quantitative Evaluation Metrics for FinRecon.
Implements the 7 core metrics outlined in Section 40 of FinRecon Deep Dive:
1. Reconciliation Accuracy
2. Exception Detection Rate
3. Resolution Accuracy
4. Human Escalation Accuracy
5. Tool Efficiency
6. Latency Profiling
7. Comparative Baseline Gain
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class MetricReport(BaseModel):
    total_transactions: int
    ground_truth_exceptions: int
    detected_exceptions: int
    reconciliation_accuracy: float
    exception_detection_rate: float
    resolution_accuracy: float
    human_escalation_accuracy: float
    tool_efficiency_score: float
    latency_seconds: float
    human_review_reduction_pct: float


def compute_evaluation_metrics(
    pipeline_state: Dict[str, Any],
    ground_truth_labels: List[Dict[str, Any]],
    elapsed_time_seconds: float
) -> MetricReport:
    """Computes comprehensive quantitative performance scores for FinRecon."""
    all_recs = pipeline_state.get("all_records", [])
    exceptions = pipeline_state.get("exceptions", [])
    resolutions = pipeline_state.get("resolutions", [])
    audit_log = pipeline_state.get("audit_log", [])

    total_txns = len(all_recs)
    gt_exceptions_count = len(ground_truth_labels)
    detected_exceptions_count = len(exceptions)

    # 1. Reconciliation Accuracy
    matched_count = total_txns - detected_exceptions_count
    recon_accuracy = round((matched_count / max(1, total_txns)) * 100, 2)

    # 2. Exception Detection Rate
    # Compare with ground truth exception IDs
    gt_order_ids = set(item["order_id"] for item in ground_truth_labels if item["category"] != "MATCHED")
    detected_order_ids = set(e["record"]["order_id"] for e in exceptions)
    
    true_positives = len(gt_order_ids.intersection(detected_order_ids))
    actual_positives = len(gt_order_ids)
    detection_rate = round((true_positives / max(1, actual_positives)) * 100, 2)

    # 3. Resolution Accuracy & 4. Human Escalation Accuracy
    # Map resolutions by order_id
    res_by_order = {r["order_id"]: r for r in resolutions}
    correct_resolutions = 0
    correct_escalations = 0
    total_ambiguous_cases = 0

    for gt in ground_truth_labels:
        oid = gt["order_id"]
        exp_res = gt.get("expected_resolution")
        res = res_by_order.get(oid)
        if not res:
            continue

        actual_action = res.get("final_action")
        if actual_action == exp_res:
            correct_resolutions += 1

        # Check specifically for cases that require human escalation
        if exp_res == "REQUIRES_HUMAN_REVIEW":
            total_ambiguous_cases += 1
            if res.get("requires_human_escalation") is True:
                correct_escalations += 1

    total_evaluated_cases = max(1, len(ground_truth_labels))
    resolution_accuracy = round((correct_resolutions / total_evaluated_cases) * 100, 2)
    human_escalation_accuracy = round((correct_escalations / max(1, total_ambiguous_cases)) * 100, 2)

    # 5. Tool Efficiency
    tool_events = sum(1 for e in audit_log if e.get("action") in [
        "PLAN_GENERATED", "DATA_VALIDATED", "MATCHING_COMPLETE",
        "EXCEPTION_INVESTIGATED", "CRITIC_VERDICT", "RESOLUTION_ROUTED"
    ])
    tool_efficiency = round(tool_events / max(1, detected_exceptions_count), 2)

    # Human review workload reduction
    # Conventional rule matcher escalates 100% of exceptions
    # FinRecon auto-resolves valid fees, cutting human review burden
    auto_resolved = sum(1 for r in resolutions if r.get("is_auto_resolved", False))
    reduction_pct = round((auto_resolved / max(1, detected_exceptions_count)) * 100, 2)

    return MetricReport(
        total_transactions=total_txns,
        ground_truth_exceptions=gt_exceptions_count,
        detected_exceptions=detected_exceptions_count,
        reconciliation_accuracy=recon_accuracy,
        exception_detection_rate=detection_rate,
        resolution_accuracy=resolution_accuracy,
        human_escalation_accuracy=human_escalation_accuracy,
        tool_efficiency_score=tool_efficiency,
        latency_seconds=round(elapsed_time_seconds, 2),
        human_review_reduction_pct=reduction_pct
    )
