"""
============================================================
SYSC3010 L3-G6 — Execute Router
Done By : Saim Hashmi

Implements POST /execute/start, POST /execute/progress,
and POST /execute/complete.
All DB access via database.crud functions through Depends(get_db_dep).
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from database import crud
from database.models import ExecutionRunCreate, MotorExecutionLogCreate
from backend.deps import get_db_dep
from backend import schemas
from backend.sio_instance import sio

router = APIRouter()


@router.post("/start", response_model=schemas.ExecuteStartResponse)
def start_execution(body: schemas.ExecuteStartRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    session = crud.get_solve_session_by_id(conn, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
    # Verify solution exists
    solutions = crud.get_solutions_by_session(conn, body.session_id)
    matching = [s for s in solutions if s["id"] == body.solution_id]
    if not matching:
        raise HTTPException(status_code=404, detail=f"Solution {body.solution_id} not found for session {body.session_id}")
    data = ExecutionRunCreate(
        session_id=body.session_id,
        solution_id=body.solution_id,
        status="executing",
        motor_node_id=body.motor_node_id,
    )
    run_id = crud.create_execution_run(conn, data)
    crud.update_solve_session_status(conn, body.session_id, "executing")
    return schemas.ExecuteStartResponse(run_id=run_id)


@router.post("/progress", response_model=schemas.MessageResponse)
async def report_progress(body: schemas.ExecuteProgressRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    data = MotorExecutionLogCreate(
        run_id=body.run_id,
        step_index=body.current_step,
        commanded_face=body.move.split()[0] if body.move else "?",
        commanded_dir="CW",
        commanded_deg=90,
        status="completed",
    )
    crud.create_motor_log(conn, data)
    pct = round(body.current_step / body.total_steps * 100, 1) if body.total_steps else 0.0
    await sio.emit("execution_progress", {
        "session_id": body.session_id,
        "run_id": body.run_id,
        "current_step": body.current_step,
        "total_steps": body.total_steps,
        "move": body.move,
        "pct_complete": pct,
    })
    return schemas.MessageResponse(message="Progress recorded")


@router.post("/complete", response_model=schemas.MessageResponse)
def complete_execution(body: schemas.ExecuteCompleteRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    # Map "success" -> "completed", "failed" -> "failed" for DB status
    db_status = "completed" if body.status == "success" else "failed"
    crud.update_execution_run_status(conn, body.run_id, db_status)
    # Update session status
    session_status = "completed" if body.status == "success" else "failed"
    crud.update_solve_session_status(conn, body.session_id, session_status)
    return schemas.MessageResponse(message=f"Execution {db_status}")
