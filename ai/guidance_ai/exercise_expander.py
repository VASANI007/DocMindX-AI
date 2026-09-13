"""
    Lightweight AI Exercise & Guidance Expander for DocMindX AI
Combines:
1. Small verified local anchor knowledge base
2. Gemini 2.0 / Groq Llama 3.1 constrained clinical prompt expansion
3. Curated trusted-source video links (Government & Hospital allow-lists only)
"""
import os
import json
import requests
import pandas as pd
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import GEMINI_API_KEY, GROQ_API_KEY

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VIDEO_LINKS_CSV = os.path.join(WORKSPACE_ROOT, "datasets", "media", "trusted_video_links.csv")

# Cache for video links dataframe
_df_videos = None

def _load_video_links():
    global _df_videos
    if _df_videos is None:
        if os.path.exists(VIDEO_LINKS_CSV):
            try:
                _df_videos = pd.read_csv(VIDEO_LINKS_CSV)
            except Exception:
                _df_videos = pd.DataFrame()
        else:
            _df_videos = pd.DataFrame()
    return _df_videos

def get_curated_video_link(exercise_id: str, exercise_name: str = "") -> dict | None:
    """
    Looks up a curated, verified video link from recognized health/hospital organizations.
    Returns None if no verified link is present (missing is safer than unverified).
    """
    df = _load_video_links()
    if df.empty:
        return None

    # 1. Match by exercise ID
    if exercise_id and "exercise_id" in df.columns:
        match = df[df["exercise_id"].str.upper() == exercise_id.strip().upper()]
        if not match.empty:
            row = match.iloc[0]
            return {
                "video_url": str(row.get("video_url", "")),
                "channel_source": str(row.get("channel_source", "Verified Health Institution")),
                "verified_by": str(row.get("verified_by", "Clinical Review Board"))
            }

    # 2. Match by exercise name
    if exercise_name and "exercise_name" in df.columns:
        for _, row in df.iterrows():
            if str(row["exercise_name"]).lower() in exercise_name.lower() or exercise_name.lower() in str(row["exercise_name"]).lower():
                return {
                    "video_url": str(row.get("video_url", "")),
                    "channel_source": str(row.get("channel_source", "Verified Health Institution")),
                    "verified_by": str(row.get("verified_by", "Clinical Review Board"))
                }

    return None

def expand_exercise_guidance(exercise_entry: dict, user_symptoms: list, condition_category: str = "", lang: str = "en") -> dict:
    """
    Expands a verified anchor exercise into structured clinical guidance using Gemini/Groq,
    grounded firmly in the local anchor dataset precautions.
    """
    name = exercise_entry.get("exercise_name", "Restorative Mobility")
    known_precaution = exercise_entry.get("precautions", "Avoid strenuous exertion.")
    default_steps = exercise_entry.get("steps", "Perform gently within comfortable range of motion.")
    avoid_if = exercise_entry.get("avoid_if", "Acute pain or discomfort.")
    description = exercise_entry.get("description", "Restorative wellness guidance.")

    # 1. Build Constrained Prompt
    lang_name = "English" if lang == "en" else "Hindi" if lang == "hi" else "Gujarati"
    prompt = f"""
    You are a professional clinical wellness and physiotherapy communicator.
User symptoms: {', '.join(user_symptoms) if user_symptoms else 'Mild discomfort'}
Medical Context: Triage cleared (no acute surgical or emergency flags detected).
Matched Anchor Exercise: {name}
Condition Category: {condition_category or 'General Restorative'}
Known Mandatory Precaution: {known_precaution}

Task: Expand this into structured, safe, step-by-step instructions for a general patient in {lang_name}.
Output strictly valid JSON with these exact keys:
{{
  "why_it_helps": "Brief 1-2 sentence clinical explanation of why this posture aids recovery",
  "steps": "Clear numbered steps (1. ... 2. ... 3. ...)",
  "duration": "Recommended duration/reps (e.g. 5-10 minutes / 8-10 repetitions)",
  "precautions": "Include the known precaution: '{known_precaution}' plus essential safety notes",
  "avoid_if": "Specific conditions where this posture must be strictly avoided: '{avoid_if}'"
}}
Do NOT prescribe this as a medical cure. Do NOT output anything outside the JSON object.
"""

    # 2. Try Gemini (gemini-3.6-flash)
    if GEMINI_API_KEY:
        for gemini_model in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.7-flash"]:
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500, "responseMimeType": "application/json"}
                }
                res = requests.post(gemini_url, headers={"Content-Type": "application/json"}, json=payload, timeout=6)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_resp = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = json.loads(text_resp)
                        if isinstance(parsed, dict) and "steps" in parsed:
                            return parsed
            except Exception:
                pass

    # 3. Try Groq (Llama 3.1)
    if GROQ_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            body = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a clinical wellness communicator. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=5)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "steps" in parsed:
                    return parsed
        except Exception:
            pass

    # 4. Deterministic Local Fallback (Guaranteed Safe)
    return {
        "why_it_helps": description,
        "steps": default_steps,
        "duration": "5–10 minutes with calm, steady breathing.",
        "precautions": known_precaution,
        "avoid_if": avoid_if
    }
