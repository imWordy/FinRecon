"""
Evidence Graph Builder for FinRecon.
Constructs directed node-edge structures tracing the full financial transaction lifecycle:
Order -> Payment(s) -> Deductions (Fees/Taxes) -> Settlement(s) -> Resolution.
Exports to JSON and Mermaid diagram formats.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # "order", "payment", "deduction", "settlement", "dispute", "refund", "resolution"
    amount: Optional[float] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str
    relation: str


class EvidenceGraph(BaseModel):
    exception_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    formula_text: str = ""

    def to_mermaid(self) -> str:
        """Generates a Mermaid graph TD diagram representation."""
        lines = ["flowchart TD"]
        for node in self.nodes:
            amt_str = f"\\n₹{node.amount:.2f}" if node.amount is not None else ""
            stat_str = f"\\n({node.status})" if node.status else ""
            clean_label = node.label.replace('"', "'")
            lines.append(f'    {node.id}["{clean_label}{amt_str}{stat_str}"]')

        for edge in self.edges:
            lines.append(f'    {edge.source} -->|"{edge.label}"| {edge.target}')

        return "\n".join(lines)


def build_evidence_graph_for_exception(
    exception_item: Dict[str, Any],
    hypothesis: Optional[Dict[str, Any]] = None,
    resolution: Optional[Dict[str, Any]] = None
) -> EvidenceGraph:
    """Builds a structured evidence graph for a specific reconciliation exception."""
    rec = exception_item.get("record", {})
    exc_id = exception_item.get("exception_id", "EXC-UNKNOWN")
    oid = rec.get("order_id", "ORD-UNKNOWN")
    pid = rec.get("payment_id")
    sid = rec.get("settlement_id")

    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []
    formula_parts = []

    # 1. Order Node
    o_node_id = f"node_{oid.replace('-', '_')}"
    nodes.append(GraphNode(
        id=o_node_id,
        label=f"Order {oid}",
        type="order",
        amount=rec.get("order_amount"),
        status="PLACED"
    ))

    # 2. Payment Node
    if pid:
        p_node_id = f"node_{pid.replace('-', '_')}"
        p_amount = rec.get("payment_amount", 0.0)
        nodes.append(GraphNode(
            id=p_node_id,
            label=f"Payment {pid}",
            type="payment",
            amount=p_amount,
            status="CAPTURED"
        ))
        edges.append(GraphEdge(
            source=o_node_id,
            target=p_node_id,
            label="captured",
            relation="FULFILLS"
        ))
        formula_parts.append(f"Payment ₹{p_amount:.2f}")

    # 3. Deductions & Evidence Items
    if hypothesis:
        for ev in hypothesis.get("evidence_trail", []):
            ev_type = ev.get("type")
            data = ev.get("data", {})
            if ev_type == "fee_record":
                fee_id = data.get("fee_id", "FEE")
                f_node_id = f"node_{fee_id.replace('-', '_')}"
                fee_amt = data.get("fee_amount", 0.0)
                tax_amt = data.get("tax_amount", 0.0)
                tot_ded = data.get("total_deduction", fee_amt + tax_amt)

                nodes.append(GraphNode(
                    id=f_node_id,
                    label=f"Gateway Fee + Tax\\n(₹{fee_amt:.2f} + ₹{tax_amt:.2f})",
                    type="deduction",
                    amount=tot_ded,
                    status="DEDUCTED"
                ))
                if pid:
                    edges.append(GraphEdge(
                        source=p_node_id,
                        target=f_node_id,
                        label="deducts fee",
                        relation="DEDUCTION"
                    ))
                formula_parts.append(f"- Fee/Tax ₹{tot_ded:.2f}")

            elif ev_type == "refund_record":
                ref_id = data.get("refund_id", "REF")
                r_node_id = f"node_{ref_id.replace('-', '_')}"
                ref_amt = data.get("refund_amount", 0.0)
                nodes.append(GraphNode(
                    id=r_node_id,
                    label=f"Refund {ref_id}",
                    type="refund",
                    amount=ref_amt,
                    status=data.get("status", "PROCESSED")
                ))
                if pid:
                    edges.append(GraphEdge(
                        source=p_node_id,
                        target=r_node_id,
                        label="refunded",
                        relation="REFUND"
                    ))

            elif ev_type == "dispute_record":
                disp_id = data.get("dispute_id", "DISP")
                d_node_id = f"node_{disp_id.replace('-', '_')}"
                nodes.append(GraphNode(
                    id=d_node_id,
                    label=f"Dispute {disp_id}\\n({data.get('claim_reason', 'Dispute')})",
                    type="dispute",
                    status=data.get("status", "OPEN")
                ))
                if pid:
                    edges.append(GraphEdge(
                        source=p_node_id,
                        target=d_node_id,
                        label="disputed",
                        relation="DISPUTE"
                    ))

    # 4. Settlement Node
    if sid:
        s_node_id = f"node_{sid.replace('-', '_')}"
        s_amount = rec.get("settlement_amount", 0.0)
        nodes.append(GraphNode(
            id=s_node_id,
            label=f"Settlement {sid}",
            type="settlement",
            amount=s_amount,
            status="SETTLED"
        ))
        if pid:
            edges.append(GraphEdge(
                source=p_node_id,
                target=s_node_id,
                label="settles to merchant",
                relation="SETTLEMENT"
            ))
        formula_parts.append(f"= Settlement ₹{s_amount:.2f}")

    # 5. Resolution Node
    if resolution:
        res_node_id = f"node_res_{exc_id.replace('-', '_')}"
        res_action = resolution.get("final_action", "UNKNOWN")
        nodes.append(GraphNode(
            id=res_node_id,
            label=f"Resolution: {res_action}",
            type="resolution",
            status="RESOLVED" if resolution.get("is_auto_resolved") else "ESCALATED"
        ))
        parent = s_node_id if sid else (p_node_id if pid else o_node_id)
        edges.append(GraphEdge(
            source=parent,
            target=res_node_id,
            label="routed to",
            relation="RESOLUTION"
        ))

    formula_str = " ".join(formula_parts) if formula_parts else f"Discrepancy: ₹{rec.get('discrepancy', 0.0):.2f}"

    return EvidenceGraph(
        exception_id=exc_id,
        nodes=nodes,
        edges=edges,
        formula_text=formula_str
    )
