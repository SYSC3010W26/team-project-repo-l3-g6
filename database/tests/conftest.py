import tempfile
import os

import pytest

import database.db as db_module
from database.init_db import create_tables


@pytest.fixture
def conn():
    """Yield a fresh SQLite connection with all tables created.

    Each test gets its own temporary database file — fully isolated.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["DATABASE_URL"] = db_path
    db_module.DB_PATH = db_path
    c = db_module.get_db()
    create_tables(c)
    yield c
    c.close()
    os.unlink(db_path)
