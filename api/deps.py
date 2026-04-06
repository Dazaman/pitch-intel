import os
import sqlite3

from pipeline.db import get_connection, init_schema

_conn: sqlite3.Connection | None = None


def get_db() -> sqlite3.Connection:
    """Return the shared DB connection. Creates it on first call."""
    global _conn
    if _conn is None:
        local_path = os.environ.get("LOCAL_DB_PATH")
        _conn = get_connection(local_path)
        _conn.row_factory = sqlite3.Row
        init_schema(_conn)
    return _conn


def override_db(conn: sqlite3.Connection) -> None:
    """Override the DB connection (for testing)."""
    global _conn
    _conn = conn
