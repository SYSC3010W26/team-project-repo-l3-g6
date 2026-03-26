"""
DB dependency injection for FastAPI route handlers.
Wraps database.db.db_session() as a generator for Depends().
"""
import sqlite3
from typing import Generator
from database.db import db_session


def get_db_dep() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: yields an open DB connection with auto-commit/rollback."""
    with db_session() as conn:
        yield conn
