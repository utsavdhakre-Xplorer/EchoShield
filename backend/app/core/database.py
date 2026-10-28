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
    try:
        from app.models.user import User as RealUser
        from app.models.call_log import CallLog as RealCallLog
        
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        await init_beanie(
            database=client.get_default_database(),
            document_models=[RealUser, RealCallLog],
        )
        User = RealUser
        CallLog = RealCallLog
        db_connected = True
        logger.info("Connected to MongoDB.")
    except Exception as e:
        db_connected = False
        logger.warning(f"Failed to connect to MongoDB: {e}")
        logger.warning("Running in MOCK MODE - database operations will be simulated.")
        client = None
        # Use mock models
        User = MockUser
        CallLog = MockCallLog


async def disconnect_db():
    global client, db_connected
    if client:
        client.close()
        logger.info("Disconnected from MongoDB.")
    db_connected = False


def get_client() -> AsyncIOMotorClient:
    return client


def is_db_connected() -> bool:
    return db_connected
