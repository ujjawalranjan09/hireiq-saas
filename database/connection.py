"""Database connection module with MongoDB singleton."""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from app.config import MONGO_URI, MONGO_DB_NAME

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """MongoDB connection singleton."""
    
    _instance: Optional["MongoDBConnection"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls) -> "MongoDBConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            if self._client is None:
                self._client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
                self._client.admin.command("ping")
                self._db = self._client[MONGO_DB_NAME]
                logger.info(f"Connected to MongoDB: {MONGO_DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._client = None
            self._db = None
            raise

    @property
    def db(self) -> Optional[Database]:
        """Get the database instance."""
        if self._db is None:
            self.connect()
        return self._db

    def get_collection(self, name: str) -> Collection:
        """Get a collection by name."""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[name]

    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")


# Global singleton
_connection: Optional[MongoDBConnection] = None


def get_connection() -> MongoDBConnection:
    """Get the global MongoDB connection singleton."""
    global _connection
    if _connection is None:
        _connection = MongoDBConnection()
        _connection.connect()
    return _connection


def get_db() -> Database:
    """Get the database instance directly."""
    return get_connection().db
