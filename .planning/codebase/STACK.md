# Technology Stack

**Analysis Date:** 2026-03-24

## Languages

**Primary:**
- Python 3.13 - All core application logic, APIs, control server, solver algorithms, motor control, scanner integration

## Runtime

**Environment:**
- Python 3.13.12
- Linux (Raspberry Pi 4 target)

**Package Manager:**
- pip
- Lockfile: `requirements.txt` present

## Frameworks

**Core:**
- FastAPI - Web API framework for control server (Rpi4 GUI/API server)
- Uvicorn[standard] - ASGI server to run FastAPI applications

**Data & Validation:**
- Pydantic v2 - Data validation and serialization for request/response models

**Communication:**
- python-socketio - Real-time bidirectional communication between nodes (motor control, heartbeat, state management)
- Built-in socket module - Raw socket communication for baseline node-to-server messaging

**HTTP Client:**
- httpx - Async HTTP client for healthchecks (Moonraker API calls)

## Key Dependencies

**Critical:**
- FastAPI - Web framework for server node API endpoints
- Uvicorn[standard] - ASGI server runtime
- Pydantic - Request/response validation and serialization (Pydantic v2)
- python-socketio - Async socket.io client for distributed node communication
- python-dotenv - Environment variable loading from .env files
- httpx - Async HTTP client for hardware healthchecks

**Database:**
- sqlite3 - Built-in Python module for local development database
- psycopg2-binary - Commented in requirements.txt for production Supabase/PostgreSQL migration

**Optional/Future:**
- psycopg2-binary - PostgreSQL driver for production deployment (currently commented out)

## Configuration

**Environment:**
- Configuration via `.env` file (loaded by python-dotenv)
- Environment variables: `DATABASE_URL`, `NODE_ID`, `SERVER_URL`, `MOONRAKER_URL`, `HEARTBEAT_INTERVAL`

**Build:**
- No explicit build configuration (Python source executed directly)
- Virtual environment: `.venv/` (created by `setup_dev.sh`)

## Database

**Development:**
- SQLite via `DATABASE_URL` environment variable (default: `./rubiks.db`)
- Connection: `sqlite3.Connection` with row factory for dict-like access
- Foreign key constraints enabled via PRAGMA

**Production (Ready for deployment):**
- Supabase PostgreSQL via `psycopg2-binary` (driver commented in requirements.txt)
- Connection string format: `postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres`
- Drop-in replacement migration path documented in `database/db.py`

## Platform Requirements

**Development:**
- Python 3.10+
- Linux/Unix-like environment (macOS compatible)
- 4+ GB RAM recommended for venv and solver algorithms

**Production:**
- Raspberry Pi 4 with Linux OS
- Hardware requirements per node:
  - **Motor Node (Rpi3):** BTT SKR v1.4 board with 5x TMC2209 stepper drivers (24V 1.4A), Klipper firmware
  - **Scanner Node (Rpi1):** Camera module for cube state recognition
  - **Solver Node (Rpi2):** 1+ GB RAM for CFOP algorithm computation
  - **Control Server (Rpi4):** Database server + GUI server, 2+ GB RAM

**Network:**
- TCP/IP connectivity between all nodes via socket.io (port configurable via `SERVER_URL`)
- HTTP access to Moonraker API on motor node for hardware healthchecks

---

*Stack analysis: 2026-03-24*
