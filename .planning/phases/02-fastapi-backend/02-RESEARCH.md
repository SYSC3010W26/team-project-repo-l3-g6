# Phase 02: FastAPI Backend - Research

**Researched:** 2026-03-25
**Domain:** FastAPI + python-socketio ASGI integration, REST routing, dependency injection, integration testing
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01** — Server lives in `backend/` package at project root. Structure: `backend/__init__.py`, `backend/main.py` (FastAPI app + socketio app creation), `backend/schemas.py` (API-specific request/response models), `backend/routers/` with `pipeline.py`, `nodes.py`, `status.py`, `ws.py` (or socket event handlers).

**D-02** — API-specific request/response models in `backend/schemas.py` — separate from `database/models.py`. `schemas.py` may import from `database/models.py` where convenient but defines its own lean Pydantic v2 models for each endpoint's input/output contract.

**D-03** — Single `python-socketio` AsyncServer mounted on FastAPI via ASGI. `app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)`. Socket.IO handles `/socket.io/*`, FastAPI handles REST routes. One server, one protocol — both Pi nodes and the Phase 4 frontend use Socket.IO clients.

**D-04** — Server emits two broadcast events:
- `job_state_update` — on any pipeline stage change; payload: `session_id`, `status` (idle|scanning|solving|executing|done|error), `node_status` dict (node name → online bool)
- `execution_progress` — per motor step; payload: `session_id`, `current_step`, `total_steps`, `move`, `pct_complete`

**D-05** — Motor Pi inbound events the server must handle: `heartbeat`, `state_change`, `execution_complete` (and `register`, `load_moves`, `start_solve` for node coordination). Event names match `motorctl/src/server_bridge.py`.

**D-06** — Pipeline-stage-based routing:
```
POST   /jobs/start
GET    /jobs/{session_id}
POST   /scan/submit
GET    /scan/{session_id}
POST   /solve/submit
GET    /solve/{session_id}
POST   /execute/start
POST   /execute/progress
POST   /execute/complete
POST   /nodes/heartbeat
GET    /nodes/status
GET    /logs
```

**D-07** — Error responses use FastAPI defaults: `HTTPException` with `detail` string, automatic 422 for validation errors. No custom envelope.

**D-08** — Integration tests use FastAPI's built-in `TestClient`. No DB mocking — use `tempfile` + `create_tables` fixture pattern from Phase 1 (`database/tests/conftest.py`).

**D-09** — Test files in `backend/tests/`: `conftest.py`, `test_integration.py`, plus per-router tests.

### Claude's Discretion

- CORS configuration — allow all origins (`*`) for LAN dev; Claude can harden if needed.
- Dependency injection pattern for DB connection — how route handlers get a connection (e.g., `Depends(get_db)` or direct import of `db_session()`).
- Whether to include a `GET /` health check root endpoint.
- Socket.IO namespace design — default namespace (`/`) is fine unless Claude sees reason for named namespaces.

### Deferred Ideas (OUT OF SCOPE)

- Authentication / API keys on endpoints — LAN-only, no auth in Phase 2.
- PostgreSQL migration — `db.py` documents the swap; not a Phase 2 deliverable.
- Socket.IO namespaces — add in Phase 3+ if isolation needed.
- `/execute/verify` endpoint for post-solve re-scan — Phase 3 scope.
- Rate limiting / throttling — out of scope for course deliverable.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-01 | FastAPI server runs on Database & GUI Pi and is reachable by all other Pis on local LAN | Uvicorn `--host 0.0.0.0 --port 8000`; CORS allow all origins; socketio.ASGIApp mount |
| API-02 | REST endpoints exist for all pipeline stages (submit/fetch cube state, solution, execution status) | FastAPI routers; Pydantic v2 schemas; CRUD calls from database/crud.py |
| API-03 | WebSocket endpoint streams live job state and execution progress to connected web clients | python-socketio AsyncServer; `sio.emit()` for `job_state_update` and `execution_progress` |
| API-04 | API accepts heartbeat writes from all 4 Pis and updates `node_status` table | `POST /nodes/heartbeat` router + `upsert_node_status` CRUD |
| API-05 | API returns correct HTTP status codes and structured error responses | FastAPI `HTTPException`, automatic 422; Pydantic v2 response_model validation |
| TEST-03 | API endpoints have integration tests covering the happy path (scan → solve → execute flow) | FastAPI TestClient + tempfile DB fixture; `backend/tests/test_integration.py` |
</phase_requirements>

