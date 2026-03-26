"""
Test fixtures for backend API integration tests.
Pattern: tempfile DB + create_tables + TestClient(fastapi_app).
Per D-08: wraps fastapi_app (NOT the socketio.ASGIApp wrapper).
"""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

import database.db as db_module
from database.init_db import create_tables
from backend.main import fastapi_app  # NOT app (the socketio.ASGIApp)


@pytest.fixture
def client():
    """Each test gets a fresh SQLite DB + TestClient wrapping fastapi_app only."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["DATABASE_URL"] = db_path
    db_module.DB_PATH = db_path
    conn = db_module.get_db()
    create_tables(conn)
    conn.close()
    with TestClient(fastapi_app) as c:
        yield c
    os.unlink(db_path)
