"""
DB dependency injection for FastAPI route handlers.
Uses the shared db_session() which serializes access via a lock.
"""
import sqlite3
from typing import Generator
from database.db import db_session


def get_db_dep() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: yields the shared DB connection with auto-commit/rollback."""
    with db_session() as conn:
        yield conn
