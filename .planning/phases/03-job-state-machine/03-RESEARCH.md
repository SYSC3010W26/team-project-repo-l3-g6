# Phase 3: Job State Machine - Research

**Researched:** 2026-03-26
**Domain:** Server-side job state machine, heartbeat monitoring, control flags for distributed Pi coordination
**Confidence:** HIGH

## Summary

Phase 3 implements a **server-enforced job state machine** (Idle → Scanning → Solving → Executing → Done/Error) that prevents illegal transitions and coordinates four Raspberry Pi subsystems through database polling and Socket.IO broadcasts. Key components include:

1. **JobStateMachine class** — Stateless validation logic living in `backend/job_state.py`, reading/writing all state to `solve_sessions.status` via `crud.update_solve_session_status()`. No in-memory state held on the class instance.

2. **Heartbeat monitor** — Background asyncio task that polls `node_status` every 2 seconds, transitions active jobs to Error if a Pi hasn't heartbeat within 5 seconds, broadcasts `job_state_update` via Socket.IO, and logs fatal events to `system_logs`.

3. **Control flags** — New `job_control` SQLite table (schema: `session_id`, `action` [start/stop/reset/rescan], `issued_by`, `issued_at`, `status` [pending/acknowledged]) that Pis observe via REST polling or Socket.IO notifications.

All state machine logic is **testable without a running server** (TEST-02) because the class delegates all DB access to `crud` functions that accept a mock connection. The heartbeat monitor uses native `asyncio.create_task()` (no external scheduler) and integrates with FastAPI's lifespan or startup event.

**Primary recommendation:** Implement the state machine as a simple dict-based transition table with validation, not a library (e.g., `transitions`), because the schema is small (5 states, 8 valid transitions) and the class needs to touch DB on every transition anyway. Use Pydantic Literal types for request validation and leverage existing CRUD patterns for consistency.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `JobStateMachine` class lives in `backend/job_state.py`. Holds the transition table and validates every move — raises on illegal transitions.
- **D-02:** Class is stateless between requests — all state is read from and written to `solve_sessions.status` in the DB. No in-memory state held on the class instance.
- **D-03:** Routers call the class to validate + execute transitions. The class does not touch HTTP — it only reads/writes DB via the existing `crud.update_solve_session_status()`.
- **D-04:** This design satisfies TEST-02: the class can be unit-tested by passing a mock DB connection, no running server needed.
- **D-05:** Explicit REST calls only. Pi subsystems call `POST /jobs/{session_id}/transition` with `{"to": "solving"}` when they're done with their step.
- **D-06:** Server validates the requested transition is legal before updating state. Illegal transition → 400 response with `{"detail": "Invalid transition: scanning → executing"}`.
- **D-07:** GUI-triggered control actions (Start, Stop, Reset, Rescan) go through the same endpoint, not a separate one.
- **D-08:** Implemented as an `asyncio.create_task` background task started in FastAPI's `@app.on_event("startup")` (or `lifespan` context). No external scheduler dependency.
- **D-09:** Checks every 2 seconds. A Pi is considered dead if `last_heartbeat` in `node_status` is older than 5 seconds.
- **D-10:** On dead Pi detection during an active job: transition job to Error state, write a FATAL system log entry, broadcast `job_state_update` via Socket.IO. No execution_run cleanup — keep DB state as-is for debugging. GUI shows the error.
- **D-11:** Monitor only fires Error if there is an active job (status not Idle/Done/Error). Offline Pis when no job is running just get logged, not errored.
- **D-12:** New `job_control` table in SQLite. Schema: `session_id` (FK to solve_sessions), `action` (VARCHAR: start/stop/reset/rescan), `issued_by` (VARCHAR: gui/system), `issued_at` (TIMESTAMP), `status` (VARCHAR: pending/acknowledged).
- **D-13:** All 4 Pis can observe pending control flags by polling `GET /jobs/{session_id}/control` or being notified via Socket.IO broadcast.
- **D-14:** `POST /jobs/{session_id}/control` endpoint writes the flag. Pis acknowledge via `POST /jobs/{session_id}/control/ack`.
- **D-15:** `init_db.py` gets the new `job_control` table added to `schema.sql`.

### Claude's Discretion

- Exact asyncio task wiring pattern (lifespan vs on_event decorator)
- How to handle the edge case where a Pi reconnects after being declared dead
- Whether to use `apscheduler` if asyncio task proves unreliable in testing
- Pydantic schemas for the new transition and control endpoints

