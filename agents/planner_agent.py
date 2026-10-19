"""
Planner Agent for FinRecon.
Decomposes natural language financial reconciliation requests into structured,
executable task steps and data dependency graphs.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from agents.base_agent import BaseAgent, AgentResponse


class TaskPlanModel(BaseModel):
    objective: str
    required_datasets: List[str]
    tasks: List[str]
    estimated_steps: int
    routing_strategy: str


class PlannerAgent(BaseAgent):
    """Interprets user prompt and produces structured execution plan."""

    def __init__(self):
        super().__init__(name="PlannerAgent", role="Workflow Orchestrator & Task Planner")

    def run(self, inputs: Dict[str, Any]) -> AgentResponse:
        user_request = inputs.get("user_request", "Reconcile transactions and investigate exceptions.")
        
        # Deconstruct request based on semantic keywords
        req_lower = user_request.lower()
        datasets = ["orders", "payments", "settlements"]
        if "fee" in req_lower or "deduction" in req_lower or "mismatch" in req_lower:
            datasets.append("fees")
        if "refund" in req_lower:
            datasets.append("refunds")
        if "dispute" in req_lower or "duplicate" in req_lower or "charge" in req_lower:
            datasets.append("disputes")
            datasets.append("customers")

        # Always ensure minimum relational datasets
        all_required = list(set(datasets + ["orders", "payments", "settlements"]))

        tasks = [
            "validate_datasets_schema",
            "execute_matching_hierarchy",
            "isolate_reconciliation_exceptions",
            "investigate_exception_evidence",
            "retrieve_governing_policies",
            "critic_adversarial_validation",
            "route_resolution_or_escalation",
            "compile_audit_report"
        ]

        plan = TaskPlanModel(
            objective=user_request,
            required_datasets=all_required,
            tasks=tasks,
            estimated_steps=len(tasks),
            routing_strategy="HYBRID_LANGGRAPH_CONDITIONAL"
        )

        thought = (
            f"Parsed user request: '{user_request}'. Identified {len(all_required)} dataset dependencies. "
            f"Generated an 8-stage deterministic-agentic pipeline plan."
        )

        return AgentResponse(
            agent_name=self.name,
            status="SUCCESS",
            data=plan.model_dump(),
            thought_process=thought,
            confidence=1.0
        )
