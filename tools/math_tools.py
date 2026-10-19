"""
Deterministic mathematical tools for FinRecon.
All monetary calculations, fee balance checks, and rounding verification
are performed strictly in Python without probabilistic model approximation.
"""

from typing import Tuple, Dict, Any, Optional

ROUNDING_TOLERANCE = 0.05

def calculate_discrepancy(expected_amount: float, actual_amount: float) -> float:
    """Calculates absolute or directional discrepancy rounded to 2 decimal places."""
    return round(float(expected_amount) - float(actual_amount), 2)

def verify_fee_arithmetic(
    payment_amount: float,
    fee_amount: float,
    tax_amount: float,
    settlement_amount: float,
    tolerance: float = ROUNDING_TOLERANCE
) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Verifies if: Payment Amount - Fee Amount - Tax Amount == Settlement Amount
    
    Returns:
        (is_valid, variance, breakdown_dict)
    """
    total_deductions = round(float(fee_amount) + float(tax_amount), 2)
    expected_settlement = round(float(payment_amount) - total_deductions, 2)
    variance = round(float(settlement_amount) - expected_settlement, 2)
    
    is_valid = abs(variance) <= tolerance
    
    breakdown = {
        "payment_amount": round(float(payment_amount), 2),
        "fee_amount": round(float(fee_amount), 2),
        "tax_amount": round(float(tax_amount), 2),
        "total_deductions": total_deductions,
        "expected_settlement": expected_settlement,
        "actual_settlement": round(float(settlement_amount), 2),
        "variance": variance,
        "equation": f"{payment_amount:.2f} - {fee_amount:.2f} - {tax_amount:.2f} = {expected_settlement:.2f} (Actual: {settlement_amount:.2f})",
        "balanced": is_valid
    }
    return is_valid, variance, breakdown

def verify_refund_limit(
    original_payment_amount: float,
    refund_amount: float
) -> Tuple[bool, float]:
    """
    Verifies that refund_amount <= original_payment_amount.
    Returns:
        (is_valid, excess_amount)
    """
    excess = round(float(refund_amount) - float(original_payment_amount), 2)
    if excess > 0:
        return False, excess
    return True, 0.0
