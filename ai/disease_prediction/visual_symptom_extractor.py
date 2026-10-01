"""
Visual Clinical Symptom & Finding Extractor for DocMindX AI
Powered by Gemini Vision AI with strict Anti-Fabrication & Zero Direct Diagnosis constraints.

Extracts ONLY objective visible findings (e.g., erythema/redness, edema/swelling, rash,
laceration/cut, contusion/bruise, conjunctival injection/eye redness) from clinical photos of
affected anatomical regions. Visual findings are mapped through the Master Symptom Taxonomy
(symptoms_master.csv) to authoritative canonical IDs.
"""
import io
import re
import json
import logging
from typing import Dict, Any, List, Optional
from PIL import Image

from config.settings import gemini_pool, DEFAULT_GEMINI_MODELS
from ai.disease_prediction.canonical_concepts import canonical_normalizer

_logger = logging.getLogger("DocMindX.VisualSymptomExtractor")
_VISION_MODELS = list(DEFAULT_GEMINI_MODELS)


def _safe_parse_json(text: str) -> Optional[dict]:
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass
    return None


def _optimize_clinical_image(image_bytes: bytes) -> tuple[bytes, str]:
    """
    Downsamples clinical photos to a clean JPEG under 1600px dimension
    for fast and reliable Gemini Vision analysis.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        max_dim = max(img.width, img.height)
        if max_dim > 1600:
            scale = 1600 / float(max_dim)
            new_w = int(img.width * scale)
            new_h = int(img.height * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=85, optimize=True)
        return out_buf.getvalue(), "image/jpeg"
    except Exception as exc:
        _logger.warning("[VisualExtractor] Image optimization failed: %s", exc)
        return image_bytes, "image/jpeg"


class VisualSymptomExtractor:
    """
    Multimodal Visual Cue Extractor.
    Extracts objective visual cues from a patient's photo of an affected body area
    and validates them against the Master Symptom Taxonomy.
    """

    SYSTEM_PROMPT = """You are the Clinical Visual Cue Extraction Engine of DocMindX AI.
Your sole job is to examine an image of an affected anatomical area or physical presentation and extract ONLY visible, objective clinical findings.

CRITICAL CLINICAL SAFETY RULES:
1. ZERO DIRECT DISEASE DIAGNOSIS: You MUST NOT diagnose any disease directly (e.g. NEVER output 'Cellulitis', 'Eczema', 'Melanoma', 'Conjunctivitis', 'Psoriasis', 'Fracture').
2. VISUAL EVIDENCE ONLY: Extract only what is clearly visible (e.g. 'Skin Redness', 'Skin Rash', 'Swelling', 'Skin Ulcers', 'Blisters', 'Bruising Easily', 'Cut or Open Wound', 'Eye Redness', 'Yellowing of Skin or Eyes').
3. NO INFERRED SYSTEMIC SYMPTOMS: Do NOT add invisible symptoms such as 'Fever', 'Pain', 'Nausea', 'Headache', or 'Itching'.
4. ANATOMICAL REGION: Identify the visible anatomical region (e.g. 'forearm', 'face', 'knee', 'eye', 'mouth', 'back', 'foot').
5. QUALITY CHECK: If the image is blurry, unrecognizable, or not a clinical photo, indicate in 'image_quality'.

Output strictly valid JSON with this exact structure:
{
  "is_clinical_photo": true,
  "image_quality": "clear",
  "anatomical_region": "forearm",
  "visual_findings": [
    {
      "finding_name": "Skin Redness",
      "location": "forearm",
      "confidence": 0.95,
      "description": "Mild erythema on the anterior forearm"
    },
    {
      "finding_name": "Swelling",
      "location": "forearm",
      "confidence": 0.88,
      "description": "Localized swelling"
    }
  ],
  "visual_summary": "Localized skin redness and swelling visible on the forearm."
}"""

    def extract_visual_symptoms(self, image_bytes: bytes, user_lang: str = "en") -> Dict[str, Any]:
        """
        Analyzes a photo of an affected body region, extracts visual cues,
        and validates them against symptoms_master.csv.
        """
        if not image_bytes:
            return {
                "success": False,
                "error": "No image data provided",
                "visual_findings": [],
                "canonical_symptoms": [],
                "symptom_ids": [],
                "symptom_labels": [],
                "visual_summary": "",
                "fallback_used": True
            }

        opt_bytes, mime_type = _optimize_clinical_image(image_bytes)
        import base64
        b64_img = base64.b64encode(opt_bytes).decode("utf-8")

        prompt = f"{self.SYSTEM_PROMPT}\nAnalyze this clinical image carefully and return the structured JSON."

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": b64_img
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.05,
                "responseMimeType": "application/json"
            }
        }

        parsed_data = None
        fallback_used = False

        if gemini_pool.get_active_keys():
            res_data, model_used, _ = gemini_pool.execute_with_failover(
                payload=payload,
                models=_VISION_MODELS,
                timeout=18
            )
            if res_data:
                candidates = res_data.get("candidates", [])
                if candidates:
                    raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    parsed_data = _safe_parse_json(raw_text)

        if not parsed_data:
            fallback_used = True
            _logger.info("[VisualExtractor] Vision API unavailable or empty; returning graceful empty state")
            return {
                "success": False,
                "error": "Visual AI analysis currently unavailable or unable to process image.",
                "visual_findings": [],
                "canonical_symptoms": [],
                "symptom_ids": [],
                "symptom_labels": [],
                "visual_summary": "Could not extract visual cues automatically. Please describe your symptoms in words.",
                "fallback_used": True
            }

        # Validate findings against master taxonomy
        validated_symptoms = []
        validated_ids = []
        validated_labels = []

        findings_raw = parsed_data.get("visual_findings", [])
        for f in findings_raw:
            fname = str(f.get("finding_name") or "").strip()
            if not fname:
                continue

            # Match against master symptom taxonomy
            match_det = canonical_normalizer.bridge.match_symptom_detailed(fname)
            if match_det.get("dataset_match") and match_det.get("symptom_id"):
                sid = match_det["symptom_id"]
                c_name = match_det.get("dataset_name") or fname
                if sid not in validated_ids:
                    validated_ids.append(sid)
                if c_name not in validated_labels:
                    validated_labels.append(c_name)
                validated_symptoms.append({
                    "symptom_id": sid,
                    "canonical_name": c_name,
                    "raw_finding": fname,
                    "location": f.get("location", ""),
                    "confidence": f.get("confidence", 0.9),
                    "description": f.get("description", ""),
                    "source": "CLINICAL_IMAGE_VISION",
                    "provenance": "GEMINI_VISION_THEN_DATASET_VALIDATED"
                })

        summary = parsed_data.get("visual_summary") or ""
        if not summary and validated_labels:
            summary = f"Identified visible signs: {', '.join(validated_labels)}."

        return {
            "success": True,
            "is_clinical_photo": parsed_data.get("is_clinical_photo", True),
            "image_quality": parsed_data.get("image_quality", "clear"),
            "anatomical_region": parsed_data.get("anatomical_region", ""),
            "visual_findings": findings_raw,
            "canonical_symptoms": validated_symptoms,
            "symptom_ids": validated_ids,
            "symptom_labels": validated_labels,
            "visual_summary": summary,
            "fallback_used": fallback_used
        }


# Global singleton instance
visual_symptom_extractor = VisualSymptomExtractor()
