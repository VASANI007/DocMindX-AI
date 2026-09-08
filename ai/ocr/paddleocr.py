"""
    DocMindX AI - Advanced OCR Pipeline Integration
Provides fallback OCR capabilities for scanned prescriptions and medical charts.
"""
from PIL import Image
import pytesseract
from ai.ocr.image_cleaner import preprocess_medical_image

def extract_text_advanced_ocr(image_input) -> str:
    """
    Applies image preprocessing and executes optical character recognition.
    Falls back gracefully if specific binary OCR tools are uninstalled.
    """
    try:
        cleaned_img = preprocess_medical_image(image_input)
        text = pytesseract.image_to_string(cleaned_img, config="--psm 6")
        if text and text.strip():
            return text.strip()
    except Exception as e:
        print(f"OCR Pipeline note: {e}")

    try:
        # Direct raw extraction fallback
        if isinstance(image_input, Image.Image):
            return pytesseract.image_to_string(image_input).strip()
    except Exception:
        pass

    return ""
