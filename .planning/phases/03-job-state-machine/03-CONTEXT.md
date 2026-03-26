# Phase 3: Job State Machine - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Server-side job state machine that enforces pipeline ordering (Idle → Scanning → Solving → Executing → Done/Error), detects Pi failures via heartbeat monitoring, and exposes control flags for GUI actions (Start, Stop, Reset, Rescan). No hardware required — fully testable in isolation.

**Out of scope for this phase:** GUI pages (Phase 4), 3D cube display (Phase 5), actual scanner/solver/motor execution (those Pis own that logic).

</domain>

<decisions>
## Implementation Decisions

### State Machine Location
- **D-01:** A `JobStateMachine` class lives in `backend/job_state.py`. Holds the transition table and validates every move — raises on illegal transitions (e.g., cannot go Scanning → Executing).
- **D-02:** Class is stateless between requests — all state is read from and written to `solve_sessions.status` in the DB. No in-memory state held on the class instance.
- **D-03:** Routers call the class to validate + execute transitions. The class does not touch HTTP — it only reads/writes DB via the existing `crud.update_solve_session_status()`.
- **D-04:** This design satisfies TEST-02: the class can be unit-tested by passing a mock DB connection, no running server needed.

### Transition Triggers
- **D-05:** Explicit REST calls only. Pi subsystems (Scanner, Solver, Motor) call `POST /jobs/{session_id}/transition` with `{"to": "solving"}` when they're done with their step.
- **D-06:** Server validates the requested transition is legal before updating state. Illegal transition → 400 response with `{"detail": "Invalid transition: scanning → executing"}`.
- **D-07:** GUI-triggered control actions (Start, Stop, Reset, Rescan) go through the same endpoint, not a separate one.

### Heartbeat Monitor
- **D-08:** Implemented as an `asyncio.create_task` background task started in FastAPI's `@app.on_event("startup")` (or `lifespan` context). No external scheduler dependency.
- **D-09:** Checks every 2 seconds. A Pi is considered dead if `last_heartbeat` in `node_status` is older than 5 seconds.
- **D-10:** On dead Pi detection during an active job: transition job to Error state, write a FATAL system log entry, broadcast `job_state_update` via Socket.IO. No execution_run cleanup — keep DB state as-is for debugging. GUI shows the error.
- **D-11:** Monitor only fires Error if there is an active job (status not Idle/Done/Error). Offline Pis when no job is running just get logged, not errored.

### Control Flags Storage
- **D-12:** New `job_control` table in SQLite. Schema: `session_id` (FK to solve_sessions), `action` (VARCHAR: start/stop/reset/rescan), `issued_by` (VARCHAR: gui/system), `issued_at` (TIMESTAMP), `status` (VARCHAR: pending/acknowledged).
- **D-13:** All 4 Pis can observe pending control flags by polling `GET /jobs/{session_id}/control` or being notified via Socket.IO broadcast.
- **D-14:** `POST /jobs/{session_id}/control` endpoint writes the flag. Pis acknowledge via `POST /jobs/{session_id}/control/ack`.
- **D-15:** `init_db.py` gets the new `job_control` table added to `schema.sql`.

### Claude's Discretion
- Exact asyncio task wiring pattern (lifespan vs on_event decorator)
- How to handle the edge case where a Pi reconnects after being declared dead
- Whether to use `apscheduler` if asyncio task proves unreliable in testing
- Pydantic schemas for the new transition and control endpoints

</decisions>

<specifics>
## Specific Ideas

- State machine must be testable without running a server (TEST-02) — the Python class design directly enables this
- Eric's Motor Pi has its own hardware state machine in `motorctl/src/` — Phase 3 is a completely separate server-side job state machine, no overlap
- Heartbeat dead threshold is exactly 5 seconds (from JOB-04 requirement)
- Control flags are DB-persisted so other Pis can observe them without a WebSocket connection

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing backend code (integration points)
- `backend/main.py` — FastAPI app, sio, ASGI composition, router registration pattern
- `backend/sio_instance.py` — shared sio instance (import from here, not main.py)
- `backend/deps.py` — `get_db_dep` dependency injection pattern (use for all new endpoints)
- `backend/routers/jobs.py` — existing job endpoints; new transition/control endpoints go here or in new router
- `backend/socket_handlers.py` — Socket.IO broadcast patterns (`job_state_update` payload shape)

### Database layer (integration points)
- `database/crud.py` — `update_solve_session_status()` at line 74 (state machine will call this)
- `database/schema.sql` — add `job_control` table here
- `database/init_db.py` — table creation script (must include new table)
- `database/models.py` — Pydantic models for new table rows

### Requirements
- `.planning/REQUIREMENTS.md` §JOB-01 through JOB-05, TEST-02 — all requirements this phase must satisfy

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `crud.update_solve_session_status(conn, session_id, status)` — already exists, state machine calls this directly
- `crud.get_solve_session_by_id(conn, session_id)` — use to fetch current state before validating transition
- `sio.emit("job_state_update", {...})` — broadcast pattern already established in socket_handlers.py
- `SystemLogCreate` + `crud.create_log()` — use for heartbeat failure log entries

### Established Patterns
- All routers use `Depends(get_db_dep)` for DB injection — new endpoints must follow this
- Import `sio` from `backend.sio_instance` (not `backend.main`) to avoid circular imports
- `async def` handlers required for any route that calls `await sio.emit()`
- `HTTPException(status_code=400, detail="...")` pattern for validation errors

### Integration Points
- `backend/routers/jobs.py` — most natural home for `POST /jobs/{id}/transition` and `POST /jobs/{id}/control`
- `backend/main.py` startup event — where the heartbeat monitor asyncio task gets registered
- `database/schema.sql` + `database/init_db.py` — where `job_control` table is added

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope. GUI pages that *display* job state are Phase 4.

</deferred>

---

*Phase: 03-job-state-machine*
*Context gathered: 2026-03-26*
