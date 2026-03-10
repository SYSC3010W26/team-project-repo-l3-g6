#!/usr/bin/env bash
# ============================================================
# SYSC3010 L3-G6 — Local Development Environment Setup
# Run once from the project root:  bash setup_dev.sh
# ============================================================

set -e  # exit immediately on any error

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/.venv"
ENV_FILE="$ROOT/.env"
DB_PATH="$ROOT/rubiks_dev.db"

# ── Colours ────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}  [OK]${NC} $1"; }
info() { echo -e "${CYAN}  -->>${NC} $1"; }
warn() { echo -e "${YELLOW}  [WARN]${NC} $1"; }
fail() { echo -e "${RED}  [FAIL]${NC} $1"; exit 1; }

echo ""
echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}  SYSC3010 L3-G6 — Dev Environment Setup${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

# ── 1. Python version check ────────────────────────────────
info "Checking Python version..."
PYTHON=$(command -v python3 || command -v python || fail "Python not found. Install Python 3.10+.")
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJ=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
PY_MIN=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJ" -lt 3 ] || { [ "$PY_MAJ" -eq 3 ] && [ "$PY_MIN" -lt 10 ]; }; then
    fail "Python 3.10+ required, found $PY_VER"
fi
ok "Python $PY_VER found at $PYTHON"

# ── 2. Virtual environment ─────────────────────────────────
if [ -d "$VENV" ]; then
    warn "Virtual environment already exists at .venv — skipping creation."
else
    info "Creating virtual environment at .venv ..."
    "$PYTHON" -m venv "$VENV"
    ok "Virtual environment created."
fi

# Activate
source "$VENV/bin/activate"
ok "Virtual environment activated."

# ── 3. Install dependencies ────────────────────────────────
info "Installing Python dependencies from requirements.txt ..."
pip install --quiet --upgrade pip
pip install --quiet -r "$ROOT/requirements.txt"
ok "Dependencies installed."

# ── 4. Create .env file ────────────────────────────────────
if [ -f "$ENV_FILE" ]; then
    warn ".env already exists — not overwriting."
else
    info "Creating .env file ..."
    cat > "$ENV_FILE" <<EOF
# ============================================================
# Local development environment variables
# DO NOT commit this file if it contains real credentials.
# ============================================================

DATABASE_URL=$DB_PATH

# Uncomment and fill in for Supabase production:
# DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
EOF
    ok ".env created (DATABASE_URL=$DB_PATH)."
fi

# ── 5. Initialise database schema ─────────────────────────
info "Initialising database schema ..."
DATABASE_URL="$DB_PATH" "$PYTHON" -m database.init_db
ok "Schema initialised."

# ── 6. Seed realistic development data ────────────────────
info "Seeding development data ..."

DATABASE_URL="$DB_PATH" "$PYTHON" - <<'PYEOF'
import os, sys, sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB = os.environ["DATABASE_URL"]
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

def now(offset_minutes=0):
    return (datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)).isoformat()

cur = conn.cursor()

# ── Extra users ────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM users")
if cur.fetchone()[0] < 2:
    cur.executemany(
        "INSERT INTO users (username, role, created_at) VALUES (?, ?, ?)",
        [
            ("operator", "operator", now(-120)),
            ("viewer",   "viewer",   now(-60)),
        ],
    )
    print("  [OK] Seeded extra users: operator, viewer")
else:
    print("  [SKIP] Extra users already present")

# ── Node status (all 4 Pis) ────────────────────────────────
nodes = [
    ("rpi1-scanner", "scanner",  "192.168.1.101", "online",  now(-1),  "Idle, ready to scan"),
    ("rpi2-solver",  "solver",   "192.168.1.102", "online",  now(-1),  "Idle, awaiting cube state"),
    ("rpi3-motors",  "motors",   "192.168.1.103", "online",  now(-1),  "Idle, awaiting solution"),
    ("rpi4-db",      "database", "192.168.1.104", "online",  now(),    "Serving API on :8000"),
]
for n in nodes:
    cur.execute("""
        INSERT INTO node_status
            (node_id, node_type, ip_address, status, last_heartbeat, last_message)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(node_id) DO UPDATE SET
            status=excluded.status,
            last_heartbeat=excluded.last_heartbeat,
            last_message=excluded.last_message
    """, n)
print("  [OK] Seeded node_status for all 4 Pis")

# ── Completed solve session ────────────────────────────────
cur.execute("""
    INSERT INTO solve_sessions
        (user_id, session_name, selected_algorithm, status, started_at, completed_at, notes)
    VALUES (1, 'Dev Session #1', 'Kociemba', 'completed', ?, ?, 'Seeded by setup_dev.sh')
""", (now(-30), now(-25)))
session1 = cur.lastrowid

# Scan faces
faces = [
    ("U", "RRRGGGBBBWWWOOOYYYRRR", 0.98),
    ("D", "WWWOOOYYYRRRGGGBBBWWW", 0.97),
    ("F", "GGGBBBWWWOOOYYYRRRGGG", 0.96),
    ("B", "BBBWWWOOOYYYRRRGGGBBB", 0.95),
    ("L", "OOOYYYRRRGGGBBBWWWOOO", 0.97),
    ("R", "YYYRRRGGGBBBWWWOOOMMM", 0.94),
]
for face_name, face_string, confidence in faces:
    cur.execute("""
        INSERT INTO scan_faces (session_id, face_name, face_string, confidence, captured_by, created_at)
        VALUES (?, ?, ?, ?, 'rpi1-scanner', ?)
    """, (session1, face_name, face_string, confidence, now(-29)))

