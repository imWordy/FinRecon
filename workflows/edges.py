"""
Conditional Routing Edges for FinRecon LangGraph Workflow.
Directs state machine flow based on exception counts, critique verdicts,
and queue progression.
"""

from typing import Literal
from workflows.state import FinReconState


def route_after_reconciliation(state: FinReconState) -> Literal["investigate", "report"]:
    """
    If exceptions were detected during reconciliation, proceed to investigation;
    otherwise transition directly to final report.
    """
    exceptions = state.get("exceptions", [])
    if len(exceptions) > 0:
        return "investigate"
    return "report"


def route_after_resolution(state: FinReconState) -> Literal["investigate", "report"]:
    """
    Checks if there are remaining exceptions in the queue.
    If yes, loop back to investigate; otherwise generate final summary report.
    """
    idx = state.get("current_exception_idx", 0)
    exceptions = state.get("exceptions", [])
    if idx < len(exceptions):
        return "investigate"
    return "report"
