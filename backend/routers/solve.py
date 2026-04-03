"""
============================================================
SYSC3010 L3-G6 — Solve Router
Done By : Saim Hashmi

Implements POST /solve/start (trigger solver), POST /solve/submit (manual), 
and GET /solve/{session_id}.
All DB access via database.crud functions through Depends(get_db_dep).
============================================================
"""
import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from database import crud
from database.models import SolutionCreate, SolutionStepCreate, ExecutionRunCreate
from database.crud import create_execution_run
from backend.deps import get_db_dep
from backend import schemas
from backend.sio_instance import sio

router = APIRouter()


def parse_moves(solution_string: str) -> list[dict]:
    """Parse a Rubik's cube solution string into a list of step data."""
    if not solution_string:
        return []

    moves = solution_string.split()
    steps = []
    for i, move in enumerate(moves):
        # Move format: F, F', F2, F2'
        face = move[0]
        direction = "CW"
        degrees = 90

        if len(move) > 1:
            suffix = move[1:]
            if suffix == "2":
                degrees = 180
            elif suffix == "'":
                direction = "CCW"
            elif suffix == "2'":
                degrees = 180
                direction = "CCW"

        steps.append({
            "step_index": i,
            "face": face,
            "direction": direction,
            "degrees": degrees
        })
    return steps


@router.post("/start", response_model=schemas.SolveStartResponse)
async def start_solve(body: schemas.SolveStartRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    """
    Acknowledge the solve request and transition session to 'solving' state.
    
    Prerequisites:
    - Session must exist
    - Valid cube state must have been scanned (in cube_states table)
    
    Returns:
    - session_id: ID of the session
    - status: current state of the session (solving)
    """
    # Fetch the session
    session = crud.get_solve_session_by_id(conn, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
    
    # Fetch the most recent valid cube state
    cube_states = crud.get_cube_states_by_session(conn, body.session_id)
    valid_states = [s for s in cube_states if s["is_valid"]]
    if not valid_states:
        raise HTTPException(status_code=400, detail="No valid cube state scanned yet")
    
    # Transition to 'solving' state
    # This acts as a signal for the external solver daemon
    crud.update_solve_session_status(conn, body.session_id, "solving")
    
    # Emit start event via socket.io
    await sio.emit("solve_started", {
        "session_id": body.session_id,
        "status": "solving"
    })
    
    return schemas.SolveStartResponse(
        session_id=body.session_id,
        status="solving"
    )


@router.post("/submit", response_model=schemas.SolveSubmitResponse)
async def submit_solution(body: schemas.SolveSubmitRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    session = crud.get_solve_session_by_id(conn, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")

    # Create the solution record
    data = SolutionCreate(
        session_id=body.session_id,
        algorithm_used=body.algorithm_used,
        move_count=body.move_count,
        solution_string=body.solution_string,
    )
    solution_id = crud.create_solution(conn, data)

    # Parse and store individual steps
    steps_data = parse_moves(body.solution_string)
    for step in steps_data:
        crud.create_solution_step(
            conn,
            SolutionStepCreate(
                solution_id=solution_id,
                **step
            )
        )

    # Emit solve_complete to dashboard
    await sio.emit("solve_complete", {
        "session_id": body.session_id,
        "solution_id": solution_id,
        "move_count": body.move_count,
        "solution_string": body.solution_string
    })

    # Auto-trigger motor execution: transition to executing, emit to Motor Pi
    crud.update_solve_session_status(conn, body.session_id, "executing")
    create_execution_run(conn, ExecutionRunCreate(
        session_id=body.session_id,
        solution_id=solution_id,
        status="executing",
        motor_node_id="motor-node",
    ))

    # Send moves to Motor Pi via Socket.IO
    await sio.emit("load_moves", {"moves": body.solution_string})
    await sio.emit("start_solve", {})

    # Broadcast executing state to dashboard
    await sio.emit("job_state_update", {
        "session_id": body.session_id,
        "status": "executing",
        "node_status": {},
    })

    return schemas.SolveSubmitResponse(solution_id=solution_id)


@router.get("/{session_id}", response_model=schemas.SolveResultResponse)
def get_solution(session_id: int, conn: sqlite3.Connection = Depends(get_db_dep)):
    rows = crud.get_solutions_by_session(conn, session_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No solution for session {session_id}")
    latest = rows[-1]
    step_rows = crud.get_solution_steps_by_solution(conn, latest["id"])
    steps = []
    for s in step_rows:
        notation = s["face"]
        if s["degrees"] == 180:
            notation += "2"
        if s["direction"] == "CCW":
            notation += "'"
        steps.append(schemas.SolutionStepResponse(
            step_index=s["step_index"],
            move_notation=notation,
        ))
    return schemas.SolveResultResponse(
        session_id=latest["session_id"],
        solution_id=latest["id"],
        algorithm_used=latest["algorithm_used"],
        move_count=latest["move_count"],
        solution_string=latest.get("solution_string"),
        generated_at=latest["generated_at"],
        steps=steps,
    )
