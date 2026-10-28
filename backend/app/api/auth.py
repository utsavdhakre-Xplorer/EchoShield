from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from fastapi import Depends
from uuid import uuid4

router = APIRouter()


@router.post("/signup", response_model=dict, status_code=201)
async def signup(user_data: dict):
    from app.core.database import User
    
    # Check existing email
    existing = await User.find_one({"email": user_data.get("email")})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = await User.find_one({"username": user_data.get("username")})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=user_data.get("email"),
        username=user_data.get("username"),
        hashed_password=hash_password(user_data.get("password")),
        full_name=user_data.get("full_name"),
        family_contact_email=user_data.get("family_contact_email"),
    )
    await user.insert()

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
async def login(credentials: dict):
    from app.core.database import User
    
    user = await User.find_one({"email": credentials.get("email")})
    if not user or not verify_password(credentials.get("password"), user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.last_login = datetime.utcnow()
    await user.save()

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
    logs = await CallLog.find({"user_id": current_user.id}).sort([("call_start", -1)]).limit(50).to_list()
    return [
        {
            "id": log.id,
            "call_start": log.call_start.isoformat() if hasattr(log.call_start, 'isoformat') else str(log.call_start),
            "call_end": log.call_end.isoformat() if log.call_end and hasattr(log.call_end, 'isoformat') else log.call_end,
            "caller_number": log.caller_number,
            "threat_level": log.threat_level,
            "overall_threat_score": log.overall_threat_score,
            "is_deepfake": log.is_deepfake,
            "urgency_detected": log.urgency_detected,
            "transcript": log.transcript,
            "negotiator_strategy": log.negotiator_strategy,
        }
        for log in logs
    ]
