"""
============================================================
SYSC3010 L3-G6 — Job State Machine Unit Tests (TEST-02)
Done By : Saim Hashmi

All tests use a temporary SQLite database.
No running server required — satisfies TEST-02.
============================================================
"""
import os
import tempfile

import pytest

import database.db as db_module
from database.init_db import create_tables
from database import crud
from database.models import (
    SolveSessionCreate,
    CubeStateCreate,
    SolutionCreate,
    JobControlCreate,
)
from backend.job_state import JobStateMachine, InvalidTransitionError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_db():
    """Create a fresh temp DB for each test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    original = db_module.DB_PATH
    db_module.DB_PATH = path
    os.environ["DATABASE_URL"] = path
    conn = db_module.get_db()
    create_tables(conn)
    yield conn
    conn.close()
    db_module.DB_PATH = original
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def machine():
    return JobStateMachine()


@pytest.fixture
def pending_session(fresh_db):
    """Create a session in pending state (the default from create_solve_session)."""
    return crud.create_solve_session(
        fresh_db,
        SolveSessionCreate(selected_algorithm="CFOP", status="pending"),
    )


@pytest.fixture
def idle_session(fresh_db):
    """Create a session in idle state."""
    sid = crud.create_solve_session(
        fresh_db,
        SolveSessionCreate(selected_algorithm="CFOP", status="idle"),
    )
    crud.update_solve_session_status(fresh_db, sid, "idle")
    return sid


# ---------------------------------------------------------------------------
# JOB-01: Pipeline ordering enforcement — legal transitions
# ---------------------------------------------------------------------------

def test_legal_transition_pending_to_scanning(fresh_db, machine, pending_session):
    """pending → scanning is a legal transition (default start state)."""
    result = machine.transition(fresh_db, pending_session, "scanning")
    assert result == "scanning"
    row = crud.get_solve_session_by_id(fresh_db, pending_session)
    assert row["status"] == "scanning"


def test_legal_transition_idle_to_scanning(fresh_db, machine, idle_session):
    """idle → scanning is a legal transition."""
    result = machine.transition(fresh_db, idle_session, "scanning")
    assert result == "scanning"
    row = crud.get_solve_session_by_id(fresh_db, idle_session)
    assert row["status"] == "scanning"


def test_legal_transition_scanning_to_solving(fresh_db, machine, idle_session):
    """scanning → solving is legal when a valid cube state exists (JOB-02)."""
    machine.transition(fresh_db, idle_session, "scanning")
    # Provide valid cube state (is_valid is bool in models.py)
    crud.create_cube_state(
        fresh_db,
        CubeStateCreate(
            session_id=idle_session,
            source="camera",
            state_string="U" * 54,
            is_valid=True,
            confidence=0.95,
        ),
    )
    result = machine.transition(fresh_db, idle_session, "solving")
    assert result == "solving"
    row = crud.get_solve_session_by_id(fresh_db, idle_session)
    assert row["status"] == "solving"


def test_legal_transition_solving_to_executing(fresh_db, machine, idle_session):
    """solving → executing is legal when a solution exists (JOB-03)."""
    machine.transition(fresh_db, idle_session, "scanning")
    crud.create_cube_state(
        fresh_db,
        CubeStateCreate(
            session_id=idle_session, source="camera",
            state_string="U" * 54, is_valid=True, confidence=0.95,
        ),
    )
    machine.transition(fresh_db, idle_session, "solving")
    # Provide solution
    crud.create_solution(
        fresh_db,
        SolutionCreate(
            session_id=idle_session,
            algorithm_used="CFOP",
            move_count=20,
            solution_string="R U R' U' " * 5,
            generated_by="solver-pi",
        ),
    )
    result = machine.transition(fresh_db, idle_session, "executing")
    assert result == "executing"
    row = crud.get_solve_session_by_id(fresh_db, idle_session)
    assert row["status"] == "executing"


def test_legal_transition_executing_to_done(fresh_db, machine, idle_session):
    """executing → done is a legal transition."""
    crud.update_solve_session_status(fresh_db, idle_session, "executing")
    result = machine.transition(fresh_db, idle_session, "done")
    assert result == "done"


def test_legal_transition_error_to_idle(fresh_db, machine, idle_session):
    """error → idle is legal (reset from error state)."""
    crud.update_solve_session_status(fresh_db, idle_session, "error")
    result = machine.transition(fresh_db, idle_session, "idle")
    assert result == "idle"


def test_legal_transition_done_to_idle(fresh_db, machine, idle_session):
    """done → idle is legal (start a new run)."""
    crud.update_solve_session_status(fresh_db, idle_session, "done")
    result = machine.transition(fresh_db, idle_session, "idle")
    assert result == "idle"


# ---------------------------------------------------------------------------
# JOB-01: Illegal transitions
# ---------------------------------------------------------------------------

def test_illegal_transition_idle_to_executing(fresh_db, machine, idle_session):
    """idle → executing is illegal — must go through scanning first."""
    with pytest.raises(InvalidTransitionError, match="Invalid transition"):
        machine.transition(fresh_db, idle_session, "executing")
    row = crud.get_solve_session_by_id(fresh_db, idle_session)
    assert row["status"] == "idle"


def test_illegal_transition_idle_to_solving(fresh_db, machine, idle_session):
    """idle → solving is illegal."""
    with pytest.raises(InvalidTransitionError, match="Invalid transition"):
        machine.transition(fresh_db, idle_session, "solving")


def test_illegal_transition_scanning_to_executing(fresh_db, machine, idle_session):
    """scanning → executing is illegal — must solve first."""
    machine.transition(fresh_db, idle_session, "scanning")
    with pytest.raises(InvalidTransitionError, match="Invalid transition"):
        machine.transition(fresh_db, idle_session, "executing")


def test_illegal_transition_idle_to_done(fresh_db, machine, idle_session):
    """idle → done is illegal."""
    with pytest.raises(InvalidTransitionError, match="Invalid transition"):
        machine.transition(fresh_db, idle_session, "done")


def test_illegal_transition_scanning_to_done(fresh_db, machine, idle_session):
    """scanning → done is illegal (skip solve/execute)."""
    machine.transition(fresh_db, idle_session, "scanning")
    with pytest.raises(InvalidTransitionError, match="Invalid transition"):
        machine.transition(fresh_db, idle_session, "done")


# ---------------------------------------------------------------------------
# JOB-02: Scanning → solving requires valid cube state
# ---------------------------------------------------------------------------

def test_scanning_to_solving_no_cube_state(fresh_db, machine, idle_session):
    """scanning → solving blocked when no cube state exists."""
    machine.transition(fresh_db, idle_session, "scanning")
    with pytest.raises(InvalidTransitionError, match="no valid cube state"):
        machine.transition(fresh_db, idle_session, "solving")


def test_scanning_to_solving_invalid_cube_state(fresh_db, machine, idle_session):
    """scanning → solving blocked when cube state exists but is_valid=False."""
    machine.transition(fresh_db, idle_session, "scanning")
    crud.create_cube_state(
        fresh_db,
        CubeStateCreate(
            session_id=idle_session,
            source="camera",
            state_string="X" * 54,
            is_valid=False,
            confidence=0.3,
        ),
    )
    with pytest.raises(InvalidTransitionError, match="no valid cube state"):
        machine.transition(fresh_db, idle_session, "solving")


# ---------------------------------------------------------------------------
# JOB-03: Solving → executing requires solution
# ---------------------------------------------------------------------------

def test_solving_to_executing_no_solution(fresh_db, machine, idle_session):
    """solving → executing blocked when no solution exists."""
    machine.transition(fresh_db, idle_session, "scanning")
    crud.create_cube_state(
        fresh_db,
        CubeStateCreate(
            session_id=idle_session, source="camera",
            state_string="U" * 54, is_valid=True, confidence=0.95,
        ),
    )
    machine.transition(fresh_db, idle_session, "solving")
    with pytest.raises(InvalidTransitionError, match="no solution"):
        machine.transition(fresh_db, idle_session, "executing")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_session_not_found_raises_value_error(fresh_db, machine):
    """Transitioning a non-existent session raises ValueError."""
    with pytest.raises(ValueError, match="not found"):
        machine.transition(fresh_db, 99999, "scanning")


def test_transition_to_error_from_all_active_states(fresh_db, machine, idle_session):
    """Any active state can transition to error (heartbeat failure path)."""
    for active_state in ("scanning", "solving", "executing"):
        crud.update_solve_session_status(fresh_db, idle_session, active_state)
        result = machine.transition(fresh_db, idle_session, "error")
        assert result == "error"
        # Reset for next iteration
        crud.update_solve_session_status(fresh_db, idle_session, "idle")


def test_valid_transitions_table_has_all_states():
    """VALID_TRANSITIONS covers all required pipeline states."""
    from backend.job_state import VALID_TRANSITIONS
    required_states = {"idle", "pending", "scanning", "solving", "executing", "done", "error"}
    assert required_states <= set(VALID_TRANSITIONS.keys()), (
        f"Missing states: {required_states - set(VALID_TRANSITIONS.keys())}"
    )


# ---------------------------------------------------------------------------
# JOB-05: Control flag CRUD operations
# ---------------------------------------------------------------------------

def test_create_and_read_control_flag(fresh_db, idle_session):
    """Control flags can be created and read back as pending."""
    control_id = crud.create_job_control(
        fresh_db,
        JobControlCreate(
            session_id=idle_session,
            action="start",
            issued_by="gui",
        ),
    )
    assert control_id is not None
    assert control_id > 0
    pending = crud.get_pending_controls(fresh_db, idle_session)
    assert len(pending) == 1
    assert pending[0]["action"] == "start"
    assert pending[0]["issued_by"] == "gui"
    assert pending[0]["status"] == "pending"


def test_ack_control_flag_removes_from_pending(fresh_db, idle_session):
    """Acknowledging a control flag removes it from the pending list."""
    control_id = crud.create_job_control(
        fresh_db,
        JobControlCreate(
            session_id=idle_session,
            action="stop",
            issued_by="gui",
        ),
    )
    crud.ack_job_control(fresh_db, control_id)
    pending = crud.get_pending_controls(fresh_db, idle_session)
    assert len(pending) == 0


def test_multiple_control_flags_pending(fresh_db, idle_session):
    """Multiple control flags can be pending for the same session."""
    for action in ("start", "stop", "reset", "rescan"):
        crud.create_job_control(
            fresh_db,
            JobControlCreate(
                session_id=idle_session,
                action=action,
                issued_by="gui",
            ),
        )
    pending = crud.get_pending_controls(fresh_db, idle_session)
    assert len(pending) == 4
    actions = {p["action"] for p in pending}
    assert actions == {"start", "stop", "reset", "rescan"}


def test_ack_only_affects_target_flag(fresh_db, idle_session):
    """Acknowledging one flag leaves others pending."""
    id1 = crud.create_job_control(
        fresh_db,
        JobControlCreate(session_id=idle_session, action="start", issued_by="gui"),
    )
    crud.create_job_control(
        fresh_db,
        JobControlCreate(session_id=idle_session, action="stop", issued_by="gui"),
    )
    crud.ack_job_control(fresh_db, id1)
    pending = crud.get_pending_controls(fresh_db, idle_session)
    assert len(pending) == 1
    assert pending[0]["action"] == "stop"
