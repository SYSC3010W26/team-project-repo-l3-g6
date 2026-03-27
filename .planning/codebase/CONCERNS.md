# CONCERNS.md — Pi³ Rubik's Cube Solver

> Generated: 2026-03-27 | Focus: Technical debt, security, performance, fragile areas

---

## 1. Security

### 1.1 Wildcard CORS (HIGH)
**File:** `backend/main.py` — line 35
```python
allow_origins=["*"]
```
The FastAPI app allows requests from any origin. This is acceptable in a closed local-network lab environment (Raspberry Pi LAN), but must be locked down to specific origins before any internet-facing deployment.

**Risk:** Any web page on the local network can make authenticated API calls on behalf of the user.

**Fix:** Set `allow_origins` to `["http://localhost:5173", "http://<pi4-ip>:5173"]` for dev; restrict further for production.

---

### 1.2 No Authentication on Any Endpoint (HIGH)
**Files:** `backend/routers/*.py`
All HTTP and Socket.IO endpoints are fully public — no API key, JWT, or session token required. Any device on the same network can start/abort/manipulate solve sessions.

**Risk:** Unintended or malicious control of the physical robot arm.

**Fix:** Add a shared API key header check (e.g., `X-API-Key`) for all Pi-to-server endpoints; restrict web dashboard endpoints similarly.

---

### 1.3 `.env` Committed to Repo (MEDIUM)
**File:** `.env`
The `.env` file is present in the working tree (confirmed readable). While `.gitignore` excludes it, if it was ever committed, credentials could be in history.

```
DATABASE_URL=/home/anakafeel/.../rubiks_dev.db
```
The absolute path exposes developer machine layout. The Supabase comment also includes a placeholder password.

**Fix:** Verify `.env` is not in git history (`git log --all -- .env`). Use a `.env.example` file with placeholder values for team onboarding.

---

### 1.4 No Input Validation on Socket.IO Events (MEDIUM)
**File:** `backend/socket_handlers.py`
All `data.get(...)` calls fall back to `"unknown"` with no schema validation:
```python
node_id = data.get("node_id", "unknown")
state = data.get("state", "unknown")
```
A malformed or malicious event could write `"unknown"` to the database or trigger unintended state transitions.

**Fix:** Add Pydantic models for inbound Socket.IO payloads, or at minimum add explicit `isinstance` + field checks before processing.

---

### 1.5 No HTTPS/WSS (LOW — lab context)
All traffic between Pi nodes and the server is plain HTTP and WS. In a university lab LAN this is acceptable, but warrants a note for the design document.

---

## 2. Technical Debt

### 2.1 Duplicate `actuator.py` / `server_bridge.py` Files (HIGH)
**Files:** `motorctl/src/actuator.py` and `motorctl/src/server_bridge.py`

Both files are nearly identical — they define the same `MotorState` enum, `StateManager` class, and Socket.IO event handlers (`load_moves`, `start_solve`). The `actuator.py` even imports from itself:
```python
# motorctl/src/actuator.py line 10
from actuator import execute_move_sequence  # circular / wrong module
```
This will cause an `ImportError` at runtime on the Pi. It appears `actuator.py` is a leftover copy of `server_bridge.py` before they diverged.

**Fix:** Delete `actuator.py` or refactor it into two clean modules — one for the socket bridge, one for the physical motor control logic — and fix the circular import.

---

### 2.2 Raw SQL Inline in `heartbeat.py` (MEDIUM)
**File:** `backend/heartbeat.py` — lines 67–70
```python
active_jobs = conn.execute(
    "SELECT id FROM solve_sessions "
    "WHERE status IN ('scanning', 'solving', 'executing')"
).fetchall()
```
This raw SQL query duplicates the session-fetch logic that lives in `database/crud.py`. If the status enum or table name changes, this query will silently break while the CRUD layer is updated separately.

**Fix:** Extract a `crud.get_active_sessions(conn)` function and call it from both `heartbeat.py` and any other caller.

---

### 2.3 Deprecated `on_event` Startup Hook (MEDIUM)
**File:** `backend/main.py` — line 44
```python
@fastapi_app.on_event("startup")
async def startup_event():
```
`on_event` is deprecated in FastAPI ≥ 0.100. The recommended pattern is `lifespan` context managers (FastAPI 0.93+).

