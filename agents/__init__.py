"""
Agents package initialization for FinRecon.
Exposes BaseAgent, PlannerAgent, ValidationAgent, InvestigationAgent,
CriticAgent, and ResolutionAgent.
"""

from agents.base_agent import BaseAgent, AgentResponse
from agents.planner_agent import PlannerAgent, TaskPlanModel
from agents.validation_agent import ValidationAgent
from agents.investigation_agent import InvestigationAgent, InvestigationHypothesis
from agents.critic_agent import CriticAgent, CriticVerdict
from agents.resolution_agent import ResolutionAgent, FinalResolutionReport

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "PlannerAgent",
    "TaskPlanModel",
    "ValidationAgent",
    "InvestigationAgent",
    "InvestigationHypothesis",
    "CriticAgent",
    "CriticVerdict",
    "ResolutionAgent",
    "FinalResolutionReport"
]
