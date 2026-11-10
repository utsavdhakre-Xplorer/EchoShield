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

app = FastAPI(
    title="EchoShield API",
    description="Real-Time AI Scammer Interceptor Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Explicit allowlist in deployment; local Flutter/web development remains supported.
_origins = [origin.strip() for origin in os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080"
).split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.on_event("startup")
async def startup_event():
    try:
        await connect_db()
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)
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
