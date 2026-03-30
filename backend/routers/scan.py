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
import logging
from database import crud
from database.models import CubeStateCreate
from backend.deps import get_db_dep
from backend import schemas

logger = logging.getLogger(__name__)

router = APIRouter()


def validate_state_string(state_string: str) -> tuple[bool, str]:
    """
    Validate a cube state string.
    
    Requirements:
    - Exactly 54 characters (6 faces × 9 stickers)
    - No '?' characters (all colours must be recognized)
    - Valid Rubik's cube colour letters: W, Y, R, O, B, G
    
    Returns:
        (is_valid: bool, error_message: str or empty if valid)
    """
    if not state_string:
        return False, "state_string cannot be empty"
    
    if len(state_string) != 54:
        return False, f"state_string must be exactly 54 characters (got {len(state_string)})"
    
    if "?" in state_string:
        unknown_count = state_string.count("?")
        return False, f"state_string contains {unknown_count} unrecognized colour(s). Please retake the scan."
    
    valid_colours = set("WYROBG")
    invalid_colours = set(state_string) - valid_colours
    if invalid_colours:
        return False, f"state_string contains invalid colour(s): {', '.join(sorted(invalid_colours))}"
    
    return True, ""


@router.post("/submit", response_model=schemas.ScanSubmitResponse)
def submit_scan(body: schemas.ScanSubmitRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    """
    Submit a scanned cube state for a session.
    
    Validates:
    - Session exists
    - state_string is valid (54 chars, no '?', valid colours)
    
    Returns:
        {cube_state_id: int} on success
    
    Error responses:
    - 404: Session not found
    - 400: Invalid state_string
    """
    
    # Verify session exists
    session = crud.get_solve_session_by_id(conn, body.session_id)
    if not session:
        logger.warning(f"Scan submit rejected: Session {body.session_id} not found")
        raise HTTPException(status_code=404, detail=f"Session {body.session_id} not found")
    
    # Validate state string format and contents
    is_valid, error_msg = validate_state_string(body.state_string)
    if not is_valid:
        logger.warning(f"Scan submit rejected for session {body.session_id}: {error_msg}. State: {body.state_string}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Log successful validation
    logger.info(
        f"Scan submit validated for session {body.session_id}: "
        f"state_string={body.state_string[:20]}..., "
        f"is_valid={body.is_valid}, confidence={body.confidence:.1%}"
    )
    
    # Create cube state record
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
    
    logger.info(f"Cube state {cube_state_id} created for session {body.session_id}")
    
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
