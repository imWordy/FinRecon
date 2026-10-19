"""
Workflow Node Definitions for FinRecon.
Each node consumes the shared FinReconState, executes the respective agent/tool,
and returns state updates along with append-only audit entries.
"""

from datetime import datetime
from typing import Dict, Any

from workflows.state import FinReconState
from agents.planner_agent import PlannerAgent
from agents.validation_agent import ValidationAgent
from agents.investigation_agent import InvestigationAgent
from agents.critic_agent import CriticAgent
from agents.resolution_agent import ResolutionAgent
from tools.reconciliation_tools import run_reconciliation
from tools.exception_types import ExceptionItem

# Initialize agents
planner = PlannerAgent()
validator = ValidationAgent()
investigator = InvestigationAgent()
critic = CriticAgent()
resolver = ResolutionAgent()


def _log_audit(state: FinReconState, agent_name: str, action: str, details: Dict[str, Any]):
    """Appends an entry to the shared audit log."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": action,
        "details": details
    }
    if "audit_log" not in state or state["audit_log"] is None:
        state["audit_log"] = []
    state["audit_log"].append(log_entry)


def plan_node(state: FinReconState) -> Dict[str, Any]:
    """Planner Agent: Decomposes the user request into an execution plan."""
    user_req = state.get("user_request", "Reconcile financial records and resolve exceptions.")
    resp = planner.run({"user_request": user_req})
    _log_audit(state, planner.name, "PLAN_GENERATED", resp.data)
    return {
        "task_plan": resp.data,
        "audit_log": state.get("audit_log", [])
    }


def validate_node(state: FinReconState) -> Dict[str, Any]:
    """Validation Agent: Checks input financial datasets."""
    datasets = state["datasets"]
    resp = validator.run({"datasets": datasets})
    _log_audit(state, validator.name, "DATA_VALIDATED", resp.data)
    return {
        "validation_report": resp.data,
        "audit_log": state.get("audit_log", [])
    }


def reconcile_node(state: FinReconState) -> Dict[str, Any]:
    """Deterministic Reconciler: Executes the matching hierarchy."""
    datasets = state["datasets"]
    all_recs, exceptions = run_reconciliation(datasets)

    # Convert Pydantic models to dicts for state serialization
    exc_dicts = [e.model_dump() for e in exceptions]
    rec_dicts = [r.model_dump() for r in all_recs]

    _log_audit(state, "ReconciliationEngine", "MATCHING_COMPLETE", {
        "total_records": len(rec_dicts),
        "total_exceptions": len(exc_dicts)
    })

    return {
        "all_records": rec_dicts,
        "exceptions": exc_dicts,
        "current_exception_idx": 0,
        "resolutions": [],
        "audit_log": state.get("audit_log", [])
    }


def investigate_node(state: FinReconState) -> Dict[str, Any]:
    """Investigation Agent: Deep dives into current exception."""
    idx = state.get("current_exception_idx", 0)
    exceptions = state.get("exceptions", [])
    
    if idx >= len(exceptions):
        return {"current_exception": None}

    raw_exc = exceptions[idx]
    exc_obj = ExceptionItem(**raw_exc)
    datasets = state["datasets"]

    resp = investigator.run({"exception": exc_obj, "datasets": datasets})
    _log_audit(state, investigator.name, "EXCEPTION_INVESTIGATED", {
        "exception_id": exc_obj.exception_id,
        "root_cause": resp.data.get("root_cause")
    })

    return {
        "current_exception": raw_exc,
        "current_hypothesis": resp.data,
        "audit_log": state.get("audit_log", [])
    }


def critic_node(state: FinReconState) -> Dict[str, Any]:
    """Critic Agent: Adversarially audits hypothesis."""
    hyp = state["current_hypothesis"]
    resp = critic.run({"hypothesis": hyp})
    
    _log_audit(state, critic.name, "CRITIC_VERDICT", {
        "exception_id": hyp.get("exception_id"),
        "verdict": resp.data.get("verdict"),
        "notes": resp.data.get("critique_notes")
    })

    return {
        "current_critic_verdict": resp.data,
        "audit_log": state.get("audit_log", [])
    }


def resolve_node(state: FinReconState) -> Dict[str, Any]:
    """Resolution Agent: Produces final decision and routes."""
    hyp = state["current_hypothesis"]
    verdict = state["current_critic_verdict"]

    resp = resolver.run({"hypothesis": hyp, "critic_verdict": verdict})
    
    resolutions = list(state.get("resolutions", []))
    resolutions.append(resp.data)

    _log_audit(state, resolver.name, "RESOLUTION_ROUTED", {
        "exception_id": hyp.get("exception_id"),
        "final_action": resp.data.get("final_action"),
        "requires_human": resp.data.get("requires_human_escalation")
    })

    # Increment index for queue processing
    next_idx = state.get("current_exception_idx", 0) + 1

    return {
        "resolutions": resolutions,
        "current_exception_idx": next_idx,
        "audit_log": state.get("audit_log", [])
    }


def report_node(state: FinReconState) -> Dict[str, Any]:
    """Summary Node: Compiles final reconciliation metrics."""
    all_recs = state.get("all_records", [])
    exceptions = state.get("exceptions", [])
    resolutions = state.get("resolutions", [])

    auto_resolved = sum(1 for r in resolutions if r.get("is_auto_resolved", False))
    human_review = sum(1 for r in resolutions if r.get("requires_human_escalation", True))
    matched_count = len(all_recs) - len(exceptions)

    summary = {
        "total_transactions": len(all_recs),
        "matched_count": matched_count,
        "matched_rate": round(matched_count / max(1, len(all_recs)) * 100, 2),
        "total_exceptions": len(exceptions),
        "auto_resolved_count": auto_resolved,
        "human_review_count": human_review,
        "resolutions": resolutions,
        "audit_trail_events": len(state.get("audit_log", []))
    }

    _log_audit(state, "ReportingNode", "FINAL_REPORT_COMPILED", summary)

    return {
        "summary_report": summary,
        "audit_log": state.get("audit_log", [])
    }
