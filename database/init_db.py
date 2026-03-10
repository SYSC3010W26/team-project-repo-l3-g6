"""
============================================================
SYSC3010 L3-G6 — Database Initialiser
Reads schema.sql, creates all tables in SQLite, seeds a
default admin user.

Usage:
    python init_db.py

Environment variables:
    DATABASE_URL  Path to the SQLite file (default: ./rubiks.db)
============================================================
"""

import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_URL", "./rubiks.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    schema_sql = SCHEMA_PATH.read_text()
    # Execute each statement individually so we can report each table
    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
    cursor = conn.cursor()
    for stmt in statements:
        if stmt.upper().startswith("CREATE TABLE"):
            # Extract table name for reporting
            parts = stmt.split()
            table_name = parts[5] if "IF NOT EXISTS" in stmt.upper() else parts[2]
            cursor.execute(stmt)
            print(f"  [OK] Table created (or already exists): {table_name}")
        elif stmt:
            cursor.execute(stmt)
    conn.commit()


def seed_default_user(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    existing = cursor.execute(
        "SELECT id FROM users WHERE username = 'admin'"
    ).fetchone()
    if existing:
        print("  [SKIP] Default admin user already exists.")
    else:
        cursor.execute(
            "INSERT INTO users (username, role) VALUES (?, ?)",
            ("admin", "admin"),
        )
        conn.commit()
        print("  [OK] Default admin user seeded (username='admin', role='admin').")


def main() -> None:
    print(f"[init_db] Using database: {DB_PATH}")
    conn = get_connection(DB_PATH)
    try:
        print("[init_db] Creating tables...")
        create_tables(conn)
        print("[init_db] Seeding default data...")
        seed_default_user(conn)
        print("[init_db] Done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
