"""
============================================================
SYSC3010 L3-G6 — Scan Router
Done By : Saim Hashmi

Implements POST /scan/submit and GET /scan/{session_id}.
All DB access via database.crud functions through Depends(get_db_dep).
============================================================
"""
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from database import crud
from database.models import CubeStateCreate
from backend.deps import get_db_dep
from backend import schemas

router = APIRouter()


@router.post("/submit", response_model=schemas.ScanSubmitResponse)
def submit_scan(body: schemas.ScanSubmitRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    # Verify session exists
    session = crud.get_solve_session_by_id(conn, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
    data = CubeStateCreate(
        session_id=body.session_id,
        source="scanner",
        state_string=body.state_string,
        is_valid=body.is_valid,
        confidence=body.confidence,
    )
    cube_state_id = crud.create_cube_state(conn, data)
    # Update session status to scanning
    crud.update_solve_session_status(conn, body.session_id, "scanning")
    return schemas.ScanSubmitResponse(cube_state_id=cube_state_id)


@router.get("/{session_id}", response_model=schemas.ScanResultResponse)
def get_scan(session_id: int, conn: sqlite3.Connection = Depends(get_db_dep)):
    rows = crud.get_cube_states_by_session(conn, session_id)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No scan results for session {session_id}")
    latest = rows[-1]  # Most recent scan
    return schemas.ScanResultResponse(
        session_id=latest["session_id"],
        state_string=latest["state_string"],
        is_valid=bool(latest["is_valid"]),
        confidence=latest.get("confidence"),
        created_at=latest["created_at"],
    )
