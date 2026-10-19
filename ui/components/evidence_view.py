"""
Evidence and Investigation View Component for FinRecon UI.
Visualizes the transaction dossier, mathematical formula, RAG policy citations,
and Mermaid directed graph.
"""

from typing import Dict, Any, List
import streamlit as st

from reporting.evidence_graph import build_evidence_graph_for_exception


def render_evidence_view(
    exception_item: Dict[str, Any],
    hypothesis: Dict[str, Any],
    resolution: Dict[str, Any]
):
    """Renders comprehensive investigation dossier for an individual exception."""
    rec = exception_item.get("record", {})
    exc_id = exception_item.get("exception_id")
    graph = build_evidence_graph_for_exception(exception_item, hypothesis, resolution)

    st.markdown(f"### 🔍 Investigation Dossier: `{exc_id}` ({rec.get('order_id')})")

    col_meta, col_math = st.columns([1, 1])

    with col_meta:
        st.markdown("**Transaction Identifiers**")
        st.write(f"- **Order ID**: `{rec.get('order_id')}`")
        st.write(f"- **Payment ID**: `{rec.get('payment_id', 'N/A')}`")
        st.write(f"- **Settlement ID**: `{rec.get('settlement_id', 'N/A')}`")
        st.write(f"- **Gross Captured**: `₹{rec.get('payment_amount', 0.0):.2f}`")
        st.write(f"- **Net Settlement**: `₹{rec.get('settlement_amount', 0.0):.2f}`")
        st.write(f"- **Discrepancy**: `₹{rec.get('discrepancy', 0.0):.2f}`")

    with col_math:
        st.markdown("**Deterministic Math Verification**")
        arith = hypothesis.get("arithmetic_breakdown")
        if arith:
            if arith.get("balanced"):
                st.success(f"✅ Balanced: `{arith.get('equation')}`")
            else:
                st.error(f"❌ Mismatch: `{arith.get('equation')}` (Variance: ₹{arith.get('variance', 0.0):.2f})")
        else:
            st.info(f"Formula: `{graph.formula_text}`")

        st.markdown("**AI Agent Decision**")
        action = resolution.get("final_action", "UNKNOWN")
        if resolution.get("is_auto_resolved"):
            st.success(f"Action: **{action}** (Auto-Resolved)")
        else:
            st.warning(f"Action: **{action}** (Escalated to Human)")

    # Mermaid Evidence Graph
    st.markdown("**Visual Transaction Evidence Flow**")
    st.markdown(f"```mermaid\n{graph.to_mermaid()}\n```")

    # Policy RAG Citations
    policies = hypothesis.get("relevant_policy_chunks", [])
    if policies:
        st.markdown("**📜 Retrieved Institutional Policy Citations**")
        for p in policies:
            with st.expander(f"Policy: {p.get('source_file')} — {p.get('header')}"):
                st.markdown(p.get("content"))
                st.caption(f"Relevance Score: {p.get('relevance_score', 0.0)}")
