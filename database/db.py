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
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_URL", "./rubiks.db")


# ---------------------------------------------------------------------------
# SQLite — local development
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return an open SQLite connection with row dict-like access enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager that opens a connection, yields it, then closes it.

    Usage:
        with db_session() as conn:
            conn.execute(...)
    """
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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
