import ollama
from typing import Optional
from core.config import config
from core.utils import encode_image_to_base64
from PIL import Image

class VisionClient:
    def __init__(self, model_name: str = config.MODEL_VISION):
        self.model_name = model_name

    def get_action(self, instruction: str, image: Image.Image) -> str:
        """
        Sends the image and instruction to the local Vision model (Ollama).
        Returns the raw text response.
        """
        img_b64 = encode_image_to_base64(image)

        try:
            # UI-TARS specific prompt structure can be enforced here if needed,
            # but usually the user prompt "Instruction: ..." is enough for fine-tuned models.
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': f"Instruction: {instruction}",
                    'images': [img_b64]
                }]
            )
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Vision API Error: {e}")
            return ""