---

## Summary

Phase 2 builds the FastAPI + python-socketio server from scratch. The database layer (Phase 1) is complete and tested — all CRUD functions are ready to call from route handlers. The server must be the integration hub: REST endpoints let Pi nodes submit pipeline data, and Socket.IO broadcasts let the Phase 4 frontend receive real-time updates.

The critical technical challenge is the ASGI composition: `socketio.ASGIApp` wraps the FastAPI app so both can share port 8000. The FastAPI app is created first, then wrapped by the socketio ASGI adapter — this means REST tests use `TestClient(fastapi_app)` (unwrapped), not `TestClient(full_asgi_app)`. Socket.IO event tests are deferred to Phase 3 per the locked decisions.

Dependency injection for the DB connection is the main discretion area. The `Depends(get_db)` FastAPI pattern is idiomatic but requires a generator function; the existing `db_session()` context manager from Phase 1 provides the same semantics and can be adapted. The recommendation is `Depends(get_db_dep)` where `get_db_dep` is a thin generator wrapper around `db_session()` — this gives FastAPI automatic request/response lifecycle management while reusing the existing connection factory.

**Primary recommendation:** Build `backend/main.py` with FastAPI app + socketio AsyncServer, mount via `socketio.ASGIApp`, register all routers under their prefix paths, and run with `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.135.1 (installed) / 0.135.2 (latest) | REST API framework | Already in `.venv`; Pydantic v2 native; async-first |
| uvicorn[standard] | 0.41.0 (installed) | ASGI server | Already in `.venv`; required by FastAPI; production-grade on Pi |
| pydantic | 2.12.5 (installed) | Request/response validation | Already in `.venv`; `from_attributes=True` matches `database/models.py` |
| python-socketio | 5.16.1 (latest) | Socket.IO server + ASGI mount | Chosen by team (Motor Pi `server_bridge.py` already uses socketio client); AsyncServer supports ASGI mount |
| python-dotenv | installed | Environment config | Already used in `database/db.py`; `DATABASE_URL`, `SERVER_URL` env vars |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28.1 (latest) | FastAPI TestClient dependency | Required by FastAPI's `TestClient` (httpx is the underlying transport) |
| pytest | 8.3.4 (installed) | Test runner | Already configured in `pytest.ini` |
| websockets | 16.0 (installed) | Uvicorn WebSocket transport | Installed already as uvicorn[standard] transitive dep |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-socketio | raw WebSockets (Starlette) | Motor Pi already uses socketio client — changing is out of scope |
| FastAPI TestClient | pytest-asyncio + httpx.AsyncClient | TestClient is synchronous; simpler for integration tests; matches D-08 |
| Depends(get_db_dep) | Direct `db_session()` calls in route body | `Depends` is idiomatic FastAPI; ensures cleanup on exception |

**Installation (missing packages only):**
```bash
pip install python-socketio httpx
```

**Version verification (confirmed 2026-03-25):**
- `fastapi` 0.135.1 — installed in `.venv`, 0.135.2 available on PyPI
- `pydantic` 2.12.5 — installed
- `uvicorn` 0.41.0 — installed
- `python-socketio` 5.16.1 — latest on PyPI, NOT yet installed; must add to `requirements.txt`
- `httpx` 0.28.1 — latest on PyPI, NOT yet installed; must add to `requirements.txt`

---

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── __init__.py
├── main.py               # FastAPI app creation, socketio AsyncServer, ASGI mount
├── schemas.py            # Lean Pydantic v2 request/response models per endpoint
├── deps.py               # get_db_dep() generator for Depends()
├── routers/
│   ├── __init__.py
│   ├── jobs.py           # POST /jobs/start, GET /jobs/{session_id}
│   ├── scan.py           # POST /scan/submit, GET /scan/{session_id}
│   ├── solve.py          # POST /solve/submit, GET /solve/{session_id}
│   ├── execute.py        # POST /execute/start, /progress, /complete
│   ├── nodes.py          # POST /nodes/heartbeat, GET /nodes/status
│   └── logs.py           # GET /logs
└── tests/
    ├── __init__.py
    ├── conftest.py        # TestClient + tempfile DB fixture
    └── test_integration.py
```

