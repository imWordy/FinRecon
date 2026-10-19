"""
Interactive Exception Table Component for FinRecon UI.
Displays filterable tabular view of exceptions with status tags and select buttons.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import streamlit as st


def render_exception_table(
    exceptions: List[Dict[str, Any]],
    resolutions: List[Dict[str, Any]]
) -> Optional[int]:
    """Renders interactive exception table and returns the selected exception index."""
    if not exceptions:
        st.success("🎉 No exceptions detected in this dataset batch! 100% matched.")
        return None

    # Merge exception records with resolution data
    res_map = {r.get("exception_id"): r for r in resolutions}
    table_data = []

    for idx, exc in enumerate(exceptions):
        eid = exc.get("exception_id")
        rec = exc.get("record", {})
        res = res_map.get(eid, {})
        
        status_action = res.get("final_action", exc.get("status", "INVESTIGATING"))
        is_auto = res.get("is_auto_resolved", False)

        table_data.append({
            "#": idx + 1,
            "Exception ID": eid,
            "Order ID": rec.get("order_id"),
            "Payment ID": rec.get("payment_id", "N/A"),
            "Expected": f"₹{rec.get('order_amount', 0.0):.2f}",
            "Settled": f"₹{rec.get('settlement_amount', 0.0):.2f}" if rec.get('settlement_amount') is not None else "Missing",
            "Variance": f"₹{rec.get('discrepancy', 0.0):.2f}",
            "Resolution Action": status_action,
            "Routing": "✅ AUTO-RESOLVED" if is_auto else "⚠️ HUMAN REVIEW"
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Selector for investigation dossier
    options = [f"{row['Exception ID']} — {row['Order ID']} ({row['Resolution Action']})" for row in table_data]
    selected_option = st.selectbox("Select Exception Dossier to Inspect:", options=options, index=0)
    
    selected_idx = options.index(selected_option) if selected_option else 0
    return selected_idx
