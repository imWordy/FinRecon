"""
Human-in-the-Loop (HITL) Action Dialog Component for FinRecon UI.
Enables finance operators to approve adjustments, dispute charges, or override decisions.
"""

from typing import Dict, Any, Callable
import streamlit as st


def render_hitl_action_box(
    exception_id: str,
    resolution: Dict[str, Any],
    on_action_callback: Callable[[str, str], None]
):
    """Renders human review operational controls for escalated exceptions."""
    if not resolution.get("requires_human_escalation", False):
        st.info("💡 This case was mathematically verified and auto-resolved. Human intervention is not required.")
        return

    st.warning("⚠️ **Human Review Required**: This transaction triggered mandatory escalation.")
    st.markdown(f"**Escalation Reason**: {resolution.get('reasoning_summary')}")
    st.markdown(f"**Recommended Operation**: `{resolution.get('recommended_operation')}`")

    col1, col2, col3 = st.columns(3)

    notes = st.text_input("Reviewer Audit Notes:", value="Reviewed discrepancy against payment gateway logs.")

    with col1:
        if st.button("✅ Approve Fee Adjustment", key=f"btn_approve_{exception_id}", use_container_width=True):
            on_action_callback("APPROVED_FEE_ADJUSTMENT", notes)
            st.success("Fee adjustment approved and recorded to general ledger.")

    with col2:
        if st.button("📩 Escalate to Gateway Desk", key=f"btn_gateway_{exception_id}", use_container_width=True):
            on_action_callback("ESCALATED_TO_GATEWAY_DESK", notes)
            st.info("Automated inquiry ticket dispatched to payment gateway desk.")

    with col3:
        if st.button("🚩 Mark for Fraud Review", key=f"btn_fraud_{exception_id}", use_container_width=True):
            on_action_callback("FLAGGED_FRAUD_INVESTIGATION", notes)
            st.error("Transaction flagged and forwarded to fraud risk operations.")
