from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.core.security import get_current_user
from app.services.scam_detector import detect_scam_tactics
from app.services.threat_classifier import classify_threat
from app.services.negotiator import generate_negotiator_strategy
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_transcript_request(request: dict):
    """Validate and normalize user-provided transcript analysis fields."""
    transcript = request.get("transcript", "")
    call_id = request.get("call_id")
    caller_number = request.get("caller_number")

    if caller_number is not None and (not isinstance(caller_number, str) or len(caller_number) > 32):
        raise HTTPException(status_code=400, detail="Caller number must be a string of at most 32 characters")
    if call_id is not None and (not isinstance(call_id, str) or len(call_id) > 100):
        raise HTTPException(status_code=400, detail="Call ID must be a string of at most 100 characters")
    if not isinstance(transcript, str):
        raise HTTPException(status_code=400, detail="Transcript must be a string")
    transcript = transcript.strip()
    if len(transcript) < 5:
        raise HTTPException(status_code=400, detail="Transcript too short")
    if len(transcript) > 10000:
        raise HTTPException(status_code=413, detail="Transcript exceeds the 10000-character limit")
    return transcript, call_id, caller_number


@router.post("/analyze", response_model=dict)
async def analyze_transcript(
    request: dict = Body(...),
    current_user = Depends(get_current_user),
):
    """Analyze a transcript string directly and return threat assessment."""
    import asyncio
    
    transcript, call_id, caller_number = validate_transcript_request(request)
    
    logger.info("Analyzing transcript payload (characters=%d)", len(transcript))
    
    # Run analysis tasks concurrently
    scam_task = detect_scam_tactics(transcript)
    
    try:
        scam_result = await asyncio.wait_for(scam_task, timeout=65.0)
    except asyncio.TimeoutError:
        logger.error("Transcript scam detection timed out")
        raise HTTPException(status_code=504, detail="Scam detection timed out; please retry")
    logger.info("Scam detection complete: urgency_score=%s", scam_result["urgency_score"])
    
    threat = classify_threat(
        deepfake_confidence=0.0,
        is_deepfake=False,
        urgency_score=scam_result["urgency_score"],
        urgency_detected=scam_result["urgency_detected"],
        deepfake_verified=False,
        tactics_detected=scam_result.get("tactics_detected"),
    )
    logger.info("Threat classification complete: threat_level=%s", threat["threat_level"])
    
    try:
        strategy = await asyncio.wait_for(
            generate_negotiator_strategy(transcript, threat["threat_level"]),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        logger.error("Negotiator strategy generation timed out")
        raise HTTPException(status_code=504, detail="Strategy generation timed out; please retry")
    logger.info("Negotiator strategy generated")

    # Serialize threat_level enum to string
    threat_level_str = threat["threat_level"].value if hasattr(threat["threat_level"], 'value') else str(threat["threat_level"])

    # Persist call to database so it appears in past calls history
    from app.core.database import CallLog
    try:
        new_log = CallLog(
            user_id=str(current_user.id),
            caller_number=caller_number,
            transcript=transcript,
            threat_level=threat["threat_level"],
            deepfake_confidence=0.0,
            is_deepfake=False,
            urgency_score=scam_result["urgency_score"],
            urgency_detected=scam_result["urgency_detected"],
            overall_threat_score=threat["overall_score"],
            urgency_phrases_found=scam_result.get("phrases_found", []),
            negotiator_strategy=strategy,
            alert_sent=threat["alert_required"],
        )
        await new_log.insert()
        call_log_id = str(new_log.id)
    except Exception as e:
        logger.warning("Failed to save call log (exception type: %s)", type(e).__name__)
        raise HTTPException(status_code=503, detail="Unable to save analysis; database temporarily unavailable") from e

    logger.info("Transcript analysis complete; returning response.")

    return {
        "call_log_id": call_log_id,
        "transcript": transcript,
        "is_deepfake": False,
        "deepfake_confidence": 0.0,
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


@router.get("/call-logs")
async def get_call_logs(
    limit: int = Query(default=20, ge=1, le=100),
    current_user = Depends(get_current_user),
):
    """Get call logs for current user."""
    from app.core.database import CallLog
    if CallLog is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")
    
    try:
        logs = await CallLog.find({"user_id": str(current_user.id)}).sort([("call_start", -1)]).limit(limit).to_list()
    except Exception as exc:
        logger.warning("Call logs retrieval failed (exception type: %s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Call logs are temporarily unavailable") from exc
    return [
        {
            "id": str(log.id),
            "call_start": log.call_start.isoformat() if hasattr(log.call_start, 'isoformat') else str(log.call_start),
            "call_end": log.call_end.isoformat() if getattr(log, 'call_end', None) and hasattr(log.call_end, 'isoformat') else getattr(log, 'call_end', None),
            "threat_level": log.threat_level.value if hasattr(log.threat_level, 'value') else str(log.threat_level),
            "overall_threat_score": log.overall_threat_score,
            "is_deepfake": log.is_deepfake,
            "deepfake_confidence": getattr(log, 'deepfake_confidence', 0.0),
            "urgency_detected": log.urgency_detected,
            "urgency_score": getattr(log, 'urgency_score', 0.0),
            "urgency_phrases_found": getattr(log, 'urgency_phrases_found', []),
            "transcript": log.transcript,
            "negotiator_strategy": log.negotiator_strategy,
            "caller_number": log.caller_number,
        }
        for log in logs
    ]


@router.get("/stats")
async def get_stats(current_user = Depends(get_current_user)):
    """Get user statistics."""
    from app.core.database import CallLog
    # Match /call-logs behavior: fail clearly when persistence is unavailable
    # instead of dereferencing None and returning an internal server error.
    if CallLog is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")

    try:
        await ensure_seed_logs(CallLog, str(current_user.id))
        all_logs = await CallLog.find({"user_id": str(current_user.id)}).to_list()
    except Exception as exc:
        logger.warning("Statistics retrieval failed (exception type: %s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Statistics are temporarily unavailable") from exc
    total_calls = len(all_logs)
    # threat_level may be a ThreatLevel enum or a plain string — normalise to str
    scam_calls = sum(1 for l in all_logs if str(getattr(l.threat_level, 'value', l.threat_level)) in ["HIGH", "CRITICAL"])
    deepfake_calls = sum(1 for l in all_logs if l.is_deepfake)
    avg_threat = sum(l.overall_threat_score for l in all_logs) / total_calls if total_calls else 0

    threat_breakdown = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for log in all_logs:
        level_str = str(getattr(log.threat_level, 'value', log.threat_level))
        threat_breakdown[level_str] = threat_breakdown.get(level_str, 0) + 1

    return {
        "total_calls_analyzed": total_calls,
        "scam_calls_detected": scam_calls,
        "deepfake_calls_detected": deepfake_calls,
        "average_threat_score": round(avg_threat, 3),
        "threat_breakdown": threat_breakdown,
    }
