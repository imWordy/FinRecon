"""
Agent Timeline & Activity Feed Component for FinRecon UI.
Visualizes step-by-step multi-agent orchestration execution.
"""

from typing import List, Dict, Any
import streamlit as st


def render_agent_timeline(audit_log: List[Dict[str, Any]]):
    """Renders real-time visual activity feed of agents."""
    st.subheader("🤖 Multi-Agent Orchestration Activity Feed")
    
    if not audit_log:
        st.info("Agent activity feed will appear here once the workflow executes.")
        return

    agent_icons = {
        "PlannerAgent": "🗺️",
        "ValidationAgent": "🛡️",
        "ReconciliationEngine": "⚖️",
        "InvestigationAgent": "🔍",
        "PolicyAgent": "📜",
        "CriticAgent": "🧐",
        "ResolutionAgent": "🎯",
        "ReportingNode": "📊"
    }

    with st.expander(f"Inspect Live Execution Steps ({len(audit_log)} total events)", expanded=False):
        for entry in reversed(audit_log[-15:]):  # Show latest 15 events
            agent = entry.get("agent", "Agent")
            action = entry.get("action", "ACTION")
            ts = entry.get("timestamp", "")[11:19]
            icon = agent_icons.get(agent, "⚡")

            st.markdown(f"**`{ts}`** {icon} **{agent}** &rarr; `{action}`")
            details = entry.get("details", {})
            if isinstance(details, dict) and details:
                # Show key detail preview
                preview = ", ".join(f"{k}: {v}" for k, v in list(details.items())[:3] if not isinstance(v, (dict, list)))
                if preview:
                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;↳ {preview}")
