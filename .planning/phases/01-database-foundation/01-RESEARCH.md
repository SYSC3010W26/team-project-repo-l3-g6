# Phase 1: Database Foundation — Research

**Researched:** 2026-03-24
**Domain:** SQLite / Python CRUD layer (sqlite3 + Pydantic v2 + pytest)
**Confidence:** HIGH — all findings are based on direct code inspection of the existing codebase; no speculative claims.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Add CRUD functions for ALL 6 missing tables: `scan_faces`, `solution_steps`, `execution_runs`, `motor_execution_log`, `verification_results`, `users`. This gives Phase 2 API endpoints clean functions to import instead of writing raw SQL.
- **D-02:** Operation pattern for new tables: `create_*` + `get_by_session` or `get_by_id`, matching existing crud.py conventions. Also add `update_execution_run_status()` since Motor Pi needs to update execution run status after each step.
- **D-03:** No delete functions — this is an audit-style database; records are never removed.
- **D-04:** Tests live in `database/tests/` (co-located with the module). Filename pattern: `test_crud.py`, `test_schema.py`, etc. pytest discovers them automatically.
- **D-05:** Test fixture: `tempfile` + `create_tables` per the pattern documented in `docs/server/DATABASE.md`. Each test function gets a fresh SQLite file — tests are isolated and do not touch `rubiks_dev.db`.
- **D-06:** A shared `conftest.py` in `database/tests/` provides the `conn` fixture so all test files can reuse it.
- **D-07:** Remove `get_connection()` from `init_db.py` and import `get_db()` from `database.db` instead. This ensures the connection definition is single-sourced.
- **D-08:** Keep `users` as a fully supported table with CRUD functions. It is already in `schema.sql`, seeded by `init_db.py`, and referenced by `solve_sessions.user_id`.
- **D-09:** `solve_sessions.user_id` remains an optional FK (already `REFERENCES users(id)` without NOT NULL constraint). The admin user seeded by `init_db.py` serves as the default operator for sessions where no explicit user is assigned.

### Claude's Discretion

- Test coverage depth: which specific CRUD assertions to make (row count, field values, FK enforcement) is left to the planner.
- Whether to add a `get_all_nodes()` convenience function for the heartbeat monitor is Claude's call.
- Whether to add a `database/tests/__init__.py` is Claude's call (usually not needed for pytest).

### Deferred Ideas (OUT OF SCOPE)

- Auth/login flow for the users table — keeping users as a real table is Phase 1; role-based access enforcement is future scope.
- PostgreSQL / Supabase migration — documented in db.py comments and DATABASE.md; not a Phase 1 deliverable.
- Indexing for performance (e.g., index on session_id FK columns) — out of scope for Phase 1.
- Connection pooling — not needed for SQLite single-file dev setup.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DB-01 | Database schema is fully initialized on startup (all 11 tables) | `init_db.py` already creates all 11 tables via `schema.sql`; D-07 cleanup ensures single-source connection; verified all 11 tables in schema.sql |
| DB-02 | CRUD operations exist for all tables used by other subsystems | 5 of 11 tables have CRUD today; 6 are missing; exact signatures identified below |
| DB-03 | Database enforces foreign key constraints and correct data types | `PRAGMA foreign_keys = ON` is set in `get_db()`; must verify it is also set when `init_db.py` opens its connection (D-07 fixes this) |
| DB-04 | Each subsystem can read/write only the tables it owns | Enforced by API layer (Phase 2); Phase 1 ensures the CRUD functions exist per table so Phase 2 can assign ownership at the route level |
| TEST-01 | Database CRUD operations have unit tests covering create, read, update for all major tables | No test directory exists today; must create `database/tests/conftest.py`, `test_crud.py`, `test_schema.py` from scratch |
</phase_requirements>

---

## Summary

