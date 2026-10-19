"""
Resolution & Routing Agent for FinRecon.
Consolidates Investigation Hypothesis and Critic Verdict to assign the definitive
operational resolution action, action recommendation, and audit metadata.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from agents.base_agent import BaseAgent, AgentResponse
from tools.exception_types import ResolutionAction


class FinalResolutionReport(BaseModel):
    exception_id: str
    order_id: str
    payment_id: str
    final_action: str
    is_auto_resolved: bool
    requires_human_escalation: bool
    reasoning_summary: str
    recommended_operation: str
    evidence_summary: List[str] = Field(default_factory=list)
    confidence_score: float


class ResolutionAgent(BaseAgent):
    """Assigns final business decision and human escalation routing."""

    def __init__(self):
        super().__init__(name="ResolutionAgent", role="Workflow Decision & Routing Executive")

    def run(self, inputs: Dict[str, Any]) -> AgentResponse:
        hypothesis: Dict[str, Any] = inputs["hypothesis"]
        critic_verdict: Dict[str, Any] = inputs["critic_verdict"]

        exception_id = hypothesis["exception_id"]
        order_id = hypothesis["order_id"]
        payment_id = hypothesis.get("payment_id", "")
        proposed = hypothesis.get("proposed_resolution")
        verdict = critic_verdict.get("verdict")
        rejection_reasons = critic_verdict.get("rejection_reasons", [])

        # Routing Logic
        if verdict == "PASS" and proposed == "AUTO_RESOLVE_VALID_FEE":
            final_action = ResolutionAction.AUTO_RESOLVE_VALID_FEE.value
            is_auto = True
            requires_human = False
            rec_op = "Close exception and log verified gateway processing fee in general ledger."
            summary = (
                f"Auto-resolved: Discrepancy successfully validated as legitimate fee/tax deduction "
                f"matching fee schedule policy caps."
            )
            confidence = 0.98

        elif proposed == "FLAG_SUSPECTED_DUPLICATE":
            final_action = ResolutionAction.FLAG_SUSPECTED_DUPLICATE.value
            is_auto = False
            requires_human = True
            rec_op = "Review duplicate payment charges with customer support and initiate gateway refund for secondary charge."
            summary = "Suspected duplicate charge detected across payments. Customer dispute verified."
            confidence = 0.95

        elif proposed == "ESCALATE_GATEWAY_SETTLEMENT":
            final_action = ResolutionAction.ESCALATE_GATEWAY_SETTLEMENT.value
            is_auto = False
            requires_human = True
            rec_op = "Trigger automated settlement query to payment gateway operations desk for missing funds."
            summary = "Payment captured but missing from settlement batches past T+2 timeline."
            confidence = 0.95

        else:
            # Fallback to Human Escalation
            final_action = ResolutionAction.REQUIRES_HUMAN_REVIEW.value
            is_auto = False
            requires_human = True
            rec_op = "Assign to Tier-2 Finance Operations Analyst for manual ledger adjustment or gateway dispute."
            reasons_str = "; ".join(rejection_reasons) if rejection_reasons else hypothesis.get("root_cause", "")
            summary = f"Escalated to human review due to unverified balance or policy contradiction: {reasons_str}"
            confidence = 0.99

        evidence_items = [f"Category: {hypothesis.get('investigated_category')}"]
        if hypothesis.get("arithmetic_breakdown"):
            evidence_items.append(f"Equation: {hypothesis['arithmetic_breakdown'].get('equation')}")
        for p in hypothesis.get("relevant_policy_chunks", []):
            evidence_items.append(f"Policy: {p.get('source_file')} - {p.get('header')}")

        report = FinalResolutionReport(
            exception_id=exception_id,
            order_id=order_id,
            payment_id=payment_id,
            final_action=final_action,
            is_auto_resolved=is_auto,
            requires_human_escalation=requires_human,
            reasoning_summary=summary,
            recommended_operation=rec_op,
            evidence_summary=evidence_items,
            confidence_score=confidence
        )

        return AgentResponse(
            agent_name=self.name,
            status="SUCCESS",
            data=report.model_dump(),
            thought_process=summary,
            confidence=confidence
        )
