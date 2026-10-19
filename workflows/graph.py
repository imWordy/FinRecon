"""
LangGraph Multi-Agent Orchestration State Graph for FinRecon.
Assembles Planner, Validator, Reconciler, Investigator, Critic, Resolver, and Reporter
nodes into a compiled, stateful, auditable workflow.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from workflows.state import FinReconState
from workflows.nodes import (
    plan_node,
    validate_node,
    reconcile_node,
    investigate_node,
    critic_node,
    resolve_node,
    report_node
)
from workflows.edges import (
    route_after_reconciliation,
    route_after_resolution
)


def build_reconciliation_graph() -> StateGraph:
    """Builds and wires the full FinRecon multi-agent state graph."""
    builder = StateGraph(FinReconState)

    # 1. Register Nodes
    builder.add_node("planner", plan_node)
    builder.add_node("validator", validate_node)
    builder.add_node("reconciler", reconcile_node)
    builder.add_node("investigate", investigate_node)
    builder.add_node("critic", critic_node)
    builder.add_node("resolver", resolve_node)
    builder.add_node("report", report_node)

    # 2. Add Fixed Edges
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "validator")
    builder.add_edge("validator", "reconciler")

    # 3. Add Conditional Edge after Reconciler
    builder.add_conditional_edges(
        "reconciler",
        route_after_reconciliation,
        {
            "investigate": "investigate",
            "report": "report"
        }
    )

    # 4. Sequential Investigation Loop: Investigate -> Critic -> Resolver
    builder.add_edge("investigate", "critic")
    builder.add_edge("critic", "resolver")

    # 5. Conditional Edge after Resolver: More exceptions to investigate?
    builder.add_conditional_edges(
        "resolver",
        route_after_resolution,
        {
            "investigate": "investigate",
            "report": "report"
        }
    )

    # 6. Final Edge
    builder.add_edge("report", END)

    return builder


def compile_reconciliation_workflow():
    """Compiles the state graph into an executable runnable."""
    graph = build_reconciliation_graph()
    return graph.compile()


def run_finrecon_pipeline(
    datasets: Dict[str, Any],
    user_request: str = "Reconcile transaction records and investigate discrepancies."
) -> FinReconState:
    """High-level runner executing the compiled LangGraph workflow end-to-end."""
    app = compile_reconciliation_workflow()
    initial_state: FinReconState = {
        "user_request": user_request,
        "datasets": datasets,
        "audit_log": []
    }
    final_state = app.invoke(initial_state)
    return final_state
