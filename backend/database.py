import os
import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_db() -> Optional[AsyncIOMotorDatabase]:
    """Connect to MongoDB and return the database instance."""
    global _client, _db

    mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "ark_ide")

    try:
        _client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        # Verify connection
        await _client.admin.command("ping")
        _db = _client[db_name]
        logger.info(f"Connected to MongoDB: {db_name} at {mongo_url}")

        # Create indexes
        await _ensure_indexes(_db)
        return _db
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Running without persistence.")
        _client = None
        _db = None
        return None


async def _ensure_indexes(db: AsyncIOMotorDatabase):
    """Create required indexes on startup."""
    try:
        await db.projects.create_index("id", unique=True)
        await db.projects.create_index("stage")
        await db.projects.create_index("created_at")
        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.warning(f"Failed to create indexes: {e}")


async def disconnect_db():
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_db() -> Optional[AsyncIOMotorDatabase]:
    """Return the current database instance (may be None if not connected)."""
    return _db
