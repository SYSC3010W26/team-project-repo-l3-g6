---
phase: 3
slug: job-state-machine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | `pytest.ini` (testpaths: database/tests, backend/tests) |
| **Quick run command** | `pytest backend/tests/test_job_state.py -x` |
| **Full suite command** | `pytest -xvs` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest backend/tests/test_job_state.py -x`
- **After every plan wave:** Run `pytest -xvs`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | JOB-01 | unit | `pytest backend/tests/test_job_state.py::test_state_machine_transition_legal -x` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | JOB-01 | unit | `pytest backend/tests/test_job_state.py::test_state_machine_all_states -x` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 1 | JOB-02 | unit | `pytest backend/tests/test_job_state.py::test_scanning_to_solving_requires_cube_state -x` | ❌ W0 | ⬜ pending |
| 3-01-04 | 01 | 1 | JOB-03 | unit | `pytest backend/tests/test_job_state.py::test_solving_to_executing_requires_solution -x` | ❌ W0 | ⬜ pending |
| 3-01-05 | 01 | 1 | TEST-02 | unit | `pytest backend/tests/test_job_state.py -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 2 | JOB-04 | integration | `pytest backend/tests/test_heartbeat.py::test_heartbeat_monitor_errors_stale_pi -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 2 | JOB-04 | integration | `pytest backend/tests/test_heartbeat.py::test_heartbeat_monitor_ignores_stale_idle_job -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 3 | JOB-05 | integration | `pytest backend/tests/test_control_flags.py::test_post_control_flag_creates_row -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 3 | JOB-05 | integration | `pytest backend/tests/test_control_flags.py::test_get_pending_control_flags -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_job_state.py` — stubs for JOB-01, JOB-02, JOB-03, TEST-02
- [ ] `backend/tests/test_heartbeat.py` — stubs for JOB-04
- [ ] `backend/tests/test_control_flags.py` — stubs for JOB-05
- [ ] `backend/job_state.py` — JobStateMachine class (needed for test imports)
- [ ] `backend/heartbeat.py` — heartbeat_monitor() coroutine (needed for test imports)
- [ ] `database/schema.sql` — add job_control table definition (D-15)
- [ ] `database/models.py` — add JobControl, JobControlCreate Pydantic models
- [ ] `database/crud.py` — add CRUD functions for job_control (create, get pending, update status)
- [ ] `backend/schemas.py` — add JobTransitionRequest, ControlFlagRequest, ControlFlagResponse schemas
- [ ] `backend/routers/jobs.py` — add POST /jobs/{id}/transition, POST /jobs/{id}/control, GET /jobs/{id}/control, POST /jobs/{id}/control/ack
- [ ] `backend/main.py` — add startup event or lifespan to launch heartbeat_monitor task

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Socket.IO `job_state_update` broadcast received by client on transition | JOB-01 | Requires live WebSocket client connection | Connect a Socket.IO test client, trigger state transition via REST, verify event received |
| GUI control flag observable within 2 seconds by a polling Pi | JOB-05 | Requires multi-process polling timing | Issue control flag via POST, poll GET endpoint from a separate process, verify within 2 poll cycles |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
