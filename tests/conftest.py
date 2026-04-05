import sqlite3

import pytest


@pytest.fixture
def db():
    """In-memory SQLite database with schema applied."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    from pipeline.db import init_schema

    init_schema(conn)

    yield conn
    conn.close()
