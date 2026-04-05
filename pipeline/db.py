import sqlite3

from pipeline.config import SCHEMA_PATH, TURSO_AUTH_TOKEN, TURSO_DATABASE_URL


def get_connection(local_path: str | None = None) -> sqlite3.Connection:
    """Return a database connection.

    If local_path is given, use a local SQLite file (for tests).
    Otherwise connect to Turso via libsql.
    """
    if local_path:
        return sqlite3.connect(local_path)

    import libsql_experimental as libsql

    conn = libsql.connect(
        "pitch-intel.db",
        sync_url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN,
    )
    conn.sync()
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes from schema.sql."""
    sql = SCHEMA_PATH.read_text()
    conn.executescript(sql)
    conn.commit()
