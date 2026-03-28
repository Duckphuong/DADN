from dataclasses import dataclass

from flask import current_app
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError


MONGO_CONNECTION_EXTENSION_KEY = "mongo_connection"


@dataclass(slots=True)
class MongoConnectionState:
    configured: bool
    connected: bool
    db_name: str | None
    error: str | None = None


@dataclass(slots=True)
class MongoConnection:
    client: MongoClient | None
    database: Database | None
    state: MongoConnectionState


def init_mongo(app) -> MongoConnection:
    mongo_uri = app.config.get("MONGO_URI", "").strip()
    db_name = app.config.get("MONGO_DB_NAME", "").strip()
    timeout_ms = int(app.config.get("MONGO_CONNECT_TIMEOUT_MS", 5000))

    state = MongoConnectionState(
        configured=bool(mongo_uri and db_name),
        connected=False,
        db_name=db_name or None,
        error=None,
    )
    connection = MongoConnection(client=None, database=None, state=state)
    app.extensions[MONGO_CONNECTION_EXTENSION_KEY] = connection

    if not state.configured:
        state.error = "Missing MONGO_URI or MONGO_DB_NAME"
        app.logger.warning("MongoDB config is incomplete. Skipping MongoDB initialization.")
        return connection

    if "******" in mongo_uri:
        state.error = "MONGO_URI still contains a masked password placeholder"
        app.logger.warning(
            "MongoDB config is present but MONGO_URI still contains a masked password."
        )
        return connection

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=timeout_ms)
        client.admin.command("ping")
        connection.client = client
        connection.database = client[db_name]
        state.connected = True
        app.logger.info("MongoDB connected successfully to database '%s'.", db_name)
        return connection
    except PyMongoError as exc:
        state.error = str(exc)
        app.logger.exception("MongoDB connection failed.")
        if app.config.get("MONGO_FAIL_FAST", False):
            raise RuntimeError("MongoDB connection failed.") from exc
        return connection


def get_mongo_connection() -> MongoConnection:
    return current_app.extensions.get(
        MONGO_CONNECTION_EXTENSION_KEY,
        MongoConnection(
            client=None,
            database=None,
            state=MongoConnectionState(
                configured=False,
                connected=False,
                db_name=None,
                error="MongoDB has not been initialized",
            ),
        ),
    )


def get_mongo_database() -> Database | None:
    return get_mongo_connection().database


def get_mongo_state() -> dict:
    state = get_mongo_connection().state
    return {
        "configured": state.configured,
        "connected": state.connected,
        "db_name": state.db_name,
        "error": state.error,
    }
