import json
import os
import time
from dataclasses import dataclass
from typing import Optional, Dict

STATE_FILE = "agent_state.json"

@dataclass
class AgentState:
    objective: Optional[str] = None
    status: str = "IDLE"  # IDLE, WORKING, WAITING, COMPLETED, STOPPED
    last_updated: float = 0.0
    last_log: str = ""

class StateManager:
    def __init__(self, filepath=STATE_FILE):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            self.save_state(AgentState())

    def save_state(self, state: AgentState):
        data = {
            "objective": state.objective,
            "status": state.status,
            "last_updated": time.time(),
            "last_log": state.last_log
        }
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def get_state(self) -> AgentState:
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            return AgentState(
                objective=data.get("objective"),
                status=data.get("status", "IDLE"),
                last_updated=data.get("last_updated", 0.0),
                last_log=data.get("last_log", "")
            )
        except (json.JSONDecodeError, FileNotFoundError):
            return AgentState()

    def set_objective(self, objective: str):
        state = self.get_state()
        state.objective = objective
        state.status = "WORKING"
        self.save_state(state)

    def clear_objective(self):
        state = self.get_state()
        state.objective = None
        state.status = "IDLE"
        self.save_state(state)

    def update_status(self, status: str, log_entry: str = ""):
        state = self.get_state()
        state.status = status
        if log_entry:
            state.last_log = log_entry
        self.save_state(state)
