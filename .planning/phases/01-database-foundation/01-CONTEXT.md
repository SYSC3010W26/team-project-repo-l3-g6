# Phase 1: Database Foundation - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete the database layer so all 11 tables are fully supported, all CRUD operations are covered, the init script is clean, and unit tests validate every critical operation. Phase 1 does NOT build FastAPI routes, job state machine, or any network-facing code — that is Phase 2+.

</domain>

<decisions>
## Implementation Decisions

### CRUD Coverage

- **D-01:** Add CRUD functions for ALL 6 missing tables: `scan_faces`, `solution_steps`, `execution_runs`, `motor_execution_log`, `verification_results`, `users`. This gives Phase 2 API endpoints clean functions to import instead of writing raw SQL.
- **D-02:** Operation pattern for new tables: `create_*` + `get_by_session` or `get_by_id`, matching existing crud.py conventions. Also add `update_execution_run_status()` since Motor Pi needs to update execution run status after each step.
- **D-03:** No delete functions — this is an audit-style database; records are never removed.

### Test Structure

- **D-04:** Tests live in `database/tests/` (co-located with the module). Filename pattern: `test_crud.py`, `test_schema.py`, etc. pytest discovers them automatically.
- **D-05:** Test fixture: `tempfile` + `create_tables` per the pattern documented in `docs/server/DATABASE.md`. Each test function gets a fresh SQLite file — tests are isolated and do not touch `rubiks_dev.db`.
- **D-06:** A shared `conftest.py` in `database/tests/` provides the `conn` fixture so all test files can reuse it.

### init_db.py Cleanup

- **D-07:** Remove `get_connection()` from `init_db.py` and import `get_db()` from `database.db` instead. This ensures the connection definition is single-sourced — any future change to `db.py` (e.g., PostgreSQL swap) automatically propagates to the init script.

### Schema and users Table

- **D-08:** Keep `users` as a fully supported table with CRUD functions. It is already in `schema.sql`, seeded by `init_db.py`, and referenced by `solve_sessions.user_id`. Update the requirements traceability to list 11 tables.
- **D-09:** `solve_sessions.user_id` remains an optional FK (already `REFERENCES users(id)` without NOT NULL constraint). The admin user seeded by `init_db.py` serves as the default operator for sessions where no explicit user is assigned.

### Claude's Discretion

- Test coverage depth: which specific CRUD assertions to make (row count, field values, FK enforcement) is left to the planner.
- Whether to add a `get_all_nodes()` convenience function for the heartbeat monitor is Claude's call.
- Whether to add a `database/tests/__init__.py` is Claude's call (usually not needed for pytest).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Database Layer
- `database/schema.sql` — Source of truth for all 11 table definitions (users, node_status, solve_sessions, cube_states, scan_faces, solutions, solution_steps, execution_runs, motor_execution_log, verification_results, system_logs)
- `database/models.py` — Pydantic v2 models for all tables; CRUD functions must accept/return types consistent with these models
- `database/crud.py` — Existing CRUD functions; new functions must follow the same patterns (connection as first arg, return lastrowid for inserts, return list[dict] for reads)
- `database/db.py` — Connection factory (`get_db()`, `db_session()`); init_db.py should import from here
- `database/init_db.py` — Bootstrap script; refactor to import from db.py and verify all 11 tables created

### Documentation
- `docs/server/DATABASE.md` — Comprehensive reference including test fixture pattern (Section 12), CRUD API reference (Section 10), and end-to-end flow (Section 9)

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 1 requirement IDs: DB-01, DB-02, DB-03, DB-04, TEST-01

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `database/db.py:db_session()`: Context manager (open → yield → commit/rollback → close) — all CRUD tests should use this instead of manual connection management
- `database/crud.py:_now()`: UTC timestamp helper — new CRUD functions should reuse this
- `database/crud.py:_row_to_dict()`: Row conversion helper — reuse for all new read functions
- `init_db.py:create_tables()`: Already reads schema.sql and reports per-table — no changes needed beyond importing `get_db()` instead of duplicating `get_connection()`

### Established Patterns
- All CRUD functions take `conn: sqlite3.Connection` as first argument (callers manage transaction scope)
- Inserts use positional `?` placeholders — not named params
- Timestamps are stored as ISO 8601 strings via `_now()`, not Python datetime objects
- Models use `from_attributes = True` in model_config for ORM compatibility

### Integration Points
- `solve_sessions.id` is the join key for all session-scoped tables (cube_states, scan_faces, solutions, execution_runs, verification_results, system_logs)
- `solutions.id` is the join key for `solution_steps` and `execution_runs`
- `execution_runs.id` is the join key for `motor_execution_log`
- `node_status.node_id` is referenced by `system_logs.node_id`

</code_context>

<specifics>
## Specific Ideas

- `update_execution_run_status(conn, run_id, status, completed_at=None)` — mirrors existing `update_solve_session_status()` pattern; Motor Pi needs this to mark runs as completed/failed
- Test fixture from DATABASE.md Section 12 is the exact pattern to use in `database/tests/conftest.py`
- `init_db.py` should import: `from database.db import get_db` and remove its own `get_connection()` body

</specifics>

<deferred>
## Deferred Ideas

- Auth/login flow for the users table — keeping users as a real table is Phase 1; role-based access enforcement is future scope
- PostgreSQL / Supabase migration — documented in db.py comments and DATABASE.md; not a Phase 1 deliverable
- Indexing for performance (e.g., index on session_id FK columns) — out of scope for Phase 1; add if performance testing reveals a need
- Connection pooling — not needed for SQLite single-file dev setup

</deferred>

---

*Phase: 01-database-foundation*
*Context gathered: 2026-03-24*
