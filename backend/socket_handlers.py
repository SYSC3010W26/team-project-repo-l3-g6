"""
============================================================
SYSC3010 L3-G6 — Socket.IO Event Handlers (Motor Pi inbound)
Done By : Saim Hashmi

Registers @sio.on handlers on the AsyncServer created in main.py.
Imported by main.py AFTER sio is created to trigger registration.

Motor Pi event contract (see motorctl/src/server_bridge.py):
  - 'state_change' {'node_id': str, 'state': str}
  - 'log'          {'node_id': str, 'msg': str}
  - 'complete'     {'node_id': str, 'status': 'success'|'failed'}
  NOTE: Motor Pi emits 'complete' — see motorctl/src/server_bridge.py line 49

Server broadcasts to frontend (D-04):
  - 'job_state_update'     {'session_id': int|None, 'status': str, 'node_status': dict}
  - 'execution_progress'   {'session_id': int, 'current_step': int, ...}
============================================================
"""

from datetime import datetime, timezone

from backend.sio_instance import sio
from database.db import db_session
from database import crud
from database.models import SystemLogCreate, NodeStatusUpsert


# ---------------------------------------------------------------------------
# Connection lifecycle
# ---------------------------------------------------------------------------

@sio.on("connect")
async def on_connect(sid, environ):
    print(f"[SocketIO] Client connected: {sid}")


@sio.on("disconnect")
async def on_disconnect(sid):
    print(f"[SocketIO] Client disconnected: {sid}")


# ---------------------------------------------------------------------------
# Motor Pi inbound events
# ---------------------------------------------------------------------------

@sio.on("state_change")
async def on_state_change(sid, data):
    """Motor Pi state machine transition notification.

    Receives: {'node_id': str, 'state': str}
    Writes a system log entry, then broadcasts job_state_update to all clients.
    """
    node_id = data.get("node_id", "unknown")
    state = data.get("state", "unknown")

    with db_session() as conn:
        crud.create_log(
            conn,
            SystemLogCreate(
                node_id=node_id,
                level="INFO",
                event_type="state_change",
                message=f"Node {node_id} transitioned to state: {state}",
            ),
        )

    await sio.emit(
        "job_state_update",
        {"session_id": None, "status": state, "node_status": {}},
    )


@sio.on("complete")
# Motor Pi emits 'complete' — see motorctl/src/server_bridge.py line 49
async def on_complete(sid, data):
    """Motor Pi execution finished notification.

    Receives: {'node_id': str, 'status': 'success'|'failed'}
    Writes a system log entry, updates the active execution session to done/error,
    then broadcasts job_state_update with terminal status.
    """
    node_id = data.get("node_id", "unknown")
    status = data.get("status", "unknown")
    broadcast_status = "done" if status == "success" else "error"

    session_id = None
    with db_session() as conn:
        crud.create_log(
            conn,
            SystemLogCreate(
                node_id=node_id,
                level="INFO",
                event_type="execution_complete",
                message=f"Node {node_id} execution finished with status: {status}",
            ),
        )
        # Find the executing session and transition it to done/error
        row = conn.execute(
            "SELECT id FROM solve_sessions WHERE status = 'executing' ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        if row:
            session_id = row[0]
            crud.update_solve_session_status(conn, session_id, broadcast_status)
            # Mark the execution run as completed/failed
            run_row = conn.execute(
                "SELECT id FROM execution_runs WHERE session_id = ? AND status = 'executing' ORDER BY started_at DESC LIMIT 1",
                (session_id,)
            ).fetchone()
            if run_row:
                db_run_status = "completed" if status == "success" else "failed"
                crud.update_execution_run_status(conn, run_row[0], db_run_status)

    await sio.emit(
        "job_state_update",
        {"session_id": session_id, "status": broadcast_status, "node_status": {}},
    )


@sio.on("log")
async def on_log(sid, data):
    """Motor Pi log message.

    Receives: {'node_id': str, 'msg': str}
    Writes a system log entry (no broadcast needed for log messages).
    """
    node_id = data.get("node_id", "unknown")
    msg = data.get("msg", "")

    with db_session() as conn:
        crud.create_log(
            conn,
            SystemLogCreate(
                node_id=node_id,
                level="INFO",
                event_type="node_log",
                message=msg,
            ),
        )


@sio.on("heartbeat")
async def on_heartbeat(sid, data):
    """Motor Pi (or any node) heartbeat event.

    Receives: {'node_id': str, 'node_type': str, 'status': str, ...}
    Upserts node status row, then broadcasts job_state_update with updated node list.
    """
    node_id = data.get("node_id", "unknown")
    node_type = data.get("node_type", "unknown")
    status = data.get("status", "online")

    with db_session() as conn:
        crud.upsert_heartbeat(
            conn,
            NodeStatusUpsert(
                node_id=node_id,
                node_type=node_type,
                status=status,
                last_heartbeat=datetime.now(timezone.utc),
            ),
        )
        nodes = crud.get_all_nodes(conn)

    node_status = {n["node_id"]: n["status"] for n in nodes}
    await sio.emit(
        "job_state_update",
        {"session_id": None, "status": "heartbeat", "node_status": node_status},
    )
