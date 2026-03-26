# Phase 2: FastAPI Backend - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 02 — FastAPI Backend

---

## Areas Discussed

All four gray areas were selected for discussion.

---

## Area 1: Project Layout

**Q: Where should the FastAPI server live and how should it be structured?**

Options presented:
- `backend/` package with `main.py` + `routers/` + `schemas.py` *(selected)*
- `server/` package (same structure, different name)
- Single `main.py` at root

**Selected:** `backend/` package
**Rationale:** Clean separation from `database/`. Consistent with standard FastAPI project layout. Easy to extend in Phase 3+.

---

**Q: Should schemas.py reuse database/models.py directly, or define separate API schemas?**

Options presented:
- Separate `backend/schemas.py` with lean API-specific models *(selected)*
- Reuse `database/models.py` models directly in route handlers

**Selected:** Separate `backend/schemas.py`
**Rationale:** Keeps API contract independent of DB model changes. Can still import from `database/models.py` where convenient.

---

## Area 2: WebSocket / Socket.IO Split

**Q: How should real-time communication be handled?**

Options presented:
- Single `python-socketio` AsyncServer for everything — Pis and frontend *(selected)*
- Socket.IO for Pi nodes + native FastAPI WebSocket for frontend

**Selected:** Socket.IO for everything
**Rationale:** One server, one protocol. Motor Pi already uses `python-socketio` AsyncClient. Frontend (Phase 4) can use `socket.io-client` JS. Simpler ops.

---

**Q: Which Socket.IO events should the server emit to the frontend?**

Options presented:
- `job_state_update` + `execution_progress` as separate named events *(selected)*
- Single generic `state_update` event with a `type` field

**Selected:** `job_state_update` + `execution_progress`
**Rationale:** Explicit named events. `job_state_update` fires on pipeline stage change; `execution_progress` fires per motor step with completion percentage.

---

## Area 3: REST Endpoint Structure

**Q: How should REST routes be organized?**

Options presented:
- Pipeline-stage-based: `/scan`, `/solve`, `/execute`, `/jobs`, `/nodes` *(selected)*
- Resource-based: `/cube-states`, `/solutions`, `/execution-runs`, `/node-status`

**Selected:** Pipeline-stage-based
**Rationale:** Intuitive for the other Pis — Scanner Pi POSTs to `/scan/submit`, Solver Pi to `/solve/submit`, Motor Pi to `/execute/*`. Mirrors the solve pipeline.

---

**Q: What HTTP error response shape?**

Options presented:
- FastAPI defaults — raw Pydantic models for success, HTTPException for errors *(selected)*
- Custom response envelope `{success, data, error}`

**Selected:** FastAPI defaults
**Rationale:** Simple. Aligns with what TestClient integration tests expect. No boilerplate overhead for a course deliverable.

---

## Area 4: Integration Test Scope

**Q: What should TEST-03 integration tests cover and how should they run?**

Options presented:
- FastAPI `TestClient` + real SQLite (same fixture pattern as Phase 1) *(selected)*
- TestClient + mocked DB (rejected — same risk as noted in Phase 1 deferred)
- Real server + httpx async client (overkill)

**Selected:** TestClient + real SQLite
**Rationale:** Hits real route handlers with a fresh in-memory SQLite DB per test. No mocking. Fast. Consistent with Phase 1 approach. Same `tempfile` + `create_tables` fixture pattern.

---

**Q: Where should tests live?**

Options presented:
- `backend/tests/` co-located with the module *(selected)*
- Root `tests/` directory

**Selected:** `backend/tests/`
**Rationale:** Consistent with `database/tests/` co-location convention from Phase 1.

---

*Discussion log generated: 2026-03-25*
