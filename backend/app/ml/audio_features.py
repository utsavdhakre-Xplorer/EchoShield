"""
Audio feature extractor for acoustic anomaly and voice characteristics.

Extracts standard acoustic descriptors using librosa:
  - MFCCs  — speaker spectral envelope and timbral variation
  - ZCR    — zero crossing rate (frequency/noisiness indicator)
  - Spectral centroid — brightness / spectral center of mass
  - RMS energy variance — speech dynamics (human vs synthetic flatness)

Note: Acoustic heuristics provide anomaly indicators and should not be treated
as conclusive deepfake verification on their own.
"""

from __future__ import annotations
import os
import logging
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)


def extract_audio_features(audio_path: str) -> Dict[str, Any]:
    """
    Extract acoustic features from an audio file.

    Args:
        audio_path: Path to a 16kHz mono WAV file.

    Returns:
        {
            "synthetic_voice_probability": float,
            "is_speech_present": bool,
            "zcr_mean": float,
            "spectral_centroid_mean": float,
            "rms_variance": float,
            "mfcc_std_mean": float,
        }
    """
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
        return _empty_result()

    try:
        import librosa  # type: ignore

        y, sr = librosa.load(audio_path, sr=16000, mono=True)

        if len(y) < int(sr * 0.4):  # less than 0.4 seconds — skip
            return _empty_result()

        # Check for silence or near-silence: do not flag silence as synthetic voice
        peak_amp = float(np.max(np.abs(y)))
        if peak_amp < 0.01:
            return _empty_result(is_speech_present=False)

        # 1. Zero Crossing Rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = float(np.mean(zcr))

        # 2. Spectral Centroid
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = float(np.mean(centroid))
        centroid_std = float(np.std(centroid))

        # 3. RMS Energy variance
        rms = librosa.feature.rms(y=y)[0]
        rms_var = float(np.var(rms))
        rms_mean = float(np.mean(rms))

        # If overall RMS is negligible, speech is not present
        if rms_mean < 0.005:
            return _empty_result(is_speech_present=False)

        # 4. MFCC spread
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_std_mean = float(np.mean(np.std(mfccs, axis=1)))

        # ── Acoustic Anomaly Heuristic ────────────────────────────────────────
        # Calibrated acoustic anomaly indicator:
        # High-quality natural human speech has dynamic energy variation (rms_var > 0.002)
        # and natural spectral variation (centroid_std > 300, mfcc_std_mean > 8.0).
        score = 0.0

        if rms_var < 0.0003:
            score += 0.20
        elif rms_var < 0.001:
            score += 0.10

        if centroid_std < 150:
            score += 0.20
        elif centroid_std < 350:
            score += 0.10

        if mfcc_std_mean < 4.0:
            score += 0.20
        elif mfcc_std_mean < 8.0:
            score += 0.10

        # Highly unnatural spectral centroid or extreme ZCR
        if zcr_mean > 0.20:
            score += 0.15

        score = round(min(score, 0.85), 4)

        logger.info(
            f"[AudioFeatures] zcr={zcr_mean:.4f}, centroid_std={centroid_std:.1f}, "
            f"rms_var={rms_var:.6f}, mfcc_std={mfcc_std_mean:.2f} → anomaly_score={score:.3f}"
        )

        return {
            "synthetic_voice_probability": score,
            "is_speech_present": True,
            "zcr_mean": round(zcr_mean, 4),
            "spectral_centroid_mean": round(centroid_mean, 2),
            "rms_variance": round(rms_var, 6),
            "mfcc_std_mean": round(mfcc_std_mean, 4),
        }

    except Exception as e:
        logger.error(f"[AudioFeatures] Feature extraction failed: {e}")
        return _empty_result()


def _empty_result(is_speech_present: bool = False) -> Dict[str, Any]:
    return {
        "synthetic_voice_probability": 0.0,
        "is_speech_present": is_speech_present,
        "zcr_mean": 0.0,
        "spectral_centroid_mean": 0.0,
        "rms_variance": 0.0,
        "mfcc_std_mean": 0.0,
    }
