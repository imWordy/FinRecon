# Settlement Timeline & Reconciliation Tolerance Policy

## 1. Settlement Timeline Standards
- **Standard Settlement Window (T+2)**: Payment gateway settlements are expected within T+2 business days from the initial payment capture date (where T represents the transaction capture date, excluding bank holidays and Sundays).
- **Delayed Settlement Window (T+3 to T+5)**: Transactions remaining unsettled after T+2 but within T+5 business days are marked with status `PENDING_SETTLEMENT`.
- **Missing Settlement Alert**: Any captured payment older than T+5 business days without a matching settlement batch entry is classified as `MISSING_SETTLEMENT` and escalated for automated gateway query.

## 2. Settlement Tolerances & Thresholds
- **Zero-Tolerance Rule**: Financial operations operate on a zero-tolerance policy (₹0.00 unexplained difference). 
- Every rupee of variance between Gross Order Amount, Captured Amount, and Settlement Credit must be fully accounted for by documented fees, taxes, partial refunds, or dispute reserves.
- Differences without itemized explanation cannot be written off automatically.

## 3. Partial Settlement Rules
- When a transaction is settled in multiple tranches, the sum of all tranche settlements plus legitimate deductions must equal the gross captured amount.
- An exception must remain `INVESTIGATING` until all tranches are linked or the variance is identified.

## 4. Currency and Rounding Rules
- All settlements must be in Indian Rupees (INR, ₹).
- Mathematical rounding adjustments of up to ₹0.05 are permissible due to fractional paise calculations on tax amounts, but must be explicitly documented as `ROUNDING_VARIANCE`.
