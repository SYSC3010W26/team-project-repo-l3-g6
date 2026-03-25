"""
============================================================
SYSC3010 L3-G6 — CRUD Unit Tests
Tests all CRUD operations across all 11 tables.
Uses shared conn fixture from conftest.py — each test gets
a fresh isolated SQLite database.
============================================================
"""

import sqlite3
from datetime import datetime, timezone

import pytest

from database.crud import (
    # solve_sessions
    create_solve_session,
    get_solve_session_by_id,
    update_solve_session_status,
    # cube_states
    create_cube_state,
    get_cube_states_by_session,
    # scan_faces
    create_scan_face,
    get_scan_faces_by_session,
    # solutions
    create_solution,
    get_solutions_by_session,
    # solution_steps
    create_solution_step,
    get_solution_steps_by_solution,
    # execution_runs
    create_execution_run,
    get_execution_runs_by_session,
    update_execution_run_status,
    # motor_execution_log
    create_motor_log,
    get_motor_logs_by_run,
    # verification_results
    create_verification_result,
    get_verification_results_by_session,
    # system_logs
    create_log,
    # node_status
    upsert_heartbeat,
    get_all_nodes,
    # users
    create_user,
    get_user_by_id,
)
from database.models import (
    SolveSessionCreate,
    CubeStateCreate,
    ScanFaceCreate,
    SolutionCreate,
    SolutionStepCreate,
    ExecutionRunCreate,
    MotorExecutionLogCreate,
    VerificationResultCreate,
    SystemLogCreate,
    NodeStatusUpsert,
    UserCreate,
)


# ---------------------------------------------------------------------------
# Private helpers — FK parent row factories
# ---------------------------------------------------------------------------

def _make_session(conn) -> int:
    """Create a minimal solve_session and return its id. Used as FK parent."""
    return create_solve_session(
        conn,
        SolveSessionCreate(selected_algorithm="Kociemba", status="pending"),
    )


def _make_solution(conn, session_id: int) -> int:
    return create_solution(
        conn,
        SolutionCreate(
            session_id=session_id,
            algorithm_used="Kociemba",
            move_count=6,
            solution_string="U R2 F' B R U'",
            generated_by="rpi2-solver",
        ),
    )


def _make_execution_run(conn, session_id: int, solution_id: int) -> int:
    return create_execution_run(
        conn,
        ExecutionRunCreate(
            session_id=session_id,
            solution_id=solution_id,
            status="running",
            motor_node_id="rpi3-motors",
        ),
    )


# ===========================================================================
# TASK 1: Tests for existing CRUD functions (5 tables) + FK enforcement
# ===========================================================================

# ---------------------------------------------------------------------------
# solve_sessions
# ---------------------------------------------------------------------------

def test_create_and_get_solve_session(conn):
    """Round-trip: insert a session and verify all fields come back correctly."""
    session_id = create_solve_session(
        conn,
        SolveSessionCreate(
            selected_algorithm="Kociemba",
            status="pending",
            session_name="Test",
        ),
    )
    assert isinstance(session_id, int)
    assert session_id >= 1

    result = get_solve_session_by_id(conn, session_id)
    assert isinstance(result, dict)
    assert result["selected_algorithm"] == "Kociemba"
    assert result["status"] == "pending"
    assert result["session_name"] == "Test"


def test_update_solve_session_status(conn):
    """update_solve_session_status auto-sets completed_at for terminal state."""
    session_id = _make_session(conn)
    update_solve_session_status(conn, session_id, "completed")
    result = get_solve_session_by_id(conn, session_id)
    assert result["status"] == "completed"
    assert result["completed_at"] is not None


def test_get_nonexistent_session_returns_none(conn):
    """get_solve_session_by_id returns None for a missing session id."""
    assert get_solve_session_by_id(conn, 99999) is None


# ---------------------------------------------------------------------------
# cube_states
# ---------------------------------------------------------------------------

def test_create_and_get_cube_states(conn):
    """Round-trip: insert a cube state and verify it is retrieved correctly."""
    sid = _make_session(conn)
    state_id = create_cube_state(
        conn,
        CubeStateCreate(
            session_id=sid,
            source="rpi1-scanner",
            state_string="RRRGGG...",
            is_valid=True,
            confidence=0.95,
        ),
    )
    assert state_id >= 1

    rows = get_cube_states_by_session(conn, sid)
    assert len(rows) == 1
    assert rows[0]["source"] == "rpi1-scanner"
    assert rows[0]["is_valid"] == 1  # SQLite stores bool as int


