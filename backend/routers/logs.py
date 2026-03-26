"""
============================================================
SYSC3010 L3-G6 — Logs Router
Done By : Saim Hashmi

Implements GET /logs with optional level filter and limit.
Uses a direct read-only SELECT on system_logs — acceptable because
crud.py only provides create_log(), not a filtered get_logs().
============================================================
"""
from fastapi import APIRouter, Depends, Query
import sqlite3
from backend.deps import get_db_dep
from backend import schemas

router = APIRouter()


@router.get("", response_model=list[schemas.LogEntryResponse])
def get_logs(
    level: str | None = Query(None, description="Filter by log level (INFO, WARNING, ERROR, FATAL)"),
    limit: int = Query(50, ge=1, le=500),
    conn: sqlite3.Connection = Depends(get_db_dep),
):
    query = "SELECT * FROM system_logs"
    params = []
    if level:
        query += " WHERE level = ?"
        params.append(level)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    return [
        schemas.LogEntryResponse(
            id=r["id"],
            session_id=r.get("session_id"),
            node_id=r.get("node_id"),
            level=r["level"],
            event_type=r["event_type"],
            message=r["message"],
            metadata=r.get("metadata"),
            created_at=r["created_at"],
        )
        for r in rows
    ]