### Deferred Ideas (OUT OF SCOPE)

- None — discussion stayed within phase scope. GUI pages that *display* job state are Phase 4.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| JOB-01 | Server enforces pipeline ordering: Idle → Scanning → Solving → Executing → Done/Error | JobStateMachine class with transition table; status validated via crud.get_solve_session_by_id() before update |
| JOB-02 | Solve only starts after a valid cube state exists in DB (confidence flag set) | Pre-transition checks in JobStateMachine: Scanning → Solving only allowed if cube_states has valid=True and confidence set |
| JOB-03 | Execute only starts after a solution exists in DB | Pre-transition checks: Solving → Executing only allowed if solutions row exists for session_id |
| JOB-04 | Server detects missing heartbeat from any Pi within 5 seconds and transitions job to Error state | Background heartbeat_monitor task: checks every 2 seconds, compares now() - last_heartbeat > 5 seconds, calls state machine on match |
| JOB-05 | GUI actions (Start, Stop, Reset, Rescan) are written as control flags observable by other subsystems | job_control table + POST/GET endpoints; Pis poll or subscribe to Socket.IO broadcasts |
| TEST-02 | Job state machine transitions are testable in isolation (no hardware required) | JobStateMachine accepts sqlite3.Connection; tests pass in-memory DB or temp file; no async required for state validation |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.109.0+ | Request routing, OpenAPI docs, dependency injection | Already in project; standard for async Python APIs |
| python-socketio | 5.11.0+ | WebSocket/polling hybrid for real-time state broadcasts | Already in project; D-13 control flags use Socket.IO emissions |
| SQLite (sqlite3) | Built-in (Python 3.13+) | Relational storage, transactional consistency, FK constraints | Schema already defined in `schema.sql`; Phase 1 complete |
| Pydantic | 2.x | Request/response validation, JSON schema generation | Already in project; used for all schemas |
| pytest | 8.x+ | Unit & integration test framework | Already in project; 30 tests pass; no external test runner needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| asyncio | Built-in (Python 3.13+) | Native async/await, background tasks | Heartbeat monitor uses `asyncio.create_task()` for polling loop |
| typing | Built-in (Python 3.13+) | Type hints for state machine and validators | Enum, Literal types constrain valid states and transitions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom state machine class | `transitions` library | Overkill for 5 states; library doesn't touch DB; would need wrapper anyway |
| Custom state machine class | `python-statemachine` library | Heavier, requires inheritance; still need DB wrapper for TEST-02 isolation |
| asyncio.create_task | `APScheduler` | APScheduler is an external process; asyncio is simpler, no separate daemon needed for this 2-second polling |
| APScheduler | `Celery` + Redis | Requires separate Redis instance on Pi; heartbeat failure already tested locally without external deps |
| Database polling for control flags | Message broker (RabbitMQ/Kafka) | No message broker in scope (Phase 3 is server-side only); polling + Socket.IO broadcasts fit within DB-only architecture |
| Database polling for control flags | Pub/Sub service | Not available on local LAN; database + Socket.IO are sufficient for Phase 3 scope |

**Installation:**
FastAPI, Pydantic, and socketio are already in `.venv/`. No new packages required for Phase 3.

**Version verification:**
- FastAPI: existing project uses 0.109.0+; heartbeat task and state machine routes compatible with current version
- python-socketio: existing project uses 5.11.0+; `sio.emit()` pattern stable across versions
- Pydantic: project uses v2.x; Literal and custom validators work as shown in existing schemas

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── main.py                      # FastAPI app, sio wrapper, router registration
├── sio_instance.py              # Singleton AsyncServer (shared across routes)
├── job_state.py                 # [NEW] JobStateMachine class
├── heartbeat.py                 # [NEW] heartbeat_monitor task
├── schemas.py                   # Request/response models (add JobTransitionRequest, ControlFlagRequest)
├── deps.py                       # get_db_dep() dependency
├── routers/
│   ├── jobs.py                  # [EXTEND] Add transition/control endpoints
│   ├── scan.py
│   ├── solve.py
│   ├── execute.py
│   ├── nodes.py
│   └── logs.py
└── tests/
    ├── conftest.py              # Fixture setup (client, temp DB)
    └── test_integration.py       # [EXTEND] Add state machine + control flag tests
