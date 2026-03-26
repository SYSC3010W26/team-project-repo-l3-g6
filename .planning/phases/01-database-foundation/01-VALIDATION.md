---
phase: 1
slug: database-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | `pytest.ini` — Wave 0 creates |
| **Quick run command** | `python -m pytest database/tests/test_schema.py -q` |
| **Full suite command** | `python -m pytest database/tests/ -v` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest database/tests/test_schema.py -q`
- **After every plan wave:** Run `python -m pytest database/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| schema-verify | 01-01 | 1 | DB-01 | unit | `python -m pytest database/tests/test_schema.py -q` | ❌ W0 | ⬜ pending |
| init-db-refactor | 01-01 | 1 | DB-04 | integration | `python init_db.py && python -m pytest database/tests/test_schema.py -q` | ❌ W0 | ⬜ pending |
| crud-scan-faces | 01-02 | 2 | DB-02 | unit | `python -m pytest database/tests/test_crud.py::test_scan_faces -q` | ❌ W0 | ⬜ pending |
| crud-solution-steps | 01-02 | 2 | DB-02 | unit | `python -m pytest database/tests/test_crud.py::test_solution_steps -q` | ❌ W0 | ⬜ pending |
| crud-execution-runs | 01-02 | 2 | DB-03 | unit | `python -m pytest database/tests/test_crud.py::test_execution_runs -q` | ❌ W0 | ⬜ pending |
| crud-motor-log | 01-02 | 2 | DB-03 | unit | `python -m pytest database/tests/test_crud.py::test_motor_execution_log -q` | ❌ W0 | ⬜ pending |
| crud-verification | 01-02 | 2 | DB-02 | unit | `python -m pytest database/tests/test_crud.py::test_verification_results -q` | ❌ W0 | ⬜ pending |
| crud-users | 01-02 | 2 | DB-02 | unit | `python -m pytest database/tests/test_crud.py::test_users -q` | ❌ W0 | ⬜ pending |
| full-test-suite | 01-03 | 3 | TEST-01 | unit | `python -m pytest database/tests/ -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `database/tests/__init__.py` (empty, optional but keeps imports clean)
- [ ] `database/tests/conftest.py` — shared `conn` fixture using `tempfile` + `create_tables`
- [ ] `database/tests/test_schema.py` — stubs for DB-01 (all 11 tables exist, FK constraints)
- [ ] `database/tests/test_crud.py` — stubs for DB-02, DB-03 (all 6 missing table CRUD functions)
- [ ] `pytest.ini` — rootdir config pointing to `database/tests/`
- [ ] `pytest` added to `.venv` — `pip install pytest` (currently system-only, not in `.venv`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `python init_db.py` creates `rubiks_dev.db` with all 11 tables | DB-04 | File creation on real filesystem | Run `python init_db.py`, then `sqlite3 rubiks_dev.db .tables` — must list all 11 tables |
| Scanner Pi can write to `scan_faces` over network | DB-02 | Requires Scanner Pi hardware | Phase 2 integration test — out of scope for Phase 1 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
