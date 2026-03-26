# Roadmap: Pi³ — Database & GUI Pi (Saim)

**Milestone:** v1.0 — Full pipeline demo ready

## Phases

- [x] **Phase 1: Database Foundation** - Complete database layer with schema, CRUD ops, and unit tests
- [x] **Phase 2: FastAPI Backend** - REST and WebSocket API serving all subsystems on LAN (completed 2026-03-26)
- [ ] **Phase 3: Job State Machine** - Pipeline ordering enforcement, heartbeat monitoring, control flags
- [ ] **Phase 4: Web Dashboard (Core Pages)** - All 5 dashboard pages connected to live data
- [ ] **Phase 5: 3D Cube Visualization and Notifications** - 3D cube model and fatal error notifications

## Phase Details

### Phase 1: Database Foundation
**Goal**: Complete database layer is initialized, tested, and ready for other subsystems to integrate against.
**Depends on**: Nothing (first phase)
**Requirements**: [DB-01, DB-02, DB-03, DB-04, TEST-01]
**Success Criteria** (what must be TRUE):
  1. Running `python init_db.py` creates a valid SQLite database with all 11 tables
  2. All CRUD tests pass for tables used by other subsystems
  3. Scanner, Solver, and Motor Pis can write/read their respective tables without errors
**Plans:** 3/3 plans executed

Plans:
- [x] 01-01-PLAN.md — Schema verification, init_db.py refactor, pytest infrastructure and test fixture
- [x] 01-02-PLAN.md — CRUD operations for all 6 missing tables (scan_faces, solution_steps, execution_runs, motor_execution_log, verification_results, users)
- [x] 01-03-PLAN.md — Unit tests for all CRUD operations across all 11 tables

### Phase 2: FastAPI Backend
**Goal**: REST and WebSocket API is running on the Pi, reachable by all subsystems on the LAN, and serves as the integration bridge for the full pipeline.
**Depends on**: Phase 1
**Requirements**: [API-01, API-02, API-03, API-04, API-05, TEST-03]
**Success Criteria** (what must be TRUE):
  1. All other Pi subsystems can call the API and receive correct responses
  2. WebSocket client receives real-time updates as job state changes
  3. Integration tests pass for happy-path data flow
  4. Server accessible at `http://<rpi4-ip>:8000`
**Plans:** 3/3 plans complete

Plans:
- [x] 02-01-PLAN.md — Backend package scaffold, schemas, deps, main.py with FastAPI + socketio ASGI mount
- [x] 02-02-PLAN.md — All 6 REST routers (jobs, scan, solve, execute, nodes, logs) with full CRUD logic
- [x] 02-03-PLAN.md — Socket.IO event handlers for Motor Pi + integration tests for happy-path flow

### Phase 3: Job State Machine
**Goal**: Server enforces the Scan to Solve to Execute to Done pipeline ordering, detects Pi failures via heartbeat monitoring, and exposes control signals for GUI actions.
**Depends on**: Phase 2
**Requirements**: [JOB-01, JOB-02, JOB-03, JOB-04, JOB-05, TEST-02]
**Success Criteria** (what must be TRUE):
  1. Job cannot skip stages (e.g., cannot execute before solve is complete)
  2. Simulating a missing heartbeat causes Error state within 5 seconds
  3. State machine tests pass in isolation (no hardware required)
  4. GUI control flags (Start, Stop, Reset, Rescan) are written and observable by subsystems
**Plans**: TBD

Plans:
- [ ] 03-01: State machine (Idle, Scanning, Solving, Executing, Done/Error) with enforced transitions
- [ ] 03-02: Heartbeat monitor background task
- [ ] 03-03: Control flags and state machine unit tests

### Phase 4: Web Dashboard (Core Pages)
**Goal**: All 5 dashboard pages are functional, accessible from phone/computer on LAN, and connected to live data via WebSocket.
**Depends on**: Phase 3
**Requirements**: [GUI-01, GUI-02, GUI-03, GUI-04, GUI-05, GUI-07, GUI-08]
**Success Criteria** (what must be TRUE):
  1. All 5 pages render and show real data from the database
  2. WebSocket updates Dashboard and Execution Monitor in real time without page refresh
  3. Accessible from a phone browser on the same Wi-Fi network
  4. Start/Stop/Reset/Rescan buttons trigger correct control flag writes
**Plans**: TBD

Plans:
- [ ] 04-01: React/Vue app scaffold and Dashboard page (pipeline stage, node health, control buttons)
- [ ] 04-02: Solve Results and Solution Review pages
- [ ] 04-03: Execution Monitor and System Logs pages

### Phase 5: 3D Cube Visualization and Notifications
**Goal**: Dashboard shows an interactive 3D cube model reflecting the current scanned state, and fatal errors trigger visible notifications.
**Depends on**: Phase 4
**Requirements**: [GUI-06, NOTF-01, NOTF-02, NOTF-03]
**Success Criteria** (what must be TRUE):
  1. Scanning a cube updates the 3D model on the dashboard with correct face colors
  2. Simulating a fatal error triggers both the error banner and browser notification
  3. 3D model renders on mobile browser without performance issues
  4. Recovery guidance shown alongside error state
**Plans**: TBD

Plans:
- [ ] 05-01: Three.js 3D cube model with cube state color mapping
- [ ] 05-02: Fatal error banner, browser notifications, and recovery guidance

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Database Foundation | 3/3 | Complete |  |
| 2. FastAPI Backend | 3/3 | Complete   | 2026-03-26 |
| 3. Job State Machine | 0/3 | Not started | - |
| 4. Web Dashboard (Core Pages) | 0/3 | Not started | - |
| 5. 3D Cube Visualization and Notifications | 0/2 | Not started | - |

---
*Roadmap reformatted: 2026-03-24 for GSD tooling compatibility*
*Last updated: 2026-03-25*