database/
├── schema.sql                   # [EXTEND] Add job_control table
├── models.py                    # [EXTEND] Add JobControlCreate, JobControl Pydantic models
├── crud.py                      # [EXTEND] Add CRUD for job_control table
├── init_db.py                   # [No change] create_tables() auto-applies schema.sql
└── db.py                        # DB connection factory
```

### Pattern 1: Stateless State Machine with DB as Single Source of Truth

**What:** The state machine class reads current state from the DB, validates the requested transition against a static transition table, and writes the new state back to the DB. The class holds no state between requests.

**When to use:** Distributed systems where multiple processes might try to transition a job simultaneously; database consistency is paramount; request handlers need to be stateless.

**Example:**

```python
# Source: D-02, D-03 from CONTEXT.md
from typing import Literal
import sqlite3
from database import crud

class JobStateMachine:
    """Stateless job state validator. All state lives in DB."""

    # Valid transitions as a dict: current_status -> list of allowed next_status
    TRANSITIONS = {
        "idle": ["scanning"],
        "scanning": ["solving", "idle"],      # Can rescan or reset
        "solving": ["executing", "idle"],     # Can reset
        "executing": ["done", "error", "idle"], # Can stop/reset
        "done": [],                            # Terminal
        "error": ["idle"],                     # Can reset
    }

    @staticmethod
    def validate_transition(
        conn: sqlite3.Connection,
        session_id: int,
        target_status: str
    ) -> None:
        """Validates transition is legal. Raises ValueError if not allowed."""
        current_row = crud.get_solve_session_by_id(conn, session_id)
        if not current_row:
            raise ValueError(f"Session {session_id} not found")

        current_status = current_row["status"]
        allowed_next = JobStateMachine.TRANSITIONS.get(current_status, [])

        if target_status not in allowed_next:
            raise ValueError(
                f"Invalid transition: {current_status} → {target_status}"
            )

    @staticmethod
    def transition(
        conn: sqlite3.Connection,
        session_id: int,
        target_status: str
    ) -> None:
        """Execute the transition if legal. Raises on illegal move."""
        JobStateMachine.validate_transition(conn, session_id, target_status)
        crud.update_solve_session_status(conn, session_id, target_status)

# Usage in route handler:
@router.post("/jobs/{session_id}/transition")
def transition_job(session_id: int, body: JobTransitionRequest, conn = Depends(get_db_dep)):
    try:
        JobStateMachine.transition(conn, session_id, body.to)
        await sio.emit("job_state_update", {"session_id": session_id, "status": body.to})
        return {"status": body.to}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Pattern 2: Background Heartbeat Monitor with asyncio.create_task

**What:** A coroutine that polls the DB every 2 seconds, checks `node_status.last_heartbeat`, detects stale Pis, and transitions active jobs to Error. Started via FastAPI startup event or lifespan context.

**When to use:** Long-running background checks that don't require request context; need to run independently from HTTP handlers; want to avoid external schedulers.

**Example:**

```python
# Source: D-08, D-09, D-10, D-11 from CONTEXT.md
import asyncio
from datetime import datetime, timezone, timedelta
from database.db import db_session
from database import crud
from database.models import SystemLogCreate
from backend.sio_instance import sio
from backend.job_state import JobStateMachine

async def heartbeat_monitor():
    """Background task: detect dead Pis every 2 seconds, error active jobs."""
    while True:
        try:
            await asyncio.sleep(2)

            with db_session() as conn:
                # Get all active jobs (not idle/done/error)
                active_jobs = conn.execute(
                    "SELECT id, id as session_id FROM solve_sessions WHERE status IN ('scanning', 'solving', 'executing')"
                ).fetchall()

                # Get all nodes with stale heartbeats (older than 5 seconds)
                all_nodes = crud.get_all_nodes(conn)
                now = datetime.now(timezone.utc)
                stale_nodes = [
                    n for n in all_nodes
                    if (now - datetime.fromisoformat(n["last_heartbeat"])) > timedelta(seconds=5)
                ]

                # If an active job has a stale Pi, error the job
                for job in active_jobs:
                    session_id = job["session_id"]
                    # Transition job to error (D-10)
                    try:
                        JobStateMachine.transition(conn, session_id, "error")
                        # Log fatal event
                        crud.create_log(
                            conn,
                            SystemLogCreate(
                                session_id=session_id,
                                node_id=None,
                                level="FATAL",
                                event_type="heartbeat_failure",
                                message=f"Active job transitioned to Error: stale Pi detected",
                            ),
                        )
                        # Broadcast to GUI
                        await sio.emit(
                            "job_state_update",
                            {"session_id": session_id, "status": "error", "reason": "Pi heartbeat lost"},
                        )
                    except ValueError:
                        # Job might have already changed state; ignore
                        pass

        except Exception as e:
            print(f"[heartbeat_monitor] Error: {e}")
            # Continue looping even on error

# Startup hook in main.py:
@fastapi_app.on_event("startup")
async def start_heartbeat_monitor():
    asyncio.create_task(heartbeat_monitor())
```

