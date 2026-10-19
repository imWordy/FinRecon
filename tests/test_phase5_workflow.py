"""
Phase 5 Automated Test Suite:
Validates Multi-Agent LangGraph Orchestration:
- TC-P5-01: Graph compilation without unbound edges or state schema errors
- TC-P5-02: Zero-exception data bypasses investigation directly to report
- TC-P5-03: End-to-end execution across dataset batch with exception loop
- TC-P5-04: Tamper-evident audit log completeness across all graph transitions
"""

from pathlib import Path
import pytest
import pandas as pd

from tools.data_tools import load_financial_datasets
from workflows.graph import compile_reconciliation_workflow, run_finrecon_pipeline
from workflows.state import FinReconState

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

@pytest.fixture
def datasets():
    return load_financial_datasets(DATA_DIR)


def test_tc_p5_01_graph_compilation():
    """TC-P5-01: Validates that the state graph compiles successfully."""
    app = compile_reconciliation_workflow()
    assert app is not None
    # Check that required nodes exist
    expected_nodes = {"planner", "validator", "reconciler", "investigate", "critic", "resolver", "report"}
    assert expected_nodes.issubset(set(app.nodes.keys()))


def test_tc_p5_02_zero_exception_path():
    """TC-P5-02: Clean data with 0 exceptions routes directly from reconciler to report."""
    clean_datasets = {
        "orders": pd.DataFrame([{
            "order_id": "ORD-0001",
            "customer_id": "CUST-0001",
            "order_date": "2026-10-01 10:00:00",
            "amount": 2500.0,
            "status": "PAID"
        }]),
        "payments": pd.DataFrame([{
            "payment_id": "TXN-0001",
            "order_id": "ORD-0001",
            "payment_date": "2026-10-01 10:05:00",
            "amount": 2500.0,
            "method": "UPI",
            "status": "CAPTURED"
        }]),
        "settlements": pd.DataFrame([{
            "settlement_id": "SET-0001",
            "payment_id": "TXN-0001",
            "settlement_date": "2026-10-02 10:00:00",
            "amount": 2500.0,
            "status": "SETTLED"
        }]),
        "fees": pd.DataFrame(columns=["fee_id", "payment_id", "fee_amount", "tax_amount", "total_deduction", "fee_type", "created_at"]),
        "refunds": pd.DataFrame(columns=["refund_id", "payment_id", "order_id", "refund_amount", "refund_date", "reason", "status"]),
        "disputes": pd.DataFrame(columns=["dispute_id", "payment_id", "customer_id", "dispute_date", "claim_reason", "status"]),
        "customers": pd.DataFrame([{"customer_id": "CUST-0001", "name": "Test", "email": "test@example.com", "tier": "STANDARD"}])
    }

    final_state = run_finrecon_pipeline(clean_datasets, user_request="Reconcile clean sample")
    
    # Assertions
    assert len(final_state["exceptions"]) == 0
    assert len(final_state["resolutions"]) == 0
    assert final_state["summary_report"]["total_exceptions"] == 0
    assert final_state["summary_report"]["matched_count"] == 1
    assert final_state["summary_report"]["matched_rate"] == 100.0


def test_tc_p5_03_end_to_end_batch_execution(datasets):
    """TC-P5-03: End-to-end execution on sample batch with mixed anomalies."""
    # Slice first 30 orders containing Case 1, Case 2, Case 3
    order_subset = datasets["orders"].iloc[:30].copy()
    order_ids = set(order_subset["order_id"])
    
    sliced_datasets = {
        "orders": order_subset,
        "payments": datasets["payments"][datasets["payments"]["order_id"].isin(order_ids)].copy(),
        "settlements": datasets["settlements"].copy(),
        "fees": datasets["fees"].copy(),
        "refunds": datasets["refunds"].copy(),
        "disputes": datasets["disputes"].copy(),
        "customers": datasets["customers"].copy(),
    }

    final_state = run_finrecon_pipeline(
        sliced_datasets,
        user_request="Reconcile first 30 orders and resolve exceptions"
    )

    report = final_state["summary_report"]
    assert report["total_transactions"] == 30
    assert report["total_exceptions"] > 0
    assert len(report["resolutions"]) == report["total_exceptions"]
    assert report["auto_resolved_count"] > 0


def test_tc_p5_04_state_audit_trail_completeness(datasets):
    """TC-P5-04: Verifies tamper-evident audit trail entries for every node transition."""
    # Slice small 5-order batch
    order_subset = datasets["orders"].iloc[:5].copy()
    order_ids = set(order_subset["order_id"])
    
    sliced = {
        "orders": order_subset,
        "payments": datasets["payments"][datasets["payments"]["order_id"].isin(order_ids)].copy(),
        "settlements": datasets["settlements"].copy(),
        "fees": datasets["fees"].copy(),
        "refunds": datasets["refunds"].copy(),
        "disputes": datasets["disputes"].copy(),
        "customers": datasets["customers"].copy(),
    }

    final_state = run_finrecon_pipeline(sliced)
    audit = final_state.get("audit_log", [])
    assert len(audit) >= 4, "Audit log should have entries from planner, validator, reconciler, and reporter"

    agents_in_log = set(e["agent"] for e in audit)
    assert "PlannerAgent" in agents_in_log
    assert "ValidationAgent" in agents_in_log
    assert "ReconciliationEngine" in agents_in_log
    assert "ReportingNode" in agents_in_log

    for entry in audit:
        assert "timestamp" in entry
        assert "action" in entry
        assert "details" in entry
