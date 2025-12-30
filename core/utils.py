import base64
from io import BytesIO
from PIL import Image

def encode_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    """Converts a PIL Image to a base64 encoded string."""
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def save_debug_image(image: Image.Image, filename: str):
    """Saves an image for debugging purposes."""
    # In a real scenario, check if a debug folder exists
    try:
        image.save(filename)
    except Exception as e:
        print(f"Failed to save debug image: {e}")
