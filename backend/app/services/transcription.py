import os
import logging
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Thread pool for blocking operations
_executor = ThreadPoolExecutor(max_workers=2)

# Try to import whisper; fall back gracefully for environments without it
try:
    import whisper
    _WHISPER_MODEL = None
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None  # type: ignore
    _WHISPER_MODEL = None
    WHISPER_AVAILABLE = False
    logger.warning("openai-whisper not installed. Speech transcription will be unavailable.")


def _get_model():
    """Lazy load Whisper model with error handling."""
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None and WHISPER_AVAILABLE:
        model_size = os.getenv("WHISPER_MODEL", "base")
        logger.info(f"Loading Whisper model: {model_size}")
        _WHISPER_MODEL = whisper.load_model(model_size)
    return _WHISPER_MODEL


def _transcribe_sync(audio_path: str) -> str:
    """Synchronous transcription using Whisper."""
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
        logger.warning(f"Audio file {audio_path} is missing or too small to transcribe.")
        return ""

    if not WHISPER_AVAILABLE:
        # Check if mock transcription is explicitly enabled for testing
        if os.getenv("MOCK_TRANSCRIPTION", "false").lower() in ["true", "1"]:
            return _test_mock_transcription()
        return "[Transcription unavailable: Whisper not installed]"

    try:
        model = _get_model()
        if model is None:
            return ""
        result = model.transcribe(audio_path, fp16=False, language="en")
        transcript = result.get("text", "").strip()
        logger.info(f"Transcribed {len(transcript)} characters from {audio_path}")
        return transcript if transcript else "[No speech detected]"
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return ""


async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file to text using OpenAI Whisper (async-safe)."""
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
        return ""

    try:
        loop = asyncio.get_event_loop()
        transcript = await asyncio.wait_for(
            loop.run_in_executor(_executor, _transcribe_sync, audio_path),
            timeout=30.0,
        )
        return transcript
    except asyncio.TimeoutError:
        logger.error(f"Transcription timeout on {audio_path}")
        return ""
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""


def _test_mock_transcription() -> str:
    """Deterministic mock transcription solely for explicit unit test mock mode."""
    return "This is a simulated incoming phone call for test verification."