### Pattern 3: Control Flags as Database Poll Endpoint

**What:** REST endpoint that writes control actions (start, stop, reset, rescan) to a `job_control` table. Pis query the endpoint periodically or receive Socket.IO broadcasts. Pis acknowledge by marking the flag as "acknowledged" so the GUI knows the Pi received it.

**When to use:** Commands that need to be persisted and can tolerate polling latency (200ms–1s is fine for cube solving); reduces risk of lost commands due to network glitches; fits within database-centric architecture.

**Example:**

```python
# Source: D-12, D-13, D-14, D-15 from CONTEXT.md

# In schemas.py:
class ControlFlagRequest(BaseModel):
    action: Literal["start", "stop", "reset", "rescan"]
    issued_by: str = "gui"  # "gui" or "system"

class ControlFlagResponse(BaseModel):
    id: int
    action: str
    issued_by: str
    status: str  # "pending" or "acknowledged"

# In routers/jobs.py:
@router.post("/jobs/{session_id}/control", response_model=ControlFlagResponse)
def issue_control_flag(
    session_id: int,
    body: ControlFlagRequest,
    conn: sqlite3.Connection = Depends(get_db_dep)
):
    """Write a control flag. Pis observe via polling or Socket.IO."""
    cursor = conn.execute(
        """
        INSERT INTO job_control (session_id, action, issued_by, issued_at, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, body.action, body.issued_by, datetime.now(timezone.utc), "pending"),
    )
    flag_id = cursor.lastrowid
    conn.commit()

    # Broadcast to all connected Pis
    await sio.emit(
        "control_flag_issued",
        {"session_id": session_id, "action": body.action, "issued_by": body.issued_by},
    )

    return ControlFlagResponse(
        id=flag_id,
        action=body.action,
        issued_by=body.issued_by,
        status="pending",
    )

@router.get("/jobs/{session_id}/control")
def get_pending_control_flags(
    session_id: int,
    conn: sqlite3.Connection = Depends(get_db_dep)
):
    """Pis poll this to get pending commands."""
    rows = conn.execute(
        "SELECT * FROM job_control WHERE session_id = ? AND status = 'pending' ORDER BY issued_at DESC LIMIT 1",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]

@router.post("/jobs/{session_id}/control/ack")
def acknowledge_control_flag(
    session_id: int,
    flag_id: int,
    conn: sqlite3.Connection = Depends(get_db_dep)
):
    """Pi acknowledges receipt of a control flag."""
    conn.execute(
        "UPDATE job_control SET status = 'acknowledged' WHERE id = ?",
        (flag_id,),
    )
    conn.commit()
    return {"status": "acknowledged"}
```

### Anti-Patterns to Avoid

- **In-memory state on the state machine instance:** Tempting because it's fast, but breaks TEST-02 (can't test without a running server) and fails in distributed scenarios where multiple requests might race.
- **Putting state machine logic in the route handler:** Creates spaghetti; logic is scattered across files. Centralizing in `job_state.py` makes TEST-02 possible and testing easier.
- **Using an external scheduler (APScheduler, Celery) for heartbeat monitoring:** Adds dependency, complexity, and a new process to manage. `asyncio.create_task()` is sufficient for a 2-second polling loop and fits the single-server (Database Pi) architecture.
- **Storing control flags only in memory or transient state:** Pis can miss messages if they're offline momentarily. Database persistence ensures the command survives network flaps.
- **Relying only on WebSocket broadcasts for control flags:** WebSocket is real-time but unreliable (disconnections, no persistence). Combining database polling + Socket.IO broadcasts gives both reliability and speed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Finite state machine logic for job pipeline | Custom nested if/elif chain to validate transitions | `JobStateMachine` class with dict-based transition table | Easier to understand at a glance; catches invalid transitions early; testable in isolation; extensible when states change |
| Heartbeat timeout detection | Manual timestamp comparison in routes | Background `asyncio.create_task()` polling loop | Decouples timeout logic from request handlers; can check all Pis simultaneously; doesn't block request processing |
| Control flag delivery | Send and hope (one-shot message) | Database table + polling + Socket.IO | Ensures Pis receive commands even if offline; persistent audit trail; Pis can retry if they miss a broadcast |
| Job state broadcast to GUI | Manual `await sio.emit()` scattered throughout routes | Centralized state machine that calls a "broadcast on transition" helper | Avoids duplicate broadcasts; guarantees GUI stays in sync; easy to add new listeners (e.g., logs, metrics) |

