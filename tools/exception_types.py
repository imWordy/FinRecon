"""
Exception and status models for FinRecon.
Defines strongly-typed schemas for transaction states, reconciliation matches,
and exception classifications.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    MISSING_SETTLEMENT = "MISSING_SETTLEMENT"
    MISSING_PAYMENT = "MISSING_PAYMENT"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    REFUND_MISMATCH = "REFUND_MISMATCH"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    UNKNOWN = "UNKNOWN"


class ResolutionAction(str, Enum):
    AUTO_RESOLVE_MATCHED = "AUTO_RESOLVE_MATCHED"
    AUTO_RESOLVE_VALID_FEE = "AUTO_RESOLVE_VALID_FEE"
    FLAG_SUSPECTED_DUPLICATE = "FLAG_SUSPECTED_DUPLICATE"
    ESCALATE_GATEWAY_SETTLEMENT = "ESCALATE_GATEWAY_SETTLEMENT"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"
    INVESTIGATING = "INVESTIGATING"


class ReconciliationRecord(BaseModel):
    order_id: str
    payment_id: Optional[str] = None
    settlement_id: Optional[str] = None
    customer_id: Optional[str] = None
    order_amount: float
    payment_amount: Optional[float] = None
    settlement_amount: Optional[float] = None
    discrepancy: float = 0.0
    status: ReconciliationStatus
    matching_stage: str  # e.g., "EXACT_PAYMENT_ID", "ORDER_ID", "WINDOW_FALLBACK"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExceptionItem(BaseModel):
    exception_id: str
    record: ReconciliationRecord
    detected_at_stage: str
    preliminary_reason: str
    status: ReconciliationStatus
    resolved: bool = False
    resolution_action: Optional[ResolutionAction] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
