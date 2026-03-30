"""
============================================================
SYSC3010 L3-G6 — Motor Execution Timeout Monitor
M004/S04/T05 Implementation

Monitors active motor execution runs. If no progress report
is received within MOTOR_TIMEOUT_SECONDS, marks the run as
failed and transitions the session to error state.

Started via asyncio.create_task in main.py startup event.
============================================================
"""
import asyncio
from datetime import datetime, timezone, timedelta

from database.db import db_session
from database import crud
from database.models import SystemLogCreate
from backend.sio_instance import sio
from backend.job_state import JobStateMachine, InvalidTransitionError

# M004/S04/T05: Motor execution timeout
MOTOR_TIMEOUT_SECONDS = 30
TIMEOUT_CHECK_INTERVAL = 5  # Check every 5 seconds

_state_machine = JobStateMachine()


async def motor_execution_timeout_monitor() -> None:
    """Background task: detect motor execution timeouts every 5 seconds.
    
    If an execution_run in 'executing' status has not received a progress
    report for > 30 seconds, auto-fail it and transition session to error.
    """
    while True:
        try:
            await asyncio.sleep(TIMEOUT_CHECK_INTERVAL)
            
            with db_session() as conn:
                # Find all execution runs currently executing
                executing_runs = conn.execute(
                    "SELECT * FROM execution_runs WHERE status = 'executing'"
                ).fetchall()
                
                if not executing_runs:
                    continue
                
                now = datetime.now(timezone.utc)
                
                for run in executing_runs:
                    run_id = run[0]  # id is first column
                    session_id = run[1]  # session_id is second column
                    
                    # Get the most recent motor log for this run
                    latest_log = conn.execute(
                        "SELECT ts FROM motor_execution_log "
                        "WHERE run_id = ? "
                        "ORDER BY ts DESC LIMIT 1",
                        (run_id,)
                    ).fetchone()
                    
                    if not latest_log:
                        # No progress yet - check run creation time instead
                        run_created = conn.execute(
                            "SELECT created_at FROM execution_runs WHERE id = ?",
                            (run_id,)
                        ).fetchone()
                        if not run_created:
                            continue
                        reference_time_str = run_created[0]
                    else:
                        reference_time_str = latest_log[0]
                    
                    try:
                        reference_time = datetime.fromisoformat(reference_time_str)
                        if reference_time.tzinfo is None:
                            reference_time = reference_time.replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        continue
                    
                    time_elapsed = (now - reference_time).total_seconds()
                    
                    if time_elapsed > MOTOR_TIMEOUT_SECONDS:
                        # Timeout detected - fail the run and error the job
                        crud.update_execution_run_status(conn, run_id, "failed")
                        
                        # Transition session to error
                        try:
                            _state_machine.transition(conn, session_id, "error")
                        except InvalidTransitionError:
                            # May already be in error; safe to ignore
                            pass
                        
                        # Log the timeout
                        crud.create_log(
                            conn,
                            SystemLogCreate(
                                session_id=session_id,
                                level="FATAL",
                                event_type="motor_execution_timeout",
                                message=(
                                    f"Motor execution run {run_id} timed out after "
                                    f"{time_elapsed:.1f}s (threshold: {MOTOR_TIMEOUT_SECONDS}s). "
                                    f"No progress report received."
                                ),
                            ),
                        )
                        
                        # Broadcast timeout event to dashboard
                        await sio.emit("execution_timeout", {
                            "session_id": session_id,
                            "run_id": run_id,
                            "elapsed_seconds": round(time_elapsed, 1),
                            "timeout_threshold": MOTOR_TIMEOUT_SECONDS,
                        })
        
        except Exception as e:
            # Keep monitoring despite errors
            print(f"[motor_execution_timeout_monitor] Error: {e}")
