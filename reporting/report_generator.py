"""
Comprehensive Report Generator for FinRecon.
Produces human-readable markdown summaries, executive metrics, and
itemized exception dossiers with mathematical equations and policy citations.
"""

from typing import Dict, Any, List
from reporting.evidence_graph import build_evidence_graph_for_exception


def generate_executive_summary_markdown(summary: Dict[str, Any]) -> str:
    """Generates high-level markdown summary report for finance executives."""
    total = summary.get("total_transactions", 0)
    matched = summary.get("matched_count", 0)
    match_rate = summary.get("matched_rate", 0.0)
    exceptions = summary.get("total_exceptions", 0)
    auto_resolved = summary.get("auto_resolved_count", 0)
    human_review = summary.get("human_review_count", 0)

    lines = [
        "# FinRecon — Financial Reconciliation & Resolution Executive Report",
        "",
        "## 1. Executive Operations Summary",
        f"- **Total Processed Transactions**: `{total:,}`",
        f"- **Deterministic Matched**: `{matched:,}` ({match_rate:.2f}%)",
        f"- **Exceptions Flagged for Investigation**: `{exceptions:,}`",
        f"- **AI-Investigated & Auto-Resolved**: `{auto_resolved:,}`",
        f"- **Mandatory Human Review Escalations**: `{human_review:,}`",
        "",
        "## 2. Exception Classification & Decisions",
        "| Exception ID | Order ID | Payment ID | Final Action | Status | Recommended Next Step |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for res in summary.get("resolutions", []):
        eid = res.get("exception_id")
        oid = res.get("order_id")
        pid = res.get("payment_id", "N/A")
        action = res.get("final_action")
        status = "AUTO-RESOLVED" if res.get("is_auto_resolved") else "ESCALATED"
        op = res.get("recommended_operation", "")
        lines.append(f"| `{eid}` | `{oid}` | `{pid}` | `{action}` | **{status}** | {op} |")

    lines.append("")
    lines.append("---")
    lines.append("*Generated automatically by FinRecon Multi-Agent Reconciliation System.*")

    return "\n".join(lines)


def generate_exception_dossier_markdown(
    exception_item: Dict[str, Any],
    hypothesis: Dict[str, Any],
    resolution: Dict[str, Any]
) -> str:
    """Generates an auditable single-case investigation dossier with math equation & policy links."""
    rec = exception_item.get("record", {})
    exc_id = exception_item.get("exception_id")
    graph = build_evidence_graph_for_exception(exception_item, hypothesis, resolution)

    lines = [
        f"# Forensic Investigation Dossier: {exc_id}",
        "",
        "## 1. Transaction Overview",
        f"- **Order ID**: `{rec.get('order_id')}`",
        f"- **Payment ID**: `{rec.get('payment_id')}`",
        f"- **Settlement ID**: `{rec.get('settlement_id')}`",
        f"- **Order Amount**: `₹{rec.get('order_amount', 0.0):.2f}`",
        f"- **Payment Amount**: `₹{rec.get('payment_amount', 0.0):.2f}`",
        f"- **Actual Settlement**: `₹{rec.get('settlement_amount', 0.0):.2f}`",
        f"- **Observed Discrepancy**: `₹{rec.get('discrepancy', 0.0):.2f}`",
        "",
        "## 2. Mathematical Balance & Verification",
        f"> **Equation**: `{graph.formula_text}`",
        ""
    ]

    arith = hypothesis.get("arithmetic_breakdown")
    if arith:
        lines.extend([
            f"- **Formula**: `{arith.get('equation')}`",
            f"- **Variance**: `₹{arith.get('variance', 0.0):.2f}`",
            f"- **Balanced**: `{'YES (0.00 variance)' if arith.get('balanced') else 'NO (Unexplained variance remaining)'}`",
            ""
        ])

    lines.extend([
        "## 3. Governing Policy Citations",
    ])

    for p in hypothesis.get("relevant_policy_chunks", []):
        lines.append(f"### Policy: {p.get('source_file')} — {p.get('header')}")
        lines.append(f"> {p.get('content')}")
        lines.append("")

    lines.extend([
        "## 4. Final Recommendation & Routing",
        f"- **Decision**: `{resolution.get('final_action')}`",
        f"- **Human Escalation**: `{'REQUIRED' if resolution.get('requires_human_escalation') else 'NOT REQUIRED'}`",
        f"- **Summary**: {resolution.get('reasoning_summary')}",
        f"- **Operational Action**: {resolution.get('recommended_operation')}",
        "",
        "## 5. Visual Evidence Lifecycle",
        "```mermaid",
        graph.to_mermaid(),
        "```"
    ])

    return "\n".join(lines)
