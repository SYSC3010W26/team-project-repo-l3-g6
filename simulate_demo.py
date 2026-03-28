#!/usr/bin/env python3
"""
============================================================
SYSC3010 L3-G6 — Demo Simulation Script
Done By : Saim Hashmi

Simulates the full pipeline (Scan → Solve → Execute) by hitting
the backend REST API. No hardware required — run this alongside
the backend to see the dashboard come alive.

Usage:
    1. Start backend:   uvicorn backend.main:app --host 0.0.0.0 --port 8000
    2. Start frontend:  cd frontend && npm run dev
    3. Run this script: python simulate_demo.py

You can also point it at a remote server:
    PI_SERVER_IP=192.168.1.100 python simulate_demo.py
============================================================
"""
import requests
import time
import threading
import sys
import os
import argparse

# Use central config if available, otherwise fall back to env/defaults
try:
    from pi_config import SERVER_URL, HEARTBEAT_INTERVAL
except ImportError:
    SERVER_IP = os.getenv("PI_SERVER_IP", "localhost")
    SERVER_PORT = os.getenv("PI_SERVER_PORT", "8000")
    SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
    HEARTBEAT_INTERVAL = 3

API = SERVER_URL

# ── Simulated cube state (scrambled) ────────────────────────
SCRAMBLED_CUBE = (
    "RRGGBBOOWW"
    "YYRRGGBBOO"
    "WWYYRRGGO"
    "OBWYRGOBY"
    "WGROBYWGR"
    "BYOWG"
)[:54].ljust(54, "W")  # pad to 54 chars

# ── Simulated solution ──────────────────────────────────────
SOLUTION_MOVES = "R U R' U' F' D2 L B L' B' R U2 R' U F R U R' U'"


def heartbeat_loop(nodes: list[str], stop_event: threading.Event):
    """Send heartbeats for all simulated nodes every few seconds."""
    node_types = {
        "rpi1-scanner": "scanner",
        "rpi2-solver": "solver",
        "rpi3-motors": "motor",
        "rpi4-db": "database",
    }
    while not stop_event.is_set():
        for node_id in nodes:
            try:
                requests.post(f"{API}/nodes/heartbeat", json={
                    "node_id": node_id,
                    "node_type": node_types.get(node_id, "unknown"),
                    "status": "online",
                })
            except requests.ConnectionError:
                pass
        stop_event.wait(HEARTBEAT_INTERVAL)


def run_demo(keep_alive: bool = True):
    print(f"🎯 Pi³ Demo Simulator")
    print(f"   Server: {API}")
    print()

    # Check server is reachable
    try:
        r = requests.get(f"{API}/")
        print(f"✅ Server reachable: {r.json()}")
    except requests.ConnectionError:
        print(f"❌ Cannot reach server at {API}")
        print(f"   Start it with: uvicorn backend.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    # Start heartbeats for all 4 nodes
    nodes = ["rpi1-scanner", "rpi2-solver", "rpi3-motors", "rpi4-db"]
    stop = threading.Event()
    hb_thread = threading.Thread(target=heartbeat_loop, args=(nodes, stop), daemon=True)
    hb_thread.start()
    print("💓 Heartbeats started for all 4 nodes")
    time.sleep(2)  # Let heartbeats register

    # Step 1: Start a solve session
    print("\n── Step 1: Starting solve session ──")
    r = requests.post(f"{API}/jobs/start", json={
        "algorithm": "CFOP",
        "session_name": "Demo Run",
    })
    session = r.json()
    session_id = session["session_id"]
    print(f"   Session #{session_id} created")

    time.sleep(2)

    # Step 2: Submit scanned cube state
    print("\n── Step 2: Scanner submitting cube state ──")
    r = requests.post(f"{API}/scan/submit", json={
        "session_id": session_id,
        "state_string": SCRAMBLED_CUBE,
        "is_valid": True,
        "confidence": 0.95,
    })
    print(f"   Cube state submitted (confidence: 95%)")

    time.sleep(2)

    # Step 3: Transition to solving
    print("\n── Step 3: Transitioning to solving ──")
    r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "solving"})
    if r.status_code == 200:
        print(f"   Status → solving")
    else:
        print(f"   Transition response: {r.status_code} {r.text}")

    time.sleep(2)

    # Step 4: Submit solution
    print("\n── Step 4: Solver submitting solution ──")
    moves = SOLUTION_MOVES.split()
    r = requests.post(f"{API}/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": len(moves),
        "solution_string": SOLUTION_MOVES,
    })
    solution = r.json()
    print(f"   Solution submitted ({len(moves)} moves)")

    time.sleep(2)

    # Step 5: Transition to executing
    print("\n── Step 5: Transitioning to executing ──")
    r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "executing"})
    if r.status_code == 200:
        print(f"   Status → executing")

    time.sleep(1)

    # Step 6: Simulate motor execution progress
    print("\n── Step 6: Motor executing moves ──")
    for i, move in enumerate(moves):
        print(f"   [{i+1}/{len(moves)}] {move}")
        time.sleep(0.5)

    # Step 7: Mark as done
    print("\n── Step 7: Completing ──")
    r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "done"})
    if r.status_code == 200:
        print(f"   Status → done ✅")

    print("\n🎉 Demo complete! Check the dashboard at http://localhost:4173")

    if not keep_alive:
        stop.set()
        print("✅ One-shot mode complete. Exiting.")
        return

    print("   Heartbeats will continue running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()
        print("\n👋 Stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate PI³ scan→solve→execute demo flow")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the full flow once and exit (for local e2e/CI checks)",
    )
    args = parser.parse_args()

    run_demo(keep_alive=not args.once)
