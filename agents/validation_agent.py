"""
Data Validation Agent for FinRecon.
Performs pre-flight data sanity, schema verification, null key checks,
and integrity validation before downstream agents reason over data.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent, AgentResponse
from tools.data_tools import validate_dataset_schemas


class ValidationAgent(BaseAgent):
    """Guards against malformed, incomplete, or corrupted financial data."""

    def __init__(self):
        super().__init__(name="ValidationAgent", role="Financial Data Integrity Guard")

    def run(self, inputs: Dict[str, Any]) -> AgentResponse:
        datasets = inputs.get("datasets", {})
        if not datasets:
            return AgentResponse(
                agent_name=self.name,
                status="FAILED",
                data={"is_valid": False, "errors": ["No datasets provided for validation."]},
                thought_process="Validation failed: Input datasets dictionary was empty.",
                confidence=1.0
            )

        report = validate_dataset_schemas(datasets)
        is_valid = report["is_valid"]
        status = "SUCCESS" if is_valid else "FAILED"

        thought = (
            f"Validated {len(datasets)} tables. Schema status: {'PASS' if is_valid else 'FAIL'}. "
            f"Found {len(report.get('errors', []))} errors and {len(report.get('warnings', []))} warnings."
        )

        return AgentResponse(
            agent_name=self.name,
            status=status,
            data=report,
            thought_process=thought,
            confidence=1.0 if is_valid else 0.0
        )
