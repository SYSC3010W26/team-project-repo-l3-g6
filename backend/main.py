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
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import jobs, scan, solve, execute, nodes, logs

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
# Socket.IO AsyncServer (shared port via ASGI composition)
# ---------------------------------------------------------------------------

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

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

fastapi_app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
fastapi_app.include_router(scan.router, prefix="/scan", tags=["scan"])
fastapi_app.include_router(solve.router, prefix="/solve", tags=["solve"])
fastapi_app.include_router(execute.router, prefix="/execute", tags=["execute"])
fastapi_app.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
fastapi_app.include_router(logs.router, prefix="/logs", tags=["logs"])
