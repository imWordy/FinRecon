"""
Workflow State Definition for FinRecon.
TypedDict defining the shared state across all agent and deterministic nodes.
"""

from typing import TypedDict, List, Dict, Any, Optional


class FinReconState(TypedDict, total=False):
    # User Request & High-Level Plan
    user_request: str
    task_plan: Dict[str, Any]
    
    # Input Datasets & Validation
    datasets: Dict[str, Any]
    validation_report: Dict[str, Any]
    
    # Reconciliation Results
    all_records: List[Dict[str, Any]]
    exceptions: List[Dict[str, Any]]
    
    # Current Exception Processing Queue
    current_exception_idx: int
    current_exception: Optional[Dict[str, Any]]
    
    # Investigation & Reasoning Artifacts
    current_hypothesis: Optional[Dict[str, Any]]
    current_critic_verdict: Optional[Dict[str, Any]]
    
    # Final Cumulative Resolutions
    resolutions: List[Dict[str, Any]]
    summary_report: Dict[str, Any]
    
    # Tamper-evident Audit Trail
    audit_log: List[Dict[str, Any]]
