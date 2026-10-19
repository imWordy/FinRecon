"""
Phase 4 Automated Test Suite:
Validates standalone agent execution in isolation:
- PlannerAgent: Task decomposition and dataset discovery
- ValidationAgent: Data schema inspection
- InvestigationAgent: Cross-system evidence forensic compilation
- CriticAgent: Adversarial validation, arithmetic balance, policy cap check
- ResolutionAgent: Final decisioning and human-in-the-loop escalation routing
"""

from pathlib import Path
import pytest

from tools.data_tools import load_financial_datasets
from tools.reconciliation_tools import run_reconciliation
from tools.exception_types import ReconciliationStatus
from agents.planner_agent import PlannerAgent, TaskPlanModel
from agents.validation_agent import ValidationAgent
from agents.investigation_agent import InvestigationAgent
from agents.critic_agent import CriticAgent
from agents.resolution_agent import ResolutionAgent

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

@pytest.fixture
def datasets():
    return load_financial_datasets(DATA_DIR)

@pytest.fixture
def exceptions(datasets):
    _, excs = run_reconciliation(datasets)
    return excs


def test_tc_p4_01_planner_task_breakdown():
    """TC-P4-01: PlannerAgent decomposes high-level prompt into valid structured task plan."""
    planner = PlannerAgent()
    resp = planner.run({"user_request": "Reconcile October gateway settlements and investigate fee differences"})
    assert resp.status == "SUCCESS"
    assert resp.agent_name == "PlannerAgent"
    
    plan_data = resp.data
    assert "objective" in plan_data
    assert "required_datasets" in plan_data
    assert "orders" in plan_data["required_datasets"]
    assert "fees" in plan_data["required_datasets"]
    assert len(plan_data["tasks"]) >= 5


def test_tc_p4_02_validation_agent(datasets):
    """TC-P4-02: ValidationAgent passes clean datasets and rejects missing ones."""
    val_agent = ValidationAgent()
    
    # 1. Success on valid
    resp_success = val_agent.run({"datasets": datasets})
    assert resp_success.status == "SUCCESS"
    assert resp_success.data["is_valid"] is True

    # 2. Failure on empty
    resp_fail = val_agent.run({"datasets": {}})
    assert resp_fail.status == "FAILED"
    assert resp_fail.data["is_valid"] is False


def test_tc_p4_03_investigation_and_critic_valid_deduction(datasets, exceptions):
    """TC-P4-03: Investigation Agent explains Case 2 valid fee, and Critic Agent passes it."""
    # Find Case 2 exception (ORD-0010: ₹5000 payment, ₹4850 settlement, ₹150 fee/tax)
    case_2_exc = next((e for e in exceptions if e.record.order_id == "ORD-0010"), None)
    assert case_2_exc is not None

    inv_agent = InvestigationAgent()
    inv_resp = inv_agent.run({"exception": case_2_exc, "datasets": datasets})
    assert inv_resp.status == "SUCCESS"
    
    hyp = inv_resp.data
    assert hyp["proposed_resolution"] == "AUTO_RESOLVE_VALID_FEE"
    assert hyp["arithmetic_breakdown"]["balanced"] is True
    assert hyp["arithmetic_breakdown"]["variance"] == 0.0

    # Critic Agent Review
    critic = CriticAgent()
    critic_resp = critic.run({"hypothesis": hyp})
    assert critic_resp.status == "SUCCESS"
    verdict = critic_resp.data
    assert verdict["verdict"] == "PASS"
    assert verdict["mathematical_integrity"] is True
    assert verdict["policy_compliance"] is True

    # Resolution Agent
    resolver = ResolutionAgent()
    res_resp = resolver.run({"hypothesis": hyp, "critic_verdict": verdict})
    assert res_resp.status == "SUCCESS"
    final_rep = res_resp.data
    assert final_rep["final_action"] == "AUTO_RESOLVE_VALID_FEE"
    assert final_rep["is_auto_resolved"] is True
    assert final_rep["requires_human_escalation"] is False


def test_tc_p4_04_investigation_and_critic_rejection_on_contradiction(datasets, exceptions):
    """TC-P4-04: Case 6 (₹500 gap, only ₹200 fee) is rejected by Critic and routed to human review."""
    # Find Case 6 exception (ORD-0070: ₹18,500 order, ₹500 discrepancy, only ₹200 fee record)
    case_6_exc = next((e for e in exceptions if e.record.order_id == "ORD-0070"), None)
    assert case_6_exc is not None

    inv_agent = InvestigationAgent()
    inv_resp = inv_agent.run({"exception": case_6_exc, "datasets": datasets})
    assert inv_resp.status == "SUCCESS"
    
    hyp = inv_resp.data
    assert hyp["proposed_resolution"] == "REQUIRES_HUMAN_REVIEW"
    assert hyp["arithmetic_breakdown"]["balanced"] is False
    assert abs(hyp["arithmetic_breakdown"]["variance"]) > 0

    # Critic Agent Review
    critic = CriticAgent()
    critic_resp = critic.run({"hypothesis": hyp})
    assert critic_resp.status == "SUCCESS"
    verdict = critic_resp.data
    assert verdict["verdict"] == "FAIL"

    # Resolution Agent must enforce Human Escalation
    resolver = ResolutionAgent()
    res_resp = resolver.run({"hypothesis": hyp, "critic_verdict": verdict})
    final_rep = res_resp.data
    assert final_rep["final_action"] == "REQUIRES_HUMAN_REVIEW"
    assert final_rep["is_auto_resolved"] is False
    assert final_rep["requires_human_escalation"] is True
