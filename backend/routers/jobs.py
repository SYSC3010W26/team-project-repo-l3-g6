"""
============================================================
SYSC3010 L3-G6 — Jobs Router
Done By : Saim Hashmi

Implements POST /jobs/start and GET /jobs/{session_id}.
All DB access via database.crud functions through Depends(get_db_dep).
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from database import crud
from database.models import SolveSessionCreate, JobControlCreate
from database.crud import create_job_control, get_pending_controls, ack_job_control
from backend.deps import get_db_dep
from backend import schemas
from backend.job_state import JobStateMachine, InvalidTransitionError
from backend.sio_instance import sio

router = APIRouter()


@router.post("/start", response_model=schemas.JobStartResponse, status_code=201)
def start_job(body: schemas.JobStartRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    data = SolveSessionCreate(
        selected_algorithm=body.algorithm,
        status="pending",
        session_name=body.session_name,
    )
    session_id = crud.create_solve_session(conn, data)
    return schemas.JobStartResponse(session_id=session_id)


@router.get("/{session_id}", response_model=schemas.JobStateResponse)
def get_job(session_id: int, conn: sqlite3.Connection = Depends(get_db_dep)):
    row = crud.get_solve_session_by_id(conn, session_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return schemas.JobStateResponse(
        session_id=row["id"],
        status=row["status"],
        started_at=row["started_at"],
        completed_at=row.get("completed_at"),
        selected_algorithm=row["selected_algorithm"],
    )


_state_machine = JobStateMachine()


@router.post("/{session_id}/transition", response_model=schemas.JobTransitionResponse)
async def transition_job(
    session_id: int,
    body: schemas.JobTransitionRequest,
    conn: sqlite3.Connection = Depends(get_db_dep),
):
    """Validate and execute a job state transition.

    Called by Pi subsystems and GUI actions (D-05, D-07).
    Illegal transitions return 400. Session not found returns 404.
    Broadcasts job_state_update via Socket.IO on success.
    """
    session = crud.get_solve_session_by_id(conn, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    previous_status = session["status"]
    try:
        new_status = _state_machine.transition(conn, session_id, body.to)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    await sio.emit(
        "job_state_update",
        {"session_id": session_id, "status": new_status, "node_status": {}},
    )
    return schemas.JobTransitionResponse(
        session_id=session_id,
        previous_status=previous_status,
        new_status=new_status,
    )


@router.post("/{session_id}/control", response_model=schemas.ControlFlagResponse, status_code=201)
async def post_control_flag(
    session_id: int,
    body: schemas.ControlFlagRequest,
    conn: sqlite3.Connection = Depends(get_db_dep),
):
    """Write a control flag (Start, Stop, Reset, Rescan) observable by all Pis (JOB-05)."""
    session = crud.get_solve_session_by_id(conn, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    from datetime import datetime, timezone
    issued_at = datetime.now(timezone.utc).isoformat()
    control_id = create_job_control(
        conn,
        JobControlCreate(
            session_id=session_id,
            action=body.action,
            issued_by=body.issued_by,
            issued_at=issued_at,
        ),
    )
    await sio.emit(
        "control_flag",
        {"session_id": session_id, "action": body.action, "control_id": control_id},
    )
    return schemas.ControlFlagResponse(
        control_id=control_id,
        session_id=session_id,
        action=body.action,
        issued_by=body.issued_by,
        issued_at=issued_at,
        status="pending",
    )


@router.get("/{session_id}/control", response_model=list[schemas.ControlFlagResponse])
def get_control_flags(
    session_id: int,
    conn: sqlite3.Connection = Depends(get_db_dep),
):
    """Return all pending control flags for a session (JOB-05, D-13)."""
    session = crud.get_solve_session_by_id(conn, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    rows = get_pending_controls(conn, session_id)
    return [
        schemas.ControlFlagResponse(
            control_id=r["id"],
            session_id=r["session_id"],
            action=r["action"],
            issued_by=r["issued_by"],
            issued_at=r["issued_at"],
            status=r["status"],
        )
        for r in rows
    ]


@router.post("/{session_id}/control/ack", response_model=schemas.MessageResponse)
def ack_control_flag(
    session_id: int,
    body: schemas.ControlAckRequest,
    conn: sqlite3.Connection = Depends(get_db_dep),
):
    """Acknowledge a pending control flag (D-14)."""
    ack_job_control(conn, body.control_id)
    return schemas.MessageResponse(message=f"Control flag {body.control_id} acknowledged")
