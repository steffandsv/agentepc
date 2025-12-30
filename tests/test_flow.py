import sys
import os
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.append(os.getcwd())

# 1. Mock pyautogui and its sub-dependencies BEFORE importing anything that uses them
# This prevents the "Connect to Display" error because the real module is never loaded.
mock_pyautogui = MagicMock()
mock_pyautogui.FAILSAFE = True
mock_pyautogui.PAUSE = 1.0
mock_pyautogui.screenshot.return_value = MagicMock()
mock_pyautogui.size.return_value = (1920, 1080)
sys.modules['pyautogui'] = mock_pyautogui

# Mock mouseinfo as well since it's often the culprit for X11 checks
sys.modules['mouseinfo'] = MagicMock()

# Now imports from tests.mock_apis which defines the behavior we want
from tests.mock_apis import MockOpenAI, MockOllama, MockPytesseract

# Now we can safely import our core modules.
# They will see the mocked pyautogui in sys.modules.
with patch('openai.OpenAI', side_effect=MockOpenAI), \
     patch('ollama.chat', side_effect=MockOllama().chat), \
     patch('pytesseract.image_to_string', side_effect=MockPytesseract().image_to_string):

    from core.brain.planner import Planner
    from core.brain.memory import ShortTermMemory
    from core.vision.client import VisionClient
    from core.vision.parser import ActionParser
    from core.vision.ocr import OCRProcessor
    from core.action.motor import Motor

    def test_cycle():
        print("--- STARTING TEST CYCLE ---")

        # Setup
        memory = ShortTermMemory()
        planner = Planner()
        vision = VisionClient()
        ocr = OCRProcessor()
        motor = Motor()
        parser = ActionParser(1920, 1080)

        # 1. Perception
        print("Testing Perception...")
        # Since we mocked the module, we need to set the return value for the instance call used in code if needed
        # But our MockPyAutoGUI in mock_apis was slightly different structure.
        # Let's just rely on the sys.modules mock we set up above, but configure it.

        # Configure the mock image for OCR
        from PIL import Image
        mock_img = Image.new('RGB', (100, 100), color='white')
        mock_pyautogui.screenshot.return_value = mock_img

        img = mock_pyautogui.screenshot()
        text = ocr.extract_text(img)
        # Verify OCR was called (it uses pytesseract which we patched)
        assert "user@host" in text
        print("Perception OK.")

        # 2. Planning
        print("Testing Planning...")
        plan = planner.plan_next_step("Open Terminal", memory, text)
        assert "Terminal" in plan
        print(f"Planning OK. Plan: {plan}")

        # 3. Grounding
        print("Testing Grounding...")
        raw_action = vision.get_action(plan, img)
        print(f"Raw Action: {raw_action}")
        action_data = parser.parse(raw_action)
        assert action_data['type'] == 'click'
        # Scale check: 100/1000 * 1920 = 192
        assert action_data['x'] == 192
        print(f"Grounding OK. Parsed: {action_data}")

        # 4. Execution
        print("Testing Execution...")
        motor.execute(action_data)
        # Verify pyautogui.moveTo was called on our sys.module mock
        mock_pyautogui.moveTo.assert_called()
        mock_pyautogui.click.assert_called()
        print("Execution OK.")

        print("--- TEST CYCLE COMPLETE ---")

    if __name__ == "__main__":
        test_cycle()
