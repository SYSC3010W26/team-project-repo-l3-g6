---
phase: 03-job-state-machine
plan: 02
subsystem: api
tags: [fastapi, asyncio, heartbeat, socketio, sqlite]

# Dependency graph
requires:
  - phase: 03-01
    provides: JobStateMachine class and InvalidTransitionError (backend/job_state.py)
  - phase: 02-fastapi-backend
    provides: FastAPI app, sio_instance, db_session, crud functions
provides:
  - backend/heartbeat.py with heartbeat_monitor() background coroutine
  - backend/main.py startup event launching heartbeat_monitor via asyncio.create_task
  - backend/job_state.py (created as Rule 3 blocking-dependency fix)
affects: [03-03, 04-web-dashboard, 05-3d-cube-visualization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "asyncio background task pattern: asyncio.create_task in @on_event('startup')"
    - "Heartbeat monitor: poll DB every 2s, compare timestamps, transition stale jobs to error"
    - "Exception survivor loop: outer try/except keeps heartbeat polling alive through DB/SIO errors"

key-files:
  created:
    - backend/heartbeat.py
    - backend/job_state.py
  modified:
    - backend/main.py

key-decisions:
  - "heartbeat_monitor() uses asyncio.sleep(2) at top of loop before DB access so it doesn't hammer DB on startup"
  - "Only jobs with status IN ('scanning','solving','executing') receive Error transition — idle/done/error jobs are skipped (D-11)"
  - "InvalidTransitionError and ValueError caught per-job inside the active_jobs loop to prevent one race from killing all jobs"
  - "job_state.py created as Rule 3 deviation — 03-01 dependency not yet committed by parallel agent"

patterns-established:
  - "Background async task: asyncio.create_task inside @fastapi_app.on_event('startup')"
  - "Stale node detection: datetime.fromisoformat + timezone-aware comparison"

requirements-completed: [JOB-04]

# Metrics
duration: 12min
completed: 2026-03-26
---

# Phase 03 Plan 02: Heartbeat Monitor Summary

**asyncio background task polls node_status every 2s and transitions active jobs to Error state with FATAL log + Socket.IO broadcast when any Pi goes silent for 5+ seconds (JOB-04)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-26T00:00:00Z
- **Completed:** 2026-03-26T00:12:00Z
- **Tasks:** 2
- **Files modified:** 3 (2 created, 1 modified)

## Accomplishments
- Created `backend/heartbeat.py` with `heartbeat_monitor()` async coroutine implementing 2s poll / 5s dead threshold
- Wired heartbeat_monitor into FastAPI startup event via `asyncio.create_task` in `backend/main.py`
- All 30 existing tests still pass after startup event registration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create backend/heartbeat.py** - `a19ce91` (feat)
2. **Task 2: Register heartbeat_monitor in main.py startup** - `992c095` (feat)

## Files Created/Modified
- `backend/heartbeat.py` - Heartbeat monitor coroutine: polls node_status, detects stale Pis, transitions active jobs to error, writes FATAL log, emits job_state_update
- `backend/job_state.py` - JobStateMachine class (Rule 3 deviation — created as 03-01 dependency)
- `backend/main.py` - Added asyncio import, heartbeat_monitor import, and @on_event("startup") handler

## Decisions Made
- Used `asyncio.sleep` at the top of the while loop (before DB access) to avoid hammering DB immediately on startup
- Per-job exception handling inside active_jobs loop — `InvalidTransitionError` and `ValueError` silently ignored to handle race conditions where job was already transitioned
- Stale Pis with no active jobs get a WARNING log (not Error) per D-11
- `on_event("startup")` generates a deprecation warning in newer FastAPI but still works correctly — noted in test output

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created backend/job_state.py as 03-01 dependency**
- **Found during:** Task 1 (creating backend/heartbeat.py)
- **Issue:** heartbeat.py imports JobStateMachine from backend.job_state, but job_state.py was to be created by plan 03-01 which had not yet been committed by the parallel agent
- **Fix:** Created backend/job_state.py with the full JobStateMachine class exactly as specified in 03-01-PLAN.md — VALID_TRANSITIONS dict, transition() method, _require_valid_cube_state() and _require_solution() guards
- **Files modified:** backend/job_state.py
- **Verification:** Module import verified; heartbeat_monitor() imports and runs correctly
- **Committed in:** a19ce91 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking dependency)
**Impact on plan:** Necessary to unblock Task 1. job_state.py content matches 03-01-PLAN.md spec exactly — the parallel agent will find it already present.

## Issues Encountered
- None beyond the blocking dependency described above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Heartbeat monitor is live on server boot — JOB-04 fully satisfied
- `backend/job_state.py` available for 03-03 (control flags, job transition endpoint)
- All 30 tests green; no regressions

---
*Phase: 03-job-state-machine*
*Completed: 2026-03-26*
