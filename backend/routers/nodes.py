"""
============================================================
SYSC3010 L3-G6 — Nodes Router
Done By : Saim Hashmi

Implements POST /nodes/heartbeat and GET /nodes/status.
All DB access via database.crud functions through Depends(get_db_dep).
============================================================
"""
from fastapi import APIRouter, Depends
import sqlite3
from datetime import datetime, timezone
from database import crud
from database.models import NodeStatusUpsert
from backend.deps import get_db_dep
from backend import schemas

router = APIRouter()


@router.post("/heartbeat", response_model=schemas.MessageResponse)
def submit_heartbeat(body: schemas.HeartbeatRequest, conn: sqlite3.Connection = Depends(get_db_dep)):
    data = NodeStatusUpsert(
        node_id=body.node_id,
        node_type=body.node_type,
        ip_address=body.ip_address,
        status=body.status,
        last_heartbeat=datetime.now(timezone.utc),
        last_message=body.last_message,
    )
    crud.upsert_heartbeat(conn, data)
    return schemas.MessageResponse(message="Heartbeat recorded")


@router.get("/status", response_model=list[schemas.NodeStatusResponse])
def get_node_status(conn: sqlite3.Connection = Depends(get_db_dep)):
    rows = crud.get_all_nodes(conn)
    return [
        schemas.NodeStatusResponse(
            node_id=r["node_id"],
            node_type=r["node_type"],
            ip_address=r.get("ip_address"),
            status=r["status"],
            last_heartbeat=r["last_heartbeat"],
            last_message=r.get("last_message"),
        )
        for r in rows
    ]
