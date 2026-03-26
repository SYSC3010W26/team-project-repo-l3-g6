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
    ScanFaceCreate,
    SolutionStepCreate,
    ExecutionRunCreate,
    MotorExecutionLogCreate,
    VerificationResultCreate,
    UserCreate,
    JobControlCreate,
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
# scan_faces
# ---------------------------------------------------------------------------

def create_scan_face(conn: sqlite3.Connection, data: ScanFaceCreate) -> int:
    """Insert a face scan record; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO scan_faces
            (session_id, face_name, face_string, confidence, captured_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.face_name,
            data.face_string,
            data.confidence,
            data.captured_by,
            _now(),
        ),
    )
    return cursor.lastrowid


def get_scan_faces_by_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    """Return all face scan rows for a given session."""
    rows = conn.execute(
        "SELECT * FROM scan_faces WHERE session_id = ? ORDER BY created_at",
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
# solution_steps
# ---------------------------------------------------------------------------

def create_solution_step(conn: sqlite3.Connection, data: SolutionStepCreate) -> int:
    """Insert a solution step; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO solution_steps
            (solution_id, step_index, face, direction, degrees, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.solution_id,
            data.step_index,
            data.face,
            data.direction,
            data.degrees,
            _now(),
        ),
    )
    return cursor.lastrowid


def get_solution_steps_by_solution(
    conn: sqlite3.Connection, solution_id: int
) -> list[dict]:
    """Return all steps for a solution, ordered by step_index (not created_at)."""
    rows = conn.execute(
        "SELECT * FROM solution_steps WHERE solution_id = ? ORDER BY step_index",
        (solution_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# execution_runs
# ---------------------------------------------------------------------------

def create_execution_run(conn: sqlite3.Connection, data: ExecutionRunCreate) -> int:
    """Insert an execution run; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO execution_runs
            (session_id, solution_id, status, started_at, motor_node_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.solution_id,
            data.status,
            _now(),
            data.motor_node_id,
        ),
    )
    return cursor.lastrowid


def get_execution_runs_by_session(
    conn: sqlite3.Connection, session_id: int
) -> list[dict]:
    """Return all execution runs for a given session."""
    rows = conn.execute(
        "SELECT * FROM execution_runs WHERE session_id = ? ORDER BY started_at",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_execution_run_status(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    completed_at: Optional[str] = None,
) -> None:
    """Update the status of an execution run. Auto-sets completed_at for terminal states."""
    if completed_at is None and status in ("completed", "failed", "cancelled"):
        completed_at = _now()
    conn.execute(
        "UPDATE execution_runs SET status = ?, completed_at = ? WHERE id = ?",
        (status, completed_at, run_id),
    )


# ---------------------------------------------------------------------------
# motor_execution_log
# ---------------------------------------------------------------------------

def create_motor_log(
    conn: sqlite3.Connection, data: MotorExecutionLogCreate
) -> int:
    """Insert a motor execution log entry; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO motor_execution_log
            (run_id, step_index, commanded_face, commanded_dir,
             commanded_deg, status, error_code, error_message, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.run_id,
            data.step_index,
            data.commanded_face,
            data.commanded_dir,
            data.commanded_deg,
            data.status,
            data.error_code,
            data.error_message,
            _now(),  # ts column
        ),
    )
    return cursor.lastrowid


def get_motor_logs_by_run(conn: sqlite3.Connection, run_id: int) -> list[dict]:
    """Return all motor log entries for a given execution run."""
    rows = conn.execute(
        "SELECT * FROM motor_execution_log WHERE run_id = ? ORDER BY step_index",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# verification_results
# ---------------------------------------------------------------------------

def create_verification_result(
    conn: sqlite3.Connection, data: VerificationResultCreate
) -> int:
    """Insert a verification result; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO verification_results
            (session_id, run_id, verified, final_state_string,
             method, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.run_id,
            data.verified,
            data.final_state_string,
            data.method,
            data.notes,
            _now(),
        ),
    )
    return cursor.lastrowid


def get_verification_results_by_session(
    conn: sqlite3.Connection, session_id: int
) -> list[dict]:
    """Return all verification results for a given session."""
    rows = conn.execute(
        "SELECT * FROM verification_results WHERE session_id = ? ORDER BY created_at",
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


def get_all_nodes(conn: sqlite3.Connection) -> list[dict]:
    """Return all node status rows. Used by heartbeat monitor to detect stale nodes."""
    rows = conn.execute(
        "SELECT * FROM node_status ORDER BY node_id"
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

def create_user(conn: sqlite3.Connection, data: UserCreate) -> int:
    """Insert a new user; returns the new row id."""
    cursor = conn.execute(
        """
        INSERT INTO users (username, role, created_at)
        VALUES (?, ?, ?)
        """,
        (data.username, data.role, _now()),
    )
    return cursor.lastrowid


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[dict]:
    """Return a user row as a dict, or None if not found."""
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


# ---------------------------------------------------------------------------
# job_control
# ---------------------------------------------------------------------------

def create_job_control(conn: sqlite3.Connection, data: JobControlCreate) -> int:
    """Insert a job control flag; returns the new row id."""
    issued_at = data.issued_at or _now()
    cursor = conn.execute(
        """
        INSERT INTO job_control (session_id, action, issued_by, issued_at, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (data.session_id, data.action, data.issued_by, issued_at, data.status),
    )
    return cursor.lastrowid


def get_pending_controls(conn: sqlite3.Connection, session_id: int) -> list:
    """Return all pending control flags for a session, ordered by issued_at."""
    rows = conn.execute(
        "SELECT * FROM job_control WHERE session_id = ? AND status = 'pending' ORDER BY issued_at",
        (session_id,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def ack_job_control(conn: sqlite3.Connection, control_id: int) -> None:
    """Mark a control flag as acknowledged."""
    conn.execute(
        "UPDATE job_control SET status = 'acknowledged' WHERE id = ?",
        (control_id,),
    )
