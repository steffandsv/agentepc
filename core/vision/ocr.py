import pytesseract
from PIL import Image

class OCRProcessor:
    def __init__(self, lang: str = 'eng'):
        self.lang = lang

    def extract_text(self, image: Image.Image) -> str:
        """
        Extracts text from the image using Tesseract.
        Includes basic preprocessing to improve accuracy.
        """
        try:
            # Preprocessing: Convert to grayscale
            gray_image = image.convert('L')

            # Optional: Thresholding (binarization) can help
            # threshold_image = gray_image.point(lambda x: 0 if x < 128 else 255, '1')

            text = pytesseract.image_to_string(gray_image, lang=self.lang)

            # Clean up the text
            clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
            return " ".join(clean_lines)
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def check_exists(self, text_to_find: str, image: Image.Image) -> bool:
        """Checks if a specific string exists in the screen text."""
        full_text = self.extract_text(image)
        return text_to_find.lower() in full_text.lower()
