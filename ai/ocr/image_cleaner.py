"""
    DocMindX AI - Image Cleaning and Preprocessing for Medical OCR
"""
import io
from PIL import Image, ImageEnhance, ImageFilter

def preprocess_medical_image(image_input) -> Image.Image:
    """
    Cleans, contrast-boosts, and sharpens scanned medical reports,
    prescriptions, and lab documents for optimal OCR text extraction.
    """
    if isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, str):
        img = Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        img = image_input
    else:
        raise ValueError("Unsupported image input type")

    # Convert to RGB then Grayscale
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    gray = img.convert("L")

    # Contrast enhancement for handwritten and faded print
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.8)

    # Sharpness enhancement
    sharp_enhancer = ImageEnhance.Sharpness(enhanced)
    sharpened = sharp_enhancer.enhance(1.5)

    return sharpened

def deskew_and_binarize(img: Image.Image, threshold: int = 150) -> Image.Image:
    """Applies binarization thresholding to isolate dark text from light paper."""
    gray = img.convert("L")
    return gray.point(lambda p: 255 if p > threshold else 0, "1")
