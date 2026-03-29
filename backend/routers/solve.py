"""
============================================================
SYSC3010 L3-G6 — Solve Router
Done By : Saim Hashmi

Implements POST /solve/start (trigger solver), POST /solve/submit (manual), 
and GET /solve/{session_id}.
All DB access via database.crud functions through Depends(get_db_dep).
============================================================
"""
import sys
import os
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from database import crud
from database.models import SolutionCreate, SolutionStepCreate
from backend.deps import get_db_dep
from backend import schemas
from backend.sio_instance import sio

router = APIRouter()

# Import solver (add solver directory to path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'solver'))
try:
    from Solver import Solver, CubeNotSolvableError
    SOLVER_AVAILABLE = True
except ImportError:
    SOLVER_AVAILABLE = False


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


@router.post("/start", response_model=schemas.SolveSubmitResponse)
async def start_solve(body: schemas.SolveStartRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    """
    Trigger the CFOP solver to compute a solution for a scanned cube state.
    
    Prerequisites:
    - Session must exist
    - Valid cube state must have been scanned (in cube_states table)
    
    Returns:
    - solution_id: ID of the newly created solution
    """
    if not SOLVER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Solver not available on this system")
    
    # Fetch the session
    session = crud.get_solve_session_by_id(conn, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
    
    # Fetch the most recent valid cube state
    cube_states = crud.get_cube_states_by_session(conn, body.session_id)
    valid_states = [s for s in cube_states if s["is_valid"]]
    if not valid_states:
        raise HTTPException(status_code=400, detail="No valid cube state scanned yet")
    
    latest_state = valid_states[-1]["state_string"]
    
    # Call the solver
    try:
        solver = Solver()
        solver.load_state(latest_state)
        
        if solver.is_solved():
            solution_string = ""  # Already solved
            move_count = 0
        else:
            solution_string = solver.solve()
            move_count = len(solution_string.split()) if solution_string else 0
        
        # Create solution record
        data = SolutionCreate(
            session_id=body.session_id,
            algorithm_used="CFOP",
            move_count=move_count,
            solution_string=solution_string,
        )
        solution_id = crud.create_solution(conn, data)
        
        # Parse and store individual steps
        if solution_string:
            steps_data = parse_moves(solution_string)
            for step in steps_data:
                crud.create_solution_step(
                    conn,
                    SolutionStepCreate(
                        solution_id=solution_id,
                        **step
                    )
                )
        
        # Update session status
        crud.update_solve_session_status(conn, body.session_id, "solved")
        
        # Emit progress via socket.io
        await sio.emit("solve_complete", {
            "session_id": body.session_id,
            "solution_id": solution_id,
            "move_count": move_count,
            "solution_string": solution_string
        })
        
        return schemas.SolveSubmitResponse(solution_id=solution_id)
    
    except CubeNotSolvableError as e:
        crud.update_solve_session_status(conn, body.session_id, "error")
        raise HTTPException(status_code=400, detail=f"Cube state not solvable: {e}")
    except ValueError as e:
        crud.update_solve_session_status(conn, body.session_id, "error")
        raise HTTPException(status_code=400, detail=f"Invalid cube state: {e}")
    except Exception as e:
        crud.update_solve_session_status(conn, body.session_id, "error")
        raise HTTPException(status_code=500, detail=f"Solver error: {e}")


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

    crud.update_solve_session_status(conn, body.session_id, "solving")
    
    # Emit via socket.io
    await sio.emit("solve_complete", {
        "session_id": body.session_id,
        "solution_id": solution_id,
        "move_count": body.move_count,
        "solution_string": body.solution_string
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
