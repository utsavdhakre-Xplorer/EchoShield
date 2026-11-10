from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from fastapi import Depends
import logging

logger = logging.getLogger(__name__)
from app.models.user import UserCreate, UserLogin

router = APIRouter()


@router.post("/signup", response_model=dict, status_code=201)
async def signup(user_data: UserCreate):
    from app.core.database import User
    if User is None:
        raise HTTPException(status_code=503, detail="Database unavailable; signup is temporarily disabled")
    
    # Check existing email
    email = str(user_data.email).lower()
    username = user_data.username.strip()
    try:
        existing = await User.find_one({"email": email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        existing_username = await User.find_one({"username": username})
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Signup uniqueness check failed (exception type: %s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc

    try:
        password_hash = hash_password(user_data.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = User(
        email=email,
        username=username,
        hashed_password=password_hash,
        full_name=user_data.full_name,
        family_contact_email=str(user_data.family_contact_email) if user_data.family_contact_email else None,
    )
    try:
        await user.insert()
    except Exception as exc:
        logger.warning("Signup persistence failed (exception type: %s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Unable to create account; database temporarily unavailable") from exc

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    from app.core.database import User
    if User is None:
        raise HTTPException(status_code=503, detail="Database unavailable; login is temporarily disabled")
    
    try:
        user = await User.find_one({"email": str(credentials.email).lower()})
    except Exception as exc:
        logger.warning("Login user lookup failed (exception type: %s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not getattr(user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    user.last_login = datetime.utcnow()
    try:
        await user.save()
    except Exception as exc:
        logger.warning("Login timestamp persistence failed (exception type: %s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from exc

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.get("/me", response_model=dict)
async def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "created_at": current_user.created_at.isoformat(),
    }


@router.get("/call-history")
async def get_call_history(current_user = Depends(get_current_user)):
    from app.core.database import CallLog
    from app.core.seed_data import ensure_seed_logs

    if CallLog is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")

    try:
        await ensure_seed_logs(CallLog, str(current_user.id))
        logs = await CallLog.find({"user_id": str(current_user.id)}).sort([("call_start", -1)]).limit(50).to_list()
    except Exception as exc:
        logger.warning("Call history retrieval failed (exception type: %s)", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Call history is temporarily unavailable") from exc
    return [
        {
            "id": str(log.id),
            "call_start": log.call_start.isoformat() if hasattr(log.call_start, 'isoformat') else str(log.call_start),
            "call_end": log.call_end.isoformat() if log.call_end and hasattr(log.call_end, 'isoformat') else log.call_end,
            "caller_number": log.caller_number,
            "threat_level": log.threat_level.value if hasattr(log.threat_level, 'value') else str(log.threat_level),
            "overall_threat_score": log.overall_threat_score,
            "is_deepfake": log.is_deepfake,
            "deepfake_confidence": getattr(log, 'deepfake_confidence', 0.0),
            "urgency_detected": log.urgency_detected,
            "urgency_score": getattr(log, 'urgency_score', 0.0),
            "urgency_phrases_found": getattr(log, 'urgency_phrases_found', []),
            "transcript": log.transcript,
            "negotiator_strategy": log.negotiator_strategy,
        }
        for log in logs
    ]
