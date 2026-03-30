#!/usr/bin/env python3
"""
============================================================
SYSC3010 L3-G6 — Demo Simulation Script
Done By : Saim Hashmi

Simulates the full pipeline (Scan → Solve → Execute) by hitting
the backend REST API. No hardware required — run this alongside
the backend to see the dashboard come alive.

Uses Luke's CFOP solver to generate real solutions from actual cube states.

Usage:
    1. Start backend:   uvicorn backend.main:app --host 0.0.0.0 --port 8000
    2. Start frontend:  cd frontend && npm run dev
    3. Run this script: python locale2etest.py

You can also point it at a remote server:
    PI_SERVER_IP=192.168.1.100 python locale2etest.py
============================================================
"""
import requests
import time
import threading
import sys
import os
import argparse

# Add solver directory to path so we can import Luke's solver
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'solver'))
from Solver import Solver, CubeNotSolvableError

# Use central config if available, otherwise fall back to env/defaults
try:
    from Scanner.pi_config import SERVER_URL, HEARTBEAT_INTERVAL
except ImportError:
    SERVER_IP = os.getenv("PI_SERVER_IP", "localhost")
    SERVER_PORT = os.getenv("PI_SERVER_PORT", "8000")
    SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
    HEARTBEAT_INTERVAL = 3

API = SERVER_URL

# ── Simulated cube state (scrambled) ────────────────────────
# Use a real valid scramble from the solver
solver_instance = Solver()
SCRAMBLE = solver_instance.scramble(length=20)
SCRAMBLED_CUBE = solver_instance.get_state_string()

print(f"✨ Generated scramble: {SCRAMBLE}")
print(f"✨ Scrambled cube state: {SCRAMBLED_CUBE}")


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

    # Step 4: Solve the cube using Luke's solver
    print("\n── Step 4: Solver computing solution ──")
    try:
        solver = Solver()
        solver.load_state(SCRAMBLED_CUBE)
        solution_moves_str = solver.solve()
        if not solution_moves_str:
            print("   Cube is already solved! Using empty solution.")
            moves = []
        else:
            moves = solution_moves_str.split()
        print(f"   Solution found ({len(moves)} moves): {solution_moves_str if solution_moves_str else '(none)'}")
    except CubeNotSolvableError as e:
        print(f"   ❌ Cube state is invalid: {e}")
        stop.set()
        return
    except ValueError as e:
        print(f"   ❌ Error loading cube state: {e}")
        stop.set()
        return

    time.sleep(1)

    # Step 5: Submit solution
    print("\n── Step 5: Submitting solution to backend ──")
    r = requests.post(f"{API}/solve/submit", json={
        "session_id": session_id,
        "algorithm_used": "CFOP",
        "move_count": len(moves),
        "solution_string": solution_moves_str if solution_moves_str else "",
    })
    solution_resp = r.json()
    solution_id = solution_resp["solution_id"]
    print(f"   Solution ID: {solution_id}")

    time.sleep(2)

    # Step 6: Transition to executing
    print("\n── Step 6: Transitioning to executing ──")
    r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "executing"})
    if r.status_code == 200:
        print(f"   Status → executing")

    # Start the execution run (unblocks Socket.IO progress)
    r = requests.post(f"{API}/execute/start", json={
        "session_id": session_id,
        "solution_id": solution_id,
        "motor_node_id": "rpi3-motors"
    })
    run_resp = r.json()
    run_id = run_resp["run_id"]
    print(f"   Execution run #{run_id} started")

    time.sleep(1)

    # Step 7: Motor executing moves
    if moves:
        print("\n── Step 7: Motor executing moves ──")
        for i, move in enumerate(moves):
            print(f"   [{i+1}/{len(moves)}] {move}")
            # Report progress to backend (triggers WebSocket event for dashboard)
            requests.post(f"{API}/execute/progress", json={
                "session_id": session_id,
                "run_id": run_id,
                "current_step": i + 1,
                "total_steps": len(moves),
                "move": move
            })
            time.sleep(0.5)
    else:
        print("\n── Step 7: No moves to execute (cube already solved) ──")

    # Step 8: Mark as done
    print("\n── Step 8: Completing ──")
    # Mark execution run as success
    requests.post(f"{API}/execute/complete", json={
        "session_id": session_id,
        "run_id": run_id,
        "status": "success"
    })

    # Final job transition to 'done'
    r = requests.post(f"{API}/jobs/{session_id}/transition", json={"to": "done"})
    if r.status_code == 200:
        print(f"   Status → done ✅")
    else:
        # If execute/complete already set it to 'completed', transition to 'done' might fail
        # depending on state machine rules. Let's check current status.
        r_state = requests.get(f"{API}/jobs/{session_id}")
        current_status = r_state.json()["status"]
        print(f"   Status → {current_status} ✅")

    print("\n🎉 Demo complete! Check the dashboard at http://localhost:5173")

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
