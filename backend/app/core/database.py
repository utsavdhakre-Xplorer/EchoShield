import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import logging
from app.core.mock_db import MockUser, MockCallLog

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/echoshield")

client: AsyncIOMotorClient = None
db_connected = False

# These will be replaced with mock models if MongoDB unavailable
User = None
CallLog = None


async def connect_db():
    global client, db_connected, User, CallLog
    candidate_client = None
    try:
        from app.models.user import User as RealUser
        from app.models.call_log import CallLog as RealCallLog

        candidate_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        await init_beanie(
            database=candidate_client.get_default_database(),
            document_models=[RealUser, RealCallLog],
        )
        client = candidate_client
        User = RealUser
        CallLog = RealCallLog
        db_connected = True
        logger.info("Connected to MongoDB.")
    except Exception as e:
        # Close any client created during an unsuccessful initialization.
        if candidate_client is not None:
            try:
                candidate_client.close()
            except Exception as close_error:
                logger.warning(
                    "MongoDB cleanup failed (exception type: %s)",
                    type(close_error).__name__,
                )
        client = None
        db_connected = False
        logger.warning("Failed to connect to MongoDB (exception type: %s)", type(e).__name__)
        # Mock storage is opt-in: never silently replace a real database in deployment.
        if os.getenv("ENABLE_MOCK_DB", "false").strip().lower() in {"1", "true", "yes"}:
            logger.warning("Running in explicitly enabled MOCK MODE; data is volatile.")
            User = MockUser
            CallLog = MockCallLog
        else:
            User = None
            CallLog = None
            logger.error("Database unavailable and mock mode disabled; database-backed routes will return service errors.")


async def disconnect_db():
    global client, db_connected
    active_client = client
    client = None
    db_connected = False
    if active_client:
        active_client.close()
        logger.info("Disconnected from MongoDB.")


def get_client() -> AsyncIOMotorClient:
    return client


def is_db_connected() -> bool:
    return db_connected
