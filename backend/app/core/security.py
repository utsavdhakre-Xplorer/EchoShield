import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Never ship a predictable signing key. Production must provide JWT_SECRET_KEY.
_ENV = os.getenv("ECHOSHIELD_ENV", "development").lower()
_configured_secret = os.getenv("JWT_SECRET_KEY", "").strip()
if _ENV == "production" and len(_configured_secret) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be set to at least 32 characters in production")
SECRET_KEY = _configured_secret or secrets.token_urlsafe(48)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

security = HTTPBearer()


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")
    # bcrypt only accepts up to 72 bytes; count UTF-8 bytes, not characters.
    if len(password_bytes) > 72:
        raise ValueError("Password cannot exceed 72 UTF-8 bytes")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from app.core.database import User
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    if User is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    try:
        user = await User.get(user_id)
    except Exception as exc:
        # A database query failure is not the same as a missing account.
        raise HTTPException(
            status_code=503,
            detail="Unable to verify user account; database is temporarily unavailable",
        ) from exc
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not getattr(user, "is_active", True):
        raise HTTPException(status_code=403, detail="User account is disabled")
    return user
