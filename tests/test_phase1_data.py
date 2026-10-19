"""
Phase 1 Automated Test Suite:
Validates environment setup, synthetic dataset schema/relationships, 
policy document availability, and ground-truth exception distribution.
"""

import json
from pathlib import Path
import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

def test_tc_p1_01_dataset_generation_integrity():
    """Verify that all 7 required CSV files exist and contain non-zero records."""
    required_files = [
        "orders.csv",
        "payments.csv",
        "settlements.csv",
        "fees.csv",
        "refunds.csv",
        "disputes.csv",
        "customers.csv",
    ]
    for filename in required_files:
        file_path = DATA_DIR / filename
        assert file_path.exists(), f"Missing required dataset: {filename}"
        df = pd.read_csv(file_path)
        assert len(df) > 0, f"Dataset {filename} is unexpectedly empty"

def test_tc_p1_02_schema_and_key_relationships():
    """Verify primary and foreign key consistency across datasets."""
    df_orders = pd.read_csv(DATA_DIR / "orders.csv")
    df_payments = pd.read_csv(DATA_DIR / "payments.csv")
    df_settlements = pd.read_csv(DATA_DIR / "settlements.csv")
    df_fees = pd.read_csv(DATA_DIR / "fees.csv")
    df_refunds = pd.read_csv(DATA_DIR / "refunds.csv")
    df_disputes = pd.read_csv(DATA_DIR / "disputes.csv")
    df_customers = pd.read_csv(DATA_DIR / "customers.csv")
    
    # Check Orders schema & uniqueness
    assert set(["order_id", "customer_id", "order_date", "amount", "status"]).issubset(df_orders.columns)
    assert df_orders["order_id"].is_unique, "order_id must be unique in orders.csv"
    
    # Check customer references
    customer_ids = set(df_customers["customer_id"])
    assert set(df_orders["customer_id"]).issubset(customer_ids), "Orphan customer_id in orders.csv"
    
    # Check payments reference existing orders
    order_ids = set(df_orders["order_id"])
    assert set(df_payments["order_id"]).issubset(order_ids), "Orphan order_id in payments.csv"
    
    # Check settlements reference existing payments
    payment_ids = set(df_payments["payment_id"])
    assert set(df_settlements["payment_id"]).issubset(payment_ids), "Orphan payment_id in settlements.csv"
    
    # Check fees reference existing payments
    assert set(df_fees["payment_id"]).issubset(payment_ids), "Orphan payment_id in fees.csv"
    
    # Check refunds reference existing orders and payments
    assert set(df_refunds["payment_id"]).issubset(payment_ids), "Orphan payment_id in refunds.csv"
    assert set(df_refunds["order_id"]).issubset(order_ids), "Orphan order_id in refunds.csv"
    
    # Check disputes reference existing payments
    assert set(df_disputes["payment_id"]).issubset(payment_ids), "Orphan payment_id in disputes.csv"

def test_tc_p1_03_ground_truth_distribution():
    """Verify ground_truth_labels.json contains all 6 canonical anomaly categories."""
    gt_path = DATA_DIR / "ground_truth_labels.json"
    assert gt_path.exists(), "Missing ground_truth_labels.json"
    
    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
        
    assert len(ground_truth) > 0, "Ground truth labels file is empty"
    
    categories = set(item["category"] for item in ground_truth)
    expected_categories = {
        "MATCHED",
        "VALID_FEE_DEDUCTION",
        "MISSING_SETTLEMENT",
        "POSSIBLE_DUPLICATE",
        "REFUND_AMOUNT_EXCEPTION",
        "REQUIRES_HUMAN_REVIEW"
    }
    assert expected_categories.issubset(categories), f"Missing expected test categories. Present: {categories}"

def test_tc_p1_04_knowledge_base_accessibility():
    """Verify that all policy documents exist and contain required policy clauses."""
    required_policies = [
        "fee_schedule.md",
        "settlement_policy.md",
        "refund_policy.md",
        "dispute_policy.md",
        "escalation_policy.md"
    ]
    for policy in required_policies:
        p_path = KNOWLEDGE_DIR / policy
        assert p_path.exists(), f"Policy file {policy} does not exist in knowledge directory"
        content = p_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 100, f"Policy file {policy} is too short or empty"
        assert "# " in content, f"Policy file {policy} lacks proper markdown headers"
