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

from config.settings import GEMINI_API_KEY, gemini_pool


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

    # 2. Vision OCR for Images & Scanned Documents (via Gemini Vision Multi-Key Pool)
    if gemini_pool.get_active_keys():
        opt_bytes, mime_type = (file_bytes, "application/pdf") if is_pdf else _optimize_image_bytes(file_bytes)
        b64_data = base64.b64encode(opt_bytes).decode("utf-8")

        models_to_try = [
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.7-flash"
        ]

        prompt = (
            "You are an expert clinical medical vision assistant, diagnostic radiologist, and clinical OCR specialist.\n\n"
            "Analyze this uploaded medical image or document and provide a complete clinical transcription and observation:\n\n"
            "1. IF THIS IS A PRINTED OR HANDWRITTEN MEDICAL DOCUMENT / REPORT:\n"
            "(e.g., Blood/pathology lab report, doctor prescription, printed radiology report, discharge summary, clinical record)\n"
            "- Accurately transcribe all printed and handwritten text line-by-line.\n"
            "- Extract patient details, clinical test parameters, observed values, units, reference intervals, doctor notes, diagnosis, Rx medications, dosage, frequency, and food timings.\n\n"
            "2. IF THIS IS A MEDICAL RADIOGRAPHIC SCAN / DIAGNOSTIC IMAGING IMAGE:\n"
            "(e.g., Chest X-Ray, Bone / Orthopedic / Fracture X-Ray, Dental / OPG X-Ray, Spine X-Ray, CT Scan, HRCT, MRI Scan, Ultrasound / USG, Mammogram)\n"
            "CRITICAL: Even if there is minimal or NO printed text on the scan, DO NOT return empty or say 'No text found'!\n"
            "Instead, perform a thorough clinical radiological inspection and output a structured diagnostic imaging transcription in this exact format:\n"
            "STUDY TYPE / MODALITY: [e.g., Digital Radiograph / Chest X-Ray / Musculoskeletal Bone X-Ray / Dental X-Ray / CT Scan / MRI]\n"
            "ANATOMICAL REGION & VIEW: [e.g., Chest PA/AP View, Right Wrist AP/Lateral, Knee Joint, Lumbar Spine, etc.]\n"
            "RADIOLOGICAL & VISUAL FINDINGS:\n"
            "- [Detailed radiological observation: bone alignment, cortical continuity, fracture line, osteopenia, or joint space narrowing]\n"
            "- [Detailed radiological observation: soft tissues, lung fields, vascular markings, cardiac shadow, diaphragm, consolidation, effusion, or opacity]\n"
            "- [Detailed radiological observation: presence of foreign body, medical hardware, implants, or degenerative changes]\n"
            "CLINICAL IMPRESSION:\n"
            "[Clear, concise radiological impression summarizing primary finding, acute pathology, or normal anatomical study]\n"
            "RECOMMENDATIONS:\n"
            "[Clinical correlation, orthopedic or physician consultation advice, or follow-up imaging if clinically indicated]\n"
            "- Any patient name, dates, or hospital labels visible on the scan borders.\n\n"
            "3. IF THIS IS A MEDICATION PACKAGING, BOTTLE, OR BLISTER PACK:\n"
            "- Transcribe medicine brand name, generic active salts, strength/dosage, manufacturer, and usage instructions.\n\n"
            "Output the clean transcription and clinical findings."
        )

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
        res_data, _, _ = gemini_pool.execute_with_failover(payload=payload, models=models_to_try, timeout=20)
        if res_data:
            candidates = res_data.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                if text and len(text) >= 5 and not _is_binary_garbage(text):
                    return text

    # 3. Local Pytesseract Fallback for printed text (if Gemini Vision is unavailable)
    try:
        import pytesseract
        from PIL import Image
        img_for_tess = Image.open(io.BytesIO(file_bytes))
        tess_text = pytesseract.image_to_string(img_for_tess)
        if tess_text and len(tess_text.strip()) > 15 and not _is_binary_garbage(tess_text):
            return tess_text.strip()
    except Exception:
        pass

    return ""