The database layer is partially built. `schema.sql` defines all 11 tables correctly. `db.py` provides a clean connection factory with FK enforcement and a context manager. `models.py` has complete Pydantic v2 models for every table. However, `crud.py` only covers 5 of the 11 tables (`solve_sessions`, `cube_states`, `solutions`, `system_logs`, `node_status`), and there are no tests at all.

Phase 1 has two concrete work streams: (1) add CRUD for the 6 missing tables following the exact patterns already established in `crud.py`, and (2) build a pytest test suite in `database/tests/` using the temp-file fixture pattern from DATABASE.md Section 12. A third task — a small cleanup of `init_db.py` to remove the duplicate `get_connection()` function — is a single-import change.

The integration urgency is real. Luke's Solver Pi is ~80% done and will soon write `solutions`/`solution_steps` rows. Eric's Motor Pi hardware is complete and needs `execution_runs`/`motor_execution_log` CRUD. These are not placeholder tasks — the missing CRUD functions are blocking integration.

**Primary recommendation:** Implement CRUD for the 6 missing tables in `crud.py`, write tests in `database/tests/`, and clean up `init_db.py` as three separate, sequenced tasks.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `sqlite3` | stdlib (3.13) | SQLite driver | Zero-dependency; already in use |
| Pydantic | 2.12.5 (confirmed in `.venv`) | Input validation + model serialisation | Already used in `models.py`; FastAPI expects it |
| pytest | 8.3.4 (system Python) | Test runner | Installed system-wide; not yet in `requirements.txt` |
| python-dotenv | in requirements.txt | Load `DATABASE_URL` from `.env` | Already used in `db.py` and `init_db.py` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tempfile` | stdlib | Temp SQLite file per test | Used in every test fixture |
| `contextlib.contextmanager` | stdlib | `db_session()` context manager | Already implemented in `db.py` |

### Notes on pytest

pytest is installed system-wide (Python 3.13, version 8.3.4) but is **not listed in `requirements.txt`**. The planner must add `pytest` to `requirements.txt` or document that tests are run with the system Python. The `.venv` does not have pytest installed.

**Installation (to add to requirements.txt):**
```bash
pytest
```

---

## CRUD Coverage Audit

### Tables WITH CRUD functions today

| Table | Functions in crud.py |
|-------|---------------------|
| `solve_sessions` | `create_solve_session`, `get_solve_session_by_id`, `update_solve_session_status` |
| `cube_states` | `create_cube_state`, `get_cube_states_by_session` |
| `solutions` | `create_solution`, `get_solutions_by_session` |
| `system_logs` | `create_log` |
| `node_status` | `upsert_heartbeat` |

### Tables MISSING CRUD functions (must add in Phase 1)

| Table | Required By | Urgency | Operations Needed |
|-------|-------------|---------|-------------------|
| `scan_faces` | Scanner Pi (Eric) | HIGH | `create_scan_face`, `get_scan_faces_by_session` |
| `solution_steps` | Solver Pi (Luke) + Motor Pi (Eric) | CRITICAL | `create_solution_step`, `get_solution_steps_by_solution` |
| `execution_runs` | Motor Pi (Eric) | CRITICAL | `create_execution_run`, `get_execution_runs_by_session`, `update_execution_run_status` |
| `motor_execution_log` | Motor Pi (Eric) | CRITICAL | `create_motor_log`, `get_motor_logs_by_run` |
| `verification_results` | Scanner Pi post-solve | HIGH | `create_verification_result`, `get_verification_results_by_session` |
| `users` | Rpi4 admin seeding + session FK | MEDIUM | `create_user`, `get_user_by_id` |

---

## Architecture Patterns

### Existing CRUD Pattern (extract from crud.py)

Every function follows this contract — new functions MUST match it exactly:

**Pattern: create_*(conn, data: XxxCreate) -> int**
```python
# Source: database/crud.py (verified by direct inspection)
def create_solve_session(conn: sqlite3.Connection, data: SolveSessionCreate) -> int:
    cursor = conn.execute(
        """
        INSERT INTO solve_sessions
            (user_id, session_name, selected_algorithm, status, started_at, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.user_id,
            data.session_name,
            data.selected_algorithm,
            data.status,
            _now(),
            data.notes,
        ),
    )
    return cursor.lastrowid
```

**Pattern: get_*_by_session(conn, session_id: int) -> list[dict]**
```python
# Source: database/crud.py (verified by direct inspection)
def get_cube_states_by_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM cube_states WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

**Pattern: update_*_status(conn, id, status, completed_at=None)**
```python
# Source: database/crud.py (verified by direct inspection)
def update_solve_session_status(
    conn: sqlite3.Connection,
    session_id: int,
    status: str,
    completed_at: Optional[str] = None,
) -> None:
    if completed_at is None and status in ("completed", "failed", "cancelled"):
        completed_at = _now()
    conn.execute(
        "UPDATE solve_sessions SET status = ?, completed_at = ? WHERE id = ?",
        (status, completed_at, session_id),
    )
```

### Exact Function Signatures for 6 Missing Tables

The following signatures are derived directly from `schema.sql` column definitions and `models.py` `*Create` classes. These are not estimates — they are derived from the source of truth.

#### scan_faces

```python
# schema.sql: id, session_id (FK→solve_sessions), face_name, face_string,
#             confidence (nullable), captured_by (nullable), created_at
def create_scan_face(conn: sqlite3.Connection, data: ScanFaceCreate) -> int:
    cursor = conn.execute(
        """
        INSERT INTO scan_faces
            (session_id, face_name, face_string, confidence, captured_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.face_name,
            data.face_string,
            data.confidence,
            data.captured_by,
            _now(),
        ),
    )
    return cursor.lastrowid

