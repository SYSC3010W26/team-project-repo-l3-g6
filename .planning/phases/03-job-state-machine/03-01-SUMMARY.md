---
phase: 03-job-state-machine
plan: 01
subsystem: database, api
tags: [sqlite, fastapi, pydantic, state-machine, job-control]

# Dependency graph
requires:
  - phase: 02-fastapi-backend
    provides: REST routers, Socket.IO sio instance, Depends(get_db_dep) pattern, schemas.py, crud.py, models.py

provides:
  - job_control table in database/schema.sql with id, session_id, action, issued_by, issued_at, status columns
  - JobControlCreate, JobControl Pydantic models in database/models.py
  - create_job_control, get_pending_controls, ack_job_control CRUD functions in database/crud.py
  - backend/job_state.py with JobStateMachine class and InvalidTransitionError exception
  - VALID_TRANSITIONS dict enforcing Idle/Pending → Scanning → Solving → Executing → Done/Error
  - Pre-transition guards: _require_valid_cube_state (JOB-02) and _require_solution (JOB-03)
  - JobTransitionRequest, JobTransitionResponse, ControlFlagRequest, ControlFlagResponse, ControlAckRequest schemas
  - POST /jobs/{id}/transition endpoint — validates and executes state transitions with Socket.IO broadcast
  - POST /jobs/{id}/control endpoint — writes GUI control flags (start/stop/reset/rescan)
  - GET /jobs/{id}/control endpoint — returns pending control flags for subsystems to poll
  - POST /jobs/{id}/control/ack endpoint — acknowledges consumed control flags

affects:
  - 03-02-heartbeat-monitor (reads node_status, emits job_state_update via sio)
  - 03-03-control-flags-tests (tests JobStateMachine and control endpoints)
  - 04-web-dashboard (calls transition and control endpoints from GUI)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - JobStateMachine is stateless — all state sourced from solve_sessions.status in DB; testable with any sqlite3.Connection
    - Pre-transition guards query cube_states and solutions tables directly via conn.execute (not crud functions) for simplicity
    - Control flags use job_control table as observable event bus — written by GUI, consumed (acked) by Pi subsystems
    - transition endpoint is async to support await sio.emit(); control flag endpoints follow same pattern

key-files:
  created:
    - backend/job_state.py
  modified:
    - database/schema.sql
    - database/models.py
    - database/crud.py
    - backend/schemas.py
    - backend/routers/jobs.py
    - database/tests/test_schema.py

key-decisions:
  - "JobStateMachine is stateless — reads current status from DB on each call; no in-memory state"
  - "pending status (from /jobs/start) is allowed to transition to scanning — matches real startup flow"
  - "Pre-transition guards query DB directly via conn.execute rather than CRUD helpers to keep job_state.py self-contained"
  - "test_all_11_tables_created renamed to test_all_12_tables_created after adding job_control table"

patterns-established:
  - "State machine pattern: VALID_TRANSITIONS dict + guard methods in dedicated module (backend/job_state.py)"
  - "Control flag bus: job_control table as DB-backed observable event queue — write (GUI) / poll+ack (Pi subsystems)"

requirements-completed: [JOB-01, JOB-02, JOB-03]

# Metrics
duration: 2min
completed: 2026-03-26
---

# Phase 3 Plan 01: Job State Machine Summary

**JobStateMachine class enforcing Idle/Pending → Scanning → Solving → Executing → Done/Error pipeline with pre-transition DB guards, job_control table for GUI control flags, and four new REST endpoints**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-26T16:16:57Z
- **Completed:** 2026-03-26T16:19:38Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- job_control table added to schema.sql with full CRUD coverage (create, query pending, acknowledge)
- JobStateMachine enforces legal state transitions and blocks illegal jumps (e.g., scanning → executing raises InvalidTransitionError)
- Pre-transition guards enforce JOB-02 (cube state must exist before solving) and JOB-03 (solution must exist before executing)
- Four REST endpoints added: transition, control POST, control GET, control/ack — all wired to DB and Socket.IO broadcasts
- All 30 tests still pass after changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Add job_control table to schema + models + CRUD** - `b4d61e9` (feat)
2. **Task 2: JobStateMachine class + Pydantic schemas + transition endpoint** - `c64491f` (feat)

## Files Created/Modified

- `backend/job_state.py` - JobStateMachine class with VALID_TRANSITIONS dict, transition() method, and pre-transition guards
- `database/schema.sql` - Added job_control table DDL after system_logs
- `database/models.py` - Added JobControlCreate and JobControl Pydantic models
- `database/crud.py` - Added JobControlCreate import and three CRUD functions (create_job_control, get_pending_controls, ack_job_control)
- `backend/schemas.py` - Added JobTransitionRequest, JobTransitionResponse, ControlFlagRequest, ControlFlagResponse, ControlAckRequest
- `backend/routers/jobs.py` - Added _state_machine singleton and four new endpoints (transition, control POST/GET, control/ack)
- `database/tests/test_schema.py` - Updated test name and expected table set to include job_control (11 → 12 tables)

## Decisions Made

- JobStateMachine is stateless: reads current status from DB on every call; no in-memory state cached between requests. This makes it directly testable by passing any sqlite3.Connection.
- `pending` status (created by `POST /jobs/start`) is included in VALID_TRANSITIONS as allowed to transition to `scanning`, matching the real startup sequence.
- Pre-transition guards (`_require_valid_cube_state`, `_require_solution`) use `conn.execute` directly rather than CRUD helpers to keep `backend/job_state.py` self-contained and independently testable.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_schema.py to expect 12 tables instead of 11**
- **Found during:** Task 2 (verification - pytest run)
- **Issue:** `test_all_11_tables_created` asserted exactly 11 tables; adding `job_control` caused it to fail with "Extra: ['job_control']"
- **Fix:** Renamed test to `test_all_12_tables_created` and added `job_control` to the expected_tables set
- **Files modified:** `database/tests/test_schema.py`
- **Verification:** All 30 tests pass after fix
- **Committed in:** `c64491f` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Required fix — the schema test was testing the old table count. No scope creep.

## Issues Encountered

None — all plan steps executed as specified, one test updated to reflect new schema state.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- JobStateMachine is fully testable without a running server — passes a bare sqlite3.Connection
- job_control table ready for Phase 03-03 unit tests
- Heartbeat monitor (Plan 03-02) can emit `error` transitions via `_state_machine.transition(conn, session_id, 'error')`
- All 4 control flag endpoints ready for web dashboard integration (Plan 04)

---
*Phase: 03-job-state-machine*
*Completed: 2026-03-26*
