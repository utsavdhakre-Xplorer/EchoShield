# Load local environment before importing modules that read environment variables.
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.api import auth, audio, analysis, ws_audio
from app.core.database import connect_db, disconnect_db, is_db_connected
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_ENV = os.getenv("ECHOSHIELD_ENV", "development").strip().lower()
app = FastAPI(
    title="EchoShield API",
    description="Real-Time AI Scammer Interceptor Backend",
    version="1.0.0",
    docs_url="/docs" if _ENV != "production" else None,
    redoc_url="/redoc" if _ENV != "production" else None,
)

# Explicit allowlist in deployment; local Flutter/web development remains supported.
_origins = [origin.strip() for origin in os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080"
).split(",") if origin.strip()]
if _ENV == "production":
    if not os.getenv("CORS_ORIGINS", "").strip():
        raise RuntimeError("CORS_ORIGINS must explicitly list trusted production origins")
    if "*" in _origins:
        raise RuntimeError("Wildcard CORS origin is not allowed in production")
    if os.getenv("ENABLE_MOCK_DB", "false").strip().lower() in {"1", "true", "yes"}:
        raise RuntimeError("ENABLE_MOCK_DB must be disabled in production")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.middleware("http")
async def security_response_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "microphone=(self), camera=(), geolocation=()")
    response.headers.setdefault("Cache-Control", "no-store")
    if _ENV == "production":
        # HTTPS must be terminated by the trusted deployment proxy/load balancer.
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

@app.on_event("startup")
async def startup_event():
    try:
        await connect_db()
    except Exception as e:
        logger.error("Database initialization failed (exception type: %s)", type(e).__name__)
        if _ENV == "production":
            raise RuntimeError("Production database initialization failed") from e
    if _ENV == "production" and not is_db_connected():
        # Fail closed: never start production with volatile mock or unavailable persistence.
        raise RuntimeError("Production requires a connected persistent database")
    logger.info("EchoShield backend started. database_connected=%s", is_db_connected())

@app.on_event("shutdown")
async def shutdown_event():
    await disconnect_db()
    logger.info("EchoShield backend stopped.")

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(audio.router, tags=["Audio Processing"])
app.include_router(analysis.router, tags=["Analysis"])
app.include_router(ws_audio.router, tags=["WebSocket Streaming"])

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "EchoShield", "version": "1.0.0"}

@app.get("/ready", tags=["System"])
async def readiness_check():
    if not is_db_connected():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database is not connected")
    return {"status": "ready", "database": "connected"}

_DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "web-dashboard")
_DASHBOARD_FILE = os.path.join(_DASHBOARD_DIR, "index.html")

@app.get("/", tags=["Dashboard"])
async def serve_dashboard():
    if os.path.exists(_DASHBOARD_FILE):
        return FileResponse(_DASHBOARD_FILE, media_type="text/html")
    return {"message": "EchoShield API is running. Visit /docs for API documentation."}
