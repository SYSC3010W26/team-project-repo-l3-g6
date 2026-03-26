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
from database.models import SolveSessionCreate
from backend.deps import get_db_dep
from backend import schemas

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
