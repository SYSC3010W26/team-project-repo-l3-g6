"""
============================================================
SYSC3010 L3-G6 — Schema Verification Tests
Verifies all 11 tables are created correctly, FK enforcement
is active, and key columns exist on critical tables.
============================================================
"""

import sqlite3

import pytest


# ---------------------------------------------------------------------------
# Test: All 11 tables are created
# ---------------------------------------------------------------------------

def test_all_11_tables_created(conn):
    """All 11 expected tables must exist after create_tables()."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    actual_tables = {row["name"] for row in rows}

    expected_tables = {
        "cube_states",
        "execution_runs",
        "motor_execution_log",
        "node_status",
        "scan_faces",
        "solution_steps",
        "solutions",
        "solve_sessions",
        "system_logs",
        "users",
        "verification_results",
    }

    assert actual_tables == expected_tables, (
        f"Table mismatch.\n"
        f"  Expected: {sorted(expected_tables)}\n"
        f"  Got:      {sorted(actual_tables)}\n"
        f"  Missing:  {sorted(expected_tables - actual_tables)}\n"
        f"  Extra:    {sorted(actual_tables - expected_tables)}"
    )


# ---------------------------------------------------------------------------
# Test: PRAGMA foreign_keys is ON
# ---------------------------------------------------------------------------

def test_foreign_keys_enabled(conn):
    """PRAGMA foreign_keys must be 1 (ON) on the test connection."""
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    assert result[0] == 1, "Expected PRAGMA foreign_keys = ON (1), got OFF (0)"


# ---------------------------------------------------------------------------
# Test: FK violation is rejected
# ---------------------------------------------------------------------------

def test_fk_enforcement_rejects_invalid_reference(conn):
    """Inserting a solve_sessions row with non-existent user_id must raise IntegrityError."""
    # Insert a valid user first
    conn.execute(
        "INSERT INTO users (username, role) VALUES (?, ?)",
        ("testuser", "admin"),
    )
    conn.commit()

    # Attempt to insert a solve_sessions row referencing a non-existent user_id
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO solve_sessions
                (user_id, selected_algorithm, status, started_at)
            VALUES (?, ?, ?, ?)
            """,
            (99999, "CFOP", "pending", "2026-01-01T00:00:00+00:00"),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Test: Key columns exist on critical tables
# ---------------------------------------------------------------------------

def _get_columns(conn, table_name):
    """Return a set of column names for the given table."""
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def test_each_table_has_expected_columns(conn):
    """Critical tables must have their expected key columns."""
    checks = {
        "users": {"id", "username", "role", "created_at"},
        "solve_sessions": {"id", "user_id", "session_name", "selected_algorithm", "status", "started_at"},
        "execution_runs": {"id", "session_id", "solution_id", "status", "started_at", "completed_at", "motor_node_id"},
        "motor_execution_log": {"id", "run_id", "step_index", "commanded_face", "commanded_dir", "commanded_deg", "status", "ts"},
    }

    for table_name, required_columns in checks.items():
        actual_columns = _get_columns(conn, table_name)
        missing = required_columns - actual_columns
        assert not missing, (
            f"Table '{table_name}' is missing columns: {sorted(missing)}\n"
            f"  Actual columns: {sorted(actual_columns)}"
        )
