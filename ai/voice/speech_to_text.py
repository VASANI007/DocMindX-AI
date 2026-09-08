"""
DocMindX AI — Multilingual Speech-to-Text Transcription Module
Supports Gemini Multimodal Audio AI (via GEMINI_API_KEY), Google Cloud Speech-to-Text API,
and resilient SpeechRecognition fallback.
Supports Hindi (hi-IN), Gujarati (gu-IN), English (en-IN/en-US), and regional Indian languages.
"""
import os
import io
import sys
import logging
from typing import Union, BinaryIO

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from config.settings import (
    GEMINI_API_KEY,
    GOOGLE_CLOUD_SPEECH_API_KEY,
    GOOGLE_APPLICATION_CREDENTIALS
)

logger = logging.getLogger("SpeechToText")

# Check if official Google Cloud Speech library is available
try:
    from google.cloud import speech_v1 as speech
    _GCP_SPEECH_AVAILABLE = True
except ImportError:
    _GCP_SPEECH_AVAILABLE = False

# Check if google.generativeai is available
try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

def _extract_audio_bytes(audio_data: Union[str, bytes, BinaryIO]) -> bytes:
    """Extracts raw bytes from various audio input formats (bytes, file, BytesIO, UploadedFile)."""
    if isinstance(audio_data, bytes):
        return audio_data
    elif isinstance(audio_data, str) and os.path.exists(audio_data):
        with open(audio_data, "rb") as f:
            return f.read()
    elif hasattr(audio_data, "read"):
        current_pos = audio_data.tell() if hasattr(audio_data, "tell") else None
        if hasattr(audio_data, "seek"):
            audio_data.seek(0)
        content = audio_data.read()
        if current_pos is not None and hasattr(audio_data, "seek"):
            audio_data.seek(current_pos)
        return content
    elif hasattr(audio_data, "getvalue"):
        return audio_data.getvalue()
    return b""

def transcribe_audio(audio_data: Union[str, bytes, BinaryIO], language_code: str = "hi-IN") -> str:
    """
    Transcribes spoken audio into text.
    Tier 1: Gemini Multimodal Audio AI (uses GEMINI_API_KEY already in .env — no GCP setup needed!)
    Tier 2: Official Google Cloud Speech-to-Text API (if GOOGLE_CLOUD_SPEECH_API_KEY / credentials configured)
    Tier 3: Resilient SpeechRecognition (free local fallback) if offline or keys unconfigured.
    Never crashes the application.
    """
    raw_bytes = _extract_audio_bytes(audio_data)
    if not raw_bytes or len(raw_bytes) < 100:
        logger.debug("Audio data empty or too short for transcription.")
        return ""

    # Normalize language codes
    lang_map = {
        "hi": "hi-IN",
        "gu": "gu-IN",
        "en": "en-IN",
        "mr": "mr-IN",
        "bn": "bn-IN",
        "ta": "ta-IN",
        "te": "te-IN"
    }
    normalized_lang = lang_map.get(language_code, language_code)

    # Detect mime type (WAV by default from st.audio_input)
    mime_type = "audio/wav"
    if raw_bytes.startswith(b"ID3") or raw_bytes.startswith(b"\xff\xfb"):
        mime_type = "audio/mp3"
    elif raw_bytes.startswith(b"OggS"):
        mime_type = "audio/ogg"

    # 1. Primary: Gemini Multimodal Audio Transcription (Uses GEMINI_API_KEY)
    if _GENAI_AVAILABLE and GEMINI_API_KEY and len(GEMINI_API_KEY.strip()) > 5:
        try:
            genai.configure(api_key=GEMINI_API_KEY.strip())
            prompt = (
                f"You are a medical speech-to-text transcriber. "
                f"Accurately transcribe the spoken clinical symptoms or operational notes in this audio into text. "
                f"The spoken language is {normalized_lang} (Hindi, Gujarati, or English). "
                f"Return ONLY the verbatim transcription text without any explanation, markdown headers, or quotes."
            )
            audio_part = {
                "mime_type": mime_type,
                "data": raw_bytes
            }

            # Primary: gemini-3.5-transcribe, with automatic resilient fallbacks
            transcription_models = ["gemini-3.5-transcribe", "gemini-1.5-flash", "gemini-2.0-flash"]
            for m_name in transcription_models:
                try:
                    model = genai.GenerativeModel(m_name)
                    response = model.generate_content([prompt, audio_part])
                    if response and response.text:
                        text = response.text.strip().strip('"\'')
                        if text:
                            logger.info(f"Gemini ({m_name}) transcribed audio: {len(text)} chars ({normalized_lang}).")
                            return text
                except Exception as m_err:
                    logger.debug(f"Gemini model {m_name} attempt: {m_err}")
                    continue
        except Exception as e:
            logger.info(f"Gemini audio transcription notice: {e}. Trying Google Cloud Speech / SpeechRecognition fallback.")

    # 2. Secondary: Official Google Cloud Speech-to-Text API
    has_gcp_creds = bool(GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_CLOUD_SPEECH_API_KEY or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    if _GCP_SPEECH_AVAILABLE and has_gcp_creds:
        try:
            if GOOGLE_CLOUD_SPEECH_API_KEY and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                client = speech.SpeechClient(client_options={"api_key": GOOGLE_CLOUD_SPEECH_API_KEY})
            else:
                client = speech.SpeechClient()

            audio = speech.RecognitionAudio(content=raw_bytes)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                sample_rate_hertz=16000,
                language_code=normalized_lang,
                alternative_language_codes=["en-IN", "hi-IN"],
                enable_automatic_punctuation=True
            )

            response = client.recognize(config=config, audio=audio)
            transcripts = [result.alternatives[0].transcript for result in response.results if result.alternatives]
            if transcripts:
                text = " ".join(transcripts).strip()
                logger.info(f"Google Cloud Speech transcribed {len(text)} characters ({normalized_lang}).")
                return text
        except Exception as e:
            logger.warning(f"Google Cloud Speech API call failed: {e}. Falling back to SpeechRecognition.")

    # 3. Resilient Offline/Free Fallback via SpeechRecognition
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        
        with sr.AudioFile(io.BytesIO(raw_bytes)) as source:
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio = r.record(source)
            
        text = r.recognize_google(audio, language=normalized_lang)
        return text.strip() if text else ""
    except Exception as e:
        logger.info(f"Speech recognition fallback notice: {e}")
        return ""
