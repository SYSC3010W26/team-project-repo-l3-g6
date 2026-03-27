"""
============================================================
SYSC3010 L3-G6 — Logs Router
Done By : Saim Hashmi

Implements GET /logs with optional severity and node filters.
Uses direct read-only SELECT on system_logs (no get_logs() in crud.py —
adding one is out of scope per Phase 02 decision, direct SQL is acceptable here).
Field 'level' in DB is exposed as 'severity' in the API to match the frontend
SystemLog interface (gap closure plan 04-04).
============================================================
"""
from fastapi import APIRouter, Depends, Query
import sqlite3
from backend.deps import get_db_dep
from backend import schemas

router = APIRouter()


@router.get("", response_model=list[schemas.LogEntryResponse])
def get_logs(
    severity: str | None = Query(None, description="Filter by severity (info, warning, error, fatal)"),
    node: str | None = Query(None, description="Filter by node_id (scanner, solver, motor, database)"),
    limit: int = Query(50, ge=1, le=500),
    conn: sqlite3.Connection = Depends(get_db_dep),
):
    query = "SELECT * FROM system_logs"
    params: list = []
    conditions: list[str] = []

    if severity:
        conditions.append("level = ?")
        params.append(severity)
    if node:
        conditions.append("node_id = ?")
        params.append(node)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [
        schemas.LogEntryResponse(
            id=r["id"],
            session_id=r["session_id"],
            node_id=r["node_id"],
            severity=r["level"],          # DB column is 'level', API field is 'severity'
            event_type=r["event_type"],
            message=r["message"],
            metadata=r["metadata"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
