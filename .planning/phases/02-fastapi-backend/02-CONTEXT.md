# Phase 2: FastAPI Backend - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the REST + WebSocket API server that runs on the Database & GUI Pi (Rpi4). This server is the integration bridge — all other Pis (Scanner, Solver, Motor) read/write pipeline state through it via REST, and the web frontend gets real-time updates via Socket.IO. Phase 2 does NOT implement the job state machine enforcement, heartbeat monitoring background task, or any frontend pages — those are Phase 3 and Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Project Layout

- **D-01:** Server lives in a `backend/` package at the project root. Structure: `backend/__init__.py`, `backend/main.py` (FastAPI app + socketio app creation), `backend/schemas.py` (API-specific request/response models), `backend/routers/` with `pipeline.py`, `nodes.py`, `status.py`, `ws.py` (or socket event handlers).
- **D-02:** API-specific request/response models live in `backend/schemas.py` — separate from `database/models.py`. `schemas.py` may import from `database/models.py` where convenient but defines its own lean Pydantic v2 models for each endpoint's input/output contract.

### WebSocket / Socket.IO

- **D-03:** Single `python-socketio` AsyncServer mounted on FastAPI via ASGI. `app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)`. Socket.IO handles `/socket.io/*`, FastAPI handles REST routes. One server, one protocol — both Pi nodes and the Phase 4 frontend use Socket.IO clients.
- **D-04:** Server emits two broadcast events to frontend clients:
  - `job_state_update` — emitted on any pipeline stage change; payload includes `session_id`, `status` (idle|scanning|solving|executing|done|error), and `node_status` dict (node name → online bool)
  - `execution_progress` — emitted per motor step; payload includes `session_id`, `current_step`, `total_steps`, `move`, `pct_complete`
- **D-05:** Motor Pi inbound events the server must handle: `heartbeat`, `state_change`, `execution_complete` (and `register`, `load_moves`, `start_solve` for node coordination). Exact event names match `motorctl/src/server_bridge.py` and `EndToEndDemo/` socket events.

### REST Endpoint Structure

- **D-06:** Pipeline-stage-based routing (not resource-based). Routes map to the solve pipeline stages so each Pi knows exactly where to call:
  ```
  POST   /jobs/start              # GUI: start new solve session
  GET    /jobs/{session_id}       # all Pis: get current job state

  POST   /scan/submit             # Scanner Pi: submit cube state + scan faces
  GET    /scan/{session_id}       # fetch scan result

  POST   /solve/submit            # Solver Pi: submit solution + steps
  GET    /solve/{session_id}      # fetch solution

  POST   /execute/start           # Motor Pi: fetch move list to execute
  POST   /execute/progress        # Motor Pi: report per-step progress
  POST   /execute/complete        # Motor Pi: report execution run done

  POST   /nodes/heartbeat         # all Pis: write heartbeat to node_status
  GET    /nodes/status            # GUI: get all node health

  GET    /logs                    # GUI: fetch system_logs entries
  ```
- **D-07:** Error responses use FastAPI defaults — no custom envelope. Success responses return raw Pydantic models. Errors use `HTTPException` with `detail` string. Validation errors use FastAPI's automatic 422 responses.

### Testing

- **D-08:** Integration tests use FastAPI's built-in `TestClient` (synchronous httpx wrapper). Tests hit real route handlers. No DB mocking — use the same `tempfile` + `create_tables` fixture pattern from Phase 1 (`database/tests/conftest.py`), adapted for `backend/tests/conftest.py`.
- **D-09:** Test files live in `backend/tests/` co-located with the module — consistent with the `database/tests/` pattern from Phase 1. Files: `conftest.py` (TestClient + DB fixture), `test_integration.py` (happy-path scan → solve → execute flow), plus per-router tests as needed.

### Claude's Discretion

- CORS configuration — allow all origins (`*`) for LAN dev; Claude can harden if needed.
- Dependency injection pattern for DB connection — how the route handlers get a DB connection (e.g., `Depends(get_db)` or direct import of `db_session()`).
- Whether to include a `GET /` health check root endpoint.
- Socket.IO namespace design — default namespace (`/`) is fine unless Claude sees a reason to use named namespaces.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Database Layer
- `database/crud.py` — All CRUD functions Phase 2 routes will call; patterns must be consistent
- `database/db.py` — `get_db()` and `db_session()` — connection factory for route handlers
- `database/models.py` — Pydantic v2 models; `backend/schemas.py` should align with these
- `database/schema.sql` — Source of truth for all 11 table definitions

### Documentation
- `docs/server/DATABASE.md` — Section 9 (end-to-end flow) and Section 12 (test fixture pattern)

### Motor Pi Integration
- `motorctl/src/server_bridge.py` — Socket.IO event names and payload formats the Motor Pi sends/expects
- `EndToEndDemo/server_db.py` — Prototype server (TCP, not FastAPI) showing the message routing logic to replicate

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 2 requirement IDs: API-01, API-02, API-03, API-04, API-05, TEST-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `database/crud.py` — All 11 tables have CRUD functions ready to call from route handlers; no raw SQL needed in routes
- `database/db.py:db_session()` — Context manager for transaction scope; use in route handlers via dependency injection
- `database/models.py` — Pydantic v2 models with `from_attributes = True`; importable into `backend/schemas.py`
- `database/tests/conftest.py` — Test fixture pattern (`tempfile` + `create_tables`); replicate for `backend/tests/conftest.py`

### Established Patterns
- CRUD functions take `conn: sqlite3.Connection` as first arg — route handlers must pass a connection
- Timestamps stored as ISO 8601 strings via `_now()` — do not pass Python datetime objects to CRUD functions
- Pydantic v2 `from_attributes = True` on all models — consistent with FastAPI response_model usage

### Integration Points
- `solve_sessions.id` is the session key threaded through all pipeline stages (scan → solve → execute)
- `node_status` table is written by `/nodes/heartbeat` and read by `/nodes/status`; Phase 3 heartbeat monitor will query it too
- `execution_runs` and `motor_execution_log` tables are written by `/execute/*` endpoints
- Socket.IO events from Motor Pi arrive at server event handlers and trigger DB writes + `job_state_update` broadcast to frontend

</code_context>

<specifics>
## Specific Ideas

- `app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)` is the exact mount pattern; run with `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- `TestClient(fastapi_app)` wraps only the FastAPI app (not the socketio.ASGIApp wrapper) for REST tests — Socket.IO events tested separately or deferred to Phase 3
- Motor Pi's `server_bridge.py` already connects to `SERVER_URL` env var via SocketIO async client — server must listen on same port (8000) and default namespace

</specifics>

<deferred>
## Deferred Ideas

- Authentication / API keys on endpoints — Phase 2 is LAN-only with no auth; role-based access enforcement is future scope (noted in Phase 1 deferred)
- PostgreSQL migration — db.py documents the swap; not a Phase 2 deliverable
- Socket.IO namespaces — if Motor Pi and frontend need isolation, add namespaces in Phase 3+
- `/execute/verify` endpoint for post-solve re-scan — Scanner Pi submits verification result; relevant to Phase 3 pipeline ordering
- Rate limiting / throttling — out of scope for course deliverable

</deferred>

---

*Phase: 02-fastapi-backend*
*Context gathered: 2026-03-25*
