import os
# Ensure Display is set before importing pyautogui
os.environ["DISPLAY"] = ":0"

import time
import re
import pyautogui
import subprocess
import numpy as np
from datetime import datetime
from PIL import Image
from core.config import config
from core.brain.planner import Planner
from core.brain.memory import ShortTermMemory
from core.vision.client import VisionClient
from core.vision.parser import ActionParser
from core.vision.ocr import OCRProcessor
from core.action.motor import Motor
from core.state import StateManager

def is_screen_black(image: Image.Image) -> bool:
    """Checks if the screenshot is mostly black."""
    try:
        arr = np.array(image)
        return np.mean(arr) < 5
    except Exception:
        return False

def wake_screen():
    """Attempts to wake the screen using xset."""
    try:
        print("DEBUG: Attempting to wake screen with xset...")
        subprocess.run(['xset', 'dpms', 'force', 'on'], check=False)
        subprocess.run(['xset', '-dpms'], check=False)
        subprocess.run(['xset', 's', 'off'], check=False)
    except Exception as e:
        print(f"WARNING: Failed to run xset: {e}")

def parse_brain_command(plan_text: str) -> dict:
    """Parses direct commands from the Brain, bypassing Vision."""
    plan_text = plan_text.lower()

    if "wait" in plan_text:
        return {"type": "wait"}

    # 1. Hotkeys
    match_keys = re.search(r"press keys? ['\"](.*?)['\"]", plan_text)
    if match_keys:
        keys_str = match_keys.group(1)
        keys = [k.strip() for k in re.split(r'[+, ]', keys_str) if k.strip()]
        return {"type": "hotkey", "keys": keys}

    # 2. Single Key
    match_key = re.search(r"press key ['\"](.*?)['\"]", plan_text)
    if match_key:
        return {"type": "key", "content": match_key.group(1)}

    # 3. Type
    match_type = re.search(r"type ['\"](.*?)['\"]", plan_text)
    if match_type:
        return {"type": "type", "content": match_type.group(1)}

    return None

def check_self_observation(ocr_text: str) -> str:
    """Detects if the agent is looking at its own log output."""
    markers = ["Sovereign Agent", "NEW CYCLE", "brain/planner.py", "core/state.py"]
    count = sum(1 for m in markers if m.lower() in ocr_text.lower())

    if count >= 1:
        print("(!) SELF-AWARENESS: I see my own logs.")
        return "[SYSTEM WARNING: YOU ARE LOOKING AT YOUR OWN CONSOLE. DO NOT TYPE COMMANDS HERE. MINIMIZE THIS WINDOW (SUPER+D) OR WAIT.]\n\n"
    return ""

def main():
    print("--- SOVEREIGN AGENT V3 (DAEMON MODE) ---")
    print("[*] Waiting for commands via core/state.py...")

    # Ensure static directory exists
    if not os.path.exists("static"):
        os.makedirs("static")

    # Initialize Components
    memory = ShortTermMemory()
    planner = Planner()
    vision = VisionClient()
    ocr = OCRProcessor()
    motor = Motor()
    state_manager = StateManager()

    # Determine Screen Size
    try:
        w, h = pyautogui.size()
        print(f"DEBUG: Screen size detected as {w}x{h}")
    except Exception as e:
        print(f"WARNING: Could not detect screen size: {e}. using default 1920x1080")
        w, h = 1920, 1080

    parser = ActionParser(w, h)
    
    # Main Loop (Daemon)
    while True:
        state = state_manager.get_state()

        # 1. CHECK STATE
        if not state.objective or state.status == "STOPPED":
            if state.status != "IDLE" and state.status != "STOPPED":
                 state_manager.update_status("IDLE", "Waiting for new objective...")
            time.sleep(5)
            continue

        objective = state.objective
        print(f"\n--- NEW CYCLE (Obj: {objective}) ---")
        state_manager.update_status("WORKING", f"Cycle started at {datetime.now().strftime('%H:%M:%S')}")

        # 2. PERCEPTION
        try:
            screenshot = pyautogui.screenshot()

            # Save for Web UI
            try:
                screenshot.save("static/latest_monitor.png")
            except Exception as save_err:
                print(f"WARNING: Could not save monitor image: {save_err}")

            if is_screen_black(screenshot):
                print("(!) CRITICAL: Screen appears to be BLACK.")
                wake_screen()
                state_manager.update_status("WARNING", "Screen Black - Attempting Wake")
                time.sleep(2)
                continue # Retry next loop

        except Exception as e:
            print(f"CRITICAL PERCEPTION ERROR: {e}")
            state_manager.update_status("ERROR", f"Perception failed: {e}")
            time.sleep(5)
            continue

        screen_text = ocr.extract_text(screenshot)
        
        # Inject Self-Awareness Warning
        context_warning = check_self_observation(screen_text)
        full_context = context_warning + screen_text

        # 3. PLANNING
        high_level_plan = planner.plan_next_step(objective, memory, full_context)
        state_manager.update_status("PLANNING", f"Plan: {high_level_plan}")

        # 4. GROUNDING / ACTION
        action_data = None
        direct_cmd = parse_brain_command(high_level_plan)

        if direct_cmd:
            print(f"DEBUG: Executing direct command: {direct_cmd}")
            action_data = direct_cmd
        else:
            raw_action = vision.get_action(high_level_plan, screenshot)
            action_data = parser.parse(raw_action)

        # 5. EXECUTION
        success = False
        if action_data:
            if action_data.get("type") == "wait":
                print("Action: WAIT")
                success = True
            else:
                success = motor.execute(action_data)

        status_msg = "SUCCESS" if success else "FAILED"

        # 6. MEMORY & LOGGING
        memory.add_event(f"Plan: {high_level_plan} -> Action: {action_data} -> Result: {status_msg}")
        state_manager.update_status("EXECUTING", f"Action: {high_level_plan} ({status_msg})")

        if not success and "wait" not in high_level_plan.lower():
             print("(!) Action failed, retrying next cycle...")
        
        time.sleep(2)

if __name__ == "__main__":
    main()
