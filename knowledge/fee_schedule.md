# Fee Schedule & Merchant Pricing Policy

## 1. Scope & Application
This policy governs payment gateway processing fee schedules, tax deductions, and maximum allowable fee caps applicable across all transaction settlements processed through merchant payment channels.

## 2. Standard Gateway Processing Fee Schedule
1. **Domestic UPI Transactions**:
   - Processing fee: 0.00% (Zero MDR per regulatory mandate).
   - Fixed handling fee: ₹0.00.
2. **Standard Domestic Debit Cards**:
   - Processing fee: 0.90% of the gross transaction value.
3. **Domestic Credit Cards & Net Banking**:
   - Processing fee: 2.00% of the gross transaction value.
   - Fixed transaction surcharge: ₹0.00.
4. **Corporate Credit Cards & International Cards**:
   - Processing fee: 3.00% of the gross transaction value.

## 3. Applicable Taxes (GST)
- All gateway processing fees are subject to 18.00% Goods and Services Tax (GST).
- The tax amount is calculated strictly as: `GST = Processing Fee * 0.18`.
- The net deduction from captured funds equals `Total Deduction = Processing Fee + GST`.

## 4. Maximum Allowable Fee Caps
- **Standard Cap**: Under no circumstances shall the combined gateway fee plus tax for a single standard domestic retail transaction exceed **₹300.00**.
- **Exception Trigger**: Any observed settlement deduction exceeding ₹300.00 on a standard tier payment is categorized as an unauthorized deduction and must be flagged for financial investigation.

## 5. Audit & Compliance
Every fee deduction reflected in settlement reports must match a corresponding entry in the fee log with a valid calculation formula:
`Expected Settlement = Gross Captured Amount - (Fee Amount + Tax Amount)`.
