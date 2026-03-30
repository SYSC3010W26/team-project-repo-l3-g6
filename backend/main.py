"""
============================================================
SYSC3010 L3-G6 — FastAPI Backend Entry Point
Done By : Saim Hashmi

Creates the FastAPI app, wraps it with python-socketio ASGI for
shared-port WebSocket support, applies CORS middleware, and
includes all route routers.

Entry point for uvicorn:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000

- `app`         — socketio.ASGIApp (uvicorn entry point)
- `fastapi_app` — FastAPI app (use with TestClient in tests)
- `sio`         — socketio.AsyncServer (Socket.IO event handlers attach here)
============================================================
"""
import asyncio
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.sio_instance import sio
from backend.routers import jobs, scan, solve, execute, nodes, logs
from backend.heartbeat import heartbeat_monitor
from backend.motor_timeout import motor_execution_timeout_monitor
from database.init_db import create_tables
from database.db import get_db

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

fastapi_app = FastAPI(title="Rubik's Cube Solver API", version="1.0.0")

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Background tasks — started when FastAPI boots
# ---------------------------------------------------------------------------

@fastapi_app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks on server boot (D-08)."""
    # Initialize database schema if tables don't exist
    conn = get_db()
    try:
        create_tables(conn)
    finally:
        conn.close()
    
    # Start background tasks
    asyncio.create_task(heartbeat_monitor())
    asyncio.create_task(motor_execution_timeout_monitor())

# ---------------------------------------------------------------------------
# ASGI composition — sio wraps fastapi_app so both share port 8000
# ---------------------------------------------------------------------------

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@fastapi_app.get("/")
def health_check():
    return {"status": "ok", "service": "rubiks-solver-api"}

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

fastapi_app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
fastapi_app.include_router(scan.router, prefix="/api/scan", tags=["scan"])
fastapi_app.include_router(solve.router, prefix="/api/solve", tags=["solve"])
fastapi_app.include_router(execute.router, prefix="/api/execute", tags=["execute"])
fastapi_app.include_router(nodes.router, prefix="/api/nodes", tags=["nodes"])
fastapi_app.include_router(logs.router, prefix="/api/logs", tags=["logs"])

# Register Socket.IO event handlers (must import after sio is created)
import backend.socket_handlers  # noqa: F401, E402
