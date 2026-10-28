from typing import Dict, Any, List, Optional
from app.models.call_log import ThreatLevel
import logging

logger = logging.getLogger(__name__)


def classify_threat(
    deepfake_confidence: float,
    is_deepfake: bool,
    urgency_score: float,
    urgency_detected: bool,
    deepfake_verified: bool = False,
    tactics_detected: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Combine deepfake detection and conversational scam tactics into a unified threat classification.
    
    Principles:
    1. Scam urgency/coercion is the primary threat vector. A human scammer is just as dangerous
       as an AI scammer; a real human voice must never dilute a severe scam score.
    2. Deepfake detection is evaluated only when backed by a verified model. Unverified or
       unavailable deepfake models are isolated and never drag down threat scores.
    3. When deepfake is verified:
       - AI voice + scam tactics escalates to a CRITICAL threat (sophisticated synthetic attack).
       - AI voice without scam tactics indicates automated IVR/assistant (capped at MEDIUM).
       - Human voice + scam tactics maintains the full severity of the scam tactics.
    """
    factors: List[str] = []

    # 1. Evaluate Scam Intent
    scam_score = max(0.0, min(urgency_score, 1.0))
    if tactics_detected:
        factors.append(f"Scam tactics identified ({len(tactics_detected)}): {', '.join(tactics_detected)}")
    elif urgency_detected or scam_score >= 0.40:
        factors.append(f"Elevated scam urgency detected (score: {scam_score:.2f})")
    else:
        factors.append("No predatory scam tactics or coercion identified in transcript")

    # 2. Evaluate Voice Authenticity / Deepfake Risk
    if not deepfake_verified:
        # Deepfake model is unverified / unavailable: isolate from calculation
        combined = scam_score
        factors.append("Voice authenticity: unverified (deepfake detector checkpoint not loaded)")
    else:
        # Deepfake model is verified
        if is_deepfake and urgency_detected:
            # Synthetic voice combined with scam tactics = severe multi-vector attack
            combined = min(max(scam_score, 0.75) + 0.20, 1.0)
            factors.append(
                f"Escalation: Verified synthetic/deepfake voice ({deepfake_confidence:.2f}) "
                "used in conjunction with predatory scam tactics"
            )
        elif is_deepfake and not urgency_detected:
            # Synthetic voice in benign context (automated notification, IVR, TTS)
            combined = min(deepfake_confidence * 0.40, 0.45)
            factors.append(
                f"Synthetic voice detected ({deepfake_confidence:.2f}) without scam tactics "
                "(likely automated IVR / voice assistant)"
            )
        else:
            # Verified natural human voice: does not reduce human scammer risk
            combined = scam_score
            factors.append(f"Voice authenticity verified: natural speech (synthetic prob: {deepfake_confidence:.2f})")

    # 3. Determine Threat Level & Alerting Thresholds
    combined = round(max(0.0, min(combined, 1.0)), 4)

    if combined >= 0.80:
        level = ThreatLevel.CRITICAL
        alert_required = True
        factors.append("CRITICAL THREAT: Immediate interception or caller disconnection advised")
    elif combined >= 0.55:
        level = ThreatLevel.HIGH
        alert_required = True
        factors.append("HIGH RISK: Likely fraudulent call. Caution and verification advised")
    elif combined >= 0.35:
        level = ThreatLevel.MEDIUM
        alert_required = False
        factors.append("MEDIUM: Suspicious indicators present. Proceed with caution")
    else:
        level = ThreatLevel.LOW
        alert_required = False
        factors.append("LOW: Standard conversational dialogue without imminent risk")

    logger.info(
        f"Threat classification: combined={combined:.3f}, level={level}, "
        f"alert={alert_required}, verified_df={deepfake_verified}"
    )

    return {
        "overall_score": combined,
        "threat_level": level,
        "alert_required": alert_required,
        "threat_factors": factors,
    }
