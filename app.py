"""
FinRecon — Agentic Financial Transaction Reconciliation & Exception Resolution System
Main Streamlit Application Entrypoint.
"""

import sys
from pathlib import Path
import streamlit as st

# Setup Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from workflows.graph import run_finrecon_pipeline
from ui.components.sidebar import render_sidebar
from ui.components.kpi_metrics import render_kpi_cards
from ui.components.exception_table import render_exception_table
from ui.components.agent_timeline import render_agent_timeline
from ui.components.evidence_view import render_evidence_view
from ui.components.hitl_modal import render_hitl_action_box
from reporting.audit_logger import AuditLogger

# Page Config
st.set_page_config(
    page_title="FinRecon | Agentic Financial Reconciliation",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Custom Styling
css_file = BASE_DIR / "ui" / "styles.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def init_session():
    """Initializes session state memory."""
    if "pipeline_state" not in st.session_state:
        st.session_state.pipeline_state = None
    if "human_actions" not in st.session_state:
        st.session_state.human_actions = []


def main():
    init_session()

    st.markdown('<div class="main-header">💳 FinRecon Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Multi-Agent Financial Transaction Reconciliation, Policy RAG & Exception Resolution</div>',
        unsafe_allow_html=True
    )

    # 1. Render Sidebar & Fetch Data
    datasets, user_prompt, run_btn = render_sidebar()

    # 2. Pipeline Execution
    if run_btn or st.session_state.pipeline_state is None:
        with st.spinner("🤖 Coordinating Multi-Agent LangGraph Workflow..."):
            pipeline_state = run_finrecon_pipeline(datasets, user_request=user_prompt)
            st.session_state.pipeline_state = pipeline_state

    state = st.session_state.pipeline_state
    summary = state.get("summary_report", {})
    exceptions = state.get("exceptions", [])
    resolutions = state.get("resolutions", [])
    audit_log = state.get("audit_log", [])

    # 3. KPI Header Cards
    render_kpi_cards(summary)
    st.divider()

    # 4. Agent Execution Activity Timeline
    render_agent_timeline(audit_log)
    st.divider()

    # 5. Main Split View: Exception Table (Left) & Forensic Dossier (Right)
    col_table, col_dossier = st.columns([1.1, 1.3])

    with col_table:
        st.subheader("📋 Reconciliation Exception Queue")
        selected_idx = render_exception_table(exceptions, resolutions)

    with col_dossier:
        if exceptions and selected_idx is not None and selected_idx < len(exceptions):
            curr_exc = exceptions[selected_idx]
            curr_eid = curr_exc.get("exception_id")
            
            # Match resolution
            res = next((r for r in resolutions if r.get("exception_id") == curr_eid), {
                "exception_id": curr_eid,
                "order_id": curr_exc.get("record", {}).get("order_id"),
                "final_action": "REQUIRES_HUMAN_REVIEW",
                "is_auto_resolved": False,
                "requires_human_escalation": True,
                "reasoning_summary": curr_exc.get("preliminary_reason"),
                "recommended_operation": "Inspect transaction manually."
            })
            
            # Match hypothesis if available in audit or state
            hyp = {
                "exception_id": curr_eid,
                "investigated_category": curr_exc.get("status"),
                "root_cause": curr_exc.get("preliminary_reason"),
                "evidence_trail": [],
                "arithmetic_breakdown": None,
                "relevant_policy_chunks": []
            }

            # Render Dossier
            render_evidence_view(curr_exc, hyp, res)

            # Render Human In The Loop Box
            def on_human_action(action_type: str, notes: str):
                logger = AuditLogger(BASE_DIR / "data" / "reconciliation_audit.jsonl")
                entry = logger.log_event(
                    agent="HumanReviewer",
                    action=action_type,
                    details={"exception_id": curr_eid, "notes": notes}
                )
                st.session_state.human_actions.append(entry)

            st.divider()
            render_hitl_action_box(curr_eid, res, on_human_action)
        else:
            st.info("Select an exception from the queue to inspect evidence.")


if __name__ == "__main__":
    main()