### Pattern 1: FastAPI + python-socketio ASGI Mount

**What:** Create FastAPI app independently, create socketio AsyncServer independently, compose them with `socketio.ASGIApp` so they share one port. FastAPI handles `/api/*` or plain REST paths; socketio handles `/socket.io/*` automatically.

**When to use:** This is the only pattern for sharing port 8000 between REST and Socket.IO in a single process.

**Example:**
```python
# backend/main.py
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import jobs, scan, solve, execute, nodes, logs

# 1. Create FastAPI app
fastapi_app = FastAPI(title="Rubik's Solver API")
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(jobs.router, prefix="/jobs")
fastapi_app.include_router(scan.router, prefix="/scan")
fastapi_app.include_router(solve.router, prefix="/solve")
fastapi_app.include_router(execute.router, prefix="/execute")
fastapi_app.include_router(nodes.router, prefix="/nodes")
fastapi_app.include_router(logs.router)

# 2. Create socketio AsyncServer
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# 3. Compose — socketio handles /socket.io/*, FastAPI handles the rest
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
```

**Run with:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Source:** python-socketio v5 official docs — ASGI integration section.

### Pattern 2: DB Dependency Injection

**What:** Thin generator wrapper around `db_session()` so FastAPI's `Depends()` handles connection lifecycle (open, commit/rollback, close) per request.

**When to use:** Every route handler that needs a DB connection — which is all of them.

**Example:**
```python
# backend/deps.py
from typing import Generator
import sqlite3
from database.db import db_session

def get_db_dep() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: yields an open DB connection with auto-commit/rollback."""
    with db_session() as conn:
        yield conn
```

```python
# backend/routers/jobs.py
from fastapi import APIRouter, Depends, HTTPException
from database import crud
from backend.deps import get_db_dep
from backend import schemas
import sqlite3

router = APIRouter()

@router.post("/start", response_model=schemas.JobStartResponse, status_code=201)
def start_job(
    body: schemas.JobStartRequest,
    conn: sqlite3.Connection = Depends(get_db_dep),
):
    session_id = crud.create_solve_session(conn, body.to_session_create())
    return schemas.JobStartResponse(session_id=session_id)
```

**Source:** FastAPI official docs — Dependencies section (Depends with yield).

### Pattern 3: Socket.IO Event Handlers

**What:** Register event handlers on `sio` to receive Motor Pi events. The `sio` object is created in `main.py` and imported or accessed by the socket event module.

**When to use:** All Motor Pi inbound events: `register`, `heartbeat`, `state_change`, `execution_complete`.

**Example:**
```python
# backend/main.py (or a ws.py imported by main.py)
@sio.on("heartbeat")
async def on_heartbeat(sid, data):
    """Motor Pi sends: {'node_id': '...', 'status': '...'}"""
    from database.db import db_session
    from database import crud
    from database.models import NodeStatusUpsert
    with db_session() as conn:
        crud.upsert_node_status(conn, NodeStatusUpsert(**data))
    # Broadcast updated node status to frontend
    await sio.emit("job_state_update", {
        "session_id": None,
        "status": "idle",
        "node_status": {},  # populated from DB
    })

@sio.on("execution_complete")
async def on_execution_complete(sid, data):
    """Motor Pi emits 'complete' event (see server_bridge.py line 49)."""
    # Update execution_runs status, emit job_state_update
    ...
```

**Source:** `motorctl/src/server_bridge.py` — event names and payload shapes used by Motor Pi client.

### Pattern 4: Lean Schemas in backend/schemas.py

**What:** Define API-contract-specific Pydantic v2 models separately from database models. Import from `database/models.py` where it helps, but define slimmer request/response shapes per endpoint.

**When to use:** Every endpoint input/output — never return raw `dict` from route handlers.

