"""
WebSocket endpoint for real-time audio streaming and scam detection.

Mobile client connects to:
    ws://<host>/ws/analyze?token=<JWT>

Protocol:
  - Client sends raw binary audio frames (PCM 16kHz mono int16)
  - Server buffers frames (~5s chunks), processes with:
      1. Whisper transcription
      2. Deepfake detection & acoustic feature analysis
      3. Contextual scam tactic detection
      4. Threat classification & response
"""

import asyncio
import io
import json
import logging
import struct
import tempfile
import os
import wave
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt

from app.core.security import SECRET_KEY, ALGORITHM
from app.services.transcription import transcribe_audio
from app.services.scam_detector import detect_scam_tactics
from app.services.deepfake_detector import detect_deepfake
from app.services.threat_classifier import classify_threat
from app.services.negotiator import generate_negotiator_strategy
from app.ml.audio_features import extract_audio_features

logger = logging.getLogger(__name__)
router = APIRouter()

# Buffer ~5 seconds of 16kHz mono int16 PCM
_SAMPLE_RATE = 16000
_CHUNK_SECONDS = 5
_BUFFER_SIZE = _SAMPLE_RATE * _CHUNK_SECONDS * 2  # 2 bytes per int16 sample
_MIN_BUFFER_SIZE = _SAMPLE_RATE * 1 * 2          # 1 second minimum for residual flush


def _verify_token(token: str) -> Optional[str]:
    """Return user_id if token is valid, else None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def _process_audio_buffer(pcm_bytes: bytes, chunk_idx: int) -> dict:
    """Write PCM to a temp WAV file and run the full detection pipeline."""
    # Ensure even number of bytes for 16-bit PCM
    if len(pcm_bytes) % 2 != 0:
        pcm_bytes = pcm_bytes[:-1]

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp_path = f.name

    # Write WAV safely after temp file descriptor is closed
    with wave.open(tmp_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # int16
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(pcm_bytes)

    try:
        transcript = await transcribe_audio(tmp_path)
        deepfake_result = await detect_deepfake(tmp_path, pcm_bytes)
        audio_features = extract_audio_features(tmp_path)
        scam_result = await detect_scam_tactics(transcript)

        threat = classify_threat(
            deepfake_confidence=deepfake_result["confidence"],
            is_deepfake=deepfake_result["is_deepfake"],
            urgency_score=scam_result["urgency_score"],
            urgency_detected=scam_result["urgency_detected"],
            deepfake_verified=deepfake_result.get("model_verified", False),
            tactics_detected=scam_result.get("tactics_detected"),
        )
        strategy = await generate_negotiator_strategy(transcript, threat["threat_level"])

        threat_level_str = (
            threat["threat_level"].value
            if hasattr(threat["threat_level"], "value")
            else str(threat["threat_level"])
        )

        return {
            "chunk_index": chunk_idx,
            "transcript": transcript,
            "is_deepfake": deepfake_result["is_deepfake"],
            "deepfake_confidence": deepfake_result["confidence"],
            "deepfake_verified": deepfake_result.get("model_verified", False),
            "synthetic_voice_probability": audio_features.get("synthetic_voice_probability", 0.0),
            "urgency_detected": scam_result["urgency_detected"],
            "urgency_score": scam_result["urgency_score"],
            "urgency_phrases_found": scam_result["phrases_found"],
            "tactics_detected": scam_result.get("tactics_detected", []),
            "overall_threat_score": threat["overall_score"],
            "threat_level": threat_level_str,
            "threat_factors": threat.get("threat_factors", []),
            "negotiator_strategy": strategy,
            "alert_required": threat["alert_required"],
        }
    except Exception as e:
        logger.error(f"[WS] Processing error on chunk {chunk_idx}: {e}")
        return {
            "chunk_index": chunk_idx,
            "error": str(e),
            "transcript": "",
            "threat_level": "LOW",
            "overall_threat_score": 0.0,
            "alert_required": False,
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@router.websocket("/ws/analyze")
async def ws_analyze(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    """
    Real-time binary audio streaming endpoint.
    Accepts PCM int16 at 16kHz mono, returns JSON threat results every 5s.
    """
    user_id = _verify_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    logger.info(f"[WS] Client connected: user={user_id}")

    audio_buffer = bytearray()
    chunk_idx = 0

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=30.0)
            except asyncio.TimeoutError:
                logger.info("[WS] Timeout — no audio received for 30s, closing.")
                break

            audio_buffer.extend(data)

            if len(audio_buffer) >= _BUFFER_SIZE:
                pcm_chunk = bytes(audio_buffer[:_BUFFER_SIZE])
                audio_buffer = audio_buffer[_BUFFER_SIZE:]

                result = await _process_audio_buffer(pcm_chunk, chunk_idx)
                chunk_idx += 1

                await websocket.send_text(json.dumps(result))
                logger.info(
                    f"[WS] Chunk {chunk_idx} → threat={result.get('threat_level')} "
                    f"score={result.get('overall_threat_score', 0):.3f}"
                )

        # Process any residual audio on graceful loop termination
        if len(audio_buffer) >= _MIN_BUFFER_SIZE:
            pcm_chunk = bytes(audio_buffer)
            audio_buffer.clear()
            final_result = await _process_audio_buffer(pcm_chunk, chunk_idx)
            await websocket.send_text(json.dumps(final_result))

    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"[WS] Unexpected error: {e}")
    finally:
        logger.info(f"[WS] Session ended for user={user_id}, processed {chunk_idx} chunks")
