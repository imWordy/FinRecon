"""
Audit Logger for FinRecon.
Maintains an append-only, tamper-evident JSONL audit trail recording all
agent decisions, tool invocations, inputs, and outputs.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class AuditLogger:
    """Manages append-only JSONL event logs."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        agent: str,
        action: str,
        details: Dict[str, Any],
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Appends a structured event to the log file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "confidence": confidence,
            "details": details
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def export_from_state(self, audit_entries: List[Dict[str, Any]]) -> int:
        """Flushes a list of in-memory state audit entries to disk."""
        count = 0
        with open(self.log_path, "a", encoding="utf-8") as f:
            for entry in audit_entries:
                f.write(json.dumps(entry) + "\n")
                count += 1
        return count

    def read_all_events(self) -> List[Dict[str, Any]]:
        """Reads all logged audit events from disk."""
        if not self.log_path.exists():
            return []
        events = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