**Example:**
```python
# backend/schemas.py
from pydantic import BaseModel
from typing import Optional

class JobStartRequest(BaseModel):
    """POST /jobs/start — GUI initiates a new solve session."""
    algorithm: str = "CFOP"
    session_name: Optional[str] = None

class JobStartResponse(BaseModel):
    session_id: int

class JobStateResponse(BaseModel):
    session_id: int
    status: str   # idle|scanning|solving|executing|done|error
    started_at: str

class ScanSubmitRequest(BaseModel):
    session_id: int
    state_string: str  # 54-char cube state
    is_valid: bool
    confidence: Optional[float] = None

class SolveSubmitRequest(BaseModel):
    session_id: int
    algorithm_used: str
    move_count: int
    solution_string: str

class ExecuteStartRequest(BaseModel):
    session_id: int
    solution_id: int
    motor_node_id: Optional[str] = None

class ExecuteProgressRequest(BaseModel):
    session_id: int
    run_id: int
    current_step: int
    total_steps: int
    move: str

class ExecuteCompleteRequest(BaseModel):
    session_id: int
    run_id: int
    status: str  # success|failed

class HeartbeatRequest(BaseModel):
    node_id: str
    node_type: str
    ip_address: Optional[str] = None
    status: str = "online"
    last_message: Optional[str] = None
```

### Anti-Patterns to Avoid

- **Wrapping `socketio.ASGIApp` in TestClient for REST tests:** `TestClient` cannot handle the Socket.IO handshake. Wrap only `fastapi_app` for REST integration tests (per D-08/specifics from CONTEXT.md).
- **Raw SQL in route handlers:** All DB access goes through `database/crud.py` functions. No raw `conn.execute()` in routers.
- **Importing `db_session()` directly in route bodies without `Depends`:** Skips FastAPI's dependency lifecycle; connection may not be closed on exception.
- **Passing Python `datetime` objects to CRUD functions:** Phase 1 established that timestamps are ISO 8601 strings via `_now()`. Do not pass `datetime.now()` — let CRUD functions call `_now()` internally.
- **Modifying `solver/`, `motorctl/`, `EndToEndDemo/`:** Per STATE.md scope rules — these directories are off-limits.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Request validation | Custom validator functions | Pydantic v2 `BaseModel` + FastAPI | FastAPI validates automatically, returns 422 with details |
| CORS headers | Manual `Access-Control-Allow-*` headers | `CORSMiddleware` from fastapi.middleware.cors | Edge cases with preflight OPTIONS requests |
| DB connection lifecycle | try/finally blocks in every route | `Depends(get_db_dep)` generator | FastAPI handles cleanup even on exception |
| Socket.IO handshake & transport | Raw WebSocket protocol | python-socketio `AsyncServer` | Long-polling fallback, reconnection, rooms, namespaces |
| HTTP status code mapping | if/elif chains | FastAPI `HTTPException(status_code=404)` | Automatic JSON error body, OpenAPI docs, logging |
| Test DB isolation | Test-specific DB creation code | `tempfile.NamedTemporaryFile` fixture (Phase 1 pattern) | Already proven; each test gets a fresh DB file |

**Key insight:** FastAPI's automatic validation + python-socketio's ASGI mount together handle the two hardest integration problems. The application code is almost entirely business logic (call CRUD → emit event → return schema).

---

## Common Pitfalls

### Pitfall 1: Testing the socketio.ASGIApp wrapper instead of fastapi_app

**What goes wrong:** `TestClient(app)` where `app` is the `socketio.ASGIApp` wrapper fails or hangs because the Socket.IO handshake interferes with regular HTTP test requests.

**Why it happens:** `socketio.ASGIApp` intercepts requests to inspect if they're Socket.IO handshakes. HTTPX's sync transport inside TestClient doesn't negotiate the Socket.IO protocol correctly.

**How to avoid:** In `conftest.py`, import and wrap `fastapi_app` directly — not `app`. Per CONTEXT.md specifics: `TestClient(fastapi_app)` not `TestClient(app)`.

**Warning signs:** Tests return 400 or hang indefinitely on the first request.

### Pitfall 2: Motor Pi event name mismatch

**What goes wrong:** Server registers handler for `execution_complete` but Motor Pi emits `complete` (see `server_bridge.py` line 49: `await sio.emit('complete', ...)`).

**Why it happens:** CONTEXT.md D-05 says "execution_complete" but the actual code uses `complete`. Research confirms `server_bridge.py` line 49 uses `'complete'`.

**How to avoid:** Register handler on `sio.on("complete")` to match the Motor Pi's actual emit, or verify with the Motor Pi team if the event name should be harmonized. Document the exact event name in the server's socket handler as a comment referencing `server_bridge.py`.

