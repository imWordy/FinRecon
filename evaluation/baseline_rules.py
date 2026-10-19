"""
Rule-Based Baseline Reconciler for FinRecon Evaluation.
Simulates standard commercial reconciliation software using rigid rules:
- Matches exact payment_id and order_id.
- Flags any discrepancy as an error without root cause explanation.
- Lacks policy knowledge, cannot distinguish fees from fraud, and escalates ALL exceptions to human review.
"""

from typing import Dict, Any, List, Tuple
import pandas as pd


class RuleBasedReconciler:
    """Conventional rule-based financial reconciliation baseline."""

    def __init__(self):
        self.name = "Traditional_Rule_Based_Reconciler"

    def reconcile(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Executes basic matching logic.
        Returns:
            summary dictionary with matched, mismatched, and unclassified counts.
        """
        df_orders = datasets["orders"]
        df_payments = datasets["payments"]
        df_settlements = datasets["settlements"]

        p_map = {row["order_id"]: row for row in df_payments.to_dict(orient="records")}
        s_map = {row["payment_id"]: row for row in df_settlements.to_dict(orient="records")}

        matched = 0
        exceptions = []

        for o in df_orders.to_dict(orient="records"):
            oid = o["order_id"]
            p = p_map.get(oid)
            if not p:
                exceptions.append({
                    "order_id": oid,
                    "type": "MISSING_PAYMENT",
                    "reason": "Payment not found",
                    "requires_human": True,
                    "explained": False
                })
                continue

            pid = p["payment_id"]
            s = s_map.get(pid)
            if not s:
                exceptions.append({
                    "order_id": oid,
                    "payment_id": pid,
                    "type": "MISSING_SETTLEMENT",
                    "reason": "Settlement not found",
                    "requires_human": True,
                    "explained": False
                })
                continue

            # Pure exact amount comparison
            if float(p["amount"]) == float(s["amount"]):
                matched += 1
            else:
                # Rule-based systems cannot explain fee deductions
                exceptions.append({
                    "order_id": oid,
                    "payment_id": pid,
                    "type": "AMOUNT_MISMATCH",
                    "reason": "Amounts differ",
                    "requires_human": True,  # Must escalate every difference!
                    "explained": False
                })

        total = len(df_orders)
        return {
            "system": self.name,
            "total_transactions": total,
            "matched_count": matched,
            "reconciliation_accuracy": round((matched / max(1, total)) * 100, 2),
            "exception_count": len(exceptions),
            "auto_resolved_count": 0,  # 0% auto-resolution capability
            "human_review_count": len(exceptions),  # 100% human review burden
            "explanation_coverage": 0.0,
            "exceptions": exceptions
        }
