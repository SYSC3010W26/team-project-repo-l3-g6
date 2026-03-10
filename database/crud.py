"""
============================================================
Done By : Saim Hashmi 
SYSC3010 L3-G6 — CRUD Helper Functions
Covers the most critical tables used across all four Pis.
All functions accept an open sqlite3.Connection so callers
can manage transaction scope via db_session() from db.py.
============================================================
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .models import (
    SolveSessionCreate,
    CubeStateCreate,
    SolutionCreate,
    SystemLogCreate,
    NodeStatusUpsert,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row) if row else {}


# ---------------------------------------------------------------------------
# solve_sessions
# ---------------------------------------------------------------------------

def create_solve_session(conn: sqlite3.Connection, data: SolveSessionCreate) -> int:
    """Insert a new solve session; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO solve_sessions
            (user_id, session_name, selected_algorithm, status, started_at, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.user_id,
            data.session_name,
            data.selected_algorithm,
            data.status,
            _now(),
            data.notes,
        ),
    )
    return cursor.lastrowid


def get_solve_session_by_id(conn: sqlite3.Connection, session_id: int) -> Optional[dict]:
    """Return a solve session row as a dict, or None if not found."""
    row = conn.execute(
        "SELECT * FROM solve_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def update_solve_session_status(
    conn: sqlite3.Connection,
    session_id: int,
    status: str,
    completed_at: Optional[str] = None,
) -> None:
    """Update the status (and optionally completed_at) of a solve session."""
    if completed_at is None and status in ("completed", "failed", "cancelled"):
        completed_at = _now()
    conn.execute(
        "UPDATE solve_sessions SET status = ?, completed_at = ? WHERE id = ?",
        (status, completed_at, session_id),
    )


# ---------------------------------------------------------------------------
# cube_states
# ---------------------------------------------------------------------------

def create_cube_state(conn: sqlite3.Connection, data: CubeStateCreate) -> int:
    """Insert a cube state record; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO cube_states
            (session_id, source, state_string, is_valid, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.source,
            data.state_string,
            data.is_valid,
            data.confidence,
            _now(),
        ),
    )
    return cursor.lastrowid


def get_cube_states_by_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    """Return all cube state rows for a given session."""
    rows = conn.execute(
        "SELECT * FROM cube_states WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# solutions
# ---------------------------------------------------------------------------

def create_solution(conn: sqlite3.Connection, data: SolutionCreate) -> int:
    """Insert a solution record; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO solutions
            (session_id, algorithm_used, move_count, solution_string,
             generated_by, generated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.algorithm_used,
            data.move_count,
            data.solution_string,
            data.generated_by,
            _now(),
        ),
    )
    return cursor.lastrowid


def get_solutions_by_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    """Return all solution rows for a given session."""
    rows = conn.execute(
        "SELECT * FROM solutions WHERE session_id = ? ORDER BY generated_at",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# system_logs
# ---------------------------------------------------------------------------

def create_log(conn: sqlite3.Connection, data: SystemLogCreate) -> int:
    """Append a system log entry; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO system_logs
            (session_id, node_id, level, event_type, message, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.node_id,
            data.level,
            data.event_type,
            data.message,
            data.metadata,
            _now(),
        ),
    )
    return cursor.lastrowid


# ---------------------------------------------------------------------------
# node_status
# ---------------------------------------------------------------------------

def upsert_heartbeat(conn: sqlite3.Connection, data: NodeStatusUpsert) -> None:
    """Insert or update a node's status record (heartbeat upsert)."""
    conn.execute(
        """
        INSERT INTO node_status
            (node_id, node_type, ip_address, status, last_heartbeat, last_message)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            node_type      = excluded.node_type,
            ip_address     = excluded.ip_address,
            status         = excluded.status,
            last_heartbeat = excluded.last_heartbeat,
            last_message   = excluded.last_message
        """,
        (
            data.node_id,
            data.node_type,
            data.ip_address,
            data.status,
            data.last_heartbeat.isoformat(),
            data.last_message,
        ),
    )
