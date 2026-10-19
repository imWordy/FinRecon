"""
Investigation Agent for FinRecon.
Investigates financial exceptions across cross-system evidence:
- Queries related fees, taxes, settlement dates, refunds, and disputes.
- Formulates an evidence-backed resolution hypothesis.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agents.base_agent import BaseAgent, AgentResponse
from tools.exception_types import ExceptionItem, ReconciliationStatus
from tools.data_tools import query_records
from tools.math_tools import verify_fee_arithmetic, verify_refund_limit
from rag.retriever import search_policy


class InvestigationHypothesis(BaseModel):
    exception_id: str
    order_id: str
    payment_id: Optional[str] = None
    investigated_category: str
    root_cause: str
    evidence_trail: List[Dict[str, Any]] = Field(default_factory=list)
    arithmetic_breakdown: Optional[Dict[str, Any]] = None
    relevant_policy_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    proposed_resolution: str


class InvestigationAgent(BaseAgent):
    """Investigates discrepancy root causes by gathering cross-system evidence."""

    def __init__(self):
        super().__init__(name="InvestigationAgent", role="Financial Forensic Investigator")

    def run(self, inputs: Dict[str, Any]) -> AgentResponse:
        exception: ExceptionItem = inputs["exception"]
        datasets: Dict[str, Any] = inputs["datasets"]

        rec = exception.record
        status = rec.status
        oid = rec.order_id
        pid = rec.payment_id

        evidence = []
        arithmetic = None
        policies = []
        proposed = "REQUIRES_HUMAN_REVIEW"
        root_cause = "Unknown financial anomaly"

        # Investigation Path 1: AMOUNT_MISMATCH
        if status == ReconciliationStatus.AMOUNT_MISMATCH:
            # Query fee table for payment
            fee_records = query_records(datasets["fees"], {"payment_id": pid})
            if fee_records:
                fee_row = fee_records[0]
                evidence.append({"type": "fee_record", "data": fee_row})
                
                # Check arithmetic
                is_balanced, var, breakdown = verify_fee_arithmetic(
                    payment_amount=rec.payment_amount,
                    fee_amount=fee_row["fee_amount"],
                    tax_amount=fee_row["tax_amount"],
                    settlement_amount=rec.settlement_amount
                )
                arithmetic = breakdown

                # Retrieve Fee and Settlement policies
                policies = search_policy("gateway fee schedule tax deduction cap", policy_type="fee", top_k=2)

                if is_balanced:
                    root_cause = (
                        f"Discrepancy of ₹{rec.discrepancy:.2f} is fully explained by documented gateway fee "
                        f"₹{fee_row['fee_amount']:.2f} and tax ₹{fee_row['tax_amount']:.2f}."
                    )
                    proposed = "AUTO_RESOLVE_VALID_FEE"
                else:
                    root_cause = (
                        f"Documented fee ₹{fee_row['total_deduction']:.2f} does not fully explain "
                        f"discrepancy of ₹{rec.discrepancy:.2f}. Remaining unexplained variance: ₹{abs(var):.2f}."
                    )
                    proposed = "REQUIRES_HUMAN_REVIEW"
            else:
                root_cause = f"Settlement amount differs by ₹{rec.discrepancy:.2f} with zero corresponding fee entries."
                proposed = "REQUIRES_HUMAN_REVIEW"

        # Investigation Path 2: POSSIBLE_DUPLICATE
        elif status == ReconciliationStatus.POSSIBLE_DUPLICATE:
            related_payments = query_records(datasets["payments"], {"order_id": oid})
            evidence.append({"type": "related_payments", "count": len(related_payments), "records": related_payments})
            
            disputes = query_records(datasets["disputes"], {"payment_id": pid})
            if disputes:
                evidence.append({"type": "dispute_record", "data": disputes[0]})
                
            policies = search_policy("customer charged twice duplicate payment dispute", policy_type="dispute", top_k=2)
            root_cause = f"Order {oid} has {len(related_payments)} distinct captured payment charges."
            proposed = "FLAG_SUSPECTED_DUPLICATE"

        # Investigation Path 3: MISSING_SETTLEMENT
        elif status == ReconciliationStatus.MISSING_SETTLEMENT:
            evidence.append({"type": "payment_record", "payment_id": pid, "amount": rec.payment_amount})
            policies = search_policy("missing settlement T+2 timeline delay", policy_type="settlement", top_k=2)
            root_cause = f"Payment {pid} captured successfully but not present in any settlement batch."
            proposed = "ESCALATE_GATEWAY_SETTLEMENT"

        # Investigation Path 4: REFUND_MISMATCH
        elif status == ReconciliationStatus.REFUND_MISMATCH:
            refund_records = query_records(datasets["refunds"], {"payment_id": pid})
            if refund_records:
                rf = refund_records[0]
                evidence.append({"type": "refund_record", "data": rf})
                is_valid_rf, excess = verify_refund_limit(rec.payment_amount, rf["refund_amount"])
                policies = search_policy("refund limit maximum eligible amount", policy_type="refund", top_k=2)
                if not is_valid_rf:
                    root_cause = f"Refund amount ₹{rf['refund_amount']:.2f} exceeds captured payment ₹{rec.payment_amount:.2f} by ₹{excess:.2f}."
                    proposed = "REQUIRES_HUMAN_REVIEW"

        hypothesis = InvestigationHypothesis(
            exception_id=exception.exception_id,
            order_id=oid,
            payment_id=pid,
            investigated_category=status.value,
            root_cause=root_cause,
            evidence_trail=evidence,
            arithmetic_breakdown=arithmetic,
            relevant_policy_chunks=policies,
            proposed_resolution=proposed
        )

        thought = f"Completed forensic investigation for {exception.exception_id}. Root cause: {root_cause}"

        return AgentResponse(
            agent_name=self.name,
            status="SUCCESS",
            data=hypothesis.model_dump(),
            thought_process=thought,
            confidence=0.95
        )
