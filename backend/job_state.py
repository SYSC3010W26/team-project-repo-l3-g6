"""
============================================================
SYSC3010 L3-G6 — Job State Machine
Done By : Saim Hashmi

Enforces Idle → Scanning → Solving → Executing → Done/Error
pipeline ordering. Stateless between requests — all state is
read from and written to solve_sessions.status in the DB.
Satisfies TEST-02: testable by passing a mock sqlite3.Connection.
============================================================
"""
import sqlite3
from typing import Optional

from database import crud


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""
    pass


# Valid transitions: {from_state: [allowed_to_states]}
VALID_TRANSITIONS: dict[str, list[str]] = {
    "idle":      ["scanning"],
    "pending":   ["scanning"],
    "scanning":  ["solving", "error"],
    "solving":   ["executing", "error"],
    "executing": ["done", "error"],
    "done":      ["idle"],
    "error":     ["idle"],
}

# Terminal states that accept completed_at
TERMINAL_STATES = {"done", "error", "completed", "cancelled", "failed"}


class JobStateMachine:
    """
    Stateless validator for solve session state transitions.

    Usage:
        machine = JobStateMachine()
        machine.transition(conn, session_id, "scanning")
    """

    def transition(self, conn: sqlite3.Connection, session_id: int, to_state: str) -> str:
        """
        Validate and execute a state transition.

        Returns the new status string on success.
        Raises InvalidTransitionError on illegal transition.
        Raises ValueError if session does not exist.
        """
        session = crud.get_solve_session_by_id(conn, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        from_state = session["status"]
        allowed = VALID_TRANSITIONS.get(from_state, [])

        if to_state not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {from_state} \u2192 {to_state}"
            )

        # Pre-transition guards
        if to_state == "solving":
            self._require_valid_cube_state(conn, session_id)
        elif to_state == "executing":
            self._require_solution(conn, session_id)

        crud.update_solve_session_status(conn, session_id, to_state)
        return to_state

    # ------------------------------------------------------------------
    # Pre-transition guards (JOB-02, JOB-03)
    # ------------------------------------------------------------------

    def _require_valid_cube_state(self, conn: sqlite3.Connection, session_id: int) -> None:
        """JOB-02: Solve only starts after a valid cube state exists (is_valid=1)."""
        row = conn.execute(
            "SELECT id FROM cube_states WHERE session_id = ? AND is_valid = 1 LIMIT 1",
            (session_id,),
        ).fetchone()
        if not row:
            raise InvalidTransitionError(
                f"Cannot transition to solving: no valid cube state found for session {session_id}"
            )

    def _require_solution(self, conn: sqlite3.Connection, session_id: int) -> None:
        """JOB-03: Execute only starts after a solution exists in DB."""
        row = conn.execute(
            "SELECT id FROM solutions WHERE session_id = ? LIMIT 1",
            (session_id,),
        ).fetchone()
        if not row:
            raise InvalidTransitionError(
                f"Cannot transition to executing: no solution found for session {session_id}"
            )
