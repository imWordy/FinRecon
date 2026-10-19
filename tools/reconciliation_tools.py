"""
Deterministic reconciliation and matching hierarchy engine for FinRecon.
Implements the multi-stage matching hierarchy and anomaly detection rules:
1. Exact Payment ID matching
2. Order ID matching
3. Duplicate payment detection
4. Discrepancy calculation & baseline classification
"""

from typing import Dict, Any, List, Tuple
import pandas as pd

from tools.exception_types import (
    ReconciliationStatus,
    ReconciliationRecord,
    ExceptionItem
)
from tools.math_tools import calculate_discrepancy


def detect_duplicate_payments(df_payments: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Detects orders that have more than one CAPTURED payment record.
    Returns: {order_id: [payment_id_1, payment_id_2, ...]}
    """
    captured_payments = df_payments[df_payments["status"] == "CAPTURED"]
    counts = captured_payments.groupby("order_id")["payment_id"].apply(list).to_dict()
    duplicates = {oid: pids for oid, pids in counts.items() if len(pids) > 1}
    return duplicates


def run_reconciliation(
    datasets: Dict[str, pd.DataFrame]
) -> Tuple[List[ReconciliationRecord], List[ExceptionItem]]:
    """
    Executes the deterministic matching hierarchy across orders, payments, and settlements.
    Returns:
        (all_records, exception_items)
    """
    df_orders = datasets["orders"]
    df_payments = datasets["payments"]
    df_settlements = datasets["settlements"]

    # Pre-index payments and settlements for performance
    duplicate_payments_map = detect_duplicate_payments(df_payments)
    
    # Map order_id -> list of payment records
    order_to_payments = {}
    for row in df_payments.to_dict(orient="records"):
        order_to_payments.setdefault(row["order_id"], []).append(row)

    # Map payment_id -> settlement record
    payment_to_settlement = {}
    for row in df_settlements.to_dict(orient="records"):
        payment_to_settlement[row["payment_id"]] = row

    all_records: List[ReconciliationRecord] = []
    exceptions: List[ExceptionItem] = []
    exception_counter = 1

    for order_row in df_orders.to_dict(orient="records"):
        oid = order_row["order_id"]
        o_amount = float(order_row["amount"])
        c_id = order_row.get("customer_id")
        
        related_payments = order_to_payments.get(oid, [])

        # Stage 1 Check: Missing Payment
        if not related_payments:
            rec = ReconciliationRecord(
                order_id=oid,
                customer_id=c_id,
                order_amount=o_amount,
                status=ReconciliationStatus.MISSING_PAYMENT,
                matching_stage="ORDER_UNPAID",
                discrepancy=o_amount
            )
            all_records.append(rec)
            exc = ExceptionItem(
                exception_id=f"EXC-{exception_counter:04d}",
                record=rec,
                detected_at_stage="STAGE_1_PAYMENT_LOOKUP",
                preliminary_reason="No captured payment found for order",
                status=ReconciliationStatus.MISSING_PAYMENT
            )
            exceptions.append(exc)
            exception_counter += 1
            continue

        # Check: Duplicate Payments on single Order
        if oid in duplicate_payments_map:
            for p_rec in related_payments:
                p_id = p_rec["payment_id"]
                p_amount = float(p_rec["amount"])
                s_rec = payment_to_settlement.get(p_id)
                s_id = s_rec["settlement_id"] if s_rec else None
                s_amount = float(s_rec["amount"]) if s_rec else None

                rec = ReconciliationRecord(
                    order_id=oid,
                    payment_id=p_id,
                    settlement_id=s_id,
                    customer_id=c_id,
                    order_amount=o_amount,
                    payment_amount=p_amount,
                    settlement_amount=s_amount,
                    status=ReconciliationStatus.POSSIBLE_DUPLICATE,
                    matching_stage="DUPLICATE_CHECK",
                    metadata={"duplicate_group": duplicate_payments_map[oid]}
                )
                all_records.append(rec)
                
                # Flag the duplicate as an exception
                exc = ExceptionItem(
                    exception_id=f"EXC-{exception_counter:04d}",
                    record=rec,
                    detected_at_stage="STAGE_DUPLICATE_DETECTION",
                    preliminary_reason=f"Multiple captured payments for single order {oid}",
                    status=ReconciliationStatus.POSSIBLE_DUPLICATE
                )
                exceptions.append(exc)
                exception_counter += 1
            continue

        # Single standard payment flow
        p_rec = related_payments[0]
        p_id = p_rec["payment_id"]
        p_amount = float(p_rec["amount"])
        
        s_rec = payment_to_settlement.get(p_id)

        # Stage 2 Check: Missing Settlement
        if not s_rec:
            rec = ReconciliationRecord(
                order_id=oid,
                payment_id=p_id,
                customer_id=c_id,
                order_amount=o_amount,
                payment_amount=p_amount,
                settlement_amount=None,
                discrepancy=p_amount,
                status=ReconciliationStatus.MISSING_SETTLEMENT,
                matching_stage="STAGE_2_SETTLEMENT_LOOKUP"
            )
            all_records.append(rec)
            exc = ExceptionItem(
                exception_id=f"EXC-{exception_counter:04d}",
                record=rec,
                detected_at_stage="STAGE_2_SETTLEMENT_LOOKUP",
                preliminary_reason="Payment captured but missing settlement entry",
                status=ReconciliationStatus.MISSING_SETTLEMENT
            )
            exceptions.append(exc)
            exception_counter += 1
            continue

        # Stage 3 Check: Settlement Amount Comparison
        s_id = s_rec["settlement_id"]
        s_amount = float(s_rec["amount"])
        diff = calculate_discrepancy(p_amount, s_amount)

        if abs(diff) == 0.0:
            rec = ReconciliationRecord(
                order_id=oid,
                payment_id=p_id,
                settlement_id=s_id,
                customer_id=c_id,
                order_amount=o_amount,
                payment_amount=p_amount,
                settlement_amount=s_amount,
                discrepancy=0.0,
                status=ReconciliationStatus.MATCHED,
                matching_stage="EXACT_MATCH"
            )
            all_records.append(rec)
        else:
            rec = ReconciliationRecord(
                order_id=oid,
                payment_id=p_id,
                settlement_id=s_id,
                customer_id=c_id,
                order_amount=o_amount,
                payment_amount=p_amount,
                settlement_amount=s_amount,
                discrepancy=diff,
                status=ReconciliationStatus.AMOUNT_MISMATCH,
                matching_stage="EXACT_MATCH_WITH_DISCREPANCY"
            )
            all_records.append(rec)
            exc = ExceptionItem(
                exception_id=f"EXC-{exception_counter:04d}",
                record=rec,
                detected_at_stage="STAGE_3_AMOUNT_VERIFICATION",
                preliminary_reason=f"Payment {p_amount:.2f} differs from settlement {s_amount:.2f} by {diff:.2f}",
                status=ReconciliationStatus.AMOUNT_MISMATCH
            )
            exceptions.append(exc)
            exception_counter += 1

    return all_records, exceptions
