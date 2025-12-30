import pytesseract
from PIL import Image
import os

class OCRProcessor:
    def __init__(self, lang: str = 'eng'):
        self.lang = lang

    def extract_text(self, image: Image.Image) -> str:
        try:
            # DEBUG: Salvar o que o OCR está vendo
            image.save("debug_ocr_input.png")
            
            # Converter para escala de cinza
            gray_image = image.convert('L')
            
            # Tentar extrair texto
            text = pytesseract.image_to_string(gray_image, lang=self.lang)
            
            # Se vazio, alerta no log
            if not text.strip():
                print("(!) OCR WARNING: Image appears empty or textless.")
                
            clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
            return " ".join(clean_lines)

        except pytesseract.TesseractNotFoundError:
            print("CRITICAL ERROR: Tesseract is not installed or not in PATH.")
            print("Install via: sudo apt install tesseract-ocr")
            return ""
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def check_exists(self, text_to_find: str, image: Image.Image) -> bool:
        full_text = self.extract_text(image)
        return text_to_find.lower() in full_text.lower()