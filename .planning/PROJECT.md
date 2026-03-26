# Pi³ — Rubik's Cube Solver

## What This Is

Pi³ is a distributed Rubik's cube solving robot built for SYSC3010 (Group L3-G6). A physical robot with 5 stepper motors and 2 cameras scans a scrambled cube, computes a CFOP solution, and physically executes it — all coordinated by 4 Raspberry Pis communicating through a central database. A web dashboard (phone/computer) gives users real-time visibility and control over the solving process.

## Core Value

A scrambled cube placed in the robot comes out solved, with the full pipeline (Scan → Solve → Execute → Verify) running end-to-end without manual intervention.

## Requirements

### Validated

- ✓ Cube state representation (54-facelet array, 54-char string) — existing
- ✓ CFOP algorithm structure (AlgorithmSelector, CFOPAlgorithm, permutation tables) — existing
- ✓ Colour detection pipeline (HSV classification, face scan from camera frame) — existing
- ✓ Database schema (jobs, cube_states, solutions, execution_status, events, heartbeats) — existing
- ✓ Motor state machine (STARTUP → WAITING_FOR_LIST → WAITING_FOR_START → EXECUTING) — existing
- ✓ Node heartbeat protocol (periodic emission, TCP registration pattern) — existing
- ✓ End-to-end demo (TCP stubs: Scanner, Solver, Motor nodes, Run_Tests orchestrator) — existing

### Active

- [ ] **Scanner integration** — Full camera capture pipeline connected to DB: scan both faces, validate cube state, write to `cube_states` table with confidence flag
- [ ] **Solver completion** — CFOP algorithm fully solves any valid cube state; reads from DB, writes move sequence to `solutions` table; optimize for move count (variant generation)
- [ ] **Motor execution** — Implement `execute_move_sequence()`: translate move notation (R U R' U' etc.) to GPIO/STEP-DIR signals via motor bridge IC; ensure exactly 90° rotation, <15s total solve
- [x] **Database backend (FastAPI)** — REST + WebSocket API exposing job state, cube states, solutions, execution progress, node health; serves as the integration layer for all 4 Pis — Validated in Phase 02: fastapi-backend
- [ ] **Job state machine** — Server enforces Idle → Scanning → Solving → Executing → Done/Error transitions; detects missing heartbeats (>5s) and transitions to Error
- [ ] **Web dashboard** — All 5 pages: Dashboard, Solve Results, Execution Monitor, Solution Review, System Logs; React or Vue; 3D cube model display; phone/computer accessible on local LAN
- [ ] **Heartbeat monitoring** — Server detects unresponsive Pi within 5 seconds; GUI shows node online/offline status; fatal errors trigger browser notification
- [ ] **Notification system** — GUI banner + browser notification on fatal error (disconnected motor/camera, unresponsive Pi)
- [ ] **Solve verification** — After motor execution completes, scanner re-checks cube state and writes result to `verification_results`; GUI displays confirmed-solved status
- [ ] **Pipeline integration** — All 4 subsystems wired end-to-end through the database; full solve triggered from GUI Start button without manual steps between stages
- [ ] **Unit tests** — Each subsystem independently testable: motor state machine, solver algorithm, scanner colour detection (already partially done), database CRUD, GUI

### Out of Scope

- Internet access / cloud connectivity — system runs on local LAN only (port-forward is user option, not a system requirement)
- Top face motor — physical design has 5 motors covering 5/6 faces; top face stationary by design (CFOP accounts for this)
- Non-CFOP algorithms in v1 — beginner method / Kociemba left out; CFOP is the primary algorithm
- Mobile app — web dashboard covers phone access via browser; no native iOS/Android app
- Multi-cube / batch solving — single cube per session

## Context

- **Course**: SYSC3010 Computer Systems Development, Carleton University, Group L3-G6
- **Team**: Saim Hashmi (Database & GUI Pi — Rpi4), Luke Grundy (Solver Pi — Rpi2), Basil Thotapilly (Scanner Pi — Rpi1), Eric McFetridge (Motor Control Pi — Rpi3)
- **Current state**: Mid-project. DB schema done. Scanner colour detection works. CFOP structure exists but solve loop incomplete. Motor state machine exists but `execute_move_sequence()` not implemented. Backend and GUI not started.
- **Key design choice**: All inter-Pi coordination goes through the database — no direct Pi-to-Pi TCP messages in production. The demo's `EndToEndDemo/` uses direct TCP sockets and is a prototype only.
- **Data ownership**: Scanner Pi owns `cube_states`; Solver Pi owns `solutions`; Motor Pi owns `execution_status`; Database & GUI Pi owns job state machine, `events`, `heartbeats`.
- **Hardware**: Raspberry Pi 4s, SKR v1.4 motor controller board (Klipper), STEP/DIR stepper signals, 2x Pi Camera modules (USB or CSI), custom 3D-printed housing (STLs in `models/`)

## Constraints

- **Hardware**: 5 motors — top face cannot rotate; CFOP algorithm must keep one face stationary
- **Performance**: Full solve (scan + compute + execute) must complete in <15 seconds motor execution time
- **Reliability**: Unresponsive Pi detected within 5 seconds via heartbeat; motors stop within 1 second of stop signal
- **Runtime**: Python 3.13 on all Pis; `.venv/` virtual environment; FastAPI + uvicorn for backend
- **Network**: Local Wi-Fi LAN only; static IPs or hostname resolution between Pis; no internet dependency
- **Frontend**: React or Vue; must be accessible from phone or computer on same LAN
- **Academic**: SYSC3010 course deliverable — subsystems must be independently testable with well-defined inputs/outputs

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Database as coordination layer (no direct Pi-to-Pi TCP in production) | Loose coupling, crash recovery, debugging — each Pi can restart independently | — Pending |
| CFOP as primary solving algorithm | Keeps one face stationary (matches 5-motor hardware), educational value, generates multiple variants for move optimization | — Pending |
| 54-char string as cube state format | Compact, database-storable, directly maps to 54-facelet array | — Pending |
| FastAPI + WebSockets for backend | Python-native, runs on Pi, supports real-time GUI updates without polling | — Pending |
| React or Vue for frontend | Component model suits 5-page dashboard; team preference | — Pending |
| Socket.IO for motor Pi ↔ server (production) | Async, event-driven, cleaner than raw TCP for state machine events | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-24 after initialization*