# ---------------------------------------------------------------------------
# solutions
# ---------------------------------------------------------------------------

def test_create_and_get_solutions(conn):
    """Round-trip: insert a solution and verify field values."""
    sid = _make_session(conn)
    sol_id = _make_solution(conn, sid)
    assert sol_id >= 1

    rows = get_solutions_by_session(conn, sid)
    assert len(rows) == 1
    assert rows[0]["algorithm_used"] == "Kociemba"
    assert rows[0]["move_count"] == 6


# ---------------------------------------------------------------------------
# system_logs
# ---------------------------------------------------------------------------

def test_create_log(conn):
    """create_log returns a valid integer id."""
    log_id = create_log(
        conn,
        SystemLogCreate(level="INFO", event_type="test", message="hello"),
    )
    assert isinstance(log_id, int)
    assert log_id >= 1


# ---------------------------------------------------------------------------
# node_status
# ---------------------------------------------------------------------------

def test_upsert_heartbeat_and_get_all_nodes(conn):
    """Upsert creates exactly one row; second upsert updates in-place."""
    upsert_heartbeat(
        conn,
        NodeStatusUpsert(
            node_id="rpi1-scanner",
            node_type="scanner",
            status="online",
            last_heartbeat=datetime.now(timezone.utc),
        ),
    )
    rows = get_all_nodes(conn)
    assert len(rows) == 1
    assert rows[0]["node_id"] == "rpi1-scanner"

    # Second upsert with different status — must NOT create a duplicate
    upsert_heartbeat(
        conn,
        NodeStatusUpsert(
            node_id="rpi1-scanner",
            node_type="scanner",
            status="offline",
            last_heartbeat=datetime.now(timezone.utc),
        ),
    )
    rows = get_all_nodes(conn)
    assert len(rows) == 1
    assert rows[0]["status"] == "offline"


# ---------------------------------------------------------------------------
# FK enforcement (DB-03)
# ---------------------------------------------------------------------------

def test_fk_violation_cube_state_invalid_session(conn):
    """Inserting a cube_state with a non-existent session_id raises IntegrityError."""
    with pytest.raises(sqlite3.IntegrityError):
        create_cube_state(
            conn,
            CubeStateCreate(
                session_id=99999,
                source="test",
                state_string="X",
                is_valid=False,
            ),
        )
        conn.commit()


def test_fk_violation_execution_run_invalid_solution(conn):
    """Inserting an execution_run with a non-existent solution_id raises IntegrityError."""
    sid = _make_session(conn)
    with pytest.raises(sqlite3.IntegrityError):
        create_execution_run(
            conn,
            ExecutionRunCreate(
                session_id=sid,
                solution_id=99999,
                status="running",
            ),
        )
        conn.commit()


# ===========================================================================
# TASK 2: Tests for 6 new CRUD tables (scan_faces through users)
# ===========================================================================

# ---------------------------------------------------------------------------
# scan_faces
# ---------------------------------------------------------------------------

def test_create_and_get_scan_faces(conn):
    """Insert 2 scan faces and verify both are retrieved."""
    sid = _make_session(conn)

    create_scan_face(
        conn,
        ScanFaceCreate(
            session_id=sid,
            face_name="U",
            face_string="RRRGGGBBB",
            confidence=0.97,
            captured_by="rpi1-scanner",
        ),
    )
    create_scan_face(
        conn,
        ScanFaceCreate(
            session_id=sid,
            face_name="D",
            face_string="WWWOOOYYYY",
            confidence=0.96,
            captured_by="rpi1-scanner",
        ),
    )

    rows = get_scan_faces_by_session(conn, sid)
    assert len(rows) == 2
    face_names = {r["face_name"] for r in rows}
    assert "U" in face_names
    assert "D" in face_names
    # Confidence on first inserted row (ordered by created_at)
    assert rows[0]["confidence"] in (0.97, 0.96)


# ---------------------------------------------------------------------------
# solution_steps
# ---------------------------------------------------------------------------

