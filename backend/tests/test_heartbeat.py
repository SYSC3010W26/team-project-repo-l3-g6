"""
============================================================
SYSC3010 L3-G6 — Heartbeat Monitor Tests (JOB-04)
Done By : Saim Hashmi

Tests the heartbeat_monitor coroutine logic by running one
iteration at a time with controlled time. Uses temp DB,
no running server (TEST-02 compatible).
============================================================
"""
import asyncio
import os
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest

import database.db as db_module
from database.init_db import create_tables
from database import crud
from database.models import (
    SolveSessionCreate,
    NodeStatusUpsert,
)
from backend.heartbeat import HEARTBEAT_DEAD_THRESHOLD


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_db():
    """Create a fresh temp DB for each test and restore DB_PATH after."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    original = db_module.DB_PATH
    db_module.DB_PATH = path
    os.environ["DATABASE_URL"] = path
    conn = db_module.get_db()
    create_tables(conn)
    conn.commit()
    yield conn
    conn.close()
    db_module.DB_PATH = original
    try:
        os.unlink(path)
    except OSError:
        pass


def _register_node(conn, node_id, last_heartbeat):
    """Insert or update a node with the given heartbeat timestamp."""
    crud.upsert_heartbeat(
        conn,
        NodeStatusUpsert(
            node_id=node_id,
            node_type="pi",
            status="online",
            last_heartbeat=last_heartbeat,
        ),
    )
    conn.commit()


def _create_session_with_status(conn, status):
    """Create a solve session with the specified status; return session_id."""
    sid = crud.create_solve_session(
        conn,
        SolveSessionCreate(selected_algorithm="CFOP", status=status),
    )
    if status != "pending":
        crud.update_solve_session_status(conn, sid, status)
    conn.commit()
    return sid


async def _run_one_heartbeat_iteration(mock_sio_emit=None):
    """
    Run the heartbeat monitor for exactly one loop iteration, then stop.

    Patches:
    - asyncio.sleep: first call returns None (one iteration), second raises CancelledError
    - sio.emit: replaced with an AsyncMock to capture calls without real Socket.IO
    """
    call_count = 0

    async def mock_sleep(seconds):
        nonlocal call_count
        call_count += 1
        if call_count > 1:
            raise asyncio.CancelledError()
        # First call: don't actually sleep, just yield control

    if mock_sio_emit is None:
        mock_sio_emit = AsyncMock()

    with patch("backend.heartbeat.asyncio.sleep", side_effect=mock_sleep):
        with patch("backend.heartbeat.sio.emit", side_effect=mock_sio_emit):
            try:
                from backend.heartbeat import heartbeat_monitor
                await heartbeat_monitor()
            except asyncio.CancelledError:
                pass

    return mock_sio_emit


# ---------------------------------------------------------------------------
# JOB-04: threshold constant
# ---------------------------------------------------------------------------

def test_heartbeat_threshold_is_five_seconds():
    """JOB-04: The heartbeat dead threshold must be exactly 5 seconds."""
    assert HEARTBEAT_DEAD_THRESHOLD == 5


# ---------------------------------------------------------------------------
# JOB-04: Stale Pi with active job → Error
# ---------------------------------------------------------------------------

def test_heartbeat_monitor_errors_stale_pi_with_active_job(fresh_db):
    """Active job transitions to Error when a Pi heartbeat is stale > 5 sec."""
    # Register a node with a stale heartbeat (10 seconds ago)
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    _register_node(fresh_db, "scanner-pi", stale_time)

    # Create a scanning session (active)
    session_id = _create_session_with_status(fresh_db, "scanning")

    # Run one heartbeat iteration
    mock_emit = asyncio.get_event_loop().run_until_complete(
        _run_one_heartbeat_iteration()
    )

    # Verify job is now in error state
    row = crud.get_solve_session_by_id(fresh_db, session_id)
    assert row["status"] == "error", (
        f"Expected status='error', got '{row['status']}'"
    )

    # Verify FATAL log entry written
    logs = fresh_db.execute(
        "SELECT * FROM system_logs WHERE level = 'FATAL' AND event_type = 'heartbeat_failure'"
    ).fetchall()
    assert len(logs) >= 1, "Expected at least one FATAL heartbeat_failure log"

    # Verify Socket.IO broadcast was emitted
    mock_emit.assert_called()
    # Check the broadcast included error status
    call_args = mock_emit.call_args_list[0]
    event_name = call_args[0][0]
    event_data = call_args[0][1]
    assert event_name == "job_state_update"
    assert event_data["status"] == "error"
    assert event_data["session_id"] == session_id


def test_heartbeat_monitor_errors_solving_job_on_stale_pi(fresh_db):
    """Solving job transitions to Error when a Pi heartbeat is stale."""
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=8)
    _register_node(fresh_db, "solver-pi", stale_time)

    session_id = _create_session_with_status(fresh_db, "solving")

    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())

    row = crud.get_solve_session_by_id(fresh_db, session_id)
    assert row["status"] == "error"


def test_heartbeat_monitor_errors_executing_job_on_stale_pi(fresh_db):
    """Executing job transitions to Error when a Pi heartbeat is stale."""
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=7)
    _register_node(fresh_db, "motor-pi", stale_time)

    session_id = _create_session_with_status(fresh_db, "executing")

    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())

    row = crud.get_solve_session_by_id(fresh_db, session_id)
    assert row["status"] == "error"


# ---------------------------------------------------------------------------
# D-11: Stale Pi with non-active job → no Error
# ---------------------------------------------------------------------------

def test_heartbeat_monitor_ignores_stale_pi_when_job_is_idle(fresh_db):
    """D-11: Stale Pi during idle job does NOT trigger Error state."""
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    _register_node(fresh_db, "scanner-pi", stale_time)

    # Session is idle (not active)
    session_id = _create_session_with_status(fresh_db, "idle")

    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())

    row = crud.get_solve_session_by_id(fresh_db, session_id)
    assert row["status"] == "idle", (
        f"Expected status='idle', got '{row['status']}'"
    )


def test_heartbeat_monitor_ignores_stale_pi_when_job_is_done(fresh_db):
    """D-11: Stale Pi during done job does NOT trigger Error state."""
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    _register_node(fresh_db, "scanner-pi", stale_time)

    session_id = _create_session_with_status(fresh_db, "done")
    # Override the completed_at auto-set for done state
    fresh_db.execute(
        "UPDATE solve_sessions SET status = 'done' WHERE id = ?", (session_id,)
    )
    fresh_db.commit()

    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())

    row = crud.get_solve_session_by_id(fresh_db, session_id)
    assert row["status"] == "done"


# ---------------------------------------------------------------------------
# Fresh Pi — no Error triggered
# ---------------------------------------------------------------------------

def test_heartbeat_monitor_ignores_fresh_pi(fresh_db):
    """Fresh heartbeat (1 second ago) does NOT trigger Error for active job."""
    fresh_time = datetime.now(timezone.utc) - timedelta(seconds=1)
    _register_node(fresh_db, "scanner-pi", fresh_time)

    session_id = _create_session_with_status(fresh_db, "scanning")

    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())

    row = crud.get_solve_session_by_id(fresh_db, session_id)
    assert row["status"] == "scanning", (
        f"Expected status='scanning', got '{row['status']}'"
    )


def test_heartbeat_monitor_uses_five_second_boundary(fresh_db):
    """A heartbeat exactly 4 seconds old (< threshold) does NOT trigger Error."""
    # 4 seconds old — under the 5-second threshold
    fresh_enough = datetime.now(timezone.utc) - timedelta(seconds=4)
    _register_node(fresh_db, "scanner-pi", fresh_enough)

    session_id = _create_session_with_status(fresh_db, "scanning")

    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())

    row = crud.get_solve_session_by_id(fresh_db, session_id)
    assert row["status"] == "scanning"


# ---------------------------------------------------------------------------
# Edge cases: empty table, no crash
# ---------------------------------------------------------------------------

def test_heartbeat_monitor_no_nodes_no_crash(fresh_db):
    """Heartbeat monitor handles empty node_status table gracefully (no crash)."""
    # No nodes anywhere
    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())
    # Pass if no exception raised


def test_heartbeat_monitor_no_active_jobs_writes_warning_log(fresh_db):
    """Stale Pi with no active jobs writes a WARNING log (not FATAL)."""
    stale_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    _register_node(fresh_db, "scanner-pi", stale_time)

    # Create idle session only — no active jobs
    _create_session_with_status(fresh_db, "idle")

    asyncio.get_event_loop().run_until_complete(_run_one_heartbeat_iteration())

    # Check for WARNING log (D-11)
    logs = fresh_db.execute(
        "SELECT * FROM system_logs WHERE level = 'WARNING' AND event_type = 'heartbeat_stale'"
    ).fetchall()
    assert len(logs) >= 1, "Expected at least one WARNING heartbeat_stale log"
