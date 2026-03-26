"""
============================================================
SYSC3010 L3-G6 — Solve Router
Done By : Saim Hashmi

Implements POST /solve/submit and GET /solve/{session_id}.
All DB access via database.crud functions through Depends(get_db_dep).
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from database import crud
from database.models import SolutionCreate
from backend.deps import get_db_dep
from backend import schemas

router = APIRouter()


@router.post("/submit", response_model=schemas.SolveSubmitResponse)
def submit_solution(body: schemas.SolveSubmitRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    session = crud.get_solve_session_by_id(conn, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
    data = SolutionCreate(
        session_id=body.session_id,
        algorithm_used=body.algorithm_used,
        move_count=body.move_count,
        solution_string=body.solution_string,
    )
    solution_id = crud.create_solution(conn, data)
    crud.update_solve_session_status(conn, body.session_id, "solving")
    return schemas.SolveSubmitResponse(solution_id=solution_id)


@router.get("/{session_id}", response_model=schemas.SolveResultResponse)
def get_solution(session_id: int, conn: sqlite3.Connection = Depends(get_db_dep)):
    rows = crud.get_solutions_by_session(conn, session_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No solution for session {session_id}")
    latest = rows[-1]
    return schemas.SolveResultResponse(
        session_id=latest["session_id"],
        solution_id=latest["id"],
        algorithm_used=latest["algorithm_used"],
        move_count=latest["move_count"],
        solution_string=latest.get("solution_string"),
        generated_at=latest["generated_at"],
    )