def test_create_and_get_solution_steps_ordered_by_step_index(conn):
    """Steps inserted out of order must come back sorted by step_index."""
    sid = _make_session(conn)
    sol_id = _make_solution(conn, sid)

    # Insert deliberately out of order
    create_solution_step(
        conn,
        SolutionStepCreate(solution_id=sol_id, step_index=2, face="F", direction="CW", degrees=90),
    )
    create_solution_step(
        conn,
        SolutionStepCreate(solution_id=sol_id, step_index=0, face="U", direction="CW", degrees=90),
    )
    create_solution_step(
        conn,
        SolutionStepCreate(solution_id=sol_id, step_index=1, face="R", direction="CCW", degrees=180),
    )

    rows = get_solution_steps_by_solution(conn, sol_id)
    assert len(rows) == 3
    # ORDER BY step_index must produce 0, 1, 2 regardless of insertion order
    assert rows[0]["step_index"] == 0
    assert rows[1]["step_index"] == 1
    assert rows[2]["step_index"] == 2


# ---------------------------------------------------------------------------
# execution_runs
# ---------------------------------------------------------------------------

def test_create_and_get_execution_runs(conn):
    """Round-trip: insert an execution run and verify field values."""
    sid = _make_session(conn)
    sol_id = _make_solution(conn, sid)
    run_id = _make_execution_run(conn, sid, sol_id)
    assert run_id >= 1

    rows = get_execution_runs_by_session(conn, sid)
    assert len(rows) == 1
    assert rows[0]["status"] == "running"
    assert rows[0]["motor_node_id"] == "rpi3-motors"


def test_update_execution_run_status(conn):
    """update_execution_run_status auto-sets completed_at for terminal state."""
    sid = _make_session(conn)
    sol_id = _make_solution(conn, sid)
    run_id = _make_execution_run(conn, sid, sol_id)

    update_execution_run_status(conn, run_id, "completed")
    rows = get_execution_runs_by_session(conn, sid)
    assert rows[0]["status"] == "completed"
    assert rows[0]["completed_at"] is not None


def test_update_execution_run_status_non_terminal(conn):
    """update_execution_run_status does NOT auto-set completed_at for non-terminal state."""
    sid = _make_session(conn)
    sol_id = _make_solution(conn, sid)
    run_id = _make_execution_run(conn, sid, sol_id)

    update_execution_run_status(conn, run_id, "paused")
    rows = get_execution_runs_by_session(conn, sid)
    assert rows[0]["status"] == "paused"
    assert rows[0]["completed_at"] is None


# ---------------------------------------------------------------------------
# motor_execution_log
# ---------------------------------------------------------------------------

def test_create_and_get_motor_logs(conn):
    """Insert 2 motor log entries and verify they come back ordered by step_index."""
    sid = _make_session(conn)
    sol_id = _make_solution(conn, sid)
    run_id = _make_execution_run(conn, sid, sol_id)

    create_motor_log(
        conn,
        MotorExecutionLogCreate(
            run_id=run_id,
            step_index=0,
            commanded_face="U",
            commanded_dir="CW",
            commanded_deg=90,
            status="success",
        ),
    )
    create_motor_log(
        conn,
        MotorExecutionLogCreate(
            run_id=run_id,
            step_index=1,
            commanded_face="R",
            commanded_dir="CCW",
            commanded_deg=180,
            status="success",
        ),
    )

    rows = get_motor_logs_by_run(conn, run_id)
    assert len(rows) == 2
    assert rows[0]["step_index"] == 0
    assert rows[0]["commanded_face"] == "U"


# ---------------------------------------------------------------------------
# verification_results
# ---------------------------------------------------------------------------

def test_create_and_get_verification_results(conn):
    """Round-trip: insert a verification result and verify field values."""
    sid = _make_session(conn)
    sol_id = _make_solution(conn, sid)
    run_id = _make_execution_run(conn, sid, sol_id)

    create_verification_result(
        conn,
        VerificationResultCreate(
            session_id=sid,
            run_id=run_id,
            verified=True,
            method="camera-rescan",
            final_state_string="SOLVED",
        ),
    )

    rows = get_verification_results_by_session(conn, sid)
    assert len(rows) == 1
    assert rows[0]["verified"] == 1  # SQLite stores bool as int
    assert rows[0]["method"] == "camera-rescan"


# ---------------------------------------------------------------------------
# users
# ---------------------------------------------------------------------------

def test_create_and_get_user(conn):
    """Round-trip: insert a user and verify all fields come back correctly."""
    user_id = create_user(conn, UserCreate(username="testuser", role="operator"))
    assert isinstance(user_id, int)
    assert user_id >= 1

    result = get_user_by_id(conn, user_id)
    assert result is not None
    assert result["username"] == "testuser"
    assert result["role"] == "operator"


def test_get_nonexistent_user_returns_none(conn):
    """get_user_by_id returns None for a missing user id."""
    assert get_user_by_id(conn, 99999) is None
