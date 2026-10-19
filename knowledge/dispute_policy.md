# Dispute Investigation & Chargeback Policy

## 1. Scope & Objective
This policy defines the evidentiary requirements and cross-referencing criteria for customer payment disputes, chargeback notices, and double-debit claims.

## 2. Customer Double-Charge Claims ("Charged Twice")
When a customer files a dispute claiming they were charged multiple times for a single order:
1. **Scenario A (True Duplicate Payment)**:
   - One `order_id` exists.
   - Two distinct captured payments (`TXN-1`, `TXN-2`) exist with identical amounts.
   - No auto-reversal or refund record exists for either transaction.
   - **Action**: Verify duplicate capture, flag `POSSIBLE_DUPLICATE`, and recommend initiating an immediate refund for the secondary transaction.
2. **Scenario B (Separate Legitimate Orders)**:
   - Payment A maps to Order A.
   - Payment B maps to Order B.
   - **Action**: Dispute claim unsupported. Mark as `CLAIM_NOT_SUPPORTED`.
3. **Scenario C (Pre-Reversed Charge)**:
   - Payment A captured.
   - Payment B captured but possesses an immediate corresponding reversal or void record within the gateway logs.
   - **Action**: Mark as `NO_DUPLICATE_CHARGE` (already resolved at gateway layer).

## 3. Dispute Holdbacks & Reserve Deductions
- Chargeback notifications trigger a provisional withholding by the payment gateway.
- An exception must be cross-referenced against `disputes.csv` before classifying any unexpected settlement deficit as an unauthorized discrepancy.
