# Database Layer — SYSC3010 L3-G6 Rubik's Cube Solver
### Written by : Saim Hashmi

## Table of Contents

1. [Overview](#1-overview)
2. [Why Both SQLite and Supabase?](#2-why-both-sqlite-and-supabase)
3. [Repository Structure](#3-repository-structure)
4. [File-by-File Breakdown](#4-file-by-file-breakdown)
5. [Database Schema](#5-database-schema)
6. [Local Dev Setup Script — `setup_dev.sh`](#6-local-dev-setup-script--setup_devsh)
7. [Getting Started — Manual Setup](#7-getting-started--manual-setup)
8. [Switching to Production (Supabase)](#8-switching-to-production-supabase)
9. [End-to-End Flow Across All Four Pis](#9-end-to-end-flow-across-all-four-pis)
10. [CRUD API Reference](#10-crud-api-reference)
11. [Environment Variables](#11-environment-variables)
12. [Extending the Layer](#12-extending-the-layer)

---

## 1. Overview

The database layer lives on **Rpi4** (the Database & GUI node) and serves as the single source of truth for the entire distributed Rubik's Cube Solver system. Instead of Pis talking directly to each other over sockets for every operation, they read and write rows in this database. This decouples the nodes — a Pi can go offline and catch up by re-reading the database when it comes back.

```
Rpi1 (Scanner) ──┐
Rpi2 (Solver)  ──┼──► SQLite / Supabase DB on Rpi4 ◄──── FastAPI GUI
Rpi3 (Motors)  ──┘
```

The code is written against **SQLite** for local development (zero infrastructure, runs anywhere, great for testing on a laptop). The same Python code can be pointed at a **Supabase PostgreSQL** database in production by changing one environment variable and swapping ~10 lines in `db.py`.

---

## 2. Why Both SQLite and Supabase?

| | SQLite (local dev) | Supabase PostgreSQL (production) |
|---|---|---|
| **Setup** | Zero — file on disk | Free hosted instance, online dashboard |
| **Requires network?** | No | Yes |
| **Best for** | Laptop dev, CI, unit tests | Deployed Pis, real-time GUI, remote access |
| **Persistent across reboots?** | Yes (file on SD card) | Yes (cloud) |
| **Concurrent writers?** | Limited (fine for 4 Pis) | Full ACID, handles many writers |
| **Inspect data?** | `sqlite3` CLI or DB Browser | Supabase web dashboard |

**The rule of thumb:** develop and test with SQLite, deploy the real solve sessions to Supabase. Because both are accessed through the same `db.py` interface (either `sqlite3` or `psycopg2`), **no application code outside `db.py` needs to change** when you switch.

---

## 3. Repository Structure

```
team-project-repo-l3-g6/
├── database/
│   ├── __init__.py       # Makes 'database' a Python package
│   ├── schema.sql        # DDL for all 11 tables
│   ├── init_db.py        # One-time setup script (create tables + seed data)
│   ├── db.py             # Connection factory + context manager
│   ├── models.py         # Pydantic v2 data models (FastAPI-compatible)
│   ├── crud.py           # CRUD helper functions
│   └── DATABASE.md       # This file
├── EndToEndDemo/
│   ├── server_db.py      # Existing socket-based server (Rpi4 entry point)
│   ├── Base_Node.py
│   ├── Scanner_Pi_Stub.py
│   ├── Solver_Pi_Stub.py
│   └── Motor_Pi_Stub.py
├── setup_dev.sh          # One-command local dev environment bootstrap
├── requirements.txt      # Python dependencies
└── WeeklyUpdates/
```

---

## 4. File-by-File Breakdown

### `database/schema.sql`

Pure SQL DDL (Data Definition Language). Contains `CREATE TABLE IF NOT EXISTS` statements for all 11 tables. This file is database-agnostic — the syntax works for both SQLite and PostgreSQL with minor type differences (handled by `init_db.py` executing it through the appropriate driver).

**Why a separate `.sql` file instead of inline strings?**
- Easy to read and review in any SQL editor
- Can be imported directly into Supabase's SQL editor to create the schema there
- Source-of-truth for the schema, separate from application logic

---

### `database/init_db.py`

A **one-time setup script** run when first deploying on a new Pi or a fresh dev machine. It:

1. Connects to the database (SQLite path from `DATABASE_URL`)
2. Reads and executes every `CREATE TABLE` statement in `schema.sql`
3. Prints a confirmation line per table
4. Inserts a default `admin` user (skips if already present)

Run it once. Re-running it is safe — all tables use `IF NOT EXISTS`.

---

### `database/db.py`

The **connection module** — the only file that knows whether we're talking to SQLite or PostgreSQL. Everything else imports from here.

Two exports:

- **`get_db()`** — returns a raw connection. Use when you need manual transaction control.
- **`db_session()`** — a `contextmanager` that opens a connection, yields it to your `with` block, commits on success, rolls back on exception, and always closes the connection. Use this in almost all cases.

---

### `database/models.py`

**Pydantic v2** models — one set per table. Each table has three model classes:

| Class suffix | Purpose |
|---|---|
| `Base` | Shared fields (no id, no auto timestamps) |
| `Create` | What you pass in when inserting a row |
| Full (e.g. `User`) | Full row including id and timestamps — used for API responses |

FastAPI uses these automatically to validate incoming JSON bodies and serialise outgoing responses. They also serve as lightweight documentation of what each table holds.

---

### `database/crud.py`

**CRUD helper functions** for the five most critical tables:

| Table | Functions |
|---|---|
| `solve_sessions` | `create_solve_session`, `get_solve_session_by_id`, `update_solve_session_status` |
| `cube_states` | `create_cube_state`, `get_cube_states_by_session` |
| `solutions` | `create_solution`, `get_solutions_by_session` |
| `system_logs` | `create_log` |
| `node_status` | `upsert_heartbeat` |

All functions take an open `sqlite3.Connection` as their first argument so the caller controls transactions. Typical usage:

```python
from database.db import db_session
from database.crud import create_solve_session
from database.models import SolveSessionCreate

with db_session() as conn:
    session_id = create_solve_session(conn, SolveSessionCreate(
        selected_algorithm="Kociemba",
        status="pending",
    ))
```

---

### `requirements.txt`

Python package dependencies for Rpi4:

```
fastapi           # Web framework for the GUI API
uvicorn[standard] # ASGI server to run FastAPI
pydantic          # Data validation (v2)
python-dotenv     # Load DATABASE_URL and other secrets from .env
# psycopg2-binary # Uncomment for Supabase production
```

---

### `setup_dev.sh`

A root-level bash script that fully bootstraps the local development environment in one command. See [Section 6](#6-local-dev-setup-script--setup_devsh) for a full breakdown.

---

## 5. Database Schema

### Entity Relationship Summary

```
users
  └─ solve_sessions (user_id → users.id)
       ├─ cube_states     (session_id → solve_sessions.id)
       ├─ scan_faces       (session_id → solve_sessions.id)
       ├─ solutions        (session_id → solve_sessions.id)
       │    └─ solution_steps (solution_id → solutions.id)
       ├─ execution_runs   (session_id + solution_id → ...)
       │    └─ motor_execution_log (run_id → execution_runs.id)
       ├─ verification_results (session_id + run_id → ...)
       └─ system_logs      (session_id → solve_sessions.id)

node_status  ←── system_logs (node_id → node_status.node_id)
```

### Table Descriptions

| Table | Owner Pi | Purpose |
|---|---|---|
| `users` | Rpi4 | Authenticated operators who can start sessions |
| `node_status` | All Pis | Live heartbeat / IP / status of each Pi |
| `solve_sessions` | Rpi4 | Top-level record for one cube-solve attempt |
| `cube_states` | Rpi1 / Rpi2 | Scanned or computed cube state strings |
| `scan_faces` | Rpi1 | Per-face scan results from the camera |
| `solutions` | Rpi2 | Full move sequence generated by the solver |
| `solution_steps` | Rpi2 | Individual moves in a solution |
| `execution_runs` | Rpi3 / Rpi4 | Physical execution attempt of a solution |
| `motor_execution_log` | Rpi3 | Per-step motor command + status log |
| `verification_results` | Rpi1 / Rpi4 | Post-solve verification scan result |
| `system_logs` | All Pis | Distributed event log (INFO / WARN / ERROR) |

---

## 6. Local Dev Setup Script — `setup_dev.sh`

`setup_dev.sh` lives at the project root and sets up everything needed for local development in a single command — virtual environment, dependencies, `.env` file, database schema, and realistic seed data.

### What it does — step by step

| Step | Action |
|---|---|
| 1 | Checks Python 3.10+ is installed and prints the version found |
| 2 | Creates `.venv/` virtual environment (skips if it already exists) |
| 3 | Runs `pip install -r requirements.txt` inside the venv |
| 4 | Creates `.env` with `DATABASE_URL=./rubiks_dev.db` (skips if it already exists) |
| 5 | Runs `database/init_db.py` — creates all 11 tables, seeds the `admin` user |
| 6 | Seeds realistic development data across every table (see below) |
| 7 | Prints a row-count table for every table so you can confirm everything landed |

### Seed data included

| Data | Details |
|---|---|
| **Users** | `admin` (role=admin), `operator` (role=operator), `viewer` (role=viewer) |
| **Node status** | All 4 Pis registered: rpi1-scanner, rpi2-solver, rpi3-motors, rpi4-db — all `online` |
| **Solve session #1** | Status `completed`, algorithm `Kociemba`, user=admin |
| **Scan faces** | 6 face scans (U/D/F/B/L/R) with confidence scores attached to session #1 |
| **Cube state** | Full 54-char state string, `is_valid=true`, attached to session #1 |
| **Solution** | 6-move solution `"U R2 F' B R U'"` generated by rpi2-solver |
| **Solution steps** | 6 individual step rows (face, direction, degrees) |
| **Execution run** | Status `completed`, executed by rpi3-motors |
| **Motor log** | 6 per-step motor command rows, all `status=success` |
| **Verification** | Post-solve scan confirmed solved (`verified=true`) |
| **Solve session #2** | Status `scanning`, algorithm `CFOP`, user=operator — simulates an in-progress session |
| **System logs** | 7 log entries across all nodes (INFO for normal events, WARN for a slow motor step) |

### Usage

```bash
# First time — run from the project root
bash setup_dev.sh
```

Expected output (abbreviated):

```
============================================================
  SYSC3010 L3-G6 — Dev Environment Setup
============================================================

  -->> Checking Python version...
  [OK] Python 3.10 found at /usr/bin/python3
  -->> Creating virtual environment at .venv ...
  [OK] Virtual environment created.
  [OK] Virtual environment activated.
  -->> Installing Python dependencies from requirements.txt ...
  [OK] Dependencies installed.
  -->> Creating .env file ...
  [OK] .env created (DATABASE_URL=.../rubiks_dev.db).
  -->> Initialising database schema ...
  [OK] Schema initialised.
  -->> Seeding development data ...
  [OK] Seeded extra users: operator, viewer
  [OK] Seeded node_status for all 4 Pis
  [OK] Seeded completed solve session #1 (6 moves, verified)
  [OK] Seeded in-progress solve session #2 (status=scanning)
  [OK] Seeded 7 system log entries
  [OK] All dev data committed.
  [OK] Development data seeded.
  -->> Verifying database contents ...

  Table                   Rows
  -----------------------------------
  cube_states               2
  execution_runs            1
  motor_execution_log       6
  node_status               4
  scan_faces                6
  solution_steps            6
  solutions                 1
  solve_sessions            2
  system_logs               7
  users                     3
  verification_results      1

============================================================
  Setup complete!
============================================================
```

### After setup

```bash
# Activate the virtual environment for any subsequent work
source .venv/bin/activate

# Inspect the database directly
sqlite3 rubiks_dev.db
sqlite3 rubiks_dev.db ".tables"
sqlite3 rubiks_dev.db "SELECT * FROM solve_sessions;"

# Run the FastAPI server (once routes exist)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Re-running and resetting

The script is **idempotent** — re-running it is safe:
- The venv creation step is skipped if `.venv/` already exists.
- `.env` is not overwritten if it already exists.
- All `CREATE TABLE` statements use `IF NOT EXISTS`.

To do a **full reset** (wipe and start fresh):

```bash
rm rubiks_dev.db && bash setup_dev.sh
```

To reset both the database and the env file:

```bash
rm -f rubiks_dev.db .env && bash setup_dev.sh
```

---

## 7. Getting Started — Manual Setup

> If you prefer to run each step yourself instead of using `setup_dev.sh`, follow this section.

### Prerequisites

- Python 3.10+
- pip

### Step 1 — Clone the repo and enter it

```bash
git clone <repo-url>
cd team-project-repo-l3-g6
```

### Step 2 — Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate       # Linux / macOS
# .venv\Scripts\activate        # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — (Optional) Configure the database path

By default the SQLite file is created as `./rubiks.db` relative to where you run the script. To use a custom path create a `.env` file in the project root:

```bash
# .env
DATABASE_URL=./data/rubiks_dev.db
```

### Step 5 — Initialise the database

```bash
python -m database.init_db
```

Expected output:

```
[init_db] Using database: ./rubiks.db
[init_db] Creating tables...
  [OK] Table created (or already exists): users
  [OK] Table created (or already exists): node_status
  [OK] Table created (or already exists): solve_sessions
  [OK] Table created (or already exists): cube_states
  [OK] Table created (or already exists): scan_faces
  [OK] Table created (or already exists): solutions
  [OK] Table created (or already exists): solution_steps
  [OK] Table created (or already exists): execution_runs
  [OK] Table created (or already exists): motor_execution_log
  [OK] Table created (or already exists): verification_results
  [OK] Table created (or already exists): system_logs
[init_db] Seeding default data...
  [OK] Default admin user seeded (username='admin', role='admin').
[init_db] Done.
```

### Step 6 — Verify with the SQLite CLI (optional)

```bash
sqlite3 rubiks.db ".tables"
sqlite3 rubiks.db "SELECT * FROM users;"
```

### Step 7 — Run the FastAPI server (once routes are wired up)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 8. Switching to Production (Supabase)

### Step 1 — Create a Supabase project

1. Go to [supabase.com](https://supabase.com) and create a free project.
2. From **Settings → Database**, copy the **Connection string** (URI format):
   ```
   postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
   ```

### Step 2 — Create the schema in Supabase

Open the **SQL Editor** in the Supabase dashboard and paste the contents of `database/schema.sql`. Click **Run**. All 11 tables will be created.

Alternatively (from your terminal with psql installed):

```bash
psql "postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres" \
  -f database/schema.sql
```

### Step 3 — Set the environment variable on Rpi4

```bash
# /etc/environment  or  ~/.bashrc  or  .env file
DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
```

### Step 4 — Install psycopg2

```bash
pip install psycopg2-binary
```

Or uncomment it in `requirements.txt` and re-run `pip install -r requirements.txt`.

### Step 5 — Swap the connection code in `db.py`

Open `database/db.py` and replace the SQLite `get_db()` and `db_session()` functions with the psycopg2 block that is already written in the comments at the bottom of that file. It is a drop-in replacement — no other file needs to change.

**Before (SQLite):**
```python
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

**After (Supabase / psycopg2):**
```python
import psycopg2
import psycopg2.extras

def get_db():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn
```

Everything else (`db_session()`, all of `crud.py`, all of `models.py`) stays exactly the same.

---

## 9. End-to-End Flow Across All Four Pis

Below is the complete data flow for a single cube-solve session. The database is the communication backbone — no Pi calls another Pi's API directly for data exchange.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐
│  Rpi1    │    │  Rpi2    │    │  Rpi3    │    │  Rpi4            │
│ Scanner  │    │ Solver   │    │ Motors   │    │ Database & GUI   │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────────┬─────────┘
     │               │               │                    │
     │         ① User starts a session via GUI            │
     │               │               │          INSERT solve_sessions
     │               │               │                    │
     │  ② Scan each face             │                    │
     │─────────────────────────────────────────► INSERT scan_faces
     │               │               │          INSERT cube_states
     │               │               │                    │
     │         ③ Solver reads cube state                  │
     │               │◄───────────────────────── SELECT cube_states
     │               │               │                    │
     │         ④ Solver computes solution                 │
     │               │─────────────────────────► INSERT solutions
     │               │─────────────────────────► INSERT solution_steps
     │               │               │                    │
     │               │    ⑤ Motor Pi reads solution       │
     │               │               │◄────────── SELECT solutions
     │               │               │◄────────── SELECT solution_steps
     │               │               │                    │
     │               │    ⑥ Motor Pi executes             │
     │               │               │──────────► INSERT execution_runs
     │               │               │──────────► INSERT motor_execution_log (per step)
     │               │               │──────────► UPDATE execution_runs (completed)
     │               │               │                    │
     │  ⑦ Scanner verifies final state                   │
     │─────────────────────────────────────────► INSERT verification_results
     │               │               │          UPDATE solve_sessions (completed)
     │               │               │                    │
     │         ⑧ GUI reads everything and displays        │
     │               │               │◄────────── SELECT * (all tables)
```

### Heartbeat Loop (continuous, all Pis)

Every Pi runs a background thread that calls `upsert_heartbeat()` every few seconds:

```python
# On each Pi (Scanner, Solver, Motors)
from database.crud import upsert_heartbeat
from database.models import NodeStatusUpsert
from datetime import datetime, timezone

upsert_heartbeat(conn, NodeStatusUpsert(
    node_id="rpi1-scanner",
    node_type="scanner",
    ip_address="192.168.1.101",
    status="online",
    last_heartbeat=datetime.now(timezone.utc),
    last_message="Idle",
))
```

The GUI reads `node_status` to show a live dashboard of which Pis are online.

### Detailed Step-by-Step

#### Step 1 — Session creation (Rpi4 GUI)
The operator opens the web GUI served by FastAPI on Rpi4, selects an algorithm (e.g., Kociemba), and clicks **Start**. The GUI calls:
```python
session_id = create_solve_session(conn, SolveSessionCreate(
    user_id=1,
    session_name="Morning run #3",
    selected_algorithm="Kociemba",
    status="scanning",
))
```

#### Step 2 — Face scanning (Rpi1)
Rpi1 iterates through all 6 faces. For each face:
```python
conn.execute(
    "INSERT INTO scan_faces (session_id, face_name, face_string, confidence, captured_by) VALUES (?,?,?,?,?)",
    (session_id, "U", "RRGGBBYYW...", 0.97, "rpi1-scanner"),
)
```
After all 6 faces are captured, Rpi1 assembles the full 54-character cube state string and writes it:
```python
create_cube_state(conn, CubeStateCreate(
    session_id=session_id,
    source="rpi1-scanner",
    state_string="RRRGGGBBB...",  # 54 chars
    is_valid=True,
    confidence=0.96,
))
```

#### Step 3 — Solving (Rpi2)
Rpi2 polls for new cube states with `status = 'scanning_complete'`:
```python
row = conn.execute(
    "SELECT * FROM cube_states WHERE session_id = ? AND is_valid = 1 ORDER BY created_at DESC LIMIT 1",
    (session_id,)
).fetchone()
```
Rpi2 runs the algorithm and writes the solution:
```python
solution_id = create_solution(conn, SolutionCreate(
    session_id=session_id,
    algorithm_used="Kociemba",
    move_count=20,
    solution_string="U R2 F B R ...",
    generated_by="rpi2-solver",
))
```
Then writes each move as a `solution_step` row.

#### Step 4 — Motor execution (Rpi3)
Rpi3 polls for sessions with `status = 'solved'` and a solution available:
```python
steps = conn.execute(
    "SELECT * FROM solution_steps WHERE solution_id = ? ORDER BY step_index",
    (solution_id,)
).fetchall()
```
Creates an `execution_run`, then for each step fires the motor and logs the result:
```python
conn.execute(
    "INSERT INTO motor_execution_log (run_id, step_index, commanded_face, commanded_dir, commanded_deg, status, ts) VALUES (?,?,?,?,?,?,?)",
    (run_id, i, "U", "CW", 90, "success", now()),
)
```

#### Step 5 — Verification (Rpi1)
After Rpi3 signals completion (by updating `execution_runs.status = 'completed'`), Rpi1 scans the cube again and writes:
```python
conn.execute(
    "INSERT INTO verification_results (session_id, run_id, verified, method, created_at) VALUES (?,?,?,?,?)",
    (session_id, run_id, True, "camera-rescan", now()),
)
```

#### Step 6 — Session close (Rpi4)
```python
update_solve_session_status(conn, session_id, "completed")
```

---

## 10. CRUD API Reference

### `create_solve_session(conn, data: SolveSessionCreate) -> int`
Inserts a new session row. Returns the new `id`.

### `get_solve_session_by_id(conn, session_id: int) -> dict | None`
Returns the full row as a dict, or `None` if not found.

### `update_solve_session_status(conn, session_id, status, completed_at=None)`
Updates `status`. If `status` is `"completed"`, `"failed"`, or `"cancelled"` and no `completed_at` is given, it is set to the current UTC time automatically.

### `create_cube_state(conn, data: CubeStateCreate) -> int`
Inserts a cube state. Returns new `id`.

### `get_cube_states_by_session(conn, session_id) -> list[dict]`
All cube state rows for a session, ordered by `created_at`.

### `create_solution(conn, data: SolutionCreate) -> int`
Inserts a solution. Returns new `id`.

### `get_solutions_by_session(conn, session_id) -> list[dict]`
All solution rows for a session, ordered by `generated_at`.

### `create_log(conn, data: SystemLogCreate) -> int`
Appends a log entry. Returns new `id`. Use this everywhere instead of `print()` on deployed Pis.

### `upsert_heartbeat(conn, data: NodeStatusUpsert) -> None`
Insert-or-update a node's status row. Safe to call from a background thread every few seconds.

---

## 11. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `./rubiks.db` | SQLite file path (dev) or PostgreSQL connection URI (prod) |

Create a `.env` file in the project root — `python-dotenv` loads it automatically when you call `load_dotenv()` in `db.py` and `init_db.py`:

```bash
# .env — do NOT commit this file if it contains real credentials
DATABASE_URL=./rubiks.db
```

For production add it to Rpi4's system environment or a protected `.env`:

```bash
DATABASE_URL=postgresql://postgres:supersecret@db.abcdef.supabase.co:5432/postgres
```

---

## 12. Extending the Layer

### Adding a new table

1. Add the `CREATE TABLE IF NOT EXISTS` statement to `schema.sql`.
2. Re-run `python -m database.init_db` — it skips existing tables and creates new ones.
3. Add Pydantic models (Base, Create, full) to `models.py`.
4. Add CRUD functions to `crud.py`.

### Adding a FastAPI route

```python
# main.py (create this in the project root)
from fastapi import FastAPI, HTTPException
from database.db import db_session
from database.crud import get_solve_session_by_id
from database.models import SolveSession

app = FastAPI(title="Rubik's Cube Solver API")

@app.get("/sessions/{session_id}", response_model=SolveSession)
def read_session(session_id: int):
    with db_session() as conn:
        row = get_solve_session_by_id(conn, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row
```

Run with:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Running tests against a temp database

```python
import tempfile, os, pytest
from database.db import db_session
from database.init_db import create_tables

@pytest.fixture
def conn():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.environ["DATABASE_URL"] = db_path
    import database.db as db_module
    db_module.DB_PATH = db_path
    c = db_module.get_db()
    create_tables(c)
    yield c
    c.close()
    os.unlink(db_path)
```
