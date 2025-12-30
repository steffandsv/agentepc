from unittest.mock import MagicMock
from PIL import Image

class MockOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = MagicMock()
        self.chat.completions.create.return_value = self._mock_response()

    def _mock_response(self):
        mock_msg = MagicMock()
        mock_msg.message.content = "Click on the Terminal icon"

        mock_choice = MagicMock()
        mock_choice.choices = [mock_msg]
        return mock_choice

class MockOllama:
    def chat(self, model, messages):
        instruction = messages[0]['content']
        # Simulate UI-TARS response
        if "Terminal" in instruction:
            return {'message': {'content': "Action: click(point='<point>100 200</point>')"}}
        return {'message': {'content': "Action: click(point='<point>500 500</point>')"}}

class MockPyAutoGUI:
    def screenshot(self):
        return Image.new('RGB', (1920, 1080), color='white')

    def size(self):
        return (1920, 1080)

    def moveTo(self, x, y, duration=0):
        print(f"MOCK MOVE: {x}, {y}")

    def click(self):
        print("MOCK CLICK")

    def write(self, text, interval=0):
        print(f"MOCK WRITE: {text}")

    def press(self, key):
        print(f"MOCK PRESS: {key}")

class MockPytesseract:
    def image_to_string(self, image, lang=None):
        return "user@host:~$ Desktop Documents Downloads"
