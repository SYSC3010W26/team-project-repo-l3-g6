"""
============================================================
SYSC3010 L3-G6 — Central Pi Configuration
Done By : Saim Hashmi

Single source of truth for the server endpoint.
Every subsystem imports from here instead of hardcoding URLs.

Usage (from any Pi):
    from pi_config import SERVER_URL, NODE_HEARTBEAT_INTERVAL

On the Database/GUI Pi (Rpi4), leave SERVER_IP as-is.
On other Pis, set the PI_SERVER_IP environment variable:
    export PI_SERVER_IP=192.168.1.100

Or create a .env file in the project root:
    PI_SERVER_IP=192.168.1.100
============================================================
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required — env vars work fine

# ---------------------------------------------------------------------------
# Server connection
# ---------------------------------------------------------------------------

SERVER_IP = os.getenv("PI_SERVER_IP", "localhost")
SERVER_PORT = int(os.getenv("PI_SERVER_PORT", "8000"))
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
SOCKETIO_URL = SERVER_URL  # Socket.IO connects to same endpoint

# ---------------------------------------------------------------------------
# API helper — builds full endpoint URLs
# ---------------------------------------------------------------------------

API_BASE = f"{SERVER_URL}"

def api_url(path: str) -> str:
    """Build a full API URL from a relative path.
    
    Examples:
        api_url("/jobs/start")       → "http://192.168.1.100:8000/jobs/start"
        api_url("/nodes/heartbeat")  → "http://192.168.1.100:8000/nodes/heartbeat"
        api_url("/scan/submit")      → "http://192.168.1.100:8000/scan/submit"
    """
    return f"{API_BASE}{path}"

# ---------------------------------------------------------------------------
# Node identity — set per-Pi in .env
# ---------------------------------------------------------------------------

NODE_ID = os.getenv("NODE_ID", "unknown")
NODE_TYPE = os.getenv("NODE_TYPE", "unknown")

# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "3"))  # seconds
HEARTBEAT_STALE_THRESHOLD = 5  # seconds — server marks node offline after this

# ---------------------------------------------------------------------------
# Quick reference — .env file for each Pi
# ---------------------------------------------------------------------------
#
# === Rpi1 (Scanner Pi) .env ===
# PI_SERVER_IP=<rpi4-ip>
# NODE_ID=rpi1-scanner
# NODE_TYPE=scanner
#
# === Rpi2 (Solver Pi) .env ===
# PI_SERVER_IP=<rpi4-ip>
# NODE_ID=rpi2-solver
# NODE_TYPE=solver
#
# === Rpi3 (Motor Pi) .env ===
# PI_SERVER_IP=<rpi4-ip>
# NODE_ID=rpi3-motors
# NODE_TYPE=motor
#
# === Rpi4 (Database & GUI Pi) .env ===
# PI_SERVER_IP=localhost
# NODE_ID=rpi4-db
# NODE_TYPE=database
# DATABASE_URL=./rubiks.db
#
