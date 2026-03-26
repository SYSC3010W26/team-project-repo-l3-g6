# External Integrations

**Analysis Date:** 2026-03-24

## APIs & External Services

**Hardware Control:**
- Moonraker API - Klipper firmware control interface for motor hardware
  - SDK/Client: Built-in httpx async HTTP client
  - Usage: Motor node healthchecks at startup (`motorctl/src/healthcheck.py`)
  - Endpoint: `{MOONRAKER_URL}/printer/info`
  - Authentication: Not detected (local network assumed)

**Node-to-Server Communication:**
- Socket.io WebSocket Protocol - Real-time event-based communication
  - SDK/Client: `python-socketio` async client
  - Usage: All distributed nodes communicate with control server
  - Connection: Initiated by motor control node at `motorctl/src/server_bridge.py`
  - Events: `heartbeat`, `state_change`, `load_moves`, `start_solve`, `execution_complete`, `log`, `node_state_update`

## Data Storage

**Databases:**
- SQLite (Development)
  - Provider: Built-in Python sqlite3 module
  - Connection: `database/db.py` via context manager `db_session()`
  - Default path: `./rubiks.db`
  - Configurable via `DATABASE_URL` env var
  - Row factory: Dict-like access enabled
  - Foreign keys: Enforced via PRAGMA

- PostgreSQL via Supabase (Production Ready)
  - Provider: Supabase PostgreSQL
  - Connection: Via `psycopg2-binary` (currently commented in `requirements.txt`)
  - Connection string format: `postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres`
  - Migration path: Drop-in replacement in `database/db.py` lines 63-82
  - Schema: Identical to SQLite schema in `database/schema.sql`

**File Storage:**
- Local filesystem only - No cloud storage integration detected

**Caching:**
- None detected - State managed in-memory per node or persisted to database

## Authentication & Identity

**Auth Provider:**
- Custom/Manual authentication - No external auth service detected
- User table: `users` table in database with `username` and `role` fields
- Implementation: Pydantic models `UserBase`, `UserCreate`, `User` in `database/models.py`
- No OAuth, JWT, or external identity provider integration

## Monitoring & Observability

**Error Tracking:**
- None detected - No integration with error tracking services (Sentry, etc.)

**Logs:**
- Database-driven approach:
  - Table: `system_logs` table for distributed event logging
  - Schema: `node_id`, `level`, `event_type`, `message`, `metadata`, `created_at`
  - All node events routed through central server for persistent storage
  - CRUD: `database/crud.py` contains log insertion functions

**Health Monitoring:**
- Heartbeat mechanism:
  - Motor node sends periodic heartbeats via socket.io (`motorctl/src/heartbeat.py`)
  - Interval: Configurable via `HEARTBEAT_INTERVAL` env var (default: 5 seconds)
  - Tracked in database `node_status` table

## CI/CD & Deployment

**Hosting:**
- Raspberry Pi 4 cluster (distributed)
  - Control Server: Rpi4 with FastAPI + database
  - Motor Node: Rpi3 with motor control logic
  - Solver Node: Rpi2 with cube solving algorithms
  - Scanner Node: Rpi1 with optical recognition

**Deployment:**
- Direct Python execution (no containerization detected)
- Manual startup via Python + asyncio
- Environment configuration via `.env` file
- Development setup via `setup_dev.sh` bash script

**CI Pipeline:**
- None detected - No GitHub Actions, GitLab CI, or Jenkins configuration

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - Path to SQLite database or PostgreSQL connection string
- `NODE_ID` - Unique identifier for motor control node
- `SERVER_URL` - WebSocket endpoint for server connection (e.g., `http://localhost:5000`)
- `MOONRAKER_URL` - HTTP endpoint for Klipper API (e.g., `http://localhost:7125`)
- `HEARTBEAT_INTERVAL` - Heartbeat frequency in seconds (default: 5)

**Secrets location:**
- `.env` file (local development)
- Environment variables set on production Raspberry Pi instances
- No secrets management system detected (Vault, AWS Secrets Manager, etc.)

## Webhooks & Callbacks

**Incoming:**
- Socket.io events from motor node to server:
  - `register` - Node registration with server
  - `heartbeat` - Periodic health check
  - `state_change` - Motor node state transitions
  - `node_state_update` - State manager updates

**Outgoing:**
- Socket.io events from server to motor node:
  - `load_moves` - Send move sequence to motor
  - `start_solve` - Begin motor execution

**Message Format:**
- JSON objects with structure: `{"type": "...", "node": "...", "data": {...}}`
- Low-level socket protocol in `EndToEndDemo/server_db.py`

## Motor Hardware Integration

**Stepper Drivers:**
- 5x TMC2209 stepper motor drivers
- Operating voltage: 24V
- Peak current: 1.4A per driver
- Interface: Via BTT SKR v1.4 control board

**Firmware Control:**
- Klipper firmware - Real-time motion controller for stepper motors
- Interface: Moonraker API at `{MOONRAKER_URL}/printer/info`
- Health check polling: Motor node validates hardware readiness at startup

**Motor Command Protocol:**
- Move notation: Standard Rubik's cube notation (U, D, L, R, F, B + primes/doubles)
- Execution: `motorctl/src/actuator.py` - `execute_move_sequence()` function
- Logging: Per-step execution log in `motor_execution_log` database table

---

*Integration audit: 2026-03-24*
