import os
# Ensure Display is set before importing pyautogui
os.environ["DISPLAY"] = ":0"

import time
import pyautogui
from datetime import datetime
from core.config import config
from core.brain.planner import Planner
from core.brain.memory import ShortTermMemory
from core.vision.client import VisionClient
from core.vision.parser import ActionParser
from core.vision.ocr import OCRProcessor
from core.action.motor import Motor

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
    except Exception as e:
        print(f"WARNING: Could not detect screen size: {e}. using default 1920x1080")
        w, h = 1920, 1080

    parser = ActionParser(w, h)
    
    objective = input(">> ENTER OBJECTIVE: ")
    
    while True:
        print("\n--- NEW CYCLE ---")
        cycle_id = datetime.now().strftime("%H%M%S")

        # 1. PERCEPTION
        screenshot = pyautogui.screenshot()
        # Save debug screenshot
        screenshot.save(f"debug_monitor_{cycle_id}.png")
        print(f"DEBUG: Saved screenshot to debug_monitor_{cycle_id}.png")

        screen_text = ocr.extract_text(screenshot)
        print(f"PERCEPTION (OCR PREVIEW):\n{screen_text[:500]}\n[...]")
        
        # 2. PLANNING (Brain)
        high_level_plan = planner.plan_next_step(objective, memory, screen_text)

        # 3. GROUNDING (Vision)
        raw_action = vision.get_action(high_level_plan, screenshot)
        action_data = parser.parse(raw_action)

        # 4. ACTION (Motor)
        if action_data:
            success = motor.execute(action_data)
            status = "SUCCESS" if success else "FAILED"
        else:
            print(f"FAILED to parse action from: {raw_action}")
            status = "FAILED PARSING"
            success = False

        # 5. REFLECTION / MEMORY
        memory.add_event(f"State: ... -> Plan: {high_level_plan} -> Action: {raw_action} -> Result: {status}")
        
        if not success and "wait" not in high_level_plan.lower():
            print("(!) Retrying or changing strategy next cycle...")
        
        time.sleep(2)

if __name__ == "__main__":
    main()