def get_scan_faces_by_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM scan_faces WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

#### solution_steps

```python
# schema.sql: id, solution_id (FK→solutions), step_index, face, direction,
#             degrees, created_at
def create_solution_step(conn: sqlite3.Connection, data: SolutionStepCreate) -> int:
    cursor = conn.execute(
        """
        INSERT INTO solution_steps
            (solution_id, step_index, face, direction, degrees, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data.solution_id,
            data.step_index,
            data.face,
            data.direction,
            data.degrees,
            _now(),
        ),
    )
    return cursor.lastrowid

def get_solution_steps_by_solution(
    conn: sqlite3.Connection, solution_id: int
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM solution_steps WHERE solution_id = ? ORDER BY step_index",
        (solution_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

Note: ordered by `step_index` (not `created_at`) because Motor Pi needs steps in execution order.

#### execution_runs

```python
# schema.sql: id, session_id (FK→solve_sessions), solution_id (FK→solutions),
#             status, started_at, completed_at (nullable), motor_node_id (nullable)
def create_execution_run(conn: sqlite3.Connection, data: ExecutionRunCreate) -> int:
    cursor = conn.execute(
        """
        INSERT INTO execution_runs
            (session_id, solution_id, status, started_at, motor_node_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.solution_id,
            data.status,
            _now(),
            data.motor_node_id,
        ),
    )
    return cursor.lastrowid

def get_execution_runs_by_session(
    conn: sqlite3.Connection, session_id: int
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM execution_runs WHERE session_id = ? ORDER BY started_at",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]

def update_execution_run_status(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    completed_at: Optional[str] = None,
) -> None:
    # Mirror of update_solve_session_status pattern (D-02 / CONTEXT.md specifics)
    if completed_at is None and status in ("completed", "failed", "cancelled"):
        completed_at = _now()
    conn.execute(
        "UPDATE execution_runs SET status = ?, completed_at = ? WHERE id = ?",
        (status, completed_at, run_id),
    )
```

#### motor_execution_log

```python
# schema.sql: id, run_id (FK→execution_runs), step_index, commanded_face,
#             commanded_dir, commanded_deg, status, error_code (nullable),
#             error_message (nullable), ts
def create_motor_log(
    conn: sqlite3.Connection, data: MotorExecutionLogCreate
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO motor_execution_log
            (run_id, step_index, commanded_face, commanded_dir,
             commanded_deg, status, error_code, error_message, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.run_id,
            data.step_index,
            data.commanded_face,
            data.commanded_dir,
            data.commanded_deg,
            data.status,
            data.error_code,
            data.error_message,
            _now(),
        ),
    )
    return cursor.lastrowid

def get_motor_logs_by_run(conn: sqlite3.Connection, run_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM motor_execution_log WHERE run_id = ? ORDER BY step_index",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

#### verification_results

```python
# schema.sql: id, session_id (FK→solve_sessions), run_id (nullable FK→execution_runs),
#             verified, final_state_string (nullable), method, notes (nullable),
#             created_at
def create_verification_result(
    conn: sqlite3.Connection, data: VerificationResultCreate
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO verification_results
            (session_id, run_id, verified, final_state_string,
             method, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.session_id,
            data.run_id,
            data.verified,
            data.final_state_string,
            data.method,
            data.notes,
            _now(),
        ),
    )
    return cursor.lastrowid

def get_verification_results_by_session(
    conn: sqlite3.Connection, session_id: int
) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM verification_results WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

#### users

```python
# schema.sql: id, username, role, created_at
# Note: no password column — Phase 1 only; auth enforcement is deferred
def create_user(conn: sqlite3.Connection, data: UserCreate) -> int:
    cursor = conn.execute(
        """
        INSERT INTO users (username, role, created_at)
        VALUES (?, ?, ?)
        """,
        (data.username, data.role, _now()),
    )
    return cursor.lastrowid

def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None
```

### Required Import Updates to crud.py

The existing import block in `crud.py` imports only:
```python
from .models import (
    SolveSessionCreate, CubeStateCreate, SolutionCreate,
    SystemLogCreate, NodeStatusUpsert,
)
```

After adding the 6 new functions, the import block must also include:
```python
    ScanFaceCreate,
    SolutionStepCreate,
    ExecutionRunCreate,
    MotorExecutionLogCreate,
    VerificationResultCreate,
    UserCreate,
```

### init_db.py Refactoring (D-07)

Current state — `init_db.py` has a local duplicate of the connection function:
```python
def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

And it calls it as: `conn = get_connection(DB_PATH)`

Target state after D-07:
- Remove `get_connection()` entirely from `init_db.py`
- Remove `import sqlite3` from `init_db.py` (no longer needed directly)
- Add `from database.db import get_db`
- Change the call in `main()` to: `conn = get_db()`

Critical: `get_db()` in `db.py` reads `DB_PATH` from module-level, not as a parameter. The `main()` call site in `init_db.py` currently passes `DB_PATH` as an argument. After refactoring, `DATABASE_URL` must be set in the environment (via `.env`) before `get_db()` is called — which is already handled by `load_dotenv()` at the top of `init_db.py`. This is safe.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FK enforcement | Manual FK checks in Python | `PRAGMA foreign_keys = ON` (already in `get_db()`) | SQLite natively enforces FKs when pragma is ON |
| UTC timestamp generation | `datetime.now()` without tz | `_now()` helper already in crud.py | `_now()` uses `timezone.utc` — ensures no naive datetimes |
| Transaction management | Manual `conn.commit()` / rollback | `db_session()` context manager from `db.py` | Already handles commit/rollback/close in all paths |
| Test isolation | Shared test database | `tempfile.NamedTemporaryFile` per fixture | Each test gets a fresh file; no state leakage |
| Row dict conversion | `row["col"]` access | `_row_to_dict()` already in crud.py | Works with `sqlite3.Row`; returns `{}` safely for None rows |

---

## Common Pitfalls

### Pitfall 1: FK violations not raised at INSERT time

**What goes wrong:** `execution_runs` has two FKs (`session_id` → `solve_sessions.id` AND `solution_id` → `solutions.id`). If a test inserts an `execution_run` without first creating a valid `solve_session` and `solution`, the insert silently succeeds — SQLite ignores FK constraints unless `PRAGMA foreign_keys = ON` is set on the connection.

**Why it happens:** The `conn` fixture in tests must call `PRAGMA foreign_keys = ON`. The `get_db()` function does this, but if any test creates a raw `sqlite3.connect()` without going through `get_db()`, FK enforcement is absent.

**How to avoid:** Always use `get_db()` or the fixture that calls `get_db()`. Never call `sqlite3.connect()` directly in tests.

**Warning signs:** FK-violating inserts succeed silently in tests; FK errors only appear when running against production DB.

### Pitfall 2: _now() timestamp vs. schema DEFAULT CURRENT_TIMESTAMP

**What goes wrong:** `schema.sql` defines `DEFAULT CURRENT_TIMESTAMP` for timestamp columns. However, all existing `INSERT` statements in `crud.py` supply the timestamp explicitly via `_now()` — they do NOT rely on the DEFAULT. If a new CRUD function omits the timestamp column from the `INSERT`, SQLite will use its own `CURRENT_TIMESTAMP` (which is UTC but in a different format: `"2026-03-24 12:00:00"` vs. `_now()`'s ISO 8601 `"2026-03-24T12:00:00+00:00"`).

**Why it happens:** Inconsistent timestamp formats break downstream code that parses them as datetimes, and they produce inconsistent sort results if mixed.

**How to avoid:** Always pass `_now()` explicitly in every `INSERT` — do not rely on `DEFAULT CURRENT_TIMESTAMP`.

### Pitfall 3: solution_steps ordered by created_at instead of step_index

**What goes wrong:** If `get_solution_steps_by_solution` returns steps `ORDER BY created_at` instead of `ORDER BY step_index`, Motor Pi will execute moves in insertion order, which may not match logical order if steps were batched or inserted out of order.

**How to avoid:** Always order `solution_steps` by `step_index ASC`.

### Pitfall 4: motor_execution_log timestamp column is named ts not created_at

**What goes wrong:** All other tables use `created_at` for their timestamp. `motor_execution_log` uses `ts` (as defined in `schema.sql` and `models.py`). An `ORDER BY created_at` query on this table will fail.

**How to avoid:** Use `ORDER BY step_index` or `ORDER BY ts` for `motor_execution_log` queries. The planner and implementer must note this inconsistency.

### Pitfall 5: init_db.py run mode

**What goes wrong:** `init_db.py` is designed to be run as `python -m database.init_db` (module mode). Running it as `python database/init_db.py` (file mode) may fail with relative import errors because `crud.py` uses `from .models import ...`.

**How to avoid:** Always invoke as `python -m database.init_db` from the project root. Document this in test setup.

### Pitfall 6: Test discovery — pytest needs database/tests/__init__.py or proper config

**What goes wrong:** By default, pytest discovers tests by walking directories. If the `database/tests/` directory is not a proper Python package OR if `database/` itself causes import confusion (it has an `__init__.py`), pytest may fail to import test files with "ModuleNotFoundError: No module named 'database'".

**How to avoid:** Add `pytest` to `requirements.txt`. Consider adding a root `conftest.py` or `pyproject.toml`/`pytest.ini` with `pythonpath = .` so pytest resolves `database.*` imports correctly. Since `database/__init__.py` exists, the package import path `from database.crud import ...` works when pytest is run from the project root.

**Recommended `pytest.ini` at project root:**
```ini
[pytest]
testpaths = database/tests
pythonpath = .
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 (system Python; must add to requirements.txt) |
| Config file | `pytest.ini` at project root — needs `pythonpath = .` (Wave 0 gap) |
| Quick run command | `pytest database/tests/ -x -q` |
| Full suite command | `pytest database/tests/ -v` |

### Test File Structure

```
database/
├── tests/
│   ├── conftest.py       # Shared conn fixture (Wave 0 gap)
│   ├── test_schema.py    # DB-01: all 11 tables created by init_db
│   └── test_crud.py      # TEST-01: create/read/update for all major tables
```

### Fixture Pattern (from DATABASE.md Section 12, locked by D-05/D-06)

```python
# database/tests/conftest.py
import tempfile, os, pytest
import database.db as db_module
from database.init_db import create_tables

@pytest.fixture
def conn():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["DATABASE_URL"] = db_path
    db_module.DB_PATH = db_path
    c = db_module.get_db()
    create_tables(c)
    yield c
    c.close()
    os.unlink(db_path)
```

Note: this fixture directly patches `db_module.DB_PATH` so `get_db()` uses the temp file. This is the exact pattern from DATABASE.md and is safe for sequential test runs.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DB-01 | All 11 tables created by `create_tables()` | unit | `pytest database/tests/test_schema.py -x` | Wave 0 gap |
| DB-01 | `init_db.py` uses `get_db()` (no duplicate `get_connection`) | unit | `pytest database/tests/test_schema.py -x` | Wave 0 gap |
| DB-02 | `create_scan_face` inserts and returns valid id | unit | `pytest database/tests/test_crud.py::test_create_scan_face -x` | Wave 0 gap |
| DB-02 | `get_scan_faces_by_session` returns correct rows | unit | `pytest database/tests/test_crud.py::test_get_scan_faces -x` | Wave 0 gap |
| DB-02 | `create_solution_step` inserts and returns valid id | unit | `pytest database/tests/test_crud.py::test_create_solution_step -x` | Wave 0 gap |
| DB-02 | `get_solution_steps_by_solution` returns steps ordered by step_index | unit | `pytest database/tests/test_crud.py::test_get_solution_steps_ordered -x` | Wave 0 gap |
| DB-02 | `create_execution_run` inserts and returns valid id | unit | `pytest database/tests/test_crud.py::test_create_execution_run -x` | Wave 0 gap |
| DB-02 | `update_execution_run_status` updates status and sets completed_at | unit | `pytest database/tests/test_crud.py::test_update_execution_run_status -x` | Wave 0 gap |
| DB-02 | `create_motor_log` inserts and returns valid id | unit | `pytest database/tests/test_crud.py::test_create_motor_log -x` | Wave 0 gap |
| DB-02 | `create_verification_result` inserts and returns valid id | unit | `pytest database/tests/test_crud.py::test_create_verification_result -x` | Wave 0 gap |
| DB-02 | `create_user` / `get_user_by_id` round-trip | unit | `pytest database/tests/test_crud.py::test_user_crud -x` | Wave 0 gap |
| DB-03 | FK violation raises `IntegrityError` when FK pragma is ON | unit | `pytest database/tests/test_crud.py::test_fk_enforcement -x` | Wave 0 gap |
| TEST-01 | All existing CRUD functions (solve_sessions, cube_states, solutions, system_logs, node_status) have test coverage | unit | `pytest database/tests/test_crud.py -x` | Wave 0 gap |

### Sampling Rate

- **Per task commit:** `pytest database/tests/ -x -q`
- **Per wave merge:** `pytest database/tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `database/tests/` directory — does not exist
- [ ] `database/tests/conftest.py` — shared `conn` fixture
- [ ] `database/tests/test_schema.py` — DB-01 coverage
- [ ] `database/tests/test_crud.py` — DB-02, DB-03, TEST-01 coverage
- [ ] `pytest.ini` at project root — `pythonpath = .` and `testpaths = database/tests`
- [ ] `pytest` added to `requirements.txt` — not currently listed

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `class Config: orm_mode = True` | Pydantic v2 `model_config = {"from_attributes": True}` | Pydantic 2.0 (2023) | `models.py` is already correct for v2; no migration needed |
| `sqlite3.connect(path)` returning tuple rows | `conn.row_factory = sqlite3.Row` + `dict(row)` | Long-standing pattern | Already implemented in `get_db()` and `_row_to_dict()` |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | Yes | 3.13.12 | — |
| pytest | TEST-01 | Partial (system Python only) | 8.3.4 | Must add to requirements.txt; not in .venv |
| sqlite3 | DB layer | Yes (stdlib) | built-in | — |
| pydantic | models.py, crud.py | Yes (.venv) | 2.12.5 | — |
| fastapi | Phase 2 (not Phase 1) | Yes (.venv) | 0.135.1 | — |
| python-dotenv | db.py, init_db.py | Yes (in requirements.txt) | in .venv | — |
| rubiks_dev.db | Dev testing | Yes (exists at project root) | — | Re-create with `bash setup_dev.sh` |

**Missing dependencies with no fallback:**
- `pytest` not in `.venv` / `requirements.txt` — must be added before tests can run

**Missing dependencies with fallback:**
- None

---

## Open Questions

1. **Should `get_all_nodes()` be added to crud.py?**
   - What we know: `node_status` has `upsert_heartbeat` but no read function. The heartbeat monitor in Phase 3 will need to read all node rows to detect stale heartbeats.
   - What's unclear: Whether Phase 2 needs it before Phase 3.
   - Recommendation: Add `get_all_nodes(conn) -> list[dict]` in Phase 1 since it is trivial and prevents Phase 2 from writing raw SQL. This is Claude's discretion per CONTEXT.md.

2. **Should `database/tests/__init__.py` exist?**
   - What we know: pytest generally does NOT need `__init__.py` in test directories. However, if there are naming collisions (two `conftest.py` at different levels), `__init__.py` helps namespace them.
   - Recommendation: Do NOT add it. pytest autodiscovery works without it, and it adds no benefit here. This is Claude's discretion per CONTEXT.md.

3. **FK enforcement in conftest.py fixture**
   - What we know: The fixture calls `db_module.get_db()` which sets `PRAGMA foreign_keys = ON`. The `create_tables(c)` call uses the same connection, so FK enforcement is active during table creation AND test execution.
   - Confirmation: This is correct behavior — no gap here.

---

## Sources

### Primary (HIGH confidence)

- `database/schema.sql` — inspected directly; all 11 table definitions confirmed
- `database/crud.py` — inspected directly; all 5 existing functions, patterns, and helpers confirmed
- `database/db.py` — inspected directly; `get_db()`, `db_session()`, `PRAGMA foreign_keys = ON` confirmed
- `database/models.py` — inspected directly; all `*Create` model fields confirmed for each missing table
- `database/init_db.py` — inspected directly; duplicate `get_connection()` confirmed; D-07 change scope confirmed
- `docs/server/DATABASE.md Section 12` — inspected directly; fixture pattern confirmed verbatim

### Secondary (MEDIUM confidence)

- pytest 8.3.4 system install confirmed by `python3 -c "import pytest; print(pytest.__version__)"`
- pydantic 2.12.5 in `.venv` confirmed by `python -c "import pydantic; print(pydantic.__version__)"`
- fastapi 0.135.1 in `.venv` confirmed by direct import

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions confirmed by direct environment inspection
- Architecture: HIGH — all patterns derived from existing production code, not guessed
- Pitfalls: HIGH — all identified from direct schema/code inspection, not training data assumptions
- Test fixture: HIGH — fixture verbatim from DATABASE.md Section 12 confirmed by file inspection

**Research date:** 2026-03-24
**Valid until:** Stable — SQLite stdlib, Pydantic v2, pytest patterns are stable; re-verify only if requirements.txt changes
