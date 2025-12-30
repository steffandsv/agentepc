from collections import deque
from typing import List

class ShortTermMemory:
    def __init__(self, max_len: int = 10):
        self.history = deque(maxlen=max_len)

    def add_event(self, description: str):
        """Adds an event to the history."""
        self.history.append(description)

    def get_context(self) -> str:
        """Returns the formatted history context."""
        if not self.history:
            return "No recent history."

        context = "RECENT HISTORY (Last to First):\n"
        for i, event in enumerate(reversed(self.history)):
            context += f"{i+1}. {event}\n"
        return context
