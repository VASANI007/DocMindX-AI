"""
DocMindX AI — Multilingual Text-to-Speech Audio Synthesis Module
Powered by official Google Cloud Text-to-Speech API with resilient gTTS fallback.
Synthesizes speech into base64 audio data URI for seamless browser playback.
"""
import os
import io
import sys
import base64
import re
import logging
from typing import Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from config.settings import GOOGLE_CLOUD_SPEECH_API_KEY, GOOGLE_APPLICATION_CREDENTIALS

logger = logging.getLogger("TextToSpeech")

# Check if official Google Cloud Text-to-Speech library is available
try:
    from google.cloud import texttospeech_v1 as texttospeech
    _GCP_TTS_AVAILABLE = True
except ImportError:
    _GCP_TTS_AVAILABLE = False

def synthesize_speech(text: str, lang: str = "en") -> str:
    """
    Synthesizes speech into an in-memory base64 audio string for browser playback.
    Primary: Official Google Cloud Text-to-Speech API.
    Fallback: gTTS (Google Text-to-Speech free tier).
    """
    if not text or not text.strip():
        return ""

    # Clean markdown formatting before speech
    clean = re.sub(r"[\*\_#`~>]", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    truncated_text = clean[:350]

    # Map language codes
    lang_code_map = {
        "hi": "hi-IN",
        "gu": "gu-IN",
        "en": "en-IN",
        "mr": "mr-IN",
        "bn": "bn-IN",
        "ta": "ta-IN",
        "te": "te-IN"
    }
    gcp_lang = lang_code_map.get(lang, "en-IN")

    # 1. Official Google Cloud Text-to-Speech
    has_gcp_creds = bool(GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CLOUD_SPEECH_API_KEY or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    if _GCP_TTS_AVAILABLE and has_gcp_creds:
        try:
            if GOOGLE_CLOUD_SPEECH_API_KEY and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                client = texttospeech.TextToSpeechClient(client_options={"api_key": GOOGLE_CLOUD_SPEECH_API_KEY})
            else:
                client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=truncated_text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=gcp_lang,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.95
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
            logger.info(f"Google Cloud TTS generated audio ({gcp_lang}).")
            return f"data:audio/mp3;base64,{audio_b64}"
        except Exception as e:
            logger.warning(f"Google Cloud TTS API call failed: {e}. Falling back to gTTS.")

    # 2. Resilient gTTS Fallback
    try:
        from gtts import gTTS
        gtts_lang = "hi" if lang == "hi" else ("gu" if lang == "gu" else "en")
        tts = gTTS(text=truncated_text, lang=gtts_lang, slow=False)
        
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_b64 = base64.b64encode(fp.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{audio_b64}"
    except Exception as e:
        logger.warning(f"TTS synthesis notice: {e}")
        return ""
