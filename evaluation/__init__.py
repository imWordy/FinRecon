"""
Evaluation package initialization for FinRecon.
Exposes RuleBasedReconciler, MetricReport, compute_evaluation_metrics, and run_comparative_benchmark.
"""

from evaluation.baseline_rules import RuleBasedReconciler
from evaluation.metrics import MetricReport, compute_evaluation_metrics
from evaluation.run_benchmark import run_comparative_benchmark

__all__ = [
    "RuleBasedReconciler",
    "MetricReport",
    "compute_evaluation_metrics",
    "run_comparative_benchmark"
]
