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

def is_screen_black(image: Image.Image) -> bool:
    """Checks if the screenshot is mostly black."""
    try:
        # Convert to numpy array for fast checking
        arr = np.array(image)
        # Check if mean brightness is very low (e.g. < 5)
        return np.mean(arr) < 5
    except Exception:
        return False

def wake_screen():
    """Attempts to wake the screen using xset."""
    try:
        print("DEBUG: Attempting to wake screen with xset...")
        subprocess.run(['xset', 'dpms', 'force', 'on'], check=False)
        subprocess.run(['xset', '-dpms'], check=False) # Disable energy saving
        subprocess.run(['xset', 's', 'off'], check=False) # Disable screensaver
    except Exception as e:
        print(f"WARNING: Failed to run xset: {e}")

def parse_brain_command(plan_text: str) -> dict:
    """Parses direct commands from the Brain, bypassing Vision."""
    plan_text = plan_text.lower()

    # 1. Hotkeys: "Press keys 'ctrl+alt+t'"
    # Regex look for: press key(s) '...' or "..."
    match_keys = re.search(r"press keys? ['\"](.*?)['\"]", plan_text)
    if match_keys:
        keys_str = match_keys.group(1)
        # Split by + or space or comma
        keys = [k.strip() for k in re.split(r'[+, ]', keys_str) if k.strip()]
        return {"type": "hotkey", "keys": keys}

    # 2. Single Key: "Press key 'enter'"
    match_key = re.search(r"press key ['\"](.*?)['\"]", plan_text)
    if match_key:
        return {"type": "key", "content": match_key.group(1)}

    # 3. Type: "Type 'sudo apt update'"
    match_type = re.search(r"type ['\"](.*?)['\"]", plan_text)
    if match_type:
        return {"type": "type", "content": match_type.group(1)}

    return None

def check_self_observation(ocr_text: str) -> str:
    """Detects if the agent is looking at its own log output."""
    markers = ["ENTER OBJECTIVE", "Sovereign Agent", "NEW CYCLE", "brain/planner.py"]
    count = sum(1 for m in markers if m.lower() in ocr_text.lower())

    if count >= 1:
        print("(!) SELF-AWARENESS: I see my own logs. Warning the Brain.")
        return "[SYSTEM WARNING: YOU ARE LOOKING AT YOUR OWN CONSOLE. DO NOT TYPE COMMANDS HERE. OPEN A NEW TERMINAL (CTRL+ALT+T) OR MINIMIZE THIS WINDOW FIRST.]\n\n"
    return ""

def main():
    print("--- SOVEREIGN AGENT V3 (HYBRID ARCHITECTURE) ---")

    # Initialize Components
    memory = ShortTermMemory()
    planner = Planner()
    vision = VisionClient()
    ocr = OCRProcessor()
    motor = Motor()

    # Determine Screen Size (Dynamic)
    try:
        w, h = pyautogui.size()
        print(f"DEBUG: Screen size detected as {w}x{h}")
        if w < 1280 or h < 720:
            print("WARNING: Detected low resolution (headless?). Agent will operate in NATIVE resolution mode.")
    except Exception as e:
        print(f"WARNING: Could not detect screen size: {e}. using default 1920x1080")
        w, h = 1920, 1080

    parser = ActionParser(w, h)
    
    objective = input(">> ENTER OBJECTIVE: ")
    
    while True:
        print("\n--- NEW CYCLE ---")
        cycle_id = datetime.now().strftime("%H%M%S")

        # 1. PERCEPTION
        try:
            screenshot = pyautogui.screenshot()
            # Save debug screenshot
            screenshot.save(f"debug_monitor_{cycle_id}.png")

            # Check for black screen
            if is_screen_black(screenshot):
                print("(!) CRITICAL: Screen appears to be BLACK (off or locked).")
                wake_screen()

        except Exception as e:
            print(f"CRITICAL PERCEPTION ERROR: Could not take screenshot. {e}")
            time.sleep(5)
            continue

        screen_text = ocr.extract_text(screenshot)
        print(f"PERCEPTION (OCR PREVIEW):\n{screen_text[:500]}\n[...]")
        
        if len(screen_text.strip()) == 0:
            print("(!) WARNING: OCR detected 0 characters.")

        # Inject Self-Awareness Warning
        context_warning = check_self_observation(screen_text)
        full_context = context_warning + screen_text

        # 2. PLANNING (Brain)
        high_level_plan = planner.plan_next_step(objective, memory, full_context)

        # 3. GROUNDING OR SHORTCUT (Vision vs Logic)
        action_data = None

        # Check if plan is a direct command (optimization)
        direct_cmd = parse_brain_command(high_level_plan)

        if direct_cmd:
            print(f"DEBUG: Bypassing Vision. Executing direct command: {direct_cmd}")
            action_data = direct_cmd
        else:
            # Use Vision Model to find coordinates
            raw_action = vision.get_action(high_level_plan, screenshot)
            action_data = parser.parse(raw_action)

        # 4. ACTION (Motor)
        if action_data:
            success = motor.execute(action_data)
            status = "SUCCESS" if success else "FAILED"
        else:
            print(f"FAILED to parse action.")
            status = "FAILED PARSING"
            success = False

        # 5. REFLECTION / MEMORY
        memory.add_event(f"State: ... -> Plan: {high_level_plan} -> Action: {action_data} -> Result: {status}")

        if not success and "wait" not in high_level_plan.lower():
            print("(!) Retrying or changing strategy next cycle...")
        
        time.sleep(2)

if __name__ == "__main__":
    main()
