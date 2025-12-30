import pyautogui
import time
import subprocess
from typing import Dict, Any
from core.config import config

# Safety Configuration
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 1.0

class Motor:
    def __init__(self):
        pass

    def _normalize_key(self, key_name: str) -> str:
        """
        Normalizes key names to PyAutoGUI standard.
        """
        key = key_name.lower().strip()

        # Enhanced Mapping for Super/Windows key
        mapping = {
            "return": "enter",
            "super": "winleft", # PyAutoGUI uses 'winleft' or 'winright' for Linux usually
            "windows": "winleft",
            "win": "winleft",
            "meta": "winleft",
            "cmd": "winleft",
            "command": "winleft",
            "control": "ctrl",
            "esc": "escape"
        }

        return mapping.get(key, key)

    def execute(self, action_data: Dict[str, Any]) -> bool:
        """
        Executes the parsed action.
        """
        if not action_data:
            print("Action data is empty.")
            return False

        action_type = action_data.get("type")

        try:
            if action_type == "click":
                x, y = action_data["x"], action_data["y"]
                print(f"ACT: Clicking at ({x}, {y})")
                pyautogui.moveTo(x, y, duration=0.5)
                pyautogui.click()
                return True

            elif action_type == "type":
                text = action_data["content"]
                print(f"ACT: Typing '{text}'")
                pyautogui.write(text, interval=0.05)
                return True

            elif action_type == "key":
                raw_key = action_data["content"]
                key = self._normalize_key(raw_key)

                print(f"ACT: Pressing key '{key}' (raw: {raw_key})")
                pyautogui.press(key)
                return True

            elif action_type == "hotkey":
                raw_keys = action_data["keys"]
                keys = [self._normalize_key(k) for k in raw_keys]

                print(f"ACT: Hotkey sequence {keys} (raw: {raw_keys})")
                pyautogui.hotkey(*keys)
                return True

        except Exception as e:
            print(f"ACT Error: {e}")
            return False

        return False