**Warning signs:** Motor Pi successfully connects but `execution_complete` / `complete` event never triggers DB writes.

### Pitfall 3: pytest.ini testpaths excludes backend/tests

**What goes wrong:** Running `pytest` from project root only discovers `database/tests/` (as configured in current `pytest.ini`).

**Why it happens:** `pytest.ini` currently has `testpaths = database/tests`. Phase 2 adds `backend/tests/` which is not in that list.

**How to avoid:** Update `pytest.ini` to include both:
```ini
[pytest]
testpaths = database/tests backend/tests
pythonpath = .
```

**Warning signs:** `pytest` runs 22 tests (Phase 1 only) even after creating `backend/tests/test_integration.py`.

### Pitfall 4: python-socketio and httpx not in requirements.txt

**What goes wrong:** Server import fails on a fresh Pi clone with `ModuleNotFoundError: No module named 'socketio'`. Tests fail with `ModuleNotFoundError: No module named 'httpx'`.

**Why it happens:** Current `requirements.txt` lists `fastapi`, `uvicorn[standard]`, `pydantic`, `python-dotenv`, `pytest` — but not `python-socketio` or `httpx`. Both are needed; neither is installed in `.venv` currently.

**How to avoid:** Add both to `requirements.txt` before implementing. FastAPI's `TestClient` requires `httpx` as an optional dependency — it won't import without it.

**Warning signs:** `from fastapi.testclient import TestClient` raises ImportError about httpx.

### Pitfall 5: ASGI async_mode must match the server

**What goes wrong:** `socketio.AsyncServer(async_mode='threading')` raises errors when mounted as ASGI.

**Why it happens:** ASGI requires the async-capable mode. The synchronous threading mode is for Flask/Django, not FastAPI/Starlette/uvicorn.

**How to avoid:** Always create `socketio.AsyncServer(async_mode="asgi", ...)`. This is the only valid mode for ASGI mounting.

**Warning signs:** Error on startup: `ValueError: async_mode is not compatible with the ASGI server`.

### Pitfall 6: solve_sessions.status values must match schema enum

**What goes wrong:** Inserting status `"idle"` into `solve_sessions.status` when the schema only allows `pending|scanning|solving|executing|completed|failed`.

**Why it happens:** D-04 defines broadcast event `status` values as `idle|scanning|solving|executing|done|error`, but the database schema (ARCHITECTURE.md) uses `pending → scanning → solving → executing → completed/failed`. These are different vocabularies.

**How to avoid:** Keep two distinct status vocabularies: (1) DB status values match `schema.sql` (`pending`, `scanning`, `solving`, `executing`, `completed`, `failed`); (2) broadcast event status uses the D-04 values (`idle`, `scanning`, etc.). The route handler translates between them when emitting Socket.IO events.

**Warning signs:** SQLite CHECK constraint failure on `solve_sessions` insert.

---

## Code Examples

### ASGI Mount (verified pattern)

```python
# backend/main.py
import socketio
from fastapi import FastAPI

fastapi_app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# app is the ASGI entry point for uvicorn
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
```

Source: python-socketio v5 docs — "Using with ASGI" section.

### DB Dependency Generator

```python
# backend/deps.py
import sqlite3
from typing import Generator
from database.db import db_session

def get_db_dep() -> Generator[sqlite3.Connection, None, None]:
    with db_session() as conn:
        yield conn
```

Source: Phase 1 `database/db.py` — `db_session()` context manager; FastAPI docs — Dependencies with yield.

### TestClient Fixture (integration tests)

```python
# backend/tests/conftest.py
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

import database.db as db_module
from database.init_db import create_tables
from backend.main import fastapi_app  # NOT app (the socketio.ASGIApp)

@pytest.fixture
def client():
    """Each test gets a fresh SQLite DB + TestClient wrapping fastapi_app only."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["DATABASE_URL"] = db_path
    db_module.DB_PATH = db_path
    conn = db_module.get_db()
    create_tables(conn)
    conn.close()
    with TestClient(fastapi_app) as c:
        yield c
    os.unlink(db_path)
```

Source: Pattern from `database/tests/conftest.py` (Phase 1); adapted per D-08.

### Happy-Path Integration Test Skeleton