**Key insight:** The state machine is the core abstraction. Every decision (whether a Pi can move to the next stage, whether a job should error, whether to broadcast) flows through it. Hand-rolled state checks in each route quickly become inconsistent and brittle.

## Common Pitfalls

### Pitfall 1: Race Condition on Concurrent Transition Requests

**What goes wrong:** Two routes try to transition the same job simultaneously. Without locking, both might see status="scanning" and both execute their transition checks, leading to inconsistent state or bypassed validations.

**Why it happens:** SQLite allows concurrent reads, but writes serialize. However, validating then writing introduces a read-write race window.

**How to avoid:** Use database transactions and constraints. The validation happens *inside* the update, not before. Example: `JobStateMachine.validate_transition()` reads the current status, and `crud.update_solve_session_status()` commits in one transaction. If a concurrent update changed the status, the second request's validation will catch it (because it re-reads the row). For extra safety, use SQLite's `SERIALIZABLE` isolation level or add a check inside the UPDATE itself (e.g., `WHERE status = ?`).

**Warning signs:** Logs showing "Invalid transition: scanning → executing" when you expected it to succeed; multiple routes triggering transitions at the same time.

### Pitfall 2: Heartbeat Monitor Gets Stuck or Crashes Silently

**What goes wrong:** The `asyncio.create_task()` background loop encounters an exception (DB connection error, Socket.IO emit fails) and silently exits. The monitor stops working, and jobs never transition to Error when Pis go offline.

**Why it happens:** Background tasks don't have a parent context to propagate exceptions; without explicit try/except, they fail silently.

**How to avoid:** Wrap the heartbeat monitor in try/except at the loop level (as shown in the example above). Log errors but continue looping. Also, test the monitor with a mock DB that raises exceptions to verify it doesn't crash.

**Warning signs:** Pis stay "offline" but active jobs never error; no log entries from the monitor after a while.

### Pitfall 3: Job Transitions Without Checking Prerequisite Data

**What goes wrong:** A route accepts `POST /jobs/{id}/transition` with `{"to": "executing"}` without verifying a solution exists. The job moves to executing, but the Motor Pi finds no steps to execute.

**Why it happens:** Transition validation is purely graph-based (is the edge in the state machine?) rather than semantic (does the data exist?).

**How to avoid:** Pre-transition checks fetch dependent data. Example: before Scanning → Solving, verify `SELECT * FROM cube_states WHERE session_id = ? AND is_valid = 1 AND confidence > 0.8`. Before Solving → Executing, verify `SELECT * FROM solutions WHERE session_id = ?`. These checks are part of `JobStateMachine.validate_transition()`.

**Warning signs:** Jobs in Executing state but no rows in `solutions` table; Motor Pi receives empty move lists.

### Pitfall 4: Control Flag Gets Lost Due to Polling Latency

**What goes wrong:** GUI issues a "stop" command, but the Motor Pi only polls `/jobs/{id}/control` every 5 seconds. By the time the Pi reads the flag, 5 seconds have passed and the cube is already mid-execution.

**Why it happens:** Pure polling has inherent latency; Socket.IO broadcasts are fast but fragile (dropped if Pi is momentarily offline).

**How to avoid:** Combine strategies. Control flags live in the database (persistent). The Pi polls every 1–2 seconds *and* listens for `control_flag_issued` Socket.IO broadcasts. If a broadcast arrives, the Pi checks the flag immediately; if the Pi is offline, it reads the persisted flag on reconnect. This gives both low-latency (broadcast) and reliability (polling) with no additional infrastructure.

**Warning signs:** Motors don't respond to stop commands promptly; GUI says "stopping" but the cube keeps moving for several seconds.

### Pitfall 5: Heartbeat Monitor Errors Jobs Too Aggressively

