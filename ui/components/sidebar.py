"""
Sidebar Component for FinRecon UI.
Manages dataset selection, policy knowledge inspection, and workflow triggers.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import streamlit as st

from config import DATA_DIR, KNOWLEDGE_DIR
from tools.data_tools import load_financial_datasets


def render_sidebar() -> Tuple[Dict[str, pd.DataFrame], str, bool]:
    """Renders the configuration and dataset selector sidebar."""
    st.sidebar.title("💳 FinRecon Operations")
    st.sidebar.markdown("**Agentic Reconciliation & Exception Resolution**")

    st.sidebar.divider()
    st.sidebar.subheader("1. Active Financial Data Sources")

    data_status = {
        "Orders (orders.csv)": (DATA_DIR / "orders.csv").exists(),
        "Payments (payments.csv)": (DATA_DIR / "payments.csv").exists(),
        "Settlements (settlements.csv)": (DATA_DIR / "settlements.csv").exists(),
        "Gateway Fees (fees.csv)": (DATA_DIR / "fees.csv").exists(),
        "Refunds (refunds.csv)": (DATA_DIR / "refunds.csv").exists(),
        "Disputes (disputes.csv)": (DATA_DIR / "disputes.csv").exists(),
    }

    for name, exists in data_status.items():
        st.sidebar.checkbox(name, value=exists, disabled=True)

    st.sidebar.subheader("2. Policy Knowledge Base")
    policies = list(KNOWLEDGE_DIR.glob("*.md"))
    for p in policies:
        st.sidebar.text(f"📄 {p.name}")

    st.sidebar.divider()
    st.sidebar.subheader("3. Investigation Scope")
    sample_size = st.sidebar.slider("Batch Size", min_value=10, max_value=1000, value=50, step=10)
    user_prompt = st.sidebar.text_area(
        "Natural Language Objective",
        value="Reconcile payment settlements and investigate discrepancies with policy RAG."
    )

    run_btn = st.sidebar.button("🚀 Run FinRecon Workflow", use_container_width=True, type="primary")

    # Load and slice datasets based on sample size
    datasets = load_financial_datasets(DATA_DIR)
    order_subset = datasets["orders"].iloc[:sample_size].copy()
    order_ids = set(order_subset["order_id"])

    sliced_datasets = {
        "orders": order_subset,
        "payments": datasets["payments"][datasets["payments"]["order_id"].isin(order_ids)].copy(),
        "settlements": datasets["settlements"].copy(),
        "fees": datasets["fees"].copy(),
        "refunds": datasets["refunds"].copy(),
        "disputes": datasets["disputes"].copy(),
        "customers": datasets["customers"].copy(),
    }

    return sliced_datasets, user_prompt, run_btn
