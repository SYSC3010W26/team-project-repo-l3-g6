# Requirements: Pi³ — Database & GUI Pi (Saim)

**Defined:** 2026-03-24
**Core Value:** A scrambled cube placed in the robot comes out solved, with the full pipeline running end-to-end without manual intervention — and Saim's subsystem is the coordination layer that makes that possible.

## v1 Requirements

### Database

- [x] **DB-01**: Database schema is fully initialized on startup (`solve_sessions`, `scan_faces`, `cube_states`, `solutions`, `solution_steps`, `execution_runs`, `motor_execution_log`, `verification_results`, `node_status`, `system_logs`)
- [x] **DB-02**: CRUD operations exist for all tables used by other subsystems (cube_states, solutions, execution_status, heartbeats, events)
- [x] **DB-03**: Database enforces foreign key constraints and correct data types
- [x] **DB-04**: Each subsystem can read/write only the tables it owns (data ownership enforced by API layer)

### Backend API

- [x] **API-01**: FastAPI server runs on Database & GUI Pi and is reachable by all other Pis on local LAN
- [x] **API-02**: REST endpoints exist for all pipeline stages: submit cube state, fetch cube state, submit solution, fetch solution, submit execution status, fetch execution status
- [x] **API-03**: WebSocket endpoint streams live job state and execution progress to connected web clients
- [x] **API-04**: API accepts heartbeat writes from all 4 Pis and updates `node_status` table
- [x] **API-05**: API returns correct HTTP status codes and structured error responses

### Job State Machine

- [ ] **JOB-01**: Server enforces pipeline ordering: Idle → Scanning → Solving → Executing → Done/Error
- [ ] **JOB-02**: Solve only starts after a valid cube state exists in DB (confidence flag set)
- [ ] **JOB-03**: Execute only starts after a solution exists in DB
- [x] **JOB-04**: Server detects missing heartbeat from any Pi within 5 seconds and transitions job to Error state
- [ ] **JOB-05**: GUI actions (Start, Stop, Reset, Rescan) are written as control flags observable by other subsystems

### Web Dashboard

- [ ] **GUI-01**: Dashboard page — shows current pipeline stage, node health (online/offline per Pi), last cube state, active job status
- [ ] **GUI-02**: Solve Results page — shows history of past solve sessions with algorithm, move count, solve time
- [ ] **GUI-03**: Execution Monitor page — shows live progress of current motor execution (current move index, move list, completion percentage)
- [ ] **GUI-04**: Solution Review page — displays full move sequence for a selected solve; allows step-by-step review
- [ ] **GUI-05**: System Logs page — displays timestamped event log filtered by severity (Info/Warning/Error/Fatal)
- [ ] **GUI-06**: Dashboard displays a 3D interactive cube model reflecting the current scanned cube state
- [ ] **GUI-07**: Dashboard is accessible from a phone or computer browser on the same LAN (no internet required)
- [ ] **GUI-08**: User can trigger Start Solve, Stop, Reset, and Rescan actions from the dashboard

### Notifications & Error Handling

- [ ] **NOTF-01**: GUI displays a visible error banner when a fatal event is logged (disconnected motor, unresponsive Pi, camera failure)
- [ ] **NOTF-02**: Browser notification is triggered for fatal errors when the user has the dashboard open
- [ ] **NOTF-03**: Error state includes recovery guidance displayed to the user (e.g., "Check Motor Pi connection")

### Testing

- [x] **TEST-01**: Database CRUD operations have unit tests covering create, read, update for all major tables
- [ ] **TEST-02**: Job state machine transitions are testable in isolation (no hardware required)
- [x] **TEST-03**: API endpoints have integration tests covering the happy path (scan → solve → execute flow)

## v2 Requirements

### Enhancements

- **V2-01**: Algorithm selection from GUI (user picks CFOP variant or speed)
- **V2-02**: Motor speed adjustment from GUI (full speed vs. user-defined RPM)
- **V2-03**: Solve statistics comparison (chart: algorithm vs. average move count / time)
- **V2-04**: Tutorial mode — GUI steps through solution moves with explanation
- **V2-05**: Port-forward support / external access with authentication

## Out of Scope

| Feature | Reason |
|---------|--------|
| Internet connectivity | System runs on local LAN only |
| Native mobile app | Web dashboard covers phone access via browser |
| Multi-cube / batch sessions | Single cube per session by design |
| Top face motor control | Physical hardware has 5 motors; top face is stationary |
| Non-CFOP algorithms in v1 | CFOP is the only algorithm for initial demo |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DB-01 | Phase 1 | Complete |
| DB-02 | Phase 1 | Complete |
| DB-03 | Phase 1 | Complete |
| DB-04 | Phase 1 | Complete |
| API-01 | Phase 2 | Complete |
| API-02 | Phase 2 | Complete |
| API-03 | Phase 2 | Complete |
| API-04 | Phase 2 | Complete |
| API-05 | Phase 2 | Complete |
| JOB-01 | Phase 3 | Pending |
| JOB-02 | Phase 3 | Pending |
| JOB-03 | Phase 3 | Pending |
| JOB-04 | Phase 3 | Complete |
| JOB-05 | Phase 3 | Pending |
| GUI-01 | Phase 4 | Pending |
| GUI-02 | Phase 4 | Pending |
| GUI-03 | Phase 4 | Pending |
| GUI-04 | Phase 4 | Pending |
| GUI-05 | Phase 4 | Pending |
| GUI-06 | Phase 5 | Pending |
| GUI-07 | Phase 4 | Pending |
| GUI-08 | Phase 4 | Pending |
| NOTF-01 | Phase 5 | Pending |
| NOTF-02 | Phase 5 | Pending |
| NOTF-03 | Phase 5 | Pending |
| TEST-01 | Phase 1 | Complete |
| TEST-02 | Phase 3 | Pending |
| TEST-03 | Phase 2 | Complete |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 after initial definition*