**What goes wrong:** A Pi experiences a brief network hiccup (2-second lag in sending heartbeat) and the monitor immediately errors the job. The job is now in Error state and the GUI shows a red error banner, even though the Pi is still working.

**Why it happens:** The 5-second threshold is correct for long-term failures, but heartbeat granularity can be coarse if Pis send updates infrequently.

**How to avoid:** The heartbeat monitor only errors jobs if a Pi is stale *and* the job is actively running (status in [scanning, solving, executing]). If a Pi comes back before the job moves to the next state, the job is still valid. For extra resilience, log warnings at 3 seconds and only error at 5 seconds; alert the GUI ("Warning: Pi response slow") at 3 seconds and error it only if it persists.

**Warning signs:** Jobs erroring intermittently during normal operation; network logs showing brief, recoverable hiccups correspond to job error events.

## Code Examples

Verified patterns from official sources:

### Example 1: Unit Test of State Machine (No Server Required)

```python
# Source: D-04 from CONTEXT.md — TEST-02 requirement
# File: backend/tests/test_job_state.py (to be created in Phase 3)

import sqlite3
import tempfile
from database.init_db import create_tables
from database import crud
from database.models import SolveSessionCreate
from backend.job_state import JobStateMachine

def test_state_machine_transition_valid():
    """JobStateMachine accepts legal transitions (no server needed)."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    create_tables(conn)

    # Create a session in idle state
    session_id = crud.create_solve_session(conn, SolveSessionCreate(
        selected_algorithm="CFOP",
        status="idle",
    ))

    # Transition idle -> scanning (legal)
    JobStateMachine.transition(conn, session_id, "scanning")

    # Verify state changed
    row = crud.get_solve_session_by_id(conn, session_id)
    assert row["status"] == "scanning"

    # Transition scanning -> solving (legal)
    JobStateMachine.transition(conn, session_id, "solving")
    row = crud.get_solve_session_by_id(conn, session_id)
    assert row["status"] == "solving"

    conn.close()

def test_state_machine_transition_illegal():
    """JobStateMachine rejects illegal transitions."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    create_tables(conn)

    # Create a session in idle state
    session_id = crud.create_solve_session(conn, SolveSessionCreate(
        selected_algorithm="CFOP",
        status="idle",
    ))

    # Try to jump from idle -> executing (illegal)
    with pytest.raises(ValueError, match="Invalid transition"):
        JobStateMachine.transition(conn, session_id, "executing")

    # Verify state didn't change
    row = crud.get_solve_session_by_id(conn, session_id)
    assert row["status"] == "idle"

    conn.close()
```

### Example 2: State Machine with Pydantic Request Validation

```python
# Source: D-05, D-06 from CONTEXT.md
# File: backend/schemas.py (extend existing file)

from typing import Literal
from pydantic import BaseModel, field_validator

class JobTransitionRequest(BaseModel):
    to: Literal["idle", "scanning", "solving", "executing", "done", "error"]

    # Optional: validate that 'to' is a valid state (Literal does this automatically in v2)

# In routers/jobs.py:
@router.post("/jobs/{session_id}/transition")
async def transition_job(
    session_id: int,
    body: JobTransitionRequest,
    conn: sqlite3.Connection = Depends(get_db_dep)
):
    """POST /jobs/{session_id}/transition with {"to": "solving"}."""
    try:
        JobStateMachine.transition(conn, session_id, body.to)
        # Broadcast new state to all connected clients
        await sio.emit(
            "job_state_update",
            {
                "session_id": session_id,
                "status": body.to,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        return {"session_id": session_id, "status": body.to}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Example 3: Integrating Heartbeat Monitor into FastAPI Startup

```python
# Source: D-08 from CONTEXT.md
# File: backend/main.py (extend existing file)

import asyncio
from backend.heartbeat import heartbeat_monitor

@fastapi_app.on_event("startup")
async def startup_event():
    """Start the background heartbeat monitor on app startup."""
    asyncio.create_task(heartbeat_monitor())

# Or with the newer lifespan API (FastAPI 0.93+):
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(heartbeat_monitor())
    yield
    # Shutdown (if needed)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

