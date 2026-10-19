"""
Base Agent and Model Abstraction for FinRecon.
Provides a unified interface across local Ollama, cloud LLMs, or deterministic mock modes.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from config import LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL


class AgentResponse(BaseModel):
    agent_name: str
    status: str
    data: Dict[str, Any]
    thought_process: str
    confidence: float = 1.0


class BaseAgent(ABC):
    """Abstract base class for all specialized FinRecon agents."""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.provider = LLM_PROVIDER

    @abstractmethod
    def run(self, inputs: Dict[str, Any]) -> AgentResponse:
        """Executes agent task and returns structured AgentResponse."""
        pass

    def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generic LLM caller supporting Ollama HTTP endpoint or fallback mock generator.
        """
        if self.provider == "ollama":
            import urllib.request
            url = f"{OLLAMA_BASE_URL}/api/generate"
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": system_prompt or "",
                "stream": False
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    return res_json.get("response", "")
            except Exception as e:
                # Fallback to local rule reasoning if Ollama is unreachable
                return f"[FALLBACK_LOCAL_REASONING]: {str(e)}"

        # Default internal mock mode returns structured response
        return ""
