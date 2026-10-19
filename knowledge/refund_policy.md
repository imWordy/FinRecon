# Refund Eligibility, Limits & Reconciliation Policy

## 1. Refund Scope & Validity
- A refund record is considered valid only when it is tied to a pre-existing captured payment (`payment_id`) and an approved customer order (`order_id`).
- Unlinked refunds or refunds referencing non-existent payment transactions are classified as `ORPHAN_REFUND_ANOMALY` and must be blocked from automatic settlement.

## 2. Refund Amount Limits
- **Maximum Cap**: The cumulative refund amount for any given transaction cannot exceed the original gross captured payment amount (`Total Refunds <= Captured Amount`).
- **Excess Refund Exception**: If a refund record specifies an amount greater than the original captured amount (e.g., refund of ₹3,500 on a ₹3,000 charge), the system must immediately trigger `REFUND_AMOUNT_EXCEPTION`.
- Over-refunds are treated as severe operational errors or potential fraudulent leakage.

## 3. Duplicate Refund Prevention
- Two or more refund records sharing the same `payment_id`, identical refund amount, and timestamp within a 24-hour window must be investigated for accidental duplicate disbursement (`POSSIBLE_DUPLICATE_REFUND`).

## 4. Refund Settlement Timing & Fee Reversal
- In the event of a full refund within 48 hours, payment gateway processing fees may or may not be returned depending on the gateway agreement.
- Merchant settlement reports must reflect refund debits against subsequent settlement batches.
