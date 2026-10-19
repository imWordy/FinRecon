"""
Synthetic Financial Dataset Generator for FinRecon.

Generates 7 interrelated CSV files simulating e-commerce order lifecycle:
1. orders.csv
2. payments.csv
3. settlements.csv
4. fees.csv
5. refunds.csv
6. disputes.csv
7. customers.csv

Deliberately includes ground-truth synthetic test cases:
- Case 1: Normal Match (Order == Payment == Settlement)
- Case 2: Valid Fee Deduction (Payment - Fee - Tax == Settlement)
- Case 3: Missing Settlement (Payment captured, no settlement after T+3)
- Case 4: Duplicate Payment (Single Order with two distinct captured payments)
- Case 5: Refund Mismatch (Refund amount > original payment amount)
- Case 6: Contradictory Evidence (Variance does not balance with fee schedule -> requires human review)
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# Paths
DATA_DIR = Path(__file__).resolve().parent

def generate_synthetic_data(num_orders: int = 1000, random_seed: int = 42) -> dict:
    random.seed(random_seed)
    
    start_date = datetime(2026, 10, 1)
    
    # 1. Customers
    num_customers = max(50, num_orders // 5)
    customers = []
    for i in range(1, num_customers + 1):
        customers.append({
            "customer_id": f"CUST-{i:04d}",
            "name": f"Customer_{i}",
            "email": f"customer_{i}@example.com",
            "tier": random.choice(["STANDARD", "PREMIUM", "ENTERPRISE"])
        })
    df_customers = pd.DataFrame(customers)
    
    # Pre-allocate containers
    orders = []
    payments = []
    settlements = []
    fees = []
    refunds = []
    disputes = []
    ground_truth = []
    
    # Targeted injection indices
    # We allocate specific indices for our 6 canonical test cases
    case_indices = {
        "case_1_normal": [1, 2, 3],
        "case_2_valid_fee": [10, 11, 12, 13, 14],
        "case_3_missing_settlement": [25, 26, 27],
        "case_4_duplicate_payment": [40, 41],
        "case_5_refund_mismatch": [55, 56],
        "case_6_contradictory": [70, 71, 72]
    }
    
    payment_counter = 1
    settlement_counter = 1
    fee_counter = 1
    refund_counter = 1
    dispute_counter = 1
    
    for i in range(1, num_orders + 1):
        order_id = f"ORD-{i:04d}"
        cust = random.choice(customers)["customer_id"]
        order_date = start_date + timedelta(days=(i % 25), hours=random.randint(8, 20))
        
        # Determine case type
        is_case_1 = i in case_indices["case_1_normal"]
        is_case_2 = i in case_indices["case_2_valid_fee"]
        is_case_3 = i in case_indices["case_3_missing_settlement"]
        is_case_4 = i in case_indices["case_4_duplicate_payment"]
        is_case_5 = i in case_indices["case_5_refund_mismatch"]
        is_case_6 = i in case_indices["case_6_contradictory"]
        
        # Base order amount
        if is_case_1:
            order_amount = 2500.00
        elif is_case_2:
            order_amount = 5000.00
        elif is_case_3:
            order_amount = 3200.00
        elif is_case_4:
            order_amount = 2999.00
        elif is_case_5:
            order_amount = 3000.00
        elif is_case_6:
            order_amount = 18500.00
        else:
            # General distribution
            order_amount = float(random.choice([500, 1200, 1800, 2500, 3500, 4800, 6500, 10000]))
            
        orders.append({
            "order_id": order_id,
            "customer_id": cust,
            "order_date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": round(order_amount, 2),
            "status": "PAID"
        })
        
        # Case 4: Duplicate Payment (1 order, 2 captured payments)
        if is_case_4:
            p1_id = f"TXN-{payment_counter:04d}"
            payment_counter += 1
            p2_id = f"TXN-{payment_counter:04d}"
            payment_counter += 1
            
            p_date1 = order_date + timedelta(minutes=2)
            p_date2 = order_date + timedelta(minutes=15)
            
            payments.append({
                "payment_id": p1_id,
                "order_id": order_id,
                "payment_date": p_date1.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": order_amount,
                "method": "CREDIT_CARD",
                "status": "CAPTURED"
            })
            payments.append({
                "payment_id": p2_id,
                "order_id": order_id,
                "payment_date": p_date2.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": order_amount,
                "method": "CREDIT_CARD",
                "status": "CAPTURED"
            })
            
            # Settlement for p1 only
            s_id = f"SET-{settlement_counter:04d}"
            settlement_counter += 1
            settlements.append({
                "settlement_id": s_id,
                "payment_id": p1_id,
                "settlement_date": (p_date1 + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "amount": order_amount,
                "status": "SETTLED"
            })
            
            disputes.append({
                "dispute_id": f"DISP-{dispute_counter:04d}",
                "payment_id": p2_id,
                "customer_id": cust,
                "dispute_date": (p_date2 + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "claim_reason": "Charged twice for single order",
                "status": "OPEN"
            })
            dispute_counter += 1
            
            ground_truth.append({
                "order_id": order_id,
                "payment_id": p2_id,
                "category": "POSSIBLE_DUPLICATE",
                "case_id": "CASE_4",
                "description": "Two captured payments for single order; dispute filed by customer",
                "expected_resolution": "FLAG_SUSPECTED_DUPLICATE"
            })
            continue

        # Standard single payment per order
        payment_id = f"TXN-{payment_counter:04d}"
        payment_counter += 1
        p_date = order_date + timedelta(minutes=random.randint(1, 10))
        
        payments.append({
            "payment_id": payment_id,
            "order_id": order_id,
            "payment_date": p_date.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": order_amount,
            "method": "UPI" if is_case_1 else "CREDIT_CARD",
            "status": "CAPTURED"
        })
        
        # Case 3: Missing Settlement (Payment captured, no settlement)
        if is_case_3:
            ground_truth.append({
                "order_id": order_id,
                "payment_id": payment_id,
                "category": "MISSING_SETTLEMENT",
                "case_id": "CASE_3",
                "description": "Captured payment has no settlement record after T+3 business days",
                "expected_resolution": "ESCALATE_GATEWAY_SETTLEMENT"
            })
            continue
            
        # Case 1: Normal Match (Zero fee UPI or direct full settlement)
        if is_case_1:
            settlement_id = f"SET-{settlement_counter:04d}"
            settlement_counter += 1
            s_date = p_date + timedelta(days=1)
            settlements.append({
                "settlement_id": settlement_id,
                "payment_id": payment_id,
                "settlement_date": s_date.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": order_amount,
                "status": "SETTLED"
            })
            ground_truth.append({
                "order_id": order_id,
                "payment_id": payment_id,
                "category": "MATCHED",
                "case_id": "CASE_1",
                "description": "Exact match across order, payment, and settlement",
                "expected_resolution": "AUTO_RESOLVE_MATCHED"
            })
            continue

        # Case 2: Valid Fee Deduction (₹5,000 payment -> ₹100 fee + ₹50 GST -> ₹4,850 settlement)
        if is_case_2:
            fee_amt = 100.00
            tax_amt = 50.00
            settled_amt = order_amount - fee_amt - tax_amt  # 4850.00
            
            settlement_id = f"SET-{settlement_counter:04d}"
            settlement_counter += 1
            s_date = p_date + timedelta(days=2)
            
            settlements.append({
                "settlement_id": settlement_id,
                "payment_id": payment_id,
                "settlement_date": s_date.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": settled_amt,
                "status": "SETTLED"
            })
            
            fee_id = f"FEE-{fee_counter:04d}"
            fee_counter += 1
            fees.append({
                "fee_id": fee_id,
                "payment_id": payment_id,
                "fee_amount": fee_amt,
                "tax_amount": tax_amt,
                "total_deduction": fee_amt + tax_amt,
                "fee_type": "GATEWAY_PROCESSING_FEE",
                "created_at": s_date.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            ground_truth.append({
                "order_id": order_id,
                "payment_id": payment_id,
                "category": "VALID_FEE_DEDUCTION",
                "case_id": "CASE_2",
                "description": "Difference explained by valid ₹100 fee and ₹50 tax matching policy",
                "expected_resolution": "AUTO_RESOLVE_VALID_FEE"
            })
            continue

        # Case 5: Refund Mismatch (Payment ₹3,000, Refund recorded for ₹3,500)
        if is_case_5:
            settlement_id = f"SET-{settlement_counter:04d}"
            settlement_counter += 1
            s_date = p_date + timedelta(days=2)
            settlements.append({
                "settlement_id": settlement_id,
                "payment_id": payment_id,
                "settlement_date": s_date.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": order_amount,
                "status": "SETTLED"
            })
            
            refund_id = f"REF-{refund_counter:04d}"
            refund_counter += 1
            refunds.append({
                "refund_id": refund_id,
                "payment_id": payment_id,
                "order_id": order_id,
                "refund_amount": 3500.00,  # Exceeds 3000.00 payment
                "refund_date": (p_date + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "reason": "Customer cancellation",
                "status": "PROCESSED"
            })
            
            ground_truth.append({
                "order_id": order_id,
                "payment_id": payment_id,
                "category": "REFUND_AMOUNT_EXCEPTION",
                "case_id": "CASE_5",
                "description": "Refund amount ₹3,500 exceeds original payment amount ₹3,000",
                "expected_resolution": "REQUIRES_HUMAN_REVIEW"
            })
            continue

        # Case 6: Contradictory Evidence (Discrepancy ₹500, but fee record is only ₹200)
        if is_case_6:
            # Order = 18500, Settlement = 18000, Difference = 500
            settled_amt = order_amount - 500.00
            settlement_id = f"SET-{settlement_counter:04d}"
            settlement_counter += 1
            s_date = p_date + timedelta(days=2)
            
            settlements.append({
                "settlement_id": settlement_id,
                "payment_id": payment_id,
                "settlement_date": s_date.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": settled_amt,
                "status": "SETTLED"
            })
            
            fee_id = f"FEE-{fee_counter:04d}"
            fee_counter += 1
            fees.append({
                "fee_id": fee_id,
                "payment_id": payment_id,
                "fee_amount": 169.49,
                "tax_amount": 30.51,
                "total_deduction": 200.00,  # Explains only 200 of the 500 gap!
                "fee_type": "GATEWAY_PROCESSING_FEE",
                "created_at": s_date.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            ground_truth.append({
                "order_id": order_id,
                "payment_id": payment_id,
                "category": "REQUIRES_HUMAN_REVIEW",
                "case_id": "CASE_6",
                "description": "Observed difference of ₹500 has only ₹200 fee record; remaining ₹300 unexplained",
                "expected_resolution": "REQUIRES_HUMAN_REVIEW"
            })
            continue

        # General distribution transactions (mix of clean matches and fee deductions)
        fee_rate = 0.02
        fee_amt = round(order_amount * fee_rate, 2)
        tax_amt = round(fee_amt * 0.18, 2)
        total_deduction = fee_amt + tax_amt
        settled_amt = round(order_amount - total_deduction, 2)
        
        s_id = f"SET-{settlement_counter:04d}"
        settlement_counter += 1
        s_date = p_date + timedelta(days=2)
        
        settlements.append({
            "settlement_id": s_id,
            "payment_id": payment_id,
            "settlement_date": s_date.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": settled_amt,
            "status": "SETTLED"
        })
        
        f_id = f"FEE-{fee_counter:04d}"
        fee_counter += 1
        fees.append({
            "fee_id": f_id,
            "payment_id": payment_id,
            "fee_amount": fee_amt,
            "tax_amount": tax_amt,
            "total_deduction": total_deduction,
            "fee_type": "GATEWAY_PROCESSING_FEE",
            "created_at": s_date.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Convert to DataFrames
    df_orders = pd.DataFrame(orders)
    df_payments = pd.DataFrame(payments)
    df_settlements = pd.DataFrame(settlements)
    df_fees = pd.DataFrame(fees)
    df_refunds = pd.DataFrame(refunds)
    df_disputes = pd.DataFrame(disputes)
    
    # Save to disk
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_orders.to_csv(DATA_DIR / "orders.csv", index=False)
    df_payments.to_csv(DATA_DIR / "payments.csv", index=False)
    df_settlements.to_csv(DATA_DIR / "settlements.csv", index=False)
    df_fees.to_csv(DATA_DIR / "fees.csv", index=False)
    df_refunds.to_csv(DATA_DIR / "refunds.csv", index=False)
    df_disputes.to_csv(DATA_DIR / "disputes.csv", index=False)
    df_customers.to_csv(DATA_DIR / "customers.csv", index=False)
    
    with open(DATA_DIR / "ground_truth_labels.json", "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)
        
    return {
        "orders_count": len(df_orders),
        "payments_count": len(df_payments),
        "settlements_count": len(df_settlements),
        "fees_count": len(df_fees),
        "refunds_count": len(df_refunds),
        "disputes_count": len(df_disputes),
        "customers_count": len(df_customers),
        "ground_truth_count": len(ground_truth)
    }

if __name__ == "__main__":
    stats = generate_synthetic_data()
    print("Synthetic dataset successfully generated:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