```python
# backend/tests/test_integration.py
def test_full_pipeline_happy_path(client):
    # 1. Start job
    r = client.post("/jobs/start", json={"algorithm": "CFOP"})
    assert r.status_code == 201
    session_id = r.json()["session_id"]

    # 2. Scanner submits cube state
    r = client.post("/scan/submit", json={
        "session_id": session_id,
        "state_string": "U" * 54,
        "is_valid": True,
    })
    assert r.status_code == 200

    # 3. Fetch scan
    r = client.get(f"/scan/{session_id}")
    assert r.status_code == 200

    # 4. Solver submits solution
    r = client.post("/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": 20,
        "solution_string": "R U R' U'",
    })
    assert r.status_code == 200
    solution_id = r.json()["solution_id"]

    # 5. Motor starts execution
    r = client.post("/execute/start", json={
        "session_id": session_id,
        "solution_id": solution_id,
    })
    assert r.status_code == 200

    # 6. Motor reports completion
    run_id = r.json()["run_id"]
    r = client.post("/execute/complete", json={
        "session_id": session_id,
        "run_id": run_id,
        "status": "success",
    })
    assert r.status_code == 200
```

Source: TEST-03 requirement; D-08/D-09 decisions from CONTEXT.md.

### HTTPException Usage (per D-07)

```python
from fastapi import HTTPException

# 404 when session not found
session = crud.get_solve_session_by_id(conn, session_id)
if session is None:
    raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Socket.IO with Flask (sync) | Socket.IO AsyncServer with ASGI (async) | python-socketio v4+ | Async handlers required for uvicorn/FastAPI |
| Pydantic v1 `.from_orm()` | Pydantic v2 `model_config = {"from_attributes": True}` | Pydantic v2 (2023) | Already used in `database/models.py` — consistent |
| `response_model` attribute | Same — still used in FastAPI 0.135 | N/A | No change needed |

**Deprecated/outdated:**
- `socketio.Server(async_mode='eventlet')`: eventlet is legacy; use `async_mode="asgi"` for ASGI servers.
- Pydantic v1 `class Config: orm_mode = True`: replaced by `model_config = {"from_attributes": True}` in v2.

---

## Open Questions

1. **Motor Pi `complete` vs `execution_complete` event name**
   - What we know: `motorctl/src/server_bridge.py` line 49 emits `'complete'`, not `'execution_complete'`
   - What's unclear: CONTEXT.md D-05 lists `execution_complete` as a Motor Pi event. This may be the intended final name that hasn't been updated in `server_bridge.py` yet, or the server must listen for `'complete'`.
   - Recommendation: Register `sio.on("complete")` to match existing Motor Pi code. Add a comment noting the discrepancy. Flag for Motor Pi team (Eric) to confirm if renaming to `execution_complete` is planned.

2. **TestClient + socketio.ASGIApp interaction for Socket.IO tests**
   - What we know: REST tests use `TestClient(fastapi_app)` per D-08. Socket.IO events are excluded from Phase 2 tests per specifics in CONTEXT.md ("Socket.IO events tested separately or deferred to Phase 3").
   - What's unclear: None — this is unambiguously deferred.
   - Recommendation: Do not write Socket.IO event tests in Phase 2. Mark with `# TODO Phase 3` comments.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | All backend code | ✓ | 3.13.x (Linux) | — |
| fastapi | REST framework | ✓ | 0.135.1 (in .venv) | — |
| uvicorn[standard] | ASGI server | ✓ | 0.41.0 (in .venv) | — |
| pydantic v2 | Request validation | ✓ | 2.12.5 (in .venv) | — |
| python-socketio | Socket.IO server | ✗ | not installed | — |
| httpx | TestClient transport | ✗ | not installed | — |
| pytest | Test runner | ✓ | 8.3.4 (in .venv) | — |
| websockets | Uvicorn WS transport | ✓ | 16.0 (transitive) | — |

**Missing dependencies with no fallback:**
- `python-socketio` 5.16.1 — required for D-03 ASGI mount; must `pip install python-socketio` and add to `requirements.txt`
- `httpx` 0.28.1 — required for `TestClient` import; must `pip install httpx` and add to `requirements.txt`

