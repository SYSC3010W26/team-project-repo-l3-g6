---
phase: 2
slug: fastapi-backend
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already configured in `pytest.ini`) |
| **Config file** | `pytest.ini` — testpaths must include `backend/tests` |
| **Quick run command** | `python -m pytest backend/tests/ -x -q` |
| **Full suite command** | `python -m pytest database/tests/ backend/tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest backend/tests/ -x -q`
- **After every plan wave:** Run `python -m pytest database/tests/ backend/tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | API-01 | integration | `python -m pytest backend/tests/test_integration.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | API-02 | integration | `python -m pytest backend/tests/test_routes_scan.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | API-02 | integration | `python -m pytest backend/tests/test_routes_solve.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | API-02 | integration | `python -m pytest backend/tests/test_routes_execute.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | API-04 | integration | `python -m pytest backend/tests/test_routes_nodes.py -x -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | API-03 | integration | `python -m pytest backend/tests/test_socketio.py -x -q` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 3 | TEST-03 | integration | `python -m pytest backend/tests/test_integration.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/__init__.py` — package marker
- [ ] `backend/tests/__init__.py` — package marker
- [ ] `backend/tests/conftest.py` — TestClient + fresh SQLite DB fixture (replicates database/tests/conftest.py pattern)
- [ ] `pytest.ini` updated — add `backend/tests` to `testpaths`
- [ ] `requirements.txt` updated — add `python-socketio`, `httpx` if not present
- [ ] Stub test files with placeholder `pass` bodies so pytest discovers them on Wave 0

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Server reachable at `http://<rpi4-ip>:8000` | API-01 | Requires real LAN hardware | Run `uvicorn backend.main:app --host 0.0.0.0 --port 8000` on Rpi4 and `curl http://<rpi4-ip>:8000/` from another Pi |
| Motor Pi connects via Socket.IO | API-03 | Requires `motorctl/` running on Rpi3 | Start server, start motor Pi, check `node_status` table for motor heartbeat row |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
