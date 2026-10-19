# Operational Escalation & Human-in-the-Loop Policy

## 1. Governance Principles
FinRecon functions strictly as a decision-support, investigation, and reconciliation automation platform. The system does not possess authority to move funds, initiate bank wires, or autonomously write off unverified financial balances.

## 2. Mandatory Human Escalation Thresholds
An exception cannot be auto-resolved and must be escalated to a human finance reviewer (`REQUIRES_HUMAN_REVIEW`) under any of the following mandatory conditions:

1. **Unexplained Discrepancy Threshold**:
   - Any financial variance between captured amount and settlement amount exceeding **₹500.00** that is not mathematically balanced by verified fee records or legitimate refunds.
2. **Contradictory Evidence**:
   - Any case where an observed discrepancy conflicts with the fee schedule (e.g., fee record indicates ₹200 while settlement reflects a ₹500 deficit).
   - Incomplete evidence chains where records cannot be matched across systems.
3. **Critic Agent Rejection**:
   - Any resolution proposed by the Investigation Agent that is rejected or assigned a confidence score below **0.85** by the Critic Agent.
4. **Over-Refunds & Fraud Flags**:
   - All `REFUND_AMOUNT_EXCEPTION` occurrences where the refund amount exceeds the original payment value.
5. **High-Value Single Transactions**:
   - Any unresolved discrepancy on transactions with a gross value exceeding **₹50,000.00**, regardless of the variance amount.

## 3. Human Review Workflow
- Cases escalated for human review must compile a comprehensive audit docket containing:
  - Complete evidence graph and timeline.
  - Mathematical calculations and observed variance.
  - Retrieved policy citations that triggered the escalation.
  - Reviewer action recommendations (Approve Fee Adjustment, Contact Gateway Support, or Flag for Fraud Investigation).