# Cube state
cur.execute("""
    INSERT INTO cube_states (session_id, source, state_string, is_valid, confidence, created_at)
    VALUES (?, 'rpi1-scanner', 'RRRGGGBBBWWWOOOYYYRRRGGGBBBWWWOOOYYYRRRGGGBBBWWWOOOYYYY', 1, 0.96, ?)
""", (session1, now(-28)))

# Solution
cur.execute("""
    INSERT INTO solutions (session_id, algorithm_used, move_count, solution_string, generated_by, generated_at)
    VALUES (?, 'Kociemba', 6, "U R2 F' B R U'", 'rpi2-solver', ?)
""", (session1, now(-27)))
solution1 = cur.lastrowid

# Solution steps
steps = [
    (0, "U", "CW",  90),
    (1, "R", "CW",  180),
    (2, "F", "CCW", 90),
    (3, "B", "CW",  90),
    (4, "R", "CW",  90),
    (5, "U", "CCW", 90),
]
for idx, face, direction, degrees in steps:
    cur.execute("""
        INSERT INTO solution_steps (solution_id, step_index, face, direction, degrees, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (solution1, idx, face, direction, degrees, now(-26)))

# Execution run
cur.execute("""
    INSERT INTO execution_runs (session_id, solution_id, status, started_at, completed_at, motor_node_id)
    VALUES (?, ?, 'completed', ?, ?, 'rpi3-motors')
""", (session1, solution1, now(-26), now(-25)))
run1 = cur.lastrowid

# Motor execution log
for idx, face, direction, degrees in steps:
    cur.execute("""
        INSERT INTO motor_execution_log
            (run_id, step_index, commanded_face, commanded_dir, commanded_deg, status, ts)
        VALUES (?, ?, ?, ?, ?, 'success', ?)
    """, (run1, idx, face, direction, degrees, now(-26 + idx)))

# Verification
cur.execute("""
    INSERT INTO verification_results (session_id, run_id, verified, final_state_string, method, notes, created_at)
    VALUES (?, ?, 1, 'WWWWWWWWWGGGGGGGGGRRRRRRRRRBBBBBBBBBOOOOOOOOOYYYYYYYYY', 'camera-rescan', 'All faces solid', ?)
""", (session1, run1, now(-24)))

print("  [OK] Seeded completed solve session #1 (6 moves, verified)")

# ── In-progress solve session ──────────────────────────────
cur.execute("""
    INSERT INTO solve_sessions
        (user_id, session_name, selected_algorithm, status, started_at, notes)
    VALUES (2, 'Dev Session #2', 'CFOP', 'scanning', ?, 'In-progress for GUI dev')
""", (now(-5),))
session2 = cur.lastrowid
cur.execute("""
    INSERT INTO cube_states (session_id, source, state_string, is_valid, confidence, created_at)
    VALUES (?, 'rpi1-scanner', 'PARTIAL_SCAN_IN_PROGRESS', 0, NULL, ?)
""", (session2, now(-4)))
print("  [OK] Seeded in-progress solve session #2 (status=scanning)")

# ── System logs ────────────────────────────────────────────
logs = [
    (session1, "rpi1-scanner", "INFO",  "SCAN_COMPLETE",    "All 6 faces scanned successfully",       None),
    (session1, "rpi2-solver",  "INFO",  "SOLVE_COMPLETE",   "Kociemba solution found in 6 moves",     '{"time_ms": 142}'),
    (session1, "rpi3-motors",  "INFO",  "EXEC_COMPLETE",    "All 6 motor commands executed",           None),
    (session1, "rpi1-scanner", "INFO",  "VERIFY_OK",        "Post-solve verification passed",          None),
    (session2, "rpi1-scanner", "INFO",  "SCAN_START",       "Starting face scan for session 2",        None),
    (None,     "rpi4-db",      "INFO",  "SERVER_START",     "FastAPI server started on port 8000",     None),
    (None,     "rpi3-motors",  "WARN",  "MOTOR_SLOW",       "Motor step took longer than expected",   '{"step": 3, "ms": 850}'),
]
for s_id, node, level, etype, msg, meta in logs:
    cur.execute("""
        INSERT INTO system_logs (session_id, node_id, level, event_type, message, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (s_id, node, level, etype, msg, meta, now()))
print("  [OK] Seeded 7 system log entries")

conn.commit()
conn.close()
print("  [OK] All dev data committed.")
PYEOF

ok "Development data seeded."

# ── 7. Verify ─────────────────────────────────────────────
info "Verifying database contents ..."

"$PYTHON" - <<PYEOF
import sqlite3, os
conn = sqlite3.connect(os.environ.get("DATABASE_URL", "$DB_PATH"))
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print()
print("  Table                   Rows")
print("  " + "-"*35)
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:<25} {count}")
conn.close()
PYEOF

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Setup complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  Database : ${CYAN}$DB_PATH${NC}"
echo -e "  Activate : ${CYAN}source .venv/bin/activate${NC}"
echo -e "  Run API  : ${CYAN}uvicorn main:app --host 0.0.0.0 --port 8000 --reload${NC}"
echo -e "  SQLite   : ${CYAN}sqlite3 $DB_PATH${NC}"
echo ""
echo -e "  To reset the database and re-seed from scratch:"
echo -e "    ${CYAN}rm $DB_PATH && bash setup_dev.sh${NC}"
echo ""