**Fix:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(heartbeat_monitor())
    yield

fastapi_app = FastAPI(lifespan=lifespan, ...)
```

---

### 2.4 `execute.py` Bypasses the Job State Machine (MEDIUM)
**File:** `backend/routers/execute.py` — lines 39, 72–73
```python
crud.update_solve_session_status(conn, body.session_id, "executing")   # line 39
crud.update_solve_session_status(conn, body.session_id, session_status) # line 73
```
These routers update `solve_sessions.status` directly via CRUD instead of going through `JobStateMachine.transition()`. This means the state guard checks (`_require_valid_cube_state`, `_require_solution`) and the invalid-transition error can be bypassed.

**Fix:** Replace direct `crud.update_solve_session_status` calls in `execute.py` with `JobStateMachine().transition(conn, session_id, ...)`.

---

### 2.5 `completed` / `failed` Status Mismatch with State Machine (MEDIUM)
**File:** `backend/routers/execute.py` — line 69
```python
db_status = "completed" if body.status == "success" else "failed"
```
The state machine in `job_state.py` defines `"done"` and `"error"` (not `"completed"` or `"failed"`), but `execute.py` writes `"completed"` / `"failed"` into the DB. These are inconsistent terminal states.

`TERMINAL_STATES` in `job_state.py` includes both sets as a workaround:
```python
TERMINAL_STATES = {"done", "error", "completed", "cancelled", "failed"}
```
This dual vocabulary is a source of bugs — queries filtering by status must cover multiple synonyms.

**Fix:** Standardize on `"done"` and `"error"` throughout the system.

---

### 2.6 Supabase Migration Not Implemented (LOW)
**File:** `database/db.py` — lines 54–83
Production PostgreSQL/Supabase support is commented out as a manual swap. The `.env` comment also says `"need to set this up later"`. There is no migration tooling (Alembic, etc.).

**Risk:** The SQLite schema and PostgreSQL schema may diverge silently. Schema changes in `schema.sql` are not tracked with migrations.

**Fix:** Add Alembic, or at minimum document the migration procedure with a checklist in the README.

---

### 2.7 `motorctl` has No Node-Level `.env` Documentation (LOW)
**File:** `motorctl/src/server_bridge.py` — lines 19, 55
```python
NODE_ID = os.getenv("NODE_ID")         # None if unset
await sio.connect(os.getenv("SERVER_URL"))  # TypeError if unset
```
If `NODE_ID` or `SERVER_URL` env vars are missing, the motor Pi will silently use `None` as its node ID (corrupting logs) or crash with a `TypeError` on connect.

**Fix:** Add startup assertions:
```python
NODE_ID = os.environ["NODE_ID"]    # raises KeyError immediately if missing
SERVER_URL = os.environ["SERVER_URL"]
```
And provide a `motorctl/.env.example`.

---

## 3. Performance

### 3.1 Heartbeat Monitor Opens a DB Connection Every 2 Seconds (MEDIUM)
**File:** `backend/heartbeat.py` — lines 40–83
Each heartbeat cycle opens and closes a `db_session()` context (SQLite connection). Under load with many nodes, this could create contention on the SQLite file lock.

**Risk:** SQLite's default `check_same_thread=False` masks threading errors. Under async load (uvicorn + asyncio), multiple coroutines could hold the write lock simultaneously.

**Fix:** Consider a connection pool (e.g., `aiosqlite` for async-native SQLite access), or migrate to PostgreSQL earlier than planned.

---

### 3.2 Solver is Synchronous / Blocking (MEDIUM)
**File:** `backend/routers/solve.py` (calls into `solver/Solver.py`)
The CFOP solve algorithm is CPU-bound and synchronous. Calling it from an async FastAPI route will block the entire event loop for the duration of solving (typically < 1s for CFOP, but can spike).

**Fix:** Wrap in `asyncio.to_thread()`:
```python
solution = await asyncio.to_thread(solver.solve)
```

---

### 3.3 No Pagination on Log / Session Endpoints (LOW)
**Files:** `backend/routers/logs.py`, `backend/routers/jobs.py`
Log queries return all rows without pagination. The `system_logs` table is append-only; after extended operation it will grow large and slow full-table scans.

**Fix:** Add `limit` / `offset` query parameters (or cursor-based pagination) to log and session list endpoints.

---

## 4. Fragile Areas

### 4.1 Solver Does Not Validate Physical Cube Parity (HIGH)
**File:** `solver/Solver.py` — `load_state()` and `solve()`
`load_state()` validates the string format (length, characters, face counts) but does NOT validate physical cube parity. A state string can pass all format checks yet be physically impossible (e.g., a single edge flip), causing `solve()` to raise `CubeNotSolvableError` only at the end of a full solve — wasting time.

**Fix:** Add a parity check after `set_cube_state()` to detect impossible states early.

---

### 4.2 Socket.IO `complete` Event Has No `session_id` (HIGH)
**File:** `backend/socket_handlers.py` — `on_complete()` line 96–100
```python
await sio.emit("job_state_update", {"session_id": None, "status": broadcast_status, ...})
```
The `complete` event from the motor Pi does not carry `session_id`. The server broadcasts `session_id: None` to the frontend, which cannot determine which session finished. The frontend must infer the active session from its own state.

**Risk:** Race condition if two jobs complete near-simultaneously, or if the frontend's local session state is stale.

**Fix:** The motor Pi should include `session_id` in the `complete` payload; the server should validate and re-broadcast it.

---

### 4.3 Two Databases in the Repo (MEDIUM)
Two SQLite DB files exist at the project root:
- `rubiks.db` (0 bytes, placeholder)
- `rubiks_dev.db` (471 KB, real data)

Plus `database/rubiks_solver.db` (0 bytes).

Both `.gitignore` excludes `*.db`, but the zero-byte placeholder files appear to be manually tracked. This causes confusion about which DB file is authoritative.

**Fix:** Delete placeholder `.db` files; document in README that `rubiks_dev.db` is created by `setup_dev.sh` and is gitignored.

---

### 4.4 `UnitTests/Scanner/` is Empty (MEDIUM)
**Directory:** `UnitTests/Scanner/`
The top-level `UnitTests/` directory exists for the image scanner subsystem but contains no test files. The camera/CV scanning pipeline has no automated test coverage.

**Risk:** Scanner regressions (e.g., face detection, colour mapping) will only be caught manually.

**Fix:** Add unit tests for the scanner subsystem, at minimum for colour-to-face-letter mapping logic.

---

### 4.5 No Error Recovery Path for Motor Pi Reconnect (MEDIUM)
**File:** `motorctl/src/server_bridge.py`
There is no reconnection logic after `sio.connect()`. If the network drops temporarily, the motor Pi Socket.IO client will not attempt to reconnect — it will remain disconnected and silently miss all events.

**Fix:** Pass `reconnection=True, reconnection_attempts=inf` to `socketio.AsyncClient()`, or add an explicit retry loop around `connect_to_server()`.

---

### 4.6 Frontend `dist/` in Repo (LOW)
**Directory:** `frontend/dist/`
The compiled production build is committed to the repo. Build artifacts should be gitignored and generated at deploy time.

**Fix:** Add `frontend/dist/` to `.gitignore`.

---

## 5. Missing Coverage Summary

| Area | Gap |
|--|--|
| Scanner | No tests at all (`UnitTests/Scanner/` empty) |
| Frontend | No unit or integration tests found |
| `execute.py` | Bypasses state machine — not covered by state machine tests |
| Socket.IO handlers | No integration tests for inbound events |
| `motorctl` reconnect | No tests for disconnect/reconnect behaviour |
| Solver parity | No test for physically impossible cube states |

---

## 6. Risk Matrix

| # | Concern | Severity | Effort to Fix |
|---|---|---|---|
| 1.1 | Wildcard CORS | High | Low |
| 1.2 | No authentication | High | Medium |
| 2.1 | Duplicate `actuator.py` with circular import | High | Low |
| 4.2 | `complete` event missing `session_id` | High | Low |
| 4.1 | Solver parity not validated | High | Medium |
| 2.4 | `execute.py` bypasses state machine | Medium | Low |
| 2.5 | `done`/`completed` status mismatch | Medium | Low |
| 3.2 | Blocking solver in async route | Medium | Low |
| 4.5 | No motor Pi reconnect logic | Medium | Low |
| 2.3 | Deprecated `on_event` hook | Low | Low |
| 3.3 | No pagination on logs | Low | Medium |
| 4.6 | `frontend/dist/` in repo | Low | Low |
