"""
KPI Header Component for FinRecon Dashboard.
Renders high-level financial operational metrics cards.
"""

from typing import Dict, Any
import streamlit as st


def render_kpi_cards(summary: Dict[str, Any]):
    """Renders 4 executive KPI metrics cards."""
    total = summary.get("total_transactions", 0)
    matched = summary.get("matched_count", 0)
    exceptions = summary.get("total_exceptions", 0)
    auto_resolved = summary.get("auto_resolved_count", 0)
    human_review = summary.get("human_review_count", 0)
    match_rate = summary.get("matched_rate", 0.0)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="Total Transactions",
            value=f"{total:,}",
            help="Total order and payment records processed in current batch"
        )
    with c2:
        st.metric(
            label="Cleanly Matched",
            value=f"{matched:,}",
            delta=f"{match_rate:.1f}% rate",
            help="Zero-discrepancy identical transactions"
        )
    with c3:
        st.metric(
            label="Exceptions Detected",
            value=f"{exceptions:,}",
            delta=f"{exceptions} flagged" if exceptions > 0 else "None",
            delta_color="inverse",
            help="Transactions with differences, missing files, or duplicates"
        )
    with c4:
        st.metric(
            label="AI Auto-Resolved",
            value=f"{auto_resolved:,}",
            delta=f"{human_review} Escalated to Human",
            delta_color="off",
            help="Cases resolved via policy RAG vs escalated for human review"
        )
