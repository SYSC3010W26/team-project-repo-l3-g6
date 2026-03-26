"""
============================================================
SYSC3010 L3-G6 — Heartbeat Monitor Background Task
Done By : Saim Hashmi

Polls node_status every 2 seconds. If any Pi's last_heartbeat
is older than 5 seconds AND there is an active job, the job
transitions to Error state (JOB-04).

Started via asyncio.create_task in main.py startup event (D-08).
============================================================
"""
import asyncio
from datetime import datetime, timezone, timedelta

from database.db import db_session
from database import crud
from database.models import SystemLogCreate
from backend.sio_instance import sio
from backend.job_state import JobStateMachine, InvalidTransitionError

# Constants from CONTEXT.md decisions D-09, D-10, D-11
HEARTBEAT_CHECK_INTERVAL = 2   # seconds between checks
HEARTBEAT_DEAD_THRESHOLD = 5   # seconds before a Pi is considered dead

_state_machine = JobStateMachine()


async def heartbeat_monitor() -> None:
    """Background task: detect dead Pis every 2 seconds, error active jobs.

    D-09: Checks every 2 seconds.
    D-10: On dead Pi during active job → Error state + FATAL log + broadcast.
    D-11: Only fires Error if there is an active job (not idle/done/error).
    """
    while True:
        try:
            await asyncio.sleep(HEARTBEAT_CHECK_INTERVAL)

            with db_session() as conn:
                # Fetch all registered nodes
                all_nodes = crud.get_all_nodes(conn)
                if not all_nodes:
                    continue

                # Identify stale nodes (last_heartbeat > 5 seconds ago)
                now = datetime.now(timezone.utc)
                stale_nodes = []
                for node in all_nodes:
                    last_hb = node.get("last_heartbeat")
                    if not last_hb:
                        continue
                    try:
                        hb_time = datetime.fromisoformat(last_hb)
                        # Ensure timezone-aware comparison
                        if hb_time.tzinfo is None:
                            hb_time = hb_time.replace(tzinfo=timezone.utc)
                        if (now - hb_time) > timedelta(seconds=HEARTBEAT_DEAD_THRESHOLD):
                            stale_nodes.append(node)
                    except (ValueError, TypeError):
                        continue

                if not stale_nodes:
                    continue

                # Find active jobs (status not in idle/done/error)
                active_jobs = conn.execute(
                    "SELECT id FROM solve_sessions "
                    "WHERE status IN ('scanning', 'solving', 'executing')"
                ).fetchall()

                if not active_jobs:
                    # D-11: Stale Pis when no active job → log only, no Error
                    stale_ids = ", ".join(n["node_id"] for n in stale_nodes)
                    crud.create_log(
                        conn,
                        SystemLogCreate(
                            level="WARNING",
                            event_type="heartbeat_stale",
                            message=f"Stale Pi(s) detected (no active job): {stale_ids}",
                        ),
                    )
                    continue

                # Error each active job (D-10)
                stale_ids = ", ".join(n["node_id"] for n in stale_nodes)
                for job in active_jobs:
                    session_id = job["id"]
                    try:
                        _state_machine.transition(conn, session_id, "error")

                        # Write FATAL system log entry
                        crud.create_log(
                            conn,
                            SystemLogCreate(
                                session_id=session_id,
                                level="FATAL",
                                event_type="heartbeat_failure",
                                message=(
                                    f"Active job {session_id} transitioned to Error: "
                                    f"stale Pi(s) detected: {stale_ids}"
                                ),
                            ),
                        )

                        # Broadcast to GUI
                        await sio.emit(
                            "job_state_update",
                            {
                                "session_id": session_id,
                                "status": "error",
                                "node_status": {},
                            },
                        )
                    except InvalidTransitionError:
                        # Job may have already transitioned (race); safe to ignore
                        pass
                    except ValueError:
                        # Session not found (deleted); safe to ignore
                        pass

        except Exception as e:
            # D-08: Loop must survive exceptions and keep polling
            print(f"[heartbeat_monitor] Error: {e}")
