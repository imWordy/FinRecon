"""
Phase 2 Automated Test Suite:
Validates deterministic tools, schema validation, matching hierarchy,
discrepancy detection, duplicate detection, and arithmetic verification.
"""

from pathlib import Path
import pytest
import pandas as pd

from tools.data_tools import load_financial_datasets, validate_dataset_schemas, query_records
from tools.math_tools import calculate_discrepancy, verify_fee_arithmetic, verify_refund_limit
from tools.reconciliation_tools import run_reconciliation, detect_duplicate_payments
from tools.exception_types import ReconciliationStatus

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

@pytest.fixture
def datasets():
    return load_financial_datasets(DATA_DIR)


def test_tc_p2_01_strict_schema_validation(datasets):
    """TC-P2-01: Schema validation correctly accepts valid datasets and flags errors on invalid ones."""
    # Test valid datasets
    report = validate_dataset_schemas(datasets)
    assert report["is_valid"] is True, f"Valid datasets failed validation: {report['errors']}"
    assert len(report["errors"]) == 0

    # Test invalid schema injection (missing column)
    corrupted = {k: v.copy() for k, v in datasets.items()}
    corrupted["orders"] = corrupted["orders"].drop(columns=["amount"])
    corrupted_report = validate_dataset_schemas(corrupted)
    assert corrupted_report["is_valid"] is False
    assert any("missing columns" in err for err in corrupted_report["errors"])

    # Test negative amount detection
    corrupted_neg = {k: v.copy() for k, v in datasets.items()}
    corrupted_neg["payments"].loc[0, "amount"] = -500.00
    neg_report = validate_dataset_schemas(corrupted_neg)
    assert neg_report["is_valid"] is False
    assert any("negative values" in err for err in neg_report["errors"])


def test_tc_p2_02_exact_match_accuracy(datasets):
    """TC-P2-02: 100% precision on baseline identical transactions (Case 1)."""
    all_records, exceptions = run_reconciliation(datasets)
    assert len(all_records) >= 1000

    # Verify Case 1 records (ORD-0001, ORD-0002, ORD-0003) are MATCHED
    case_1_records = [r for r in all_records if r.order_id in ["ORD-0001", "ORD-0002", "ORD-0003"]]
    assert len(case_1_records) == 3
    for r in case_1_records:
        assert r.status == ReconciliationStatus.MATCHED
        assert r.discrepancy == 0.0
        assert r.payment_amount == r.settlement_amount


def test_tc_p2_03_discrepancy_detection(datasets):
    """TC-P2-03: Correctly flags discrepancy between ₹5,000 payment and ₹4,850 settlement (Case 2)."""
    all_records, exceptions = run_reconciliation(datasets)

    # ORD-0010 is Case 2 (₹5,000 captured, ₹4,850 settled, diff = ₹150)
    case_2_rec = next((r for r in all_records if r.order_id == "ORD-0010"), None)
    assert case_2_rec is not None
    assert case_2_rec.status == ReconciliationStatus.AMOUNT_MISMATCH
    assert case_2_rec.discrepancy == 150.00
    assert case_2_rec.payment_amount == 5000.00
    assert case_2_rec.settlement_amount == 4850.00

    # Must also be present in exceptions list
    exc = next((e for e in exceptions if e.record.order_id == "ORD-0010"), None)
    assert exc is not None
    assert exc.status == ReconciliationStatus.AMOUNT_MISMATCH


def test_tc_p2_04_duplicate_flagging(datasets):
    """TC-P2-04: Correctly detects multiple captured payments for single order as POSSIBLE_DUPLICATE (Case 4)."""
    all_records, exceptions = run_reconciliation(datasets)

    # ORD-0040 and ORD-0041 are Case 4
    duplicates = detect_duplicate_payments(datasets["payments"])
    assert "ORD-0040" in duplicates
    assert len(duplicates["ORD-0040"]) == 2

    # Check reconciliation records
    dup_recs = [r for r in all_records if r.order_id == "ORD-0040"]
    assert len(dup_recs) == 2
    for r in dup_recs:
        assert r.status == ReconciliationStatus.POSSIBLE_DUPLICATE


def test_tc_p2_05_arithmetic_verification():
    """TC-P2-05: Strict arithmetic check for fee balances and refund caps."""
    # 1. Valid fee deduction (₹5000 - ₹100 - ₹50 = ₹4850)
    is_valid, var, breakdown = verify_fee_arithmetic(
        payment_amount=5000.00,
        fee_amount=100.00,
        tax_amount=50.00,
        settlement_amount=4850.00
    )
    assert is_valid is True
    assert var == 0.0
    assert breakdown["balanced"] is True

    # 2. Invalid fee deduction (Unexplained difference: ₹500 diff, but ₹169.49 fee + ₹30.51 tax = ₹200)
    is_valid_bad, var_bad, breakdown_bad = verify_fee_arithmetic(
        payment_amount=18500.00,
        fee_amount=169.49,
        tax_amount=30.51,
        settlement_amount=18000.00
    )
    assert is_valid_bad is False
    assert var_bad == -300.00  # 18000 is 300 less than expected 18300
    assert breakdown_bad["balanced"] is False

    # 3. Refund limit check
    valid_rf, excess_0 = verify_refund_limit(3000.00, 3000.00)
    assert valid_rf is True
    assert excess_0 == 0.0

    invalid_rf, excess_500 = verify_refund_limit(3000.00, 3500.00)
    assert invalid_rf is False
    assert excess_500 == 500.00
