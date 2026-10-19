"""
Phase 6 Automated Test Suite:
Validates Explainability, Visual Evidence Graph, Audit Trail Logging,
and Forensic Exception Dossier Generation:
- TC-P6-01: Evidence graph structure generation (Order -> Payment -> Deductions -> Settlement)
- TC-P6-02: Exact mathematical equation rendering in investigation reports
- TC-P6-03: Append-only JSONL audit trail serialization and roundtrip reading
"""

import json
from pathlib import Path
import pytest

from tools.data_tools import load_financial_datasets
from tools.reconciliation_tools import run_reconciliation
from agents.investigation_agent import InvestigationAgent
from agents.critic_agent import CriticAgent
from agents.resolution_agent import ResolutionAgent
from reporting.evidence_graph import build_evidence_graph_for_exception
from reporting.audit_logger import AuditLogger
from reporting.report_generator import (
    generate_executive_summary_markdown,
    generate_exception_dossier_markdown
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TEMP_LOG_FILE = BASE_DIR / "tests" / "test_audit.jsonl"


@pytest.fixture
def datasets():
    return load_financial_datasets(DATA_DIR)

@pytest.fixture
def case_2_suite(datasets):
    _, exceptions = run_reconciliation(datasets)
    case_2_exc = next(e for e in exceptions if e.record.order_id == "ORD-0010")
    
    inv = InvestigationAgent().run({"exception": case_2_exc, "datasets": datasets})
    critic = CriticAgent().run({"hypothesis": inv.data})
    res = ResolutionAgent().run({"hypothesis": inv.data, "critic_verdict": critic.data})
    
    return case_2_exc.model_dump(), inv.data, res.data


def test_tc_p6_01_evidence_graph_generation(case_2_suite):
    """TC-P6-01: Validates directed evidence graph linking Order -> Payment -> Fee -> Settlement."""
    exc_item, hyp, res = case_2_suite
    graph = build_evidence_graph_for_exception(exc_item, hyp, res)

    assert len(graph.nodes) >= 4, "Expected at least Order, Payment, Fee, and Settlement nodes"
    node_types = set(n.type for n in graph.nodes)
    assert {"order", "payment", "deduction", "settlement"}.issubset(node_types)

    # Check edges
    assert len(graph.edges) >= 3
    relations = set(e.relation for e in graph.edges)
    assert "FULFILLS" in relations or "DEDUCTION" in relations

    # Check Mermaid diagram generation
    mermaid_code = graph.to_mermaid()
    assert mermaid_code.startswith("flowchart TD")
    assert "ORD_0010" in mermaid_code
    assert "TXN_" in mermaid_code


def test_tc_p6_02_mathematical_equation_in_summary(case_2_suite):
    """TC-P6-02: Generates exception dossier containing explicit arithmetic equation."""
    exc_item, hyp, res = case_2_suite
    dossier = generate_exception_dossier_markdown(exc_item, hyp, res)

    assert "# Forensic Investigation Dossier" in dossier
    assert "5000.00" in dossier
    assert "4850.00" in dossier
    # Verify exact equation appears in mathematical section
    assert "5000.00 - 100.00 - 50.00 = 4850.00" in dossier
    # Verify policy section appears
    assert "Governing Policy Citations" in dossier
    # Verify mermaid diagram is included
    assert "```mermaid" in dossier


def test_tc_p6_03_audit_log_serialization():
    """TC-P6-03: Validates JSONL audit trail persistence and schema fidelity."""
    if TEMP_LOG_FILE.exists():
        TEMP_LOG_FILE.unlink()

    logger = AuditLogger(TEMP_LOG_FILE)
    
    # 1. Log events
    logger.log_event("PlannerAgent", "PLAN_GENERATED", {"tasks": 5}, confidence=1.0)
    logger.log_event("CriticAgent", "CRITIC_VERDICT", {"verdict": "PASS"}, confidence=0.98)

    assert TEMP_LOG_FILE.exists()

    # 2. Read back
    events = logger.read_all_events()
    assert len(events) == 2
    assert events[0]["agent"] == "PlannerAgent"
    assert events[1]["agent"] == "CriticAgent"
    assert events[1]["details"]["verdict"] == "PASS"

    # Clean up
    if TEMP_LOG_FILE.exists():
        TEMP_LOG_FILE.unlink()
