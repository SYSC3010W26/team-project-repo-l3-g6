"""
============================================================
Done By : Saim Hashmi 
SYSC3010 L3-G6 — Database Connection Module

Local dev:  SQLite via DATABASE_URL env var (default: ./rubiks.db)
Production: swap get_connection() body for the psycopg2 block below.
============================================================
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_URL", "./rubiks.db")

# ---------------------------------------------------------------------------
# Shared connection — single SQLite connection with a lock.
# This prevents stale-read issues that occur when each request opens its own
# connection: SQLite serializes writes via the lock, and all reads see the
# latest committed state because they share the same connection.
# ---------------------------------------------------------------------------

_db_lock = threading.Lock()
_shared_conn: sqlite3.Connection | None = None


def _open_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = DELETE")
    return conn


def get_db() -> sqlite3.Connection:
    """Return the shared SQLite connection (creates it on first call)."""
    global _shared_conn
    with _db_lock:
        if _shared_conn is None:
            _shared_conn = _open_connection()
    return _shared_conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager that acquires the shared connection lock, yields it,
    commits on success, rolls back on failure.

    Usage:
        with db_session() as conn:
            conn.execute(...)
    """
    conn = get_db()
    with _db_lock:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# ---------------------------------------------------------------------------
# Supabase / PostgreSQL — production (swap in when deploying to Rpi4)
#
# To migrate:
#   1. pip install psycopg2-binary
#   2. Set DATABASE_URL to your Supabase connection string, e.g.:
#      postgresql://postgres:<password>@db.<project>.supabase.co:5432/postgres
#   3. Replace the functions above with the block below:
#
# import psycopg2
# import psycopg2.extras
#
# def get_db():
#     conn = psycopg2.connect(os.getenv("DATABASE_URL"))
#     conn.cursor_factory = psycopg2.extras.RealDictCursor
#     return conn
#
# from contextlib import contextmanager
# @contextmanager
# def db_session():
#     conn = get_db()
#     try:
#         yield conn
#         conn.commit()
#     except Exception:
#         conn.rollback()
#         raise
#     finally:
#         conn.close()
# ---------------------------------------------------------------------------
