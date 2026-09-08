"""
    Medical Document Text Extractor (PDF & Image OCR)
Powered by Gemini Vision AI with robust image optimization, binary filtering, and resilient fallback.
"""
import io
import os
import re
import base64
import requests
from PIL import Image

from config.settings import GEMINI_API_KEY


def _is_binary_garbage(text: str) -> bool:
    """Checks if text contains raw binary EXIF/JFIF/null garbage."""
    if not text:
        return True
    # If text has common image header signatures
    if "JFIF" in text or "Exif" in text or "Photoshop" in text or "<?xpacket" in text:
        return True
    # Count printable characters vs unprintable/weird control characters
    printable_count = sum(1 for c in text if c.isprintable() or c in "\n\r\t")
    if len(text) > 0 and (printable_count / len(text)) < 0.85:
        return True
    return False


def _optimize_image_bytes(file_bytes: bytes) -> tuple[bytes, str]:
    """
    Downsamples large camera photos (e.g. 10MB phone snapshots) to a clean,
    high-DPI JPEG under 1600px max dimension for instant, reliable Vision OCR.
    """
    try:
        img = Image.open(io.BytesIO(file_bytes))
        # Convert RGBA / P to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize if larger than 1600px on either side
        max_dim = max(img.width, img.height)
        if max_dim > 1600:
            scale = 1600 / float(max_dim)
            new_w = int(img.width * scale)
            new_h = int(img.height * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=85, optimize=True)
        return out_buf.getvalue(), "image/jpeg"
    except Exception:
        return file_bytes, "image/jpeg"


def extract_text_from_file(uploaded_file) -> str:
    """
    Extract text content from uploaded PDF or Image using real Gemini Vision OCR.
    Returns clean extracted clinical text or empty string if no valid text found.
    """
    if uploaded_file is None:
        return ""

    file_name = getattr(uploaded_file, "name", "").lower()

    # Reset file pointer to beginning
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    file_bytes = uploaded_file.read()
    if not file_bytes:
        return ""

    # Reset pointer for subsequent reads
    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    is_pdf = file_name.endswith(".pdf")

    # 1. Native PDF Text Extraction (Fastest for digital PDFs)
    if is_pdf:
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            extracted_pdf = ""
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    extracted_pdf += t + "\n"
            if extracted_pdf.strip() and len(extracted_pdf.strip()) > 20 and not _is_binary_garbage(extracted_pdf):
                return extracted_pdf.strip()
        except Exception:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                extracted_pdf = ""
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        extracted_pdf += t + "\n"
                if extracted_pdf.strip() and len(extracted_pdf.strip()) > 20 and not _is_binary_garbage(extracted_pdf):
                    return extracted_pdf.strip()
            except Exception:
                pass

    # 2. Vision OCR for Images & Scanned Documents (via Gemini Vision API)
    if GEMINI_API_KEY:
        opt_bytes, mime_type = (file_bytes, "application/pdf") if is_pdf else _optimize_image_bytes(file_bytes)
        b64_data = base64.b64encode(opt_bytes).decode("utf-8")

        models_to_try = [
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-2.5-flash"
        ]

        prompt = (
            "You are an expert clinical OCR assistant. Transcribe and extract all printed and handwritten text "
            "from this medical document, doctor prescription, diagnostic imaging / radiology report, or laboratory test. "
            "Accurately transcribe all medication names, dosages, timings, doctor notes, radiology findings, "
            "clinical impressions, test parameters, observed values, units, and reference intervals line-by-line.\n"
            "Output ONLY the extracted text."
        )

        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64_data
                                }
                            }
                        ]
                    }],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048}
                }
                headers = {"Content-Type": "application/json"}
                res = requests.post(url, json=payload, headers=headers, timeout=12)
                if res.status_code == 200:
                    candidates = res.json().get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        if text and len(text) >= 5 and not _is_binary_garbage(text):
                            return text
            except Exception:
                pass

    return ""
