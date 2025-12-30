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
                key = action_data["content"].lower()
                # Map some common discrepancies
                key_map = {
                    "return": "enter",
                    "super": "win",
                    "windows": "win",
                    "control": "ctrl"
                }
                key = key_map.get(key, key)

                print(f"ACT: Pressing key '{key}'")
                pyautogui.press(key)
                return True

            elif action_type == "hotkey":
                keys = action_data["keys"]
                # Clean up keys
                key_map = {
                    "return": "enter",
                    "super": "win",
                    "windows": "win",
                    "control": "ctrl"
                }
                keys = [key_map.get(k.lower(), k.lower()) for k in keys]

                print(f"ACT: Hotkey sequence {keys}")
                pyautogui.hotkey(*keys)
                return True

        except Exception as e:
            print(f"ACT Error: {e}")
            return False

        return False

    def special_action(self, action_name: str) -> bool:
        """Handles special high-level actions that might need lower level access."""
        if action_name == "open_terminal":
             # Fallback if clicking fails
             print("ACT: Launching terminal via hotkey")
             pyautogui.hotkey('ctrl', 'alt', 't')
             return True
        return False