**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | `pytest.ini` (exists; needs `testpaths` updated) |
| Quick run command | `python -m pytest backend/tests/ -x -q` |
| Full suite command | `python -m pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | Server starts and responds to GET / or any endpoint | smoke | `python -m pytest backend/tests/test_integration.py::test_health -x` | ❌ Wave 0 |
| API-02 | All pipeline REST endpoints return 2xx for valid input | integration | `python -m pytest backend/tests/test_integration.py -x` | ❌ Wave 0 |
| API-03 | Socket.IO server accepts connection | manual-only | n/a — deferred to Phase 3 per CONTEXT.md | N/A |
| API-04 | POST /nodes/heartbeat writes to node_status table | integration | `python -m pytest backend/tests/test_nodes.py -x` | ❌ Wave 0 |
| API-05 | 404 returned for unknown session_id; 422 for bad body | integration | `python -m pytest backend/tests/test_integration.py -x -k "error"` | ❌ Wave 0 |
| TEST-03 | Happy-path scan → solve → execute flow passes | integration | `python -m pytest backend/tests/test_integration.py::test_full_pipeline_happy_path -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest backend/tests/ -x -q`
- **Per wave merge:** `python -m pytest -x -q` (full suite including Phase 1 database tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/__init__.py` — package marker
- [ ] `backend/tests/__init__.py` — test package marker
- [ ] `backend/tests/conftest.py` — TestClient + tempfile DB fixture
- [ ] `backend/tests/test_integration.py` — happy-path and error case tests
- [ ] `backend/tests/test_nodes.py` — heartbeat and node status tests
- [ ] `pytest.ini` — add `backend/tests` to `testpaths`
- [ ] `requirements.txt` — add `python-socketio` and `httpx`
- [ ] Framework install: `pip install python-socketio httpx`

---

## Project Constraints (from CLAUDE.md)

CLAUDE.md does not exist in the project root. Constraints come from STATE.md and memory:

- **No git commits by Claude** — Saim manages all git operations.
- **Scope boundary:** Only modify `database/`, `backend/` (new), `.planning/`. Do not touch `solver/`, `motorctl/`, `EndToEndDemo/`, `UnitTests/Scanner/`.
- **Language:** Python 3.13 only; no new languages introduced.
- **Database:** SQLite for development; all CRUD goes through `database/crud.py` functions.
- **Timestamps:** ISO 8601 strings via `_now()` from `database/crud.py` — never pass Python `datetime` objects to CRUD functions.

---

## Sources

### Primary (HIGH confidence)

- **Codebase direct reads** — `database/db.py`, `database/models.py`, `database/crud.py`, `database/tests/conftest.py`, `motorctl/src/server_bridge.py`, `EndToEndDemo/server_db.py` — all read and verified 2026-03-25
- **pip registry** — `pip index versions python-socketio` confirmed 5.16.1 as latest; `pip index versions httpx` confirmed 0.28.1
- **Installed package versions** — verified via `.venv/lib/python*/site-packages/` directory listing: fastapi 0.135.1, pydantic 2.12.5, uvicorn 0.41.0, pytest 8.3.4, websockets 16.0
- **`.planning/` context files** — CONTEXT.md, REQUIREMENTS.md, STATE.md, STACK.md, ARCHITECTURE.md, INTEGRATIONS.md, ROADMAP.md — all read 2026-03-25

### Secondary (MEDIUM confidence)

- **python-socketio ASGI pattern** — `socketio.ASGIApp(sio, other_asgi_app=fastapi_app)` — consistent with python-socketio v5 documented ASGI integration; `async_mode="asgi"` requirement confirmed by library source
- **FastAPI `Depends` with yield** — generator-based dependency for DB connections is standard FastAPI pattern; aligns with Pydantic v2 usage in `database/models.py`

### Tertiary (LOW confidence)

- None — all critical claims backed by direct codebase reads or package registry.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against .venv and pip registry
- Architecture: HIGH — patterns derived from existing codebase (server_bridge.py, db.py, conftest.py) not speculation
- Pitfalls: HIGH (motor event name mismatch) / MEDIUM (others) — event name discrepancy confirmed by direct code read; other pitfalls from FastAPI/socketio known failure modes

**Research date:** 2026-03-25
**Valid until:** 2026-06-25 (stable libraries; python-socketio and FastAPI release frequently but API surface for this use is stable)