fastapi_app = FastAPI(lifespan=lifespan)
```

## Environment Availability

No external dependencies beyond those already in `.venv/`:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.13.12 | — |
| FastAPI | Routers | ✓ | 0.109.0+ | — |
| python-socketio | Broadcasts | ✓ | 5.11.0+ | — |
| Pydantic | Validation | ✓ | 2.x | — |
| pytest | Testing | ✓ | 8.3.4 | — |
| SQLite (sqlite3) | Database | ✓ | Built-in | — |
| asyncio | Heartbeat task | ✓ | Built-in | — |

All required tools are present and working. No external services or CLI tools needed for Phase 3.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | pytest.ini (testpaths: database/tests, backend/tests) |
| Quick run command | `pytest backend/tests/test_job_state.py -x` |
| Full suite command | `pytest -xvs` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| JOB-01 | Legal transitions allowed, illegal rejected | unit | `pytest backend/tests/test_job_state.py::test_state_machine_transition_legal -x` | ❌ Wave 0 |
| JOB-01 | All 5 states represented in transition table | unit | `pytest backend/tests/test_job_state.py::test_state_machine_all_states -x` | ❌ Wave 0 |
| JOB-02 | Scanning → Solving blocked if no valid cube state | unit | `pytest backend/tests/test_job_state.py::test_scanning_to_solving_requires_cube_state -x` | ❌ Wave 0 |
| JOB-03 | Solving → Executing blocked if no solution | unit | `pytest backend/tests/test_job_state.py::test_solving_to_executing_requires_solution -x` | ❌ Wave 0 |
| JOB-04 | Stale Pi (5+ sec) errors active job | integration | `pytest backend/tests/test_heartbeat.py::test_heartbeat_monitor_errors_stale_pi -x` | ❌ Wave 0 |
| JOB-04 | Offline Pi during idle job does not error | integration | `pytest backend/tests/test_heartbeat.py::test_heartbeat_monitor_ignores_stale_idle_job -x` | ❌ Wave 0 |
| JOB-05 | Control flag written to job_control table | integration | `pytest backend/tests/test_control_flags.py::test_post_control_flag_creates_row -x` | ❌ Wave 0 |
| JOB-05 | Control flag readable via GET endpoint | integration | `pytest backend/tests/test_control_flags.py::test_get_pending_control_flags -x` | ❌ Wave 0 |
| TEST-02 | State machine tests work with in-memory DB | unit | `pytest backend/tests/test_job_state.py -x` (all tests use tempfile, no server) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_job_state.py -x` (state machine unit tests < 1s)
- **Per wave merge:** `pytest -xvs` (full suite including integration tests < 5s)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_job_state.py` — unit tests for JobStateMachine.validate_transition() and JobStateMachine.transition(), covering all 8 transitions and 5 states, plus prerequisite data checks (JOB-02, JOB-03)
- [ ] `backend/tests/test_heartbeat.py` — integration tests for heartbeat_monitor asyncio task, mocking `asyncio.sleep()` and time progression to verify 5-second timeout and Error state transition
- [ ] `backend/tests/test_control_flags.py` — integration tests for POST/GET control flag endpoints, job_control table CRUD, Socket.IO broadcast assertions
- [ ] `backend/job_state.py` — JobStateMachine class implementation
- [ ] `backend/heartbeat.py` — heartbeat_monitor() coroutine
- [ ] `database/schema.sql` — add job_control table definition (D-15)
- [ ] `database/models.py` — add JobControl, JobControlCreate Pydantic models
- [ ] `database/crud.py` — add CRUD functions for job_control (create, get pending, update status)
- [ ] `backend/schemas.py` — add JobTransitionRequest, ControlFlagRequest, ControlFlagResponse schemas
- [ ] `backend/routers/jobs.py` — add POST /jobs/{id}/transition, POST /jobs/{id}/control, POST /jobs/{id}/control/ack, GET /jobs/{id}/control endpoints
- [ ] `backend/main.py` — add startup event or lifespan context to launch heartbeat_monitor task

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate state machines per Pi (scanner, solver, motor) | Single server-side job state machine coordinating all Pis | Phase 3 | Eliminates inconsistency between Pi state machines; single source of truth; easier to test |
| Manual state checks in each route (if job.status == 'scanning' and ...) | Centralized JobStateMachine class with transition table | Phase 3 | Reduces code duplication; catches invalid transitions early; extensible |
| Immediate motor stop on GUI click (fire and forget) | Control flags persisted in DB, polled or broadcast | Phase 3 | Ensures stop command survives network glitches; audit trail for debugging |
| No heartbeat monitoring (assumption Pis stay online) | Background asyncio task checks last_heartbeat every 2 seconds | Phase 3 | Detects Pi failures within 5 seconds; errors jobs automatically; GUI shows error banner |

**Deprecated/outdated:**
- **Manual state validation per route:** Being replaced by JobStateMachine class.
- **Hardcoded state transitions:** Being replaced by dict-based transition table in JobStateMachine.

## Open Questions

1. **Lifespan vs. on_event for starting the heartbeat monitor**
   - What we know: FastAPI 0.93+ supports `lifespan` context managers; older versions use `@app.on_event("startup")`. Both work; lifespan is newer and more explicit.
   - What's unclear: Which pattern Saim prefers for this codebase; whether existing startup code uses one pattern consistently.
   - Recommendation: Check if `backend/main.py` already has `@app.on_event()` decorators. If yes, use that pattern for consistency. If no, use lifespan (modern, cleaner). Either works; consistency matters more.

2. **Handling Pi reconnection after being declared dead**
   - What we know: If a Pi goes offline and a job is errored, the Pi can't "recover" the job automatically. D-11 says "only error if there's an active job", so offline Pis during idle don't cause errors.
   - What's unclear: Can a Pi send heartbeats after being errored? Should it? Should the job automatically re-enter "scanning" if the Pi comes back?
   - Recommendation: For v1, keep it simple: once a job is Error, it stays Error. A human (GUI) must explicitly reset it. If a Pi comes back online after erroring a job, its heartbeats are recorded but don't change job state. In v2, could add auto-recovery logic.

3. **Whether to use apscheduler if asyncio task proves unreliable**
   - What we know: `asyncio.create_task()` in a startup event works well for simple polling; it's lightweight and no external dependencies.
   - What's unclear: Reliability under high load, Pi network glitches, or other edge cases.
   - Recommendation: Start with asyncio. If tests fail or the task crashes during integration testing, switch to apscheduler. For Phase 3, the 2-second heartbeat check is simple enough that asyncio should be fine. Revisit in Phase 4 if needed.

## Sources

### Primary (HIGH confidence)
- **Context7:** FastAPI 0.109.0+ documentation — async route handlers, Depends() injection, startup events
- **Official FastAPI docs:** https://fastapi.tiangolo.com/tutorial/background-tasks/ — startup events and background tasks
- **Official python-socketio docs:** AsyncServer creation, `await sio.emit()` patterns, broadcast behavior
- **Project codebase:** `backend/main.py`, `backend/sio_instance.py`, `backend/routers/jobs.py`, `database/crud.py` — existing patterns for dependency injection, router registration, DB access

### Secondary (MEDIUM confidence)
- **Async patterns:** https://docs.python.org/3/library/asyncio-task.html — asyncio.create_task() documented behavior, background daemon tasks
- **State machine patterns:** https://auth0.com/blog/state-pattern-in-python/ — Python state pattern design; why custom state machines are appropriate for small schemas
- **Distributed system patterns:** https://microservices.io/patterns/data/polling-publisher.html — polling vs. event-driven communication, database polling pattern for command delivery
- **Pydantic validation:** https://docs.pydantic.dev/2.0/usage/types/enums/ — Literal and Enum types for constrained validation

### Tertiary (LOW confidence, marked for validation)
- **APScheduler alternative:** https://apscheduler.readthedocs.io/ — mentioned as possible alternative if asyncio task proves unreliable; not verified as necessary for Phase 3

## Metadata

**Confidence breakdown:**
- **Standard stack:** HIGH — All libraries already in project; versions verified against requirements.
- **Architecture patterns:** HIGH — D-01 through D-15 locked decisions; patterns directly derived from project constraints.
- **State machine design:** HIGH — Simple 5-state system; transition table is straightforward; verified against JOB-01 requirement.
- **Heartbeat monitoring:** MEDIUM-HIGH — asyncio pattern is standard; 5-second timeout from JOB-04 requirement; integration details (which jobs to error) derived from D-10, D-11.
- **Control flags:** MEDIUM — Database + polling + Socket.IO is a sound pattern (verified in microservices literature); specific schema (job_control table) locked in CONTEXT.md; REST endpoint design standard for FastAPI.
- **Common pitfalls:** MEDIUM — Based on general distributed system knowledge; some (race conditions, polling latency) are specific to this implementation and would be better validated with actual testing.

**Research date:** 2026-03-26
**Valid until:** 2026-04-09 (14 days — state machine requirements are stable; heartbeat monitoring is straightforward; low risk of docs changing)

